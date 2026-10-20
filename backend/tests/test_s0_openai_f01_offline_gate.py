"""Synthetic F01 guard regression; no OpenAI/Meta/SQL calls."""
import unittest
from dataclasses import replace
from backend.s0_openai_bridge.f01_offline_gate import (
    F01Capture, F01Current, F01ModelProposal, F01Review, F01Status,
    review_f01_offline,
)


def fixtures():
    cap = F01Capture("shop-A", "case-1", "cycle-1", "req-1", 3,
                     "msg-1", "knowledge-v1", "prompt-v1", ("msg-1",))
    now = F01Current("shop-A", "case-1", "cycle-1", 3, "msg-1",
                     "knowledge-v1", "prompt-v1", True, True, True,
                     False, False, False, "sales_reply")
    proposed = F01ModelProposal("req-1", "sales_reply", "Texto fictício para revisão", ("msg-1",))
    return cap, now, proposed


class F01OfflineGateTests(unittest.TestCase):
    def check(self, expected, cap=None, now=None, proposal=None):
        a,b,c=fixtures()
        result=review_f01_offline(cap if cap is not None else a,
                                   now if now is not None else b,
                                   proposal if proposal is not None else c)
        self.assertEqual(result.status, expected)
        if expected != F01Status.REVIEW_ONLY:
            self.assertEqual(result.review_text, "")
            self.assertEqual(result.source_message_refs, ())
        return result

    def test_01_happy_path_review_not_send(self):
        res=self.check(F01Status.REVIEW_ONLY)
        self.assertNotIn('send', res.__dataclass_fields__)
        self.assertEqual(res.source_message_refs, ('msg-1',))
    def test_02_no_live_capability(self):
        self.assertFalse(hasattr(F01Review,'send_whatsapp'))
    def test_03_handoff_silences_f01(self):
        _,n,_=fixtures();self.check(F01Status.DENIED, now=replace(n,has_handoff_history=True))
    def test_04_human_current_owner_blocks(self):
        _,n,_=fixtures();self.check(F01Status.DENIED, now=replace(n,ai_is_owner=False))
    def test_05_current_pause_blocks(self):
        _,n,_=fixtures();self.check(F01Status.DENIED, now=replace(n,ai_suspended=True))
    def test_06_revoked_store_permission_blocks(self):
        _,n,_=fixtures();self.check(F01Status.DENIED, now=replace(n,store_authorized=False))
    def test_07_revoked_session_blocks(self):
        _,n,_=fixtures();self.check(F01Status.DENIED, now=replace(n,session_authorized=False))
    def test_08_optout_blocks(self):
        _,n,_=fixtures();self.check(F01Status.DENIED, now=replace(n,opted_out=True))
    def test_09_current_new_inbound_stale(self):
        _,n,_=fixtures();self.check(F01Status.STALE, now=replace(n,message_watermark='msg-2'))
    def test_10_case_changed_stale(self):
        _,n,_=fixtures();self.check(F01Status.STALE, now=replace(n,case_version=4))
    def test_11_new_knowledge_requires_rereview(self):
        _,n,_=fixtures();self.check(F01Status.STALE, now=replace(n,knowledge_version='v2'))
    def test_12_new_prompt_requires_rereview(self):
        _,n,_=fixtures();self.check(F01Status.STALE, now=replace(n,prompt_version='v2'))
    def test_13_wrong_store_denied(self):
        _,n,_=fixtures();self.check(F01Status.DENIED, now=replace(n,store='shop-B'))
    def test_14_wrong_case_denied(self):
        _,n,_=fixtures();self.check(F01Status.DENIED, now=replace(n,case='case-2'))
    def test_15_wrong_cycle_denied(self):
        _,n,_=fixtures();self.check(F01Status.DENIED, now=replace(n,cycle='cycle-2'))
    def test_16_wrong_purpose_denied(self):
        _,n,_=fixtures();self.check(F01Status.DENIED, now=replace(n,purpose='human_close_extract'))
    def test_17_malformed_authority_flag_denied(self):
        _,n,_=fixtures();self.check(F01Status.DENIED, now=replace(n,ai_suspended='false'))
    def test_18_malformed_version_denied(self):
        _,n,_=fixtures();self.check(F01Status.DENIED, now=replace(n,case_version=True))
    def test_19_handoff_outranks_stale_state(self):
        _,n,_=fixtures();self.check(F01Status.DENIED, now=replace(n,has_handoff_history=True,case_version=4))
    def test_20_revocation_outranks_malformed_model(self):
        _,n,_=fixtures();self.check(F01Status.DENIED, now=replace(n,session_authorized=False), proposal={})
    def test_21_model_cannot_impersonate_operation(self):
        _,_,p=fixtures();self.check(F01Status.INVALID_PROPOSAL, proposal=replace(p,operation_kind='human_close_extract'))
    def test_22_model_wrong_request(self):
        _,_,p=fixtures();self.check(F01Status.INVALID_PROPOSAL, proposal=replace(p,request_id='req-2'))
    def test_23_model_unrecognized_evidence(self):
        _,_,p=fixtures();self.check(F01Status.INVALID_PROPOSAL, proposal=replace(p,source_message_refs=('msg-x',)))
    def test_24_model_duplicate_evidence(self):
        _,_,p=fixtures();self.check(F01Status.INVALID_PROPOSAL, proposal=replace(p,source_message_refs=('msg-1','msg-1')))
    def test_25_model_blank_text(self):
        _,_,p=fixtures();self.check(F01Status.INVALID_PROPOSAL, proposal=replace(p,proposed_text=' '))
    def test_26_model_overlong_text(self):
        _,_,p=fixtures();self.check(F01Status.INVALID_PROPOSAL, proposal=replace(p,proposed_text='x'*2001))
    def test_27_model_wrong_text_type(self):
        _,_,p=fixtures();self.check(F01Status.INVALID_PROPOSAL, proposal=replace(p,proposed_text=['x']))
    def test_28_no_source_allowlist(self):
        c,_,_=fixtures();self.check(F01Status.DENIED, cap=replace(c,allowed_message_refs=()))
    def test_29_duplicate_source_allowlist(self):
        c,_,_=fixtures();self.check(F01Status.DENIED, cap=replace(c,allowed_message_refs=('msg-1','msg-1')))
    def test_30_other_store_independent_fixture(self):
        c,n,p=fixtures();c=replace(c,store='shop-B');n=replace(n,store='shop-B')
        self.check(F01Status.REVIEW_ONLY,cap=c,now=n,proposal=p)
    def test_31_no_legacy_handoff_reactivation(self):
        c,n,p=fixtures();n=replace(n,has_handoff_history=True,ai_is_owner=True)
        self.check(F01Status.DENIED,cap=c,now=n,proposal=p)
    def test_32_wrong_model_type(self):
        self.check(F01Status.INVALID_PROPOSAL, proposal={'proposed_text':'test'})

if __name__ == '__main__':unittest.main()
