"""I26: GoTrue sintético apenas para unidade. E2E usa GoTrue REAL local.

A resposta do mock nao autentica criptograficamente JWT e NAO pode ser
utilizada como evidencia de validacao criptografica na implantacao.
"""
import base64
import hashlib
import hmac
import json
import threading
import time
import unittest
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from backend.identity_boundary import Denied, IdentityUnavailable, Principal
from backend.s1_gateway_signed_local import _proof_material
from backend.s1_signer_process_local import LocalSignerSupervisor
from backend.s1_signer_independent_gotrue_local import LocalIndependentlyAuthenticatedGateway


class MockGoTrue(BaseHTTPRequestHandler):
    token = ""
    actor = ""
    def do_GET(self):
        if self.path != "/auth/v1/user" or self.headers.get("Authorization") != "Bearer " + self.token:
            self.send_response(401)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        body=json.dumps({"id":self.actor,"role":"authenticated"}).encode()
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


def fake_token(actor, session):
    def encoded(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
    return encoded({"alg":"HS256","typ":"JWT"})+"."+encoded({
        "role":"authenticated","sub":str(actor),"session_id":str(session)
    })+".syntheticsignaturenotvalidatedinunittest"


class IndependentAuthProcessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actor=uuid.uuid4()
        cls.session=uuid.uuid4()
        cls.operator=uuid.uuid4()
        cls.token=fake_token(cls.actor,cls.session)
        MockGoTrue.actor=str(cls.actor)
        MockGoTrue.token=cls.token
        cls.server=ThreadingHTTPServer(("127.0.0.1",0),MockGoTrue)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.auth_url="http://127.0.0.1:"+str(cls.server.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def setUp(self):
        self.supervisor=LocalSignerSupervisor(
            independent_auth_url=self.auth_url,publishable_key="public-ci-key")
        self.keyid=uuid.uuid4()
        self.secret=bytes(range(32))
        self.assertTrue(self.supervisor.load(self.keyid,self.secret))

    def tearDown(self):
        self.supervisor.close()

    def material(self,actor=None,session=None,issued=None):
        return _proof_material(
            "PAUSAR",self.actor if actor is None else actor,
            self.session if session is None else session,
            (None,None,None,None,self.operator,"AUSENCIA_TEMPORARIA"),
            int(time.time()) if issued is None else issued,uuid.uuid4())

    def test_01_independent_gotrue_verifies_before_signing(self):
        m=self.material()
        got=self.supervisor.client.sign(self.keyid,m,"Bearer "+self.token)
        self.assertEqual(got,hmac.new(self.secret,m,hashlib.sha256).hexdigest())

    def test_02_no_bearer_refused(self):
        with self.assertRaises(Denied):
            self.supervisor.client.sign(self.keyid,self.material())

    def test_03_invalid_bearer_refused(self):
        with self.assertRaises(Denied):
            self.supervisor.client.sign(self.keyid,self.material(),"Bearer invalidstring")


    def test_04_other_actor_material_rejected(self):
        with self.assertRaises(Denied):
            self.supervisor.client.sign(
                self.keyid,self.material(actor=uuid.uuid4()),"Bearer "+self.token)

    def test_05_other_session_material_rejected(self):
        with self.assertRaises(Denied):
            self.supervisor.client.sign(
                self.keyid,self.material(session=uuid.uuid4()),"Bearer "+self.token)

    def test_06_expired_proof_denied_even_with_token(self):
        with self.assertRaises(Denied):
            self.supervisor.client.sign(
                self.keyid,self.material(issued=int(time.time())-300),
                "Bearer "+self.token)

    def test_07_new_process_starts_without_key(self):
        replacement=LocalSignerSupervisor(independent_auth_url=self.auth_url,
                                          publishable_key="public-ci-key")
        try:
            with self.assertRaises(Denied):
                replacement.client.sign(self.keyid,self.material(),"Bearer "+self.token)
        finally:
            replacement.close()

    def test_08_bad_auth_config_denied(self):
        with self.assertRaises(ValueError):
            LocalSignerSupervisor(independent_auth_url="https://example.com",
                                  publishable_key="public-ci-key")
        with self.assertRaises(ValueError):
            LocalSignerSupervisor(independent_auth_url=self.auth_url)

    def test_09_authority_unavailable_fail_closed(self):
        other=LocalSignerSupervisor(independent_auth_url="http://127.0.0.1:1",
                                    publishable_key="public-ci-key")
        try:
            self.assertTrue(other.load(self.keyid,self.secret))
            with self.assertRaises(IdentityUnavailable):
                other.client.sign(self.keyid,self.material(),"Bearer "+self.token)
        finally:
            other.close()

    def test_10_gateway_requires_bearer_when_signing(self):
        class NoGoTrue:
            pass
        gateway=LocalIndependentlyAuthenticatedGateway(
            "postgresql://prumo_s1_signed_login_ci:ci@127.0.0.1:5432/postgres",
            NoGoTrue(),signer=self.supervisor.client,key_id=self.keyid)
        self.assertFalse(hasattr(gateway,"signing_key"))
        with self.assertRaises(Denied):
            gateway.proof(Principal(self.actor,self.session),"pausar",
                          (self.operator,"AUSENCIA_TEMPORARIA"),
                          authorization="Bearer badtoken")

if __name__=="__main__":
    unittest.main(verbosity=2)
