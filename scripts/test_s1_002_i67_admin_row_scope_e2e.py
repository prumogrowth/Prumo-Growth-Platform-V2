"""I67 real GoTrue: row-authorized admin records in a mixed-team S0 lot.

Runs after I66 on disposable Supabase CLI. No signed S0 authority changes.
"""
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL")!="YES":
 raise AssertionError("I67 disposable-only")
op67,token67,_,_=person("i67-other-team")
lead67="e7670000-0000-4000-8000-000000000001"
cycle67="e7670000-0000-4000-8000-000000000002"
case67="e7670000-0000-4000-8000-000000000003"
atr67="e7670000-0000-4000-8000-000000000004"
sql(f"""
insert into public.atores(id) values({U(op67)});
insert into public.equipe_prumo_s1(ator_id,estado)
 values({U(op67)},'ativo');
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values({U(g2)},{U(op67)});
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values({U(op67)},{U(store_a)},'operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('{lead67}',{U(store_a)},'+5581886700001');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values('{cycle67}',{U(store_a)},'{lead67}','aguardando primeiro disparo');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 values('{case67}',{U(store_a)},'{lead67}','{cycle67}');
insert into public.atribuicoes_humanas(id,concessionaria_id,caso_id,operador_id)
 values('{atr67}',{U(store_a)},'{case67}',{U(op67)});
insert into public.itens_lote(concessionaria_id,lote_id,ordinal_linha,lead_id,resultado)
 values({U(store_a)},'{lot64}',2,'{lead67}','aceito');
insert into public.itens_lote(concessionaria_id,lote_id,ordinal_linha,
 resultado,motivo_rejeicao) values({U(store_a)},'{lot64}',3,'rejeitado','TELEFONE_INVALIDO');
insert into public.reencontros_lote(concessionaria_id,lote_id,lead_id)
 values({U(store_a)},'{lot64}','{lead67}');
insert into public.eventos_status_comercial(concessionaria_id,ciclo_id,
 versao_ciclo_apos,status_anterior,status_posterior)
 values({U(store_a)},'{cycle67}',2,
 'aguardando primeiro disparo','primeiro disparo enviado');
""")
def rows67(table,token,col,ident,columns):
 return indirect64(table,token,col,ident,columns)
for tab,col,cols in (
 ("itens_lote","lote_id","ordinal_linha,lead_id,resultado"),
 ("reencontros_lote","lote_id","lead_id"),
 ("eventos_status_comercial","concessionaria_id","ciclo_id"),
):
 assert rows67(tab,token53,col,lot64 if col=="lote_id" else store_a,cols)==[],tab
 assert rows67(tab,token_g2,col,lot64 if col=="lote_id" else store_a,cols)==[],tab
print("PASS I67-E2E-01: baseline I64 denies row-bearing collections for both managers in mixed team batch")

sql(path="supabase/tests/s1_094_admin_row_scoped_candidate_local_only.sql")
def trip67(token):
 i=rows67("itens_lote",token,"lote_id",lot64,"ordinal_linha,lead_id,resultado")
 re=rows67("reencontros_lote",token,"lote_id",lot64,"lead_id")
 ev=rows67("eventos_status_comercial",token,"concessionaria_id",store_a,"ciclo_id")
 return (i,re,ev)
ia,ra,ea=trip67(token53)
ib,rb,eb=trip67(token_g2)
assert {x["lead_id"] for x in ia}=={lead63},ia
assert {x["lead_id"] for x in ib}=={lead67},ib
assert {x["lead_id"] for x in ra}=={lead63},ra
assert {x["lead_id"] for x in rb}=={lead67},rb
assert cycle63 in {x["ciclo_id"] for x in ea} and cycle67 not in {x["ciclo_id"] for x in ea},ea
assert cycle67 in {x["ciclo_id"] for x in eb} and cycle63 not in {x["ciclo_id"] for x in eb},eb
assert not any(x["resultado"]=="rejeitado" for x in ia+ib)
print("PASS I67-E2E-02: two actual GoTrue managers see disjoint items/recontacts/events in same physical lot")

assert rows67("lotes_importacao",token53,"id",lot64,"id")==[]
assert rows67("lotes_importacao",token_g2,"id",lot64,"id")==[]
assert rows67("canais_loja",token53,"id",channel63,"id")==[]
assert rows67("canais_loja",token_g2,"id",channel63,"id")==[]
print("PASS I67-E2E-03: shared lot headers/channel remain quarantined for both managers")
assert all(not v for v in trip67(tok6))
print("PASS I67-E2E-04: exception-only consultant has no administrative raw reads")

# Simulated revocation acts on the persisted SQL permission, not JWT refresh.
sql(f"""update public.vinculos_papel_escopo
 set valido_ate=pg_catalog.clock_timestamp()
 where ator_id={U(g2)} and concessionaria_id={U(store_a)}
 and papel='gestor' and valido_ate is null""")
assert all(not v for v in trip67(token_g2))
print("PASS I67-E2E-05: same GoTrue JWT loses all admin rows after store-grant revoke")
sql(f"""update public.vinculos_papel_escopo
 set valido_ate=null where ator_id={U(g2)}
 and concessionaria_id={U(store_a)} and papel='gestor'
 and valido_ate is not null""")
assert {x["lead_id"] for x in trip67(token_g2)[0]}=={lead67}
print("PASS I67-E2E-06: recovered grant restores only linked manager's records")

assert sql("select count(*) from pg_catalog.pg_policies where "
 "schemaname='public' and policyname like 's1_67_%'")=="3"
assert sql("select count(*) from pg_catalog.pg_policies where "
 "schemaname='public' and policyname like 's1_64_%'")=="4"
assert sql("select pg_catalog.has_schema_privilege('authenticated',"
 "'prumo_s1_interface','USAGE')")=="f"
assert sql("select count(*) from prumo_s1_i65_test.exposicoes()")=="0"
print("PASS I67-E2E-07: I66 ACL closed, no definer/view leaks, seven scoped/quarantine boundaries")
print("I67 7/7 real GoTrue scoped administrative row tests; disposable only")
_i68=Path("scripts/test_s1_002_i68_admin_projection_e2e.py")
exec(compile(_i68.read_text(encoding="utf-8"),str(_i68),"exec"),globals())

