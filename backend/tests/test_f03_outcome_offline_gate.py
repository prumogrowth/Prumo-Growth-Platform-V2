"""OAI-07 conversational outcome tests: invented messages, no NLP or bank API."""
from dataclasses import replace
import unittest
from backend.s0_openai_bridge.f03_outcome_offline_gate import (
    ConversationOutcome as O, EvidenceTopic as T, OutcomeStatus as S,
    NextStepAdvisory as N, OutcomeEvidence, OutcomeSnapshot,
    S0OutcomeAuthority, ModelOutcomeCandidate, review_f03_outcome_offline,
)


def fixture(outcome=O.CONTINUE_TO_BANK_REVIEW):
    reasons = {
        O.NEGOTIATION_READY_FOR_BANK_HANDOFF: ('CLIENT_CONFIRMED_INTENT', T.CONFIRMED_INTEREST),
        O.CONTINUE_TO_BANK_REVIEW: ('BANK_RETURN_MENTIONED', T.MENTIONED_BANK_RETURN),
        O.NEEDS_CLARIFICATION: ('NEEDS_INFORMATION', T.NEEDS_INFORMATION),
        O.CUSTOMER_WITHDREW: ('CUSTOMER_EXPLICIT_WITHDRAWAL', T.EXPLICIT_WITHDRAWAL),
        O.NO_FURTHER_COMMERCIAL_INTEREST: ('CUSTOMER_NO_FURTHER_INTEREST', T.EXPLICIT_NO_INTEREST),
        O.INCONCLUSIVE: ('UNCLEAR_RESULT', T.AMBIGUOUS),
    }
    reason, topic = reasons[outcome]
    evidence = (OutcomeEvidence('m1', 'store-A', 'case-1', 'customer', topic, True),)
    snap = OutcomeSnapshot('store-A', 'case-1', 'closed-1', 'sha-1', 'm1', 4, 6, evidence)
    auth = S0OutcomeAuthority('store-A', 'case-1', 'closed-1', 'sha-1', 'm1', 4, 6,
                               True, True, True, True, False, ())
    model = ModelOutcomeCandidate(outcome, reason, ('m1',))
    return snap, auth, model


class TestOutcome(unittest.TestCase):
    def check(self, expected, snap, auth, model, step=None):
        result = review_f03_outcome_offline(snap, auth, model)
        self.assertEqual(result.status, expected, repr(result))
        if step is not None: self.assertEqual(result.next_step, step)
        if expected in (S.DENIED, S.STALE, S.INVALID):
            self.assertIsNone(result.proposed_outcome)
            self.assertEqual(result.evidence_refs, ())
        self.assertFalse(hasattr(result, 'bank_status'))
        self.assertFalse(hasattr(result, 'send'))
        return result

    def test_01_await_bank_unverified(self):
        self.check(S.REVIEW_ONLY,*fixture(),step=N.HUMAN_CHECK_BANK_SUBMISSION)
    def test_02_await_bank_submission_proved(self):
        a,b,c=fixture();self.check(S.REVIEW_ONLY,a,replace(b,bank_submission_proved=True),c,N.BANK_RETURN_PENDING_REVIEW)
    def test_03_bank_remittance_not_sale(self):
        a,b,c=fixture();r=self.check(S.REVIEW_ONLY,a,replace(b,bank_submission_proved=True),c)
        self.assertNotIn('SOLD',str(r))
    def test_04_ready_for_bank_needs_human_remittance(self):
        self.check(S.REVIEW_ONLY,*fixture(O.NEGOTIATION_READY_FOR_BANK_HANDOFF),step=N.HUMAN_BANK_SUBMISSION)
    def test_05_ready_for_bank_proved_no_duplicate(self):
        a,b,c=fixture(O.NEGOTIATION_READY_FOR_BANK_HANDOFF)
        self.check(S.REVIEW_ONLY,a,replace(b,bank_submission_proved=True),c,N.HUMAN_CHECK_BANK_SUBMISSION)
    def test_06_essential_missing_routes_to_human(self):
        a,b,c=fixture(O.NEGOTIATION_READY_FOR_BANK_HANDOFF)
        r=self.check(S.HUMAN_REVIEW,a,replace(b,missing_required_field_codes=('TEST_FIELD',)),c,N.HUMAN_COLLECT_REQUIRED)
        self.assertEqual(r.missing_required_field_codes,('TEST_FIELD',))
    def test_07_missing_required_bank_wait_requires_human(self):
        a,b,c=fixture();self.check(S.HUMAN_REVIEW,a,replace(b,missing_required_field_codes=('REQUIRED',)),c,N.HUMAN_COLLECT_REQUIRED)
    def test_08_optional_gaps_do_not_block(self):
        self.check(S.REVIEW_ONLY,*fixture(O.NEGOTIATION_READY_FOR_BANK_HANDOFF))
    def test_09_customer_needs_clarification(self):
        self.check(S.REVIEW_ONLY,*fixture(O.NEEDS_CLARIFICATION),step=N.HUMAN_CLARIFY)
    def test_10_customer_withdrew_not_lost_status(self):
        r=self.check(S.REVIEW_ONLY,*fixture(O.CUSTOMER_WITHDREW),step=N.HUMAN_CONFIRM_WITHDRAWAL)
        self.assertFalse(hasattr(r,'commercial_status'))
    def test_11_customer_no_further_interest(self):
        self.check(S.REVIEW_ONLY,*fixture(O.NO_FURTHER_COMMERCIAL_INTEREST),step=N.HUMAN_CONFIRM_WITHDRAWAL)
    def test_12_ambiguous_human_review(self):
        self.check(S.HUMAN_REVIEW,*fixture(O.INCONCLUSIVE),step=N.HUMAN_REVIEW_OUTCOME)
    def test_13_operator_saying_client_wants_bank_return_not_proof(self):
        a,b,c=fixture();e=replace(a.evidence[0],speaker='operator')
        self.check(S.HUMAN_REVIEW,replace(a,evidence=(e,)),b,c)
    def test_14_wrong_topic_does_not_match_claim(self):
        a,b,c=fixture();e=replace(a.evidence[0],topic=T.AMBIGUOUS)
        self.check(S.HUMAN_REVIEW,replace(a,evidence=(e,)),b,c)
    def test_15_uncited_message_not_validated(self):
        a,b,c=fixture();self.check(S.HUMAN_REVIEW,a,b,replace(c,evidence_refs=('unknown',)))
    def test_16_unauthorized_citation(self):
        a,b,c=fixture();e=replace(a.evidence[0],authorized=False)
        self.check(S.HUMAN_REVIEW,replace(a,evidence=(e,)),b,c)
    def test_17_duplicate_citation_invalid(self):
        a,b,c=fixture();self.check(S.INVALID,a,b,replace(c,evidence_refs=('m1','m1')))
    def test_18_no_citation_invalid(self):
        a,b,c=fixture();self.check(S.INVALID,a,b,replace(c,evidence_refs=()))
    def test_19_unknown_reason_invalid(self):
        a,b,c=fixture();self.check(S.INVALID,a,b,replace(c,reason_code='SOLD'))
    def test_20_forged_outcome_not_enum(self):
        a,b,c=fixture();self.check(S.INVALID,a,b,replace(c,outcome='SOLD'))
    def test_21_forged_bank_approval_not_outcome(self):
        a,b,c=fixture();self.check(S.INVALID,a,b,{'outcome':'APPROVED'})
    def test_22_revoked_session(self):
        a,b,c=fixture();self.check(S.DENIED,a,replace(b,authenticated_session=False),c)
    def test_23_revoked_store(self):
        a,b,c=fixture();self.check(S.DENIED,a,replace(b,store_grant=False),c)
    def test_24_missing_valid_closure(self):
        a,b,c=fixture();self.check(S.DENIED,a,replace(b,human_closure_verified=False),c)
    def test_25_lost_operator_assignment(self):
        a,b,c=fixture();self.check(S.DENIED,a,replace(b,human_owner_valid=False),c)
    def test_26_wrong_store(self):
        a,b,c=fixture();self.check(S.DENIED,a,replace(b,store='store-B'),c)
    def test_27_wrong_case(self):
        a,b,c=fixture();self.check(S.DENIED,a,replace(b,case='case-2'),c)
    def test_28_old_closure(self):
        a,b,c=fixture();self.check(S.STALE,a,replace(b,closure_event_id='closed-2'),c)
    def test_29_changed_snapshot(self):
        a,b,c=fixture();self.check(S.STALE,a,replace(b,snapshot_hash='sha-2'),c)
    def test_30_new_inbound(self):
        a,b,c=fixture();self.check(S.STALE,a,replace(b,message_watermark='m2'),c)
    def test_31_updated_case(self):
        a,b,c=fixture();self.check(S.STALE,a,replace(b,case_version=5),c)
    def test_32_updated_form(self):
        a,b,c=fixture();self.check(S.STALE,a,replace(b,form_version=7),c)
    def test_33_revocation_beats_new_inbound(self):
        a,b,c=fixture();self.check(S.DENIED,a,replace(b,authenticated_session=False,message_watermark='m2'),c)
    def test_34_grant_revocation_beats_old_hash(self):
        a,b,c=fixture();self.check(S.DENIED,a,replace(b,store_grant=False,snapshot_hash='old'),c)
    def test_35_string_flag_denied(self):
        a,b,c=fixture();self.check(S.DENIED,a,replace(b,bank_submission_proved='true'),c)
    def test_36_bool_version_denied(self):
        a,b,c=fixture();self.check(S.DENIED,a,replace(b,case_version=True),c)
    def test_37_cross_tenant_source_rejected(self):
        a,b,c=fixture();e=replace(a.evidence[0],store='store-B')
        self.check(S.DENIED,replace(a,evidence=(e,)),b,c)
    def test_38_cross_case_source_rejected(self):
        a,b,c=fixture();e=replace(a.evidence[0],case='case-2')
        self.check(S.DENIED,replace(a,evidence=(e,)),b,c)
    def test_39_duplicate_source_catalogue_denied(self):
        a,b,c=fixture();self.check(S.DENIED,replace(a,evidence=a.evidence*2),b,c)
    def test_40_invalid_missing_catalogue_denied(self):
        a,b,c=fixture();self.check(S.DENIED,a,replace(b,missing_required_field_codes=('A', 'A')),c)
    def test_41_fake_essential_flag_rejected(self):
        a,b,c=fixture();self.check(S.DENIED,a,replace(b,missing_required_field_codes=['a']),c)
    def test_42_model_reason_mismatch_rejected(self):
        a,b,c=fixture();self.check(S.INVALID,a,b,replace(c,reason_code='NEEDS_INFORMATION'))
    def test_43_operator_informal_bank_promise_not_bank_proof(self):
        a,b,c=fixture();self.check(S.REVIEW_ONLY,a,b,c,N.HUMAN_CHECK_BANK_SUBMISSION)
    def test_44_model_cannot_override_bank_proof_state(self):
        a,b,c=fixture();r=self.check(S.REVIEW_ONLY,a,b,c)
        self.assertIs(r.next_step,N.HUMAN_CHECK_BANK_SUBMISSION)

if __name__ == '__main__':unittest.main()
