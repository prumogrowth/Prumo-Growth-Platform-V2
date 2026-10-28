"""One real PG17 + GoTrue + PostgREST + Edge I85 journey.

The stack is created/prepared/served by I84 in the CI, not by fixtures. Every
HTTP administrative operation below goes through the real Deno Edge worker.
"""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from urllib import request, error
from uuid import uuid4
from local_admin import boundary as b, environment as e
from integration.i85 import bootstrap as i85


class Journey(unittest.TestCase):
    def evidence(self, label):
        self.checks.append(label)
        print("I85-PROOF: " + label, flush=True)

    def cli(self, *args, ok=True):
        p = subprocess.run(["python3", "-m", "integration.i85", *args],
                           cwd=b.ROOT, capture_output=True)
        if p.returncode != (0 if ok else 2):
            raise AssertionError("I85_CLI_RESULT_WITHHELD")
        if p.stderr or len(p.stdout) > 16384:
            raise AssertionError("I85_CLI_DIAGNOSTICS_WITHHELD")
        result = json.loads(p.stdout)
        sensitive = list(self.operator.secrets().values()) if self.operator.state and self.operator.secret_file.exists() else []
        for value in sensitive:
            if value.encode() in p.stdout + p.stderr:
                raise AssertionError("I85_SECRET_ECHO_WITHHELD")
        return result

    def http(self, family, payload, token):
        env = e.discover()
        body = json.dumps({"version": "prumo.admin.v1", "command": payload}).encode()
        req = request.Request(env["API_URL"] + "/functions/v1/prumo-admin-i82/v1/" + family,
                              data=body, headers={"apikey": env["ANON_KEY"],
                              "Authorization": "Bearer " + token, "Content-Type": "application/json"},
                              method="POST")
        try:
            response = request.urlopen(req, timeout=25)
        except error.HTTPError as exc:
            response = exc
        with response:
            status = response.status
            raw = response.read(262145)
        self.assertLessEqual(len(raw), 262144)
        payload = json.loads(raw)
        self.assertEqual(payload["version"], "prumo.admin.v1")
        self.assertEqual(payload["scope"], "ADMINISTRATIVE_ONLY")
        for value in self.operator.secrets().values():
            self.assertNotIn(value, raw.decode())
        return status, payload

    @staticmethod
    def prof(action, target, cargo="consultor", manager=None, old=0, key=None):
        return {"action": action, "target_id": target, "cargo": cargo,
                "manager_id": manager, "expected_relationship_id": str(old),
                "idempotency_key": key or "i85-" + uuid4().hex}

    @staticmethod
    def reg(action, target=None, cargo=None, manager=None, expected=None, preview=None, cursor=None, limit=0):
        return {"action": action, "target_id": target, "cargo": cargo, "manager_id": manager,
                "expected_sha256": expected, "preview_id": preview, "cursor": cursor,
                "limit": limit, "idempotency_key": "i85-" + uuid4().hex}

    def success(self, family, payload, token, state="APPLIED"):
        status, response = self.http(family, payload, token)
        self.assertEqual((status, response["state"], response["commit"]), (200, state, "CONFIRMED"))
        return response["receipt"]

    def test_gotrue_director_full_real_journey(self):
        self.checks = []
        self.operator = i85.Bootstrap()
        self.assertEqual(self.cli("init")["authority"], "NONE")
        self.operator.load()
        with e.database() as c:
            self.assertEqual(c.execute("select count(*) from auth.users").fetchone()[0], 0)
            self.assertEqual(c.execute("select count(*) from prumo_private.s1_responsaveis_plataforma").fetchone()[0], 0)
        self.evidence("01_fresh_stack_no_auth_no_director")

        for name in ("director", "manager", "manager2", "consultant", "legacy"):
            self.assertEqual(self.cli("create", "--label", name)["identities"][name], "CONFIRMED")
        self.operator.load()
        with self.assertRaises(b.Blocked):
            self.operator.create("director")
        self.evidence("02_admin_auth_real_uuid_stable_duplicate_refused")

        # Genuine lost response AFTER POST: never issue POST twice.
        original = i85._api
        def lose_after_real_create(method, path, *args, **kwargs):
            result = original(method, path, *args, **kwargs)
            if method == "POST" and path == "/auth/v1/admin/users":
                raise b.Blocked("INJECTED_LOST_RESPONSE")
            return result
        with patch.object(i85, "_api", lose_after_real_create):
            with self.assertRaises(b.Blocked):
                self.operator.create("outsider")
        self.assertEqual(self.cli("reconcile-identity", "--label", "outsider")["identities"]["outsider"], "CONFIRMED")
        self.operator.load()
        before = self.operator.auth_row(self.operator.state["identities"]["outsider"]["email"])
        self.assertEqual(before[0], self.operator.state["identities"]["outsider"]["uuid"])
        self.evidence("03_lost_auth_response_reconciles_without_second_creation")

        # A real UUID mismatch is refused instead of silently adopting a user.
        real = self.operator.state["identities"]["manager"]["uuid"]
        self.operator.state["identities"]["manager"]["uuid"] = str(uuid4())
        self.operator.save("TEST_DIVERGENCE_INJECTION", "manager")
        with self.assertRaises(b.Blocked):
            self.operator.verify_auth("manager")
        self.operator.state["identities"]["manager"]["uuid"] = real
        self.operator.save("TEST_DIVERGENCE_RESTORED", "manager")
        self.evidence("04_real_auth_uuid_divergence_refused")

        director_token = self.operator.token("director")
        outsider_token = self.operator.token("outsider")
        self.assertEqual(self.http("i80", self.reg("INVENTORY", limit=1), director_token)[0], 403)
        self.assertEqual(self.http("i79", self.prof("REGISTER", real, "diretor"), director_token)[0], 400)
        with self.assertRaises(b.Blocked):
            self.operator.authorize_director()
        self.evidence("05_valid_session_not_authority_no_self_promotion")

        os.environ["PRUMO_I85_DIRECTOR_APPROVAL"] = i85.APPROVAL
        try:
            self.assertTrue(self.cli("authorize-director")["approval"])
        finally:
            os.environ.pop("PRUMO_I85_DIRECTOR_APPROVAL", None)
        self.operator.load()
        # Lose the local acknowledgment AFTER the real PostgreSQL COMMIT.
        original_save = self.operator.save
        def lose_confirm(event, label=None):
            if event == "DIRECTOR_BOOTSTRAP_CONFIRMED":
                raise OSError("withheld fault after commit")
            return original_save(event, label)
        with patch.object(self.operator, "save", lose_confirm):
            with self.assertRaises(OSError):
                self.operator.grant_director()
        self.assertEqual(self.cli("status")["authority"], "COMMIT_UNKNOWN")
        self.assertEqual(self.cli("reconcile-authority")["authority"], "ACTIVE")
        self.operator.load()
        self.operator._confirm_grant(self.operator.state["identities"]["director"]["uuid"])
        with self.assertRaises(b.Blocked):
            self.operator.grant_director()
        self.evidence("06_explicit_technical_approval_real_director_commit_lost_reconciled_no_second")

        manager = self.operator.state["identities"]["manager"]["uuid"]
        manager2 = self.operator.state["identities"]["manager2"]["uuid"]
        consultant = self.operator.state["identities"]["consultant"]["uuid"]
        for target in (manager, manager2):
            self.success("i79", self.prof("REGISTER", target, "gestor"), director_token)
            self.success("i79", self.prof("ACTIVATE", target, "gestor"), director_token)
        self.success("i79", self.prof("REGISTER", consultant), director_token)
        self.success("i79", self.prof("ACTIVATE", consultant, manager=manager), director_token)
        with e.database() as c:
            old = c.execute("select id from prumo_private.s1_gestor_operadores where operador_id=%s and encerrado_em is null",
                            (consultant,)).fetchone()[0]
        self.success("i79", self.prof("TRANSFER", consultant, manager=manager2, old=old), director_token)
        self.evidence("07_edge_real_register_activate_transfer_cas")

        legacy = self.operator.state["identities"]["legacy"]["uuid"]
        # Only the integration test may manufacture a pending historical fixture.
        with e.database() as c:
            c.execute("insert into public.atores(id) values (%s)", (legacy,))
            c.execute("insert into public.equipe_prumo_s1(ator_id,estado) values (%s,'pendente')", (legacy,))
        cursor = None
        item = None
        for _ in range(100):
            receipt = self.success("i80", self.reg("INVENTORY", cursor=cursor, limit=50),
                                   director_token, "INVENTORY")
            item = next((x for x in receipt["items"] if x["target_id"] == legacy), None)
            if item:
                break
            if not receipt["has_more"]:
                break
            cursor = receipt["next_cursor"]
        self.assertIsNotNone(item)
        preview = self.success("i80", self.reg("PREVIEW", legacy, "gestor",
                                             expected=item["inventory_sha256"]), director_token, "READY")
        with e.database() as c:
            self.assertIsNone(c.execute("select cargo from public.equipe_prumo_s1 where ator_id=%s",
                                        (legacy,)).fetchone()[0])
        self.success("i80", self.reg("APPLY", legacy, "gestor",
                                    expected=preview["snapshot_sha256"], preview=preview["preview_id"]),
                     director_token)
        self.evidence("08_edge_real_inventory_preview_apply_no_implicit_apply")

        manager_token = self.operator.token("manager")
        consultant_token = self.operator.token("consultant")
        commands = [("i79", self.prof("REGISTER", self.operator.state["identities"]["outsider"]["uuid"])),
                    ("i79", self.prof("ACTIVATE", consultant, manager=manager)),
                    ("i79", self.prof("TRANSFER", consultant, manager=manager, old=old)),
                    ("i80", self.reg("INVENTORY", limit=1)),
                    ("i80", self.reg("PREVIEW", legacy, "gestor", expected=item["inventory_sha256"])),
                    ("i80", self.reg("APPLY", legacy, "gestor", expected=preview["snapshot_sha256"], preview=preview["preview_id"]))]
        for token in (manager_token, consultant_token, outsider_token):
            for family, payload in commands:
                status, result = self.http(family, payload, token)
                self.assertIn(status, (401, 403))
                self.assertEqual(result["state"], "DENIED")
        self.evidence("09_manager_consultant_unassigned_denied_six_commands")

        # Concurrent identical request must create one canonical request.
        external = self.operator.state["identities"]["outsider"]["uuid"]
        payload = self.prof("REGISTER", external, key="i85-concurrent-" + uuid4().hex)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.http("i79", payload, director_token), range(2)))
        self.assertEqual(sorted(x[1]["state"] for x in results), ["ALREADY_APPLIED", "APPLIED"])
        self.evidence("10_concurrent_idempotency_one_mutation")

        # Actual Director competence revocation and live-session invalidation.
        self.assertEqual(self.cli("revoke-director")["authority"], "REVOKED")
        self.assertEqual(self.http("i80", self.reg("INVENTORY", limit=1), director_token)[0], 401)
        self.operator.load()
        with self.assertRaises(b.Blocked):
            self.operator.grant_director()
        self.evidence("11_director_revoked_sessions_invalid_and_rebootstrap_denied")

        from integration.i83.catalog import snapshot
        with e.database() as c:
            after = snapshot(c)
        expected = b.load(b.DEFAULT / "catalog.json")
        self.assertEqual(after, expected)
        self.evidence("12_owners_grants_rls_triggers_constraints_unchanged")

        state = self.cli("dispose")
        self.assertTrue(state["private_material_removed"])
        self.assertFalse(i85.ROOT.exists())
        self.evidence("13_private_custody_disposed_without_forensic_claim")
        result = {"version": "prumo.i85.evidence.v1", "checks": self.checks,
                  "secret_values_exported": False, "hosted_enabled": False,
                  "integration": "real PG17/GoTrue/PostgREST/Edge"}
        out = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "prumo_i85_journey.json"
        out.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
