"""I47: GoTrue/PostgREST proof on the I44-I46 disposable-only stack.
SQL DDL/DML here is trusted postgres *fixture*, not an authorized operation.
No real Meta, delivery receipt, Supabase hosted DB or customer's messages.
"""
if os.environ.get("CI") != "true" or os.environ.get("PRUMO_S1_I44_EPHEMERAL") != "YES":
    raise AssertionError("I47 refuses non-disposable infrastructure")
required=("sql","http","rows","actors","obj","M1","M4","C3","LA","L1","L4","CY1","CY2","CY5","CNULL")
if any(k not in globals() for k in required):
    raise AssertionError("I47 must reuse I44-I46 GoTrue setup")
sql(file="supabase/tests/s1_068_setup_indirect_acl_local_only.sql")

T1=obj("62920000",1)
P1,P2,P5=(obj("62930000",i) for i in (1,2,5))
S1,S2,S5=(obj("62940000",i) for i in (1,2,5))
E1,E2,E5=(obj("62950000",i) for i in (1,2,5))
B1,B2,B5,B0=(obj("62960000",i) for i in (1,2,5,9))
IB=obj("62970000",1)
CH=obj("62660000",1)
# I46 terminated M1->C3 management; restore only to set two genuine teams
# with distinct case access. Store grants to both enable legacy leak reproduction.
sql(f"""
begin;
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values('{M1}','{C3}');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('{M1}','{LA}','gestor'),('{M4}','{LA}','gestor');
insert into public.catalogo_templates_sinteticos
 (id,concessionaria_id,codigo,versao,aprovado_simulacao)
 values('{T1}','{LA}','I47-FICTICIO',1,true);
insert into public.planos_recontato_sinteticos
 (id,concessionaria_id,lead_id,ciclo_id,canal_id,chave_idempotencia,fingerprint)
 values('{P1}','{LA}','{L1}','{CY1}','{CH}','i47-plano1','i47-fp1'),
       ('{P2}','{LA}','{L1}','{CY2}','{CH}','i47-plano2','i47-fp2'),
       ('{P5}','{LA}','{L4}','{CY5}','{CH}','i47-plano5','i47-fp5');
insert into public.envios_template_sinteticos
 (id,concessionaria_id,plano_id,template_id,ordem,agendado_em,chave_idempotencia)
 values('{S1}','{LA}','{P1}','{T1}',1,now()+interval '2 days','i47-send1'),
       ('{S2}','{LA}','{P2}','{T1}',1,now()+interval '2 days','i47-send2'),
       ('{S5}','{LA}','{P5}','{T1}',1,now()+interval '2 days','i47-send5');
insert into public.eventos_envio_template_sinteticos
 (id,concessionaria_id,envio_id,estado_anterior,estado_posterior,motivo)
 values('{E1}','{LA}','{S1}','programado','reservado','ensaio'),
       ('{E2}','{LA}','{S2}','programado','reservado','ensaio'),
       ('{E5}','{LA}','{S5}','programado','reservado','ensaio');
insert into public.eventos_callback_sinteticos
 (id,concessionaria_id,canal_id,envio_id,
 correlacao_externa_ficticia,evento_externo_ficticio,estado_reportado,
 instante_evento,resultado,fingerprint)
 values
 ('{B1}','{LA}','{CH}','{S1}','i47-corr1','i47-evt1','INCERTO_SIMULADO',
  now(),'CORRELACIONADO','i47-hash1'),
 ('{B2}','{LA}','{CH}','{S2}','i47-corr2','i47-evt2','INCERTO_SIMULADO',
  now(),'CORRELACIONADO','i47-hash2'),
 ('{B5}','{LA}','{CH}','{S5}','i47-corr5','i47-evt5','INCERTO_SIMULADO',
  now(),'CORRELACIONADO','i47-hash5'),
 ('{B0}','{LA}','{CH}',null,'i47-missing','i47-evt9','INCERTO_SIMULADO',
  now(),'PENDENTE_RECONCILIACAO','i47-hash9');
insert into public.pendencias_inbound_simulado
 (id,concessionaria_id,canal_id,lead_id,mensagem_id,motivo)
 select '{IB}'::uuid,'{LA}'::uuid,'{CH}'::uuid,'{L1}'::uuid,id,'MULTIPLOS_CICLOS'
 from public.mensagens where conversa_id='{CNULL}'::uuid and caso_id is null;
commit;
""")
assert sql("select count(*) from public.pendencias_reconciliacao_c07_sinteticas "
           f"where concessionaria_id='{LA}'::uuid") == "4"
# Legacy S0 policies are solely store-grant based; no S1 team gate for later tables.
for token in (m1,m4):
    assert rows("planos_recontato_sinteticos",token) == {P1,P2,P5}
    assert rows("envios_template_sinteticos",token) == {S1,S2,S5}
    assert rows("eventos_envio_template_sinteticos",token) == {E1,E2,E5}
    assert rows("eventos_callback_sinteticos",token) == {B1,B2,B5,B0}
    assert rows("pendencias_inbound_simulado",token) == {IB}
print("PASS I47-01: real JWT reproduces store-wide S0 plans, sends, callbacks and ambiguous inbox")

# S1 038 did not create a DIRECT gate on late tables; however current
# store-grant policy consults vinculos_papel_escopo, itself restricted by S1 038.
# Therefore inactive actors are ALREADY denied indirectly; do not claim a leak.
no_direct_gate=sql("select count(*) from pg_catalog.pg_policies "
  "where schemaname='public' and policyname='s1_equipe_ativa_gate' "
  "and tablename in ('planos_recontato_sinteticos','eventos_callback_sinteticos')")
assert no_direct_gate=="0", "I47 S1 038 unexpectedly protected later tables directly"
sql(f"update public.equipe_prumo_s1 set estado='suspenso' where ator_id='{M1}'::uuid")
assert rows("planos_recontato_sinteticos",m1) == set()
assert rows("eventos_callback_sinteticos",m1) == set()
sql(f"update public.equipe_prumo_s1 set estado='ativo' where ator_id='{M1}'::uuid")
print("PASS I47-02: late objects lack DIRECT gate; nested vinculos RLS blocks inactive JWT")

sql(file="supabase/tests/s1_069_proto_indirect_acl_local_only.sql")
assert rows("planos_recontato_sinteticos",m1) == {P2}
assert rows("envios_template_sinteticos",m1) == {S2}
assert rows("eventos_envio_template_sinteticos",m1) == {E2}
assert rows("eventos_callback_sinteticos",m1) == {B2}
assert len(rows("pendencias_reconciliacao_c07_sinteticas",m1)) == 1
assert rows("planos_recontato_sinteticos",m4) == {P1,P2}
assert rows("envios_template_sinteticos",m4) == {S1,S2}
assert rows("eventos_callback_sinteticos",m4) == {B1,B2}
assert len(rows("pendencias_reconciliacao_c07_sinteticas",m4)) == 2
assert rows("pendencias_inbound_simulado",m1) == set()
assert rows("pendencias_inbound_simulado",m4) == set()
assert rows("catalogo_templates_sinteticos",m1) == {T1}
print("PASS I47-03: lab gate composes team case/cycle restrictions; unlinked rows fail closed")

sql(f"delete from public.vinculos_papel_escopo where "
    f"ator_id='{M1}'::uuid and concessionaria_id='{LA}'::uuid and papel='gestor'")
assert rows("planos_recontato_sinteticos",m1) == {P2}
assert rows("eventos_callback_sinteticos",m1) == {B2}
assert rows("catalogo_templates_sinteticos",m1) == set()
print("PASS I47-04: removing store grant leaves team case read but removes catalog privilege")

sql(f"update public.equipe_prumo_s1 set estado='suspenso' where ator_id='{M1}'::uuid")
for table in ("catalogo_templates_sinteticos","planos_recontato_sinteticos",
              "envios_template_sinteticos","eventos_callback_sinteticos",
              "pendencias_reconciliacao_c07_sinteticas"):
    assert rows(table,m1) == set(), "I47 inactive S1 identity saw "+table
assert rows("planos_recontato_sinteticos",m4) == {P1,P2}
print("PASS I47-05: post-038 objects are denied for inactive S1 actor with same JWT")

# Catalog audit: S0 functions must not be directly executable by authenticated,
# and none of these late tables may allow ordinary DML.
n=sql("select count(*) from pg_catalog.pg_proc p "
      "join pg_catalog.pg_namespace n on n.oid=p.pronamespace "
      "where n.nspname='prumo_private' and p.proname in "
      "('agendar_recontatos_sinteticos','registrar_callback_c07_sintetico',"
      "'conciliar_pendencia_c07_sintetica') "
      "and pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE')")
assert n=="0", "I47 S0 internal function directly executable by authenticated"
for table,body in (
    ("planos_recontato_sinteticos",{
     "concessionaria_id":LA,"lead_id":L1,"ciclo_id":CY2,"canal_id":CH,
     "chave_idempotencia":"i47-unprivileged","fingerprint":"i47-invalid"}),
    ("eventos_callback_sinteticos",{
     "concessionaria_id":LA,"canal_id":CH,"envio_id":S2,
     "correlacao_externa_ficticia":"i47-tamper","evento_externo_ficticio":"i47-fake",
     "estado_reportado":"ENVIADO_SIMULADO","instante_evento":"2026-10-22T00:00:00Z",
     "resultado":"CORRELACIONADO","fingerprint":"i47-unauthorized"})):
    status,_=http("POST","/rest/v1/"+table,token=m4,body=body)
    assert status in (401,403), "I47 unauthorized DML accepted for "+table
assert sql("select count(*) from pg_catalog.pg_policies "
           "where schemaname='public' and policyname='s1_47_ativo_gate'")=="9"
assert rows("eventos_callback_sinteticos",out) == set()
print("PASS I47-06: S0 RPC/DML denied; nine new objects gated and outsider blocked")
print("S1-002/I47: 6/6 local GoTrue/PostgREST checks, NO S0 production homologation.")
