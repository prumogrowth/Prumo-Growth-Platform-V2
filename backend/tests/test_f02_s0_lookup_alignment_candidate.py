"""E04 A37: proposed read-only S0 result alignment, not authenticated lookup."""
import unittest
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
from uuid import uuid4

from backend.f02_s0_lookup_alignment_candidate import (
    SOURCE, PINNED_S0_SCHEMA, LookupBindingClaim, LookupGate as Gate,
    S0LookupAlignment, inspect_s0_lookup_alignment_candidate as inspect,
)
from backend.tests.test_f02_version_chain_candidate import chain
from backend.tests.test_f02_version_chain_replay_candidate import evaluate


def case():
    n=chain()
    observation=evaluate(n).candidate_observation
    assert observation is not None
    bind=LookupBindingClaim(
        shop_id=observation.shop_id, lead_id=observation.lead_id,
        case_id=observation.case_id, closure_id=observation.closure_id,
        channel_id=observation.channel_id,
        idempotency_key=observation.idempotency_key,
        route_id=observation.route_id,
        f03_event_id=observation.f03_event_id,
        f02_event_id=observation.f02_event_id,
    )
    sha="a"*64
    now=datetime(2026,11,2,12,tzinfo=timezone.utc)
    projection={
        "schema":PINNED_S0_SCHEMA,
        "state":"CURRENT_REVIEW_ONLY",
        "review_ref":str(uuid4()),
        "revision":"1",
        "observed_at":now.isoformat(),
        "request_sha256":sha,
        "expires_at":(now+timedelta(hours=5)).isoformat(),
        "evidence_scope":"CFI_CONTEXT_ONLY_F02_EVIDENCE_PENDING",
        "human_ratification":"NOT_IMPLEMENTED_CONTRACT_PENDING",
        "send_authorized":False,
        "scheduling_authorized":False,
        "commercial_transition_authorized":False,
    }
    return observation,bind,projection,sha


def run(change=None, *, before=None, original=None, bind=None, sha=None):
    obs,b,p,h=case()
    if change is not None: p=change(p)
    return inspect(original or obs,bind or b,p,expected_s0_request_sha256=sha or h,
                   previous_result=before)


class S0LookupAlignmentTests(unittest.TestCase):
    def test_01_current_S0_shape_is_only_review_candidate(self):
        self.assertIs(run().status,Gate.PERSISTED_SHAPE_RECHECK_ONLY)

    def test_02_distinct_F02_and_S0_hashes_must_not_be_equated(self):
        obs,b,p,s=case()
        self.assertNotEqual(obs.payload_sha256,s)
        self.assertIs(inspect(obs,b,p,expected_s0_request_sha256=s).status,
                      Gate.PERSISTED_SHAPE_RECHECK_ONLY)
        self.assertIs(inspect(obs,b,p,expected_s0_request_sha256=obs.payload_sha256).status,
                      Gate.S0_REQUEST_DIGEST_RECHECK_REQUIRED)

    def test_03_recorded_state_only_review(self):
        self.assertIs(run(lambda p:{**p,"state":"RECORDED_REVIEW_ONLY"}).status,
                      Gate.PERSISTED_SHAPE_RECHECK_ONLY)

    def test_04_replayed_state_only_review(self):
        self.assertIs(run(lambda p:{**p,"state":"REPLAY_REVIEW_ONLY"}).status,
                      Gate.PERSISTED_SHAPE_RECHECK_ONLY)

    def test_05_withdrawn_state_stays_terminal(self):
        self.assertIs(run(lambda p:{**p,"state":"WITHDRAWN_REVIEW_ONLY"}).status,
                      Gate.TERMINAL_REVIEW_HOLD)

    def test_06_expired_state_stays_terminal(self):
        self.assertIs(run(lambda p:{**p,"state":"EXPIRED_REVIEW_ONLY"}).status,
                      Gate.TERMINAL_REVIEW_HOLD)

    def test_07_all_eight_negative_states_hold(self):
        for state in ("INPUT_REJECTED","DENIED","STALE","IDEMPOTENCY_CONFLICT",
                      "REQUEST_EXPIRED","REVIEW_REQUEST_NOT_FOUND",
                      "CLOCK_RECHECK_REQUIRED","UNAVAILABLE"):
            with self.subTest(state=state):
                def negative(p):
                    return {**p,"state":state,"review_ref":None,
                            "revision":None,"observed_at":None,
                            "request_sha256":None,"expires_at":None}
                self.assertIs(run(negative).status,Gate.NEGATIVE_REVIEW_HOLD)

    def test_08_negative_result_with_fake_review_ref_denied(self):
        self.assertIs(run(lambda p:{**p,"state":"DENIED"}).status,
                      Gate.S0_RESULT_CONTRACT_RECHECK_REQUIRED)

    def test_09_s0_never_sets_send_flag_true(self):
        for field in ("send_authorized","scheduling_authorized",
                      "commercial_transition_authorized"):
            with self.subTest(field=field):
                self.assertIs(run(lambda p:{**p,field:True}).status,
                              Gate.S0_RESULT_CONTRACT_RECHECK_REQUIRED)

    def test_10_unexpected_S0_property_denied(self):
        self.assertIs(run(lambda p:{**p,"authenticated":True}).status,
                      Gate.S0_RESULT_CONTRACT_RECHECK_REQUIRED)

    def test_11_unratified_S0_schema_drift_denied(self):
        self.assertIs(run(lambda p:{**p,"schema":"prumo.s0.f02.review.result/1.0"}).status,
                      Gate.S0_RESULT_CONTRACT_RECHECK_REQUIRED)

    def test_12_wrong_S0_request_digest_denied(self):
        self.assertIs(run(lambda p:{**p,"request_sha256":"b"*64}).status,
                      Gate.S0_REQUEST_DIGEST_RECHECK_REQUIRED)

    def test_13_provided_previous_revision_advances(self):
        obs,b,current,sha=case()
        earlier=dict(current,state="RECORDED_REVIEW_ONLY",revision="1")
        current=dict(current,revision="2",
                     observed_at=(datetime.fromisoformat(current["observed_at"])
                                  +timedelta(minutes=1)).isoformat())
        self.assertIs(inspect(obs,b,current,expected_s0_request_sha256=sha,
                             previous_result=earlier).status,
                      Gate.PERSISTED_SHAPE_RECHECK_ONLY)

    def test_14_previous_revision_cannot_regress(self):
        obs,b,current,sha=case()
        previous=dict(current,revision="5")
        self.assertIs(inspect(obs,b,current,expected_s0_request_sha256=sha,
                             previous_result=previous).status,
                      Gate.S0_RESULT_CONTINUITY_RECHECK_REQUIRED)

    def test_15_observation_clock_cannot_regress(self):
        obs,b,current,sha=case()
        previous=dict(current,observed_at=(
            datetime.fromisoformat(current["observed_at"])
            +timedelta(minutes=1)).isoformat())
        self.assertIs(inspect(obs,b,current,expected_s0_request_sha256=sha,
                             previous_result=previous).status,
                      Gate.S0_RESULT_CONTINUITY_RECHECK_REQUIRED)

    def test_16_withdrawn_cannot_be_reactivated(self):
        obs,b,current,sha=case()
        previous=dict(current,state="WITHDRAWN_REVIEW_ONLY")
        self.assertIs(inspect(obs,b,current,expected_s0_request_sha256=sha,
                             previous_result=previous).status,
                      Gate.S0_RESULT_CONTINUITY_RECHECK_REQUIRED)

    def test_17_previous_persisted_cannot_disappear_into_unavailable(self):
        obs,b,current,sha=case()
        previous=dict(current)
        negative=dict(current,state="UNAVAILABLE",review_ref=None,
                      revision=None,observed_at=None,request_sha256=None,
                      expires_at=None)
        self.assertIs(inspect(obs,b,negative,expected_s0_request_sha256=sha,
                             previous_result=previous).status,
                      Gate.S0_RESULT_CONTINUITY_RECHECK_REQUIRED)

    def test_18_previous_result_different_review_ref_denied(self):
        obs,b,current,sha=case()
        previous=dict(current,review_ref=str(uuid4()))
        self.assertIs(inspect(obs,b,current,expected_s0_request_sha256=sha,
                             previous_result=previous).status,
                      Gate.S0_RESULT_CONTINUITY_RECHECK_REQUIRED)

    def test_19_previous_result_wrong_request_digest_denied(self):
        obs,b,current,sha=case()
        previous=dict(current,request_sha256="b"*64)
        self.assertIs(inspect(obs,b,current,expected_s0_request_sha256=sha,
                             previous_result=previous).status,
                      Gate.S0_REQUEST_DIGEST_RECHECK_REQUIRED)

    def test_20_claimed_cross_shop_denied(self):
        obs,b,p,sha=case()
        self.assertIs(inspect(obs,replace(b,shop_id=uuid4()),p,
                             expected_s0_request_sha256=sha).status,
                      Gate.CLAIM_SCOPE_RECHECK_REQUIRED)

    def test_21_claimed_cross_lead_denied(self):
        obs,b,p,sha=case()
        self.assertIs(inspect(obs,replace(b,lead_id=uuid4()),p,
                             expected_s0_request_sha256=sha).status,
                      Gate.CLAIM_SCOPE_RECHECK_REQUIRED)

    def test_22_claimed_cross_case_denied(self):
        obs,b,p,sha=case()
        self.assertIs(inspect(obs,replace(b,case_id=uuid4()),p,
                             expected_s0_request_sha256=sha).status,
                      Gate.CLAIM_SCOPE_RECHECK_REQUIRED)

    def test_23_claimed_cross_closure_denied(self):
        obs,b,p,sha=case()
        self.assertIs(inspect(obs,replace(b,closure_id=uuid4()),p,
                             expected_s0_request_sha256=sha).status,
                      Gate.CLAIM_SCOPE_RECHECK_REQUIRED)

    def test_24_claimed_cross_channel_denied(self):
        obs,b,p,sha=case()
        self.assertIs(inspect(obs,replace(b,channel_id=uuid4()),p,
                             expected_s0_request_sha256=sha).status,
                      Gate.CLAIM_SCOPE_RECHECK_REQUIRED)

    def test_25_claimed_key_reuse_denied(self):
        obs,b,p,sha=case()
        self.assertIs(inspect(obs,replace(b,idempotency_key="OTHER-KEY-001"),p,
                             expected_s0_request_sha256=sha).status,
                      Gate.CLAIM_SCOPE_RECHECK_REQUIRED)

    def test_26_claimed_cross_route_denied(self):
        obs,b,p,sha=case()
        self.assertIs(inspect(obs,replace(b,route_id=uuid4()),p,
                             expected_s0_request_sha256=sha).status,
                      Gate.CLAIM_SCOPE_RECHECK_REQUIRED)

    def test_27_claimed_fake_source_grant_denied(self):
        obs,b,p,sha=case()
        self.assertIs(inspect(obs,replace(b,candidate_source="S0_SIGNED"),p,
                             expected_s0_request_sha256=sha).status,
                      Gate.CLAIM_SCOPE_RECHECK_REQUIRED)

    def test_28_expired_observation_is_not_reviewable(self):
        self.assertIs(run(lambda p:{**p,"observed_at":p["expires_at"]}).status,
                      Gate.S0_RESULT_CONTINUITY_RECHECK_REQUIRED)

    def test_29_newly_forged_approval_state_denied(self):
        self.assertIs(run(lambda p:{**p,"state":"APPROVED"}).status,
                      Gate.S0_RESULT_CONTRACT_RECHECK_REQUIRED)

    def test_30_bad_request_sha_input_denied(self):
        self.assertIs(run(sha="z"*64).status,Gate.DENIED_MALFORMED)

    def test_31_offset_equivalent_previous_expiry_is_same_instant(self):
        obs,b,current,sha=case()
        previous=dict(current,
            expires_at=datetime.fromisoformat(current["expires_at"])
            .astimezone(timezone(timedelta(hours=-3))).isoformat())
        self.assertIs(inspect(obs,b,current,expected_s0_request_sha256=sha,
                             previous_result=previous).status,
                      Gate.PERSISTED_SHAPE_RECHECK_ONLY)

    def test_32_f02_projector_schema_still_matches_pinned_document(self):
        root=Path(__file__).resolve().parents[2]
        path=root/"docs/contracts/upstream/OAI_S0_F02_REVIEW_RESULT_SCHEMA_0_1_PINNED.json"
        schema=json.loads(path.read_text())
        self.assertEqual(schema["$id"],PINNED_S0_SCHEMA)
        self.assertEqual(set(schema["properties"]["state"]["enum"]), {
            "RECORDED_REVIEW_ONLY","REPLAY_REVIEW_ONLY","CURRENT_REVIEW_ONLY",
            "WITHDRAWN_REVIEW_ONLY","EXPIRED_REVIEW_ONLY","INPUT_REJECTED",
            "DENIED","STALE","IDEMPOTENCY_CONFLICT","REQUEST_EXPIRED",
            "REVIEW_REQUEST_NOT_FOUND","CLOCK_RECHECK_REQUIRED","UNAVAILABLE"})
        self.assertTrue(all(schema["properties"][k]["const"] is False
            for k in ("send_authorized","scheduling_authorized",
                      "commercial_transition_authorized")))

    def test_33_no_authority_fields_in_result(self):
        self.assertEqual([f.name for f in fields(S0LookupAlignment)],["status"])
        self.assertTrue(all("AUTHORIZED" not in x.value and
                            "APPROVED" not in x.value and
                            "SEND" not in x.value for x in Gate))

    def test_34_history_absent_is_not_proof_of_authentic_lookup(self):
        self.assertIs(run().status,Gate.PERSISTED_SHAPE_RECHECK_ONLY)
        self.assertEqual(SOURCE,"F02_UNVERIFIED_READ_ONLY_S0_LOOKUP_CLAIM")

    def test_35_terminal_remains_terminal_even_after_expiry(self):
        self.assertIs(run(lambda p:{**p,"state":"EXPIRED_REVIEW_ONLY",
                       "observed_at":p["expires_at"]}).status,
                      Gate.TERMINAL_REVIEW_HOLD)
