"""I69 real GoTrue/PostgREST: bounded invoker export with stable keyset.

Run only in ephemeral CI, following I68. Does not deploy or modify prod.
"""
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL")!="YES":
 raise AssertionError("I69 ephemeral test only")
lot69="e7690000-0000-4000-8000-000000000002"
channel69="e7690000-0000-4000-8000-000000000003"
conv69="e7690000-0000-4000-8000-000000000004"
sql(f"""
insert into public.lotes_importacao(id,concessionaria_id,chave_importacao)
 values('{lot69}',{U(store_a)},'i69-second-local');
insert into public.itens_lote(concessionaria_id,lote_id,ordinal_linha,lead_id,resultado)
 values({U(store_a)},'{lot69}',1,'{lead63}','aceito');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
 values('{channel69}',{U(store_a)},'i69-secondary-channel');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 values('{conv69}',{U(store_a)},'{lead63}','{channel69}','{case63}');
""")
# Snapshot before candidate: direct I68 view can be scanned without a bound.
st,rows=proj68("s1_68_lotes_equipe",token53,"select=*")
assert st==200 and len(rows)>=2,(st,rows)
print("PASS I69-E2E-01: unbounded direct summary view can enumerate manager's batches before I69")
sql(path="supabase/tests/s1_098_admin_export_bounded_candidate_local_only.sql")
sql("notify pgrst,'reload schema'")

def export69(kind,token,shop,cursor=None,limit=1):
 route="/rest/v1/rpc/s1_69_exportar_"+kind
 body={"p_loja":shop,"p_apos":cursor,"p_limite":limit}
 for attempt in range(20):
  status,result=http("POST",route,bearer=token,body=body,base=api)
  if status==200:return result
  if status in (404,400) and ("schema" in str(result).lower() or "cache" in str(result).lower()):
   time.sleep(.2)
   continue
  raise AssertionError((kind,status,str(result)[:250]))
 raise AssertionError("I69 RPC schema cache not refreshed "+kind)

a=export69("lotes",token53,store_a,None,1)
assert len(a)==1 and a[0]["lote_ref"]==lot64 and a[0]["itens_autorizados"]==1,a
b=export69("lotes",token53,store_a,a[0]["lote_ref"],1)
assert len(b)==1 and b[0]["lote_ref"]==lot69 and b[0]["itens_autorizados"]==1,b
assert export69("lotes",token53,store_a,b[0]["lote_ref"],1)==[]
assert set(a[0])=={"concessionaria_id","lote_ref","itens_autorizados"}
print("PASS I69-E2E-02: first, second and empty keyset pages are disjoint, max one item each")

a=export69("canais",token53,store_a)
assert len(a)==1 and a[0]["canal_ref"]==channel63 and a[0]["conversas_autorizadas"]==2,a
b=export69("canais",token53,store_a,a[0]["canal_ref"])
assert len(b)==1 and b[0]["canal_ref"]==channel69 and b[0]["conversas_autorizadas"]==1,b
assert export69("canais",token53,store_a,b[0]["canal_ref"])==[]
assert set(a[0])=={"concessionaria_id","canal_ref","conversas_autorizadas"}
print("PASS I69-E2E-03: bounded channel pages show only manager's RLS-visible counts")

other=export69("lotes",token_g2,store_a,None,20)
assert len(other)==1 and other[0]["lote_ref"]==lot64 and other[0]["itens_autorizados"]==1,other
otherc=export69("canais",token_g2,store_a,None,20)
assert len(otherc)==1 and otherc[0]["canal_ref"]==channel63 and otherc[0]["conversas_autorizadas"]==1,otherc
assert export69("lotes",token_g2,store_b,None,20)==[]
assert export69("canais",token_g2,store_b,None,20)==[]
print("PASS I69-E2E-04: foreign-team manager cannot enumerate other team's batch, channel or store")

for name in ("s1_68_lotes_equipe","s1_68_canais_equipe"):
 st,_=proj68(name,token53,"select=*")
 assert st in (401,403),(name,st)
for kind in ("lotes","canais"):
 status,_=http("POST",f"/rest/v1/rpc/s1_69_exportar_{kind}",
               bearer=anon,body={"p_loja":store_a,"p_apos":None,"p_limite":1},base=api)
 assert status in (401,403,404),(kind,status)
print("PASS I69-E2E-05: direct I68 views revoked, anon cannot call either new RPC")

for kind,limit in (("lotes",0),("canais",21),("lotes",None)):
 st,_=http("POST",f"/rest/v1/rpc/s1_69_exportar_{kind}",
    bearer=token53,body={"p_loja":store_a,"p_apos":None,"p_limite":limit},base=api)
 assert st==400,(kind,limit,st)
st,_=http("POST","/rest/v1/rpc/s1_69_exportar_canais",
 bearer=token53,body={"p_loja":None,"p_apos":None,"p_limite":1},base=api)
assert st==400,st
print("PASS I69-E2E-06: invalid, huge, null page sizes and null shop refused over HTTP")

assert export69("lotes",tok6,store_a,None,20)==[]
assert export69("canais",tok6,store_a,None,20)==[]
sql(f"""update public.vinculos_papel_escopo
 set valido_ate=pg_catalog.clock_timestamp()
 where ator_id={U(g2)} and concessionaria_id={U(store_a)}
 and papel='gestor' and valido_ate is null;""")
assert export69("lotes",token_g2,store_a,None,20)==[]
assert export69("canais",token_g2,store_a,None,20)==[]
print("PASS I69-E2E-07: exception-only denied, same revoked-manager JWT sees empty exports")
sql(f"""update public.vinculos_papel_escopo
 set valido_ate=null where ator_id={U(g2)}
 and concessionaria_id={U(store_a)} and papel='gestor'
 and valido_ate is not null;""")
assert export69("lotes",token_g2,store_a,None,20)[0]["itens_autorizados"]==1
assert get63("casos_humanos",token_g2,(case63,case63h))==set()
print("PASS I69-E2E-08: restored grant restores scoped export, not foreign case rights")

assert sql("select count(*) from prumo_s1_i65_test.exposicoes()")=="0"
assert sql("select pg_catalog.has_function_privilege('anon',"
 "'public.s1_69_exportar_lotes(uuid,uuid,integer)','EXECUTE')")=="f"
assert sql("select pg_catalog.has_schema_privilege('authenticated',"
 "'prumo_s1_interface','USAGE')")=="f"
print("PASS I69-E2E-09: no elevated definer/view exposure, legacy I66 cut remains")
print("I69 9/9 real GoTrue bounded export E2E; ephemeral only")
