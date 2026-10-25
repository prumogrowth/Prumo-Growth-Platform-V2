"""I64 real GoTrue/PostgREST: detect and constrain S0 indirect D2 exposure.

Runs after I63 E2E, before signer-key revocation in disposable CI.
"""
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL")!="YES":
 raise AssertionError("I64 ephemeral CI only")
# G2 is a genuine manager, but not manager of I63 case / current operator.
# Explicit S0 manager store grant reproduces the indirect read leak.
sql(f"""insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values({U(g2)},{U(store_a)},'gestor');""")
unrelated64="e7640000-0000-4000-8000-000000000001"
lot64="e7640000-0000-4000-8000-000000000002"
sql(f"""
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('{unrelated64}',{U(store_a)},'+5581886400001');
insert into public.lotes_importacao(id,concessionaria_id,chave_importacao)
 values('{lot64}',{U(store_a)},'i64-e2e-import');
insert into public.itens_lote(concessionaria_id,lote_id,ordinal_linha,lead_id)
 values({U(store_a)},'{lot64}',1,'{lead63}');
insert into public.reencontros_lote(concessionaria_id,lote_id,lead_id)
 values({U(store_a)},'{lot64}','{lead63}');
insert into public.eventos_status_comercial(concessionaria_id,ciclo_id,
 versao_ciclo_apos,status_anterior,status_posterior)
 values({U(store_a)},'{cycle63}',2,
  'aguardando primeiro disparo','primeiro disparo enviado');
""")
def indirect64(table, token, column, value, selected):
 status, data=http("GET",f"/rest/v1/{table}?select={selected}&{column}=eq.{value}",
                   bearer=token,base=api)
 assert status==200,(table,status,str(data)[:250])
 return data
def bulk64(token):
 return (
  indirect64("canais_loja",token,"id",channel63,"id"),
  indirect64("lotes_importacao",token,"id",lot64,"id"),
  indirect64("itens_lote",token,"lote_id",lot64,"lead_id"),
  indirect64("reencontros_lote",token,"lote_id",lot64,"lead_id"),
  indirect64("eventos_status_comercial",token,"ciclo_id",cycle63,"ciclo_id"),
 )
assert get63("leads_loja",token_g2,(lead63,unrelated64))=={lead63,unrelated64}
assert get63("ciclos_comerciais",token_g2,(cycle63,cycle63h))=={cycle63,cycle63h}
assert all(len(items)==1 for items in bulk64(token_g2))
assert get63("casos_humanos",token_g2,(case63,case63h))==set()
print("PASS I64-E2E-01: real GoTrue manager with shop grant bypasses I63 case scope via 7 indirect S0 D2 read surfaces")
sql(path="supabase/tests/s1_089_s0_indirect_read_boundary_local_only.sql")
assert get63("leads_loja",token_g2,(lead63,unrelated64))==set()
assert get63("ciclos_comerciais",token_g2,(cycle63,cycle63h))==set()
assert all(not rows for rows in bulk64(token_g2))
print("PASS I64-E2E-02: 7 restrictive candidates close foreign-team direct leads/cycles and all five bulk reads")
# The trusted manager owns participant o3's historical assignment,
# and holds an explicit S0 store grant provisioned for I55.
assert get63("leads_loja",token53,(lead63,unrelated64))=={lead63}
assert get63("ciclos_comerciais",token53,(cycle63,cycle63h))=={cycle63,cycle63h}
assert all(not rows for rows in bulk64(token53))
print("PASS I64-E2E-03: legitimate supervisor sees same-contact leads/cycles only; bulk remains deliberately closed")
assert get63("leads_loja",tok6,(lead63,unrelated64))==set()
assert get63("ciclos_comerciais",tok6,(cycle63,cycle63h))==set()
assert get63("casos_humanos",tok6,(case63,case63h))==set()
print("PASS I64-E2E-04: revoked consultant gains neither case history nor raw D2 access")
# Live grant revocation invalidates the SAME JWT for lead/cycle SELECT.
sql(f"""update public.vinculos_papel_escopo
 set valido_ate=pg_catalog.clock_timestamp()
 where ator_id={U(g1)} and concessionaria_id={U(store_a)}
 and papel='gestor' and valido_ate is null;""")
assert get63("leads_loja",token53,(lead63,unrelated64))==set()
assert get63("ciclos_comerciais",token53,(cycle63,cycle63h))==set()
sql(f"""update public.vinculos_papel_escopo
 set valido_ate=null where ator_id={U(g1)}
 and concessionaria_id={U(store_a)} and papel='gestor'
 and valido_ate is not null;""")
assert get63("leads_loja",token53,(lead63,unrelated64))=={lead63}
print("PASS I64-E2E-05: same real JWT immediately respects revoked/restored manager-shop grant")
# Public RPC and private ledger ACL remain inaccessible.
status,_=http("POST","/rest/v1/rpc/contato_com_caso",
    bearer=token_g2,body={"p_loja":store_a,"p_lead":lead63},base=api)
assert status in (401,403,404),status
assert sql("select count(*) from pg_catalog.pg_policies where "
           "schemaname='public' and policyname like 's1_64_%'")=="7"
print("PASS I64-E2E-06: no exposed direct policy RPC; exactly 7 local-only restrictive policies")
print("I64 6/6 real GoTrue indirect D2 isolation tests; local-only CI")
_i65=Path("scripts/test_s1_002_i65_rpc_view_surface_e2e.py")
exec(compile(_i65.read_text(encoding="utf-8"),str(_i65),"exec"),globals())

