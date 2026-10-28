"""Real GoTrue/PG17/Edge proofs, distinct from the pure governance model.

One exclusive runner/owned stack. No reactivation of withdrawn authority; the
single committed Director revocation is the final test. No fixture resets of
history, disabled guards, broad grants or new business functions.
"""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID, uuid4

from integration.i84.capture import reject_material
from integration.i85 import bootstrap as i85
from integration.i85.test_journey import Journey
from integration.i86.authority import AuthorityLab, VERSION, Refusal, governance_gate
from integration.i86.cleanup import cleanup
from local_admin import boundary as b, environment as e
from local_admin.custody import read_env, scan
from local_admin.operation import Operator

OUTCOMES = []
FINAL = {}


class AuthorityTests(unittest.TestCase):
    http = Journey.http
    success = Journey.success
    prof = staticmethod(Journey.prof)
    reg = staticmethod(Journey.reg)

    @classmethod
    def setUpClass(cls):
        if os.environ.get("PRUMO_I86_DISPOSABLE") != "YES":
            raise RuntimeError("I86 opt-in required")
        cls.technical = []
        cls.addClassCleanup(cls.finish)
        cls.ops = Operator()
        cls.ops.execute("init")
        b.run(["python3", "-m", "integration.i83.test_logging_preflight"])
        cls.ops.execute("prepare", os.environ["PRUMO_G1_SOURCE_REPO"])
        cls.base_catalog = b.load(b.DEFAULT/"catalog.json")
        cls.ops.execute("provision")
        cls.remember_technical()
        cls.ops.execute("serve")
        cls.operator = i85.Bootstrap()
        cls.operator.init()
        for label in i85.LABELS:
            cls.operator.create(label)
        os.environ["PRUMO_I85_DIRECTOR_APPROVAL"] = i85.APPROVAL
        try:
            cls.operator.authorize_director()
        finally:
            os.environ.pop("PRUMO_I85_DIRECTOR_APPROVAL", None)
        cls.operator.grant_director()
        cls.operator.load()
        cls.technical.extend(cls.operator.secrets().values())
        cls.people = {k: v["uuid"] for k, v in cls.operator.state["identities"].items()}
        cls.lab = AuthorityLab()
        cls.lab.install()
        helper = cls("runTest")
        token = cls.operator.token("director")
        cls.technical.append(token)
        for label in ("manager", "manager2"):
            helper.success("i79", helper.prof("REGISTER", cls.people[label], "gestor"), token)
            helper.success("i79", helper.prof("ACTIVATE", cls.people[label], "gestor"), token)
        helper.success("i79", helper.prof("REGISTER", cls.people["consultant"]), token)
        helper.success("i79", helper.prof("ACTIVATE", cls.people["consultant"],
                                        manager=cls.people["manager"]), token)

    @classmethod
    def remember_technical(cls):
        values = read_env(b.DEFAULT)
        cls.technical.extend([i85._key(), values["PRUMO_I82_HMAC_HEX"],
                              values["PRUMO_I82_DATABASE_URL"],
                              urlsplit(values["PRUMO_I82_DATABASE_URL"]).password])

    @classmethod
    def finish(cls):
        try:
            if hasattr(cls, "base_catalog"):
                from integration.i83.catalog import snapshot
                with e.database() as conn:
                    actual = snapshot(conn)
                for role in actual["roles"]:
                    if role["rolname"] == "prumo_s1_admin_edge_local":
                        role["rolcanlogin"] = False
                if actual != cls.base_catalog:
                    raise AssertionError("I86_INHERITED_CATALOG_DRIFT")
                scan(b.DEFAULT, (b.EDGE,), extra=cls.technical)
                FINAL["catalog_equal"] = True
                FINAL["credential_log_matches"] = 0
        finally:
            FINAL["cleanup"] = cleanup()
        FINAL["source_head"] = os.environ["PRUMO_I86_SOURCE_HEAD"]

    def setUp(self):
        self.children = []
        self.addCleanup(self.kill_children)
        self.token = self.operator.token("director")
        self.technical.append(self.token)
        self.principal = self.lab._identity.verify("Bearer "+self.token)

    def kill_children(self):
        for child in self.children:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=10)

    def dto(self, key=None, expected=None):
        return {"version": VERSION, "idempotency_key": key or "i86-"+uuid4().hex,
                "expected_sha256": expected}

    def assess(self, payload=None, token=None, lab=None):
        return (lab or self.lab).assess("Bearer "+(self.token if token is None else token),
                                     self.dto() if payload is None else payload)

    def counts(self, key):
        with e.database() as c:
            observations = c.execute("select count(*) from prumo_i86_lab.observations where request_key=%s",
                                     (key,)).fetchone()[0]
            audit = c.execute("select count(*) from prumo_i86_lab.audit a join prumo_i86_lab.observations o on o.id=a.observation_id where o.request_key=%s",
                              (key,)).fetchone()[0]
        return observations, audit

    def stopped(self, stage, payload):
        read_fd, write_fd = os.pipe()
        env = os.environ.copy()
        env["PRUMO_I86_PROBE_FD"] = str(write_fd)
        child = subprocess.Popen(["python3", "-m", "integration.i86.fault_driver",
                                   "--stage", stage], cwd=b.ROOT, env=env,
                                  pass_fds=(write_fd,), stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.close(write_fd)
        self.children.append(child)
        child.stdin.write(json.dumps({"authorization": "Bearer "+self.token,
                                      "payload": payload}).encode())
        child.stdin.close()
        child.stdin = None
        try:
            ready, _, _ = select.select([read_fd], [], [], 30)
            self.assertTrue(ready, "real transaction probe did not reach stage")
            self.assertEqual(os.read(read_fd, 128).strip(), stage.encode())
        finally:
            os.close(read_fd)
        return child

    def kill(self, child):
        child.kill()
        stdout, stderr = child.communicate(timeout=10)
        reject_material(stdout+stderr, self.technical)
        self.assertEqual(child.returncode, -signal.SIGKILL)
        until = time.monotonic()+10
        while time.monotonic() < until:
            with e.database() as c:
                count = c.execute("select count(*) from pg_stat_activity where application_name='i86-crash-probe'").fetchone()[0]
            if not count:
                return
            time.sleep(.05)
        self.fail("real PostgreSQL crash transaction did not settle")

    def test_01_canonical_identity_and_competence_separated(self):
        result = self.assess()
        self.assertEqual(result.state, "OBSERVED")
        value = result.observation
        self.assertEqual(value["state"]["actor_id"], self.people["director"])
        self.assertEqual(value["state"]["session_id"], str(self.principal.session_id))
        self.assertTrue(value["state"]["ordinary_admin"])
        self.assertEqual(value["governance_state"], "PENDING_DECISION")
        self.assertFalse(value["authorization_token"])
        for kind in ("APPOINT_DIRECTOR", "REPLACE_DIRECTOR", "REACTIVATE_AUTHORITY",
                     "REVOKE_ORGANIZATIONAL_AUTHORITY"):
            self.assertFalse(governance_gate(kind)["operationally_enabled"])

    def test_02_manager_with_no_children_has_no_director_competence(self):
        token = self.operator.token("manager2")
        self.technical.append(token)
        result = self.assess(token=token)
        self.assertEqual(result.state, "OBSERVED")
        self.assertEqual(result.observation["state"]["cargo"], "gestor")
        self.assertFalse(result.observation["state"]["ordinary_admin"])
        self.assertEqual(self.http("i80", self.reg("INVENTORY", limit=1), token)[0], 403)

    def test_03_auth_only_metadata_cannot_promote(self):
        token = self.operator.token("outsider")
        self.technical.append(token)
        i85._api("PUT", "/auth/v1/user", {"data": {"cargo": "diretor", "role": "service_role",
                                                   "approval": True}}, admin=False, token=token)
        result = self.assess(token=token)
        self.assertEqual(result.state, "OBSERVED")
        self.assertFalse(result.observation["state"]["actor_present"])
        self.assertFalse(result.observation["state"]["ordinary_admin"])
        self.assertEqual(self.http("i80", self.reg("INVENTORY", limit=1), token)[0], 403)

    def test_04_service_role_is_not_a_human(self):
        self.assertEqual(self.assess(token=i85._key()).state, "DENIED")

    def test_05_payload_identity_is_rejected_without_mutation(self):
        p = self.dto()
        p["actor_id"] = self.people["director"]
        self.assertEqual(self.assess(p).state, "INPUT_REJECTED")
        self.assertEqual(self.counts(p["idempotency_key"]), (0, 0))

    def test_06_same_key_replays_one_observation_and_audits(self):
        p = self.dto()
        first = self.assess(p)
        second = self.assess(p)
        self.assertEqual((first.state, second.state), ("OBSERVED", "ALREADY_RECORDED"))
        self.assertEqual(first.observation["observation_id"], second.observation["observation_id"])
        self.assertEqual(self.counts(p["idempotency_key"]), (1, 2))

    def test_07_divergent_key_payload_conflicts(self):
        p = self.dto()
        first = self.assess(p)
        self.assertEqual(first.state, "OBSERVED")
        self.assertEqual(self.assess({**p, "expected_sha256": first.observation["state_sha256"]}).state,
                         "CONFLICT")
        self.assertEqual(self.counts(p["idempotency_key"]), (1, 1))

    def test_08_cas_obsolete_does_not_record(self):
        p = self.dto(expected="0"*64)
        self.assertEqual(self.assess(p).state, "STALE")
        self.assertEqual(self.counts(p["idempotency_key"]), (0, 0))

    def test_09_same_visible_authority_new_revision_invalidates_replay(self):
        p = self.dto()
        first = self.assess(p)
        self.assertEqual(first.state, "OBSERVED")
        # Rewrite the SAME true value, never revoke then grant without a policy.
        with e.database() as c:
            c.execute("update prumo_private.s1_responsaveis_plataforma set ativo=ativo where ator_id=%s",
                      (self.people["director"],))
        self.assertEqual(self.assess(p).state, "STALE")
        self.assertTrue(self.assess().observation["state"]["ordinary_admin"])

    def test_10_concurrent_same_key_is_one_durable_observation(self):
        p = self.dto()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.assess(p, lab=AuthorityLab()), range(2)))
        self.assertEqual({r.state for r in results}, {"OBSERVED", "ALREADY_RECORDED"})
        self.assertEqual(self.counts(p["idempotency_key"]), (1, 2))

    def test_11_distinct_intents_do_not_appoint_two_directors(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.assess(lab=AuthorityLab()), range(2)))
        self.assertTrue(all(r.state == "OBSERVED" for r in results))
        self.assertTrue(all(r.observation["governance_state"] == "PENDING_DECISION" for r in results))
        with e.database() as c:
            self.assertEqual(c.execute("select count(*) from prumo_private.s1_responsaveis_plataforma where ativo").fetchone()[0], 1)

    def test_12_real_logout_denies_replay(self):
        p = self.dto()
        self.assertEqual(self.assess(p).state, "OBSERVED")
        from scripts.test_s0_cfi01_auth_rest_local import request
        env = e.discover()
        self.assertIn(request(env["API_URL"], env["ANON_KEY"], "POST",
                              "/auth/v1/logout?scope=local", token=self.token)[0], (200, 204))
        self.assertEqual(self.assess(p).state, "DENIED")
        self.assertEqual(self.counts(p["idempotency_key"]), (1, 1))

    def test_13_expired_session_denied_in_sql(self):
        with e.database() as c:
            c.execute("update auth.sessions set not_after=clock_timestamp()-interval '1 second' where id=%s",
                      (self.principal.session_id,))
        with self.assertRaises(Refusal) as refused:
            with self.lab.connect() as c:
                self.lab.capture(c, self.principal)
        self.assertEqual(refused.exception.state, "DENIED")
        self.assertEqual(self.assess().state, "DENIED")

    def test_14_session_expiring_while_waiting_is_rechecked(self):
        with e.database() as c:
            expiry = c.execute("update auth.sessions set not_after=clock_timestamp()+interval '5 seconds' where id=%s returning not_after",
                      (self.principal.session_id,))
            expiry = expiry.fetchone()[0]
        with e.database() as blocker, ThreadPoolExecutor(max_workers=1) as pool:
            blocker.execute("select id from public.atores where id=%s for update", (self.people["director"],))
            pid = blocker.execute("select pg_backend_pid()").fetchone()[0]
            future = pool.submit(self.assess)
            until = time.monotonic()+5
            while time.monotonic() < until:
                with e.database() as c:
                    waiting = c.execute("select count(*) from pg_stat_activity where %s=any(pg_blocking_pids(pid))", (pid,)).fetchone()[0]
                if waiting:
                    break
                time.sleep(.05)
            else:
                self.fail("session probe did not reach real row-lock contention")
            until = time.monotonic()+6
            while time.monotonic() < until:
                with e.database() as c:
                    expired = c.execute("select clock_timestamp()>%s", (expiry,)).fetchone()[0]
                if expired:
                    break
                time.sleep(.05)
            else:
                self.fail("server clock did not cross session expiry")
            blocker.commit()
            self.assertEqual(future.result(timeout=15).state, "DENIED")

    def test_15_sigkill_before_commit_rolls_back_both_evidence_tables(self):
        p = self.dto()
        self.kill(self.stopped("before-commit", p))
        self.assertEqual(self.counts(p["idempotency_key"]), (0, 0))
        self.assertEqual(self.assess(p).state, "OBSERVED")

    def test_16_sigkill_after_commit_reconciles_same_key(self):
        p = self.dto()
        self.kill(self.stopped("after-commit", p))
        self.assertEqual(self.counts(p["idempotency_key"]), (1, 1))
        self.assertEqual(self.assess(p).state, "ALREADY_RECORDED")
        self.assertEqual(self.counts(p["idempotency_key"]), (1, 2))

    def test_17_deferred_audit_failure_never_reports_commit(self):
        p = self.dto()
        with e.database() as c:
            c.execute("create function prumo_i86_lab.test_fail_commit() returns trigger language plpgsql security invoker set search_path='' as $$begin raise exception 'I86_TEST_COMMIT_FAULT';end$$")
            c.execute("create constraint trigger test_commit_fault after insert on prumo_i86_lab.audit deferrable initially deferred for each row execute function prumo_i86_lab.test_fail_commit()")
        try:
            self.assertEqual(self.assess(p).state, "UNAVAILABLE")
            self.assertEqual(self.counts(p["idempotency_key"]), (0, 0))
        finally:
            with e.database() as c:
                c.execute("drop trigger test_commit_fault on prumo_i86_lab.audit")
                c.execute("drop function prumo_i86_lab.test_fail_commit()")

    def test_18_private_evidence_cannot_be_read_or_executed_by_client_roles(self):
        import psycopg
        for role in ("anon", "authenticated", "service_role", "prumo_s1_admin_edge_local"):
            with self.subTest(role=role):
                with e.database() as c:
                    self.assertFalse(c.execute("select has_schema_privilege(%s,'prumo_i86_lab','USAGE')", (role,)).fetchone()[0])
                    self.assertFalse(c.execute("select has_function_privilege(%s,'prumo_i86_lab.immutable()','EXECUTE')", (role,)).fetchone()[0])
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    with e.database() as c:
                        c.execute(psycopg.sql.SQL("set local role {}").format(psycopg.sql.Identifier(role)))
                        c.execute("select * from prumo_i86_lab.observations")

    def test_19_dedicated_login_cannot_assume_owners_or_touch_auth(self):
        import psycopg
        raw = read_env(b.DEFAULT)["PRUMO_I82_DATABASE_URL"]
        u, db = urlsplit(raw), urlsplit(e.discover()["DB_URL"])
        dsn = urlunsplit((u.scheme, u.netloc.replace("supabase_db_prumo-s0-auth-ci:5432",
                           str(db.hostname)+":"+str(db.port)), u.path, "", ""))
        for query in ("select * from auth.users", "select * from prumo_i86_lab.audit",
                      "set role prumo_s1_admin_domain_local",
                      "set role prumo_s1_professional_validator_local",
                      "set role prumo_s1_edge_custodian_local"):
            with self.subTest(query=query), self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with psycopg.connect(dsn, connect_timeout=5) as c:
                    c.execute(query)

    def test_20_evidence_is_immutable_and_cannot_claim_ratification(self):
        import psycopg
        for query in ("update prumo_i86_lab.observations set governance_state='APPROVED'",
                      "delete from prumo_i86_lab.audit", "truncate prumo_i86_lab.observations cascade"):
            with self.subTest(query=query), self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with e.database() as c:
                    c.execute(query)

    def test_21_restricted_edge_profile_survives_existing_rotation(self):
        from integration.i85.edge_profile import verify
        self.ops.execute("rotate")
        self.remember_technical()
        self.assertTrue(verify(b.load(b.DEFAULT/"state.json")))
        self.assertEqual(self.http("i80", self.reg("INVENTORY", limit=1), self.token)[0], 200)
        self.assertTrue(self.assess().observation["state"]["ordinary_admin"])

    def test_99_revocation_orders_with_live_observation_and_never_reactivates(self):
        ready, resume = threading.Event(), threading.Event()
        delayed = AuthorityLab()
        original = delayed.record
        def delayed_record(*args):
            ready.set()
            if not resume.wait(12):
                raise RuntimeError("I86_TEST_SCHEDULE_TIMEOUT")
            return original(*args)
        key = self.dto()
        self.assertEqual(self.assess(key).state, "OBSERVED")
        try:
            with patch.object(delayed, "record", delayed_record), e.database() as blocker, ThreadPoolExecutor(max_workers=3) as pool:
                late = pool.submit(self.assess, self.dto(), None, delayed)
                self.assertTrue(ready.wait(8))  # genuine GoTrue verification completed
                blocker.execute("select ator_id from public.equipe_prumo_s1 where ator_id=%s for update", (self.people["director"],))
                pid = blocker.execute("select pg_backend_pid()").fetchone()[0]
                inflight = pool.submit(self.assess)
                until = time.monotonic()+8
                while time.monotonic() < until:
                    with e.database() as c:
                        waiting = c.execute("select count(*) from pg_stat_activity where %s=any(pg_blocking_pids(pid))", (pid,)).fetchone()[0]
                    if waiting:
                        break
                    time.sleep(.05)
                else:
                    self.fail("real observation did not reach ordered row lock")
                revoked = pool.submit(self.operator.revoke_director)
                until = time.monotonic()+8
                while time.monotonic() < until:
                    with e.database() as c:
                        waiting = c.execute("select count(*) from pg_stat_activity where query like 'select id from auth.sessions%for update%' and wait_event_type='Lock'").fetchone()[0]
                    if waiting:
                        break
                    time.sleep(.05)
                else:
                    self.fail("I85 revocation did not wait on the live I86 observation")
                with e.database() as c:
                    c.execute("select ator_id from prumo_private.s1_responsaveis_plataforma where ator_id=%s for share nowait", (self.people["director"],))
                blocker.commit()
                self.assertEqual(inflight.result(timeout=15).state, "OBSERVED")
                self.assertEqual(revoked.result(timeout=15)["authority"], "REVOKED")
                resume.set()
                self.assertEqual(late.result(timeout=15).state, "DENIED")
        finally:
            resume.set()
        self.assertEqual(self.assess(key).state, "DENIED")
        fresh = self.operator.token("director")
        self.technical.append(fresh)
        observation = self.assess(token=fresh)
        self.assertEqual(observation.state, "OBSERVED")
        self.assertEqual((observation.observation["state"]["cargo"],
                          observation.observation["state"]["estado"]), ("diretor", "ativo"))
        self.assertFalse(observation.observation["state"]["ordinary_admin"])
        self.assertIn(self.http("i80", self.reg("INVENTORY", limit=1), fresh)[0], (401, 403))
        with self.assertRaises(b.Blocked):
            self.operator.grant_director()
        with e.database() as c:
            self.assertEqual(c.execute("select count(*),count(*) filter(where ativo) from prumo_private.s1_responsaveis_plataforma").fetchone(), (1, 0))


class ProofResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        OUTCOMES.append({"test": test._testMethodName, "status": "PASS", "layer": "REAL_AUTH_PG17_EDGE"})

    def addFailure(self, test, error):
        super().addFailure(test, error)
        OUTCOMES.append({"test": test._testMethodName, "status": "FAIL"})

    def addError(self, test, error):
        super().addError(test, error)
        OUTCOMES.append({"test": str(test), "status": "FAIL"})


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AuthorityTests)
    planned = [t._testMethodName for t in suite]
    result = unittest.TextTestRunner(verbosity=2, resultclass=ProofResult, failfast=True).run(suite)
    proof = {"version": "prumo.i86.real-evidence.v1",
             "status": "PASS" if result.wasSuccessful() and result.testsRun == len(planned) and not result.skipped else "FAIL",
             "planned_tests": len(planned), "tests_run": result.testsRun,
             "skipped": len(result.skipped), "results": OUTCOMES,
             "not_tested": [n for n in planned if n not in {r["test"] for r in OUTCOMES}],
             "final": FINAL, "governance": "PENDING_DECISION"}
    (Path(os.environ["RUNNER_TEMP"])/"prumo_i86_real.json").write_text(json.dumps(proof, indent=2)+"\n")
    raise SystemExit(0 if proof["status"] == "PASS" else 1)
