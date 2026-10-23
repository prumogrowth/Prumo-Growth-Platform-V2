"""I45 after I44: same synthetic tables, same REAL GoTrue JWTs, local PostgREST.
Executed by I44 runner; never connects to hosted resources. Trusted SQL below
is solely test-fixture administration, not an authorized end-user endpoint.
"""
if os.environ.get("CI") != "true" or os.environ.get("PRUMO_S1_I44_EPHEMERAL") != "YES":
    raise AssertionError("I45 only allowed in ephemeral CI")
if not all(k in globals() for k in ("sql","rows","cases","actors","obj")):
    raise AssertionError("I45 must run after I44")
L1,L2,L3,L4 = (obj("62330000",i) for i in (1,2,3,4))
CY1,CY2,CY3,CY4,CY5 = (obj("62440000",i) for i in (1,2,3,4,5))
CNULL = obj("62770000",5)
sql(f"""
begin;
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values ('{M1}','{LA}','gestor'),('{M4}','{LA}','gestor');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values ('{L4}','{LA}','+5581888844444');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values ('{CY5}','{LA}','{L4}','aguardando primeiro disparo');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id)
 values ('{CNULL}','{LA}','{L1}','{obj("62660000",1)}');
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,
 direcao,origem,conteudo_sintetico,id_externo)
 values ('{LA}','{CNULL}','{obj("62660000",1)}',
 'entrada','simulado','I45 inbound sem caso','i45-sem-caso');
commit;
""")
assert cases(m1) == {CA,CB,CD} and cases(m4) == {CC}
assert rows("leads_loja",m1) == {L1,L2,L4}
assert rows("leads_loja",m4) == {L1,L2,L4}
assert rows("ciclos_comerciais",m1) == {CY1,CY2,CY3,CY5}
assert rows("ciclos_comerciais",m4) == {CY1,CY2,CY3,CY5}
print("PASS I45-01: JWT reproduces S0 store-wide leak of other-team and unassigned leads/cycles")
sql(file="supabase/tests/s1_065_proto_scope_local_only.sql")
assert rows("leads_loja",m1) == {L1,L3}
assert rows("ciclos_comerciais",m1) == {CY1,CY2,CY4}
assert rows("leads_loja",m4) == {L2}
assert rows("ciclos_comerciais",m4) == {CY3}
assert rows("leads_loja",out) == set() and rows("ciclos_comerciais",out) == set()
assert cases(m1) == {CA,CB,CD} and cases(m4) == {CC}
print("PASS I45-02: candidate scopes leads/cycles to own team regardless of store grant")
assert rows("leads_loja",c3) == set()
assert sql("update prumo_private.s1_excecoes_55 set revogada_em=null "
           "where operador_id='" + C3 + "'::uuid returning caso_id") == CB
assert cases(c3) == {CA,CB}
assert rows("leads_loja",c3) == {L1}
assert rows("ciclos_comerciais",c3) == {CY1,CY2}
assert sql("update prumo_private.s1_excecoes_55 "
           "set revogada_em=statement_timestamp() "
           "where operador_id='" + C3 + "'::uuid returning caso_id") == CB
assert rows("leads_loja",c3) == set() and rows("ciclos_comerciais",c3) == set()
print("PASS I45-03: exceptional same-contact lead/cycle context revokes with entitlement")
sql(f"delete from public.vinculos_papel_escopo where "
    f"ator_id in ('{M1}'::uuid,'{M4}'::uuid) "
    f"and concessionaria_id='{LA}'::uuid and papel='gestor'")
assert rows("leads_loja",m1) == {L1,L3}
assert rows("ciclos_comerciais",m1) == {CY1,CY2,CY4}
assert rows("leads_loja",m4) == {L2}
assert rows("ciclos_comerciais",m4) == {CY3}
print("PASS I45-04: store-grant revocation preserves only own-team context")
sql(f"""
begin;
update prumo_private.s1_gestor_operadores set encerrado_em=statement_timestamp()
 where gestor_id='{M1}' and operador_id='{C2}' and encerrado_em is null;
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values('{M4}','{C2}');
commit;
""")
assert cases(m1) == {CB}
assert cases(m4) == {CA,CB,CC,CD}
assert rows("leads_loja",m1) == {L1}
assert rows("ciclos_comerciais",m1) == {CY2}
assert rows("leads_loja",m4) == {L1,L2,L3}
assert rows("ciclos_comerciais",m4) == {CY1,CY2,CY3,CY4}
assert cases(c2) == {CD}, "consultant S0 ownership changed unexpectedly"
print("PASS I45-05: manager reassignment re-scopes same GoTrue JWT after commit")
assert CNULL not in rows("conversas",m1)
assert CNULL not in rows("conversas",m4)
assert CNULL not in rows("conversas",c2)
assert sql("select count(*) from public.mensagens where "
           f"conversa_id='{CNULL}'::uuid and caso_id is null") == "1"
for token in (m1,m4,c2):
    status,body = http("GET","/rest/v1/mensagens?select=id"
                       f"&conversa_id=eq.{CNULL}",token=token)
    assert status == 200 and body == [], "unlinked inbound became visible"
print("PASS I45-06: case-less message remains fail-closed, contextual access pending")
print("S1-002/I45: 6/6 real-auth checks in ephemeral stack; NOT S0 production approval.")
