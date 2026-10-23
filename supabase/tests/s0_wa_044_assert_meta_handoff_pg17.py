#!/usr/bin/env python3
"""WA40: DB HMAC/nonce/forensics under a synthetic NOLOGIN service role.
Never uses Meta, Supabase hosted, live secrets, real GoTrue or Graph.
"""
import concurrent.futures
import hashlib
import hmac
import json
import os
import re
import subprocess
import time
import uuid
from urllib.parse import urlsplit

dsn=os.environ.get("PRUMO_TEST_DATABASE_URL","")
u=urlsplit(dsn)
if not (u.scheme=="postgresql" and u.hostname=="127.0.0.1" and
 u.port==5432 and u.username=="postgres" and u.path=="/prumo_s0_test_ci" and
 not u.query and not u.fragment):
 raise SystemExit("WA40: refuses non-local throwaway PG17 target")
for name in ("PGHOST","PGHOSTADDR","PGPORT","PGDATABASE","PGUSER",
             "PGSERVICE","PGSERVICEFILE","PGOPTIONS","PGSSLMODE",
             "PGSSLCERT","PGSSLKEY","PGSSLROOTCERT"):
 if os.environ.get(name):raise SystemExit("WA40: libpq override forbidden "+name)
env={"PATH":os.getenv("PATH","/usr/bin:/bin"),"HOME":os.getenv("HOME","/tmp"),
     "LC_ALL":"C","PGCONNECT_TIMEOUT":"5","PGAPPNAME":"wa40_pg17_handoff"}
def execsql(sql):
 return subprocess.run(["psql","-X","-qAt","-v","ON_ERROR_STOP=1",
                        "-v","VERBOSITY=verbose",dsn,"-c",sql],env=env,
                       capture_output=True,text=True,timeout=18,check=False)
def query(sql):
 p=execsql(sql)
 if p.returncode:raise AssertionError("WA40 query failed: "+p.stderr[-900:])
 return p.stdout.strip()
def denied(sql,sqlstate="42501"):
 p=execsql(sql)
 assert p.returncode!=0,(sql,p.stdout,p.stderr[-400:])
 assert sqlstate in p.stderr,(sql,p.stderr[-600:])
def mark(n):print(f"WA40-{n:02} PASS",flush=True)
a=dict(app="12346000001",waba="22346000001",phone="32346000001",
 canal="f7300000-0000-4000-8000-000000000001",
 intent="f7400000-0000-4000-8000-000000000001",
 attempt="ATTEMPT_A",correlation="CORR_A",recipient="5581900000000",
 wamid="wamid.WA40.SHARED",
 key="f7500000-0000-4000-8000-000000000001",secret=b"S"*48)
b=dict(app="12346000002",waba="22346000002",phone="32346000002",
 canal="f7300000-0000-4000-8000-000000000002",
 intent="f7400000-0000-4000-8000-000000000002",
 attempt="ATTEMPT_B",correlation="CORR_B",recipient="5581900000000",
 wamid="wamid.WA40.SHARED",
 key="f7500000-0000-4000-8000-000000000002",secret=b"T"*48)
def quoted(value):
 assert re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}",str(value))
 return "'"+str(value)+"'"
def packet(scope=a,event="EVT_A",kind="delivered",hashval="a"*64,
           issued=None,nonce=None,key=None,secret=None,**changes):
 s={**scope,**changes}
 t=int(time.time()) if issued is None else issued
 n=str(uuid.uuid4()) if nonce is None else nonce
 kid=s["key"] if key is None else key
 secret=s["secret"] if secret is None else secret
 fields=["prumo-meta-handoff-lab-v1","FORENSIC_APPEND_ONLY",kid,
 s["app"],s["waba"],s["phone"],s["canal"],s["intent"],s["attempt"],
 s["correlation"],s["recipient"],s["wamid"],event,kind,hashval,str(t),n]
 mac=hmac.new(secret,"|".join(fields).encode(),hashlib.sha256).hexdigest()
 args=[kid,s["app"],s["waba"],s["phone"],s["canal"],s["intent"],
       s["attempt"],s["correlation"],s["recipient"],s["wamid"],
       event,kind,hashval,str(t),n,mac]
 return args
def invocation(args,role=True,rollback=False):
 expression=("SELECT prumo_private.meta_arquivar_handoff_assinado_fixture_s0("+
     ",".join(map(quoted,args))+");")
 if role:expression="SET ROLE prumo_s0_meta_ingress_lab; "+expression
 if rollback:expression="BEGIN; "+expression+" ROLLBACK;"
 return expression
def used(nonce):
 return query("SELECT count(*) FROM prumo_private.meta_servico_nonces_fixture_s0 "
  "WHERE nonce="+quoted(nonce))=="1"
def outcome(args):
 x=query(invocation(args))
 try:return json.loads(x)
 except Exception:raise AssertionError(("invalid response",x))
def rowcount(event):
 return int(query("SELECT count(*) FROM prumo_private.meta_status_forense_fixture_s0 "
  "WHERE event_ref="+quoted(event)))

assert query("SELECT rolcanlogin::text||','||rolbypassrls::text FROM pg_roles "
 "WHERE rolname='prumo_s0_meta_ingress_lab'")=="false,false"
mark(1)
denied("SET ROLE prumo_s0_meta_ingress_lab; "
 "SELECT * FROM prumo_private.meta_servico_chaves_fixture_s0")
mark(2)
denied(invocation(packet(),role=False))
mark(3)
first=packet()
result=outcome(first)
assert result["outcome"]=="LAB_OBSERVED_UNVERIFIED",result
mark(4)
for flag in ("ack_allowed","send_authorized","retry_external",
 "production_authorized","delivery_confirmed","case_transition_authorized",
 "definitive_failure_count_increment","service_authenticated",
 "s0_production_authorized"):
 assert result[flag] is False,(flag,result)
mark(5)
assert used(first[-2])
mark(6)
assert rowcount("EVT_A")==1
mark(7)
denied(invocation(first))
mark(8)
assert outcome(packet())["outcome"]=="LAB_EXACT_BODY_REPLAY"
mark(9)
badmac=packet(event="EVT_BADMAC")
badmac[-1]="0"*64
denied(invocation(badmac))
assert not used(badmac[-2])
mark(10)
changed=packet(event="EVT_TAMPER");changed[-6]="EVT_ATTACKER"
denied(invocation(changed))
mark(11)
denied(invocation(packet(event="EVT_OLD",issued=int(time.time())-50)))
mark(12)
denied(invocation(packet(event="EVT_FUTURE",issued=int(time.time())+10)))
mark(13)
denied(invocation(packet(b,event="EVT_WRONG_KEY",key=a["key"],secret=a["secret"])))
mark(14)
denied(invocation(packet(a,event="EVT_CROSS",canal=b["canal"],intent=b["intent"])))
mark(15)
denied(invocation(packet(a,event="EVT_WRONG_RECIPIENT",recipient="5581999999999")))
mark(16)
assert outcome(packet(b,event="EVT_B"))["outcome"]=="LAB_OBSERVED_UNVERIFIED"
assert rowcount("EVT_B")==1
mark(17)
query("UPDATE prumo_private.outbox_intencoes_s0 SET estado='CANCELADA' "
 "WHERE id="+quoted(a["intent"]))
assert outcome(packet(a,event="EVT_LATE",kind="read"))["outcome"]=="LAB_LATE_UNVERIFIED"
mark(18)
assert outcome(packet(a,event="EVT_A",hashval="b"*64))[
 "outcome"]=="LAB_BODY_VARIANT_QUARANTINED"
mark(19)
race=packet(b,event="EVT_RACE")
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 results=list(pool.map(execsql,[invocation(race),invocation(race)]))
assert sum(x.returncode==0 for x in results)==1,[(x.stdout,x.stderr[-200:]) for x in results]
assert sum(x.returncode!=0 and "42501" in x.stderr for x in results)==1
assert rowcount("EVT_RACE")==1
mark(20)
reverted=packet(b,event="EVT_ROLLBACK")
p=execsql(invocation(reverted,rollback=True))
assert p.returncode==0,p.stderr[-400:]
assert not used(reverted[-2]) and rowcount("EVT_ROLLBACK")==0
mark(21)
query("UPDATE prumo_private.meta_servico_chaves_fixture_s0 SET ativo=false "
 "WHERE chave_id="+quoted(a["key"]))
denied(invocation(packet(a,event="EVT_REVOKED")))
mark(22)
for role in ("anon","authenticated","service_role","prumo_s0_gateway",
             "prumo_s0_signer","prumo_s0_signed_executor"):
 priv=query("SELECT has_function_privilege("+quoted(role)+","
  "'prumo_private.meta_arquivar_handoff_assinado_fixture_s0("
  "uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,"
  "bigint,uuid,text)','EXECUTE')")
 assert priv=="f",(role,priv)
mark(23)
denied("SET ROLE prumo_s0_meta_ingress_lab; "
 "SELECT * FROM prumo_private.meta_status_forense_fixture_s0")
mark(24)
assert query("SELECT count(*) FROM prumo_private.meta_status_forense_fixture_s0 "
 "WHERE ack_allowed OR send_authorized OR retry_external OR "
 "production_authorized OR delivery_confirmed OR "
 "case_transition_authorized OR definitive_failure_count_increment")=="0"
mark(25)
print("WA40: 25/25 synthetic signed M2M PG17 checks; ZERO production authorization",flush=True)
