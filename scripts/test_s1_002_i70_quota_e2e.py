"""I70 real JWT quota protection, audit-only accepted reservations and races.

Runs after I69 on disposable GoTrue/PostgREST. No production writes.
"""
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL")!="YES":
 raise AssertionError("I70 ephemeral CI only")
sql(path="supabase/tests/s1_100_admin_export_quota_local_only.sql")
sql("notify pgrst,'reload schema'")
def request70(kind,token=token53,lim=1,cursor=None,shop=store_a):
 route="/rest/v1/rpc/s1_69_exportar_"+kind
 return http("POST",route,bearer=token,
  body={"p_loja":shop,"p_apos":cursor,"p_limite":lim},base=api)

assert sql("select count(*) from prumo_private.s1_70_export_contadores")=="0"
assert sql("select count(*) from public.s1_70_export_reservas")=="0"
print("PASS I70-E2E-01: quota ledger and counters empty after I69 regressions; no retroactive consumption")

for n in range(4):
 st,rows=request70("lotes")
 assert st==200 and len(rows)==1 and rows[0]["lote_ref"]==lot64,(n,st,rows)
st,err=request70("lotes")
assert st==400 and "I70_QUOTA_EXCEDIDA" in str(err),(st,err)
assert sql(f"select requisicoes from prumo_private.s1_70_export_contadores "
 f"where ator_id={U(g1)} and concessionaria_id={U(store_a)} and tipo='lotes'")=="4"
assert sql(f"select count(*) from public.s1_70_export_reservas "
 f"where ator_id={U(g1)} and tipo='lotes'")=="4"
print("PASS I70-E2E-02: repeated same cursor consumes exactly four reservations; fifth denied without audit row")

st,rows=request70("canais",lim=20)
assert st==200 and len(rows)==2,(st,rows)
st,err=request70("canais",lim=11)
assert st==400 and "I70_QUOTA_EXCEDIDA" in str(err),(st,err)
st,rows=request70("canais",lim=10)
assert st==200 and len(rows)==2,(st,rows)
assert sql(f"select unidades_reservadas from prumo_private.s1_70_export_contadores "
 f"where ator_id={U(g1)} and tipo='canais'")=="30"
print("PASS I70-E2E-03: cumulative 20+11 blocked, 20+10 allowed; channels independent of lots")

# More simultaneous requests than available budget should serialize on same
# counter row, not pass due to a check-then-insert race.
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=6) as pool:
 results=list(pool.map(lambda _:request70("lotes",token=token_g2),range(6)))
passed=[x for x in results if x[0]==200]
blocked=[x for x in results if x[0]==400 and "I70_QUOTA_EXCEDIDA" in str(x[1])]
assert len(passed)==4 and len(blocked)==2,results
assert sql(f"select requisicoes from prumo_private.s1_70_export_contadores "
 f"where ator_id={U(g2)} and tipo='lotes'")=="4"
print("PASS I70-E2E-04: six concurrent real-JWT requests yield exactly four accepted and two quota-denied")

st,_=http("GET","/rest/v1/s1_70_export_reservas?select=*",
           bearer=token53,base=api)
assert st in (401,403),st
st,_=http("POST","/rest/v1/s1_70_export_reservas",bearer=token53,base=api,
 body={"ator_id":g2,"concessionaria_id":store_a,
       "tipo":"lotes","unidades_reservadas":1})
assert st in (401,403),st
assert sql(f"select count(*) from public.s1_70_export_reservas "
 f"where ator_id={U(g2)} and tipo='lotes'")=="4"
print("PASS I70-E2E-05: authenticated browser cannot read audit or forge another manager's reservation")

st,rows=request70("lotes",token=tok6)
assert st==200 and rows==[],(st,rows)
st,rows=request70("canais",token=token_g2,shop=store_b)
assert st==200 and rows==[],(st,rows)
assert sql(f"select count(*) from public.s1_70_export_reservas "
 f"where ator_id={U(op6)}")=="0"
print("PASS I70-E2E-06: no manager grant and cross-store route return empty without audit write")

sql(f"""update public.vinculos_papel_escopo
 set valido_ate=pg_catalog.clock_timestamp()
 where ator_id={U(g2)} and concessionaria_id={U(store_a)}
  and papel='gestor' and valido_ate is null""")
st,rows=request70("canais",token=token_g2)
assert st==200 and rows==[],(st,rows)
assert sql(f"select count(*) from public.s1_70_export_reservas "
 f"where ator_id={U(g2)} and tipo='canais'")=="0"
print("PASS I70-E2E-07: same JWT loses all grant-bound exports without new quota reservation")

assert sql("select count(*) from prumo_s1_i65_test.exposicoes()")=="0"
assert sql("select pg_catalog.has_schema_privilege('authenticated',"
 "'prumo_private','USAGE')")=="f"
assert sql("select pg_catalog.has_table_privilege('authenticated',"
 "'prumo_private.s1_70_export_contadores','SELECT')")=="f"
assert sql("select count(*) from pg_catalog.pg_proc "
 "where oid in ('public.s1_69_exportar_lotes(uuid,uuid,integer)'::regprocedure,"
 "'public.s1_69_exportar_canais(uuid,uuid,integer)'::regprocedure) "
 "and not prosecdef and provolatile='v'")=="2"
print("PASS I70-E2E-08: I65 scanner remains clear, invoker exports and private quota boundary intact")
print("I70 8/8 real GoTrue cumulative quota and concurrency E2E; disposable only")
