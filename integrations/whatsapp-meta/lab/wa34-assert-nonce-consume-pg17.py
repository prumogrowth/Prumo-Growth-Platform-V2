#!/usr/bin/env python3
"""WA34 offline PG17 proof: consume a synthetic nonce within a forensic append.
NO verified Meta ingress, service principal, S0 authorization, Graph or ACK.
"""
import os
import subprocess
import time
from urllib.parse import urlsplit

dsn=os.environ.get("PRUMO_TEST_DATABASE_URL","")
u=urlsplit(dsn)
if not(u.scheme=="postgresql" and u.hostname=="127.0.0.1" and
 u.port==5432 and u.username=="postgres" and u.path=="/prumo_s0_test_ci" and
 not u.query and not u.fragment):
 raise SystemExit("WA34 refuses non-disposable local PG17 target")
env={"PATH":os.environ.get("PATH","/usr/bin:/bin"),
 "HOME":os.environ.get("HOME","/tmp"),"LC_ALL":"C","PGCONNECT_TIMEOUT":"5"}
psql=["psql","-X","-qAt","-v","ON_ERROR_STOP=1",dsn]
now=1792320000000
items={
 'late':('APP_A','111111','1234567890','wamid.WA33_LATE','5581900000000',1),
 'active':('APP_A','111111','1234567890','wamid.WA33_DUPLICATE','5581900000000',1),
 'b':('APP_B','222222','9876543210','wamid.WA33_B','5581900000022',2),
 'missing':('APP_A','111111','1234567890','wamid.WA33_MISSING_CLAIM','5581900000000',1),
}
def query(command,app="wa34_read"):
 p=subprocess.run(psql+["-c",command],env={**env,"PGAPPNAME":app},
  capture_output=True,text=True,timeout=24,check=False)
 if p.returncode:raise AssertionError("WA34 SQL error: "+p.stderr[-700:])
 return p.stdout.strip()
def expect(sql,want):
 got=query(sql)
 assert got==want,(sql,got,want)
def consume(case,nonce,event,kind="SENT_REPORTED",override=None,
 issue=None,expiry=None,at=None):
 value=list(items[case])
 if override:
  for position,v in override.items():value[position]=v
 app,waba,phone,wamid,recipient,revision=value
 i=now if issue is None else issue
 x=now+60000 if expiry is None else expiry
 t=now if at is None else at
 return ("SELECT wa34_lab.consume_fixture("
   f"'{nonce}','{app}','{waba}','{phone}','{wamid}',"
   f"'{recipient}','{event}','{kind}',{revision},{i},{x},{t})")
def mark(n):print(f"WA34-{n:02} PASS",flush=True)
def wait_for(check,label):
 until=time.monotonic()+12
 while time.monotonic()<until:
  if check():return
  time.sleep(.07)
 raise AssertionError("WA34 PG17 lock did not occur: "+label)
def hold(app,statement):
 p=subprocess.Popen(psql,env={**env,"PGAPPNAME":app},
  stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
  text=True,bufsize=1)
 assert p.stdin is not None
 p.stdin.write("BEGIN;\n"+statement+";\n");p.stdin.flush()
 wait_for(lambda:query("SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
  f"WHERE application_name='{app}' AND state='idle in transaction')")=="t",app)
 return p
def blocked(app,statement):
 p=subprocess.Popen(psql+["-c",statement],env={**env,"PGAPPNAME":app},
  stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 wait_for(lambda:query("SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
  f"WHERE application_name='{app}' AND cardinality(pg_blocking_pids(pid))>0)")=="t",app)
 return p
def finish(p,commit=True):
 assert p.stdin is not None
 p.stdin.write("COMMIT;\n" if commit else "ROLLBACK;\n")
 p.stdin.flush();p.stdin.close()
 code=p.wait(timeout=12)
 out=p.stdout.read().strip() if p.stdout else ""
 err=p.stderr.read().strip() if p.stderr else ""
 assert code==0,err[-650:]
 return out
def finish_blocked(p):
 out,err=p.communicate(timeout=12)
 assert p.returncode==0,err[-650:]
 return out.strip()

expect("SELECT count(*) FROM wa34_lab.consumed_nonces","0")
mark(1)
expect("SELECT state FROM wa29_lab.claims WHERE case_ref='case31_late'",
 "LAB_INVALIDATED")
mark(2)
expect(consume('late','N_LATE_1','WA34_EVENT_LATE'),
 "LAB_NONCE_CONSUMED_ARCHIVED_NO_SEND")
expect("SELECT after_invalidation FROM wa33_lab.events WHERE event_ref='WA34_EVENT_LATE'","t")
mark(3)
expect(consume('late','N_LATE_1','WA34_EVENT_LATE'),
 "LAB_NONCE_CONSUMED_NO_RETRY")
mark(4)
expect(consume('late','N_LATE_2','WA34_EVENT_LATE'),
 "LAB_NONCE_CONSUMED_REPLAY_NO_SEND")
expect("SELECT count(*) FROM wa33_lab.events WHERE event_ref='WA34_EVENT_LATE'","1")
mark(5)
expect("SELECT consumption FROM wa34_lab.consumed_nonces WHERE nonce_ref='N_LATE_2'",
 "LAB_REPLAY")
mark(6)
expect(consume('late','N_EXPIRED','EVENT_EXPIRED',at=now+60000),"LAB_DENIED")
expect(consume('late','N_EARLY','EVENT_EARLY',at=now-1),"LAB_DENIED")
mark(7)
expect(consume('late','N_BAD_TTL','EVENT_TTL',expiry=now+120001),"LAB_DENIED")
expect(consume('late','N_BAD_INVERSE','EVENT_INVERSE',expiry=now),"LAB_DENIED")
mark(8)
expect(consume('late','N..UNSAFE/','EVENT_UNSAFE'),"LAB_DENIED")
expect("SELECT count(*) FROM wa34_lab.consumed_nonces WHERE nonce_ref LIKE 'N_BAD%'","0")
mark(9)
expect(consume('late','N_WRONG_PERSON','EVENT_WRONG_PERSON',override={4:'5581990000000'}),
 "LAB_DENIED")
mark(10)
expect(consume('late','N_WRONG_WABA','EVENT_WRONG_WABA',override={1:'222222'}),
 "LAB_DENIED")
expect(consume('late','N_WRONG_APP','EVENT_WRONG_APP',override={0:'APP_B'}),
 "LAB_DENIED")
mark(11)
expect(consume('late','N_WRONG_VERSION','EVENT_WRONG_VERSION',override={5:8}),
 "LAB_DENIED")
mark(12)
expect(consume('missing','N_NO_CLAIM','EVENT_NO_CLAIM'),"LAB_DENIED")
expect("SELECT count(*) FROM wa34_lab.consumed_nonces WHERE nonce_ref='N_NO_CLAIM'","0")
mark(13)
expect(consume('b','N_B_1','EVENT_B'),"LAB_NONCE_CONSUMED_ARCHIVED_NO_SEND")
mark(14)
expect(consume('b','N_LATE_1','EVENT_CROSS_TENANT'),
 "LAB_NONCE_CONSUMED_NO_RETRY")
expect("SELECT count(*) FROM wa33_lab.events WHERE event_ref='EVENT_CROSS_TENANT'","0")
mark(15)

# Rollback must atomically discard both nonce and forensic event.
held=hold("wa34_rollback",consume('late','N_ROLLBACK','EVENT_ROLLBACK'))
assert finish(held,False)=="LAB_NONCE_CONSUMED_ARCHIVED_NO_SEND"
expect("SELECT count(*) FROM wa34_lab.consumed_nonces WHERE nonce_ref='N_ROLLBACK'","0")
expect("SELECT count(*) FROM wa33_lab.events WHERE event_ref='EVENT_ROLLBACK'","0")
mark(16)

# Concurrency 1: same nonce/event, two sessions, unique nonce prevents retry.
first=hold("wa34_first_nonce",consume('active','N_RACE_1','EVENT_RACE_1'))
mark(17)
second=blocked("wa34_duplicate_nonce",consume('active','N_RACE_1','EVENT_RACE_1'))
mark(18)
assert finish(first)=="LAB_NONCE_CONSUMED_ARCHIVED_NO_SEND"
assert finish_blocked(second)=="LAB_NONCE_CONSUMED_NO_RETRY"
expect("SELECT count(*) FROM wa33_lab.events WHERE event_ref='EVENT_RACE_1'","1")
mark(19)

# Concurrency 2: revoke wins; historical event persists only as late.
rev=hold("wa34_revoke_first",
 "SELECT wa29_lab.revoke_fixture('shop_A','case31_conflict','OPT_OUT')")
mark(20)
late=blocked("wa34_late_second",consume('active','N_RACE_2','EVENT_RACE_2'))
mark(21)
assert finish(rev)=="LAB_REVOKED"
assert finish_blocked(late)=="LAB_NONCE_CONSUMED_ARCHIVED_NO_SEND"
expect("SELECT after_invalidation FROM wa33_lab.events WHERE event_ref='EVENT_RACE_2'","t")
expect("SELECT state FROM wa29_lab.claims WHERE case_ref='case31_conflict'",
 "LAB_INVALIDATED")
mark(22)

# Concurrency 3: retarget sender's recipient/revision first, old ticket denied.
retarget=hold("wa34_b_binding_update",
 "SELECT wa33_lab.change_binding_fixture('shop_B','case31_b','5581900000033')")
mark(23)
stale=blocked("wa34_stale_handoff",consume('b','N_STALE','EVENT_STALE'))
mark(24)
assert finish(retarget)=="LAB_BINDING_CHANGED"
assert finish_blocked(stale)=="LAB_DENIED"
expect("SELECT count(*) FROM wa34_lab.consumed_nonces WHERE nonce_ref='N_STALE'","0")
mark(25)
expect(consume('b','N_NEW_B','EVENT_NEW_B',override={4:'5581900000033',5:3}),
 "LAB_NONCE_CONSUMED_ARCHIVED_NO_SEND")
mark(26)

# No internal result produces Graph, ACK, commercial or cadence authority.
expect("SELECT count(*) FROM wa34_lab.consumed_nonces WHERE send_authorized OR "
 "production_authorized OR ack_allowed OR retry_external OR "
 "case_transition_authorized OR definitive_failure_count_increment","0")
mark(27)
expect("SELECT count(*) FROM wa33_lab.events WHERE send_authorized OR "
 "production_authorized OR ack_allowed OR definitive_failure_count_increment","0")
mark(28)
expect("SELECT count(*) FROM wa34_lab.consumed_nonces WHERE nonce_ref='N_RACE_1'","1")
expect("SELECT count(*) FROM wa34_lab.consumed_nonces WHERE nonce_ref='N_LATE_2'","1")
mark(29)
print("PASS WA34: 29 PG17 checks, 3 physical blocked races, no S0 service identity",flush=True)
