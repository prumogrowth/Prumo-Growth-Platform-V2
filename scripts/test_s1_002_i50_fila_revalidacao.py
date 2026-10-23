"""I50: CAS version, post-lock permission revocation and concurrent claims.
Only the I44-I49 disposable GoTrue/PostgREST stack, never hosted Supabase.
Trusted admin-side SQL emulates S0; no public claim endpoint is authorized.
"""
from concurrent.futures import ThreadPoolExecutor
import subprocess
import time
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I44_EPHEMERAL")!="YES":
    raise AssertionError("I50 refuses non-ephemeral execution")
if any(k not in globals() for k in (
    "sql","http","rows","obj","queue","DB","M1","M4",
    "LA","LB","L7","CY7","m1","m4","c2","CNULL")):
    raise AssertionError("I50 requires I44-I49 fixtures and real GoTrue actors")
sql(file="supabase/tests/s1_073_fila_cas_revalidacao_local_only.sql")
L8,L9,L10=(obj("62330000",i) for i in (8,9,10))
CY8,CY9,CY10=(obj("62440000",i) for i in (8,9,10))
sql(f"""
begin;
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('{L8}','{LA}','+5581888844448'),
       ('{L9}','{LA}','+5581888844449'),
       ('{L10}','{LA}','+5581888844450');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id)
 values('{CY8}','{LA}','{L8}'),('{CY9}','{LA}','{L9}'),
       ('{CY10}','{LA}','{L10}');
insert into prumo_s1_i49_test.s0_fila_sem_titular_mock
 (concessionaria_id,lead_id,ciclo_id)
 values('{LA}','{L8}','{CY8}'),('{LA}','{L9}','{CY9}');
commit;
""")
def claim50(actor_id,lead,cycle,case_id,expected=1,loja=LA):
    return sql(f"select prumo_s1_i50_test.assumir_versao_mock("
               f"'{loja}'::uuid,'{lead}'::uuid,'{cycle}'::uuid,"
               f"'{case_id}'::uuid,'{actor_id}'::uuid,{expected}::bigint)")
def count_cases(lead,loja=LA):
    return sql(f"select count(*) from public.casos_humanos "
               f"where concessionaria_id='{loja}'::uuid and lead_id='{lead}'::uuid")
def marker(lead):
    return sql(f"select estado||':'||versao from "
               "prumo_s1_i49_test.s0_fila_sem_titular_mock "
               f"where concessionaria_id='{LA}'::uuid and lead_id='{lead}'::uuid")

assert queue(m1,LA)=={(LA,L8,CY8),(LA,L9,CY9)}
assert claim50(M1,L8,CY8,obj("63100000",1),expected=2)=="CONFLICT_VERSION"
assert claim50(M1,L10,CY10,obj("63100000",2))=="NOT_IN_QUEUE"
assert marker(L8)=="pendente:1" and count_cases(L8)=="0"
assert count_cases(L10)=="0"
print("PASS I50-01: stale optimistic version and unmarked lead are denied without side effects")

# Hold the real lead row in a *separate* postgres transaction while a claim
# begins. Wait until pg_stat_activity PROVES a blocked claimant; revoke in a
# separate transaction, then release the original lock. The routine must
# revalidate permissions after acquiring the serialization lock.
def hold_lead(lead):
    p=subprocess.Popen(
      ["psql","-X","-qAt","-v","ON_ERROR_STOP=1",DB],
      stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
      text=True,bufsize=1)
    p.stdin.write("BEGIN;\n"
        f"select 'I50_HELD' from public.leads_loja where "
        f"concessionaria_id='{LA}'::uuid and id='{lead}'::uuid for update;\n")
    p.stdin.flush()
    first=p.stdout.readline().strip()
    if first!="I50_HELD":
        p.kill()
        raise AssertionError("I50 lead lock did not acquire: "+first)
    return p
def release_lead(p):
    if p.poll() is not None:
        raise AssertionError("I50 lead-holder unexpectedly exited")
    p.stdin.write("COMMIT;\n\\q\n")
    p.stdin.flush()
    p.stdin.close()
    rc=p.wait(timeout=10)
    if rc!=0:
        raise AssertionError("I50 release transaction failure")
def wait_blocked(f):
    for attempt in range(55):
        blocked=sql("select count(*) from pg_catalog.pg_stat_activity "
                    "where wait_event_type='Lock' and "
                    "query like '%prumo_s1_i50_test.assumir_versao_mock%'")
        if int(blocked)>0:
            return
        if f.done():
            raise AssertionError("I50 claim completed before forced revocation")
        time.sleep(0.1)
    raise AssertionError("I50 claimant not observed blocked on transaction lock")

lock=hold_lead(L8)
try:
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(claim50,M1,L8,CY8,obj("63100000",3))
        wait_blocked(pending)
        sql(f"delete from public.vinculos_papel_escopo "
            f"where ator_id='{M1}'::uuid and concessionaria_id='{LA}'::uuid "
            "and papel='gestor'")
        release_lead(lock)
        lock=None
        assert pending.result(timeout=15)=="REJECTED_SCOPE"
finally:
    if lock is not None and lock.poll() is None:
        release_lead(lock)
assert marker(L8)=="pendente:1" and count_cases(L8)=="0"
assert queue(m1,LA)==set() and queue(m4,LA)=={(LA,L8,CY8),(LA,L9,CY9)}
sql(f"insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) "
    f"values('{M1}','{LA}','gestor')")
print("PASS I50-02: revoke shop entitlement while claim is blocked; post-lock check denies without phantom case")

lock=hold_lead(L9)
try:
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(claim50,M1,L9,CY9,obj("63100000",4))
        wait_blocked(pending)
        sql(f"update public.equipe_prumo_s1 set estado='suspenso' "
            f"where ator_id='{M1}'::uuid")
        release_lead(lock)
        lock=None
        assert pending.result(timeout=15)=="REJECTED_SCOPE"
finally:
    if lock is not None and lock.poll() is None:
        release_lead(lock)
assert marker(L9)=="pendente:1" and count_cases(L9)=="0"
assert queue(m1,LA)==set()
assert queue(m4,LA)=={(LA,L8,CY8),(LA,L9,CY9)}
sql(f"update public.equipe_prumo_s1 set estado='ativo' "
    f"where ator_id='{M1}'::uuid")
print("PASS I50-03: suspend active team while claim is blocked; no stale JWT authority after lock")

assert claim50(M1,L7,CY7,obj("63100000",5),loja=LB)=="REJECTED_SCOPE"
assert count_cases(L7,LB)=="0" and queue(m1,LB)==set()
assert queue(m1,LA)=={(LA,L8,CY8),(LA,L9,CY9)}
print("PASS I50-04: other-store pending queue does not grant cross-dealership claim rights")

with ThreadPoolExecutor(max_workers=2) as pool:
    a=pool.submit(claim50,M1,L8,CY8,obj("63100000",6))
    b=pool.submit(claim50,M4,L8,CY8,obj("63100000",7))
    outcome=sorted([a.result(timeout=15),b.result(timeout=15)])
assert outcome==["ALREADY_CLAIMED","APPLIED"],outcome
assert marker(L8)=="resolvido:2" and count_cases(L8)=="1"
assert queue(m1,LA)=={(LA,L9,CY9)}
assert queue(m4,LA)=={(LA,L9,CY9)}
assert claim50(M4,L8,CY8,obj("63100000",8),expected=1)=="ALREADY_CLAIMED"
print("PASS I50-05: two current-version claims are serialized; one commit, one owner, no stale retry")

assert claim50(M4,L9,CY9,obj("63100000",9))=="APPLIED"
assert marker(L9)=="resolvido:2" and count_cases(L9)=="1"
assert queue(m1,LA)==set() and queue(m4,LA)==set()
for token in (m1,m4,c2):
    code,data=http("GET",f"/rest/v1/mensagens?select=id&conversa_id=eq.{CNULL}",
                   token=token)
    assert (code==200 and data==[]) or code in (401,403)
    code,_=http("GET",f"/rest/v1/rpc/assumir_versao_mock?p_loja={LA}",token=token)
    assert code in (400,401,403,404), "I50 mock claim exposed through REST"
assert sql("select count(*) from pg_catalog.pg_proc p "
    "join pg_catalog.pg_namespace n on n.oid=p.pronamespace "
    "where n.nspname='prumo_s1_i50_test' and p.proname='assumir_versao_mock' "
    "and pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE')")=="0"
print("PASS I50-06: resolving queue does not confer message read or direct client write/claim")
print("S1-002/I50: 6/6 lab regressions incl. two post-lock revocations and concurrent CAS; NO S0 operational approval.")
