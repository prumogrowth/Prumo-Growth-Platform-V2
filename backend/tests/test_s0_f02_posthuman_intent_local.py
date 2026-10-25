"""F02 posthuman intent S0 audit validation, no outbound or scheduling."""
import unittest,uuid
from backend.s0_f02_posthuman_preview_local import PostHumanPreviewRequest
from backend.s0_f02_posthuman_intent_local import (
 S0F02LocalPostHumanIntentStore,PostHumanIntentRequest,IntentResult,
 IntentState,_valid,_proposal_hash
)
def make():return PostHumanIntentRequest(
 PostHumanPreviewRequest(str(uuid.uuid4()),'policy-001'),
 'EXPLICIT_REVIEW_SYNTHETIC_ONLY','b'*64,'f02-posthuman-0001')
class Tests(unittest.TestCase):
 def test_01_valid(self):self.assertTrue(_valid(make()))
 def test_02_no_generative_approval(self):
  x=make();self.assertFalse(_valid(PostHumanIntentRequest(
    x.preview,'GENERATE_AND_SEND','b'*64,x.idempotency_key)))
 def test_03_invalid_audit_digest(self):
  x=make();self.assertFalse(_valid(PostHumanIntentRequest(
    x.preview,x.decision,'fake',x.idempotency_key)))
 def test_04_no_short_replay(self):
  x=make();self.assertFalse(_valid(PostHumanIntentRequest(
    x.preview,x.decision,x.manager_evidence_sha256,'a')))
 def test_05_response_only_state(self):
  self.assertEqual(tuple(vars(IntentResult(IntentState.RECORDED_AUDIT_ONLY))),('state',))
 def test_06_cannot_wire_nonphysical_preview(self):
  with self.assertRaises(TypeError):S0F02LocalPostHumanIntentStore(object())
 def test_07_hash_binds_template_context(self):
  r=type('Receipt',(),dict(store_ref='s',case_ref='c',closure_event_ref='e'))()
  js=dict(attemptId='a',templateId='t',templateVersion='v1',category='MARKETING')
  x=make();one=_proposal_hash(js,x,r,'channel')
  self.assertNotEqual(one,_proposal_hash({**js,'category':'UTILITY'},x,r,'channel'))
  self.assertNotEqual(one,_proposal_hash(js,x,r,'other-channel'))
if __name__=='__main__':unittest.main()
