"""S0 field-source checks; no real customer data or semantic extraction."""
import unittest,uuid
from backend.s0_f03_crossfront_evidence_local import (
    _untrusted_sources,_synthetic_claim,EvidenceResult,EvidenceState,
    S0F03LocalEvidenceReviewBridge,
)
from backend.s0_f03_operational_contracts_local import ProposedField,FieldKind
F=(ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,'preferencia ficticia'),)
MSG=str(uuid.uuid4())
def payload(value='preferencia ficticia',source=MSG):
    return {'proposalRef':'proposal-01','fields':[
        {'code':'observacao_sintetica','value':value,'sourceId':source}],
        'conflicts':[],'advisory':None}
class Tests(unittest.TestCase):
    def test_01_valid_shape_not_proof(self):
        self.assertEqual(_untrusted_sources(payload(),F),{'observacao_sintetica':uuid.UUID(MSG)})
    def test_02_value_mismatch_denied(self):
        self.assertIsNone(_untrusted_sources(payload(value='inventado'),F))
    def test_03_bad_message_id_denied(self):
        self.assertIsNone(_untrusted_sources(payload(source='fake'),F))
    def test_04_extra_permissions_denied(self):
        self.assertIsNone(_untrusted_sources({**payload(),'allowWrite':True},F))
    def test_05_conflict_requires_review(self):
        self.assertIsNone(_untrusted_sources({**payload(),'conflicts':[{'code':'x'}]},F))
    def test_06_advisory_not_field_proof(self):
        self.assertIsNone(_untrusted_sources({**payload(),'advisory':{'kind':'perdido'}},F))
    def test_07_exact_fixture_syntax_only(self):
        self.assertEqual(_synthetic_claim('observacao_sintetica=valor','observacao_sintetica'),'valor')
        self.assertIsNone(_synthetic_claim('texto observacao_sintetica=valor','observacao_sintetica'))
    def test_08_control_chars_denied(self):
        self.assertIsNone(_synthetic_claim('observacao_sintetica=','observacao_sintetica'))
        self.assertIsNone(_synthetic_claim('observacao_sintetica=a\nb','observacao_sintetica'))
    def test_09_no_disclosure(self):
        self.assertEqual(tuple(vars(EvidenceResult(EvidenceState.DENIED))),('state',))
    def test_10_guard_adapter(self):
        with self.assertRaises(TypeError):S0F03LocalEvidenceReviewBridge(object())
if __name__=='__main__':
    unittest.main()
