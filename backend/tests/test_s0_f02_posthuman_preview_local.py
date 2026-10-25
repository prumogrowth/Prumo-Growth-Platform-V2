"""S0-owned synthetic post-human template preflight input guard."""
import unittest,uuid
from backend.s0_f02_posthuman_preview_local import (
  S0F02LocalPostHumanPreview,PreviewResult,PreviewState,
  PostHumanPreviewRequest,_valid_request
)
class Tests(unittest.TestCase):
 def test_01_valid_manager_preview_shape(self):
  self.assertTrue(_valid_request(PostHumanPreviewRequest(str(uuid.uuid4()),'policy-001')))
 def test_02_wrong_uuid_denied(self):
  self.assertFalse(_valid_request(PostHumanPreviewRequest('fake','policy-001')))
 def test_03_malformed_policy_version_denied(self):
  self.assertFalse(_valid_request(PostHumanPreviewRequest(str(uuid.uuid4()),'policy invalid')))
 def test_04_boolean_not_policy_string(self):
  self.assertFalse(_valid_request(PostHumanPreviewRequest(str(uuid.uuid4()),True)))
 def test_05_no_extra_authority_in_response(self):
  self.assertEqual(tuple(vars(PreviewResult(PreviewState.PREVIEW_ONLY_LEGACY_C04_BLOCKED))),('state',))
 def test_06_incompatible_base_refused(self):
  with self.assertRaises(TypeError):
   S0F02LocalPostHumanPreview(object(),object(),'broken')
if __name__=='__main__':unittest.main()
