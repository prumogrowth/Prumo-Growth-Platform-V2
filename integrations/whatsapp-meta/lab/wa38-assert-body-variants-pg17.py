#!/usr/bin/env python3
"""WA38: PG17 real lock races for forensic SHA256 body variants only.
NO Meta secret / HMAC verification, S0 authenticated service, ACK, Graph,
provider delivery proof, commercial transition, retention or production role.
"""
import json
import os
import subprocess
import time
from urllib.parse import urlsplit

dsn=os.environ.get("PRUMO_TEST_DATABASE_URL","")
u=urlsplit(dsn)
if not(u.scheme=="postgresql" and u.hostname=="127.0.0.1" and
 u.port==5432 and u.username=="postgres" and u.path=="/prumo_s0_test_ci"
 and not u.query and not u.fragment):
 raise SystemExit("WA38 refuses all except local disposable PG17")
for key in ("PGHOST","PGHOSTADDR","PGPORT","PGDATABASE","PGUSER",
 "PGSERVICE","PGSERVICEFILE","PGOPTIONS","PGSSLMODE",
 "PGSSLCERT","PGSSLKEY","PGSSLROOTCERT"):
 if os.environ.get(key):
  raise SystemExit("WA38 refuses libpq routing override "+key)
env={"PATH":os.getenv("PATH","/usr/bin:/bin"),
     "HOME":os.getenv("HOME","/tmp"),"LC_ALL":"C","PGCONNECT_TIMEOUT":"5"}
psql=["psql","-X","-qAt","-v","ON_ERROR_STOP=1",dsn]
A=("APP_A","111111","1234567890","wamid.WA33_HIST","5581900000000",1)
B=("APP_B","222222","9876543210","wamid.WA33_B","5581900000033",3)
M=("APP_A","111111","1234567890","wamid.WA33_MISSING_CLAIM","5581900000000",1)
samples=[]
def run(sql,app="wa38_read"):
 p=subprocess.run(psql+["-c",sql],env={**env,"PGAPPNAME":app},
   capture_output=True,text=True,timeout=24,check=False)
 if p.returncode:raise AssertionError("WA38 SQL failure: "+p.stderr[-550:])
 return p.stdout.strip()
def expect(sql,want):
 got=run(sql)
 assert got==want,(sql,got,want)
def q(s):
 assert isinstance(s,str) and s and "'" not in s and "\\" not in s,(s,)
 return "'"+s+"'"
def append(scope,event,body="a",kind="DELIVERED_REPORTED",change=None):
 parts=list(scope)
 if change:
  for i,val in change.items():parts[i]=val
 app,waba,phone,wamid,recipient,revision=parts
 values=list(map(q,[app,waba,phone,wamid,recipient,event,kind]))
 digest=body*64 if len(body)==1 else body
 return "SELECT wa38_lab.archive_fixture("+",".join(values)+","+q(digest)+
   f",{revision})"
def read(shop,case,attempt,event,label=None,want=None):
 s="SELECT wa38_lab.read_fixture("+",".join(map(q,(shop,case,attempt,event)))+")"
 value=json.loads(run(s))
 assert len(value)==8,(case,value)
 for k in ("retry_external","send_authorized","ack_allowed",
  "production_authorized","delivery_confirmed",
  "definitive_failure_count_increment","case_transition_authorized"):
  assert value[k] is False,(case,k,value)
 if want:assert value["outcome"]==want,(case,value,want)
 if label:samples.append({"label":label,"snapshot":value})
 return value["outcome"]
def mark(n):print(f"WA38-{n:02} PASS",flush=True)
def until(check,label):
 end=time.monotonic()+12
 while time.monotonic()<end:
  if check():return
  time.sleep(.06)
 raise AssertionError("WA38 missing observed PG blocking: "+label)
def hold(app,statement):
 p=subprocess.Popen(psql,env={**env,"PGAPPNAME":app},
   stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
   text=True,bufsize=1)
 assert p.stdin is not None
 p.stdin.write("BEGIN;\n"+statement+";\n");p.stdin.flush()
 until(lambda:run("SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
  f"WHERE application_name='{app}' AND state='idle in transaction')")=="t",app)
 return p
def blocked(app,statement):
 p=subprocess.Popen(psql+["-c",statement],env={**env,"PGAPPNAME":app},
  stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
  text=True)
 until(lambda:run("SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
  f"WHERE application_name='{app}' AND cardinality(pg_blocking_pids(pid))>0)")=="t",app)
 return p
def finish(p,commit=True):
 assert p.stdin is not None
 p.stdin.write("COMMIT;\n" if commit else "ROLLBACK;\n")
 p.stdin.flush();p.stdin.close()
 rc=p.wait(timeout=12)
 result=p.stdout.read().strip() if p.stdout else ""
 err=p.stderr.read().strip() if p.stderr else ""
 assert rc==0,err[-550:]
 return result
def finish_blocked(p):
 result,err=p.communicate(timeout=12)
 assert p.returncode==0,err[-550:]
 return result.strip()

expect("SELECT count(*) FROM wa38_lab.observations","0")
mark(1)
read("shop_A","case31_hist","attempt31_hist","EVT_COLLIDE",
  label="none",want="LAB_NONE")
mark(2)
expect("SELECT state FROM wa29_lab.claims WHERE shop_ref='shop_A' AND "
 "case_ref='case31_hist'","LAB_INVALIDATED")
expect(append(A,"EVT_COLLIDE","a"),"LAB_LATE_OBSERVATION_UNVERIFIED")
mark(3)
read("shop_A","case31_hist","attempt31_hist","EVT_COLLIDE",
  label="late",want="LAB_LATE_UNVERIFIED")
mark(4)
expect(append(A,"EVT_COLLIDE","a"),"LAB_EXACT_BODY_REPLAY_NO_RETRY")
expect("SELECT count(*) FROM wa38_lab.observations WHERE event_ref='EVT_COLLIDE'","1")
mark(5)
expect(append(A,"EVT_COLLIDE","b"),"LAB_BODY_VARIANT_QUARANTINED")
expect("SELECT count(*) FROM wa38_lab.observations WHERE event_ref='EVT_COLLIDE'","2")
mark(6)
read("shop_A","case31_hist","attempt31_hist","EVT_COLLIDE",
  label="variant_hold",want="LAB_MULTIPLE_OR_CONFLICT_QUARANTINED")
mark(7)
expect(append(A,"EVT_COLLIDE","b"),"LAB_EXACT_BODY_REPLAY_NO_RETRY")
mark(8)
expect(append(A,"EVT_COLLIDE","b","READ_REPORTED"),
       "LAB_KIND_CONFLICT_QUARANTINED")
expect("SELECT count(*) FROM wa38_lab.observations WHERE event_ref='EVT_COLLIDE'","2")
expect("SELECT reason FROM wa38_lab.quarantine WHERE event_ref='EVT_COLLIDE'",
       "LAB_SAME_BODY_KIND_CONFLICT")
mark(9)
read("shop_A","case31_hist","attempt31_hist","EVT_COLLIDE",
  label="kind_conflict",want="LAB_MULTIPLE_OR_CONFLICT_QUARANTINED")
mark(10)
expect(append(A,"EVT_BAD_HASH",body="f"*63),"LAB_DENIED")
expect(append(A,"EVT_UPPER_HASH",body="F"),"LAB_DENIED")
mark(11)
expect(append(A,"EVT_BAD_KIND",body="d",kind="GRAPH_SENT"),"LAB_DENIED")
expect(append(A,"EVT_BAD_EVENT",body="d",kind="DELIVERED_REPORTED",
 change={3:"wamid.UNRELATED"}),"LAB_DENIED")
mark(12)
expect(append(A,"EVT_WRONG_RECIPIENT",body="d",change={4:"5581990000000"}),"LAB_DENIED")
mark(13)
expect(append(A,"EVT_WRONG_APP",body="d",change={0:"APP_B"}),"LAB_DENIED")
expect(append(A,"EVT_WRONG_WABA",body="d",change={1:"222222"}),"LAB_DENIED")
mark(14)
expect(append(A,"EVT_WRONG_REV",body="d",change={5:2}),"LAB_DENIED")
mark(15)
expect(append(M,"EVT_NO_CLAIM",body="d"),"LAB_DENIED")
mark(16)
expect(append(B,"EVT_B_ACT",body="c"),"LAB_FIRST_OBSERVATION_UNVERIFIED")
read("shop_B","case31_b","attempt31_b","EVT_B_ACT",
 label="active_b",want="LAB_SINGLE_UNVERIFIED")
mark(17)
expect(append(B,"EVT_B_ACT",body="d"),"LAB_BODY_VARIANT_QUARANTINED")
read("shop_B","case31_b","attempt31_b","EVT_B_ACT",
 label="other_tenant_hold",want="LAB_MULTIPLE_OR_CONFLICT_QUARANTINED")
mark(18)
expect(append(B,"EVT_BAD_SCOPE",body="d",change={0:"APP_A"}),"LAB_DENIED")
mark(19)
expect(append(A,"EVT_SHARED",body="a"),"LAB_LATE_OBSERVATION_UNVERIFIED")
expect(append(B,"EVT_SHARED",body="a"),"LAB_FIRST_OBSERVATION_UNVERIFIED")
expect("SELECT count(*) FROM wa38_lab.observations WHERE event_ref='EVT_SHARED'","2")
expect("SELECT count(*) FROM wa38_lab.quarantine WHERE event_ref='EVT_SHARED'","0")
mark(20)
expect("SELECT count(*) FROM wa33_lab.events WHERE event_ref='EVT_COLLIDE'","0")
expect("SELECT count(*) FROM wa34_lab.consumed_nonces WHERE event_ref='EVT_COLLIDE'","0")
mark(21)
rolled=hold("wa38_rollback",append(A,"EVT_ROLLBACK","e"))
assert finish(rolled,False)=="LAB_LATE_OBSERVATION_UNVERIFIED"
expect("SELECT count(*) FROM wa38_lab.observations WHERE event_ref='EVT_ROLLBACK'","0")
mark(22)
first=hold("wa38_exact_first",append(A,"EVT_RACE_REPLAY","e"))
mark(23)
second=blocked("wa38_exact_second",append(A,"EVT_RACE_REPLAY","e"))
mark(24)
assert finish(first)=="LAB_LATE_OBSERVATION_UNVERIFIED"
assert finish_blocked(second)=="LAB_EXACT_BODY_REPLAY_NO_RETRY"
expect("SELECT count(*) FROM wa38_lab.observations WHERE event_ref='EVT_RACE_REPLAY'","1")
mark(25)
first=hold("wa38_variant_first",append(A,"EVT_RACE_VARIANT","e"))
mark(26)
second=blocked("wa38_variant_second",append(A,"EVT_RACE_VARIANT","f"))
mark(27)
assert finish(first)=="LAB_LATE_OBSERVATION_UNVERIFIED"
assert finish_blocked(second)=="LAB_BODY_VARIANT_QUARANTINED"
expect("SELECT count(*) FROM wa38_lab.observations WHERE event_ref='EVT_RACE_VARIANT'","2")
expect("SELECT count(*) FROM wa38_lab.quarantine WHERE event_ref='EVT_RACE_VARIANT'","1")
mark(28)
rev=hold("wa38_revoke_b_first",
 "SELECT wa29_lab.revoke_fixture('shop_B','case31_b','OPT_OUT')")
mark(29)
after=blocked("wa38_archive_b_late",append(B,"EVT_B_AFTER_REVOKE","e"))
mark(30)
assert finish(rev)=="LAB_REVOKED"
assert finish_blocked(after)=="LAB_LATE_OBSERVATION_UNVERIFIED"
read("shop_B","case31_b","attempt31_b","EVT_B_AFTER_REVOKE",
 label="late_b",want="LAB_LATE_UNVERIFIED")
expect("SELECT state FROM wa29_lab.claims WHERE shop_ref='shop_B' AND "
 "case_ref='case31_b'","LAB_INVALIDATED")
mark(31)
expect("SELECT count(*) FROM wa38_lab.observations WHERE send_authorized OR "
 "retry_external OR ack_allowed OR production_authorized OR delivery_confirmed OR "
 "definitive_failure_count_increment OR case_transition_authorized","0")
expect("SELECT count(*) FROM wa38_lab.quarantine WHERE reason NOT IN "
 "('LAB_DIFFERENT_BODY_SAME_EVENT','LAB_SAME_BODY_KIND_CONFLICT')","0")
mark(32)
runner=os.path.join(os.path.dirname(__file__),"wa38-assert-db-readbacks.ts")
data="\n".join(json.dumps(x,sort_keys=True) for x in samples)+"\n"
p=subprocess.run(["node","--experimental-strip-types",runner],
 input=data,capture_output=True,text=True,timeout=15,check=False,
 env={**env,"NODE_OPTIONS":"","NODE_PATH":""})
assert p.returncode==0,p.stderr[-550:]
assert p.stdout.strip()=="WA38-TSDB PASS: 7 physical PG17 aggregates deny all authority",p.stdout
mark(33)
print("PASS WA38: 33 PG17 checks, three observed PG lock races, seven typed readbacks; no Meta",flush=True)
