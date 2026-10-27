"""S0/F02 joint candidate gates, absolute-time regression and pinned gaps."""
import json
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
from uuid import uuid4
from zoneinfo import ZoneInfo

from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, ReviewOnlyProposal, LAB_SOURCE, LOCAL_RECONCILED,
    LOCAL_ORIGIN, UNVERIFIED_EXTERNAL, UNRATIFIED_HUMAN, REQUEST_ONLY,
    prepare_handoff,
)
from backend.f02_reconciled_review_lifecycle import ReviewWindow
from backend.f02_s0_review_projection_candidate import (
    SCHEMA, EVIDENCE_SCOPE, HUMAN_RATIFICATION,
)
from backend.f02_s0_joint_homologation_candidate import (
    ALL_UNRESOLVED, JointGate, JointStatus, JointAssessment,
    assess_joint_review_candidate,
)
from backend.f02_s0_review_followup_candidate import FollowupState

GATES = Path(__file__).resolve().parents[2] / (
    "docs/contracts/OAI_E04_F02_S0_JOINT_GATES_V1.json"
)


def fixture():
    shop, lead, case, closure = (uuid4() for _ in range(4))
    e = ClaimedS0Evidence(shop,lead,case,closure,LOCAL_RECONCILED,
        LOCAL_ORIGIN,LAB_SOURCE,"a"*64,"b"*64,"c"*64,"d"*64,
        UNVERIFIED_EXTERNAL,UNRATIFIED_HUMAN)
    p = ReviewOnlyProposal(shop,lead,case,closure,uuid4(),uuid4(),
        "v1","policy-001",datetime(2026,11,10,18,tzinfo=timezone.utc),
        "joint-review-0001",REQUEST_ONLY)
    h = prepare_handoff(e,p)
    start = datetime(2026,11,1,12,tzinfo=timezone.utc)
    w = ReviewWindow(start,start+timedelta(hours=72))
    q = {
        "schema": SCHEMA, "state":"RECORDED_REVIEW_ONLY",
        "review_ref":str(uuid4()),"revision":"1",
        "observed_at":(start+timedelta(minutes=5)).isoformat(),
        "request_sha256":h.untrusted_request_sha256,
        "expires_at":w.expires_at.isoformat(),
        "evidence_scope":EVIDENCE_SCOPE,
        "human_ratification":HUMAN_RATIFICATION,
        "send_authorized":False,
        "scheduling_authorized":False,
        "commercial_transition_authorized":False,
    }
    return e,p,h,w,q


def check(e,p,h,w,q,previous=None):
    return assess_joint_review_candidate(e,p,h,w,q,previous=previous)


def negative(q,code):
    q=dict(q,state=code)
    for name in ("review_ref","revision","observed_at",
                 "request_sha256","expires_at"):
        q[name]=None
    return q


class JointCandidateTests(unittest.TestCase):
    def test_01_consistent_persisted_result_still_all_gates_pending(self):
        result=check(*fixture())
        self.assertIs(result.status,JointStatus.CANDIDATE_CONSISTENT_NOT_HOMOLOGATED)
        self.assertEqual(result.blockers,ALL_UNRESOLVED)
        self.assertEqual(len(result.blockers),7)

    def test_02_candidate_replay_does_not_clear_gates(self):
        e,p,h,w,q=fixture()
        v=check(e,p,h,w,dict(q,state="REPLAY_REVIEW_ONLY"))
        self.assertIs(v.status,JointStatus.CANDIDATE_CONSISTENT_NOT_HOMOLOGATED)
        self.assertEqual(v.blockers,ALL_UNRESOLVED)

    def test_03_terminal_withdrawal_cannot_be_rerouted_as_approval(self):
        e,p,h,w,q=fixture()
        v=check(e,p,h,w,dict(q,state="WITHDRAWN_REVIEW_ONLY"))
        self.assertIs(v.followup,FollowupState.STOP_TECHNICAL_REVIEW_REQUEST_ONLY)
        self.assertEqual(v.blockers,ALL_UNRESOLVED)

    def test_04_expired_technical_request_remains_nonoperational(self):
        e,p,h,w,q=fixture()
        v=check(e,p,h,w,dict(q,state="EXPIRED_REVIEW_ONLY"))
        self.assertIs(v.followup,FollowupState.STOP_TECHNICAL_REVIEW_REQUEST_ONLY)
        self.assertEqual(len(v.blockers),7)

    def test_05_unavailable_is_read_original_only_with_all_gates(self):
        e,p,h,w,q=fixture()
        v=check(e,p,h,w,negative(q,"UNAVAILABLE"))
        self.assertIs(v.status,JointStatus.S0_RECHECK_NOT_HOMOLOGATED)
        self.assertIs(v.followup,FollowupState.S0_READ_ORIGINAL_REQUEST_ONLY)
        self.assertEqual(v.blockers,ALL_UNRESOLVED)

    def test_06_conflict_never_auto_regenerates_request(self):
        e,p,h,w,q=fixture()
        v=check(e,p,h,w,negative(q,"IDEMPOTENCY_CONFLICT"))
        self.assertIs(v.followup,FollowupState.MANUAL_S0_IDEMPOTENCY_REVIEW_ONLY)
        self.assertEqual(v.blockers,ALL_UNRESOLVED)

    def test_07_false_approval_flag_blocks_contract(self):
        e,p,h,w,q=fixture()
        v=check(e,p,h,w,dict(q,send_authorized=True))
        self.assertIs(v.status,JointStatus.CONTRACT_RECHECK_NOT_HOMOLOGATED)
        self.assertEqual(v.blockers,ALL_UNRESOLVED)

    def test_08_nonratified_human_claim_cannot_be_elevated(self):
        e,p,h,w,q=fixture()
        v=check(replace(e,human_operational_ratification="APPROVED"),p,h,w,q)
        self.assertIs(v.status,JointStatus.CONTRACT_RECHECK_NOT_HOMOLOGATED)

    def test_09_swapped_scope_and_evidence_cannot_pass(self):
        e,p,h,w,q=fixture()
        x=uuid4()
        v=check(replace(e,closure_id=x),replace(p,closure_id=x),h,w,q)
        self.assertIs(v.status,JointStatus.CONTRACT_RECHECK_NOT_HOMOLOGATED)

    def test_10_new_document_hash_does_not_rebind_old_s0_result(self):
        e,p,h,w,q=fixture()
        proposal=replace(p,policy_version="policy-002")
        v=check(e,proposal,prepare_handoff(e,proposal),w,q)
        self.assertIs(v.status,JointStatus.CONTRACT_RECHECK_NOT_HOMOLOGATED)

    def test_11_prior_expiry_cannot_be_reopened(self):
        e,p,h,w,q=fixture()
        v=check(e,p,h,w,dict(q,revision="2"),
                previous=dict(q,state="EXPIRED_REVIEW_ONLY"))
        self.assertIs(v.status,JointStatus.CONTRACT_RECHECK_NOT_HOMOLOGATED)

    def test_12_recheck_does_not_clear_original_record(self):
        e,p,h,w,q=fixture()
        v=check(e,p,h,w,negative(q,"UNAVAILABLE"),previous=q)
        self.assertIs(v.status,JointStatus.CONTRACT_RECHECK_NOT_HOMOLOGATED)

    def test_13_joint_gates_manifest_matches_enum_and_owners(self):
        m=json.loads(GATES.read_text(encoding="utf-8"))
        self.assertEqual(m["s0_schema"],SCHEMA)
        self.assertEqual(m["criteria_type"],"HARD_BLOCKERS_NEVER_SELF_RATIFIED")
        self.assertEqual([x["id"] for x in m["gates"]],
                         [x.value for x in ALL_UNRESOLVED])
        self.assertEqual(set(ALL_UNRESOLVED),set(JointGate))
        for item in m["gates"]:
            self.assertEqual(item["status"],"INTEGRATION_PENDING")
            self.assertTrue(item["owner"] and item["needed"])
        self.assertFalse(m["real_s0_e2e_homologated"])
        self.assertFalse(m["production_authorization"])

    def test_14_interface_never_contains_approval_or_execution(self):
        e,p,h,w,q=fixture()
        v=check(e,p,h,w,q)
        self.assertEqual([f.name for f in fields(JointAssessment)],
                         ["status","followup","blockers"])
        for key in ("send","approve","schedule","retry","persist",
                    "dispatch","token","review_ref","authorization"):
            self.assertFalse(hasattr(v,key))

    def test_15_malformed_inputs_always_keep_all_gates(self):
        e,p,h,w,q=fixture()
        for inputs in ((None,p,h,w,q),(e,None,h,w,q),
                       (e,p,None,w,q),(e,p,h,None,q),
                       (e,p,h,w,{"approved":True})):
            v=check(*inputs)
            self.assertIs(v.status,JointStatus.CONTRACT_RECHECK_NOT_HOMOLOGATED)
            self.assertEqual(v.blockers,ALL_UNRESOLVED)

    def test_16_voluntary_s0_window_over_48_hours_is_not_business_policy(self):
        self.assertIs(check(*fixture()).status,
                      JointStatus.CANDIDATE_CONSISTENT_NOT_HOMOLOGATED)

    def test_17_dst_fall_back_reversed_absolute_window_is_refused(self):
        e,p,h,w,q=fixture()
        ny=ZoneInfo("America/New_York")
        # Wall time increases, but absolute time moves backwards 55 minutes.
        start=datetime(2026,11,1,1,45,tzinfo=ny,fold=1)
        end=datetime(2026,11,1,1,50,tzinfo=ny,fold=0)
        self.assertGreater(start.astimezone(timezone.utc),
                           end.astimezone(timezone.utc))
        wrong=ReviewWindow(start,end)
        q=dict(q,expires_at=end.astimezone(timezone.utc).isoformat(),
               observed_at=start.astimezone(timezone.utc).isoformat())
        v=check(e,p,h,wrong,q)
        self.assertIs(v.status,JointStatus.CONTRACT_RECHECK_NOT_HOMOLOGATED)

    def test_18_dst_fall_back_valid_absolute_window_must_not_be_rejected(self):
        e,p,h,w,q=fixture()
        ny=ZoneInfo("America/New_York")
        # Wall time decreases while UTC moves forward 30 minutes.
        start=datetime(2026,11,1,1,45,tzinfo=ny,fold=0)
        end=datetime(2026,11,1,1,15,tzinfo=ny,fold=1)
        self.assertLess(start.astimezone(timezone.utc),
                        end.astimezone(timezone.utc))
        valid=ReviewWindow(start,end)
        q=dict(q,expires_at=end.astimezone(timezone.utc).isoformat(),
               observed_at=(start.astimezone(timezone.utc)+
                            timedelta(minutes=5)).isoformat())
        v=check(e,p,h,valid,q)
        self.assertIs(v.status,JointStatus.CANDIDATE_CONSISTENT_NOT_HOMOLOGATED)

    def test_19_offsets_that_mean_the_same_instant_stay_compatible(self):
        e,p,h,w,q=fixture()
        zone=timezone(timedelta(hours=-3))
        other=replace(p,proposed_at=p.proposed_at.astimezone(zone))
        v=check(e,other,h,w,q)
        self.assertIs(v.status,JointStatus.CANDIDATE_CONSISTENT_NOT_HOMOLOGATED)

    def test_20_all_states_explicitly_deny_homologation(self):
        from backend.f02_s0_review_followup_candidate import _STATE_TO_FOLLOWUP
        e,p,h,w,q=fixture()
        for s in _STATE_TO_FOLLOWUP:
            row=dict(q,state=s)
            if s in ("INPUT_REJECTED","DENIED","STALE","IDEMPOTENCY_CONFLICT",
                     "REQUEST_EXPIRED","REVIEW_REQUEST_NOT_FOUND",
                     "CLOCK_RECHECK_REQUIRED","UNAVAILABLE"):
                row=negative(row,s)
            value=check(e,p,h,w,row)
            self.assertEqual(value.blockers,ALL_UNRESOLVED)
            self.assertTrue(value.status.value.endswith("_NOT_HOMOLOGATED"))

if __name__=="__main__":
    unittest.main()
