"""I73 real GoTrue + PostgreSQL role cutover, disposable local only.

Executed after I72 on the existing ephemeral stack.
"""
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL")!="YES":
 raise AssertionError("I73 DISPOSABLE ONLY")

import psycopg
from urllib.parse import urlsplit, urlunsplit
from backend.identity_boundary import SupabaseGoTrueVerifier, Denied, InvalidCommand
from backend.s1_gateway_export_local import LocalExportGateway, export_fields

before=int(sql("select count(*) from prumo_export_ledger.s1_70_export_reservas"))
sql(path="supabase/tests/s1_106_export_executor_local_only.sql")
sql("notify pgrst,'reload schema'")
assert sql("select pg_catalog.has_function_privilege('authenticated',"
 "'public.s1_71_exportar_resumo(text,uuid,uuid,integer)','EXECUTE')")=="f"
assert sql("select pg_catalog.has_column_privilege('authenticated',"
 "'prumo_export_ledger.s1_70_export_reservas','ator_id','INSERT')")=="f"
print("PASS I73-E2E-01: SQL role cutover removes direct authenticated RPC and INSERT grants")

# Authenticated user cannot call public RPC via actual PostgREST JWT.
st,_=export71("lotes",token=token53)
assert st in (401,403,404),st
st,_=http("POST","/rest/v1/s1_70_export_reservas",
 bearer=token53,body={"ator_id":g1,"concessionaria_id":store_a,
 "tipo":"lotes","unidades_reservadas":1},base=api)
assert st in (401,403,404),st
print("PASS I73-E2E-02: real GoTrue JWT cannot invoke legacy public export or direct ledger REST")

# Even arbitrary SQL with SET ROLE authenticated cannot spend a quota.
for direct in (
 "select public.s1_71_exportar_resumo('lotes',"
 f"'{store_a}'::uuid,null,1)",
 "insert into prumo_export_ledger.s1_70_export_reservas("
 "ator_id,concessionaria_id,tipo,unidades_reservadas) values("
 f"'{g1}'::uuid,'{store_a}'::uuid,'lotes',1)"
):
 with psycopg.connect(db) as admin:
  with admin.cursor() as cur:
   cur.execute("SET LOCAL ROLE authenticated")
   cur.execute("select pg_catalog.set_config('request.jwt.claim.sub',%s,true)",(g1,))
   try:
    cur.execute(direct)
    raise AssertionError("I73_DIRECT_AUTH_SQL_BYPASS")
   except psycopg.errors.InsufficientPrivilege:
    pass
assert int(sql("select count(*) from prumo_export_ledger.s1_70_export_reservas"))==before
print("PASS I73-E2E-03: even direct SQL authenticated cannot forge export or consume quota")

# Generate throwaway login credential only in CI RAM. Never persist or log it.
password=secrets.token_hex(24)
sql(f"create role prumo_s1_export_login_ci login noinherit password '{password}';"
 "grant prumo_s1_export_executor to prumo_s1_export_login_ci "
 "with inherit false, set true;")
u=urlsplit(db)
gateway_dsn=urlunsplit((u.scheme,
 f"prumo_s1_export_login_ci:{password}@{u.hostname}:{u.port}",u.path,"",""))
verifier=SupabaseGoTrueVerifier(api,anon)
gateway=LocalExportGateway(gateway_dsn,verifier)
principal=verifier.verify("Bearer "+token53)
assert str(principal.actor_id)==g1
assert sql("select prumo_export_auth.sessao_ativa("
 f"'{principal.actor_id}'::uuid,'{principal.session_id}'::uuid)")=="t"
print("PASS I73-E2E-04: GoTrue verifies JWT and dedicated gateway login holds SET ROLE only")

payload={"tipo":"lotes","loja_id":store_a,"apos":None,"limite":1}
result=gateway.export("Bearer "+token53,payload)
assert result["estado"]=="OK" and len(result["linhas"])==1,result
assert int(sql("select count(*) from prumo_export_ledger.s1_70_export_reservas"))==before+1
print("PASS I73-E2E-05: verified user uses executor-only invoker; RLS and quota preserved")

# Other user with revoked store grant must stay empty on SAME GoTrue JWT.
result=gateway.export("Bearer "+token_g2,payload)
assert result=={"estado":"VAZIO","linhas":[]},result
result=gateway.export("Bearer "+tok6,payload)
assert result=={"estado":"VAZIO","linhas":[]},result
assert int(sql("select count(*) from prumo_export_ledger.s1_70_export_reservas"))==before+1
print("PASS I73-E2E-06: revoked manager and non-manager cannot charge quota or export")

# No arbitrary caller-supplied identity; signature-tampered JWT fails.
bad=dict(payload,ator_id=g1)
try:
 gateway.export("Bearer "+token53,bad)
 raise AssertionError("I73_ACCEPTED_ACTOR_ID")
except InvalidCommand:
 pass
pieces=token53.split(".")
pieces[2]=("A" if pieces[2][:1]!="A" else "B")+pieces[2][1:]
try:
 gateway.export("Bearer "+".".join(pieces),payload)
 raise AssertionError("I73_ACCEPTED_TAMPERED_JWT")
except Denied:
 pass
assert int(sql("select count(*) from prumo_export_ledger.s1_70_export_reservas"))==before+1
print("PASS I73-E2E-07: actor spoofing and JWT tampering fail before DB mutation")

# Never revoke a session shared with downstream canonical I53/I62 E2E.
# Use a new synthetic GoTrue actor solely for lifecycle verification.
logout_actor,logout_token,_,_=person("i73-logout")
logout_principal=verifier.verify("Bearer "+logout_token)
assert str(logout_principal.actor_id)==logout_actor
assert sql("select prumo_export_auth.sessao_ativa("
 f"'{logout_principal.actor_id}'::uuid,'{logout_principal.session_id}'::uuid)")=="t"
st,_=http("POST","/auth/v1/logout",bearer=logout_token,base=api)
assert st in (200,204),st
assert sql("select prumo_export_auth.sessao_ativa("
 f"'{logout_principal.actor_id}'::uuid,'{logout_principal.session_id}'::uuid)")=="f"
try:
 gateway.export("Bearer "+logout_token,payload)
 raise AssertionError("I73_ACCEPTED_LOGGED_OUT_JWT")
except Denied:
 pass
print("PASS I73-E2E-08: GoTrue logout invalidates private DB session; old JWT denied")
print("I73 8/8 real GoTrue, SQL grants and executor-only export E2E; disposable only")

# I74: isolated signed exporter; no mutation of downstream E2E globals.
_i74=Path('scripts/test_s1_002_i74_signed_export_e2e.py')
exec(compile(_i74.read_text(encoding='utf-8'),str(_i74),'exec'),dict(globals()))
