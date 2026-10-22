#!/usr/bin/env python3
"""WA31: real PG17 synthetic forensic archive, NO Graph, no webhook ACK or auth."""
import json
import os
import subprocess
import time
from urllib.parse import urlsplit

dsn=os.getenv("PRUMO_TEST_DATABASE_URL","")
u=urlsplit(dsn)
if not(u.scheme=="postgresql" and u.hostname=="127.0.0.1" and
       u.port==5432 and u.username=="postgres" and
       u.path=="/prumo_s0_test_ci" and not u.query and not u.fragment):
    raise SystemExit("WA31 refuses all database targets except local disposable CI")
env={"PATH":os.getenv("PATH","/usr/bin:/bin"),
     "HOME":os.getenv("HOME","/tmp"),"LC_ALL":"C","PGCONNECT_TIMEOUT":"5"}
psql=["psql","-X","-qAt","-v","ON_ERROR_STOP=1",dsn]
samples=[]
def sql(query,app="wa31_read"):
    p=subprocess.run(psql+["-c",query],capture_output=True,text=True,
        env={**env,"PGAPPNAME":app},timeout=22,check=False)
    if p.returncode:raise AssertionError("WA31 SQL failure: "+p.stderr[-500:])
    return p.stdout.strip()
def expect(query,want):
    got=sql(query)
    assert got==want,(query,got,want)
def archive(case,event,kind="ACCEPTED",shop="shop_A",attempt=None):
    attempt=attempt or "attempt31_"+case[7:]
    return ("SELECT wa31_lab.archive_fixture("
      f"'{shop}','{case}','{attempt}','{event}','{kind}')")
def read(case,shop="shop_A",attempt=None,label=None,want=None):
    attempt=attempt or "attempt31_"+case[7:]
    value=json.loads(sql("SELECT wa31_lab.read_fixture("
        f"'{shop}','{case}','{attempt}')"))
    assert len(value)==8
    for k in ("retry_external","send_authorized","ack_allowed",
              "production_authorized","delivery_confirmed",
              "definitive_failure_count_increment","case_transition_authorized"):
        assert value[k] is False,(case,k)
    if want:assert value["outcome"]==want,(case,value,want)
    if label:samples.append({"label":label,"snapshot":value})
    return value["outcome"]
def mark(n):print(f"WA31-{n:02} PASS",flush=True)
def await_condition(check,label):
    end=time.monotonic()+12
    while time.monotonic()<end:
        if check():return
        time.sleep(.06)
    raise AssertionError("WA31 expected real database locking "+label)
def hold(app,statement):
    p=subprocess.Popen(psql,env={**env,"PGAPPNAME":app},
       stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
       text=True,bufsize=1)
    assert p.stdin is not None
    p.stdin.write("BEGIN;\n"+statement+";\n");p.stdin.flush()
    await_condition(lambda: sql("SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
      f"WHERE application_name='{app}' AND state='idle in transaction')")=="t",app)
    return p
def wait_blocked(app,statement):
    p=subprocess.Popen(psql+["-c",statement],env={**env,"PGAPPNAME":app},
      stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
      text=True)
    await_condition(lambda: sql("SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
      f"WHERE application_name='{app}' AND cardinality(pg_blocking_pids(pid))>0)")=="t",app)
    return p
def finish(p,commit=True):
    assert p.stdin is not None
    p.stdin.write("COMMIT;\n" if commit else "ROLLBACK;\n")
    p.stdin.flush();p.stdin.close()
    rc=p.wait(timeout=12)
    out=p.stdout.read().strip() if p.stdout else ""
    err=p.stderr.read().strip() if p.stderr else ""
    assert rc==0,err[-500:]
    return out
def finish_blocked(p):
    out,err=p.communicate(timeout=12)
    assert p.returncode==0,err[-500:]
    return out.strip()

expect("SELECT count(*) FROM wa31_lab.observations","0")
mark(1)
read("case31_empty",label="empty",want="LAB_EMPTY_CLAIM")
mark(2)
read("case31_no_claim",label="no_claim",want="LAB_NO_CLAIM")
expect(archive("case31_no_claim","no_claim"),"LAB_DENIED")
mark(3)
expect(archive("case31_hist","evt_before","ACCEPTED"),"LAB_ARCHIVED_UNVERIFIED")
read("case31_hist",label="active",want="LAB_ACTIVE_OBSERVATION")
mark(4)
expect(archive("case31_hist","evt_before","ACCEPTED"),"LAB_REPLAY_NO_RESEND")
expect("SELECT count(*) FROM wa31_lab.observations WHERE case_ref='case31_hist'","1")
mark(5)
expect(archive("case31_hist","evt_before_two","UNKNOWN"),"LAB_ARCHIVED_UNVERIFIED")
read("case31_hist",want="LAB_ACTIVE_OBSERVATION")
mark(6)
expect("SELECT wa29_lab.revoke_fixture('shop_A','case31_hist','OPT_OUT')",
       "LAB_REVOKED")
read("case31_hist",label="historical",want="LAB_INVALIDATED_HISTORICAL")
mark(7)
expect(archive("case31_hist","evt_after","SENT_REPORTED"),
       "LAB_ARCHIVED_AFTER_REVOCATION")
read("case31_hist",label="late",want="LAB_LATE_OBSERVATION")
mark(8)
expect("SELECT state FROM wa29_lab.claims WHERE case_ref='case31_hist'",
       "LAB_INVALIDATED")
expect("SELECT state FROM wa29_lab.reservations WHERE case_ref='case31_hist'",
       "LAB_CANCELLED")
mark(9)
expect(archive("case31_hist","evt_after","SENT_REPORTED"),"LAB_REPLAY_NO_RESEND")
expect("SELECT count(*) FROM wa31_lab.observations WHERE case_ref='case31_hist'","3")
mark(10)
expect(archive("case31_late","evt_wrong","ACCEPTED",attempt="attempt31_hist"),"LAB_DENIED")
expect(archive("case31_hist","evt_wrong","ACCEPTED",shop="shop_B"),"LAB_DENIED")
mark(11)
expect(archive("case31_conflict","evt_conflict","ACCEPTED"),"LAB_ARCHIVED_UNVERIFIED")
expect(archive("case31_conflict","evt_conflict","FAILED_REPORTED"),"LAB_QUARANTINED")
read("case31_conflict",label="conflict",want="LAB_KIND_CONFLICT")
mark(12)
expect(archive("case31_conflict","evt_new","UNKNOWN"),"LAB_QUARANTINED")
expect("SELECT count(*) FROM wa31_lab.observations WHERE case_ref='case31_conflict'","1")
mark(13)
expect("SELECT wa29_lab.revoke_fixture('shop_A','case31_late','GRANT')","LAB_REVOKED")
read("case31_late",want="LAB_INVALIDATED_EMPTY")
expect(archive("case31_late","evt_post","SENT_REPORTED"),"LAB_ARCHIVED_AFTER_REVOCATION")
read("case31_late",label="post_only",want="LAB_LATE_OBSERVATION")
mark(14)
expect("SELECT count(*) FROM wa30_lab.evidence WHERE case_ref LIKE 'case31_%'","0")
expect("SELECT count(*) FROM wa30_lab.quarantine WHERE case_ref LIKE 'case31_%'","0")
mark(15)
expect("SELECT wa31_lab.archive_fixture('shop_A','case31_hist','attempt31_hist',NULL,'ACCEPTED')","LAB_DENIED")
expect("SELECT wa31_lab.archive_fixture('shop_A','case31_hist','attempt31_hist','evt_null',NULL)","LAB_DENIED")
expect("SELECT wa31_lab.archive_fixture('shop_A','case31_hist','attempt31_hist','evt_bad','delivered')","LAB_DENIED")
mark(16)
expect("SELECT wa31_lab.archive_fixture('shop_A','case31_hist','attempt31_hist','evt_bad!','ACCEPTED')","LAB_DENIED")
read("case31_hist",attempt="attempt31_wrong",label="wrong_scope",want="LAB_NO_CLAIM")
mark(17)

rolled=hold("wa31_rollback",archive("case31_rollback","evt_rollback","UNKNOWN"))
assert finish(rolled,False)=="LAB_ARCHIVED_UNVERIFIED"
read("case31_rollback",label="rolled_back",want="LAB_EMPTY_CLAIM")
mark(18)
expect(archive("case31_b","evt_b","ACCEPTED",shop="shop_B"),
       "LAB_ARCHIVED_UNVERIFIED")
read("case31_b",shop="shop_B",label="other_shop",want="LAB_ACTIVE_OBSERVATION")
mark(19)
read("case31_b",shop="shop_A",want="LAB_NO_CLAIM")
expect("SELECT state_version FROM wa29_lab.authority WHERE case_ref='case31_b'","1")
mark(20)

# Conflict A: revocation holds case row first; forensic record waits then
# commits as POST-revocation, without granting any rights.
rev=hold("wa31_rev_first",
  "SELECT wa29_lab.revoke_fixture('shop_A','case31_revoke_first','OPT_OUT')")
mark(21)
writer=wait_blocked("wa31_archive_second",
  archive("case31_revoke_first","evt_rev_first","SENT_REPORTED"))
mark(22)
assert finish(rev)=="LAB_REVOKED"
assert finish_blocked(writer)=="LAB_ARCHIVED_AFTER_REVOCATION"
read("case31_revoke_first",label="race_post",want="LAB_LATE_OBSERVATION")
mark(23)

# Conflict B: forensic record precedes revocation. Existing observation
# remains inspectable, but claim stays invalidated after revocation.
writer=hold("wa31_archive_first",
  archive("case31_observe_first","evt_obs_first","FAILED_REPORTED"))
mark(24)
rev=wait_blocked("wa31_rev_second",
  "SELECT wa29_lab.revoke_fixture('shop_A','case31_observe_first','TEMPLATE')")
mark(25)
assert finish(writer)=="LAB_ARCHIVED_UNVERIFIED"
assert finish_blocked(rev)=="LAB_REVOKED"
read("case31_observe_first",label="race_historical",
     want="LAB_INVALIDATED_HISTORICAL")
mark(26)
expect("SELECT count(*) FROM wa31_lab.observations WHERE "
 "send_authorized OR production_authorized OR ack_allowed OR "
 "definitive_failure_count_increment","0")
mark(27)
expect("SELECT count(*) FROM wa29_lab.claims WHERE case_ref LIKE 'case31_%' "
 "AND state='LAB_INVALIDATED'","4")
mark(28)
expect("SELECT count(*) FROM wa31_lab.quarantines WHERE case_ref='case31_conflict'","1")
mark(29)
expect("SELECT count(*) FROM wa31_lab.observations WHERE case_ref='case31_revoke_first' "
 "AND observed_after_invalidation","1")
expect("SELECT count(*) FROM wa31_lab.observations WHERE case_ref='case31_observe_first' "
 "AND observed_after_invalidation","0")
mark(30)

runner=os.path.join(os.path.dirname(__file__),"wa31-assert-db-late-evidence.ts")
payload="\n".join(json.dumps(x,sort_keys=True) for x in samples)+"\n"
p=subprocess.run(["node","--experimental-strip-types",runner],
 input=payload,capture_output=True,text=True,
 env={**env,"NODE_OPTIONS":"","NODE_PATH":""},timeout=15,check=False)
assert p.returncode==0,p.stderr[-500:]
assert p.stdout.strip()=="WA31-TSDB PASS: 12 PG17 readbacks classified fail-closed",p.stdout
mark(31)
print("PASS WA31: 31 PG17 checks, two blocked lock races, 12 typed readbacks, NO Meta",flush=True)
