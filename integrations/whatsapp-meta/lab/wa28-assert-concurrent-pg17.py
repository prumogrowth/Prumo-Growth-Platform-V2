#!/usr/bin/env python3
"""WA28: deterministic concurrent PG17 fixture, no external Python packages.

We deliberately run SQL transactions with independent psql processes; control
their lock order via pg_stat_activity/pg_blocking_pids rather than fixed sleeps.
Never invoke with production DB, real credentials, Graph, S0 or dispatch.
"""
import os
import subprocess
import sys
import time
from urllib.parse import urlsplit

dsn = os.getenv("PRUMO_TEST_DATABASE_URL", "")
parsed = urlsplit(dsn)
if not (
    parsed.scheme == "postgresql"
    and parsed.hostname == "127.0.0.1"
    and parsed.port == 5432
    and parsed.username == "postgres"
    and parsed.path == "/prumo_s0_test_ci"
    and parsed.query == ""
    and parsed.fragment == ""
):
    raise SystemExit("WA28 refuses any connection outside CI disposable PostgreSQL")

# Only known environment variables: PGHOSTADDR/PGSERVICE/PGOPTIONS etc may
# otherwise override libpq's target or activate unexpected service files.
base_env = {
    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    "HOME": os.environ.get("HOME", "/tmp"),
    "LC_ALL": "C",
    "PGCONNECT_TIMEOUT": "5",
}
def command():
    return ["psql", "-X", "-qAt", "-v", "ON_ERROR_STOP=1", dsn]

def run_sql(query, app="wa28_observer"):
    result = subprocess.run(
        command() + ["-c", query], env={**base_env, "PGAPPNAME": app},
        input="", capture_output=True, text=True, timeout=20, check=False,
    )
    if result.returncode:
        raise RuntimeError("WA28 fixture SQL process failed: " + result.stderr[-500:])
    return result.stdout.strip()

def open_transaction(app, statement):
    worker = subprocess.Popen(
        command(), env={**base_env, "PGAPPNAME": app},
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )
    assert worker.stdin is not None
    worker.stdin.write("BEGIN;\n" + statement + ";\n")
    worker.stdin.flush()
    def idle():
        return run_sql(
            "SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
            f"WHERE application_name='{app}' "
            "AND state='idle in transaction');"
        ) == "t"
    await_condition(idle, f"{app}: SQL transaction not ready")
    return worker

def start_blocker(app, statement):
    proc = subprocess.Popen(
        command() + ["-c", statement],
        env={**base_env, "PGAPPNAME": app},
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )
    def waiting():
        return run_sql(
            "SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
            f"WHERE application_name='{app}' "
            "AND cardinality(pg_blocking_pids(pid))>0);"
        ) == "t"
    await_condition(waiting, f"{app}: expected row lock conflict not observed")
    return proc

def await_condition(predicate, label):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.065)
    raise AssertionError(label)

def close_holder(proc, commit=True):
    assert proc.stdin is not None
    proc.stdin.write("COMMIT;\n" if commit else "ROLLBACK;\n")
    proc.stdin.flush()
    proc.stdin.close()
    try:
        rc = proc.wait(timeout=12)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise
    output = (proc.stdout.read() if proc.stdout else "").strip()
    error = (proc.stderr.read() if proc.stderr else "").strip()
    if rc:
        raise AssertionError(f"holder aborted: {error[-400:]}")
    return output

def close_blocker(proc):
    stdout, stderr = proc.communicate(timeout=12)
    if proc.returncode != 0:
        raise AssertionError(f"blocked statement failed: {stderr[-400:]}")
    return stdout.strip()

def assert_sql(sql, expected):
    observed = run_sql(sql)
    assert observed == expected, f"expected {expected!r}, got {observed!r}"

def ok(n):
    print(f"WA28-{n:02} PASS", flush=True)

assert_sql("SELECT COUNT(*) FROM wa28_lab.authority", "6")
ok(1)

# Case 1: reserve takes case lock first. Revocation MUST wait and then cancel.
first = open_transaction(
    "wa28_hold_reservation",
    "SELECT wa28_lab.attempt_reserve("
    "'shop_A','case_reserve_first','planner_A','attempt_first',1,1)",
)
assert first.poll() is None
ok(2)
revoker = start_blocker(
    "wa28_revoke_wait",
    "SELECT wa28_lab.revoke_fixture('shop_A','case_reserve_first','OPT_OUT')",
)
ok(3)
assert close_holder(first) == "LAB_RESERVED"
assert close_blocker(revoker) == "LAB_REVOKED"
assert_sql(
    "SELECT status FROM wa28_lab.reservations "
    "WHERE shop_ref='shop_A' AND case_ref='case_reserve_first'",
    "LAB_CANCELLED",
)
ok(4)
assert_sql(
    "SELECT wa28_lab.attempt_reserve("
    "'shop_A','case_reserve_first','planner_A','attempt_late',1,1)",
    "LAB_DENIED",
)
ok(5)
assert_sql(
    "SELECT opted_out::text FROM wa28_lab.authority "
    "WHERE shop_ref='shop_A' AND case_ref='case_reserve_first'",
    "true",
)
ok(6)

# Case 2: revocation holds authority lock first. Attempt waits then fails.
rev_first = open_transaction(
    "wa28_hold_revocation",
    "SELECT wa28_lab.revoke_fixture('shop_A','case_revoke_first','GRANT')",
)
ok(7)
attempt_wait = start_blocker(
    "wa28_attempt_wait",
    "SELECT wa28_lab.attempt_reserve("
    "'shop_A','case_revoke_first','planner_A','attempt_second',1,1)",
)
ok(8)
assert close_holder(rev_first) == "LAB_REVOKED"
assert close_blocker(attempt_wait) == "LAB_DENIED"
assert_sql(
    "SELECT COUNT(*) FROM wa28_lab.reservations "
    "WHERE shop_ref='shop_A' AND case_ref='case_revoke_first'",
    "0",
)
ok(9)
assert_sql(
    "SELECT grant_active::text FROM wa28_lab.authority "
    "WHERE shop_ref='shop_A' AND case_ref='case_revoke_first'",
    "false",
)
ok(10)

# Exact duplicate reservation and stale/cross-tenant/actor rejection.
attempt = (
    "SELECT wa28_lab.attempt_reserve("
    "'shop_A','case_duplicate','planner_A','attempt_same',1,1)"
)
assert_sql(attempt, "LAB_RESERVED")
assert_sql(attempt, "LAB_ALREADY_RESERVED")
ok(11)
assert_sql(
    "SELECT COUNT(*) FROM wa28_lab.reservations "
    "WHERE shop_ref='shop_A' AND case_ref='case_duplicate'",
    "1",
)
ok(12)
assert_sql(
    "SELECT wa28_lab.attempt_reserve("
    "'shop_A','case_duplicate','planner_A','attempt_stale',2,1)",
    "LAB_DENIED",
)
ok(13)
assert_sql(
    "SELECT wa28_lab.attempt_reserve("
    "'shop_A','case_duplicate','planner_other','attempt_wrong_actor',1,1)",
    "LAB_DENIED",
)
ok(14)
assert_sql(
    "SELECT wa28_lab.attempt_reserve("
    "'shop_B','case_duplicate','planner_B','attempt_wrong_tenant',1,1)",
    "LAB_DENIED",
)
ok(15)
assert_sql(
    "SELECT wa28_lab.attempt_reserve("
    "'shop_A','case_suspended','planner_A','attempt_paused',1,1)",
    "LAB_DENIED",
)
ok(16)

# Rollback never leaves a durable reservation, never generates a Graph send.
rolled = open_transaction(
    "wa28_rollback_reservation",
    "SELECT wa28_lab.attempt_reserve("
    "'shop_A','case_rollback','planner_A','attempt_rollback',1,1)",
)
assert close_holder(rolled, commit=False) == "LAB_RESERVED"
assert_sql(
    "SELECT COUNT(*) FROM wa28_lab.reservations "
    "WHERE shop_ref='shop_A' AND case_ref='case_rollback'",
    "0",
)
ok(17)

# No per-shop contamination, no production authority even in all good states.
assert_sql(
    "SELECT wa28_lab.attempt_reserve("
    "'shop_B','case_control','planner_B','attempt_b',1,1)",
    "LAB_RESERVED",
)
assert_sql(
    "SELECT opted_out::text||','||grant_active::text "
    "FROM wa28_lab.authority WHERE shop_ref='shop_B' AND case_ref='case_control'",
    "false,true",
)
ok(18)
assert_sql(
    "SELECT COUNT(*) FROM wa28_lab.reservations "
    "WHERE send_authorized OR production_authorized",
    "0",
)
ok(19)
assert_sql(
    "SELECT COUNT(*) FROM wa28_lab.reservations "
    "WHERE status='LAB_RESERVED'",
    "2",
)
ok(20)
# Malformed revocation action must never mutate case/version or cancel B.
assert_sql(
    "SELECT wa28_lab.revoke_fixture('shop_B','case_control',NULL)",
    "LAB_DENIED",
)
assert_sql(
    "SELECT version FROM wa28_lab.authority "
    "WHERE shop_ref='shop_B' AND case_ref='case_control'",
    "1",
)
assert_sql(
    "SELECT status FROM wa28_lab.reservations "
    "WHERE shop_ref='shop_B' AND case_ref='case_control'",
    "LAB_RESERVED",
)
ok(21)
print("PASS WA28: 21 checks, two observed blocking races, separate COMMIT/ROLLBACK", flush=True)
