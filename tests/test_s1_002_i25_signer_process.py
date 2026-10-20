"""I25: testes rápidos do assinador filho, sem DB, GoTrue nem rede."""
import hashlib
import hmac
import time
import unittest
import uuid

from backend.identity_boundary import Denied, IdentityUnavailable, Principal
from backend.s1_gateway_signed_local import _proof_material
from backend.s1_signer_process_local import LocalSignerSupervisor, LocalSeparatedSignerGateway


class ProcessSignerTests(unittest.TestCase):
    def setUp(self):
        self.supervisor = LocalSignerSupervisor()
        self.id = uuid.uuid4()
        self.secret = b"i25-test-only-key-material-32byte!"  # >= 32? exact below
        self.secret = bytes(range(32))
        self.actor = uuid.uuid4()
        self.session = uuid.uuid4()
        self.operator = uuid.uuid4()

    def tearDown(self):
        self.supervisor.close()

    def material(self, *, issued=None, nonce=None):
        return _proof_material(
            "PAUSAR", self.actor, self.session,
            (None, None, None, None, self.operator, "AUSENCIA_TEMPORARIA"),
            int(time.time()) if issued is None else issued,
            uuid.uuid4() if nonce is None else nonce,
        )

    def test_01_valid_hmac_matches_sql_protocol(self):
        self.assertTrue(self.supervisor.load(self.id, self.secret))
        msg = self.material()
        self.assertEqual(self.supervisor.client.sign(self.id, msg),
                         hmac.new(self.secret, msg, hashlib.sha256).hexdigest())

    def test_02_unknown_key_denied(self):
        with self.assertRaises(Denied):
            self.supervisor.client.sign(self.id, self.material())

    def test_03_reject_short_key(self):
        self.assertFalse(self.supervisor.load(self.id, b"weak"))
        with self.assertRaises(Denied):
            self.supervisor.client.sign(self.id, self.material())

    def test_04_duplicate_keyid_cannot_rebind_secret(self):
        self.assertTrue(self.supervisor.load(self.id, self.secret))
        self.assertFalse(self.supervisor.load(self.id, bytes(reversed(range(32)))))
        msg = self.material()
        self.assertEqual(self.supervisor.client.sign(self.id, msg),
                         hmac.new(self.secret, msg, hashlib.sha256).hexdigest())

    def test_05_expired_material_denied(self):
        self.assertTrue(self.supervisor.load(self.id, self.secret))
        with self.assertRaises(Denied):
            self.supervisor.client.sign(self.id, self.material(issued=int(time.time())-200))

    def test_06_arbitrary_material_denied(self):
        self.assertTrue(self.supervisor.load(self.id, self.secret))
        with self.assertRaises(Denied):
            self.supervisor.client.sign(self.id, b"forged")

    def test_07_revoke_blocks_signing(self):
        self.assertTrue(self.supervisor.load(self.id, self.secret))
        self.assertTrue(self.supervisor.revoke(self.id))
        with self.assertRaises(Denied):
            self.supervisor.client.sign(self.id, self.material())

    def test_08_dead_worker_fail_closed(self):
        self.assertTrue(self.supervisor.load(self.id, self.secret))
        self.supervisor.terminate()
        with self.assertRaises(IdentityUnavailable):
            self.supervisor.client.sign(self.id, self.material())

    def test_09_gateway_has_no_signing_key_or_control_pipe(self):
        self.assertTrue(self.supervisor.load(self.id, self.secret))
        class DummyGoTrue:
            def verify(self, _authorization):
                raise RuntimeError("should not call")
        gateway = LocalSeparatedSignerGateway(
            "postgresql://prumo_s1_signed_login_ci:ci@127.0.0.1:5432/postgres",
            DummyGoTrue(), signer=self.supervisor.client, key_id=self.id)
        self.assertNotIn("signing_key", vars(gateway))
        self.assertNotIn("_control", vars(gateway))
        msg = self.material()
        result = gateway.proof(
            Principal(self.actor, self.session),
            "pausar", (self.operator, "AUSENCIA_TEMPORARIA"),
            issued=int(msg.decode().split("|")[-2]),
            nonce=uuid.UUID(msg.decode().split("|")[-1]),
        )
        self.assertEqual(result[-1], hmac.new(self.secret, msg, hashlib.sha256).hexdigest())

    def test_10_new_process_does_not_inherit_old_key(self):
        self.assertTrue(self.supervisor.load(self.id, self.secret))
        replacement = LocalSignerSupervisor()
        try:
            with self.assertRaises(Denied):
                replacement.client.sign(self.id, self.material())
        finally:
            replacement.close()

if __name__ == "__main__":
    unittest.main(verbosity=2)
