"""I60 disposable real-JWT fixture with complete RLS and data teardown.

Runs right after I44 and BEFORE I45-I50 negative case-less expectations.
"""
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I44_EPHEMERAL")!="YES":
    raise AssertionError("I60 disposable GoTrue only")
cA,cl2,cb,orphchat=(obj("63540000",i) for i in range(1,5))
lead1,lead2,leadB=(obj("62330000",i) for i in range(1,4))
orph=obj("63530000",1)
mids=[obj("63550000",i) for i in range(1,5)]
# Only restore the test-only entitlement explicitly revoked by I44-05.
assert sql(f"""update prumo_private.s1_excecoes_55 set revogada_em=null
 where operador_id='{C3}'::uuid and revogada_em is not null
 returning caso_id""")==CB, "I60 fixture restoration failed"
assert cases(c3)=={CA,CB}, "I60 restored case exception unavailable before I45"

sql(f"""
begin;
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('{orph}','{LA}','+5581888960002');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 values('{cA}','{LA}','{lead1}','{obj("62660000",1)}',null),
 ('{cl2}','{LA}','{lead2}','{obj("62660000",1)}',null),
 ('{cb}','{LB}','{leadB}','{obj("62660000",2)}',null),
 ('{orphchat}','{LA}','{orph}','{obj("62660000",1)}',null);
insert into public.mensagens(id,concessionaria_id,conversa_id,canal_id,caso_id,
 direcao,origem,conteudo_sintetico,id_externo)
 values('{mids[0]}','{LA}','{cA}','{obj("62660000",1)}',null,
  'entrada','simulado','I60 synthetic same contact','i60-jwt-1'),
 ('{mids[1]}','{LA}','{cl2}','{obj("62660000",1)}',null,
  'entrada','simulado','I60 synthetic other team','i60-jwt-2'),
 ('{mids[2]}','{LB}','{cb}','{obj("62660000",2)}',null,
  'entrada','simulado','I60 synthetic other store same phone','i60-jwt-3'),
 ('{mids[3]}','{LA}','{orphchat}','{obj("62660000",1)}',null,
  'entrada','simulado','I60 synthetic no-case lead','i60-jwt-4');
commit;
""")
case_less={cA,cl2,cb,orphchat}
for t in (m1,m4,c2,c3,c5,out):
    assert not (rows("conversas",t)&case_less), "I60 baseline case-less RLS leak"
print("PASS I60-REST-01: baseline denies pre-case messages even with valid current case")

sql(file="supabase/tests/s1_084_proto_rls_contexto_sem_caso_local_only.sql")
def pre(t):
    return rows("conversas",t)&case_less
assert pre(c3)=={cA}, ("I60 exceptional wrong scope",pre(c3))
assert pre(m1)=={cA,cb}, ("I60 current team manager wrong scope",pre(m1))
assert pre(m4)=={cl2}, ("I60 other manager wrong scope",pre(m4))
assert pre(c2)=={cb}, ("I60 former consultant wrong scope",pre(c2))
assert pre(c5)=={cl2}, ("I60 current consultant wrong scope",pre(c5))
assert pre(out)==set()
print("PASS I60-REST-02: case-based entitlement reveals pre-case same contact/store only")
for t,expected in ((c3,{mids[0]}),(m1,{mids[0],mids[2]}),
                  (m4,{mids[1]}),(c2,{mids[2]}),
                  (c5,{mids[1]}),(out,set())):
    assert rows("mensagens",t)&set(mids)==expected,"I60 message membership mismatch"
print("PASS I60-REST-03: real JWT message projection obeys team, shop, no-case orphan isolation")

code,_=http("POST","/rest/v1/mensagens",token=c3,body={
 "concessionaria_id":LA,"conversa_id":cA,"canal_id":obj("62660000",1),
 "caso_id":None,"direcao":"saida","origem":"simulado",
 "conteudo_sintetico":"I60 blocked outbound","enviada_por":C3})
assert code>=400
assert sql("select count(*) from public.mensagens where conteudo_sintetico='I60 blocked outbound'")=="0"
print("PASS I60-REST-04: reading pre-case history does not authorize case-less send")

assert sql(f"""update prumo_private.s1_excecoes_55
 set revogada_em=pg_catalog.clock_timestamp()
 where operador_id='{C3}'::uuid and revogada_em is null
 returning caso_id""")==CB
assert pre(c3)==set() and cases(c3)==set()
assert pre(m1)=={cA,cb} and pre(m4)=={cl2}
print("PASS I60-REST-05: revocation immediately removes exceptional history, maintains managers")

# Revert ONLY I60 lab policies and data to EXACT pre-I45 I43 candidate baseline.
sql(f"""
begin;
drop policy s1_60_conversas_sem_caso_p on public.conversas;
drop policy s1_60_conversas_restrict on public.conversas;
drop policy s1_60_mensagens_restrict on public.mensagens;
create policy s1_63_conversas_restrict on public.conversas as restrictive
 for select to authenticated using (
 caso_id is not null and (
  prumo_s1_i41_test.pode_ler_caso_id(concessionaria_id,caso_id)
  or prumo_s1_i42_test.caso_historico_autorizado(concessionaria_id,caso_id)));
create policy s1_63_mensagens_restrict on public.mensagens as restrictive
 for select to authenticated using (
 prumo_s1_i41_test.pode_ler_mensagem(concessionaria_id,conversa_id,caso_id)
 or (caso_id is not null and
  prumo_s1_i42_test.msg_historico_autorizado(concessionaria_id,conversa_id,caso_id)));
drop schema prumo_s1_i60_test cascade;
delete from public.mensagens where id in ({','.join("'" + x + "'::uuid" for x in mids)});
delete from public.conversas where id in ({','.join("'" + x + "'::uuid" for x in case_less)});
delete from public.leads_loja where id='{orph}'::uuid;
commit;
""")
assert sql("""select count(*) from pg_catalog.pg_policies where schemaname='public'
 and policyname like 's1_60_%'""")=="0"
assert sql("select count(*) from public.conversas where id::text like '63540000-%'")=="0"
assert cases(c3)==set()
print("PASS I60-REST-06: complete I60 policy/schema/data teardown; I45-I50 baseline restored")
print("I60 GoTrue/PostgREST 6/6 candidate-only scenarios, no hosted deployment")
