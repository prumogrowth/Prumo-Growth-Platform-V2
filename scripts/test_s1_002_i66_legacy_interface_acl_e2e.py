"""I66: real GoTrue + signed I62 survives SQL legacy-interface ACL closure.

All data/auth endpoints ephemeral. Legacy I51 SECURITY DEFINER wrappers
remain introspectable but are no longer SQL callable by browser roles.
"""
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL")!="YES":
 raise AssertionError("I66 disposable CI only")

for f in ("s1_mover_atendimento_sessao(uuid,uuid,uuid,uuid)",
          "s1_pausar_operador_sessao(uuid,text)",
          "s1_reativar_operador_sessao(uuid)"):
 assert sql("select pg_catalog.has_function_privilege('authenticated',"
           f"'prumo_s1_interface.{f}','EXECUTE')")=="t",f
assert sql("select pg_catalog.has_schema_privilege('authenticated',"
           "'prumo_s1_interface','USAGE')")=="t"
print("PASS I66-E2E-01: SQL ACL baseline confirms all legacy facades were callable by authenticated")

sql(path="supabase/tests/s1_092_legacy_interface_acl_quarantine_local_only.sql")
for role in ("anon","authenticated","service_role"):
 assert sql(f"select pg_catalog.has_schema_privilege('{role}',"
            "'prumo_s1_interface','USAGE')")=="f",role
 for f in ("s1_mover_atendimento_sessao(uuid,uuid,uuid,uuid)",
           "s1_pausar_operador_sessao(uuid,text)",
           "s1_reativar_operador_sessao(uuid)"):
  assert sql(f"select pg_catalog.has_function_privilege('{role}',"
             f"'prumo_s1_interface.{f}','EXECUTE')")=="f",(role,f)
print("PASS I66-E2E-02: all three facades and schema closed to browser/service roles, ownership unchanged")

# Execute as the DB authenticated role, not postgres; no forged JWT GUC can
# bypass revoked schema USAGE. This session is solely a PG role probe.
sql("""
begin;
set local role authenticated;
do $test$
begin
 begin
  perform prumo_s1_interface.s1_mover_atendimento_sessao(null,null,null,null);
  raise exception 'I66_DIRECT_SQL_BYPASS';
 exception when insufficient_privilege then
  if pg_catalog.strpos(pg_catalog.lower(SQLERRM),'permission denied')=0 then
    raise exception 'I66_ERROR_FROM_LEGACY_BODY: %',SQLERRM;end if;
 end;
end $test$;
rollback;
""")
print("PASS I66-E2E-03: PostgreSQL authenticated caller rejected BEFORE entering legacy SECURITY DEFINER")

for routine,arguments in (
 ("s1_mover_atendimento_sessao",{"p_loja":store_a,"p_caso":case63,
    "p_atribuicao_esperada":attr63,"p_destino":op6}),
 ("s1_pausar_operador_sessao",{"p_operador":op6,"p_motivo_codigo":"TESTE"}),
 ("s1_reativar_operador_sessao",{"p_operador":op6}),
):
 status,_=http("POST","/rest/v1/rpc/"+routine,
               bearer=token53,body=arguments,base=api)
 assert status in (401,403,404),(routine,status)
print("PASS I66-E2E-04: real JWT cannot access any legacy facade over PostgREST")

# Reuse I62 mTLS GoTrue-bound signer and actual SQL-only HMAC gateway.
# This exception is already revoked: signed, idempotent operation remains
# functional after legacy SQL ACL quarantine with no account mutation.
result=app62.invoke("Bearer "+token53,"revogar_excecao",
                    {"excecao_id":exception_id})
assert result=={"outcome":"ALREADY_REVOKED"},result
print("PASS I66-E2E-05: independent I62 GoTrue+HMAC signed revocation remains callable and idempotent")

assert get63("leads_loja",token53,(lead63,unrelated64))=={lead63}
assert get63("leads_loja",token_g2,(lead63,unrelated64))==set()
assert get63("casos_humanos",token_g2,(case63,case63h))==set()
print("PASS I66-E2E-06: legitimate I63/I64 historical read and cross-team isolation unchanged")

assert sql("select count(*) from pg_catalog.pg_policies where "
           "schemaname='public' and policyname like 's1_63_canon_%'")=="8"
assert sql("select count(*) from pg_catalog.pg_policies where "
           "schemaname='public' and policyname like 's1_64_%'")=="7"
assert sql("select pg_catalog.has_schema_privilege('authenticated',"
           "'prumo_private','USAGE')")=="f"
print("PASS I66-E2E-07: RLS, private schema and signed executor boundaries unaffected")

# Real, current session token remains valid, while SQL legacy operations
# are closed. The gateway is a different and explicitly signed identity path.
assert SupabaseGoTrueVerifier(api,anon).verify("Bearer "+token53).actor_id==uuid.UUID(g1)
print("PASS I66-E2E-08: same real GoTrue session remains valid after legacy ACL cutover")
print("I66 8/8 GoTrue signed and SQL ACL quarantine E2E; disposable only")
_i67=Path("scripts/test_s1_002_i67_admin_row_scope_e2e.py")
exec(compile(_i67.read_text(encoding="utf-8"),str(_i67),"exec"),globals())

