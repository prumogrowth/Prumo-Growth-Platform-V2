"""S0 F02 crossfront read-only output boundary."""
import unittest
from backend.s0_f02_posthuman_compatibility_local import (
    _candidate,F02RecheckResult,F02RecheckState,
    S0F02LocalPostHumanCompatibilityBridge,
)
GOOD={'status':'READY_FOR_S0_RECHECK','attemptId':'a1','templateId':'t1',
      'templateVersion':'v1','category':'MARKETING'}
class Tests(unittest.TestCase):
    def test_01_s2_normal_output_shape(self):self.assertTrue(_candidate(GOOD))
    def test_02_f02_not_due_does_not_grant(self):
        self.assertFalse(_candidate({'status':'NOT_DUE'}))
    def test_03_extra_send_grant_denied(self):
        self.assertFalse(_candidate({**GOOD,'send':True}))
    def test_04_model_permission_denied(self):
        self.assertFalse(_candidate({**GOOD,'status':'SENT'}))
    def test_05_nonphysical_bridge_denied(self):
        with self.assertRaises(TypeError):
            S0F02LocalPostHumanCompatibilityBridge(object(),'not-a-dsn')
    def test_06_unknown_template_category_denied(self):
        self.assertFalse(_candidate({**GOOD,'category':'OTHER'}))
    def test_07_multitenant_ref_syntax_denied(self):
        self.assertFalse(_candidate({**GOOD,'templateId':'t1\nhack'}))
    def test_08_result_only_returns_state(self):
        self.assertEqual(tuple(vars(F02RecheckResult(
            F02RecheckState.LEGACY_C04_HUMAN_CASE_INCOMPATIBLE))),('state',))
if __name__=='__main__':unittest.main()
