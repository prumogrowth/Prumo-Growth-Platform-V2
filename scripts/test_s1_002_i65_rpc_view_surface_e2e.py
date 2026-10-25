"""I65 live JWT/PostgREST proof for unsafe public owner-rights objects.

Uses real GoTrue JWT and disposable Supabase CLI only; deliberately injected
RPC/view exist briefly in ephemeral DB, then ACL revoked and objects dropped.
"""
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL")!="YES":
 raise AssertionError("I65 disposable CI only")
sql(path="supabase/tests/s1_091a_rpc_view_catalog_scanner_local_only.sql")
def count65():
 return sql("select count(*) from prumo_s1_i65_test.exposicoes()")
assert count65()=="0",("I65 baseline exposed objects",count65())
status,_=http("POST","/rest/v1/rpc/s1_mover_atendimento_sessao",bearer=token53,
 body={"p_loja":store_a,"p_caso":case63,
       "p_atribuicao_esperada":attr63,"p_destino":op6},base=api)
assert status in (401,403,404),status
assert sql("select has_schema_privilege('authenticated',"
 "'prumo_s1_interface','USAGE')")=="t"
print("PASS I65-E2E-01: existing S1 legacy SQL interface is NOT exposed in public PostgREST RPC, but remains ACL risk")
# Build malicious objects solely within disposable DB: demonstrate that
# PostgREST can expose owner-rights functions and views, despite I63/I64 RLS.
sql("""
create function public.i65_e2e_excecoes_count()
returns bigint language sql stable security definer set search_path='' as
 $leak$ select count(*) from prumo_private.s1_excecoes_caso_i61 $leak$;
grant execute on function public.i65_e2e_excecoes_count() to authenticated;
create view public.i65_e2e_excecoes_view as
 select id,caso_id from prumo_private.s1_excecoes_caso_i61;
grant select on public.i65_e2e_excecoes_view to authenticated;
notify pgrst,'reload schema';
""")
try:
 assert count65()=="2",("I65 detector missed injected vulnerability",count65())
 print("PASS I65-E2E-02: live catalog detects injected owner-rights function and view despite I64 boundaries")
 def http65(method,route,body=None):
  return http(method,route,bearer=tok6,body=body,base=api)
 # Schema reload is async; don't confuse transient 404 with a security denial.
 observed_rpc=False;observed_view=False
 for _ in range(25):
  st,got=http65("POST","/rest/v1/rpc/i65_e2e_excecoes_count",{})
  if st==200:
   assert type(got) is int and got>0,(st,got)
   observed_rpc=True
   break
  time.sleep(0.2)
 for _ in range(25):
  st,got=http65("GET","/rest/v1/i65_e2e_excecoes_view?select=id")
  if st==200:
   assert type(got) is list and len(got)>0,(st,got)
   observed_view=True
   break
  time.sleep(0.2)
 assert observed_rpc and observed_view,("I65 red-team HTTP controls not reachable",observed_rpc,observed_view)
 print("PASS I65-E2E-03: live JWT reads private data through injected definer RPC and owner-rights view (red-team only)")
 # A real privilege revocation, not just client-side filtering.
 sql("""
 revoke all on function public.i65_e2e_excecoes_count()
  from public,anon,authenticated,service_role;
 revoke all on public.i65_e2e_excecoes_view
  from public,anon,authenticated,service_role;
 notify pgrst,'reload schema';
 """)
 assert count65()=="0","I65 lingering ACL risk after revoke"
 st,_=http65("POST","/rest/v1/rpc/i65_e2e_excecoes_count",{})
 assert st in (401,403,404),st
 st,_=http65("GET","/rest/v1/i65_e2e_excecoes_view?select=id")
 assert st in (401,403,404),st
 print("PASS I65-E2E-04: revoked function/view unavailable on SAME real JWT; scanner clean")
 st,_=http("GET","/rest/v1/s1_excecoes_caso_i61?select=id",bearer=tok6,base=api)
 assert st in (401,403,404),st
 print("PASS I65-E2E-05: no PostgREST route into the canonical private exception ledger")
finally:
 sql("""
 drop view if exists public.i65_e2e_excecoes_view;
 drop function if exists public.i65_e2e_excecoes_count();
 notify pgrst,'reload schema';
 """)
assert count65()=="0",("I65 leaked fixtures",count65())
print("PASS I65-E2E-06: disposable red-team objects dropped, private boundary remains closed")
print("I65 real GoTrue RPC/view surface E2E 6/6; synthetic attack objects destroyed")
