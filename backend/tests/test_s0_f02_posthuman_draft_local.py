"""E04 F02 S0-only private post-human review draft. No executable plan."""
import unittest
from datetime import datetime,timezone,timedelta
from uuid import uuid4
from backend.s0_f02_posthuman_preview_local import PostHumanPreviewRequest
from backend.s0_f02_posthuman_intent_local import PostHumanIntentRequest
from backend.s0_f02_posthuman_draft_local import (
 S0F02PostHumanDraftLocal,PostHumanDraftRequest,DraftState,DraftResult,
 _valid_request,_hash)
def make():
 return PostHumanDraftRequest(
   PostHumanIntentRequest(PostHumanPreviewRequest(str(uuid4()),'policy-001'),
    'EXPLICIT_REVIEW_SYNTHETIC_ONLY','a'*64,'f02-human-intent-0001'),
   datetime.now(timezone.utc)+timedelta(hours=48),
   'draft-e04-key-0001')
class Tests(unittest.TestCase):
 def test_01_strict_draft_data(self):self.assertTrue(_valid_request(make()))
 def test_02_naive_date_rejected(self):
  r=make()
  self.assertFalse(_valid_request(PostHumanDraftRequest(
   r.intent,datetime.now(),r.draft_key)))
 def test_03_short_key_rejected(self):
  r=make()
  self.assertFalse(_valid_request(PostHumanDraftRequest(
   r.intent,r.proposed_at,'x')))
 def test_04_send_flag_not_allowed(self):
  r=make()
  self.assertFalse(_valid_request({'intent':r.intent,'sendNow':True}))
 def test_05_invalid_manager_evidence_rejected(self):
  r=make()
  bad=PostHumanIntentRequest(r.intent.preview,r.intent.decision,
        'garbage',r.intent.idempotency_key)
  self.assertFalse(_valid_request(PostHumanDraftRequest(
    bad,r.proposed_at,r.draft_key)))
 def test_06_no_authority_in_result(self):
  self.assertEqual(tuple(vars(DraftResult(DraftState.DRAFT_RECORDED_REVIEW_ONLY))),('state',))
 def test_07_nonphysical_preview_rejected(self):
  with self.assertRaises(TypeError):S0F02PostHumanDraftLocal(object())
if __name__=='__main__':
 unittest.main()
