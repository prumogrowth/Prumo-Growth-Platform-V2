"""I62 signed exceptional transfer and revocation contracts; no DB."""
import base64
import hashlib
import hmac
import time
import unittest
import uuid
from backend.s1_gateway_excecao_caso_local import (
 LocalSignedCaseExceptionGateway,exception_fields,safe_exception_result,_SQL_EXC62)
from backend.s1_gateway_signed_local import _proof_material
from backend.s1_signer_mtls_authority_local import _sign_with_verified_identity
from backend.identity_boundary import Principal,InvalidCommand,IdentityUnavailable

class Signer:
 def sign(self,k,material,authorization):
  return hmac.new(b"X"*32,material,hashlib.sha256).hexdigest()

class TestI62(unittest.TestCase):
 def setUp(self):
  self.a=uuid.uuid4();self.s=uuid.uuid4();self.ids=tuple(uuid.uuid4() for _ in range(4))
  self.principal=Principal(self.a,self.s)
  self.g=LocalSignedCaseExceptionGateway(
   "postgresql://prumo_s1_signed_login_ci:ci@127.0.0.1:5432/postgres",
   None,signer=Signer(),key_id=uuid.uuid4())
 def test01_move_exact_arguments(self):
  data=dict(zip(("loja_id","caso_id","atribuicao_esperada_id","destino_id"),map(str,self.ids)))
  self.assertEqual(exception_fields("mover_excecao",data),("MOVE",self.ids))
  self.assertIn("invocar_excecao_i62",_SQL_EXC62)
 def test02_revoke_fields_no_actor(self):
  self.assertEqual(exception_fields("revogar_excecao",{"excecao_id":str(self.ids[0])}),
   ("REVOKE",(self.ids[0],None,None,None)))
 def test03_reject_arbitrary_actor(self):
  with self.assertRaises(InvalidCommand):exception_fields("mover_excecao",{
   "loja_id":str(self.ids[0]),"caso_id":str(self.ids[1]),
   "atribuicao_esperada_id":str(self.ids[2]),"destino_id":str(self.ids[3]),
   "gestor_id":str(self.a)})
 def test04_reject_extra_action(self):
  with self.assertRaises(InvalidCommand):
   exception_fields("revogar_excecao",{"excecao_id":str(self.ids[0]),"destino_id":str(self.ids[3])})
 def test05_domain_sep_move_revoke(self):
  t=int(time.time());n=uuid.uuid4()
  a=self.g.proof(self.principal,"MOVE",self.ids,"Bearer demo",issued=t,nonce=n)
  b=self.g.proof(self.principal,"REVOKE",(self.ids[0],None,None,None),"Bearer demo",issued=t,nonce=n)
  self.assertNotEqual(a[-1],b[-1])
  exp=_proof_material("EXC62M",self.a,self.s,(*self.ids,None,None),t,n)
  self.assertEqual(a[-1],hmac.new(b"X"*32,exp,hashlib.sha256).hexdigest())
 def test06_signer_validates_real_subject(self):
  t=int(time.time());n=uuid.uuid4()
  proof=self.g.proof(self.principal,"MOVE",self.ids,"Bearer local",issued=t,nonce=n)
  material=_proof_material("EXC62M",self.a,self.s,(*self.ids,None,None),t,n)
  class V:
   def verify(_,authorization):return self.principal
  req={"action":"SIGN","key_id":str(self.g.key_id),
       "material":base64.b64encode(material).decode(),"authorization":"Bearer local"}
  self.assertEqual(_sign_with_verified_identity(req,{self.g.key_id:b"X"*32},V())["signature"],proof[-1])
 def test07_signer_rejects_forged_actor(self):
  material=_proof_material("EXC62M",uuid.uuid4(),self.s,(*self.ids,None,None),int(time.time()),uuid.uuid4())
  class V:
   def verify(_,authorization):return self.principal
  req={"action":"SIGN","key_id":str(self.g.key_id),
       "material":base64.b64encode(material).decode(),"authorization":"Bearer local"}
  self.assertEqual(_sign_with_verified_identity(req,{self.g.key_id:b"X"*32},V())["status"],"DENIED")
 def test08_remote_database_denied(self):
  with self.assertRaises(ValueError):
   LocalSignedCaseExceptionGateway(
    "postgresql://prumo_s1_signed_login_ci:ci@remote.example.com/postgres",
    None,signer=Signer(),key_id=uuid.uuid4())
 def test09_reply_projection_rejects_pii(self):
  value={"outcome":"MOVED_CASE_EXCEPTION","case_id":str(self.ids[0]),
         "assignment_id":str(self.ids[1]),"exception_id":str(self.ids[2])}
  self.assertEqual(safe_exception_result("MOVE",value),value)
  with self.assertRaises(IdentityUnavailable):
   safe_exception_result("MOVE",{**value,"telefone":"secret"})
 def test10_revoke_projection(self):
  self.assertEqual(safe_exception_result("REVOKE",{"outcome":"REVOKED_CASE_ACCESS"}),
                   {"outcome":"REVOKED_CASE_ACCESS"})
  with self.assertRaises(IdentityUnavailable):
   safe_exception_result("REVOKE",{"outcome":"REVOKED_CASE_ACCESS","case_id":str(self.ids[0])})
if __name__=="__main__":unittest.main()
