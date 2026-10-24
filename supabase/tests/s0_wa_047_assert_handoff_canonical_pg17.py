#!/usr/bin/env python3
"""WA43 laboratory-only, Python->PG17 canonical bytes and MAC parity.
Tests the *S0/044* format, NOT the incompatible WA34 JSON envelope.
No Meta network, actual service login, hosted Supabase, or live keys.
"""
import hashlib
import hmac
import json
import os
import re
import subprocess
import time
import uuid
from urllib.parse import urlsplit

dsn = os.getenv("PRUMO_TEST_DATABASE_URL", "")
u = urlsplit(dsn)
if not (u.scheme == "postgresql" and u.hostname == "127.0.0.1"
        and u.port == 5432 and u.username == "postgres"
        and u.path == "/prumo_s0_test_ci" and not u.query and not u.fragment):
    raise SystemExit("WA43 refuses non-local throwaway PG17 database")
for x in ("PGHOST","PGHOSTADDR","PGPORT","PGDATABASE","PGUSER",
          "PGSERVICE","PGSERVICEFILE","PGOPTIONS","PGSSLMODE",
          "PGSSLCERT","PGSSLKEY","PGSSLROOTCERT"):
    if os.getenv(x):
        raise SystemExit("WA43 refuses libpq override: " + x)
env = {"PATH":os.getenv("PATH","/usr/bin:/bin"),
       "HOME":os.getenv("HOME","/tmp"),"LC_ALL":"C",
       "PGCONNECT_TIMEOUT":"5","PGAPPNAME":"wa43_lab_wire"}
def sql(statement):
    p = subprocess.run(["psql","-X","-qAt","-v","ON_ERROR_STOP=1",
       "-v","VERBOSITY=verbose",dsn,"-c",statement],env=env,
       capture_output=True,text=True,timeout=15)
    return p.returncode,p.stdout.strip(),p.stderr
def ok(statement):
    code,out,err=sql(statement)
    if code != 0:raise AssertionError(err[-1000:])
    return out
def denied(statement):
    code,out,err=sql(statement)
    if code == 0 or "42501" not in err:
        raise AssertionError(("unexpected authorization",out,err[-700:]))
def quote(x):
    s=str(x)
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}",s):
        raise AssertionError("WA43 unsafe SQL fixture value")
    return "'"+s+"'"
def mark(n):
    print("WA43-%02d PASS" % n,flush=True)

key="f7700000-0000-4000-8000-000000000001"
secret=b"K"*48
base=[
 key,"12346000002","22346000002","32346000002",
 "f7300000-0000-4000-8000-000000000002",
 "f7400000-0000-4000-8000-000000000002",
 "ATTEMPT_B","CORR_B","5581900000000","wamid.WA40.SHARED",
 "EVT_WA43_ACCEPT","delivered","d"*64,str(int(time.time())),str(uuid.uuid4())
]
def material(values):
    return "|".join(["prumo-meta-handoff-lab-v1","FORENSIC_APPEND_ONLY"]+values)
def db_material(values):
    return ok("SELECT prumo_private.meta_material_handoff_fixture_s0("+
      ",".join(map(quote,values))+");")
def make_call(values,mac):
    return ("SET ROLE prumo_s0_meta_ingress_lab; "
       "SELECT prumo_private.meta_arquivar_handoff_assinado_fixture_s0("+
       ",".join(map(quote,values+[mac]))+");")
def signer(values):
    return hmac.new(secret,material(values).encode("utf-8"),
                    hashlib.sha256).hexdigest()

assert material(base)==db_material(base)
mark(1)
assert material(base).startswith("prumo-meta-handoff-lab-v1|FORENSIC_APPEND_ONLY|")
mark(2)
assert len(material(base).split("|"))==17
mark(3)
assert signer(base)==hmac.new(secret,db_material(base).encode("utf-8"),
                               hashlib.sha256).hexdigest()
mark(4)
# Every field, including purpose-bound scope and replay nonce, contributes
# independently to signed material; no two changed fixtures collide.
mutations={
 0:"f7700000-0000-4000-8000-000000000002",
 1:"12346000009", 2:"22346000009", 3:"32346000009",
 4:"f7300000-0000-4000-8000-000000000009",
 5:"f7400000-0000-4000-8000-000000000009",
 6:"ATTEMPT_X",7:"CORR_X",8:"5581999999999",
 9:"wamid.WA40.MUTATED",10:"EVT_WA43_OTHER",
 11:"failed",12:"e"*64,13:str(int(base[13])+1),
 14:str(uuid.uuid4())
}
seen={material(base)}
for idx,changed in mutations.items():
    variant=base.copy()
    variant[idx]=changed
    assert material(variant)==db_material(variant),(idx,variant)
    assert material(variant) not in seen,idx
    assert signer(variant)!=signer(base),idx
    seen.add(material(variant))
assert len(seen)==16
mark(5)
assert all("|" not in field for field in base)
mark(6)

# In contrast WA34 HMAC is SHA256 over JSON encoded ordered values. The
# contracts must not be silently treated as equivalent.
wa34_style=json.dumps(base,separators=(",",":"),ensure_ascii=False).encode()
assert wa34_style!=material(base).encode()
assert hmac.new(secret,wa34_style,hashlib.sha256).hexdigest()!=signer(base)
mark(7)

# Distinct artificial key generated for THIS PG17 session only (never GitHub
# Secrets). The test runs after WA40/42 which revoked the older sample keys.
ok("INSERT INTO prumo_private.meta_servico_chaves_fixture_s0 "
   "(chave_id,app_technical_ref,segredo,valido_desde,valido_ate,ativo) VALUES ("+
   quote(key)+",'12346000002',"+
   "pg_catalog.decode(pg_catalog.repeat('4b',48),'hex'),"
   "pg_catalog.clock_timestamp()-interval '60 seconds',"
   "pg_catalog.clock_timestamp()+interval '30 minutes',true);")
mark(8)

signature=signer(base)
wire=json.loads(ok(make_call(base,signature)))
assert wire["outcome"]=="LAB_OBSERVED_UNVERIFIED",wire
assert wire["handoff_contract"]=="WA40_PG17_LAB_ONLY"
mark(9)

for flag in ("ack_allowed","send_authorized","retry_external",
 "production_authorized","delivery_confirmed","case_transition_authorized",
 "definitive_failure_count_increment","service_authenticated",
 "s0_production_authorized"):
    assert wire[flag] is False,flag
mark(10)

# A one-bit semantic mutation signed under the original material is denied.
tampered=base.copy()
tampered[10]="EVT_WA43_TAMPER"
denied(make_call(tampered,signature))
mark(11)
assert ok("SELECT count(*) FROM prumo_private.meta_status_forense_fixture_s0 "
          "WHERE event_ref='EVT_WA43_TAMPER'")=="0"
mark(12)

# Same valid MAC + same nonce is never processed twice.
denied(make_call(base,signature))
mark(13)
assert ok("SELECT count(*) FROM prumo_private.meta_servico_nonces_fixture_s0 "
          "WHERE nonce="+quote(base[-1]))=="1"
mark(14)
assert ok("SELECT count(*) FROM prumo_private.meta_status_forense_fixture_s0 "
          "WHERE event_ref='EVT_WA43_ACCEPT'")=="1"
mark(15)

# JSON/WA34 MAC cannot authenticate a S0/044 packet.
other=base.copy()
other[10]="EVT_WA43_JSON"
wrong=hmac.new(secret,json.dumps(other,separators=(",",":")).encode(),
               hashlib.sha256).hexdigest()
denied(make_call(other,wrong))
mark(16)
assert ok("SELECT count(*) FROM prumo_private.meta_status_forense_fixture_s0 "
          "WHERE event_ref='EVT_WA43_JSON'")=="0"
mark(17)

assert ok("SELECT count(*) FROM prumo_private.meta_status_forense_fixture_s0 "
 "WHERE ack_allowed OR send_authorized OR retry_external OR "
 "production_authorized OR delivery_confirmed OR "
 "case_transition_authorized OR definitive_failure_count_increment")=="0"
mark(18)
print("WA43 18/18 lab canonical byte/HMAC checks; WA34 remains incompatible",
      flush=True)
