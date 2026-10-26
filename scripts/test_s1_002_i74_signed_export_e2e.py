"""I74 GoTrue real/PG signed export E2E on existing disposable I73 stack.

This file is called with a shallow copy of parent globals. No hosted DB.
"""
from backend.s1_gateway_export_signed_local import (
 LocalSignedExportGateway,_SQL_SIGNED_EXPORT)
from backend.s1_gateway_signed_local import _proof_material
from backend.s1_signer_process_local import LocalSignerSupervisor
from backend.identity_boundary import Principal
import psycopg

assert os.environ.get("CI")=="true"
assert os.environ.get("PRUMO_S1_I37_EPHEMERAL")=="YES"
sql(path="supabase/tests/s1_108_export_signed_executor_local_only.sql")
assert sql("select pg_has_role('prumo_s1_export_signed_login_ci',"
 "'prumo_s1_export_executor','MEMBER')")=="f"
assert sql("select pg_has_role('prumo_s1_export_login_ci',"
 "'prumo_s1_export_executor','MEMBER')")=="f"
print("PASS I74-E2E-01: original gateway login disconnected from executor; signed login has no membership")

# Provision disposable HMAC key. The secret travels only admin -> DB +
# supervisor control pipe; NEVER exposed to gateway/SQL application login.
key=uuid.uuid4()
secret=secrets.token_bytes(32)
sql("insert into prumo_export_auth.chaves_i74(id,secret,valid_from,valid_until)"
 f" values('{key}'::uuid,decode('{secret.hex()}','hex'),"
 "clock_timestamp()-interval '1 minute',clock_timestamp()+interval '1 hour')")
signed_password=secrets.token_hex(24)
sql("alter role prumo_s1_export_signed_login_ci login "
 f"password '{signed_password}'")
u=urlsplit(db)
signed_dsn=urlunsplit((u.scheme,
 f"prumo_s1_export_signed_login_ci:{signed_password}@{u.hostname}:{u.port}",u.path,"",""))
signer=LocalSignerSupervisor(independent_auth_url=api,publishable_key=anon)
try:
 assert signer.load(key,secret)
 signed_gateway=LocalSignedExportGateway(signed_dsn,verifier,
  signer=signer.client,key_id=key)
 del secret
 # SQL signed login cannot call its former raw RPC, nor see key/nonce tables.
 for q in (
  "select public.s1_71_exportar_resumo('lotes',"
  f"'{store_a}'::uuid,null,1)",
  "select secret from prumo_export_auth.chaves_i74",
  "select * from prumo_export_auth.nonces_i74",
  "select * from prumo_export_ledger.s1_70_export_reservas"):
  with psycopg.connect(signed_dsn) as con:
   with con.cursor() as cur:
    try:
     cur.execute(q)
     raise AssertionError("I74_RAW_SQL_BYPASS")
    except psycopg.errors.InsufficientPrivilege: pass
 print("PASS I74-E2E-02: compromised SQL login cannot call raw invoker or read HMAC/nonce/ledger")

 # Signed user: use existing session from I73 (not logged out).
 body={"tipo":"lotes","loja_id":store_a,"apos":None,"limite":1}
 principal=verifier.verify("Bearer "+token53)
 fields=export_fields(body)
 proof=signed_gateway.proof(principal,fields,"Bearer "+token53)
 before=int(sql("select count(*) from prumo_export_ledger.s1_70_export_reservas"))
 with psycopg.connect(signed_dsn) as con:
  with con.cursor() as cur:
   cur.execute(_SQL_SIGNED_EXPORT,proof)
   reply=cur.fetchone()[0]
 assert reply["estado"]=="OK" and len(reply["linhas"])==1,reply
 assert int(sql("select count(*) from prumo_export_ledger.s1_70_export_reservas"))==before+1
 assert sql(f"select count(*) from prumo_export_auth.nonces_i74 where nonce='{proof[-2]}'")=="1"
 print("PASS I74-E2E-03: independent signer revalidates GoTrue; DB verifies MAC/session and exports with RLS")

 # A spent nonce cannot be replayed, including after a first successful export.
 with psycopg.connect(signed_dsn) as con:
  with con.cursor() as cur:
   try:
    cur.execute(_SQL_SIGNED_EXPORT,proof)
    raise AssertionError("I74_REPLAY_ACCEPTED")
   except psycopg.errors.InsufficientPrivilege: pass
 assert int(sql("select count(*) from prumo_export_ledger.s1_70_export_reservas"))==before+1
 print("PASS I74-E2E-04: same signed request replay denied with no extra reservation")

 # Signed fields are immutable: alter kind, shop, cursor or limit without MAC.
 for ix,value in ((2,"canais"),(3,uuid.uuid4()),(4,uuid.uuid4()),(5,2)):
  forged=list(proof);forged[ix]=value
  with psycopg.connect(signed_dsn) as con:
   with con.cursor() as cur:
    try:
     cur.execute(_SQL_SIGNED_EXPORT,tuple(forged))
     raise AssertionError("I74_MAC_FIELDS_BYPASS")
    except psycopg.errors.InsufficientPrivilege: pass
 assert int(sql("select count(*) from prumo_export_ledger.s1_70_export_reservas"))==before+1
 print("PASS I74-E2E-05: kind, shop, cursor and page size tampering invalidates proof")

 # Signer independently rejects authenticated identity substitution.
 forged_principal=Principal(uuid.uuid4(),principal.session_id)
 try:
  signed_gateway.proof(forged_principal,fields,"Bearer "+token53)
  raise AssertionError("I74_SIGNER_ACCEPTED_FAKE_ACTOR")
 except Denied: pass
 try:
  signed_gateway.proof(principal,fields,"Bearer invalid.eyJ4IjoxfQ.invalid")
  raise AssertionError("I74_SIGNER_ACCEPTED_FAKE_JWT")
 except Denied: pass
 print("PASS I74-E2E-06: independent signer rejects spoofed actor and forged JWT")

 # Concurrent attempts sharing ONE valid signed proof must consume exactly once.
 # Use a no-grant actor: successful request remains VAZIO without spending quota.
 other=verifier.verify("Bearer "+tok6)
 concurrent=signed_gateway.proof(other,fields,"Bearer "+tok6)
 from concurrent.futures import ThreadPoolExecutor
 def run_once():
  with psycopg.connect(signed_dsn) as con:
   with con.cursor() as cur:
    try:
     cur.execute(_SQL_SIGNED_EXPORT,concurrent)
     return cur.fetchone()[0]["estado"]
    except psycopg.errors.InsufficientPrivilege:
     return "REPLAY_DENIED"
 with ThreadPoolExecutor(max_workers=2) as pool:
  results=list(pool.map(lambda _:run_once(),range(2)))
 assert sorted(results)==["REPLAY_DENIED","VAZIO"],results
 assert sql(f"select count(*) from prumo_export_auth.nonces_i74 where nonce='{concurrent[-2]}'")=="1"
 assert int(sql("select count(*) from prumo_export_ledger.s1_70_export_reservas"))==before+1
 print("PASS I74-E2E-07: atomic nonce prevents concurrent double-use, no unauthorized disclosure")

 # Time window and independent key revocation both fail closed.
 expired=list(proof);expired[-3]=int(time.time())-300;expired[-2]=uuid.uuid4()
 with psycopg.connect(signed_dsn) as con:
  with con.cursor() as cur:
   try:
    cur.execute(_SQL_SIGNED_EXPORT,tuple(expired))
    raise AssertionError("I74_STALE_MAC_ACCEPTED")
   except psycopg.errors.InsufficientPrivilege:pass
 assert signer.revoke(key)
 try:
  signed_gateway.export("Bearer "+token53,body)
  raise AssertionError("I74_REVOKED_SIGNER_ACCEPTED")
 except Denied: pass
 print("PASS I74-E2E-08: expired timestamp and independent signer key revocation denied")

finally:
 signer.close()
print("I74 8/8 real GoTrue signed export and replay E2E; disposable only")
