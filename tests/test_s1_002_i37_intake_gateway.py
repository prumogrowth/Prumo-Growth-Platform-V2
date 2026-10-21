"""I37: strictly allowlisted intake and signed CAS proof, local unit tests."""
import hmac
import hashlib
import time
import unittest
import uuid
from backend.s1_gateway_intake_signed_local import intake_fields, LocalSignedIntakeOnlyGateway
from backend.s1_gateway_signed_local import _proof_material
from backend.s1_gateway_http_policy_local import serve_http_policy_local
from backend.identity_boundary import InvalidCommand, Principal, Denied

class FakeSigner:
    def __init__(self):self.records=[]
    def sign(self,key,material,authorization):
        self.records.append((key,material,authorization))
        return hmac.new(b"z"*32,material,hashlib.sha256).hexdigest()

class FakeIdentity:
    def verify(self,authorization):return Principal(uuid.UUID("00000000-0000-4000-8000-000000000001"),uuid.UUID("00000000-0000-4000-8000-000000000002"))

class TestIntake(unittest.TestCase):
    def setUp(self):
        self.actor=uuid.UUID("00000000-0000-4000-8000-000000000001")
        self.session=uuid.UUID("00000000-0000-4000-8000-000000000002")
        self.operator=uuid.UUID("00000000-0000-4000-8000-000000000003")
        self.signer=FakeSigner()
        self.gateway=LocalSignedIntakeOnlyGateway(
          "postgresql://prumo_s1_signed_login_ci:secret@127.0.0.1:5432/postgres",
          FakeIdentity(),signer=self.signer,key_id=uuid.uuid4())
    def test_01_valid_paused(self):
        self.assertEqual(intake_fields("intake",{"operador_id":str(self.operator),
            "pausar":True,"versao_esperada":1}), (self.operator,True,1))
    def test_02_valid_resume(self):
        self.assertEqual(intake_fields("intake",{"operador_id":str(self.operator),
            "pausar":False,"versao_esperada":99}), (self.operator,False,99))
    def test_03_reason_not_allowed(self):
        with self.assertRaises(InvalidCommand):intake_fields("intake",{"operador_id":str(self.operator),"pausar":True,"versao_esperada":1,"motivo_codigo":"AUSENCIA"})
    def test_04_legacy_route_not_allowed(self):
        with self.assertRaises(InvalidCommand):intake_fields("pausar",{"operador_id":str(self.operator),"pausar":True,"versao_esperada":1})
    def test_05_version_bool_rejected(self):
        with self.assertRaises(InvalidCommand):intake_fields("intake",{"operador_id":str(self.operator),"pausar":True,"versao_esperada":True})
    def test_06_paused_nonboolean_rejected(self):
        with self.assertRaises(InvalidCommand):intake_fields("intake",{"operador_id":str(self.operator),"pausar":"true","versao_esperada":1})
    def test_07_zero_version_rejected(self):
        with self.assertRaises(InvalidCommand):intake_fields("intake",{"operador_id":str(self.operator),"pausar":True,"versao_esperada":0})
    def test_08_overflow_version_rejected(self):
        with self.assertRaises(InvalidCommand):intake_fields("intake",{"operador_id":str(self.operator),"pausar":True,"versao_esperada":2**63})
    def test_09_strict_uuid_rejected(self):
        with self.assertRaises(InvalidCommand):intake_fields("intake",{"operador_id":str(self.operator).upper(),"pausar":True,"versao_esperada":1})
    def test_10_signed_action_revision(self):
        at=int(time.time())
        nonce=uuid.uuid4()
        result=self.gateway.proof(Principal(self.actor,self.session),self.operator,True,9,"Bearer test",issued=at,nonce=nonce)
        material=_proof_material("INTAKE",self.actor,self.session,
            (None,None,None,None,self.operator,"P:9"),at,nonce)
        self.assertEqual(result[-1],hmac.new(b"z"*32,material,hashlib.sha256).hexdigest())
        self.assertEqual(self.signer.records[0][1],material)
    def test_11_resume_not_equal_pause_proof(self):
        p=Principal(self.actor,self.session);ts=int(time.time());n=uuid.uuid4()
        a=self.gateway.proof(p,self.operator,True,4,"Bearer test",issued=ts,nonce=n)[-1]
        b=self.gateway.proof(p,self.operator,False,4,"Bearer test",issued=ts,nonce=n)[-1]
        self.assertNotEqual(a,b)
    def test_12_version_changes_proof(self):
        p=Principal(self.actor,self.session);ts=int(time.time());n=uuid.uuid4()
        a=self.gateway.proof(p,self.operator,True,4,"Bearer test",issued=ts,nonce=n)[-1]
        b=self.gateway.proof(p,self.operator,True,5,"Bearer test",issued=ts,nonce=n)[-1]
        self.assertNotEqual(a,b)
    def test_13_only_loopback_database(self):
        with self.assertRaises(ValueError):
            LocalSignedIntakeOnlyGateway("postgresql://prumo_s1_signed_login_ci:secret@remote.test/postgres",FakeIdentity(),signer=self.signer,key_id=uuid.uuid4())
    def test_14_intake_only_http_allowlist(self):
        server=serve_http_policy_local(self.gateway,allowed_commands=("intake",))
        try:
            self.assertEqual(server.server_address[0],"127.0.0.1")
        finally:server.server_close()
    def test_15_unknown_http_allowlist_rejected(self):
        with self.assertRaises(ValueError):
            serve_http_policy_local(self.gateway,allowed_commands=("intake","delete_all"))
if __name__=="__main__":unittest.main()
