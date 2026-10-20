"""I30: autoridade MAC em processo separado e assinador mTLS usando CHECK.

O mock GoTrue valida contrato apenas. E2E real usa GoTrue descartavel.
"""
import hashlib
import hmac
import os
from pathlib import Path
import shutil
import tempfile
import threading
import time
import unittest
import uuid
from http.server import ThreadingHTTPServer

from test_s1_002_i26_independent_auth import MockGoTrue, fake_token
from backend.identity_boundary import Denied, IdentityUnavailable
from backend.s1_i28_rotating_certificates import create_rotating_certificates,certificate_fingerprint
from backend.s1_i29_persistent_certificate_store import LocalCertificateState
from backend.s1_i30_signed_revocation_authority_local import LocalRevocationAuthoritySupervisor
from backend.s1_signer_mtls_authority_local import LocalAuthorityBackedSignerSupervisor
from backend.s1_gateway_signed_local import _proof_material


class AuthenticatedRevocationAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actor,cls.session,cls.operator=uuid.uuid4(),uuid.uuid4(),uuid.uuid4()
        cls.token=fake_token(cls.actor,cls.session)
        MockGoTrue.actor=str(cls.actor)
        MockGoTrue.token=cls.token
        cls.gotrue=ThreadingHTTPServer(("127.0.0.1",0),MockGoTrue)
        cls.thread=threading.Thread(target=cls.gotrue.serve_forever,daemon=True)
        cls.thread.start()
        cls.auth_url="http://127.0.0.1:"+str(cls.gotrue.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.gotrue.shutdown()
        cls.gotrue.server_close()
        cls.thread.join(timeout=3)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="s1-i30-auth-")
        self.pki=create_rotating_certificates(self.temp.name)
        self.old=certificate_fingerprint(self.pki["gateway"]["cert"])
        self.next=certificate_fingerprint(self.pki["gateway_next"]["cert"])
        self.rogue=certificate_fingerprint(self.pki["gateway_rogue"]["cert"])
        self.db=Path(self.temp.name)/"ledger.sqlite3"
        self.checkpoint=Path(self.temp.name)/"auth-checkpoint.json"
        LocalCertificateState(self.db).initialize(self.old)
        self.mac_key=bytes(reversed(range(32)))
        self.auth=self.start_authority(bootstrap=True)
        self.signer=self.start_signer()
        self.keyid=uuid.uuid4()
        self.secret=bytes(range(32))
        self.assertTrue(self.signer.load(self.keyid,self.secret))

    def start_authority(self,bootstrap=False):
        return LocalRevocationAuthoritySupervisor(
            db_path=self.db, checkpoint_path=self.checkpoint,
            secret=self.mac_key,bootstrap=bootstrap, initial_fp=self.old)

    def start_signer(self):
        p=self.pki
        return LocalAuthorityBackedSignerSupervisor(
            independent_auth_url=self.auth_url,publishable_key="ci-only",
            ca=p["ca"],server_cert=p["signer"]["cert"],server_key=p["signer"]["key"],
            gateway_cert=p["gateway"]["cert"],gateway_key=p["gateway"]["key"],
            gateway_fingerprint=self.old,
            server_fingerprint=certificate_fingerprint(p["signer"]["cert"]),
            checker=self.auth.client)

    def tearDown(self):
        self.signer.close()
        self.auth.close()
        self.temp.cleanup()

    def client(self,name="gateway_next"):
        p=self.pki[name]
        return self.signer.client_with_certificate(p["cert"],p["key"])

    def material(self,actor=None,session=None):
        return _proof_material("PAUSAR",actor or self.actor,session or self.session,
          (None,None,None,None,self.operator,"AUSENCIA_TEMPORARIA"),
          int(time.time()),uuid.uuid4())

    def proof(self,client=None):
        material=self.material()
        signed=(client or self.signer.client).sign(
            self.keyid,material,"Bearer "+self.token)
        self.assertEqual(signed,hmac.new(self.secret,material,hashlib.sha256).hexdigest())

    def stage(self):
        self.assertEqual(self.auth.stage_certificate(self.next,1),("STAGED",2))

    def rotated(self):
        self.stage()
        self.assertEqual(self.auth.revoke_certificate(self.old,2),("REVOKED",3))

    def test_01_valid_authority_allows_original(self):
        self.proof()
        self.assertEqual(self.auth.status()["version"],1)

    def test_02_successor_before_stage_denied(self):
        with self.assertRaises(IdentityUnavailable):
            self.proof(self.client())

    def test_03_overlap_with_signed_ledger(self):
        self.stage()
        self.proof()
        self.proof(self.client())

    def test_04_revoked_fingerprint_stays_denied(self):
        self.rotated()
        with self.assertRaises(IdentityUnavailable):
            self.proof()
        self.proof(self.client())

    def test_05_restart_signer_does_not_reset_authority(self):
        self.rotated()
        self.signer.close()
        self.signer=self.start_signer()
        self.assertTrue(self.signer.load(self.keyid,self.secret))
        with self.assertRaises(IdentityUnavailable):
            self.proof()
        self.proof(self.client())

    def test_06_unsigned_ledger_mutation_fails_closed(self):
        self.stage()
        from sqlite3 import connect
        with connect(self.db) as db:
            db.execute("UPDATE certificates SET state='REVOKED' WHERE fingerprint=?",
                       (self.old,))
        with self.assertRaises(IdentityUnavailable):
            self.proof()
        with self.assertRaises(IdentityUnavailable):
            self.auth.status()

    def test_07_corrupted_MAC_checkpoint_fails_closed(self):
        self.checkpoint.write_text('{"revision":1,"mac":"'+'0'*64+'"}')
        with self.assertRaises(IdentityUnavailable):
            self.proof()

    def test_08_replay_old_signed_snapshot_after_rotation_denied(self):
        backup_db=Path(self.temp.name)/"db-old.bak"
        backup_mac=Path(self.temp.name)/"mac-old.bak"
        shutil.copy2(self.db,backup_db)
        shutil.copy2(self.checkpoint,backup_mac)
        self.rotated()
        self.proof(self.client())
        self.signer.close()
        self.signer=self.start_signer()
        self.assertTrue(self.signer.load(self.keyid,self.secret))
        shutil.copy2(backup_db,self.db)
        shutil.copy2(backup_mac,self.checkpoint)
        with self.assertRaises(IdentityUnavailable):
            self.proof()
        self.assertFalse(self.auth.client.allowed(self.old))

    def test_09_killed_authority_fails_closed(self):
        self.auth.terminate()
        with self.assertRaises(IdentityUnavailable):
            self.proof()

    def test_10_stale_version_refused(self):
        self.stage()
        self.assertEqual(self.auth.revoke_certificate(self.old,1),("STALE",2))
        self.proof()

    def test_11_revoked_id_cannot_be_restaged(self):
        self.rotated()
        self.assertEqual(self.auth.stage_certificate(self.old,3),("DENIED",3))

    def test_12_rogue_cert_denied_under_same_CA(self):
        self.stage()
        with self.assertRaises(IdentityUnavailable):
            self.proof(self.client("gateway_rogue"))

    def test_13_signer_has_no_admin_channel_or_MAC_key(self):
        self.assertFalse(hasattr(self.signer,"stage_certificate"))
        self.assertFalse(hasattr(self.signer,"revoke_certificate"))
        self.assertFalse(hasattr(self.signer,"_state"))
        self.assertFalse(hasattr(self.signer.client,"_control"))
        self.assertFalse(hasattr(self.auth.client,"_admin"))

    def test_14_emergency_revoke_persists_across_signer_restart(self):
        self.rotated()
        self.assertEqual(self.auth.revoke_certificate(self.next,3),("REVOKED",4))
        self.signer.close()
        self.signer=self.start_signer()
        self.assertTrue(self.signer.load(self.keyid,self.secret))
        with self.assertRaises(IdentityUnavailable):
            self.proof(self.client())
        self.assertEqual(self.auth.status()["active_count"],0)

    def test_15_valid_authority_restart_with_current_signed_state(self):
        self.rotated()
        self.signer.close()
        self.auth.close()
        self.auth=self.start_authority()
        self.signer=self.start_signer()
        self.assertTrue(self.signer.load(self.keyid,self.secret))
        with self.assertRaises(IdentityUnavailable):
            self.proof()
        self.proof(self.client())

if __name__=="__main__":
    unittest.main(verbosity=2)
