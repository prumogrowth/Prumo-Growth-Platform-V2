"""Local-only S0 synthetic human field CAS input and authority unit guards."""
from __future__ import annotations
import unittest
from unittest.mock import patch
from backend.tests.test_s0_f03_history_manifest_local import target
from backend.s0_f03_operational_contracts_local import ProposedField,FieldKind
from backend.s0_f03_version_reservation_local import VersionVector
from backend.s0_f03_field_application_local import (
    HumanDecision,FieldCAS,HumanFieldRequest,_inputs,ApplicationState,
    S0F03LocalHumanFieldApplicationStore,apply_human_s0_synthetic_fields,
)
from backend.identity_boundary import Principal
import uuid

K=b'fixture-only-content-seal-key-more-than-32-bytes'
F=(FieldCAS(ProposedField('campo_sintetico',FieldKind.TEXT_ONLY,'valor'),None),)
V=VersionVector(1,1,1,1,1)
def req(fields=F,decision=HumanDecision.EXPLICIT_APPROVE_SYNTHETIC_FIELDS):
    return HumanFieldRequest(target(),V,'request-cas-0001','test-key-v1',
                             fields,decision,'a'*64,'human-apply-0001')
class Identity:
    def verify(self,_):
        return Principal(uuid.uuid4(),uuid.uuid4())

class Tests(unittest.TestCase):
    def test_01_valid_explicit_human_request(self):
        self.assertIsNotNone(_inputs(req(),K))
    def test_02_empty_fields_denied(self):
        self.assertIsNone(_inputs(req(()),K))
    def test_03_old_hash_malformed_denied(self):
        self.assertIsNone(_inputs(req((FieldCAS(F[0].proposed,'wrong'),)),K))
    def test_04_duplicate_fields_denied(self):
        self.assertIsNone(_inputs(req(F+F),K))
    def test_05_invalid_human_evidence_denied(self):
        r=req()
        broken=HumanFieldRequest(r.binding,r.version,r.request_ref,r.key_version,
                 r.fields,r.decision,'invalid',r.idempotency_key)
        self.assertIsNone(_inputs(broken,K))
    def test_06_missing_s1_blocked_without_db(self):
        store=object.__new__(S0F03LocalHumanFieldApplicationStore)
        store._dsn='postgresql://postgres:fixture@localhost/prumo_s0_test_fake'
        result=apply_human_s0_synthetic_fields(
            'Bearer fixture',req(),identity=Identity(),store=store,s1=None,key=K)
        self.assertIs(result.state,ApplicationState.BLOCKED_S1)
    def test_07_bad_hmac_secret_denied(self):
        store=object.__new__(S0F03LocalHumanFieldApplicationStore)
        store._dsn='postgresql://postgres:fixture@localhost/prumo_s0_test_fake'
        with patch.object(Identity,'verify') as auth:
            result=apply_human_s0_synthetic_fields(
                'Bearer fixture',req(),identity=Identity(),store=store,s1=None,
                key=b'short')
        self.assertIs(result.state,ApplicationState.DENIED)
        auth.assert_not_called()
    def test_08_result_hides_customer_content(self):
        from backend.s0_f03_field_application_local import ApplicationResult
        obj=ApplicationResult(ApplicationState.DENIED)
        self.assertEqual(tuple(vars(obj)),('state',))
if __name__=='__main__':
    unittest.main()
