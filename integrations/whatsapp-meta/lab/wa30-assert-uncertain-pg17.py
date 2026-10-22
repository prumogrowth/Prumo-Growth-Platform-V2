#!/usr/bin/env python3
"""WA30: real PG17 fixture evidence reconciliation, no Graph/S0 credentials.

psql connections are separate. Their SQL observability doesn't authenticate
Meta receipts or prove whether any external request ever happened.
"""
import json
import os
import subprocess
import time
from urllib.parse import urlsplit

dsn = os.getenv("PRUMO_TEST_DATABASE_URL","")
u = urlsplit(dsn)
if not (u.scheme=="postgresql" and u.hostname=="127.0.0.1" and
        u.port==5432 and u.username=="postgres" and
        u.path=="/prumo_s0_test_ci" and not u.query and not u.fragment):
    raise SystemExit("WA30 refuses any non-disposable PG target")
env={"PATH":os.environ.get("PATH","/usr/bin:/bin"),
     "HOME":os.environ.get("HOME","/tmp"),
     "LC_ALL":"C","PGCONNECT_TIMEOUT":"5"}
psql=["psql","-X","-qAt","-v","ON_ERROR_STOP=1",dsn]
samples=[]

def read(sql,app="wa30_read"):
    p=subprocess.run(psql+["-c",sql],env={**env,"PGAPPNAME":app},
       text=True,capture_output=True,timeout=25,check=False)
    if p.returncode:
        raise AssertionError("WA30 SQL failure: "+p.stderr[-600:])
    return p.stdout.strip()
def expect(sql,value):
    got=read(sql)
    assert got==value,(sql,got,value)
def record(case,ref,kind,shop="shop_A",attempt=None):
    attempt=attempt or "attempt_"+case[5:]
    return ("SELECT wa30_lab.record_fixture("
       f"'{shop}','{case}','{attempt}','{ref}','{kind}')")
def snapshot(case,shop="shop_A",attempt=None,label=None,expected=None):
    attempt=attempt or "attempt_"+case[5:]
    data=json.loads(read("SELECT wa30_lab.read_fixture("
        f"'{shop}','{case}','{attempt}')"))
    assert len(data)==8 and all(data[k] is False for k in (
       "retry_external","send_authorized","ack_allowed",
       "production_authorized","delivery_confirmed",
       "definitive_failure_count_increment","case_transition_authorized"))
    if expected is not None:
        assert data["outcome"]==expected,(case,data["outcome"],expected)
    if label:
        samples.append({"label":label,"snapshot":data})
    return data["outcome"]
def mark(n):
    print(f"WA30-{n:02} PASS",flush=True)
def await_condition(test,label):
    end=time.monotonic()+12
    while time.monotonic()<end:
        if test(): return
        time.sleep(.06)
    raise AssertionError("WA30 expected lock not observed "+label)
def transaction(app,statement):
    p=subprocess.Popen(psql,env={**env,"PGAPPNAME":app},
       stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
       text=True,bufsize=1)
    assert p.stdin is not None
    p.stdin.write("BEGIN;\n"+statement+";\n");p.stdin.flush()
    await_condition(lambda: read("SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
       f"WHERE application_name='{app}' AND state='idle in transaction')")=="t",app)
    return p
def blocked(app,statement):
    p=subprocess.Popen(psql+["-c",statement],env={**env,"PGAPPNAME":app},
      stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
      text=True)
    await_condition(lambda: read("SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
       f"WHERE application_name='{app}' AND cardinality(pg_blocking_pids(pid))>0)")=="t",app)
    return p
def end_transaction(p,commit=True):
    assert p.stdin is not None
    p.stdin.write("COMMIT;\n" if commit else "ROLLBACK;\n")
    p.stdin.flush();p.stdin.close()
    rc=p.wait(timeout=12)
    out=p.stdout.read().strip() if p.stdout else ""
    err=p.stderr.read().strip() if p.stderr else ""
    assert rc==0,err[-500:]
    return out
def end_blocked(p):
    out,err=p.communicate(timeout=12)
    assert p.returncode==0,err[-500:]
    return out.strip()

expect("SELECT count(*) FROM wa30_lab.evidence","0")
mark(1)
snapshot("case_unknown",label="unknown",expected="LAB_CLAIM_UNRESOLVED")
mark(2)
expect(record("case_unknown","receipt_unknown","UNKNOWN"),"LAB_RECORDED_UNVERIFIED")
snapshot("case_unknown",expected="LAB_CLAIM_UNRESOLVED")
mark(3)
snapshot("case_absent",label="absent",expected="LAB_ABSENT_UNKNOWN")
mark(4)
expect(record("case_accepted","receipt_accept","ACCEPTED"),"LAB_RECORDED_UNVERIFIED")
snapshot("case_accepted",label="accepted",expected="LAB_PROVIDER_ACCEPTED_UNVERIFIED")
mark(5)
expect(record("case_accepted","receipt_accept","ACCEPTED"),"LAB_REPLAY_NO_RESEND")
expect("SELECT count(*) FROM wa30_lab.evidence WHERE case_ref='case_accepted'","1")
mark(6)
expect(record("case_accepted","receipt_unknown","UNKNOWN"),"LAB_RECORDED_UNVERIFIED")
snapshot("case_accepted",expected="LAB_PROVIDER_ACCEPTED_UNVERIFIED")
mark(7)
expect(record("case_sent","receipt_sent","SENT_REPORTED"),"LAB_RECORDED_UNVERIFIED")
snapshot("case_sent",label="sent",expected="LAB_SENT_UNVERIFIED")
mark(8)
expect(record("case_sent","receipt_accepted","ACCEPTED"),"LAB_RECORDED_UNVERIFIED")
snapshot("case_sent",expected="LAB_SENT_UNVERIFIED")
mark(9)
expect(record("case_failed","receipt_failed","FAILED_REPORTED"),"LAB_RECORDED_UNVERIFIED")
snapshot("case_failed",label="failed",expected="LAB_FAILURE_UNVERIFIED")
mark(10)
expect(record("case_conflict","receipt_sent","SENT_REPORTED"),"LAB_RECORDED_UNVERIFIED")
expect(record("case_conflict","receipt_failed","FAILED_REPORTED"),"LAB_RECORDED_UNVERIFIED")
snapshot("case_conflict",label="conflict",expected="LAB_CONFLICT")
mark(11)
expect(record("case_receipt_collision","receipt_same","ACCEPTED"),"LAB_RECORDED_UNVERIFIED")
expect(record("case_receipt_collision","receipt_same","SENT_REPORTED"),"LAB_QUARANTINED")
snapshot("case_receipt_collision",label="collision",expected="LAB_CONFLICT")
mark(12)
expect(record("case_receipt_collision","receipt_next","UNKNOWN"),"LAB_QUARANTINED")
expect("SELECT count(*) FROM wa30_lab.evidence WHERE case_ref='case_receipt_collision'","1")
mark(13)

# Recovery/retention after revocation; old evidence never resurrects claim.
expect(record("case_invalidated","receipt_accept","ACCEPTED"),"LAB_RECORDED_UNVERIFIED")
expect("SELECT wa29_lab.revoke_fixture('shop_A','case_invalidated','OPT_OUT')",
       "LAB_REVOKED")
snapshot("case_invalidated",label="invalidated",expected="LAB_INVALIDATED")
mark(14)
expect(record("case_invalidated","receipt_late","SENT_REPORTED"),"LAB_DENIED")
expect("SELECT count(*) FROM wa30_lab.evidence WHERE case_ref='case_invalidated'","1")
mark(15)
expect("SELECT wa29_lab.revoke_fixture('shop_A','case_revoke_first30','GRANT')",
       "LAB_REVOKED")
snapshot("case_revoke_first30",expected="LAB_INVALIDATED")
expect(record("case_revoke_first30","receipt_late","ACCEPTED"),"LAB_DENIED")
mark(16)

expect(record("case_absent","receipt_absent","UNKNOWN"),"LAB_DENIED")
expect(record("case_unknown","receipt_foreign","UNKNOWN",shop="shop_B"),"LAB_DENIED")
expect("SELECT wa30_lab.record_fixture('shop_A','case_unknown','attempt_wrong','receipt','UNKNOWN')","LAB_DENIED")
mark(17)
expect("SELECT wa30_lab.record_fixture('shop_A','case_unknown','attempt_unknown','receipt',NULL)","LAB_DENIED")
expect("SELECT wa30_lab.record_fixture('shop_A','case_unknown','attempt_unknown',NULL,'UNKNOWN')","LAB_DENIED")
expect("SELECT wa30_lab.record_fixture('shop_A','case_unknown','attempt_unknown','receipt','sent')","LAB_DENIED")
mark(18)

# ROLLBACK of synthetic receipt leaves only a durable claim, no extra proof.
p=transaction("wa30_rollback_receipt",record("case_rollback30","receipt_rollback","ACCEPTED"))
assert end_transaction(p,commit=False)=="LAB_RECORDED_UNVERIFIED"
snapshot("case_rollback30",label="rolled_back",expected="LAB_CLAIM_UNRESOLVED")
mark(19)
expect(record("case_b30","receipt_b","ACCEPTED",shop="shop_B"),
       "LAB_RECORDED_UNVERIFIED")
snapshot("case_b30",shop="shop_B",label="other_shop",expected="LAB_PROVIDER_ACCEPTED_UNVERIFIED")
mark(20)
snapshot("case_unknown",shop="shop_B",expected="LAB_ABSENT_UNKNOWN")
mark(21)

# Concurrency: evidence writes before a subsequent revocation; older receipt
# is durable, but readback invalidates upon opt-out.
first=transaction("wa30_evidence_first",record("case_race","receipt_race","ACCEPTED"))
mark(22)
last=blocked("wa30_revoke_second",
 "SELECT wa29_lab.revoke_fixture('shop_A','case_race','OPT_OUT')")
mark(23)
assert end_transaction(first)=="LAB_RECORDED_UNVERIFIED"
assert end_blocked(last)=="LAB_REVOKED"
snapshot("case_race",label="race_invalidated",expected="LAB_INVALIDATED")
mark(24)

# Independent auth/claim fixture row still holds a claim after rollback, while
# false terminal reports have no authority to move commercial state.
expect("SELECT count(*) FROM wa30_lab.evidence WHERE "
       "send_authorized OR production_authorized OR definitive_failure_count_increment","0")
expect("SELECT count(*) FROM wa29_lab.claims WHERE send_authorized OR production_authorized","0")
mark(25)
expect("SELECT count(*) FROM wa30_lab.quarantine WHERE case_ref='case_receipt_collision'","1")
mark(26)

# Feed raw readback rows directly into the *same* Node TS classifier tested
# by the offline runner, without inventing authenticated source origins.
runner=os.path.join(os.path.dirname(__file__),"wa30-assert-db-recovery.ts")
payload="\n".join(json.dumps(x,sort_keys=True) for x in samples)+"\n"
p=subprocess.run(["node","--experimental-strip-types",runner],input=payload,
  text=True,capture_output=True,env={**env,"NODE_OPTIONS":"","NODE_PATH":""},
  timeout=15,check=False)
assert p.returncode==0,p.stderr[-600:]
assert p.stdout.strip()=="WA30-TSDB PASS: 11 PG17 readbacks classified fail-closed",p.stdout
mark(27)
print("PASS WA30: 27 checks with physical PG17 COMMIT/ROLLBACK/row lock, no Meta",flush=True)
