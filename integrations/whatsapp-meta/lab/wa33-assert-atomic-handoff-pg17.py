#!/usr/bin/env python3
"""WA33: physical PostgreSQL 17 atomic forensic append in disposable schema.
This DOES NOT exercise real S0, HMAC, Meta Graph, webhook HTTP or authenticated users.
"""
import os
import subprocess
import time
from urllib.parse import urlsplit

dsn=os.environ.get("PRUMO_TEST_DATABASE_URL","")
u=urlsplit(dsn)
if not(u.scheme=="postgresql" and u.hostname=="127.0.0.1" and
       u.port==5432 and u.username=="postgres" and
       u.path=="/prumo_s0_test_ci" and not u.query and not u.fragment):
    raise SystemExit("WA33 refuses all database targets except local disposable CI")
env={"PATH":os.environ.get("PATH","/usr/bin:/bin"),
     "HOME":os.environ.get("HOME","/tmp"),
     "LC_ALL":"C","PGCONNECT_TIMEOUT":"5"}
psql=["psql","-X","-qAt","-v","ON_ERROR_STOP=1",dsn]
records={
 "hist":("APP_A","111111","1234567890","wamid.WA33_HIST","5581900000000"),
 "empty":("APP_A","111111","1234567890","wamid.WA33_REVOKE_FIRST","5581900000000"),
 "rollback":("APP_A","111111","1234567890","wamid.WA33_APPEND_FIRST","5581900000000"),
 "conflict":("APP_A","111111","1234567890","wamid.WA33_DUPLICATE","5581900000000"),
 "late":("APP_A","111111","1234567890","wamid.WA33_LATE","5581900000000"),
 "missing":("APP_A","111111","1234567890","wamid.WA33_MISSING_CLAIM","5581900000000"),
 "b":("APP_B","222222","9876543210","wamid.WA33_B","5581900000011"),
}
def read(query,app="wa33_read"):
    p=subprocess.run(psql+["-c",query],env={**env,"PGAPPNAME":app},
      capture_output=True,text=True,timeout=22,check=False)
    if p.returncode:
        raise AssertionError("WA33 SQL failure: "+p.stderr[-500:])
    return p.stdout.strip()
def expect(query,want):
    result=read(query)
    assert result==want,(query,result,want)
def append(k,event,kind="SENT_REPORTED",version=1,fields=None):
    data=list(records[k])
    if fields:
        for i,value in fields.items():data[i]=value
    args=",".join("'"+v+"'" for v in data)
    return "SELECT wa33_lab.append_fixture("+args+f",'{event}','{kind}',{version})"
def mark(n):print(f"WA33-{n:02} PASS",flush=True)
def wait_until(check,label):
    end=time.monotonic()+12
    while time.monotonic()<end:
        if check():return
        time.sleep(.06)
    raise AssertionError("WA33 expected PG17 lock missing: "+label)
def hold(app,statement):
    p=subprocess.Popen(psql,env={**env,"PGAPPNAME":app},
       stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
       text=True,bufsize=1)
    assert p.stdin is not None
    p.stdin.write("BEGIN;\n"+statement+";\n");p.stdin.flush()
    wait_until(lambda: read("SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
      f"WHERE application_name='{app}' AND state='idle in transaction')")=="t",app)
    return p
def blocked(app,statement):
    p=subprocess.Popen(psql+["-c",statement],env={**env,"PGAPPNAME":app},
      stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    wait_until(lambda: read("SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
      f"WHERE application_name='{app}' AND cardinality(pg_blocking_pids(pid))>0)")=="t",app)
    return p
def finish(p,commit=True):
    assert p.stdin is not None
    p.stdin.write("COMMIT;\n" if commit else "ROLLBACK;\n")
    p.stdin.flush();p.stdin.close()
    rc=p.wait(timeout=12)
    output=p.stdout.read().strip() if p.stdout else ""
    error=p.stderr.read().strip() if p.stderr else ""
    assert rc==0,error[-500:]
    return output
def finish_blocked(p):
    out,err=p.communicate(timeout=12)
    assert p.returncode==0,err[-500:]
    return out.strip()

expect("SELECT count(*) FROM wa33_lab.bindings","7")
expect("SELECT count(*) FROM wa33_lab.events","0")
mark(1)
expect("SELECT state FROM wa29_lab.claims WHERE case_ref='case31_hist'",
       "LAB_INVALIDATED")
mark(2)
expect(append("hist","evt_hist"),"LAB_ARCHIVED_LATE_NO_SEND")
expect("SELECT after_invalidation FROM wa33_lab.events WHERE event_ref='evt_hist'","t")
mark(3)
expect(append("hist","evt_hist"),"LAB_REPLAY_NO_RETRY")
expect("SELECT count(*) FROM wa33_lab.events WHERE event_ref='evt_hist'","1")
mark(4)
expect(append("hist","evt_hist","FAILED_REPORTED"),"LAB_QUARANTINED")
expect("SELECT count(*) FROM wa33_lab.quarantine WHERE case_ref='case31_hist'","1")
mark(5)
expect(append("hist","evt_next"),"LAB_QUARANTINED")
expect("SELECT count(*) FROM wa33_lab.events WHERE case_ref='case31_hist'","1")
mark(6)
expect(append("missing","evt_no_claim"),"LAB_DENIED")
mark(7)
expect(append("empty","evt_wrong_phone",fields={2:"9876543210"}),"LAB_DENIED")
expect(append("b","evt_wrong_waba",fields={1:"111111"}),"LAB_DENIED")
mark(8)
expect(append("empty","evt_wrong_person",fields={4:"5581900000001"}),"LAB_DENIED")
mark(9)
expect(append("empty","evt_wrong_version",version=2),"LAB_DENIED")
mark(10)
expect(append("empty","evt_wrong_app",fields={0:"APP_B"}),"LAB_DENIED")
expect(append("empty","evt_wrong_wamid",fields={3:"wamid.UNKNOWN"}),"LAB_DENIED")
mark(11)
expect("SELECT wa33_lab.append_fixture(NULL,'111111','1234567890','wamid.WA33_REVOKE_FIRST','5581900000000','evt','SENT_REPORTED',1)","LAB_DENIED")
expect("SELECT wa33_lab.append_fixture('APP_A','111111','1234567890','wamid.WA33_REVOKE_FIRST','5581900000000','evt',NULL,1)","LAB_DENIED")
mark(12)
expect("SELECT count(*) FROM wa31_lab.observations WHERE event_ref='evt_hist'","0")
expect("SELECT count(*) FROM wa30_lab.evidence WHERE event_ref='evt_hist'","0")
mark(13)

# Revocation locks synthetic authority first. The append must wait, then
# be retained *as late evidence* rather than resurrecting a claim.
rev=hold("wa33_rev_first",
 "SELECT wa29_lab.revoke_fixture('shop_A','case31_empty','OPT_OUT')")
mark(14)
writer=blocked("wa33_archive_after_revoke",append("empty","evt_after_revoke"))
mark(15)
assert finish(rev)=="LAB_REVOKED"
assert finish_blocked(writer)=="LAB_ARCHIVED_LATE_NO_SEND"
expect("SELECT after_invalidation FROM wa33_lab.events WHERE event_ref='evt_after_revoke'","t")
mark(16)
expect("SELECT state FROM wa29_lab.claims WHERE case_ref='case31_empty'","LAB_INVALIDATED")
expect("SELECT state FROM wa29_lab.reservations WHERE case_ref='case31_empty'","LAB_CANCELLED")
mark(17)

# Append first; revocation waits, while the existing observation remains
# historical and the claim ends invalidated after commit.
writer=hold("wa33_append_first",append("rollback","evt_before_revoke"))
mark(18)
rev=blocked("wa33_rev_after_archive",
 "SELECT wa29_lab.revoke_fixture('shop_A','case31_rollback','GRANT')")
mark(19)
assert finish(writer)=="LAB_ARCHIVED_UNVERIFIED_NO_SEND"
assert finish_blocked(rev)=="LAB_REVOKED"
expect("SELECT after_invalidation FROM wa33_lab.events WHERE event_ref='evt_before_revoke'","f")
mark(20)
expect("SELECT state FROM wa29_lab.claims WHERE case_ref='case31_rollback'","LAB_INVALIDATED")
mark(21)

# Two concurrent same-event appenders cannot create duplicate observations.
first=hold("wa33_first_replay",append("conflict","evt_duplicate"))
mark(22)
second=blocked("wa33_second_replay",append("conflict","evt_duplicate"))
mark(23)
assert finish(first)=="LAB_ARCHIVED_UNVERIFIED_NO_SEND"
assert finish_blocked(second)=="LAB_REPLAY_NO_RETRY"
expect("SELECT count(*) FROM wa33_lab.events WHERE event_ref='evt_duplicate'","1")
mark(24)

# Retargeting binding takes same case lock. A previously observed candidate
# must not become authoritative after binding recipient/revision changes.
change=hold("wa33_change_binding",
 "SELECT wa33_lab.change_binding_fixture('shop_B','case31_b','5581900000022')")
mark(25)
stale=blocked("wa33_stale_after_change",append("b","evt_stale"))
mark(26)
assert finish(change)=="LAB_BINDING_CHANGED"
assert finish_blocked(stale)=="LAB_DENIED"
expect("SELECT count(*) FROM wa33_lab.events WHERE case_ref='case31_b'","0")
mark(27)
expect(append("b","evt_fresh",version=2,fields={4:"5581900000022"}),
       "LAB_ARCHIVED_UNVERIFIED_NO_SEND")
mark(28)
expect("SELECT count(*) FROM wa33_lab.events WHERE send_authorized OR "
       "production_authorized OR ack_allowed OR definitive_failure_count_increment","0")
mark(29)
expect("SELECT count(*) FROM wa29_lab.claims WHERE case_ref IN "
       "('case31_empty','case31_rollback') AND state='LAB_INVALIDATED'","2")
expect("SELECT count(*) FROM wa33_lab.quarantine","1")
mark(30)
print("PASS WA33: 30 PostgreSQL assertions, four observed row-lock races; no Meta or authenticated S0",flush=True)
