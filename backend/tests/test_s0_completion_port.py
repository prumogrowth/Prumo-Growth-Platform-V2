"""Test contract-order skeleton; every S0/model response is synthetic."""
from dataclasses import replace
import unittest

from backend.s0_openai_bridge.s0_completion_port import (
    CompletionRequest, CompletionState as State, S0Answer, S0AnswerKind as Kind,
    S0ClosedSnapshot, prepare_f03_completion_review,
)


class FakeS0:
    def __init__(self):
        self.calls=[]
        self.captured=S0ClosedSnapshot('store-A','case-1','close-1','hash-1',
                                       'm-4',7,3,'catalogue-1',
                                       'idempotency-1','assignment-1',2)
        self.initial=S0Answer(Kind.ACCEPTED,self.captured)
        self.final=S0Answer(Kind.ACCEPTED,self.captured)
    def begin(self, request):
        self.calls.append('begin')
        return self.initial
    def recheck(self, captured):
        self.calls.append('recheck')
        return self.final


class FakeF03:
    def __init__(self, failure=False, reply=None):
        self.calls=[]
        self.failure=failure
        self.reply=reply
    def propose(self, captured):
        self.calls.append('propose')
        if self.failure: raise RuntimeError('external model unavailable')
        return (self.reply if self.reply is not None else
                {'operation_kind':'human_close_extract','bank_status':'SOLD',
                 'model_claimed_grant':True})


def fixture():
    return CompletionRequest('case-1',7,'idempotency-1'),FakeS0(),FakeF03()


class Tests(unittest.TestCase):
    def check(self, expected, request=None, s0=None, model=None):
        default_request, default_s0, default_model=fixture()
        res=prepare_f03_completion_review(
            default_request if request is None else request,
            s0=default_s0 if s0 is None else s0,
            model=default_model if model is None else model)
        self.assertEqual(res.state,expected)
        self.assertFalse(hasattr(res,'applied'))
        self.assertFalse(hasattr(res,'bank_status'))
        return res

    def test_01_no_real_s0_transport_is_blocked(self):
        req,_,model=fixture()
        self.assertEqual(prepare_f03_completion_review(req,model=model).state,
                         State.BLOCKED_BY_S0_CONTRACT)
        self.assertEqual(model.calls,[])
    def test_02_no_model_transport_is_blocked(self):
        req,s0,_=fixture()
        self.assertEqual(prepare_f03_completion_review(req,s0=s0).state,
                         State.BLOCKED_BY_S0_CONTRACT)
        self.assertEqual(s0.calls,[])
    def test_03_request_has_no_store_or_actor_field(self):
        req,_,_=fixture()
        self.assertEqual(set(req.__dataclass_fields__),
                         {'case_ref','expected_case_version','idempotency_key'})
    def test_04_two_reads_surround_model(self):
        req,s0,model=fixture()
        res=prepare_f03_completion_review(req,s0=s0,model=model)
        self.assertEqual(res.state,State.S0_VALIDATION_REQUIRED)
        self.assertEqual(s0.calls,['begin','recheck'])
        self.assertEqual(model.calls,['propose'])
    def test_05_model_claim_cannot_create_bank_sale(self):
        req,s0,model=fixture()
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.S0_VALIDATION_REQUIRED)
    def test_06_invalid_request_blocks_without_port_calls(self):
        req,s0,model=fixture()
        req=replace(req,expected_case_version=True)
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.INVALID_REQUEST)
        self.assertEqual(s0.calls,[])
        self.assertEqual(model.calls,[])
    def test_07_denial_before_model(self):
        req,s0,model=fixture();s0.initial=S0Answer(Kind.DENIED)
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.DENIED)
        self.assertEqual(model.calls,[])
    def test_08_stale_before_model(self):
        req,s0,model=fixture();s0.initial=S0Answer(Kind.STALE)
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.STALE)
        self.assertEqual(model.calls,[])
    def test_09_unavailable_initial_port_fails_closed(self):
        req,s0,model=fixture();s0.initial=S0Answer(Kind.UNAVAILABLE)
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.BLOCKED_BY_S0_CONTRACT)
        self.assertEqual(model.calls,[])
    def test_10_cross_case_capture_denied(self):
        req,s0,model=fixture()
        s0.initial=S0Answer(Kind.ACCEPTED,replace(s0.captured,case_ref='other'))
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.DENIED)
        self.assertEqual(model.calls,[])
    def test_11_case_version_mismatch_denied(self):
        req,s0,model=fixture()
        s0.initial=S0Answer(Kind.ACCEPTED,replace(s0.captured,case_version=8))
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.DENIED)
        self.assertEqual(model.calls,[])
    def test_12_malformed_initial_envelope_denied(self):
        req,s0,model=fixture()
        s0.initial=S0Answer(Kind.ACCEPTED,replace(s0.captured,form_version=True))
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.INVALID_S0_RESPONSE)
        self.assertEqual(model.calls,[])
    def test_13_denial_after_model_cannot_leak_output(self):
        req,s0,model=fixture();s0.final=S0Answer(Kind.DENIED)
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.DENIED)
        self.assertEqual(model.calls,['propose'])
    def test_14_stale_after_model_cannot_leak_output(self):
        req,s0,model=fixture();s0.final=S0Answer(Kind.STALE)
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.STALE)
    def test_15_hash_change_after_model_stale(self):
        req,s0,model=fixture()
        s0.final=S0Answer(Kind.ACCEPTED,replace(s0.captured,snapshot_hash='other'))
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.STALE)
    def test_16_new_inbound_after_model_stale(self):
        req,s0,model=fixture()
        s0.final=S0Answer(Kind.ACCEPTED,replace(s0.captured,message_watermark='m-5'))
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.STALE)
    def test_17_assignment_related_closure_change_stale(self):
        req,s0,model=fixture()
        s0.final=S0Answer(Kind.ACCEPTED,replace(s0.captured,closure_event_ref='close-2'))
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.STALE)
    def test_18_model_unavailable_no_recheck(self):
        req,s0,_=fixture();model=FakeF03(failure=True)
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.MODEL_UNAVAILABLE)
        self.assertEqual(s0.calls,['begin'])
    def test_19_port_wrong_status_type_fail_closed(self):
        req,s0,model=fixture();s0.initial=S0Answer('ACCEPTED',s0.captured)
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.INVALID_S0_RESPONSE)
        self.assertEqual(model.calls,[])
    def test_20_malformed_recheck_fails_closed(self):
        req,s0,model=fixture();s0.final=S0Answer(Kind.ACCEPTED,None)
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.INVALID_S0_RESPONSE)


    def test_21_closure_request_key_must_match_current_request(self):
        req,s0,model=fixture()
        s0.initial=S0Answer(Kind.ACCEPTED,replace(s0.captured,completion_request_key='another-key'))
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.DENIED)
        self.assertEqual(model.calls,[])
    def test_22_same_case_other_idempotency_key_not_accepted(self):
        req,s0,model=fixture()
        self.assertEqual(prepare_f03_completion_review(
            replace(req,idempotency_key='new-click'),s0=s0,model=model).state,State.DENIED)
    def test_23_assignment_changed_during_model_is_stale(self):
        req,s0,model=fixture()
        s0.final=S0Answer(Kind.ACCEPTED,replace(s0.captured,assignment_ref='assignment-2'))
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,State.STALE)
    def test_24_assignment_version_changed_during_model_is_stale(self):
        req,s0,model=fixture()
        s0.final=S0Answer(Kind.ACCEPTED,replace(s0.captured,assignment_version=3))
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,State.STALE)
    def test_25_assignment_bool_version_invalid_before_model(self):
        req,s0,model=fixture()
        s0.initial=S0Answer(Kind.ACCEPTED,replace(s0.captured,assignment_version=True))
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.INVALID_S0_RESPONSE)
        self.assertEqual(model.calls,[])
    def test_26_assignment_missing_invalid_before_model(self):
        req,s0,model=fixture()
        s0.initial=S0Answer(Kind.ACCEPTED,replace(s0.captured,assignment_ref=''))
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.INVALID_S0_RESPONSE)
        self.assertEqual(model.calls,[])
    def test_27_model_returns_none_not_ready(self):
        req,s0,model=fixture()
        model=FakeF03(reply='not-structured')
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.MODEL_RESPONSE_INVALID)
        self.assertEqual(s0.calls,['begin','recheck'])
    def test_28_model_returns_wrong_operation_not_ready(self):
        req,s0,_=fixture()
        model=FakeF03(reply={'operation_kind':'recontact_plan','bank_status':'APPROVED'})
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.MODEL_RESPONSE_INVALID)
    def test_29_model_empty_dict_not_ready(self):
        req,s0,_=fixture()
        model=FakeF03(reply={})
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.MODEL_RESPONSE_INVALID)
    def test_30_revocation_wins_over_malformed_model_after_proposal(self):
        req,s0,_=fixture()
        s0.final=S0Answer(Kind.DENIED)
        model=FakeF03(reply='malformed')
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.DENIED)
    def test_31_after_model_request_echo_changed_cannot_reuse(self):
        req,s0,model=fixture()
        s0.final=S0Answer(Kind.ACCEPTED,replace(s0.captured,completion_request_key='replayed'))
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.STALE)
    def test_32_catalogue_changed_between_calls_stale(self):
        req,s0,model=fixture()
        s0.final=S0Answer(Kind.ACCEPTED,replace(s0.captured,catalogue_version='catalogue-2'))
        self.assertEqual(prepare_f03_completion_review(req,s0=s0,model=model).state,
                         State.STALE)

if __name__ == '__main__':
    unittest.main()
