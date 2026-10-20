"""S1-002/I28: 15 testes adversariais de ciclo certificado TLS, só CI.

GoTrue aqui é mock de contrato. E2E exercita GoTrue real em Docker.
"""
import hashlib
import hmac
import tempfile
import threading
import time
import unittest
import uuid
from http.server import ThreadingHTTPServer

from test_s1_002_i26_independent_auth import MockGoTrue, fake_token
from backend.identity_boundary import Denied, IdentityUnavailable
from backend.s1_gateway_signed_local import _proof_material
from backend.s1_i28_rotating_certificates import (
    create_rotating_certificates, certificate_fingerprint)
from backend.s1_signer_mtls_rotation_local import LocalRotatingTlsSignerSupervisor


class ServiceCertificateLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix="s1-i28-pki-")
        cls.pki = create_rotating_certificates(cls.directory.name)
        cls.actor, cls.session, cls.operator = uuid.uuid4(),uuid.uuid4(),uuid.uuid4()
        cls.token = fake_token(cls.actor,cls.session)
        MockGoTrue.actor = str(cls.actor)
        MockGoTrue.token = cls.token
        cls.auth_server = ThreadingHTTPServer(("127.0.0.1",0),MockGoTrue)
        cls.thread = threading.Thread(target=cls.auth_server.serve_forever,daemon=True)
        cls.thread.start()
        cls.auth_url="http://127.0.0.1:"+str(cls.auth_server.server_address[1])
        cls.old_fp=certificate_fingerprint(cls.pki["gateway"]["cert"])
        cls.next_fp=certificate_fingerprint(cls.pki["gateway_next"]["cert"])
        cls.rogue_fp=certificate_fingerprint(cls.pki["gateway_rogue"]["cert"])

    @classmethod
    def tearDownClass(cls):
        cls.auth_server.shutdown()
        cls.auth_server.server_close()
        cls.thread.join(timeout=4)
        cls.directory.cleanup()

    def setUp(self):
        p=self.pki
        self.supervisor=LocalRotatingTlsSignerSupervisor(
            independent_auth_url=self.auth_url,publishable_key="only-ci-anon-key",
            ca=p["ca"],server_cert=p["signer"]["cert"],server_key=p["signer"]["key"],
            gateway_cert=p["gateway"]["cert"],gateway_key=p["gateway"]["key"],
            gateway_fingerprint=self.old_fp,
            server_fingerprint=certificate_fingerprint(p["signer"]["cert"]))
        self.key_id=uuid.uuid4()
        self.secret=bytes(range(32))
        self.assertTrue(self.supervisor.load(self.key_id,self.secret))

    def tearDown(self):
        self.supervisor.close()

    def material(self, actor=None, session=None):
        return _proof_material(
            "PAUSAR",actor or self.actor,session or self.session,
            (None,None,None,None,self.operator,"AUSENCIA_TEMPORARIA"),
            int(time.time()),uuid.uuid4())

    def next_client(self):
        return self.supervisor.client_with_certificate(
            self.pki["gateway_next"]["cert"],self.pki["gateway_next"]["key"])

    def rogue_client(self):
        return self.supervisor.client_with_certificate(
            self.pki["gateway_rogue"]["cert"],self.pki["gateway_rogue"]["key"])

    def proof(self,client=None):
        material=self.material()
        signature=(client or self.supervisor.client).sign(
            self.key_id,material,"Bearer "+self.token)
        self.assertEqual(signature,
                         hmac.new(self.secret,material,hashlib.sha256).hexdigest())

    def test_01_original_client_valid(self):
        self.proof()
        self.assertEqual(self.supervisor.rotation_status()["version"],1)

    def test_02_successor_denied_before_authorization(self):
        with self.assertRaises(IdentityUnavailable):
            self.proof(self.next_client())

    def test_03_new_certificate_staged_with_cas(self):
        self.assertEqual(self.supervisor.stage_certificate(self.next_fp,1),("STAGED",2))
        self.proof(self.next_client())

    def test_04_overlapping_certificates_both_work(self):
        self.assertEqual(self.supervisor.stage_certificate(self.next_fp,1),("STAGED",2))
        self.proof()
        self.proof(self.next_client())

    def test_05_revocation_blocks_old_certificate(self):
        self.assertEqual(self.supervisor.stage_certificate(self.next_fp,1),("STAGED",2))
        self.assertEqual(self.supervisor.revoke_certificate(self.old_fp,2),("REVOKED",3))
        with self.assertRaises(IdentityUnavailable):
            self.proof()
        self.proof(self.next_client())

    def test_06_revoked_certificate_cannot_be_reauthorized(self):
        self.supervisor.stage_certificate(self.next_fp,1)
        self.supervisor.revoke_certificate(self.old_fp,2)
        self.assertEqual(self.supervisor.stage_certificate(self.old_fp,3),("DENIED",3))

    def test_07_stale_revision_cannot_change_identity(self):
        self.supervisor.stage_certificate(self.next_fp,1)
        self.assertEqual(self.supervisor.revoke_certificate(self.old_fp,1),("STALE",2))
        self.proof()

    def test_08_random_certificate_denied(self):
        with self.assertRaises(IdentityUnavailable):
            self.proof(self.rogue_client())

    def test_09_invalid_fingerprint_denied(self):
        self.assertEqual(self.supervisor.stage_certificate("not-a-fingerprint",1),("DENIED",1))

    def test_10_no_more_than_two_active_identities(self):
        self.supervisor.stage_certificate(self.next_fp,1)
        self.assertEqual(self.supervisor.stage_certificate(self.rogue_fp,2),("DENIED",2))

    def test_11_gotrue_still_rejects_forged_user(self):
        self.supervisor.stage_certificate(self.next_fp,1)
        with self.assertRaises(Denied):
            self.next_client().sign(self.key_id,self.material(actor=uuid.uuid4()),
                                    "Bearer "+self.token)

    def test_12_gateway_has_no_certificate_admin_method(self):
        self.assertFalse(hasattr(self.supervisor.client,"stage_certificate"))
        self.assertFalse(hasattr(self.next_client(),"revoke_certificate"))
        self.assertFalse(hasattr(self.supervisor.client,"_control"))

    def test_13_audit_minimal_no_fingerprint_or_secrets(self):
        self.supervisor.stage_certificate(self.next_fp,1)
        self.supervisor.revoke_certificate(self.old_fp,2)
        status=self.supervisor.rotation_status()
        self.assertEqual(status["events"],[(2,"CERT_STAGED"),(3,"CERT_REVOKED")])
        self.assertEqual(status["active_count"],1)
        self.assertEqual(status["revoked_count"],1)
        self.assertNotIn(self.old_fp,str(status))
        self.assertNotIn(self.next_fp,str(status))
        self.assertNotIn(self.token,str(status))

    def test_14_emergency_revoke_last_identity_fails_closed(self):
        self.assertEqual(self.supervisor.revoke_certificate(self.old_fp,1),("REVOKED",2))
        with self.assertRaises(IdentityUnavailable):
            self.proof()
        self.assertEqual(self.supervisor.rotation_status()["active_count"],0)

    def test_15_supervisor_crash_stops_all_signing(self):
        self.supervisor.terminate()
        with self.assertRaises(IdentityUnavailable):
            self.proof()


if __name__=="__main__":
    unittest.main(verbosity=2)
