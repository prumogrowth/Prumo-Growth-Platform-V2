"""E04 multiple human episodes: pinned S2 JS and F02 proof at each cycle.

All actors/events/version readings are synthetic. No S0 or Meta authority.
"""
import copy
import unittest
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
from uuid import uuid4

from backend.f01_f02_f03_route_ledger_candidate import RouteKind as K
from backend.f02_multihuman_epoch_candidate import (
    EpochStatus as Status, HumanEpochClaim, HumanEpochResult,
    check_multi_human_epoch_candidate as check,
)
from backend.f02_reconciled_human_authorization_handoff import prepare_handoff
from backend.tests.test_f02_multiroute_s2_validation_candidate import fixture

VERSION_NAMES=("case","cycle","form","catalog","assignment")
V1=(1,2,3,4,5)
V2=(2,3,4,5,6)


def two_cycles(*, second_versions=V2):
    scope,events,e,p,w,q,visits,person = fixture()
    old_id=e.closure_id
    new_id=uuid4()
    close_at=datetime.fromisoformat(q["closure_at"])
    last=events[-1]
    extra=[]
    new_events=[
        (K.CUSTOMER_INBOUND,60,old_id),
        (K.S0_HUMAN_REOPEN_REQUEST,65,old_id),
        (K.S0_HUMAN_CLOSURE,120,new_id),
        (K.F03_PROPOSAL,130,new_id),
        (K.S0_F02_POSTHUMAN_REQUEST,150,new_id),
    ]
    for index,(kind,minute,closure_id) in enumerate(new_events,1):
        extra.append(replace(last,
            event_id=uuid4(),sequence=last.sequence+index,
            occurred_at=close_at+timedelta(minutes=minute),
            kind=kind,closure_id=closure_id))

    current=copy.deepcopy(q)
    current["closure_at"]=extra[2].occurred_at.isoformat()
    current["scope"]["closure_id"]=str(new_id)
    for idx,record in enumerate(current["proofs"].values(),1):
        record["scope"]["closure_id"]=str(new_id)
        observed=extra[2].occurred_at+timedelta(hours=idx)
        record["observed_at"]=observed.isoformat()
        record["cutoff_at"]=(observed+timedelta(minutes=15)).isoformat()
    newest_e=replace(e,closure_id=new_id)
    newest_p=replace(p,closure_id=new_id)
    current["handoff_sha256"]=prepare_handoff(
        newest_e,newest_p).untrusted_request_sha256
    updated=copy.deepcopy(list(visits))
    second_f03=copy.deepcopy(updated[-2])
    second_f02=copy.deepcopy(updated[-1])
    second_f03["req"]["closureId"]=str(new_id)
    for visit in (second_f03,second_f02):
        for key,value in zip(VERSION_NAMES,second_versions):
            visit["req"]["scope"]["expected"][key]=value
            visit["req"]["scope"]["current"][key]=value
    updated.extend([second_f03,second_f02])
    epochs=(
        HumanEpochClaim(old_id,events[-3].event_id,events[-2].event_id,
                        events[-1].event_id,V1),
        HumanEpochClaim(new_id,extra[2].event_id,extra[3].event_id,
                        extra[4].event_id,second_versions),
    )
    return (scope,events+tuple(extra),newest_e,newest_p,w,current,
            tuple(updated),person,epochs)


def alter_visit(n, stage, section, func, nth=-1):
    steps=copy.deepcopy(n[6])
    inds=[i for i,x in enumerate(steps) if x["stage"]==stage]
    if not inds:raise AssertionError("missing stage")
    func(steps[inds[nth]][section])
    return n[:6]+(tuple(steps),)+n[7:]


def replace_epochs(n,new):
    return n[:-1]+(new,)


class MultiHumanEpochTests(unittest.TestCase):
    def test_01_two_human_closures_with_updated_versions(self):
        self.assertIs(check(*two_cycles()).status,
                      Status.MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY)

    def test_02_distinct_closures_need_not_increment_versions_automatically(self):
        self.assertIs(check(*two_cycles(second_versions=V1)).status,
                      Status.MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY)

    def test_03_old_closure_proof_cannot_be_reused_for_second(self):
        n=two_cycles()
        old=replace(n[2],closure_id=n[-1][0].closure_id)
        self.assertIs(check(*(n[:2]+(old,)+n[3:])).status,
                      Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_04_missing_first_epoch_ticket(self):
        n=two_cycles()
        self.assertIs(check(*replace_epochs(n,(n[-1][-1],))).status,
                      Status.EPISODE_RECHECK_REQUIRED)

    def test_05_replayed_epoch_ticket(self):
        n=two_cycles()
        self.assertIs(check(*replace_epochs(n,(n[-1][0],n[-1][0]))).status,
                      Status.EPISODE_RECHECK_REQUIRED)

    def test_06_wrong_second_F03_event_id(self):
        n=two_cycles()
        claims=n[-1][:-1]+(replace(n[-1][-1],f03_event_id=uuid4()),)
        self.assertIs(check(*replace_epochs(n,claims)).status,
                      Status.EPISODE_RECHECK_REQUIRED)

    def test_07_wrong_first_F02_event_id(self):
        n=two_cycles()
        claims=(replace(n[-1][0],f02_event_id=uuid4()),n[-1][1])
        self.assertIs(check(*replace_epochs(n,claims)).status,
                      Status.EPISODE_RECHECK_REQUIRED)

    def test_08_swapped_epoch_ticket_order(self):
        n=two_cycles()
        self.assertIs(check(*replace_epochs(n,n[-1][::-1])).status,
                      Status.EPISODE_RECHECK_REQUIRED)

    def test_09_new_F03_cannot_use_old_versions(self):
        n=alter_visit(two_cycles(),"F03","req",
            lambda x:(x["scope"]["expected"].update(zip(VERSION_NAMES,V1)),
                      x["scope"]["current"].update(zip(VERSION_NAMES,V1))))
        self.assertIs(check(*n).status,Status.VERSION_RECHECK_REQUIRED)

    def test_10_new_F02_cannot_use_old_epoch_versions(self):
        n=alter_visit(two_cycles(),"F02","req",
            lambda x:(x["scope"]["expected"].update(zip(VERSION_NAMES,V1)),
                      x["scope"]["current"].update(zip(VERSION_NAMES,V1))))
        self.assertIs(check(*n).status,Status.VERSION_RECHECK_REQUIRED)

    def test_11_stale_current_F03_rejected_by_original_S2(self):
        n=alter_visit(two_cycles(),"F03","req",
            lambda x:x["scope"]["current"].update(form=99))
        self.assertIs(check(*n).status,Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_12_stale_current_F02_rejected_by_original_S2(self):
        n=alter_visit(two_cycles(),"F02","req",
            lambda x:x["scope"]["current"].update(case=99))
        self.assertIs(check(*n).status,Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_13_cross_epoch_declared_version_regression_rejected(self):
        new=(0,1,2,3,4)
        self.assertIs(check(*two_cycles(second_versions=new)).status,
                      Status.VERSION_REGRESSION_RECHECK_REQUIRED)

    def test_14_F03_essential_field_missing_in_second_cycle(self):
        n=alter_visit(two_cycles(),"F03","proposal",
                      lambda x:x.update(fields=[]))
        self.assertIs(check(*n).status,Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_15_F03_loss_advisory_in_second_cycle_stops_recontact(self):
        n=alter_visit(two_cycles(),"F03","req",
                      lambda x:x.update(verifiedWithdrawalSourceIds=["m7"]))
        n=alter_visit(n,"F03","proposal",
                      lambda x:x.update(commercialAdvisory={
                        "kind":"perdido","sourceIds":["m7"]}))
        self.assertIs(check(*n).status,Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_16_F02_cross_shop_in_second_epoch(self):
        n=alter_visit(two_cycles(),"F02","req",
                      lambda x:x["scope"].update(storeId=str(uuid4())))
        self.assertIs(check(*n).status,Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_17_F02_stale_template_in_second_epoch(self):
        n=alter_visit(two_cycles(),"F02","proposal",
                      lambda x:x["attempts"][0].update(version="v999"))
        self.assertIs(check(*n).status,Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_18_absent_S0_reopen_cannot_proceed_to_second_close(self):
        n=two_cycles()
        ev=tuple(x for x in n[1] if
                 x.kind is not K.S0_HUMAN_REOPEN_REQUEST)
        self.assertIs(check(*(n[:1]+(ev,)+n[2:])).status,
                      Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_19_optout_before_second_human_epoch_is_terminal(self):
        n=two_cycles()
        ev=list(n[1])
        ev[-5]=replace(ev[-5],kind=K.OPT_OUT)
        self.assertIs(check(*(n[:1]+(tuple(ev),)+n[2:])).status,
                      Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_20_meta_uncertainty_does_not_auto_resume(self):
        n=two_cycles()
        ev=list(n[1])
        ev[-5]=replace(ev[-5],kind=K.META_EXTERNAL_OUTCOME_UNCERTAIN)
        self.assertIs(check(*(n[:1]+(tuple(ev),)+n[2:])).status,
                      Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_21_epoch_ticket_fields_and_types_are_strict(self):
        n=two_cycles()
        for bad in (None,[],(),("wrong",),
                    (replace(n[-1][0],versions=(1,2,3)),n[-1][1]),
                    (replace(n[-1][0],versions=(True,2,3,4,5)),n[-1][1])):
            with self.subTest(bad=str(bad)[:30]):
                self.assertIs(check(*replace_epochs(n,bad)).status,
                              Status.DENIED_MALFORMED)

    def test_22_mismatched_latest_human_closure_id_rejected(self):
        n=two_cycles()
        bad=replace(n[-1][-1],closure_id=uuid4())
        self.assertIs(check(*replace_epochs(n,(n[-1][0],bad))).status,
                      Status.EPISODE_RECHECK_REQUIRED)

    def test_23_cross_case_second_F03_rejected(self):
        n=alter_visit(two_cycles(),"F03","req",
                      lambda x:x["scope"].update(caseId=str(uuid4())))
        self.assertIs(check(*n).status,Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_24_node_source_unavailable_fails_closed(self):
        n=two_cycles()
        with mock.patch("backend.f02_multiroute_s2_validation_candidate.S2_SOURCE",
                        Path("/tmp/nonexistent-prumo-S2-source.mjs")):
            self.assertIs(check(*n).status,Status.ROUTE_OR_S2_RECHECK_REQUIRED)

    def test_25_result_has_no_business_action_authority(self):
        n=two_cycles()
        r=check(*n)
        self.assertEqual([x.name for x in fields(HumanEpochResult)],["status"])
        self.assertTrue(all("APPROVED" not in x.value
                            and "SEND" not in x.value
                            and "AUTHORIZED" not in x.value
                            for x in Status))
