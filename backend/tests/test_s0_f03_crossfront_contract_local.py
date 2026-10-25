"""Offline S0-S2 output-shape checks; no claim that JS status is S0 grant."""
import unittest
from backend.s0_f03_crossfront_contract_local import _candidate,CrossFrontResult,CrossFrontState
from backend.s0_f03_operational_contracts_local import ProposedField,FieldKind
F=(ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,'valor'),)
OK={'status':'S0_RECHECK_ONLY','fieldCodes':['observacao_sintetica'],
    'snapshotRef':'a'*64}

class Tests(unittest.TestCase):
    def test_01_valid_shape_only_returns_claimed_digest(self):
        self.assertEqual(_candidate(OK,F),'a'*64)
    def test_02_javascript_status_is_not_human_grant(self):
        self.assertIsNone(_candidate({**OK,'status':'APPLIED_SYNTHETIC_ONLY'},F))
    def test_03_foreign_field_is_denied(self):
        self.assertIsNone(_candidate({**OK,'fieldCodes':['cpf']},F))
    def test_04_unsorted_fields_denied(self):
        two=F+(ProposedField('produto_sintetico',FieldKind.CATALOG_CODE,'MODELO'),)
        self.assertIsNone(_candidate({**OK,'fieldCodes':['produto_sintetico','observacao_sintetica']},two))
    def test_05_metadata_digest_wrong_shape_denied(self):
        self.assertIsNone(_candidate({**OK,'snapshotRef':'invalid'},F))
    def test_06_extra_permission_key_denied(self):
        self.assertIsNone(_candidate({**OK,'allowWrite':True},F))
    def test_07_empty_fields_denied(self):
        self.assertIsNone(_candidate(OK,()))
    def test_08_malformed_list_denied(self):
        self.assertIsNone(_candidate({**OK,'fieldCodes':'observacao_sintetica'},F))
    def test_09_human_result_does_not_disclose_data(self):
        result=CrossFrontResult(CrossFrontState.REVIEW_ONLY)
        self.assertEqual(tuple(vars(result)),('state',))

if __name__=='__main__':
    unittest.main()
