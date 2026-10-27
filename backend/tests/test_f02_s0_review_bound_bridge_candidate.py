"""F02/S0 candidate bridge: bind exact claimed evidence and proposal before read-only followup."""
import unittest
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, ReviewOnlyProposal, HandoffState,
    LAB_SOURCE, LOCAL_RECONCILED, LOCAL_ORIGIN,
    UNVERIFIED_EXTERNAL, UNRATIFIED_HUMAN, REQUEST_ONLY,
    prepare_handoff,
)
from backend.f02_reconciled_review_lifecycle import ReviewWindow
from backend.f02_s0_review_followup_candidate import (
    FollowupState, FollowupResult, classify_bound_s0_review_followup,
)
from backend.f02_s0_review_projection_candidate import (
    SCHEMA, EVIDENCE_SCOPE, HUMAN_RATIFICATION,
)


def fixture():
    shop, lead, case_id, close = (uuid4() for _ in range(4))
    evidence = ClaimedS0Evidence(
        shop, lead, case_id, close, LOCAL_RECONCILED, LOCAL_ORIGIN, LAB_SOURCE,
        "a"*64, "b"*64, "c"*64, "d"*64, UNVERIFIED_EXTERNAL, UNRATIFIED_HUMAN)
    proposed = datetime(2026, 11, 10, 18, tzinfo=timezone.utc)
    proposal = ReviewOnlyProposal(
        shop, lead, case_id, close, uuid4(), uuid4(),
        "v1", "policy-001", proposed, "bound-bridge-0001", REQUEST_ONLY)
    handoff = prepare_handoff(evidence, proposal)
    start = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
    window = ReviewWindow(start, start + timedelta(hours=36))
    projection = {
        "schema": SCHEMA, "state": "RECORDED_REVIEW_ONLY",
        "review_ref": str(uuid4()), "revision": "1",
        "observed_at": (start + timedelta(minutes=1)).isoformat(),
        "request_sha256": handoff.untrusted_request_sha256,
        "expires_at": window.expires_at.isoformat(),
        "evidence_scope": EVIDENCE_SCOPE,
        "human_ratification": HUMAN_RATIFICATION,
        "send_authorized": False, "scheduling_authorized": False,
        "commercial_transition_authorized": False,
    }
    return evidence, proposal, handoff, window, projection


def classify(e, p, h, w, projection, previous=None):
    return classify_bound_s0_review_followup(
        e, p, h, w, projection, previous=previous
    ).status


class BoundBridgeTests(unittest.TestCase):
    def test_01_original_packet_only_pending_evidence_recheck(self):
        self.assertIs(classify(*fixture()),
                      FollowupState.AWAIT_S0_EVIDENCE_RECHECK_ONLY)

    def test_02_s0_replay_is_still_only_pending_recheck(self):
        e,p,h,w,q=fixture()
        self.assertIs(classify(e,p,h,w,dict(q,state="REPLAY_REVIEW_ONLY")),
                      FollowupState.AWAIT_S0_EVIDENCE_RECHECK_ONLY)

    def test_03_s0_current_is_still_only_pending_recheck(self):
        e,p,h,w,q=fixture()
        self.assertIs(classify(e,p,h,w,dict(q,state="CURRENT_REVIEW_ONLY")),
                      FollowupState.AWAIT_S0_EVIDENCE_RECHECK_ONLY)

    def test_04_evidence_witness_changed_cannot_reuse_packet(self):
        e,p,h,w,q=fixture()
        for name in ("f03_receipt_sha256","c08_local_witness_sha256",
                     "origin_ledger_sha256","human_intent_sha256"):
            with self.subTest(name=name):
                changed=replace(e,**{name:"e"*64})
                self.assertIs(classify(changed,p,h,w,q),
                              FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_05_scope_change_even_consistent_new_proposal_rejected(self):
        e,p,h,w,q=fixture()
        for field in ("shop_id","lead_id","case_id","closure_id"):
            with self.subTest(field=field):
                new=uuid4()
                self.assertIs(classify(replace(e,**{field:new}),
                                       replace(p,**{field:new}),h,w,q),
                              FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_06_changed_channel_template_version_policy_rejected(self):
        e,p,h,w,q=fixture()
        for new in (replace(p,channel_id=uuid4()),
                    replace(p,template_id=uuid4()),
                    replace(p,template_version="v2"),
                    replace(p,policy_version="policy-002")):
            with self.subTest(new=new):
                self.assertIs(classify(e,new,h,w,q),
                              FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_07_change_proposal_instant_rejected(self):
        e,p,h,w,q=fixture()
        self.assertIs(classify(e,replace(p,proposed_at=p.proposed_at
                              +timedelta(minutes=1)),h,w,q),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_08_new_idempotency_key_never_auto_substituted(self):
        e,p,h,w,q=fixture()
        self.assertIs(classify(e,replace(p,idempotency_key="new-key-0001"),
                               h,w,q),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_09_forged_fresh_handoff_but_old_projection_rejected(self):
        e,p,h,w,q=fixture()
        changed=replace(p,idempotency_key="new-key-0001")
        new_h=prepare_handoff(e,changed)
        self.assertIs(classify(e,changed,new_h,w,q),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_10_wrong_action_and_elevated_human_approval_rejected(self):
        e,p,h,w,q=fixture()
        self.assertIs(classify(e,replace(p,action="SEND_NOW"),h,w,q),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)
        self.assertIs(classify(replace(e,human_operational_ratification="APPROVED"),
                               p,h,w,q),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_11_meta_cancellation_claim_not_proof(self):
        e,p,h,w,q=fixture()
        self.assertIs(classify(replace(e,external_disposition="META_CANCELLED"),
                               p,h,w,q),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_12_invalid_source_or_reconciliation_denied(self):
        e,p,h,w,q=fixture()
        for x in (replace(e,source="S0_SIGNED_PRODUCTION"),
                  replace(e,origin_state="AUTHENTICATED"),
                  replace(e,reconciliation_state="APPROVED")):
            self.assertIs(classify(x,p,h,w,q),
                          FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_13_forged_handoff_contract_rejected(self):
        e,p,h,w,q=fixture()
        for b in (replace(h,contract_version="v999"),
                  replace(h,status=HandoffState.DENIED_MALFORMED),
                  replace(h,untrusted_request_sha256="e"*64)):
            self.assertIs(classify(e,p,b,w,q),
                          FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_14_broken_projection_authority_flags_rejected(self):
        e,p,h,w,q=fixture()
        for flag in ("send_authorized","scheduling_authorized",
                     "commercial_transition_authorized"):
            self.assertIs(classify(e,p,h,w,dict(q,**{flag:True})),
                          FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_15_terminal_stays_terminal_no_sender_rights(self):
        e,p,h,w,q=fixture()
        for state in ("WITHDRAWN_REVIEW_ONLY","EXPIRED_REVIEW_ONLY"):
            self.assertIs(classify(e,p,h,w,dict(q,state=state)),
                          FollowupState.STOP_TECHNICAL_REVIEW_REQUEST_ONLY)

    def test_16_conflicting_s0_result_requires_manual_review(self):
        e,p,h,w,q=fixture()
        q=dict(q,state="IDEMPOTENCY_CONFLICT")
        for col in ("review_ref","revision","observed_at","request_sha256",
                    "expires_at"): q[col]=None
        self.assertIs(classify(e,p,h,w,q),
                      FollowupState.MANUAL_S0_IDEMPOTENCY_REVIEW_ONLY)

    def test_17_unavailable_requires_original_s0_lookup_only(self):
        e,p,h,w,q=fixture()
        q=dict(q,state="UNAVAILABLE")
        for col in ("review_ref","revision","observed_at","request_sha256",
                    "expires_at"): q[col]=None
        self.assertIs(classify(e,p,h,w,q),
                      FollowupState.S0_READ_ORIGINAL_REQUEST_ONLY)

    def test_18_prior_terminal_cannot_reopen_with_same_valid_packet(self):
        e,p,h,w,q=fixture()
        prior=dict(q,state="WITHDRAWN_REVIEW_ONLY")
        self.assertIs(classify(e,p,h,w,dict(q,revision="2"),previous=prior),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_19_prior_persisted_claim_cannot_be_erased_by_failure(self):
        e,p,h,w,q=fixture()
        negative=dict(q,state="UNAVAILABLE")
        for col in ("review_ref","revision","observed_at","request_sha256",
                    "expires_at"): negative[col]=None
        self.assertIs(classify(e,p,h,w,negative,previous=q),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_20_well_formed_long_voluntary_s0_window_not_forced_to_48h(self):
        e,p,h,w,q=fixture()
        long=replace(w,expires_at=w.requested_at+timedelta(hours=72))
        q=dict(q,expires_at=long.expires_at.isoformat())
        self.assertIs(classify(e,p,h,long,q),
                      FollowupState.AWAIT_S0_EVIDENCE_RECHECK_ONLY)

    def test_21_timezone_equivalent_proposal_does_not_change_digest(self):
        e,p,h,w,q=fixture()
        tz=timezone(timedelta(hours=-3))
        same=replace(p,proposed_at=p.proposed_at.astimezone(tz))
        self.assertIs(classify(e,same,h,w,q),
                      FollowupState.AWAIT_S0_EVIDENCE_RECHECK_ONLY)

    def test_22_null_or_forged_inputs_block(self):
        e,p,h,w,q=fixture()
        for args in ((None,p,h,w,q),(e,None,h,w,q),(e,p,None,w,q),
                     (e,p,h,None,q),(e,p,h,w,None),(e,p,h,w,{})):
            self.assertIs(classify(*args),
                          FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_23_output_has_no_action_or_credentials(self):
        e,p,h,w,q=fixture()
        result=classify_bound_s0_review_followup(e,p,h,w,q)
        self.assertEqual([f.name for f in fields(FollowupResult)],["status"])
        for key in ("send","schedule","approve","persist","retry","dispatch",
                    "bearer","token","review_ref","idempotency_key"):
            self.assertFalse(hasattr(result,key))

    def test_24_tampered_handoff_proposal_recomputed_even_on_negative_result(self):
        e,p,h,w,q=fixture()
        negative=dict(q,state="UNAVAILABLE")
        for col in ("review_ref","revision","observed_at","request_sha256",
                    "expires_at"): negative[col]=None
        self.assertIs(classify(e,replace(p,template_version="v2"),h,w,negative),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_25_normal_read_only_path_does_not_mutate_envelope(self):
        e,p,h,w,q=fixture()
        original=dict(q)
        self.assertIs(classify(e,p,h,w,q),
                      FollowupState.AWAIT_S0_EVIDENCE_RECHECK_ONLY)
        self.assertEqual(q,original)


if __name__=="__main__":
    unittest.main()
