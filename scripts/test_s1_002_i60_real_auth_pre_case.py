"""I60 after I50: real GoTrue JWTs, candidate RLS; disposable only."""
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I44_EPHEMERAL")!="YES":
    raise AssertionError("I60 CI-only")
cl2,cb,co=(obj("63540000",i) for i in (1,2,3))
orph=obj("63530000",1)
sql(f"""
begin;
-- Previous I46/I48 intentionally closed this same synthetic team link.
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
values('{M1}','{C3}');
update prumo_private.s1_excecoes_55 set revogada_em=null
where operador_id='{C3}'::uuid;
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
values('{orph}','{LA}','+5581888960002');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
values('{cl2}','{LA}','{L2}','{obj("62660000",1)}',null),
('{cb}','{LB}','{L3}','{obj("62660000",2)}',null),
('{co}','{LA}','{orph}','{obj("62660000",1)}',null);
insert into public.mensagens(id,concessionaria_id,conversa_id,canal_id,caso_id,
direcao,origem,conteudo_sintetico,id_externo)
values('{obj("63550000",1)}','{LA}','{cl2}','{obj("62660000",1)}',null,
'entrada','simulado','I60 other team pre-case','i60-e2e-a'),
('{obj("63550000",2)}','{LB}','{cb}','{obj("62660000",2)}',null,
'entrada','simulado','I60 same phone other shop','i60-e2e-b'),
('{obj("63550000",3)}','{LA}','{co}','{obj("62660000",1)}',null,
'entrada','simulado','I60 orphan contact','i60-e2e-c');
commit;
""")
assert cases(c3)=={CA,CB}
for t in (m1,m4,c2,c3,c5,out):
    assert CNULL not in rows("conversas",t), "I60 leaked before candidate"
print("PASS I60-REST-01: baseline denied unlinked conversation even with current entitlement")

sql(file="supabase/tests/s1_084_proto_rls_contexto_sem_caso_local_only.sql")
sql("notify pgrst, 'reload schema'")
def pre(t):
    visible=rows("conversas",t)
    return {x for x in (CNULL,cl2,cb,co) if x in visible}
expected=((c3,{CNULL}),(m1,{CNULL}),(m4,{CNULL,cl2,cb}),
          (c2,{cb}),(c5,{cl2}),(out,set()))
for t,ids in expected:
    assert pre(t)==ids,("I60 wrong pre-case scope",len(pre(t)),len(ids))
print("PASS I60-REST-02: current case ownership, team and exception scope exact shop/contact")
mi1,mi2,mi3=(obj("63550000",i) for i in (1,2,3))
for t,ids in ((c3,set()),(m1,set()),(m4,{mi1,mi2}),
              (c2,{mi2}),(c5,{mi1}),(out,set())):
    assert rows("mensagens",t)&{mi1,mi2,mi3}==ids
assert CNULL in pre(c3) and co not in pre(m4)
print("PASS I60-REST-03: message scope matches conversation; no orphan or cross-store leak")

code,_=http("POST","/rest/v1/mensagens",token=c3,body={
 "concessionaria_id":LA,"conversa_id":CNULL,"canal_id":obj("62660000",1),
 "caso_id":None,"direcao":"saida","origem":"simulado",
 "conteudo_sintetico":"I60 unauthorized reply","enviada_por":C3})
assert code>=400
assert sql("select count(*) from public.mensagens where conteudo_sintetico='I60 unauthorized reply'")=="0"
print("PASS I60-REST-04: contextual pre-case SELECT never unlocks outbound")

sql(f"""update prumo_private.s1_excecoes_55
 set revogada_em=pg_catalog.clock_timestamp()
 where operador_id='{C3}'::uuid and revogada_em is null""")
assert pre(c3)==set() and cases(c3)==set()
assert pre(m1)=={CNULL} and pre(m4)=={CNULL,cl2,cb}
print("PASS I60-REST-05: real JWT case exception revocation immediately hides pre-case history")
assert sql("""select count(*) from pg_catalog.pg_policies
where schemaname='public' and policyname like 's1_60_%'""")=="3"
print("PASS I60-REST-06: exact three lab candidate policies, no REST RPC/write expansion")
print("I60 GoTrue/PostgREST 6/6, no hosted deployment")
