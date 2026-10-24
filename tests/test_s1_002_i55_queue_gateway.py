"""I55 strict signed queue protocol: no direct private grants or blind claim."""
import base64
import hashlib
import hmac
import time
import unittest
import uuid
from backend.s1_gateway_fila_canonical_local import LocalSignedCanonicalQueueGateway,queue_fields,_SQL_QUEUE,_client_safe_result,_is_authorization_denial
from backend.identity_boundary import InvalidCommand,Principal,IdentityUnavailable
from backend.s1_signer_mtls_authority_local import _sign_with_verified_identity
from backend.s1_gateway_signed_local import _proof_material

class Signer:
    def __init__(self):self.material=None
    def sign(self,key,material,authorization):
        self.material=material
        return hmac.new(b"E"*32,material,hashlib.sha256).hexdigest()

class TestQueueV55(unittest.TestCase):
    def setUp(self):
        self.signer=Signer()
        self.key=uuid.uuid4()
        self.actor=uuid.uuid4()
        self.session=uuid.uuid4()
        self.shop=uuid.uuid4()
        self.cycle=uuid.uuid4()
        self.principal=Principal(self.actor,self.session)
        self.gateway=LocalSignedCanonicalQueueGateway(
          "postgresql://prumo_s1_signed_login_ci:x@127.0.0.1:5432/postgres",
          None,signer=self.signer,key_id=self.key)
    def test_01_list_exact_fields(self):
        self.assertEqual(queue_fields("fila",{"loja_id":str(self.shop)}),
                         (self.shop,None,None))
        self.assertIn("invocar_fila_v55",_SQL_QUEUE)
    def test_02_claim_exact_cas(self):
        self.assertEqual(queue_fields("assumir_fila",
            {"loja_id":str(self.shop),"ciclo_id":str(self.cycle),"versao_esperada":2}),
            (self.shop,self.cycle,2))
    def test_03_reject_extra_actor_or_unknown(self):
        for cmd,body in (("fila",{"loja_id":str(self.shop),"ator_id":str(self.actor)}),
          ("pausar",{"loja_id":str(self.shop)}),
          ("assumir_fila",{"loja_id":str(self.shop),"ciclo_id":str(self.cycle),
                           "versao_esperada":1,"case_id":str(self.cycle)})):
            with self.assertRaises(InvalidCommand):queue_fields(cmd,body)
    def test_04_reject_bool_numeric_and_bad_uuid(self):
        for ver in (True,0,-1,2**63,"1"):
            with self.assertRaises(InvalidCommand):
                queue_fields("assumir_fila",{"loja_id":str(self.shop),
                             "ciclo_id":str(self.cycle),"versao_esperada":ver})
        with self.assertRaises(InvalidCommand):
            queue_fields("fila",{"loja_id":"NOT-UUID"})
    def test_05_separate_proofs_and_bound_version(self):
        n=uuid.uuid4();now=int(time.time())
        q=self.gateway.proof(self.principal,self.shop,None,None,"Bearer x",nonce=n,issued=now)
        c=self.gateway.proof(self.principal,self.shop,self.cycle,1,"Bearer x",nonce=n,issued=now)
        d=self.gateway.proof(self.principal,self.shop,self.cycle,2,"Bearer x",nonce=n,issued=now)
        self.assertEqual(len({q[-1],c[-1],d[-1]}),3)
        expected=_proof_material("FILA55C",self.actor,self.session,
            (self.shop,self.cycle,None,None,None,"C:2"),now,n)
        self.assertEqual(d[-1],hmac.new(b"E"*32,expected,hashlib.sha256).hexdigest())
    def test_06_independent_signer_validates_queue(self):
        class V:
            def verify(inner,auth):return self.principal
        sig=self.gateway.proof(self.principal,self.shop,self.cycle,1,"Bearer test")
        p={"action":"SIGN","key_id":str(self.key),
           "material":base64.b64encode(self.signer.material).decode(),
           "authorization":"Bearer test"}
        self.assertEqual(_sign_with_verified_identity(p,{self.key:b"E"*32},V())["signature"],sig[-1])
    def test_07_independent_signer_denies_forged_session(self):
        class V:
            def verify(inner,auth):return Principal(self.actor,uuid.uuid4())
        self.gateway.proof(self.principal,self.shop,None,None,"Bearer test")
        p={"action":"SIGN","key_id":str(self.key),
           "material":base64.b64encode(self.signer.material).decode(),
           "authorization":"Bearer test"}
        self.assertEqual(_sign_with_verified_identity(p,{self.key:b"E"*32},V())["status"],"DENIED")
    def test_08_reject_remote_dsn(self):
        with self.assertRaises(ValueError):
            LocalSignedCanonicalQueueGateway(
             "postgresql://prumo_s1_signed_login_ci:x@remote.example.com/postgres",
             None,signer=self.signer,key_id=self.key)
    def test_09_rejects_privileged_list_payload_expansion(self):
        valid={"outcome":"QUEUE_LIST","items":[{
          "concessionaria_id":str(self.shop),"lead_id":str(self.actor),
          "ciclo_id":str(self.cycle),"versao":1}]}
        self.assertEqual(_client_safe_result("fila",valid),valid)
        for forged in (
            {**valid,"telefone":"secret"},
            {"outcome":"QUEUE_LIST","items":[{**valid["items"][0],"telefone":"secret"}]},
            {"outcome":"QUEUE_LIST","items":valid["items"]*26},
            {"outcome":"QUEUE_LIST","items":[{**valid["items"][0],"versao":True}]},
            {"outcome":"QUEUE_LIST","items":{}},
        ):
            with self.assertRaises(IdentityUnavailable):
                _client_safe_result("fila",forged)

    def test_10_claim_payload_strict_and_safe(self):
        ok={"outcome":"CLAIMED_BY_MANAGER","case_id":str(self.cycle),
            "assignment_id":str(self.actor),"version":2}
        self.assertEqual(_client_safe_result("assumir_fila",ok),ok)
        for outcome in ("CONFLICT","ALREADY_HAS_CASE"):
            self.assertEqual(_client_safe_result("assumir_fila",{"outcome":outcome}),{"outcome":outcome})
        for bad in (
          {**ok,"telefone":"sensitive"},
          {**ok,"case_id":"fake-id"},
          {**ok,"version":True},
          {"outcome":"CONFLICT","lead_id":str(self.actor)},
        ):
            with self.assertRaises(IdentityUnavailable):
                _client_safe_result("assumir_fila",bad)

    def test_11_sql_transient_failures_never_masquerade_as_permission_denial(self):
        for code in ("40001","40P01","55P03","57014",None):
            self.assertFalse(_is_authorization_denial(code))
        for code in ("42501","22023","23514","23505"):
            self.assertTrue(_is_authorization_denial(code))

if __name__=="__main__":unittest.main()
