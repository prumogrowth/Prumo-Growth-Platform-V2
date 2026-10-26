"""I71 ephemeral real GoTrue rolling quota, durable refusal audit and retention.

Runs after I70 E2E on the same local stack; no hosted migrations.
"""
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL")!="YES":
 raise AssertionError("I71 disposable CI only")
sql(f"""update public.vinculos_papel_escopo set valido_ate=null
 where ator_id={U(g2)} and concessionaria_id={U(store_a)}
 and papel='gestor' and valido_ate is not null""")
sql(path="supabase/tests/s1_102_export_rolling_refusals_local_only.sql")
sql("notify pgrst,'reload schema'")

def export71(kind,token=token53,lim=1,cursor=None,shop=store_a):
 route="/rest/v1/rpc/s1_71_exportar_resumo"
 body={"p_tipo":kind,"p_loja":shop,"p_apos":cursor,"p_limite":lim}
 for attempt in range(25):
  st,data=http("POST",route,bearer=token,body=body,base=api)
  if st in (404,400) and ("schema" in str(data).lower() or
    "cache" in str(data).lower() or
    "Could not find the function" in str(data)):
   time.sleep(.2)
   continue
  return st,data
 raise AssertionError("I71 PostgREST cache did not expose new invoker export")

status,payload=export71("lotes")
assert status==200 and payload=={"estado":"LIMITE_ATINGIDO","linhas":[]},(status,payload)
assert sql(f"select sum(total) from prumo_private.s1_71_export_recusas "
 f"where ator_id={U(g1)} and tipo='lotes'")=="1"
assert sql(f"select count(*) from public.s1_70_export_reservas "
 f"where ator_id={U(g1)} and tipo='lotes'")=="4"
print("PASS I71-E2E-01: I70 accepted reservations count in 60-minute window; denied JSON response persists audit")

# 6 concurrent calls to a previously UNUSED scope: mgr2 CHANNELS. Exactly 4
# accepted, 2 declined, and 2 refusal events aggregated into a private bucket.
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=6) as pool:
 results=list(pool.map(lambda _:export71("canais",token=token_g2),range(6)))
oks=[x for x in results if x[0]==200 and x[1].get("estado")=="OK"]
denials=[x for x in results if x[0]==200 and x[1].get("estado")=="LIMITE_ATINGIDO"]
assert len(oks)==4 and len(denials)==2,results
assert all(len(x[1]["linhas"])==1 and
 x[1]["linhas"][0]["conversas_autorizadas"]==1 for x in oks),oks
assert sql(f"select count(*) from public.s1_70_export_reservas "
 f"where ator_id={U(g2)} and tipo='canais'")=="4"
assert sql(f"select sum(total) from prumo_private.s1_71_export_recusas "
 f"where ator_id={U(g2)} and tipo='canais'")=="2"
print("PASS I71-E2E-02: six simultaneous real JWT calls allow four scoped results and durably log two refusals")

# Artificially shift just g1's known accepted reservations to 59 then 61m
# before now; no need to manipulate system clocks or hosted settings.
sql(f"""update public.s1_70_export_reservas set
 registrada_em=pg_catalog.clock_timestamp()-interval '59 minutes'
 where ator_id={U(g1)} and tipo='lotes'""")
status,payload=export71("lotes")
assert status==200 and payload["estado"]=="LIMITE_ATINGIDO",(status,payload)
sql(f"""update public.s1_70_export_reservas set
 registrada_em=pg_catalog.clock_timestamp()-interval '61 minutes'
 where ator_id={U(g1)} and tipo='lotes'""")
status,payload=export71("lotes")
assert status==200 and payload["estado"]=="OK" and len(payload["linhas"])==1,(status,payload)
assert payload["linhas"][0]["lote_ref"]==lot64,payload
print("PASS I71-E2E-03: rolling sixty-minute time boundary denies 59m and permits after 61m")

# Invoker/permissions + isolation of old direct RPC.
for old in ("s1_69_exportar_lotes","s1_69_exportar_canais"):
 st,_=http("POST",f"/rest/v1/rpc/{old}",bearer=token53,
  body={"p_loja":store_a,"p_apos":None,"p_limite":1},base=api)
 assert st in (401,403,404),(old,st)
st,_=http("POST","/rest/v1/rpc/s1_71_exportar_resumo",bearer=anon,
 body={"p_tipo":"lotes","p_loja":store_a,"p_apos":None,"p_limite":1},base=api)
assert st in (401,403,404),st
for k,limit in (("lotes",0),("canais",21),("lotes",None),("untrusted",1)):
 st,err=export71(k,lim=limit)
 assert st==400,(k,limit,st,err)
print("PASS I71-E2E-04: old RPCs and anon inaccessible, invalid inputs fail closed")

st,payload=export71("lotes",token=tok6)
assert st==200 and payload=={"estado":"VAZIO","linhas":[]},(st,payload)
st,payload=export71("canais",token=token53,shop=store_b)
assert st==200 and payload=={"estado":"VAZIO","linhas":[]},(st,payload)
assert sql(f"select count(*) from public.s1_70_export_reservas "
 f"where ator_id={U(op6)}")=="0"
print("PASS I71-E2E-05: exception-only and foreign shop reveal no rows and create no reservations")

# The revoked store grant cuts access with SAME user token even if budget left.
sql(f"""update public.vinculos_papel_escopo
 set valido_ate=pg_catalog.clock_timestamp()
 where ator_id={U(g2)} and concessionaria_id={U(store_a)}
 and papel='gestor' and valido_ate is null""")
st,payload=export71("lotes",token=token_g2)
assert st==200 and payload=={"estado":"VAZIO","linhas":[]},(st,payload)
assert sql(f"select count(*) from public.s1_70_export_reservas "
 f"where ator_id={U(g2)} and tipo='lotes'")=="4"
print("PASS I71-E2E-06: revoked manager grant fails closed with unchanged GoTrue JWT and no new audit")

st,_=http("GET","/rest/v1/s1_71_export_recusas?select=*",
 bearer=token53,base=api)
assert st in (401,403,404),st
assert sql("select count(*) from prumo_s1_i65_test.exposicoes()")=="0"
assert sql("select pg_catalog.has_schema_privilege('authenticated',"
 "'prumo_private','USAGE')")=="f"
print("PASS I71-E2E-07: denial audit is private, no public definer/view leak")

# Cleanup explicit admin-only: backdate ONE accepted item and ONE refusal.
sql(f"""update public.s1_70_export_reservas set
 registrada_em=pg_catalog.clock_timestamp()-interval '31 days'
 where id=(select min(id) from public.s1_70_export_reservas);
update prumo_private.s1_71_export_recusas set
 ultima_em=pg_catalog.clock_timestamp()-interval '31 days'
 where ator_id={U(g1)} and tipo='lotes';""")
ret=sql("select aceitos_excluidos::text || ':' || recusas_excluidas::text "
 "from prumo_private.s1_71_purgar_registros(pg_catalog.clock_timestamp())")
assert ret=="1:1",ret
assert int(sql("select count(*) from public.s1_70_export_reservas"))>1
print("PASS I71-E2E-08: admin-only 30-day purge deletes exactly aged accepted and denied events, retains recent")
print("I71 8/8 real GoTrue rolling quota, denied audit, concurrency, retention E2E; disposable only")

# I72: same ephemeral GoTrue/PostgREST stack, no duplicated CI startup.
_i72=Path('scripts/test_s1_002_i72_ledger_unexposed_e2e.py')
exec(compile(_i72.read_text(encoding='utf-8'),str(_i72),'exec'),globals())
