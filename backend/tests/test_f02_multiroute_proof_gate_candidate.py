"""Route + F02 claimed proof candidate use actual existing validators."""
import unittest
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.f01_f02_f03_route_ledger_candidate import (
    RouteEvent, RouteKind as K, RouteScope, UNTRUSTED_SOURCE,
)
from backend.f02_multiroute_proof_gate_candidate import (
    RoutedProofResult, RoutedProofStatus as Status,
    check_routed_posthuman_proof as check,
)
from backend.tests.test_f02_s0_proof_binding_candidate import (
    sample as proof_sample, alter,
)

def sample_route(*, multiple=True):
    evidence,proposal,window,packet = proof_sample()
    route=RouteScope(uuid4(), evidence.shop_id, evidence.lead_id, evidence.case_id)
    closure=datetime.fromisoformat(packet["closure_at"])
    # Create events before and after this same exact claimed closure time.
    chain=[
       (K.F01_OPEN,-180,None),
       (K.S0_HUMAN_HANDOFF,-90,None),
       (K.S0_HUMAN_CLOSURE,0,evidence.closure_id),
       (K.F03_PROPOSAL,20,evidence.closure_id),
       (K.S0_F02_POSTHUMAN_REQUEST,40,evidence.closure_id),
    ]
    if multiple:
        chain=[
          (K.F01_OPEN,-180,None),
          (K.S0_F02_PREHUMAN_REQUEST,-160,None),
          (K.CUSTOMER_INBOUND,-140,None),
          (K.S0_PREHUMAN_F02_RECONCILED,-130,None),
          (K.S0_F01_RESUME_REQUEST,-120,None),
          (K.S0_HUMAN_HANDOFF,-90,None),
          (K.S0_HUMAN_CLOSURE,0,evidence.closure_id),
          (K.F03_PROPOSAL,20,evidence.closure_id),
          (K.S0_F02_POSTHUMAN_REQUEST,40,evidence.closure_id),
        ]
    events=tuple(RouteEvent(uuid4(),route.route_id,route.shop_id,route.lead_id,
                            route.case_id,i,closure+timedelta(minutes=offset),
                            kind,UNTRUSTED_SOURCE,ref)
                 for i,(kind,offset,ref) in enumerate(chain,1))
    return route,events,evidence,proposal,window,packet

class MultiRouteProofTests(unittest.TestCase):
    def test_01_non_linear_route_to_review_only(self):
        route,ev,e,p,w,q=sample_route()
        got=check(route,ev,e,p,w,q)
        self.assertIs(got.status,Status.F02_ROUTE_AND_PROOF_SHAPE_RECHECK_ONLY)

    def test_02_simple_human_route_also_review_only(self):
        self.assertIs(check(*sample_route(multiple=False)).status,
                      Status.F02_ROUTE_AND_PROOF_SHAPE_RECHECK_ONLY)

    def test_03_wrong_shop_is_denied(self):
        route,ev,e,p,w,q=sample_route()
        self.assertIs(check(route,ev,replace(e,shop_id=uuid4()),p,w,q).status,
                      Status.SCOPE_RECHECK_REQUIRED)

    def test_04_wrong_case_is_denied(self):
        route,ev,e,p,w,q=sample_route()
        self.assertIs(check(route,ev,e,replace(p,case_id=uuid4()),w,q).status,
                      Status.SCOPE_RECHECK_REQUIRED)

    def test_05_previous_human_closure_cannot_be_reused(self):
        route,ev,e,p,w,q=sample_route()
        other=uuid4()
        self.assertIs(check(route,ev,replace(e,closure_id=other),p,w,q).status,
                      Status.CLOSURE_RECHECK_REQUIRED)

    def test_06_new_closure_with_old_evidence_is_denied(self):
        route,ev,e,p,w,q=sample_route()
        new=uuid4()
        rows=list(ev)
        rows[-3]=replace(rows[-3],closure_id=new)
        rows[-2]=replace(rows[-2],closure_id=new)
        rows[-1]=replace(rows[-1],closure_id=new)
        self.assertIs(check(route,tuple(rows),e,p,w,q).status,
                      Status.CLOSURE_RECHECK_REQUIRED)

    def test_07_wrong_reported_closure_time_is_denied(self):
        route,ev,e,p,w,q=sample_route()
        self.assertIs(check(route,ev,e,p,w,dict(q,closure_at="2026-11-02T12:00:00+00:00")).status,
                      Status.CLOSURE_RECHECK_REQUIRED)

    def test_08_same_closure_in_other_timezone_is_accepted(self):
        route,ev,e,p,w,q=sample_route()
        alt=(datetime.fromisoformat(q["closure_at"]).
             astimezone(timezone(timedelta(hours=-3))).isoformat())
        self.assertIs(check(route,ev,e,p,w,dict(q,closure_at=alt)).status,
                      Status.F02_ROUTE_AND_PROOF_SHAPE_RECHECK_ONLY)

    def test_09_inbound_after_posthuman_route_pauses_request(self):
        route,ev,e,p,w,q=sample_route()
        last=ev[-1]
        next_event=replace(last,event_id=uuid4(),sequence=last.sequence+1,
                           occurred_at=last.occurred_at+timedelta(minutes=1),
                           kind=K.CUSTOMER_INBOUND)
        self.assertIs(check(route,ev+(next_event,),e,p,w,q).status,
                      Status.WRONG_F02_PHASE_RECHECK_REQUIRED)

    def test_10_wrong_pre_human_request_has_no_F03_receipt(self):
        route,ev,e,p,w,q=sample_route()
        self.assertIs(check(route,ev[:2],e,p,w,q).status,
                      Status.WRONG_F02_PHASE_RECHECK_REQUIRED)

    def test_11_broken_route_rejected_before_proof_payload(self):
        route,ev,e,p,w,q=sample_route()
        bad=replace(ev[2],case_id=uuid4())
        self.assertIs(check(route,ev[:2]+(bad,)+ev[3:],e,p,w,q).status,
                      Status.ROUTE_RECHECK_REQUIRED)

    def test_12_cross_route_stolen_event_rejected(self):
        route,ev,e,p,w,q=sample_route()
        bad=replace(ev[3],route_id=uuid4())
        self.assertIs(check(route,ev[:3]+(bad,)+ev[4:],e,p,w,q).status,
                      Status.ROUTE_RECHECK_REQUIRED)

    def test_13_fake_F03_digest_rejected_by_actual_proof_validator(self):
        route,ev,e,p,w,q=sample_route()
        forged=alter(q,"f03_receipt_sha256",digest_sha256="e"*64)
        self.assertIs(check(route,ev,e,p,w,forged).status,
                      Status.PROOF_RECHECK_REQUIRED)

    def test_14_changed_F02_proposal_rejected_by_actual_handoff(self):
        route,ev,e,p,w,q=sample_route()
        changed=replace(p,policy_version="policy-002")
        self.assertIs(check(route,ev,e,changed,w,q).status,
                      Status.PROOF_RECHECK_REQUIRED)

    def test_15_changed_review_window_rejected_by_actual_proof(self):
        route,ev,e,p,w,q=sample_route()
        changed=replace(w,expires_at=w.expires_at+timedelta(minutes=1))
        self.assertIs(check(route,ev,e,p,changed,q).status,
                      Status.PROOF_RECHECK_REQUIRED)

    def test_16_proposal_before_F02_request_is_denied(self):
        route,ev,e,p,w,q=sample_route()
        early=replace(p,proposed_at=ev[-1].occurred_at-timedelta(minutes=1))
        self.assertIs(check(route,ev,e,early,w,q).status,
                      Status.TIMELINE_RECHECK_REQUIRED)

    def test_17_original_window_before_proposal_is_denied(self):
        route,ev,e,p,w,q=sample_route()
        early=replace(w,requested_at=ev[-1].occurred_at-timedelta(minutes=1))
        self.assertIs(check(route,ev,e,p,early,q).status,
                      Status.TIMELINE_RECHECK_REQUIRED)

    def test_18_malformed_packet_fails_closed(self):
        route,ev,e,p,w,q=sample_route()
        for bad in (None,[],{},dict(q,proofs={})):
            self.assertNotEqual(check(route,ev,e,p,w,bad).status,
                                Status.F02_ROUTE_AND_PROOF_SHAPE_RECHECK_ONLY)

    def test_19_optout_prevents_routed_F02_review(self):
        route,ev,e,p,w,q=sample_route()
        wrong=replace(ev[4],kind=K.OPT_OUT)
        self.assertIs(check(route,ev[:4]+(wrong,)+ev[5:],e,p,w,q).status,
                      Status.ROUTE_RECHECK_REQUIRED)

    def test_20_external_meta_unknown_never_eligible(self):
        route,ev,e,p,w,q=sample_route()
        wrong=replace(ev[1],kind=K.META_EXTERNAL_OUTCOME_UNCERTAIN)
        self.assertIs(check(route,ev[:1]+(wrong,)+ev[2:],e,p,w,q).status,
                      Status.ROUTE_RECHECK_REQUIRED)

    def test_21_no_action_fields_in_result(self):
        ans=check(*sample_route())
        self.assertEqual([x.name for x in fields(RoutedProofResult)],["status"])
        self.assertFalse(any(hasattr(ans,k) for k in (
            "can_send","authorized","ratified","schedule","template","token")))

    def test_22_no_approval_in_any_status(self):
        self.assertTrue(all("AUTHORIZED" not in x.value and "APPROVED" not in x.value
                            and "SEND" not in x.value for x in Status))

    def test_23_malformed_event_array_is_denied(self):
        route,ev,e,p,w,q=sample_route()
        self.assertIs(check(route,[],e,p,w,q).status,Status.DENIED_MALFORMED)

    def test_24_F03_must_follow_latest_close(self):
        route,ev,e,p,w,q=sample_route()
        # Removing the F03 marker leaves the S0 posthuman request invalid.
        gone=ev[:-2]+ev[-1:]
        self.assertIs(check(route,gone,e,p,w,q).status,
                      Status.ROUTE_RECHECK_REQUIRED)
