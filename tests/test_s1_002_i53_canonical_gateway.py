"""I53: independently domain-separated signed canonical intake gateway."""
import hmac
import hashlib
import base64
import time
import unittest
import uuid
from backend.s1_gateway_intake_canonical_local import (
    LocalSignedCanonicalIntakeGateway, _SQL_CANONICAL_INTAKE)
from backend.s1_gateway_intake_signed_local import (
    LocalSignedIntakeOnlyGateway, _SQL_INTAKE, intake_fields)
from backend.s1_gateway_signed_local import _proof_material
from backend.identity_boundary import InvalidCommand, Principal
from backend.s1_signer_mtls_authority_local import _sign_with_verified_identity

class FakeSigner:
    def __init__(self):
        self.proofs=[]
    def sign(self,key,material,authorization):
        self.proofs.append((material,authorization))
        return hmac.new(b"Q"*32,material,hashlib.sha256).hexdigest()

class TestCanonicalIntake(unittest.TestCase):
    def setUp(self):
        self.signer=FakeSigner()
        self.actor=uuid.UUID("00000000-0000-4000-8000-000000000021")
        self.session=uuid.UUID("00000000-0000-4000-8000-000000000022")
        self.operator=uuid.UUID("00000000-0000-4000-8000-000000000023")
        dsn="postgresql://prumo_s1_signed_login_ci:temp@127.0.0.1:5432/postgres"
        self.g=LocalSignedCanonicalIntakeGateway(
            dsn,None,signer=self.signer,key_id=uuid.uuid4())
        self.old=LocalSignedIntakeOnlyGateway(
            dsn,None,signer=self.signer,key_id=self.g.key_id)
        self.principal=Principal(self.actor,self.session)
    def test_01_sql_fixed_to_v53(self):
        self.assertEqual(self.g._statement,_SQL_CANONICAL_INTAKE)
        self.assertNotEqual(self.g._statement,_SQL_INTAKE)
        self.assertIn("invocar_intake_v53",self.g._statement)
    def test_02_independent_hmac_domain(self):
        t=int(time.time());n=uuid.uuid4()
        new=self.g.proof(self.principal,self.operator,True,1,"Bearer ephemeral",issued=t,nonce=n)
        old=self.old.proof(self.principal,self.operator,True,1,"Bearer ephemeral",issued=t,nonce=n)
        self.assertNotEqual(new[-1],old[-1])
        expected=_proof_material("INTAKE53",self.actor,self.session,
              (None,None,None,None,self.operator,"P:1"),t,n)
        self.assertEqual(new[-1],hmac.new(b"Q"*32,expected,hashlib.sha256).hexdigest())
    def test_03_pause_resume_and_revision_bound(self):
        t=int(time.time());n=uuid.uuid4()
        pause=self.g.proof(self.principal,self.operator,True,2,"Bearer ephemeral",issued=t,nonce=n)
        resume=self.g.proof(self.principal,self.operator,False,2,"Bearer ephemeral",issued=t,nonce=n)
        stale=self.g.proof(self.principal,self.operator,True,3,"Bearer ephemeral",issued=t,nonce=n)
        self.assertEqual(len({pause[-1],resume[-1],stale[-1]}),3)
    def test_04_strict_body_no_extra_fields(self):
        with self.assertRaises(InvalidCommand):
            intake_fields("intake",{"operador_id":str(self.operator),
                                   "pausar":True,"versao_esperada":1,"ator_id":str(self.actor)})
    def test_05_legacy_http_command_denied(self):
        with self.assertRaises(InvalidCommand):
            intake_fields("pausar",{"operador_id":str(self.operator),
                                   "pausar":True,"versao_esperada":1})
    def test_06_only_disposable_postgres_dsn(self):
        with self.assertRaises(ValueError):
            LocalSignedCanonicalIntakeGateway(
              "postgresql://prumo_s1_signed_login_ci:temp@db.example.com/postgres",
              None,signer=self.signer,key_id=self.g.key_id)

    def test_07_independent_authority_accepts_only_canonical_intake53(self):
        class FakeIndependentGoTrue:
            def verify(inner,authorization):
                self.assertEqual(authorization,"Bearer ephemeral")
                return self.principal
        proof=self.g.proof(self.principal,self.operator,True,7,"Bearer ephemeral")
        material=self.signer.proofs[-1][0]
        signed=_sign_with_verified_identity(
            {"action":"SIGN","key_id":str(self.g.key_id),
             "material":base64.b64encode(material).decode("ascii"),
             "authorization":"Bearer ephemeral"},
            {self.g.key_id:b"Q"*32},FakeIndependentGoTrue())
        self.assertEqual(signed["status"],"SIGNED")
        self.assertEqual(signed["signature"],proof[-1])
    def test_08_signer_rejects_wrong_session_or_bad_intake53_shape(self):
        class WrongPrincipal:
            def verify(inner,authorization):
                return Principal(self.actor,uuid.uuid4())
        self.g.proof(self.principal,self.operator,True,7,"Bearer ephemeral")
        material=self.signer.proofs[-1][0]
        payload={"action":"SIGN","key_id":str(self.g.key_id),
                 "material":base64.b64encode(material).decode("ascii"),
                 "authorization":"Bearer ephemeral"}
        self.assertEqual(_sign_with_verified_identity(payload,
            {self.g.key_id:b"Q"*32},WrongPrincipal())["status"],"DENIED")
        class CorrectPrincipal:
            def verify(inner,authorization):return self.principal
        invalid=material.replace(b"|P:7|",b"|P:0|")
        payload["material"]=base64.b64encode(invalid).decode("ascii")
        self.assertEqual(_sign_with_verified_identity(payload,
            {self.g.key_id:b"Q"*32},CorrectPrincipal())["status"],"DENIED")

if __name__=="__main__":unittest.main()
