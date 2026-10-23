#!/usr/bin/env python3
"""WA36: PG17 NOLOGIN privilege negatives only; no real S0 or service auth."""
import os
import subprocess
from urllib.parse import urlsplit

dsn=os.environ.get("PRUMO_TEST_DATABASE_URL","")
u=urlsplit(dsn)
if not (u.scheme=="postgresql" and u.hostname=="127.0.0.1" and
 u.port==5432 and u.username=="postgres" and u.path=="/prumo_s0_test_ci" and
 not u.query and not u.fragment):
 raise SystemExit("WA36 refuses non-disposable PG17 target")
for name in ("PGHOST","PGHOSTADDR","PGPORT","PGDATABASE","PGUSER",
             "PGSERVICE","PGSERVICEFILE","PGOPTIONS","PGSSLMODE",
             "PGSSLCERT","PGSSLKEY","PGSSLROOTCERT"):
 if os.getenv(name):
  raise SystemExit("WA36 refuses libpq environment routing override "+name)
env={"PATH":os.getenv("PATH","/usr/bin:/bin"),
 "HOME":os.getenv("HOME","/tmp"),"LC_ALL":"C",
 "PGCONNECT_TIMEOUT":"5","PGAPPNAME":"wa36_minpriv_test"}
psql=["psql","-X","-qAt","-v","ON_ERROR_STOP=1",
      "-v","VERBOSITY=verbose",dsn]
def run(sql):
 return subprocess.run(psql+["-c",sql],env=env,text=True,
    capture_output=True,timeout=15,check=False)
def query(sql):
 p=run(sql)
 assert p.returncode==0,p.stderr[-500:]
 return p.stdout.strip()
def expect(sql,want):
 got=query(sql)
 assert got==want,(sql,got,want)
def denied(role,statement):
 assert role in ("wa36_untrusted","wa36_human_operator",
                 "wa36_meta_ingress","wa36_s0_candidate")
 p=run(f"SET ROLE {role}; {statement}")
 assert p.returncode!=0,(role,statement,p.stdout)
 assert "42501" in p.stderr,(role,statement,p.stderr[-450:])
def mark(n):
 print(f"WA36-{n:02} PASS",flush=True)

expect("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'wa36_%'","4")
mark(1)
expect("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'wa36_%' "
 "AND (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolbypassrls)","0")
mark(2)
expect("SELECT count(*) FROM wa36_lab.reviews","1")
mark(3)
expect("SELECT has_schema_privilege('wa36_untrusted','wa36_lab','USAGE')","f")
mark(4)
expect("SELECT has_schema_privilege('wa36_meta_ingress','wa36_lab','USAGE')","t")
expect("SELECT has_schema_privilege('wa36_meta_ingress','wa36_lab','CREATE')","f")
mark(5)
denied("wa36_untrusted","SELECT count(*) FROM wa36_lab.reviews;")
mark(6)
denied("wa36_human_operator","SELECT count(*) FROM wa36_lab.reviews;")
mark(7)
denied("wa36_meta_ingress","SELECT count(*) FROM wa36_lab.reviews;")
mark(8)
denied("wa36_meta_ingress","INSERT INTO wa36_lab.reviews("
 "shop_ref,attempt_ref,nonce_ref,status) VALUES("
 "'shop_A','attempt_lab','nonce_ingress','LAB_PENDING_RATIFICATION');")
mark(9)
expect("SELECT has_function_privilege('wa36_meta_ingress',"
 "'wa36_lab.append_proposal(text,text,text)','EXECUTE')","t")
mark(10)
denied("wa36_meta_ingress","SELECT wa36_lab.append_proposal("
 "'shop_A','attempt_lab','nonce_from_meta');")
mark(11)
expect("SELECT has_function_privilege('wa36_s0_candidate',"
 "'wa36_lab.append_proposal(text,text,text)','EXECUTE')","t")
mark(12)
denied("wa36_s0_candidate","SELECT wa36_lab.append_proposal("
 "'shop_A','attempt_lab','nonce_from_fake_s0');")
mark(13)
denied("wa36_untrusted","SELECT wa36_lab.append_proposal("
 "'shop_A','attempt_lab','nonce_untrusted');")
mark(14)
denied("wa36_human_operator","SELECT wa36_lab.append_proposal("
 "'shop_A','attempt_lab','nonce_human');")
mark(15)
for role in ("wa36_untrusted","wa36_meta_ingress",
             "wa36_s0_candidate","wa36_human_operator"):
 expect("SELECT has_schema_privilege('"+role+"','wa34_lab','USAGE')","f")
mark(16)
denied("wa36_meta_ingress","SELECT wa34_lab.consume_fixture("
 "'N','APP_A','111111','1234567890','wamid.WA33_LATE',"
 "'5581900000000','EVENT','SENT_REPORTED',1,1,100,2);")
mark(17)
denied("wa36_meta_ingress","UPDATE wa36_lab.reviews "
 "SET status='LAB_PENDING_RATIFICATION';")
denied("wa36_meta_ingress","DELETE FROM wa36_lab.reviews;")
mark(18)
expect("SELECT wa36_lab.append_proposal("
 "'shop_A','attempt_lab','nonce_admin')","LAB_FIXTURE_ONLY_NOT_SERVICE_AUTH")
expect("SELECT count(*) FROM wa36_lab.reviews","2")
mark(19)
p=run("INSERT INTO wa36_lab.reviews("
 "shop_ref,attempt_ref,nonce_ref,status,send_authorized) VALUES("
 "'shop_A','attempt_lab','nonce_unsafe','LAB_PENDING_RATIFICATION',true)")
assert p.returncode!=0 and "23514" in p.stderr,p.stderr[-450:]
expect("SELECT count(*) FROM wa36_lab.reviews WHERE send_authorized OR "
 "ack_allowed OR retry_external OR production_authorized OR s0_write_authorized","0")
mark(20)
print("PASS WA36: 20 PG17 least-privilege checks; no service or S0 approval",flush=True)
