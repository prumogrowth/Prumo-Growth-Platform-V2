"""Physical JS invocation of pinned E04 S2 core.mjs with Python route gates.

Real Node execution against pinned source, but ALL inputs are synthetic fixtures;
this is NEVER an authenticated S0, F03 receipt or OpenAI/Meta integration.
"""
import copy
from dataclasses import fields, replace
from pathlib import Path
from unittest import TestCase, mock
from uuid import uuid4

from backend.f01_f02_f03_route_ledger_candidate import (
    RouteKind as K,
)
from backend.f02_multiroute_s2_validation_candidate import (
    S2RouteResult, S2RouteStatus as Status, CI_PIN, S2_SOURCE,
    check_routed_proof_with_pinned_s2 as check,
)
from backend.tests.test_f02_multiroute_proof_gate_candidate import sample_route

PERSON="SYNTHETIC_PERSON_001"


def fixture(*, multiple=True):
    scope,events,e,p,w,q=sample_route(multiple=multiple)
    vers={"case":1,"cycle":2,"form":3,"catalog":4,"assignment":5}
    def context():
        return {"authenticated":True,"authorized":True,"tenantAllowed":True,
                "storeId":str(scope.shop_id),"caseId":str(scope.case_id),
                "expected":dict(vers),"current":dict(vers)}
    visits=[]
    for event in events:
        if event.kind in (K.F01_OPEN,K.S0_F01_RESUME_REQUEST):
            visits.append({"stage":"F01",
                "req":{"scope":context(),"owner":"ai","handoff":False,
                       "humanized":False,"nowMs":1800000000000,
                       "sources":[{"id":"offer1","storeId":str(scope.shop_id),
                                   "approved":True,"active":True,"mode":"current"}]},
                "proposal":{"text":"Preço sujeito a confirmação.",
                            "commercial":True,"sourceIds":["offer1"],
                            "modality":"text"}})
        elif event.kind in (K.S0_F02_PREHUMAN_REQUEST,K.S0_F02_POSTHUMAN_REQUEST):
            post=event.kind is K.S0_F02_POSTHUMAN_REQUEST
            purpose="post_human" if post else "pre_human"
            template=str(p.template_id) if post else "pretemplate1"
            visits.append({"stage":"F02",
                "req":{"scope":context(),"explicitS0Request":True,
                       "optOut":False,"handoffPlanReuse":False,
                       "ownerRoute":"human" if post else "seller_ai",
                       "purpose":purpose,"maxAttempts":2,
                       "windowStart":"2026-11-01T00:00:00Z",
                       "windowEnd":"2026-11-15T23:00:00Z",
                       "allowedTemplates":[{"id":template,"version":"v1",
                                            "storeId":str(scope.shop_id),
                                            "purpose":purpose,"active":True}]},
                "proposal":{"attempts":[{"templateId":template,
                   "version":"v1","purpose":purpose,"at":"2026-11-02T12:00:00Z"}],
                   "finalTemplate":None}})
        elif event.kind is K.F03_PROPOSAL:
            visits.append({"stage":"F03",
                "req":{"scope":context(),"humanClosed":True,
                       "closureAuthenticated":True,"closureId":str(event.closure_id),
                       "personId":PERSON,"cutoffSequence":7,
                       "records":[
                           {"id":"m1","storeId":str(scope.shop_id),
                            "personId":PERSON,"caseId":"SYNTHETIC_PRIOR_CASE",
                            "sequence":2,"author":"customer","kind":"text",
                            "available":True,"contentAuthorized":True},
                           {"id":"m7","storeId":str(scope.shop_id),
                            "personId":PERSON,"caseId":str(scope.case_id),
                            "sequence":7,"author":"customer","kind":"text",
                            "available":True,"contentAuthorized":True}],
                       "catalog":[{"code":"renda","essential":True}],
                       "verifiedWithdrawalSourceIds":[]},
                "proposal":{"fields":[{"code":"renda","value":3500,
                                       "sourceId":"m7"}],
                            "conflicts":[],"commercialAdvisory":None}})
    return (scope,events,e,p,w,q,tuple(visits),PERSON)


def mutate(n, **changes):
    v=list(n[6])
    v[0]=dict(v[0],**changes)
    return n[:6]+(tuple(v),n[7])


def edit(n, stage, section, callback, *, nth=0):
    steps=copy.deepcopy(n[6])
    chosen=[i for i,s in enumerate(steps) if s["stage"]==stage]
    if nth>=len(chosen): raise AssertionError("Missing stage fixture")
    idx=chosen[nth]
    callback(steps[idx][section])
    return n[:6]+(tuple(steps),n[7])


class PinnedS2MultiRouteTests(TestCase):
    def test_01_full_non_linear_uses_actual_S2_validators(self):
        n=fixture()
        self.assertTrue(S2_SOURCE.is_file())
        self.assertIs(check(*n).status,Status.MULTIROUTE_AND_S2_SHAPE_RECHECK_ONLY)

    def test_02_simple_F01_human_F03_F02_still_works(self):
        self.assertIs(check(*fixture(multiple=False)).status,
                      Status.MULTIROUTE_AND_S2_SHAPE_RECHECK_ONLY)

    def test_03_stale_case_version_F01_rejected_by_S2(self):
        n=edit(fixture(),"F01","req",
               lambda x:x["scope"]["current"].update(case=9))
        self.assertIs(check(*n).status,Status.S2_VALIDATION_RECHECK_REQUIRED)

    def test_04_F01_unapproved_source_rejected_by_S2(self):
        n=edit(fixture(),"F01","req",
               lambda x:x["sources"][0].update(approved=False))
        self.assertIs(check(*n).status,Status.S2_VALIDATION_RECHECK_REQUIRED)

    def test_05_F01_commercial_without_source_rejected(self):
        n=edit(fixture(),"F01","proposal",lambda x:x.update(sourceIds=[]))
        self.assertIs(check(*n).status,Status.S2_VALIDATION_RECHECK_REQUIRED)

    def test_06_F01_stale_resume_detected_on_second_visit(self):
        n=edit(fixture(),"F01","req",
               lambda x:x["scope"]["current"].update(form=9),nth=1)
        self.assertIs(check(*n).status,Status.S2_VALIDATION_RECHECK_REQUIRED)

    def test_07_F03_unauthenticated_close_rejected_by_S2(self):
        n=edit(fixture(),"F03","req",lambda x:x.update(closureAuthenticated=False))
        self.assertIs(check(*n).status,Status.S2_VALIDATION_RECHECK_REQUIRED)

    def test_08_F03_cross_person_evidence_rejected_by_S2(self):
        n=edit(fixture(),"F03","req",
               lambda x:x["records"][0].update(personId="WRONG_PERSON"))
        self.assertIs(check(*n).status,Status.S2_VALIDATION_RECHECK_REQUIRED)

    def test_09_F03_unavailable_essential_field_requires_review(self):
        n=edit(fixture(),"F03","proposal",lambda x:x.update(fields=[]))
        self.assertIs(check(*n).status,Status.S2_VALIDATION_RECHECK_REQUIRED)

    def test_10_F03_post_cutoff_source_rejected_by_S2(self):
        n=edit(fixture(),"F03","req",
               lambda x:x["records"].append({
                    "id":"late","storeId":x["scope"]["storeId"],"personId":PERSON,
                    "caseId":x["scope"]["caseId"],"sequence":8,"author":"customer",
                    "kind":"text","available":True,"contentAuthorized":True}))
        n=edit(n,"F03","proposal",
               lambda x:x["fields"][0].update(sourceId="late"))
        self.assertIs(check(*n).status,Status.S2_VALIDATION_RECHECK_REQUIRED)

    def test_11_F03_wrong_closure_blocked_before_Node(self):
        n=edit(fixture(),"F03","req",lambda x:x.update(closureId=str(uuid4())))
        self.assertIs(check(*n).status,Status.STAGE_BINDING_RECHECK_REQUIRED)

    def test_12_F02_prehuman_owner_must_be_seller_ai(self):
        n=edit(fixture(),"F02","req",lambda x:x.update(ownerRoute="human"))
        self.assertIs(check(*n).status,Status.STAGE_BINDING_RECHECK_REQUIRED)

    def test_13_F02_posthuman_owner_must_be_human(self):
        n=edit(fixture(),"F02","req",lambda x:x.update(ownerRoute="seller_ai"),nth=1)
        self.assertIs(check(*n).status,Status.STAGE_BINDING_RECHECK_REQUIRED)

    def test_14_posthuman_F02_template_not_in_S2_allowlist_rejected(self):
        n=edit(fixture(),"F02","req",
               lambda x:x["allowedTemplates"][0].update(id="unknown_template"),nth=1)
        self.assertIs(check(*n).status,Status.S2_VALIDATION_RECHECK_REQUIRED)

    def test_15_posthuman_S2_template_must_match_F02_review_proposal(self):
        n=edit(fixture(),"F02","proposal",
               lambda x:x["attempts"][0].update(templateId="unknown_template"),nth=1)
        self.assertIs(check(*n).status,Status.STAGE_BINDING_RECHECK_REQUIRED)

    def test_16_missing_visit_refused(self):
        n=fixture()
        self.assertIs(check(*(n[:6]+(n[6][:-1],n[7]))).status,
                      Status.STAGE_BINDING_RECHECK_REQUIRED)

    def test_17_extra_visit_refused(self):
        n=fixture()
        self.assertIs(check(*(n[:6]+(n[6]+(n[6][-1],),n[7]))).status,
                      Status.STAGE_BINDING_RECHECK_REQUIRED)

    def test_18_swapped_visit_refused(self):
        n=fixture()
        visits=list(n[6])
        visits[0],visits[1]=visits[1],visits[0]
        self.assertIs(check(*(n[:6]+(tuple(visits),n[7]))).status,
                      Status.STAGE_BINDING_RECHECK_REQUIRED)

    def test_19_cross_tenant_S2_scope_refused(self):
        n=edit(fixture(),"F03","req",
               lambda x:x["scope"].update(storeId=str(uuid4())))
        self.assertIs(check(*n).status,Status.STAGE_BINDING_RECHECK_REQUIRED)

    def test_20_cross_case_S2_scope_refused(self):
        n=edit(fixture(),"F01","req",
               lambda x:x["scope"].update(caseId=str(uuid4())))
        self.assertIs(check(*n).status,Status.STAGE_BINDING_RECHECK_REQUIRED)

    def test_21_missing_pinned_S2_runtime_fails_closed(self):
        n=fixture()
        with mock.patch("backend.f02_multiroute_s2_validation_candidate.S2_SOURCE",
                        Path("/tmp/_nonexistent_pinned_S2_core_.mjs")):
            self.assertIs(check(*n).status,Status.S2_PINNED_RUNTIME_UNAVAILABLE)

    def test_22_fake_F02_source_hash_fails_before_Node(self):
        n=fixture()
        q=copy.deepcopy(n[5]);q["proofs"]["f03_receipt_sha256"]["digest_sha256"]="e"*64
        self.assertIs(check(*(n[:5]+(q,)+n[6:])).status,
                      Status.ROUTE_OR_F02_PROOF_RECHECK_REQUIRED)

    def test_23_posthuman_customer_reply_cannot_trigger_this_F02_gate(self):
        n=fixture()
        last=n[1][-1]
        reply=replace(last,event_id=uuid4(),sequence=last.sequence+1,
                      occurred_at=last.occurred_at+__import__("datetime").timedelta(minutes=1),
                      kind=K.CUSTOMER_INBOUND)
        self.assertIs(check(*(n[:1]+(n[1]+(reply,),)+n[2:])).status,
                      Status.ROUTE_OR_F02_PROOF_RECHECK_REQUIRED)

    def test_24_result_does_not_contain_action_authority(self):
        r=check(*fixture())
        self.assertEqual([x.name for x in fields(S2RouteResult)],["status"])
        self.assertFalse(any(hasattr(r,k) for k in (
            "authorize","send","schedule","approval","accessToken","sourceSignature")))

    def test_25_S2_pin_and_workflow_checkout_are_fixed(self):
        source=(Path(__file__).resolve().parents[2]/
                ".github/workflows/s0-f03-pg17.yml").read_text()
        self.assertIn(CI_PIN,source)
        self.assertTrue(S2_SOURCE.is_file())

    def test_26_synthetic_session_flag_rejected_by_real_S2(self):
        n=edit(fixture(),"F01","req",
               lambda x:x["scope"].update(authenticated=False))
        self.assertIs(check(*n).status,Status.S2_VALIDATION_RECHECK_REQUIRED)

    def test_27_valid_F03_withdrawal_advisory_does_not_trigger_F02(self):
        n=edit(fixture(),"F03","req",
               lambda x:x.update(verifiedWithdrawalSourceIds=["m7"]))
        n=edit(n,"F03","proposal",
               lambda x:x.update(commercialAdvisory={
                   "kind":"perdido","sourceIds":["m7"]}))
        self.assertIs(check(*n).status,Status.S2_VALIDATION_RECHECK_REQUIRED)
