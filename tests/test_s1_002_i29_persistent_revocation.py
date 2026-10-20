"""I29: 15 provas de tombstones persistentes com TLS e GoTrue sintético."""
import concurrent.futures
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
from backend.s1_i28_rotating_certificates import create_rotating_certificates, certificate_fingerprint
from backend.s1_i29_persistent_certificate_store import (
    LocalCertificateState, RevocationStateUnavailable)
from backend.s1_signer_mtls_persistent_local import LocalPersistentTlsSignerSupervisor
from backend.s1_gateway_signed_local import _proof_material


class PersistentCertificateTests(unittest.TestCase):
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
        self.temp=tempfile.TemporaryDirectory(prefix="s1-i29-cert-")
        self.pki=create_rotating_certificates(self.temp.name)
        self.old=certificate_fingerprint(self.pki["gateway"]["cert"])
        self.next=certificate_fingerprint(self.pki["gateway_next"]["cert"])
        self.other=certificate_fingerprint(self.pki["gateway_rogue"]["cert"])
        self.path=Path(self.temp.name)/"revocation.sqlite3"
        self.store=LocalCertificateState(self.path)
        self.store.initialize(self.old)
        self.keyid=uuid.uuid4()
        self.secret=bytes(range(32))
        self.signer=self.restart()
        self.assertTrue(self.signer.load(self.keyid,self.secret))

    def tearDown(self):
        self.signer.close()
        self.temp.cleanup()

    def restart(self):
        p=self.pki
        return LocalPersistentTlsSignerSupervisor(
            independent_auth_url=self.auth_url,publishable_key="ci-only-anon",
            ca=p["ca"],server_cert=p["signer"]["cert"],server_key=p["signer"]["key"],
            gateway_cert=p["gateway"]["cert"],gateway_key=p["gateway"]["key"],
            gateway_fingerprint=self.old,
            server_fingerprint=certificate_fingerprint(p["signer"]["cert"]),
            state_path=self.path)

    def data(self, actor=None, session=None):
        return _proof_material("PAUSAR", actor or self.actor, session or self.session,
            (None,None,None,None,self.operator,"AUSENCIA_TEMPORARIA"),
            int(time.time()),uuid.uuid4())

    def client(self,name="gateway_next"):
        p=self.pki[name]
        return self.signer.client_with_certificate(p["cert"],p["key"])

    def sign(self,client=None):
        data=self.data()
        actual=(client or self.signer.client).sign(
            self.keyid,data,"Bearer "+self.token)
        self.assertEqual(actual,hmac.new(self.secret,data,hashlib.sha256).hexdigest())

    def rotated(self):
        self.assertEqual(self.signer.stage_certificate(self.next,1),("STAGED",2))
        self.assertEqual(self.signer.revoke_certificate(self.old,2),("REVOKED",3))

    def test_01_initial_ledger_bootstrapped_exactly_once(self):
        self.sign()
        self.assertEqual(self.store.status()["version"],1)
        with self.assertRaises(FileExistsError):
            self.store.initialize(self.old)

    def test_02_unstaged_successor_denied(self):
        with self.assertRaises(IdentityUnavailable):
            self.sign(self.client())

    def test_03_staged_overlap_is_durable(self):
        self.signer.stage_certificate(self.next,1)
        self.sign()
        self.sign(self.client())
        self.assertEqual(LocalCertificateState(self.path).status()["active_count"],2)

    def test_04_revoked_gateway_fails_and_successor_works(self):
        self.rotated()
        with self.assertRaises(IdentityUnavailable):
            self.sign()
        self.sign(self.client())

    def test_05_restarted_signer_reads_tombstone_not_default_pin(self):
        self.rotated()
        self.signer.close()
        self.signer=self.restart()
        self.assertTrue(self.signer.load(self.keyid,self.secret))
        with self.assertRaises(IdentityUnavailable):
            self.sign()
        self.sign(self.client())
        self.assertEqual(self.signer.rotation_status()["version"],3)

    def test_06_revoked_identity_never_staged_after_restart(self):
        self.rotated()
        self.signer.close()
        self.signer=self.restart()
        self.assertEqual(self.signer.stage_certificate(self.old,3),("DENIED",3))

    def test_07_missing_ledger_blocks_live_and_restart(self):
        self.path.unlink()
        with self.assertRaises(IdentityUnavailable):
            self.sign()
        self.signer.close()
        with self.assertRaises(RevocationStateUnavailable):
            self.restart()
        # tearDown needs reference with close(); previous supervisor closed.
        self.signer=self._stopped_placeholder()

    def _stopped_placeholder(self):
        class Stop:
            def close(self): pass
        return Stop()

    def test_08_corrupt_ledger_fails_closed(self):
        self.signer.close()
        self.path.write_bytes(b"not sqlite")
        os.chmod(self.path,0o600)
        with self.assertRaises(RevocationStateUnavailable):
            self.restart()
        self.signer=self._stopped_placeholder()

    def test_09_permissive_file_mode_refused(self):
        os.chmod(self.path,0o644)
        with self.assertRaises(IdentityUnavailable):
            self.sign()
        os.chmod(self.path,0o600)

    def test_10_stale_version_cannot_override_revocation(self):
        self.rotated()
        self.assertEqual(self.signer.stage_certificate(self.old,1),("STALE",3))
        self.assertEqual(self.signer.revoke_certificate(self.next,2),("STALE",3))

    def test_11_parallel_CAS_only_one_stage_wins(self):
        import threading
        barrier=threading.Barrier(2)
        def race(fp):
            barrier.wait(timeout=5)
            return self.signer.stage_certificate(fp,1)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(race,[self.next,self.other]))
        self.assertEqual(sorted(x[0] for x in results),["STAGED","STALE"])
        self.assertEqual(self.store.status()["active_count"],2)

    def test_12_rogue_certificate_denied_even_if_CA_valid(self):
        self.signer.stage_certificate(self.next,1)
        with self.assertRaises(IdentityUnavailable):
            self.sign(self.client("gateway_rogue"))

    def test_13_audit_minimal_after_restart(self):
        self.rotated()
        self.signer.close()
        self.signer=self.restart()
        status=self.signer.rotation_status()
        self.assertEqual(status["events"],[(2,"CERT_STAGED"),(3,"CERT_REVOKED")])
        self.assertNotIn(self.old,str(status))
        self.assertNotIn(self.next,str(status))
        self.assertNotIn(self.token,str(status))

    def test_14_rollback_detected_after_process_observes_new_revision(self):
        backup=Path(self.temp.name)/"version-one.sqlite3"
        shutil.copy2(self.path,backup)
        self.signer.stage_certificate(self.next,1)
        self.sign(self.client())  # assinador observa revisao 2
        shutil.copy2(backup,self.path)
        with self.assertRaises(IdentityUnavailable):
            self.sign()  # revisao 1 nunca deve ser aceita NO MESMO PROCESSO

    def test_15_emergency_revoke_all_stays_blocked_after_restart(self):
        self.rotated()
        self.assertEqual(self.signer.revoke_certificate(self.next,3),("REVOKED",4))
        self.signer.close()
        self.signer=self.restart()
        self.assertTrue(self.signer.load(self.keyid,self.secret))
        with self.assertRaises(IdentityUnavailable):
            self.sign(self.client())
        self.assertEqual(self.signer.rotation_status()["active_count"],0)


if __name__=="__main__":
    unittest.main(verbosity=2)
