"""E04 A36 synthetic F02 version-chain replay and traceability regressions."""
import copy
import unittest
from dataclasses import fields, replace
from datetime import timedelta, timezone
from pathlib import Path
from unittest import mock
from uuid import uuid4

from backend.f02_version_chain_replay_candidate import (
    SCHEMA, SOURCE_STATE, MAX_PRIOR_OBSERVATIONS,
    ReplayObservation, ReplayResult, ReplayStatus as Status,
    classify_version_chain_replay_candidate as check,
)
from backend.tests.test_f02_version_chain_candidate import (
    chain, two_epochs_with_updates, MID_A, FINAL,
)
from backend.tests.test_f02_multihuman_epoch_candidate import two_cycles

def evaluate(n, history=()):
    return check(*n, history)

def alter_visits(n):
    visits=copy.deepcopy(n[6])
    visits[0]["proposal"]["text"]="Condição sujeita a nova confirmação."
    return n[:6]+(tuple(visits),)+n[7:]

def reissue(n, *, new_event_ids=True):
    """Equivalent valid separate route, still same store and idempotency key."""
    route=replace(n[0],route_id=uuid4())
    ids={e.event_id:(uuid4() if new_event_ids else e.event_id) for e in n[1]}
    events=tuple(replace(e,route_id=route.route_id,event_id=ids[e.event_id])
                 for e in n[1])
    epochs=tuple(replace(e,closure_event_id=ids[e.closure_event_id],
                         f03_event_id=ids[e.f03_event_id],
                         f02_event_id=ids[e.f02_event_id]) for e in n[8])
    updates=tuple(replace(e,event_id=ids[e.event_id],
                          f03_event_id=ids[e.f03_event_id],
                          f02_event_id=ids[e.f02_event_id]) for e in n[9])
    return (route,events)+n[2:8]+(epochs,updates)

class VersionChainReplayTests(unittest.TestCase):
    def test_01_first_chain_is_new_candidate_not_authorized(self):
        r=evaluate(chain())
        self.assertIs(r.status,Status.NEW_CHAIN_CANDIDATE_ONLY)
        self.assertIsInstance(r.candidate_observation,ReplayObservation)
        self.assertEqual(r.candidate_observation.source_state,SOURCE_STATE)

    def test_02_exact_replay_is_recognized_without_action(self):
        n=chain()
        old=evaluate(n).candidate_observation
        got=evaluate(n,(old,))
        self.assertIs(got.status,Status.IDENTICAL_REPLAY_NO_NEW_ACTION)
        self.assertEqual(got.candidate_observation,old)

    def test_03_same_request_two_identical_observations_stays_replay(self):
        n=chain(); old=evaluate(n).candidate_observation
        self.assertIs(evaluate(n,(old,old)).status,
                      Status.IDENTICAL_REPLAY_NO_NEW_ACTION)

    def test_04_deterministic_hash_identical_on_repeat(self):
        n=chain()
        self.assertEqual(evaluate(n).candidate_observation.payload_sha256,
                         evaluate(n).candidate_observation.payload_sha256)

    def test_05_utc_equivalent_event_offset_same_chain_digest(self):
        n=chain();e=list(n[1])
        shifted=replace(e[-2],occurred_at=e[-2].occurred_at.astimezone(
            timezone(timedelta(hours=-3))))
        e[-2]=shifted
        changed=n[:1]+(tuple(e),)+n[2:]
        self.assertEqual(evaluate(n).candidate_observation.payload_sha256,
                         evaluate(changed).candidate_observation.payload_sha256)

    def test_06_changed_S2_output_with_same_request_is_conflict(self):
        n=chain();old=evaluate(n).candidate_observation
        self.assertIs(evaluate(alter_visits(n),(old,)).status,
                      Status.REQUEST_CONFLICT_RECHECK_REQUIRED)

    def test_07_same_request_with_tampered_prior_digest_conflicts(self):
        n=chain();old=evaluate(n).candidate_observation
        tampered=replace(old,payload_sha256="e"*64)
        self.assertIs(evaluate(n,(tampered,)).status,
                      Status.REQUEST_CONFLICT_RECHECK_REQUIRED)

    def test_08_same_update_event_reissued_for_new_route_rejected(self):
        n=chain();old=evaluate(n).candidate_observation
        self.assertIs(evaluate(reissue(n,new_event_ids=False),(old,)).status,
                      Status.EVENT_ID_REUSE_RECHECK_REQUIRED)

    def test_09_same_scoped_key_on_fresh_route_rejected(self):
        n=chain();old=evaluate(n).candidate_observation
        self.assertIs(evaluate(reissue(n),(old,)).status,
                      Status.IDEMPOTENCY_KEY_RECHECK_REQUIRED)

    def test_10_separate_shop_with_distinct_chain_is_candidate(self):
        n=chain();old=evaluate(n).candidate_observation
        self.assertIs(evaluate(chain(),(old,)).status,
                      Status.NEW_CHAIN_CANDIDATE_ONLY)

    def test_11_prior_source_state_cannot_self_attest(self):
        n=chain();old=evaluate(n).candidate_observation
        self.assertIs(evaluate(n,(replace(old,source_state="S0_APPROVED"),)).status,
                      Status.PRIOR_OBSERVATIONS_RECHECK_REQUIRED)

    def test_12_bad_prior_schema_denied(self):
        n=chain();old=evaluate(n).candidate_observation
        self.assertIs(evaluate(n,(replace(old,schema="another-schema"),)).status,
                      Status.PRIOR_OBSERVATIONS_RECHECK_REQUIRED)

    def test_13_bad_prior_digest_denied(self):
        n=chain();old=evaluate(n).candidate_observation
        self.assertIs(evaluate(n,(replace(old,payload_sha256="zz"*32),)).status,
                      Status.PRIOR_OBSERVATIONS_RECHECK_REQUIRED)

    def test_14_duplicate_prior_request_conflicting_digest_denied(self):
        n=chain();old=evaluate(n).candidate_observation
        conflict=replace(old,payload_sha256="a"*64)
        self.assertIs(evaluate(n,(old,conflict)).status,
                      Status.PRIOR_OBSERVATIONS_RECHECK_REQUIRED)

    def test_15_prior_event_id_reused_for_different_route_denied(self):
        n=chain();old=evaluate(n).candidate_observation
        another=replace(old,route_id=uuid4())
        self.assertIs(evaluate(n,(old,another)).status,
                      Status.PRIOR_OBSERVATIONS_RECHECK_REQUIRED)

    def test_16_prior_scoped_key_colliding_across_requests_denied(self):
        n=chain();old=evaluate(n).candidate_observation
        other=replace(old,route_id=uuid4(),event_digests=())
        self.assertIs(evaluate(n,(old,other)).status,
                      Status.PRIOR_OBSERVATIONS_RECHECK_REQUIRED)

    def test_17_malformed_prior_tuple_denied(self):
        n=chain()
        self.assertIs(evaluate(n,[]).status,Status.DENIED_MALFORMED)

    def test_18_more_than_64_history_records_denied(self):
        n=chain();old=evaluate(n).candidate_observation
        history=(old,)*(MAX_PRIOR_OBSERVATIONS+1)
        self.assertIs(evaluate(n,history).status,Status.DENIED_MALFORMED)

    def test_19_prior_duplicate_event_id_in_one_record_denied(self):
        n=chain();old=evaluate(n).candidate_observation
        repeated=(old.event_digests[0],old.event_digests[0])
        self.assertIs(evaluate(n,(replace(old,event_digests=repeated),)).status,
                      Status.PRIOR_OBSERVATIONS_RECHECK_REQUIRED)

    def test_20_different_event_content_with_same_id_denied_in_history(self):
        n=chain();old=evaluate(n).candidate_observation
        events=list(old.event_digests)
        events[0]=(events[0][0],"c"*64)
        reused=replace(old,route_id=uuid4(),idempotency_key="DIFFERENT-KEY-123",
                       event_digests=tuple(events))
        self.assertIs(evaluate(n,(old,reused)).status,
                      Status.PRIOR_OBSERVATIONS_RECHECK_REQUIRED)

    def test_21_empty_version_chain_still_deterministic(self):
        # A33 fixture has no version_updates parameter; add it explicitly
        # before the separate prior_observations argument in A36.
        n=two_cycles()+((),)
        candidate=evaluate(n)
        self.assertIs(candidate.status,Status.NEW_CHAIN_CANDIDATE_ONLY)
        self.assertEqual(candidate.candidate_observation.event_digests,())
        self.assertIs(evaluate(n,(candidate.candidate_observation,)).status,
                      Status.IDENTICAL_REPLAY_NO_NEW_ACTION)

    def test_22_only_latest_human_episode_events_enter_event_receipt(self):
        n=two_epochs_with_updates()
        candidate=evaluate(n)
        self.assertIs(candidate.status,Status.NEW_CHAIN_CANDIDATE_ONLY)
        self.assertEqual(len(candidate.candidate_observation.event_digests),1)
        self.assertEqual(candidate.candidate_observation.event_digests[0][0],
                         n[9][-1].event_id)

    def test_23_broken_original_chain_never_emits_receipt(self):
        n=chain()
        updates=list(n[-1]);updates[1]=replace(updates[1],from_versions=(0,0,0,0,0))
        faulty=n[:-1]+(tuple(updates),)
        got=evaluate(faulty)
        self.assertIs(got.status,Status.ROUTE_OR_VERSION_RECHECK_REQUIRED)
        self.assertIsNone(got.candidate_observation)

    def test_24_missing_pinned_JS_source_denies_candidate(self):
        n=chain()
        with mock.patch("backend.f02_multiroute_s2_validation_candidate.S2_SOURCE",
                        Path("/tmp/_absent_e04_S2.mjs")):
            got=evaluate(n)
        self.assertIs(got.status,Status.ROUTE_OR_VERSION_RECHECK_REQUIRED)
        self.assertIsNone(got.candidate_observation)

    def test_25_version_marker_and_s2_data_are_in_payload(self):
        n=chain()
        old=evaluate(n).candidate_observation
        changed=alter_visits(n)
        new=evaluate(changed).candidate_observation
        self.assertIsNotNone(new)
        self.assertNotEqual(old.payload_sha256,new.payload_sha256)

    def test_26_no_message_send_and_no_authority_fields(self):
        r=evaluate(chain())
        self.assertEqual([f.name for f in fields(ReplayResult)],
                         ["status","candidate_observation"])
        self.assertTrue(all("APPROVED" not in s.value and
                            "AUTHORIZED" not in s.value and
                            "SEND" not in s.value for s in Status))

    def test_27_observation_identities_bind_to_final_human_episode(self):
        n=chain(); row=evaluate(n).candidate_observation
        self.assertEqual(row.route_id,n[0].route_id)
        self.assertEqual(row.shop_id,n[0].shop_id)
        self.assertEqual(row.closure_id,n[8][-1].closure_id)
        self.assertEqual(row.f03_event_id,n[8][-1].f03_event_id)
        self.assertEqual(row.f02_event_id,n[8][-1].f02_event_id)
        self.assertEqual(row.channel_id,n[3].channel_id)
        self.assertEqual(row.idempotency_key,n[3].idempotency_key)

    def test_28_no_replay_detection_without_supplied_prior(self):
        n=chain()
        a=evaluate(n);b=evaluate(n)
        self.assertIs(a.status,Status.NEW_CHAIN_CANDIDATE_ONLY)
        self.assertIs(b.status,Status.NEW_CHAIN_CANDIDATE_ONLY)

    def test_29_history_claim_without_actual_storage_is_untrusted(self):
        n=chain();row=evaluate(n).candidate_observation
        simulated=replace(row,payload_sha256="a"*64)
        self.assertIs(evaluate(n,(simulated,)).status,
                      Status.REQUEST_CONFLICT_RECHECK_REQUIRED)

    def test_30_revised_request_with_same_idempotency_key_never_authorized(self):
        n=chain();old=evaluate(n).candidate_observation
        modified=reissue(n)
        result=evaluate(modified,(old,))
        self.assertIs(result.status,Status.IDEMPOTENCY_KEY_RECHECK_REQUIRED)
        self.assertIsNone(result.candidate_observation)
