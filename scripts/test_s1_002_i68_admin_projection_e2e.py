"""I68 real GoTrue: invoker-security admin summaries and column-level ACL.

Disposable-only test appended after I67. Two managers share physical
batch+channel but have disjoint RLS-visible cases. Never hosted deployment.
"""
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL")!="YES":
 raise AssertionError("I68 ephemeral only")

conv68="e7680000-0000-4000-8000-000000000001"
sql(f"""
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 values('{conv68}',{U(store_a)},'{lead67}','{channel63}','{case67}');
""")
# Before I68: I67 grants full table SELECT for readable rows.
st,got=http("GET",f"/rest/v1/itens_lote?select=id,motivo_rejeicao&lote_id=eq.{lot64}",
 bearer=token53,base=api)
assert st==200 and len(got)==1,(st,got)
print("PASS I68-E2E-01: baseline permits surplus raw administrative columns despite I67 row-level boundary")

sql(path="supabase/tests/s1_096_admin_projection_invoker_candidate_local_only.sql")
sql("notify pgrst,'reload schema'")
def proj68(table,token,query):
 return http("GET",f"/rest/v1/{table}?{query}",bearer=token,base=api)
for table,token,query in (
 ("itens_lote",token53,f"select=id&lote_id=eq.{lot64}"),
 ("itens_lote",token53,f"select=motivo_rejeicao&lote_id=eq.{lot64}"),
 ("reencontros_lote",token53,f"select=motivo&lote_id=eq.{lot64}"),
 ("eventos_status_comercial",token53,f"select=status_anterior&ciclo_id=eq.{cycle63}"),
 ("itens_lote",token53,f"select=*&lote_id=eq.{lot64}"),
):
 st,data=proj68(table,token,query)
 assert st in (401,403),(table,st,str(data)[:160])
print("PASS I68-E2E-02: SELECT * and forbidden column requests denied by real PostgREST")

for table,query,field,expected in (
 ("itens_lote",f"select=lead_id,resultado&lote_id=eq.{lot64}","lead_id",lead63),
 ("reencontros_lote",f"select=lead_id&lote_id=eq.{lot64}","lead_id",lead63),
 ("eventos_status_comercial",f"select=ciclo_id,status_posterior&ciclo_id=eq.{cycle63}","ciclo_id",cycle63),
):
 st,data=proj68(table,token53,query)
 assert st==200 and len(data)==1 and data[0][field]==expected,(table,st,data)
print("PASS I68-E2E-03: allowed column-only projections preserve exactly manager's RLS-scoped rows")

def summaries68(token,table,filter_value,field):
 for attempt in range(30):
  st,data=proj68(table,token,f"select=*&{field}=eq.{filter_value}")
  if st==200:return data
  # PostgREST async schema cache refresh is not an authorization result.
  if st not in (404,400):raise AssertionError((table,st,data))
  time.sleep(.2)
 raise AssertionError(("I68 schema cache failed to expose",table))
a=summaries68(token53,"s1_68_lotes_equipe",lot64,"lote_ref")
b=summaries68(token_g2,"s1_68_lotes_equipe",lot64,"lote_ref")
assert len(a)==len(b)==1 and a[0]["itens_autorizados"]==b[0]["itens_autorizados"]==1,(a,b)
assert set(a[0])=={"concessionaria_id","lote_ref","itens_autorizados"}
print("PASS I68-E2E-04: both teams receive their own row counts, no global mixed-batch total or header")

chA=summaries68(token53,"s1_68_canais_equipe",channel63,"canal_ref")
chB=summaries68(token_g2,"s1_68_canais_equipe",channel63,"canal_ref")
assert len(chA)==len(chB)==1 and chA[0]["conversas_autorizadas"]==2 and chB[0]["conversas_autorizadas"]==1,(chA,chB)
assert set(chA[0])=={"concessionaria_id","canal_ref","conversas_autorizadas"}
print("PASS I68-E2E-05: channel conversation counts scoped by caller; emitter IDs never present")

for tbl,fld,val in (
 ("lotes_importacao","id",lot64),("canais_loja","id",channel63),
):
 st,rows=proj68(tbl,token53,f"select=*&{fld}=eq.{val}")
 assert st==200 and rows==[],(tbl,st,rows)
for tbl in ("s1_68_lotes_equipe","s1_68_canais_equipe"):
 st,rows=proj68(tbl,tok6,"select=*")
 assert st==200 and rows==[],(tbl,st,rows)
 st,_=http("GET",f"/rest/v1/{tbl}?select=*",bearer=anon,base=api)
 assert st in (401,403),(tbl,st)
print("PASS I68-E2E-06: raw lot/channel remain quarantined; exception-only and anon users see no admin summaries")

sql(f"""update public.vinculos_papel_escopo set valido_ate=pg_catalog.clock_timestamp()
 where ator_id={U(g2)} and concessionaria_id={U(store_a)}
 and papel='gestor' and valido_ate is null;""")
assert summaries68(token_g2,"s1_68_lotes_equipe",lot64,"lote_ref")==[]
assert summaries68(token_g2,"s1_68_canais_equipe",channel63,"canal_ref")==[]
sql(f"""update public.vinculos_papel_escopo set valido_ate=null
 where ator_id={U(g2)} and concessionaria_id={U(store_a)}
 and papel='gestor' and valido_ate is not null;""")
assert summaries68(token_g2,"s1_68_lotes_equipe",lot64,"lote_ref")[0]["itens_autorizados"]==1
print("PASS I68-E2E-07: same valid GoTrue token loses then regains only permitted summaries on grant change")

assert sql("select count(*) from prumo_s1_i65_test.exposicoes()")=="0"
assert sql("select count(*) from pg_catalog.pg_class c "
 "join pg_catalog.pg_namespace ns on ns.oid=c.relnamespace "
 "where ns.nspname='public' and c.relname like 's1_68_%' "
 "and 'security_invoker=true'=any(coalesce(c.reloptions,array[]::text[]))")=="2"
assert sql("select pg_catalog.has_column_privilege('authenticated',"
 "'public.itens_lote','id','SELECT')")=="f"
assert sql("select pg_catalog.has_schema_privilege('authenticated',"
 "'prumo_s1_interface','USAGE')")=="f"
print("PASS I68-E2E-08: invoker views and sensitive column ACL audited; I65/I66 boundaries intact")
print("I68 8/8 real GoTrue projection and scoped summaries E2E; disposable only")
