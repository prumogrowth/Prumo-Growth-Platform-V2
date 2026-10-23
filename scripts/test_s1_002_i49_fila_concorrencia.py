"""I49: minimum explicit S0 queue marker, store-scoped JWT projection, race.
All S0 operations are trusted postgres FIxtures, not authorized product APIs.
Do not deploy: mock S0 event and mock claim are only disposable tests.
"""
from concurrent.futures import ThreadPoolExecutor
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I44_EPHEMERAL")!="YES":
    raise AssertionError("I49 requires disposable CI")
if any(x not in globals() for x in (
    "sql","http","rows","obj","M1","M4","C2","LA","LB","L4","CY5",
    "m1","m4","c2","c3","c5","out","CNULL")):
    raise AssertionError("I49 must follow I44-I48")
sql(file="supabase/tests/s1_072_fila_minima_local_only.sql")
L6,L7=(obj("62330000",i) for i in (6,7))
CY6,CY7=(obj("62440000",i) for i in (6,7))
sql(f"""
begin;
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('{L6}','{LA}','+5581888844446'),
       ('{L7}','{LB}','+5581888844447');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id)
 values('{CY6}','{LA}','{L6}'),('{CY7}','{LB}','{L7}');
insert into prumo_s1_i49_test.s0_fila_sem_titular_mock
 (concessionaria_id,lead_id,ciclo_id)
 values('{LA}','{L4}','{CY5}'),('{LB}','{L7}','{CY7}');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('{M1}','{LA}','gestor');
commit;
""")
def queue(token, loja):
    for attempt in range(10):
        code,data=http("GET",f"/rest/v1/rpc/s1_i49_fila_resumo_mock?p_loja={loja}",
                        token=token)
        if code==404 and attempt<9:
            time.sleep(1)
            continue
        if code!=200 or not isinstance(data,list):
            raise AssertionError("I49 queue HTTP "+str(code))
        assert all(set(row)=={"concessionaria_id","lead_id","ciclo_id"} for row in data), (
            "I49 projection leaked fields")
        return {(row["concessionaria_id"],row["lead_id"],row["ciclo_id"])
                for row in data}
    raise AssertionError("I49 schema cache not loaded")
qA={(LA,L4,CY5)}
qB={(LB,L7,CY7)}
assert queue(m1,LA)==qA and queue(m4,LA)==qA
assert queue(m1,LB)==set() and queue(m4,LB)==set()
assert L6 not in rows("leads_loja",m1) and L6 not in rows("leads_loja",m4)
assert L4 not in rows("leads_loja",m4)
print("PASS I49-01: S0 explicit marker exposes only masked queue identifiers to two shop-approved managers")

for token in (c2,c3,c5,out):
    assert queue(token,LA)==set()
    assert queue(token,LB)==set()
code,data=http("GET",f"/rest/v1/rpc/s1_i49_fila_resumo_mock?p_loja={LA}")
assert (code==200 and data==[]) or code in (401,403), (
    "I49 anon received pending queue")
assert queue(m4,LB)==set()
print("PASS I49-02: consultants, outsider, anon and manager without shop grant cannot browse queue")

sql(f"delete from public.vinculos_papel_escopo "
    f"where ator_id='{M1}'::uuid and concessionaria_id='{LA}'::uuid "
    "and papel='gestor'")
assert queue(m1,LA)==set() and queue(m4,LA)==qA
sql(f"insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) "
    f"values('{M1}','{LA}','gestor')")
assert queue(m1,LA)==qA
print("PASS I49-03: removing/restoring dealership permission rescopes same GoTrue JWT")

sql(f"update public.equipe_prumo_s1 set estado='suspenso' "
    f"where ator_id='{M1}'::uuid")
assert queue(m1,LA)==set() and queue(m4,LA)==qA
sql(f"update public.equipe_prumo_s1 set estado='ativo' "
    f"where ator_id='{M1}'::uuid")
assert queue(m1,LA)==qA
# Grant in a DIFFERENT shop must not unlock the current one.
sql(f"insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) "
    f"values('{M1}','{LB}','gestor')")
assert queue(m1,LB)==qB and queue(m4,LB)==set()
assert queue(m1,LA)==qA
sql(f"delete from public.vinculos_papel_escopo where ator_id='{M1}'::uuid "
    f"and concessionaria_id='{LB}'::uuid and papel='gestor'")
assert queue(m1,LB)==set()
print("PASS I49-04: team suspension and cross-shop grant changes do not leak queue across stores")

# Two independent PostgreSQL sessions compete to claim the SAME S0-marked lead.
# This is a separate UNEXPOSED, postgres-only mock that locks the S0 lead row.
def claim(g,case_id):
    return sql(f"select prumo_s1_i49_test.assumir_mock("
               f"'{LA}'::uuid,'{L4}'::uuid,'{CY5}'::uuid,"
               f"'{case_id}'::uuid,'{g}'::uuid)")
case_1,case_2=obj("63000000",1),obj("63000000",2)
with ThreadPoolExecutor(max_workers=2) as pool:
    futures=[pool.submit(claim,M1,case_1),pool.submit(claim,M4,case_2)]
    outcomes=[f.result(timeout=20) for f in futures]
assert sorted(outcomes)==["ALREADY_CLAIMED","APPLIED"],outcomes
assert sql(f"select count(*) from public.casos_humanos "
           f"where concessionaria_id='{LA}'::uuid and lead_id='{L4}'::uuid")=="1"
assert sql(f"select count(*) from public.atribuicoes_humanas a "
           f"join public.casos_humanos h on h.id=a.caso_id "
           f"where h.concessionaria_id='{LA}'::uuid and h.lead_id='{L4}'::uuid "
           "and a.encerrada_em is null")=="1"
assert sql(f"select estado||':'||versao from "
           f"prumo_s1_i49_test.s0_fila_sem_titular_mock "
           f"where concessionaria_id='{LA}'::uuid and lead_id='{L4}'::uuid")=="resolvido:2"
assert queue(m1,LA)==set() and queue(m4,LA)==set()
assert claim(M1,obj("63000000",3))=="ALREADY_CLAIMED"
print("PASS I49-05: two concurrent trusted S0-shaped mock claims serialize to one owner; queue hides committed claim")

for token in (m1,m4):
    code,data=http("GET",f"/rest/v1/mensagens?select=id&conversa_id=eq.{CNULL}",
                   token=token)
    assert (code==200 and data==[]) or code in (401,403)
    code,data=http("GET",f"/rest/v1/rpc/assumir_mock?p_loja={LA}",token=token)
    assert code in (400,401,403,404), "I49 private mock improperly exposed"
code,_=http("POST","/rest/v1/casos_humanos",token=m4,body={
 "concessionaria_id":LA,"lead_id":L6,"ciclo_id":CY6,
 "id":obj("63000000",4)})
assert code in (401,403), "I49 allowed direct public case creation"
assert sql("select count(*) from pg_catalog.pg_proc p "
 "join pg_catalog.pg_namespace n on n.oid=p.pronamespace "
 "where n.nspname='prumo_s1_i49_test' and p.proname='assumir_mock' "
 "and pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE')")=="0"
assert sql("select count(*) from public.casos_humanos "
           f"where concessionaria_id='{LA}'::uuid and lead_id='{L6}'::uuid")=="0"
print("PASS I49-06: no messages or DML unlocked by projection; mock claim is not REST callable")
print("S1-002/I49: 6/6 real JWT/REST + two PostgreSQL sessions, lab-only; no S0 operational claim.")
