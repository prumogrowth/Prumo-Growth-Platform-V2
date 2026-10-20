"""I27 mTLS unitarios: certificados efemeros e GoTrue HTTP sintetico.

Nao homologam identidade OS real, nem cadeia de certificados gerenciada em
infraestrutura. Segredos/chaves sao descartados junto com TemporaryDirectory.
"""
import hashlib
import hmac
import socket
import ssl
import tempfile
import threading
import time
import unittest
import uuid
from http.server import ThreadingHTTPServer

from test_s1_002_i26_independent_auth import MockGoTrue, fake_token
from backend.identity_boundary import Denied, IdentityUnavailable
from backend.s1_gateway_signed_local import _proof_material
from backend.s1_i27_ephemeral_certificates import (
    certificate_fingerprint, create_local_certificates)
from backend.s1_signer_mtls_local import (
    LocalMutualTlsSignerClient, LocalMutualTlsSignerSupervisor,
    _send_frame, _read_frame)


class MutualTlsSignerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix="s1-i27-pki-")
        cls.pki = create_local_certificates(cls.directory.name)
        cls.actor = uuid.uuid4()
        cls.session = uuid.uuid4()
        cls.operator = uuid.uuid4()
        cls.token = fake_token(cls.actor, cls.session)
        MockGoTrue.actor = str(cls.actor)
        MockGoTrue.token = cls.token
        cls.auth_server = ThreadingHTTPServer(("127.0.0.1",0),MockGoTrue)
        cls.auth_thread = threading.Thread(target=cls.auth_server.serve_forever,daemon=True)
        cls.auth_thread.start()
        cls.auth_url = "http://127.0.0.1:" + str(cls.auth_server.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.auth_server.shutdown()
        cls.auth_server.server_close()
        cls.auth_thread.join(timeout=3)
        cls.directory.cleanup()

    def setUp(self):
        p = self.pki
        self.signer = LocalMutualTlsSignerSupervisor(
            independent_auth_url=self.auth_url,
            publishable_key="only-ci-anon-key",
            ca=p["ca"],
            server_cert=p["signer"]["cert"],
            server_key=p["signer"]["key"],
            gateway_cert=p["gateway"]["cert"],
            gateway_key=p["gateway"]["key"],
            gateway_fingerprint=certificate_fingerprint(p["gateway"]["cert"]),
            server_fingerprint=certificate_fingerprint(p["signer"]["cert"]),
        )
        self.key_id = uuid.uuid4()
        self.key = bytes(range(32))
        self.assertTrue(self.signer.load(self.key_id,self.key))

    def tearDown(self):
        self.signer.close()

    def material(self, actor=None, session=None, timestamp=None):
        return _proof_material(
            "PAUSAR", actor or self.actor, session or self.session,
            (None,None,None,None,self.operator,"AUSENCIA_TEMPORARIA"),
            int(time.time()) if timestamp is None else timestamp, uuid.uuid4())

    def client(self, *, cert=None, key=None, ca=None, pin=None):
        p = self.pki
        return LocalMutualTlsSignerClient(
            port=self.signer.client._port, process=self.signer._process,
            ca=ca or p["ca"],
            cert=cert or p["gateway"]["cert"],
            key=key or p["gateway"]["key"],
            expected_server_fingerprint=pin or certificate_fingerprint(p["signer"]["cert"]))

    def test_01_valid_gateway_certificate_and_gotrue(self):
        data = self.material()
        signature = self.signer.client.sign(self.key_id,data,"Bearer "+self.token)
        self.assertEqual(signature, hmac.new(self.key,data,hashlib.sha256).hexdigest())

    def test_02_missing_gateway_client_certificate(self):
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,cafile=self.pki["ca"])
        try:
            with socket.create_connection(("127.0.0.1",self.signer.client._port),timeout=3) as raw:
                with ctx.wrap_socket(raw,server_hostname="localhost") as stream:
                    _send_frame(stream, {"action":"SIGN","key_id":str(self.key_id),
                                         "material":"ignored","authorization":"Bearer "+self.token})
                    response = _read_frame(stream)
                    self.assertNotEqual(response.get("status"),"SIGNED")
        except (OSError,ssl.SSLError):
            pass

    def test_03_other_valid_client_certificate_denied_by_pin(self):
        intruder = self.client(cert=self.pki["intruder"]["cert"],
                               key=self.pki["intruder"]["key"])
        with self.assertRaises(IdentityUnavailable):
            intruder.sign(self.key_id,self.material(),"Bearer "+self.token)

    def test_04_wrong_server_fingerprint_denied(self):
        client = self.client(pin="0"*64)
        with self.assertRaises(IdentityUnavailable):
            client.sign(self.key_id,self.material(),"Bearer "+self.token)

    def test_05_wrong_server_trust_anchor_denied(self):
        client = self.client(ca=self.pki["gateway"]["cert"])
        with self.assertRaises(IdentityUnavailable):
            client.sign(self.key_id,self.material(),"Bearer "+self.token)

    def test_06_invalid_gotrue_bearer_denied_after_mtls(self):
        with self.assertRaises(Denied):
            self.signer.client.sign(self.key_id,self.material(),"Bearer invalidbearer")

    def test_07_forged_actor_denied_after_mtls(self):
        with self.assertRaises(Denied):
            self.signer.client.sign(self.key_id,self.material(actor=uuid.uuid4()),
                                    "Bearer "+self.token)

    def test_08_forged_session_denied_after_mtls(self):
        with self.assertRaises(Denied):
            self.signer.client.sign(self.key_id,self.material(session=uuid.uuid4()),
                                    "Bearer "+self.token)

    def test_09_expired_timestamp_denied_after_mtls(self):
        with self.assertRaises(Denied):
            self.signer.client.sign(self.key_id,
                 self.material(timestamp=int(time.time())-90),"Bearer "+self.token)

    def test_10_revocation_in_memory_blocks_signature(self):
        self.assertTrue(self.signer.revoke(self.key_id))
        with self.assertRaises(Denied):
            self.signer.client.sign(self.key_id,self.material(),"Bearer "+self.token)

    def test_11_process_crash_fails_closed(self):
        self.signer.terminate()
        with self.assertRaises(IdentityUnavailable):
            self.signer.client.sign(self.key_id,self.material(),"Bearer "+self.token)

    def test_12_no_bearer_denied_at_client(self):
        with self.assertRaises(Denied):
            self.signer.client.sign(self.key_id,self.material())

    def test_13_local_only_authority_and_pin_required(self):
        p=self.pki
        common=dict(publishable_key="only-ci-anon-key",ca=p["ca"],
                    server_cert=p["signer"]["cert"],server_key=p["signer"]["key"],
                    gateway_cert=p["gateway"]["cert"],gateway_key=p["gateway"]["key"],
                    gateway_fingerprint=certificate_fingerprint(p["gateway"]["cert"]),
                    server_fingerprint=certificate_fingerprint(p["signer"]["cert"]))
        with self.assertRaises(ValueError):
            LocalMutualTlsSignerSupervisor(independent_auth_url="https://remote.example",
                                          **common)
        with self.assertRaises(ValueError):
            LocalMutualTlsSignerSupervisor(independent_auth_url=self.auth_url,
                                          **dict(common, gateway_fingerprint="not-a-pin"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
