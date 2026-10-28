"""E04 intra-epoch version claims: F03 → S0 revision marker → F02 (lab only)."""
import copy
import unittest
from dataclasses import fields, replace
from datetime import timedelta
from uuid import uuid4

from backend.f01_f02_f03_route_ledger_candidate import (
    RouteKind as K, RouteStatus, classify_route_candidate,
)
from backend.f02_multihuman_epoch_candidate import (
    HumanEpochResult, EpochStatus as Status,
    HumanEpochClaim, VersionTransitionClaim, UNVERIFIED_VERSION_SOURCE,
    check_multi_human_epoch_candidate as check,
)
from backend.tests.test_f02_multihuman_epoch_candidate import (
    two_cycles, V1, V2, VERSION_NAMES,
)

UPDATED=(1,2,4,4,6)


def with_change(*, from_versions=V1, to_versions=UPDATED):
    n=two_cycles(second_versions=from_versions)
    scope,events,e,p,w,q,visits,person,claims=n
    next_visits=copy.deepcopy(visits)
    for key,version in zip(VERSION_NAMES,to_versions):
        next_visits[-1]["req"]["scope"]["expected"][key]=version
        next_visits[-1]["req"]["scope"]["current"][key]=version
    last=events[-1]
    revision=replace(last,kind=K.S0_VERSION_UPDATE_CLAIM,
                     event_id=uuid4(),
                     occurred_at=events[-2].occurred_at+timedelta(minutes=10))
    final=replace(last,sequence=last.sequence+1)
    events=events[:-1]+(revision,final)
    ticket=VersionTransitionClaim(
        event_id=revision.event_id, shop_id=scope.shop_id,
        lead_id=scope.lead_id, case_id=scope.case_id,
        closure_id=last.closure_id, f03_event_id=events[-3].event_id,
        f02_event_id=final.event_id,
        from_versions=from_versions,to_versions=to_versions)
    return (scope,events,e,p,w,q,tuple(next_visits),person,claims,(ticket,))


def replace_updates(n,updates):
    return n[:-1]+(updates,)


def update_ticket(n,**changes):
    return replace_updates(n,(replace(n[-1][0],**changes),))


class IntraEpochVersionTests(unittest.TestCase):
    def test_01_new_versions_between_F03_and_F02_accepted_as_claim_only(self):
        n=with_change()
        self.assertIs(check(*n).status,
                      Status.MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY)

    def test_02_unmodified_A33_route_still_accepted(self):
        n=two_cycles()
        self.assertIs(check(*n).status,
                      Status.MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY)

    def test_03_marker_without_claim_is_denied(self):
        n=with_change()
        self.assertIs(check(*replace_updates(n,())).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_04_claim_without_marker_is_denied(self):
        n=with_change()
        ev=n[1]
        # Restore event sequence; do not modify the F02 identity.
        final=replace(ev[-1],sequence=ev[-1].sequence-1)
        self.assertIs(check(*(n[:1]+(ev[:-2]+(final,),)+n[2:])).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_05_changed_F02_versions_without_marker_are_rejected(self):
        n=with_change()
        ev=n[1]; final=replace(ev[-1],sequence=ev[-1].sequence-1)
        scenario=n[:1]+(ev[:-2]+(final,),)+n[2:-1]+((),)
        self.assertIs(check(*scenario).status,
                      Status.VERSION_RECHECK_REQUIRED)

    def test_06_wrong_store_in_version_claim(self):
        self.assertIs(check(*update_ticket(with_change(),shop_id=uuid4())).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_07_wrong_lead_in_version_claim(self):
        self.assertIs(check(*update_ticket(with_change(),lead_id=uuid4())).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_08_wrong_case_in_version_claim(self):
        self.assertIs(check(*update_ticket(with_change(),case_id=uuid4())).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_09_wrong_human_closure_in_claim(self):
        self.assertIs(check(*update_ticket(with_change(),closure_id=uuid4())).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_10_claim_bound_to_wrong_F03(self):
        self.assertIs(check(*update_ticket(with_change(),f03_event_id=uuid4())).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_11_claim_bound_to_wrong_F02(self):
        self.assertIs(check(*update_ticket(with_change(),f02_event_id=uuid4())).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_12_claim_wrong_ledger_event_id(self):
        self.assertIs(check(*update_ticket(with_change(),event_id=uuid4())).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_13_false_S0_authenticity_label_not_accepted(self):
        self.assertIs(check(*update_ticket(with_change(),
                      source_state="S0_VERIFIED")).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_14_old_snapshot_does_not_match_claimed_from_versions(self):
        n=with_change()
        self.assertIs(check(*update_ticket(n,from_versions=V2)).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_15_F02_snapshot_changed_after_claim(self):
        n=with_change()
        self.assertIs(check(*update_ticket(n,to_versions=V2)).status,
                      Status.VERSION_RECHECK_REQUIRED)

    def test_16_downward_version_update_does_not_pass(self):
        n=with_change(from_versions=V2,to_versions=(1,3,4,5,7))
        self.assertIs(check(*n).status,
                      Status.VERSION_REGRESSION_RECHECK_REQUIRED)

    def test_17_no_op_update_marker_does_not_pass(self):
        n=with_change(to_versions=V1)
        self.assertIs(check(*n).status,
                      Status.VERSION_REGRESSION_RECHECK_REQUIRED)

    def test_18_bad_bool_or_float_version_denied(self):
        n=with_change()
        for versions in ((True,2,4,4,6),(1,2,4.0,4,6),(1,2)):
            with self.subTest(versions=versions):
                self.assertIs(check(*update_ticket(n,to_versions=versions)).status,
                              Status.DENIED_MALFORMED)

    def test_19_duplicate_update_ticket_does_not_pass(self):
        n=with_change()
        self.assertIs(check(*replace_updates(n,(n[-1][0],n[-1][0]))).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_20_duplicate_revision_event_does_not_pass(self):
        n=with_change()
        ev=n[1]
        extra=replace(ev[-2],event_id=uuid4(),
                      sequence=ev[-1].sequence,
                      occurred_at=ev[-2].occurred_at+timedelta(minutes=2))
        final=replace(ev[-1],sequence=ev[-1].sequence+1)
        other=ev[:-1]+(extra,final)
        self.assertIs(check(*(n[:1]+(other,)+n[2:])).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_21_revision_before_F03_refused_by_route(self):
        n=with_change()
        ev=n[1]
        # Place the version marker at the second F03 position instead.
        revision=replace(ev[-2],occurred_at=ev[-3].occurred_at,
                         sequence=ev[-3].sequence)
        f03=replace(ev[-3],sequence=ev[-3].sequence+1,
                    occurred_at=ev[-3].occurred_at+timedelta(minutes=1))
        bad=ev[:-3]+(revision,f03,ev[-1])
        self.assertIs(check(*(n[:1]+(bad,)+n[2:])).status,
                      Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_22_revision_after_F02_refused_by_route(self):
        n=with_change()
        ev=n[1]
        final=replace(ev[-1],sequence=ev[-2].sequence,
                      occurred_at=ev[-2].occurred_at)
        revision=replace(ev[-2],sequence=final.sequence+1,
                         occurred_at=final.occurred_at+timedelta(minutes=1))
        bad=ev[:-2]+(final,revision)
        self.assertIs(check(*(n[:1]+(bad,)+n[2:])).status,
                      Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_23_revision_marker_wrong_closure_denied(self):
        n=with_change()
        ev=n[1]
        wrong=replace(ev[-2],closure_id=uuid4())
        self.assertIs(check(*(n[:1]+(ev[:-2]+(wrong,ev[-1]),)+n[2:])).status,
                      Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_24_S2_F02_stale_current_version_fails_before_new_guard(self):
        n=with_change()
        visits=copy.deepcopy(n[6])
        visits[-1]["req"]["scope"]["current"]["form"]=999
        self.assertIs(check(*(n[:6]+(tuple(visits),)+n[7:])).status,
                      Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_25_new_F03_loss_advisory_still_blocks_F02(self):
        n=with_change()
        visits=copy.deepcopy(n[6])
        visits[-2]["req"]["verifiedWithdrawalSourceIds"]=["m7"]
        visits[-2]["proposal"]["commercialAdvisory"]={
            "kind":"perdido","sourceIds":["m7"]}
        self.assertIs(check(*(n[:6]+(tuple(visits),)+n[7:])).status,
                      Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_26_optout_instead_of_revision_is_terminal(self):
        n=with_change()
        ev=n[1]
        replaced=replace(ev[-2],kind=K.OPT_OUT)
        self.assertIs(check(*(n[:1]+(ev[:-2]+(replaced,ev[-1]),)+n[2:])).status,
                      Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_27_original_F03_may_keep_old_versions_if_update_is_declared(self):
        n=with_change()
        self.assertNotEqual(n[-1][0].from_versions,n[-1][0].to_versions)
        self.assertEqual(n[6][-2]["req"]["scope"]["current"]["form"],3)
        self.assertEqual(n[6][-1]["req"]["scope"]["current"]["form"],4)
        self.assertIs(check(*n).status,
                      Status.MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY)

    def test_28_event_route_without_F02_remains_F03_phase(self):
        n=with_change()
        scope,ev=n[0],n[1]
        partial=classify_route_candidate(scope,ev[:-1])
        self.assertEqual(partial.current_stage.value,"F03")
        self.assertIs(partial.status,RouteStatus.ROUTE_SHAPE_RECHECK_ONLY)

    def test_29_source_claim_cannot_grant_right_to_send(self):
        from backend.f02_multihuman_epoch_candidate import EpochStatus
        n=with_change()
        result=check(*n)
        self.assertEqual([f.name for f in fields(HumanEpochResult)],["status"])
        self.assertTrue(all("SEND" not in x.value
                            and "AUTHORIZED" not in x.value
                            and "APPROVED" not in x.value
                            for x in EpochStatus))
        self.assertEqual(n[-1][0].source_state,UNVERIFIED_VERSION_SOURCE)

    def test_30_malformed_version_updates_type_denied(self):
        n=with_change()
        for malformed in (None,[],{},("bogus",)):
            self.assertIs(check(*replace_updates(n,malformed)).status,
                          Status.DENIED_MALFORMED)

    def test_31_invalid_version_marker_time_order_rejected(self):
        n=with_change()
        ev=n[1]
        bad=replace(ev[-2],occurred_at=ev[-3].occurred_at-timedelta(seconds=1))
        self.assertIs(check(*(n[:1]+(ev[:-2]+(bad,ev[-1]),)+n[2:])).status,
                      Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_32_missing_first_epoch_claim_still_rejected(self):
        n=with_change()
        claims=(n[8][-1],)
        self.assertIs(check(*(n[:8]+(claims,n[9]))).status,
                      Status.EPISODE_RECHECK_REQUIRED)
