"""Real tests of a simulated privileged operator in an exclusive disposable VM.

No production operator, human-presence certification, public appointment API,
MCP connection or I85 bootstrap grant is used by this suite.
"""
from concurrent.futures import ThreadPoolExecutor
import base64
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time
from types import SimpleNamespace
import unittest
from urllib import request, error
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from integration.i84.capture import reject_material
from integration.i85 import bootstrap as i85
from integration.i85.test_journey import Journey
from integration.i86.authority import AuthorityLab
from integration.i86.cleanup import cleanup
from integration.i86.manual import lab_support as lab
from local_admin import boundary as b, environment as e
from local_admin.custody import read_env, scan
from local_admin.operation import Operator

RESULTS = []
FINAL = {}


class ManualTests(unittest.TestCase):
    http = Journey.http
    success = Journey.success
    prof = staticmethod(Journey.prof)
    reg = staticmethod(Journey.reg)

    @classmethod
    def setUpClass(cls):
        cls.passwords = {}
        cls.technical = []
        cls.addClassCleanup(cls.finish)
        cls.ops = Operator()
        cls.ops.execute("init")
        b.run(["python3", "-m", "integration.i83.test_logging_preflight"])
        cls.ops.execute("prepare", os.environ["PRUMO_G1_SOURCE_REPO"])
        cls.base_catalog = b.load(b.DEFAULT/"catalog.json")
        cls.ops.execute("provision")
        values = read_env(b.DEFAULT)
        cls.technical.extend([i85._key(), values["PRUMO_I82_HMAC_HEX"],
                              values["PRUMO_I82_DATABASE_URL"],
                              urlsplit(values["PRUMO_I82_DATABASE_URL"]).password])
        cls.ops.execute("serve")
        lab.install()
        cls.observer = AuthorityLab()
        cls.observer.install()
        # Only in-memory generated Auth fixtures, never a new custody system.
        cls.operator = SimpleNamespace(secrets=lambda: cls.passwords)
        cls.primary = lab.subject("primary", cls.passwords)
        cls.primary_act = lab.act(cls.primary["id"])
        if lab.apply_for_test(cls.primary_act)["state"] != "RECORDED_IN_TRANSACTION":
            raise RuntimeError("I86M_SYNTHETIC_OPERATOR_SETUP_FAILED")
        if lab.reconcile(cls.primary_act)["state"] != "COMMITTED_CURRENT_STATE_VERIFIED":
            raise RuntimeError("I86M_SYNTHETIC_OPERATOR_COMMIT_UNPROVEN")
        cls.primary_token = lab.token(cls.primary, cls.passwords, cls.technical)
        helper = cls("runTest")
        cls.manager = lab.subject("manager", cls.passwords)
        helper.success("i79", helper.prof("REGISTER", cls.manager["id"], "gestor"), cls.primary_token)
        helper.success("i79", helper.prof("ACTIVATE", cls.manager["id"], "gestor"), cls.primary_token)
        cls.manager_token = lab.token(cls.manager, cls.passwords, cls.technical)

    @classmethod
    def finish(cls):
        try:
            if hasattr(cls, "base_catalog"):
                from integration.i83.catalog import snapshot
                with e.database() as c:
                    value = snapshot(c)
                    FINAL["positive_routines_security_invoker"] = c.execute(
                        "select bool_and(not prosecdef) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='prumo_i86_manual'").fetchone()[0]
                for role in value["roles"]:
                    if role["rolname"] == "prumo_s1_admin_edge_local":
                        role["rolcanlogin"] = False
                if value != cls.base_catalog:
                    raise AssertionError("I86M_INHERITED_CATALOG_CHANGED")
                scan(b.DEFAULT, (b.EDGE,), extra=cls.technical+list(cls.passwords.values()))
                FINAL["inherited_catalog_equal"] = True
                FINAL["credential_log_matches"] = 0
                FINAL["i85_bootstrap_journal_created"] = i85.ROOT.exists()
                if i85.ROOT.exists():
                    raise AssertionError("I86M_MUST_NOT_USE_I85_BOOTSTRAP")
        finally:
            FINAL["cleanup"] = cleanup()
        FINAL["source_head"] = os.environ["PRUMO_I86_SOURCE_HEAD"]

    def setUp(self):
        self.children = []
        self.addCleanup(self.kill_children)

    def kill_children(self):
        for child in self.children:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=10)

    def person(self, label="subject"):
        return lab.subject(label, self.passwords)

    def appoint(self, person=None):
        person = self.person() if person is None else person
        values = lab.act(person["id"])
        self.assertEqual(lab.apply_for_test(values)["state"], "RECORDED_IN_TRANSACTION")
        self.assertEqual(lab.reconcile(values)["state"], "COMMITTED_CURRENT_STATE_VERIFIED")
        return person, values

    def counts(self, target, act_id):
        with lab.connect() as c:
            return tuple(c.execute(query, (value,)).fetchone()[0] for query, value in (
                ("select count(*) from public.atores where id=%s", target),
                ("select count(*) from public.equipe_prumo_s1 where ator_id=%s", target),
                ("select count(*) from prumo_private.s1_responsaveis_plataforma where ator_id=%s", target),
                ("select count(*) from prumo_i86_manual.acts where act_id=%s", act_id),
                ("select count(*) from prumo_i86_manual.audit where act_id=%s", act_id)))

    def direct_http(self, path, payload, token, profile=None):
        env = e.discover()
        headers = {"apikey": env["ANON_KEY"], "Authorization": "Bearer "+token,
                   "Content-Type": "application/json"}
        if profile:
            headers["Content-Profile"] = profile
        q = request.Request(env["API_URL"]+path, data=json.dumps(payload).encode(),
                            headers=headers, method="POST")
        try:
            response = request.urlopen(q, timeout=15)
        except error.HTTPError as exc:
            response = exc
        with response:
            raw = response.read(262145)
            status = response.status
        reject_material(raw, self.technical+list(self.passwords.values()))
        return status

    def private_rpc_denied(self, token, target):
        status = self.direct_http("/rest/v1/rpc/apply_act",
                                 {"p_target": target, "p_action": "APPOINT"}, token)
        self.assertIn(status, (400, 401, 403, 404, 406))
        status = self.direct_http("/rest/v1/rpc/apply_act",
                                 {"p_target": target, "p_action": "APPOINT"}, token,
                                 "prumo_i86_manual")
        self.assertIn(status, (400, 401, 403, 404, 406))

    def stopped(self, stage, values):
        read_fd, write_fd = os.pipe()
        env = os.environ.copy()
        env["PRUMO_I86_MANUAL_PROBE_FD"] = str(write_fd)
        child = subprocess.Popen(["python3", "-m", "integration.i86.manual.crash_probe",
                                   "--stage", stage], cwd=b.ROOT, env=env,
                                  pass_fds=(write_fd,), stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.close(write_fd)
        self.children.append(child)
        child.stdin.write(json.dumps(values, default=str).encode())
        child.stdin.close()
        child.stdin = None
        try:
            ready, _, _ = select.select([read_fd], [], [], 30)
            self.assertTrue(ready, "real manual SQL did not reach crash stage")
            self.assertEqual(os.read(read_fd, 128).strip(), stage.encode())
        finally:
            os.close(read_fd)
        return child

    def kill(self, child):
        child.kill()
        stdout, stderr = child.communicate(timeout=10)
        reject_material(stdout+stderr, self.technical+list(self.passwords.values()))
        self.assertEqual(child.returncode, -signal.SIGKILL)
        until = time.monotonic()+10
        while time.monotonic() < until:
            with lab.connect() as c:
                pending = c.execute("select count(*) from pg_stat_activity where application_name='i86-manual-crash-probe'").fetchone()[0]
            if not pending:
                return
            time.sleep(.05)
        self.fail("crashed PostgreSQL transaction did not settle")

    def test_01_canonical_auth_uuid_and_atomic_manual_appointment(self):
        person, values = self.appoint()
        self.assertEqual(self.counts(person["id"], values[0]), (1, 1, 1, 1, 1))
        token = lab.token(person, self.passwords, self.technical)
        observed = self.observer.assess("Bearer "+token,
            {"version": "prumo.i86.observation.v1", "idempotency_key": "i86m-"+uuid4().hex,
             "expected_sha256": None})
        self.assertTrue(observed.observation["state"]["ordinary_admin"])
        self.assertEqual(self.http("i80", self.reg("INVENTORY", limit=1), token)[0], 200)

    def test_02_director_cannot_appoint_another_through_ordinary_interfaces(self):
        person = self.person()
        self.private_rpc_denied(self.primary_token, person["id"])
        self.assertEqual(self.http("i79", self.prof("REGISTER", person["id"], "diretor"), self.primary_token)[0], 400)
        with lab.connect() as c:
            self.assertFalse(c.execute("select exists(select 1 from prumo_private.s1_responsaveis_plataforma where ator_id=%s)", (person["id"],)).fetchone()[0])

    def test_03_revoked_director_cannot_reactivate_itself(self):
        person, _ = self.appoint()
        values = lab.act(person["id"], "REVOKE")
        lab.apply_for_test(values)
        token = lab.token(person, self.passwords, self.technical)
        self.private_rpc_denied(token, person["id"])
        self.assertEqual(self.http("i80", self.reg("INVENTORY", limit=1), token)[0], 403)
        self.assertFalse(lab.inspect(person["id"])["state"]["competence_active"])

    def test_04_manager_cannot_appoint_director(self):
        person = self.person()
        self.private_rpc_denied(self.manager_token, person["id"])
        self.assertEqual(self.http("i80", self.reg("INVENTORY", limit=1), self.manager_token)[0], 403)

    def test_05_common_mcp_agent_sql_identity_is_denied(self):
        import psycopg
        values = lab.act(self.person()["id"])
        config = read_env(b.DEFAULT)
        u, db = urlsplit(config["PRUMO_I82_DATABASE_URL"]), urlsplit(e.discover()["DB_URL"])
        dsn = urlunsplit((u.scheme, u.netloc.replace("supabase_db_prumo-s0-auth-ci:5432",
                            str(db.hostname)+":"+str(db.port)), u.path, "", ""))
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with psycopg.connect(dsn, connect_timeout=5) as c:
                c.execute("set application_name='mcp-agent-untrusted'")
                c.execute("select set_config('prumo.i86.manual','true',true)")
                c.execute("select set_config('request.jwt.claims','{\"role\":\"service_role\",\"manual\":true}',true)")
                c.execute(lab.APPLY_SQL, values)
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with psycopg.connect(dsn, connect_timeout=5) as c:
                c.execute("set role postgres")

    def test_06_service_role_and_client_roles_have_no_private_execute(self):
        import psycopg
        signature = "prumo_i86_manual.apply_act(uuid,text,uuid,text,text,text,text)"
        for role in ("anon", "authenticated", "service_role", "prumo_s1_admin_edge_local",
                     "prumo_cfi01_pgtest_login"):
            with self.subTest(role=role):
                with lab.connect() as c:
                    self.assertEqual(c.execute(
                        "select has_schema_privilege(%s,'prumo_i86_manual','USAGE'),has_function_privilege(%s,%s,'EXECUTE')",
                        (role, role, signature)).fetchone(), (False, False))
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    with lab.connect() as c:
                        c.execute(psycopg.sql.SQL("set local role {}").format(psycopg.sql.Identifier(role)))
                        c.execute(lab.APPLY_SQL, lab.act(self.person()["id"]))

    def test_07_service_key_is_not_organizational_approval(self):
        self.private_rpc_denied(i85._key(), self.person()["id"])

    def test_08_jwt_and_metadata_forgery_do_not_grant_authority(self):
        person = self.person()
        token = lab.token(person, self.passwords, self.technical)
        i85._api("PUT", "/auth/v1/user", {"data": {"cargo": "diretor", "approved": True,
                       "operator": "postgres", "role": "service_role"}}, admin=False, token=token)
        self.assertEqual(self.http("i80", self.reg("INVENTORY", limit=1), token)[0], 403)
        self.private_rpc_denied(token, person["id"])
        parts = token.split(".")
        claims = json.loads(base64.urlsafe_b64decode(parts[1]+"="*((-len(parts[1]))%4)))
        claims["role"] = "service_role"
        parts[1] = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
        forged = ".".join(parts)
        self.technical.append(forged)
        self.assertIn(self.http("i80", self.reg("INVENTORY", limit=1), forged)[0], (401, 403))
        self.assertFalse(lab.inspect(person["id"])["state"]["competence_exists"])

    def test_09_repeated_act_does_not_duplicate_authority_or_audit(self):
        person, values = self.appoint()
        self.assertEqual(lab.apply_for_test(values)["state"], "ALREADY_RECORDED_IN_TRANSACTION")
        self.assertEqual(self.counts(person["id"], values[0]), (1, 1, 1, 1, 1))

    def test_10_concurrent_same_act_has_one_mutation(self):
        person = self.person()
        values = lab.act(person["id"])
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: lab.apply_for_test(values), range(2)))
        self.assertEqual({r["state"] for r in results},
                         {"RECORDED_IN_TRANSACTION", "ALREADY_RECORDED_IN_TRANSACTION"})
        self.assertEqual(self.counts(person["id"], values[0]), (1, 1, 1, 1, 1))

    def test_11_distinct_acts_same_subject_have_one_cas_winner(self):
        person = self.person()
        first = lab.act(person["id"])
        second = lab.act(person["id"], expected=first[3])
        def attempt(values):
            try:
                lab.apply_for_test(values)
                return "APPLIED"
            except Exception as exc:
                return getattr(exc, "sqlstate", "WITHHELD")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, (first, second)))
        self.assertEqual(sorted(results), ["40001", "APPLIED"])
        with lab.connect() as c:
            self.assertEqual(c.execute("select count(*) from prumo_private.s1_responsaveis_plataforma where ator_id=%s", (person["id"],)).fetchone()[0], 1)

    def test_12_different_subjects_can_both_be_directors_without_numeric_limit(self):
        people = [self.person(), self.person()]
        values = [lab.act(p["id"]) for p in people]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lab.apply_for_test, values))
        self.assertTrue(all(r["state"] == "RECORDED_IN_TRANSACTION" for r in results))
        with lab.connect() as c:
            self.assertEqual(c.execute("select count(*) from prumo_private.s1_responsaveis_plataforma where ator_id=any(%s::uuid[]) and ativo", ([p["id"] for p in people],)).fetchone()[0], 2)

    def test_13_existing_manager_is_not_reclassified_by_manual_appointment(self):
        import psycopg
        values = lab.act(self.manager["id"])
        with self.assertRaises(psycopg.errors.CheckViolation):
            lab.apply_for_test(values)
        self.assertEqual(lab.inspect(self.manager["id"])["state"]["cargo"], "gestor")

    def test_14_all_six_ordinary_commands_work_after_manual_appointment(self):
        director, _ = self.appoint()
        token = lab.token(director, self.passwords, self.technical)
        m1, m2, consultant, legacy = [self.person() for _ in range(4)]
        for manager in (m1, m2):
            self.success("i79", self.prof("REGISTER", manager["id"], "gestor"), token)
            self.success("i79", self.prof("ACTIVATE", manager["id"], "gestor"), token)
        self.success("i79", self.prof("REGISTER", consultant["id"]), token)
        activated = self.success("i79", self.prof("ACTIVATE", consultant["id"], manager=m1["id"]), token)
        self.success("i79", self.prof("TRANSFER", consultant["id"], manager=m2["id"],
                                     old=int(activated["relationship_id"])), token)
        with lab.connect() as c:
            c.execute("insert into public.atores(id) values(%s)", (legacy["id"],))
            c.execute("insert into public.equipe_prumo_s1(ator_id,estado) values(%s,'pendente')", (legacy["id"],))
        inventory = self.success("i80", self.reg("INVENTORY", limit=50), token, "INVENTORY")
        item = next(v for v in inventory["items"] if v["target_id"] == legacy["id"])
        preview = self.success("i80", self.reg("PREVIEW", legacy["id"], "gestor",
                         expected=item["inventory_sha256"]), token, "READY")
        with lab.connect() as c:
            self.assertIsNone(c.execute("select cargo from public.equipe_prumo_s1 where ator_id=%s", (legacy["id"],)).fetchone()[0])
        self.success("i80", self.reg("APPLY", legacy["id"], "gestor", expected=preview["snapshot_sha256"],
                                     preview=preview["preview_id"]), token)
        FINAL["six_ordinary_commands_after_manual_appointment"] = True

    def test_15_stale_cas_and_changed_act_evidence_are_rejected(self):
        import psycopg
        person, values = self.appoint()
        with self.assertRaises(psycopg.errors.SerializationFailure):
            lab.apply_for_test(lab.act(person["id"], "REVOKE", expected="0"*64))
        changed = (*values[:6], "0"*64)
        with self.assertRaises(psycopg.errors.UniqueViolation):
            lab.apply_for_test(changed)

    def test_16_missing_auth_and_missing_manual_evidence_do_not_mutate(self):
        import psycopg
        absent = str(uuid4())
        values = lab.act(absent)
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            lab.apply_for_test(values)
        person = self.person()
        values = lab.act(person["id"])
        with self.assertRaises(psycopg.errors.InvalidParameterValue):
            lab.apply_for_test((*values[:5], "", values[6]))
        self.assertEqual(self.counts(person["id"], values[0]), (0, 0, 0, 0, 0))

    def test_17_sigkill_before_commit_rolls_back_all_five_records(self):
        person = self.person()
        values = lab.act(person["id"])
        self.kill(self.stopped("before-commit", values))
        self.assertEqual(self.counts(person["id"], values[0]), (0, 0, 0, 0, 0))
        self.assertEqual(lab.reconcile(values)["state"], "NOT_PROVEN")

    def test_18_sigkill_after_commit_reconciles_without_reapplying(self):
        person = self.person()
        values = lab.act(person["id"])
        self.kill(self.stopped("after-commit", values))
        self.assertEqual(lab.reconcile(values)["state"], "COMMITTED_CURRENT_STATE_VERIFIED")
        self.assertEqual(lab.apply_for_test(values)["state"], "ALREADY_RECORDED_IN_TRANSACTION")
        self.assertEqual(self.counts(person["id"], values[0]), (1, 1, 1, 1, 1))

    def test_19_no_commit_claim_before_commit(self):
        person = self.person()
        values = lab.act(person["id"])
        with lab.connect() as c:
            result = c.execute(lab.APPLY_SQL, values).fetchone()[0]
            self.assertTrue(result["caller_commit_required"])
            self.assertEqual(c.execute("select prumo_i86_manual.reconcile_act(%s,%s)",
                            (values[0], values[6])).fetchone()[0]["state"], "COMMIT_NOT_PROVEN")
        self.assertEqual(lab.reconcile(values)["state"], "COMMITTED_CURRENT_STATE_VERIFIED")

    def test_20_deferred_audit_failure_rolls_back_whole_appointment(self):
        import psycopg
        person = self.person()
        values = lab.act(person["id"])
        with lab.connect() as c:
            c.execute("create function prumo_i86_manual.test_commit_fault() returns trigger language plpgsql security invoker set search_path='' as $$begin raise exception 'I86M_TEST_AUDIT_COMMIT_FAILURE';end$$")
            c.execute("create constraint trigger test_commit_fault after insert on prumo_i86_manual.audit deferrable initially deferred for each row execute function prumo_i86_manual.test_commit_fault()")
        try:
            with self.assertRaises(psycopg.Error):
                lab.apply_for_test(values)
            self.assertEqual(self.counts(person["id"], values[0]), (0, 0, 0, 0, 0))
            self.assertEqual(lab.reconcile(values)["state"], "NOT_PROVEN")
        finally:
            with lab.connect() as c:
                c.execute("drop trigger test_commit_fault on prumo_i86_manual.audit")
                c.execute("drop function prumo_i86_manual.test_commit_fault()")

    def test_21_manual_revocation_stops_old_and_new_sessions(self):
        person, appointment = self.appoint()
        old = lab.token(person, self.passwords, self.technical)
        self.assertEqual(self.http("i80", self.reg("INVENTORY", limit=1), old)[0], 200)
        revocation = lab.act(person["id"], "REVOKE")
        lab.apply_for_test(revocation)
        self.assertEqual(lab.reconcile(revocation)["state"], "COMMITTED_CURRENT_STATE_VERIFIED")
        self.assertIn(self.http("i80", self.reg("INVENTORY", limit=1), old)[0], (401, 403))
        fresh = lab.token(person, self.passwords, self.technical)
        self.assertEqual(self.http("i80", self.reg("INVENTORY", limit=1), fresh)[0], 403)
        state = lab.inspect(person["id"])["state"]
        self.assertEqual((state["cargo"], state["estado"], state["competence_active"]), ("diretor", "ativo", False))
        self.assertEqual(lab.reconcile(appointment)["state"], "COMMITTED_STATE_CHANGED")
        import psycopg
        with self.assertRaises(psycopg.errors.SerializationFailure):
            lab.apply_for_test(appointment)

    def test_22_manual_reactivation_never_recreates_revoked_sessions(self):
        person, _ = self.appoint()
        old = lab.token(person, self.passwords, self.technical)
        lab.apply_for_test(lab.act(person["id"], "REVOKE"))
        reactivation = lab.act(person["id"], "REACTIVATE")
        lab.apply_for_test(reactivation)
        self.assertEqual(lab.reconcile(reactivation)["state"], "COMMITTED_CURRENT_STATE_VERIFIED")
        self.assertIn(self.http("i80", self.reg("INVENTORY", limit=1), old)[0], (401, 403))
        fresh = lab.token(person, self.passwords, self.technical)
        self.assertEqual(self.http("i80", self.reg("INVENTORY", limit=1), fresh)[0], 200)

    def test_23_auth_row_contention_aborts_without_inverse_wait(self):
        import psycopg
        person = self.person()
        values = lab.act(person["id"])
        with lab.connect() as blocker:
            blocker.execute("select id from auth.users where id=%s for update", (person["id"],))
            with self.assertRaises(psycopg.errors.LockNotAvailable):
                lab.apply_for_test(values)
            blocker.rollback()
        self.assertEqual(self.counts(person["id"], values[0]), (0, 0, 0, 0, 0))

    def test_24_revocation_drains_real_http_before_cutting_authority(self):
        person, _ = self.appoint()
        token = lab.token(person, self.passwords, self.technical)
        values = lab.act(person["id"], "REVOKE")
        def revoke():
            with lab.connect() as c:
                c.execute("set application_name='i86-manual-test-revoke'")
                return c.execute(lab.APPLY_SQL, values).fetchone()[0]
        with lab.connect() as blocker, ThreadPoolExecutor(max_workers=2) as pool:
            blocker.execute("select ator_id from public.equipe_prumo_s1 where ator_id=%s for update", (person["id"],))
            pid = blocker.execute("select pg_backend_pid()").fetchone()[0]
            request = pool.submit(self.http, "i80", self.reg("INVENTORY", limit=1), token)
            until = time.monotonic()+8
            while time.monotonic() < until:
                with lab.connect() as c:
                    waiting = c.execute("select count(*) from pg_stat_activity where %s=any(pg_blocking_pids(pid))", (pid,)).fetchone()[0]
                if waiting:
                    break
                time.sleep(.05)
            else:
                self.fail("actual signed HTTP did not reach row-lock contention")
            mutation = pool.submit(revoke)
            until = time.monotonic()+8
            while time.monotonic() < until:
                with lab.connect() as c:
                    waiting = c.execute("select count(*) from pg_stat_activity where application_name='i86-manual-test-revoke' and wait_event_type='Lock'").fetchone()[0]
                if waiting:
                    break
                time.sleep(.05)
            else:
                self.fail("manual revocation did not wait for the live session")
            with lab.connect() as c:
                c.execute("select ator_id from prumo_private.s1_responsaveis_plataforma where ator_id=%s for share nowait", (person["id"],))
            blocker.commit()
            self.assertEqual(request.result(timeout=15)[0], 200)
            self.assertEqual(mutation.result(timeout=15)["state"], "RECORDED_IN_TRANSACTION")
        self.assertIn(self.http("i80", self.reg("INVENTORY", limit=1), token)[0], (401, 403))
        self.assertEqual(lab.reconcile(values)["state"], "COMMITTED_CURRENT_STATE_VERIFIED")

    def test_25_manual_audit_is_immutable_and_reflects_sql_operator(self):
        import psycopg
        with lab.connect() as c:
            row = c.execute("select sql_session_principal,sql_effective_principal,operator_record_ref,manual_record_ref,evidence_sha256 from prumo_i86_manual.audit where act_id=%s", (self.primary_act[0],)).fetchone()
        self.assertEqual(row[:2], ("postgres", "postgres"))
        self.assertEqual(row[2:], self.primary_act[4:])
        for query in ("delete from prumo_i86_manual.audit", "truncate prumo_i86_manual.acts cascade",
                      "update prumo_i86_manual.acts set result='{}'::jsonb"):
            with self.subTest(query=query), self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with lab.connect() as c:
                    c.execute(query)

    def test_26_repeatable_read_cannot_claim_current_state(self):
        import psycopg
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with lab.connect() as c:
                c.execute("set transaction isolation level repeatable read")
                c.execute("select prumo_i86_manual.inspect_subject(%s)", (self.primary["id"],))

    def test_27_i85_bootstrap_is_not_reopened_for_manual_governance(self):
        with self.assertRaises(b.Blocked):
            i85.Bootstrap().init()
        self.assertFalse(i85.ROOT.exists())

    def test_28_positive_appointment_rejects_banned_auth_identity(self):
        import psycopg
        person = self.person()
        with lab.connect() as c:
            c.execute("update auth.users set banned_until=clock_timestamp()+interval '1 day' where id=%s", (person["id"],))
        values = lab.act(person["id"])
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            lab.apply_for_test(values)
        self.assertEqual(self.counts(person["id"], values[0]), (0, 0, 0, 0, 0))

    def test_29_negative_revocation_remains_possible_for_banned_auth(self):
        person, _ = self.appoint()
        with lab.connect() as c:
            c.execute("update auth.users set banned_until=clock_timestamp()+interval '1 day' where id=%s", (person["id"],))
        values = lab.act(person["id"], "REVOKE")
        lab.apply_for_test(values)
        self.assertEqual(lab.reconcile(values)["state"], "COMMITTED_CURRENT_STATE_VERIFIED")
        self.assertFalse(lab.inspect(person["id"])["state"]["competence_active"])
        with lab.connect() as c:
            self.assertTrue(c.execute("select banned_until>clock_timestamp() from auth.users where id=%s", (person["id"],)).fetchone()[0])

    def test_30_incomplete_existing_actor_is_not_promoted_by_inference(self):
        import psycopg
        person = self.person()
        with lab.connect() as c:
            c.execute("insert into public.atores(id) values(%s)", (person["id"],))
        values = lab.act(person["id"])
        with self.assertRaises(psycopg.errors.CheckViolation):
            lab.apply_for_test(values)
        self.assertEqual(self.counts(person["id"], values[0]), (1, 0, 0, 0, 0))

    def test_99_last_director_recovery_requires_an_explicit_new_manual_act(self):
        # Test simulation of separately evidenced human acts, NOT a bulk runtime.
        with lab.connect() as c:
            ids = c.execute("select ator_id::text from prumo_private.s1_responsaveis_plataforma where ativo order by ator_id").fetchall()
        for (target,) in ids:
            lab.apply_for_test(lab.act(target, "REVOKE"))
        with lab.connect() as c:
            self.assertEqual(c.execute("select count(*) from prumo_private.s1_responsaveis_plataforma where ativo").fetchone()[0], 0)
        denied = lab.token(self.primary, self.passwords, self.technical)
        self.assertEqual(self.http("i80", self.reg("INVENTORY", limit=1), denied)[0], 403)
        recovery = lab.act(self.primary["id"], "REACTIVATE")
        lab.apply_for_test(recovery)
        self.assertEqual(lab.reconcile(recovery)["state"], "COMMITTED_CURRENT_STATE_VERIFIED")
        fresh = lab.token(self.primary, self.passwords, self.technical)
        self.assertEqual(self.http("i80", self.reg("INVENTORY", limit=1), fresh)[0], 200)
        self.assertFalse(i85.ROOT.exists())
        FINAL["last_director_recovered_by_explicit_test_manual_act_only"] = True


class ProofResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        RESULTS.append({"test": test._testMethodName, "status": "PASS"})

    def addFailure(self, test, error):
        super().addFailure(test, error)
        RESULTS.append({"test": test._testMethodName, "status": "FAIL"})

    def addError(self, test, error):
        super().addError(test, error)
        RESULTS.append({"test": str(test), "status": "FAIL"})


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ManualTests)
    planned = [test._testMethodName for test in suite]
    result = unittest.TextTestRunner(verbosity=2, resultclass=ProofResult, failfast=True).run(suite)
    proof = {"version": "prumo.i86.manual.evidence.v1",
             "status": "PASS" if result.wasSuccessful() and not result.skipped and result.testsRun == len(planned) else "FAIL",
             "planned_tests": len(planned), "tests_run": result.testsRun,
             "skipped": len(result.skipped), "results": RESULTS,
             "not_tested": [name for name in planned if name not in {r["test"] for r in RESULTS}],
             "final": FINAL,
             "manual_execution": "SYNTHETIC_TEST_SIMULATION_NOT_HUMAN_PRESENCE_CERTIFICATION"}
    (Path(os.environ["RUNNER_TEMP"])/"prumo_i86_manual_real.json").write_text(json.dumps(proof, indent=2)+"\n")
    raise SystemExit(0 if proof["status"] == "PASS" else 1)
