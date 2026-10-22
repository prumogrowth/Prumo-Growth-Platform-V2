#!/usr/bin/env python3
"""WA29 physical PG17 row-lock interleavings, explicitly inert. No network APIs."""
import os
import subprocess
import time
from urllib.parse import urlsplit

dsn = os.environ.get("PRUMO_TEST_DATABASE_URL", "")
u = urlsplit(dsn)
if not (u.scheme == "postgresql" and u.hostname == "127.0.0.1" and
        u.port == 5432 and u.username == "postgres" and
        u.path == "/prumo_s0_test_ci" and not u.query and not u.fragment):
    raise SystemExit("WA29 refuses non-disposable PostgreSQL target")
env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
       "HOME": os.environ.get("HOME", "/tmp"),
       "LC_ALL": "C", "PGCONNECT_TIMEOUT": "5"}
psql = ["psql", "-X", "-qAt", "-v", "ON_ERROR_STOP=1", dsn]

def read(sql, app="wa29_read"):
    p = subprocess.run(psql + ["-c", sql], env={**env, "PGAPPNAME": app},
                       capture_output=True, text=True, timeout=20, check=False)
    if p.returncode:
        raise AssertionError("WA29 SQL failure: " + p.stderr[-500:])
    return p.stdout.strip()

def wait_for(test, label):
    end = time.monotonic()+12
    while time.monotonic()<end:
        if test(): return
        time.sleep(.06)
    raise AssertionError("WA29 lock/transaction not observed: " + label)

def transaction(app, statement):
    p = subprocess.Popen(psql, env={**env, "PGAPPNAME": app},
       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
       text=True, bufsize=1)
    assert p.stdin is not None
    p.stdin.write("BEGIN;\n"+statement+";\n")
    p.stdin.flush()
    wait_for(lambda: read(
        "SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
        f"WHERE application_name='{app}' AND state='idle in transaction')"
    ) == "t", app)
    return p

def blocked(app, statement):
    p = subprocess.Popen(psql+["-c",statement],
      env={**env, "PGAPPNAME": app},stdin=subprocess.DEVNULL,
      stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    wait_for(lambda: read(
        "SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
        f"WHERE application_name='{app}' AND cardinality(pg_blocking_pids(pid))>0)"
    ) == "t", app)
    return p

def finish_holder(p,commit=True):
    assert p.stdin is not None
    p.stdin.write("COMMIT;\n" if commit else "ROLLBACK;\n")
    p.stdin.flush()
    p.stdin.close()
    code=p.wait(timeout=12)
    output=p.stdout.read().strip() if p.stdout else ""
    error=p.stderr.read().strip() if p.stderr else ""
    assert code==0, error[-500:]
    return output

def finish_blocked(p):
    out,err=p.communicate(timeout=12)
    assert p.returncode==0,err[-500:]
    return out.strip()

def expect(sql,value):
    got=read(sql)
    assert got==value,(sql,got,value)

def ok(n):
    print(f"WA29-{n:02} PASS",flush=True)

def claim(case,attempt,shop="shop_A",actor="planner_A",version=1,catalog=10):
    return (f"SELECT wa29_lab.claim_fixture('{shop}','{case}',"
            f"'{actor}','{attempt}',{version},{catalog})")
def revoke(case,kind="OPT_OUT"):
    return f"SELECT wa29_lab.revoke_fixture('shop_A','{case}','{kind}')"

expect("SELECT count(*) FROM wa29_lab.claims","0")
ok(1)

# Claim before revocation. SQL commit visibly wins the lock first, then a
# revocation invalidates the untransported claim. No sender consumes it.
holder=transaction("wa29_claim_first",claim("case_claim_first","attempt_a1"))
ok(2)
writer=blocked("wa29_revoke_after_claim",revoke("case_claim_first"))
ok(3)
assert finish_holder(holder)=="LAB_CLAIMED_NO_SEND_RIGHTS"
assert finish_blocked(writer)=="LAB_REVOKED"
expect("SELECT state FROM wa29_lab.claims WHERE case_ref='case_claim_first'",
       "LAB_INVALIDATED")
ok(4)
expect("SELECT state FROM wa29_lab.reservations WHERE case_ref='case_claim_first'",
       "LAB_CANCELLED")
ok(5)
expect(claim("case_claim_first","attempt_a1"),"LAB_DENIED")
ok(6)

# Revocation first: claim must wait and is refused on fresh authority.
holder=transaction("wa29_revoke_first",revoke("case_revoke_first","GRANT"))
ok(7)
waiter=blocked("wa29_claim_after_revoke",claim("case_revoke_first","attempt_a2"))
ok(8)
assert finish_holder(holder)=="LAB_REVOKED"
assert finish_blocked(waiter)=="LAB_DENIED"
expect("SELECT count(*) FROM wa29_lab.claims WHERE case_ref='case_revoke_first'","0")
ok(9)

# Two distinct attempts race to claim same case: one immutable claim only.
holder=transaction("wa29_first_of_two",claim("case_two_claims","attempt_a3"))
ok(10)
other=blocked("wa29_second_of_two",claim("case_two_claims","attempt_a4"))
ok(11)
assert finish_holder(holder)=="LAB_CLAIMED_NO_SEND_RIGHTS"
assert finish_blocked(other)=="LAB_DENIED"
expect("SELECT attempt_ref FROM wa29_lab.claims WHERE case_ref='case_two_claims'",
       "attempt_a3")
ok(12)
expect(claim("case_two_claims","attempt_a3"),"LAB_ALREADY_CLAIMED_NO_RETRY")
ok(13)
expect(claim("case_two_claims","attempt_a4"),"LAB_DENIED")
ok(14)

# Rollback claim: no durable effects. Same attempt may be freshly claimed.
rolled=transaction("wa29_rollback_claim",claim("case_rollback","attempt_a5"))
assert finish_holder(rolled,commit=False)=="LAB_CLAIMED_NO_SEND_RIGHTS"
expect("SELECT count(*) FROM wa29_lab.claims WHERE case_ref='case_rollback'","0")
ok(15)
expect(claim("case_rollback","attempt_a5"),"LAB_CLAIMED_NO_SEND_RIGHTS")
ok(16)

expect(claim("case_missing_grant","attempt_a6"),"LAB_DENIED")
expect(claim("case_campaign_expired","attempt_a7"),"LAB_DENIED")
ok(17)
expect(claim("case_rollback","attempt_a5",actor="forged_actor"),"LAB_DENIED")
expect(claim("case_rollback","attempt_a5",version=2),"LAB_DENIED")
expect(claim("case_rollback","attempt_a5",catalog=11),"LAB_DENIED")
ok(18)
expect(claim("case_rollback","attempt_a5",shop="shop_B"),"LAB_DENIED")
expect(claim("case_control","attempt_b1",shop="shop_A"),"LAB_DENIED")
ok(19)
expect("SELECT wa29_lab.revoke_fixture('shop_B','case_control',NULL)","LAB_DENIED")
expect("SELECT state_version FROM wa29_lab.authority WHERE case_ref='case_control'","1")
ok(20)

expect(claim("case_control","attempt_b1",shop="shop_B",actor="planner_B"),
       "LAB_CLAIMED_NO_SEND_RIGHTS")
expect("SELECT state FROM wa29_lab.claims WHERE shop_ref='shop_B'","LAB_CLAIMED")
ok(21)
expect("SELECT count(*) FROM wa29_lab.claims WHERE send_authorized OR production_authorized","0")
expect("SELECT count(*) FROM wa29_lab.reservations WHERE send_authorized OR production_authorized","0")
ok(22)
expect("SELECT count(*) FROM wa29_lab.claims WHERE shop_ref='shop_A' AND state='LAB_CLAIMED'","2")
expect("SELECT count(*) FROM wa29_lab.claims WHERE shop_ref='shop_A' AND state='LAB_INVALIDATED'","1")
ok(23)
print("PASS WA29: 23 physical checks, 3 observed row-lock races, no Graph authority",flush=True)
