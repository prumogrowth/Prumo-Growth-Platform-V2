"""E04 A35 chained F03→F02 version claims. Synthetic, non-authorizing."""
import copy
import unittest
from dataclasses import fields, replace
from datetime import timedelta
from uuid import uuid4

from backend.f01_f02_f03_route_ledger_candidate import (
    RouteKind as K, RouteStatus, classify_route_candidate,
)
from backend.f02_multihuman_epoch_candidate import (
    EpochStatus as Status, HumanEpochResult, VersionTransitionClaim,
    MAX_UPDATES_PER_EPISODE, UNVERIFIED_VERSION_SOURCE,
    check_multi_human_epoch_candidate as check,
)
from backend.tests.test_f02_intraepoch_version_candidate import (
    with_change, V1, VERSION_NAMES,
)

MID_A=(1,2,4,4,5)
MID_B=(1,2,4,4,6)
FINAL=(1,2,4,5,6)


def chain(versions=(MID_A,FINAL)):
    """Replace existing A34 single-hop fixture with ordered hop chain."""
    if not versions:
        raise ValueError("At least one candidate hop is required")
    n=with_change(to_versions=versions[-1])
    scope,events,e,p,w,q,visits,person,epochs,old=n
    anchor=events[-2]
    f03=events[-3]
    end=events[-1]
    markers=[]
    tickets=[]
    previous=V1
    for i,version in enumerate(versions):
        marker=replace(anchor,event_id=uuid4(),
                       sequence=anchor.sequence+i,
                       occurred_at=f03.occurred_at+timedelta(seconds=10*(i+1)))
        markers.append(marker)
        tickets.append(replace(old[0],event_id=marker.event_id,
                               from_versions=previous,to_versions=version))
        previous=version
    end=replace(end,sequence=end.sequence+len(markers)-1)
    return (scope,events[:-2]+tuple(markers)+(end,),
            e,p,w,q,visits,person,epochs,tuple(tickets))


def updates(n,records):
    return n[:-1]+(records,)


def change(n,i,**kw):
    records=list(n[-1])
    records[i]=replace(records[i],**kw)
    return updates(n,tuple(records))


def event_change(n,i,**kw):
    events=list(n[1])
    events[i]=replace(events[i],**kw)
    return (n[0],tuple(events))+n[2:]


def visit_change(n,stage,index,field,value):
    visits=copy.deepcopy(n[6])
    chosen=[v for v in visits if v["stage"]==stage]
    chosen[index]["req"]["scope"]["current"][field]=value
    return n[:6]+(tuple(visits),)+n[7:]


def two_epochs_with_updates():
    """A35 extends A34 to allow a revision in both separate closures."""
    n=chain((MID_B,))
    scope,events,e,p,w,q,visits,person,claims,revisions=n
    events=list(events)
    first_f03=next(x for x in events if x.kind is K.F03_PROPOSAL)
    first_f02=next(x for x in events if x.kind is K.S0_F02_POSTHUMAN_REQUEST)
    pos=events.index(first_f02)
    marker=replace(first_f02,kind=K.S0_VERSION_UPDATE_CLAIM,
                   event_id=uuid4(),occurred_at=first_f03.occurred_at
                   +timedelta(minutes=10))
    for i in range(pos,len(events)):
        events[i]=replace(events[i],sequence=events[i].sequence+1)
    events.insert(pos,marker)
    first=VersionTransitionClaim(
        marker.event_id,scope.shop_id,scope.lead_id,scope.case_id,
        first_f03.closure_id,first_f03.event_id,first_f02.event_id,
        V1,MID_A)
    second=replace(revisions[0],from_versions=MID_A)
    claims=claims[:1]+(replace(claims[1],versions=MID_A),)
    visits=copy.deepcopy(visits)
    # The first posthuman F02 and the second F03 now read MID_A.
    post=[v for v in visits if v["stage"]=="F02"][-2]
    f03=[v for v in visits if v["stage"]=="F03"][-1]
    for v in (post,f03):
        for name,x in zip(VERSION_NAMES,MID_A):
            v["req"]["scope"]["expected"][name]=x
            v["req"]["scope"]["current"][name]=x
    return scope,tuple(events),e,p,w,q,tuple(visits),person,claims,(first,second)


class VersionChainTests(unittest.TestCase):
    def test_01_two_ordered_changes_work_without_S0_attestation(self):
        self.assertIs(check(*chain()).status,
                      Status.MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY)

    def test_02_three_ordered_changes_keep_original_F03_snapshot(self):
        n=chain((MID_A,MID_B,FINAL))
        self.assertEqual(n[6][-2]["req"]["scope"]["current"]["form"],3)
        self.assertEqual(n[6][-1]["req"]["scope"]["current"]["form"],4)
        self.assertIs(check(*n).status,Status.MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY)

    def test_03_A34_single_hop_still_works(self):
        self.assertIs(check(*with_change()).status,
                      Status.MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY)

    def test_04_original_without_revision_unchanged(self):
        from backend.tests.test_f02_multihuman_epoch_candidate import two_cycles
        self.assertIs(check(*two_cycles()).status,
                      Status.MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY)

    def test_05_claims_swapped_with_same_ids_are_not_accepted(self):
        n=chain()
        self.assertIs(check(*updates(n,n[-1][::-1])).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_06_middle_hop_source_does_not_match_previous_target(self):
        n=chain((MID_A,FINAL))
        self.assertIs(check(*change(n,1,from_versions=V1)).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_07_first_hop_does_not_start_from_F03_snapshot(self):
        n=chain()
        self.assertIs(check(*change(n,0,from_versions=MID_B)).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_08_final_F02_snapshot_must_equal_last_hop_target(self):
        n=chain()
        self.assertIs(check(*change(n,1,to_versions=MID_B)).status,
                      Status.VERSION_RECHECK_REQUIRED)

    def test_09_missing_first_claim_denied(self):
        n=chain()
        self.assertIs(check(*updates(n,n[-1][1:])).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_10_missing_second_claim_denied(self):
        n=chain()
        self.assertIs(check(*updates(n,n[-1][:1])).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_11_duplicate_claim_id_denied(self):
        n=chain()
        self.assertIs(check(*updates(n,(n[-1][0],n[-1][0]))).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_12_duplicate_ledger_event_denied(self):
        n=chain()
        self.assertIs(check(*event_change(n,-2,
            event_id=n[1][-3].event_id)).status,
            Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_13_wrong_tenant_in_middle_update_denied(self):
        n=chain((MID_A,MID_B,FINAL))
        self.assertIs(check(*change(n,1,shop_id=uuid4())).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_14_wrong_lead_in_middle_update_denied(self):
        n=chain((MID_A,MID_B,FINAL))
        self.assertIs(check(*change(n,1,lead_id=uuid4())).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_15_wrong_case_in_middle_update_denied(self):
        n=chain((MID_A,MID_B,FINAL))
        self.assertIs(check(*change(n,1,case_id=uuid4())).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_16_wrong_human_closure_in_middle_update_denied(self):
        n=chain((MID_A,MID_B,FINAL))
        self.assertIs(check(*change(n,1,closure_id=uuid4())).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_17_wrong_F03_visit_in_middle_update_denied(self):
        n=chain((MID_A,MID_B,FINAL))
        self.assertIs(check(*change(n,1,f03_event_id=uuid4())).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_18_wrong_F02_visit_in_middle_update_denied(self):
        n=chain((MID_A,MID_B,FINAL))
        self.assertIs(check(*change(n,1,f02_event_id=uuid4())).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_19_unverified_source_cannot_self_attest(self):
        n=chain()
        self.assertIs(check(*change(n,1,source_state="S0_SIGNED")).status,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED)

    def test_20_no_op_middle_hop_denied(self):
        n=chain((MID_A,MID_B,FINAL))
        self.assertIs(check(*change(n,1,to_versions=MID_A)).status,
                      Status.VERSION_REGRESSION_RECHECK_REQUIRED)

    def test_21_regressive_middle_hop_denied(self):
        n=chain((MID_A,MID_B,FINAL))
        self.assertIs(check(*change(n,1,to_versions=V1)).status,
                      Status.VERSION_REGRESSION_RECHECK_REQUIRED)

    def test_22_wrong_ledger_event_order_denied(self):
        n=chain()
        self.assertIs(check(*event_change(n,-2,
           sequence=n[1][-3].sequence)).status,
           Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_23_earlier_ledger_timestamp_denied(self):
        n=chain()
        self.assertIs(check(*event_change(n,-2,
           occurred_at=n[1][-3].occurred_at-timedelta(seconds=1))).status,
           Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_24_last_F02_without_update_chain_denied(self):
        n=chain()
        ev=n[1][:-3]+(replace(n[1][-1],
                                  sequence=n[1][-1].sequence-2),)
        candidate=n[:1]+(ev,)+n[2:-1]+((),)
        self.assertIs(check(*candidate).status,Status.VERSION_RECHECK_REQUIRED)

    def test_25_revision_marker_cannot_be_after_F02(self):
        n=chain()
        events=n[1][:-2]+(n[1][-1],n[1][-2])
        self.assertIs(check(*(n[:1]+(events,)+n[2:])).status,
                      Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_26_change_between_two_separate_human_closures(self):
        self.assertIs(check(*two_epochs_with_updates()).status,
                      Status.MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY)

    def test_27_cross_human_epoch_regression_denied(self):
        n=two_epochs_with_updates()
        claims=n[8][:1]+(replace(n[8][1],versions=V1),)
        self.assertIn(check(*(n[:8]+(claims,n[9]))).status,(
                      Status.VERSION_RECHECK_REQUIRED,
                      Status.VERSION_UPDATE_RECHECK_REQUIRED,
                      Status.VERSION_REGRESSION_RECHECK_REQUIRED))

    def test_28_valid_16_hop_lab_cap(self):
        stages=tuple((1,2,3+i,4,5) for i in range(1,MAX_UPDATES_PER_EPISODE+1))
        self.assertIs(check(*chain(stages)).status,
                      Status.MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY)

    def test_29_excessive_17_hop_lab_cap_denied(self):
        stages=tuple((1,2,3+i,4,5) for i in range(1,MAX_UPDATES_PER_EPISODE+2))
        self.assertIs(check(*chain(stages)).status,
                      Status.VERSION_UPDATE_CHAIN_LIMIT_RECHECK_REQUIRED)

    def test_30_wrong_F02_S2_version_recheck(self):
        n=visit_change(chain(),"F02",-1,"form",999)
        self.assertIs(check(*n).status,Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_31_F03_withdrawal_advisory_holds_even_with_updates(self):
        n=chain()
        visits=copy.deepcopy(n[6])
        step=[x for x in visits if x["stage"]=="F03"][-1]
        step["req"]["verifiedWithdrawalSourceIds"]=["m7"]
        step["proposal"]["commercialAdvisory"]={
            "kind":"perdido","sourceIds":["m7"]}
        self.assertIs(check(*(n[:6]+(tuple(visits),)+n[7:])).status,
                      Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_32_missing_source_JS_checkout_holds(self):
        from pathlib import Path
        from unittest import mock
        n=chain()
        with mock.patch("backend.f02_multiroute_s2_validation_candidate.S2_SOURCE",
                       Path("/tmp/nonexistent-s2-pinned.mjs")):
            self.assertIs(check(*n).status,
                          Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_33_no_operational_authorization_in_result(self):
        r=check(*chain())
        self.assertEqual([f.name for f in fields(HumanEpochResult)],["status"])
        self.assertTrue(all("APPROVED" not in x.value and
                            "SEND" not in x.value and
                            "AUTHORIZED" not in x.value for x in Status))
        self.assertEqual(chain()[-1][0].source_state,
                         UNVERIFIED_VERSION_SOURCE)
