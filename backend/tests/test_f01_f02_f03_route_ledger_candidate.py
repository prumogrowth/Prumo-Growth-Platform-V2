"""Synthetic multi-path F01/F02/F03 ledger regressions, with zero S0 authority."""
import unittest
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.f01_f02_f03_route_ledger_candidate import (
    RouteAssessment, RouteEvent, RouteKind as K, RouteScope,
    RouteStage as Stage, RouteStatus as Status, MAX_EVENTS,
    UNTRUSTED_SOURCE, classify_route_candidate,
)

def build(kinds, *, second_closure=False):
    scope=RouteScope(*(uuid4() for _ in range(4)))
    closure=uuid4()
    next_closure=uuid4()
    active=closure
    events=[]
    first_close=False
    for seq,kind in enumerate(kinds,1):
        if kind is K.S0_HUMAN_CLOSURE:
            if first_close and second_closure:
                active=next_closure
            first_close=True
        ref=(active if kind in (K.S0_HUMAN_CLOSURE,K.F03_PROPOSAL,
                               K.S0_F02_POSTHUMAN_REQUEST,
                               K.S0_HUMAN_REOPEN_REQUEST) else None)
        if kind in (K.CUSTOMER_INBOUND,K.OPT_OUT,
                    K.META_EXTERNAL_OUTCOME_UNCERTAIN) and first_close:
            ref=active
        events.append(RouteEvent(uuid4(),scope.route_id,scope.shop_id,
                                 scope.lead_id,scope.case_id,seq,
                                 datetime(2026,11,1,tzinfo=timezone.utc)
                                    +timedelta(minutes=seq),kind,
                                 UNTRUSTED_SOURCE,ref))
    return scope,tuple(events)

def check(kinds):
    return classify_route_candidate(*build(kinds))

SHORT=(K.F01_OPEN,K.S0_F02_PREHUMAN_REQUEST,K.CUSTOMER_INBOUND,
       K.S0_PREHUMAN_F02_RECONCILED,K.S0_F01_RESUME_REQUEST)
HUMAN=(K.S0_HUMAN_HANDOFF,K.S0_HUMAN_CLOSURE,K.F03_PROPOSAL,
       K.S0_F02_POSTHUMAN_REQUEST)
LONG=SHORT+HUMAN

class RouteLedgerTests(unittest.TestCase):
    def test_01_user_cycle_F01_F02_F01_F03_F02(self):
        r=check(LONG)
        self.assertIs(r.status,Status.ROUTE_SHAPE_RECHECK_ONLY)
        self.assertEqual(r.openai_visits,("F01","F02","F01","F03","F02"))
        self.assertIs(r.current_stage,Stage.F02_POSTHUMAN)

    def test_02_original_F01_F03_F02_is_still_possible(self):
        r=check((K.F01_OPEN,)+HUMAN)
        self.assertEqual(r.openai_visits,("F01","F03","F02"))
        self.assertIs(r.status,Status.ROUTE_SHAPE_RECHECK_ONLY)

    def test_03_F01_pre_human_F02_can_pause(self):
        r=check((K.F01_OPEN,K.S0_F02_PREHUMAN_REQUEST))
        self.assertEqual(r.openai_visits,("F01","F02"))
        self.assertIs(r.current_stage,Stage.F02_PREHUMAN)

    def test_04_repeat_F01_F02_cycle_before_human(self):
        r=check(SHORT+SHORT[1:]+HUMAN)
        self.assertEqual(r.openai_visits,("F01","F02","F01","F02","F01","F03","F02"))

    def test_05_human_closed_without_F03_stops_here(self):
        kinds=(K.F01_OPEN,K.S0_HUMAN_HANDOFF,K.S0_HUMAN_CLOSURE)
        r=check(kinds)
        self.assertIs(r.current_stage,Stage.HUMAN_CLOSED)
        self.assertEqual(r.openai_visits,("F01",))

    def test_06_F03_does_not_automatically_spawn_F02(self):
        kinds=(K.F01_OPEN,K.S0_HUMAN_HANDOFF,
               K.S0_HUMAN_CLOSURE,K.F03_PROPOSAL)
        r=check(kinds)
        self.assertEqual(r.openai_visits,("F01","F03"))
        self.assertIs(r.current_stage,Stage.F03)

    def test_07_customer_inbound_never_auto_resumes_F01(self):
        r=check((K.F01_OPEN,K.S0_F02_PREHUMAN_REQUEST,
                 K.CUSTOMER_INBOUND))
        self.assertEqual(r.openai_visits,("F01","F02"))
        self.assertIs(r.current_stage,Stage.F02_PREHUMAN_INBOUND)

    def test_08_F01_resume_requires_reconciled_pre_human_cadence(self):
        r=check((K.F01_OPEN,K.S0_F02_PREHUMAN_REQUEST,
                 K.CUSTOMER_INBOUND,K.S0_F01_RESUME_REQUEST))
        self.assertIs(r.status,Status.HUMAN_ROUTE_RECHECK_REQUIRED)

    def test_09_F01_resume_cannot_follow_post_human_F02(self):
        r=check(LONG+(K.CUSTOMER_INBOUND,K.S0_F01_RESUME_REQUEST))
        self.assertIs(r.status,Status.HUMAN_ROUTE_RECHECK_REQUIRED)

    def test_10_F03_cannot_follow_F01_without_human_closure(self):
        r=check((K.F01_OPEN,K.F03_PROPOSAL))
        self.assertNotEqual(r.status,Status.ROUTE_SHAPE_RECHECK_ONLY)

    def test_11_F03_cannot_run_after_handoff_without_close(self):
        r=check((K.F01_OPEN,K.S0_HUMAN_HANDOFF,K.F03_PROPOSAL))
        self.assertIs(r.status,Status.HUMAN_ROUTE_RECHECK_REQUIRED)

    def test_12_F02_posthuman_request_requires_F03(self):
        r=check((K.F01_OPEN,K.S0_HUMAN_HANDOFF,
                 K.S0_HUMAN_CLOSURE,K.S0_F02_POSTHUMAN_REQUEST))
        self.assertIs(r.status,Status.TRANSITION_RECHECK_REQUIRED)

    def test_13_human_reopen_from_posthuman_reply_not_F01(self):
        r=check(LONG+(K.CUSTOMER_INBOUND,K.S0_HUMAN_REOPEN_REQUEST))
        self.assertIs(r.status,Status.ROUTE_SHAPE_RECHECK_ONLY)
        self.assertIs(r.current_stage,Stage.HUMAN)
        self.assertEqual(r.openai_visits,("F01","F02","F01","F03","F02"))

    def test_14_second_human_close_second_F03_and_F02_possible(self):
        r=classify_route_candidate(*build(LONG+(K.CUSTOMER_INBOUND,
            K.S0_HUMAN_REOPEN_REQUEST,K.S0_HUMAN_CLOSURE,
            K.F03_PROPOSAL,K.S0_F02_POSTHUMAN_REQUEST),second_closure=True))
        self.assertIs(r.status,Status.ROUTE_SHAPE_RECHECK_ONLY)
        self.assertEqual(r.openai_visits,
                         ("F01","F02","F01","F03","F02","F03","F02"))

    def test_15_reusing_old_human_closure_ref_for_new_cycle_rejected(self):
        r=check(LONG+(K.CUSTOMER_INBOUND,K.S0_HUMAN_REOPEN_REQUEST,
                      K.S0_HUMAN_CLOSURE))
        self.assertIs(r.status,Status.HUMAN_ROUTE_RECHECK_REQUIRED)

    def test_16_optout_is_terminal(self):
        r=check((K.F01_OPEN,K.S0_F02_PREHUMAN_REQUEST,K.OPT_OUT))
        self.assertIs(r.current_stage,Stage.OPTED_OUT)
        self.assertIs(r.status,Status.ROUTE_SHAPE_RECHECK_ONLY)

    def test_17_optout_prevents_new_attempt(self):
        r=check((K.F01_OPEN,K.S0_F02_PREHUMAN_REQUEST,K.OPT_OUT,
                 K.S0_F02_PREHUMAN_REQUEST))
        self.assertIs(r.status,Status.TRANSITION_RECHECK_REQUIRED)

    def test_18_meta_uncertainty_prevents_AI_return(self):
        r=check((K.F01_OPEN,K.S0_F02_PREHUMAN_REQUEST,
                 K.META_EXTERNAL_OUTCOME_UNCERTAIN,
                 K.S0_F01_RESUME_REQUEST))
        self.assertIs(r.status,Status.META_UNCERTAINTY_RECHECK_REQUIRED)

    def test_19_meta_unknown_alone_is_hold_not_send(self):
        r=check((K.F01_OPEN,K.S0_F02_PREHUMAN_REQUEST,
                 K.META_EXTERNAL_OUTCOME_UNCERTAIN))
        self.assertIs(r.current_stage,Stage.META_UNCERTAIN_HOLD)

    def test_20_cross_shop_and_lead_case_scope_denied(self):
        scope,ev=build(LONG)
        for col in ("shop_id","lead_id","case_id","route_id"):
            with self.subTest(col=col):
                changed=replace(ev[3],**{col:uuid4()})
                rows=ev[:3]+(changed,)+ev[4:]
                self.assertIs(classify_route_candidate(scope,rows).status,
                              Status.SCOPE_RECHECK_REQUIRED)

    def test_21_double_event_id_or_sequence_rejected(self):
        scope,ev=build(LONG)
        for changed in (replace(ev[3],event_id=ev[2].event_id),
                        replace(ev[3],sequence=ev[2].sequence)):
            rows=ev[:3]+(changed,)+ev[4:]
            self.assertIs(classify_route_candidate(scope,rows).status,
                          Status.EVENT_ORDER_RECHECK_REQUIRED)

    def test_22_timestamp_regression_even_with_high_sequence_rejected(self):
        scope,ev=build(LONG)
        earlier=replace(ev[3],occurred_at=ev[2].occurred_at-timedelta(seconds=1))
        self.assertIs(classify_route_candidate(scope,ev[:3]+(earlier,)+ev[4:]).status,
                      Status.EVENT_ORDER_RECHECK_REQUIRED)

    def test_23_matching_instant_under_new_timezone_valid(self):
        scope,ev=build(LONG)
        offset=timezone(timedelta(hours=-3))
        changed=replace(ev[1],occurred_at=ev[1].occurred_at.astimezone(offset))
        self.assertIs(classify_route_candidate(scope,ev[:1]+(changed,)+ev[2:]).status,
                      Status.ROUTE_SHAPE_RECHECK_ONLY)

    def test_24_reject_claimed_S0_signature_privilege(self):
        scope,ev=build(LONG)
        changed=replace(ev[1],claimed_source="S0_AUTHENTICATED")
        self.assertIs(classify_route_candidate(scope,ev[:1]+(changed,)+ev[2:]).status,
                      Status.DENIED_MALFORMED)

    def test_25_pre_human_event_must_not_carry_closure(self):
        scope,ev=build(LONG)
        changed=replace(ev[1],closure_id=uuid4())
        self.assertIs(classify_route_candidate(scope,ev[:1]+(changed,)+ev[2:]).status,
                      Status.HUMAN_ROUTE_RECHECK_REQUIRED)

    def test_26_cross_closure_F02_after_F03_rejected(self):
        scope,ev=build(LONG)
        last=replace(ev[-1],closure_id=uuid4())
        self.assertIs(classify_route_candidate(scope,ev[:-1]+(last,)).status,
                      Status.HUMAN_ROUTE_RECHECK_REQUIRED)

    def test_27_empty_events_or_wrong_shapes_rejected(self):
        scope,ev=build(LONG)
        for wrong in ([],(),tuple([None]),tuple(ev)*(MAX_EVENTS//len(ev)+2)):
            self.assertIs(classify_route_candidate(scope,wrong).status,
                          Status.DENIED_MALFORMED)

    def test_28_malformed_or_naive_timestamp_rejected(self):
        scope,ev=build(LONG)
        for wrong in (None,datetime(2026,11,1),17):
            changed=replace(ev[0],occurred_at=wrong)
            self.assertIs(classify_route_candidate(scope,(changed,)+ev[1:]).status,
                          Status.DENIED_MALFORMED)

    def test_29_result_never_contains_action_or_source_proof(self):
        r=check(LONG)
        self.assertEqual(tuple(x.name for x in fields(RouteAssessment)),
                         ("status","current_stage","openai_visits"))
        self.assertFalse(any(hasattr(r,name) for name in
                            ("authorized","can_send","schedule","receipt",
                             "token","signature","principal","approve")))

    def test_30_route_assertions_remain_lab_only(self):
        self.assertEqual(UNTRUSTED_SOURCE,"E04_SYNTHETIC_ROUTE_CLAIM_ONLY")
        self.assertTrue(all("AUTHORIZED" not in x.value
                            and "SEND" not in x.value
                            and "APPROVED" not in x.value
                            for x in Status))
