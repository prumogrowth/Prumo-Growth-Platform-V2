"""I74 security contract: canonical proof, independent signer, local-only DSN."""
import unittest
import uuid

from backend.identity_boundary import Principal, InvalidCommand
from backend.s1_gateway_export_signed_local import LocalSignedExportGateway
from backend.s1_gateway_export_local import export_fields

SHOP="86320000-0000-4000-8000-000000000001"
ACTOR=uuid.UUID("86310000-0000-4000-8000-000000000004")
SESSION=uuid.UUID("86310000-0000-4000-8000-000000000005")
KEY=uuid.UUID("86310000-0000-4000-8000-000000000003")
NONCE=uuid.UUID("86310000-0000-4000-8000-000000000002")

class Signer:
    def __init__(self):self.calls=[]
    def sign(self,key,material,authorization):
        self.calls.append((key,material,authorization))
        return "a"*64

class I74ExportTests(unittest.TestCase):
    def test_bound_fields_and_domain(self):
        with self.assertRaises(ValueError):
            LocalSignedExportGateway(
             "postgresql://prumo_s1_export_signed_login_ci:pw@localhost/postgres",
             object(),signer=Signer(),key_id=KEY)

    def test_exact_material_order(self):
        signer=Signer()
        class Auth:
            def verify(self,_):return Principal(ACTOR,SESSION)
        gate=LocalSignedExportGateway(
         "postgresql://prumo_s1_export_signed_login_ci:pw@localhost:54322/postgres",
         Auth(),signer=signer,key_id=KEY)
        fields=export_fields({"tipo":"canais","loja_id":SHOP,"apos":None,"limite":20})
        proof=gate.proof(Principal(ACTOR,SESSION),fields,"Bearer test",
                          issued=123456,nonce=NONCE)
        parts=signer.calls[0][1].decode().split("|")
        self.assertEqual(len(parts),12)
        self.assertEqual(parts[:4],["prumo-s1-i20-v1","EXPORT74",str(ACTOR),str(SESSION)])
        self.assertEqual(parts[4:10],[SHOP,"-","-","-","-","E:C:20"])
        self.assertEqual(parts[10:],["123456",str(NONCE)])
        self.assertEqual(signer.calls[0][0],KEY)
        self.assertEqual(proof[-1],"a"*64)
        self.assertEqual(proof[2],"canais")

    def test_no_remote_or_postgres_login(self):
        class Auth:
            def verify(self,_):return Principal(ACTOR,SESSION)
        for dsn in (
          "postgresql://postgres:pw@localhost/postgres",
          "postgresql://prumo_s1_export_signed_login_ci:pw@remote.example/postgres",
          "postgresql://prumo_s1_export_signed_login_ci:pw@localhost/production"):
            with self.assertRaises(ValueError):
                LocalSignedExportGateway(dsn,Auth(),signer=Signer(),key_id=KEY)

    def test_reject_extra_actor_field_and_wrong_type(self):
        with self.assertRaises(InvalidCommand):
            export_fields({"tipo":"lotes","loja_id":SHOP,"apos":None,"limite":1,
                           "actor":str(ACTOR)})
        with self.assertRaises(InvalidCommand):
            export_fields({"tipo":"lotes","loja_id":SHOP,"apos":None,"limite":True})
if __name__=="__main__":unittest.main()
