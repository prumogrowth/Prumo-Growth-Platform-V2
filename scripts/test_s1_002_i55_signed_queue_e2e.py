"""I55: after I53 canonical integration, use actual ephemeral GoTrue + mTLS HMAC."""
from backend.s1_gateway_fila_canonical_local import (
 LocalSignedCanonicalQueueGateway,_SQL_QUEUE)
from backend.identity_boundary import SupabaseGoTrueVerifier
import psycopg
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL")!="YES":
    raise AssertionError("I55 only in disposable CI")
sql(path="supabase/migrations/202610190054_s0_fila_humana_canonica.sql")
sql(path="supabase/tests/s1_079_fila_assinada_canonica_local_only.sql")
# I37 legacy movement only requires a team link, NOT a manager/store grant.
# I55 intentionally requires current 'gestor' shop grant for queue list/claim.
# Provision synthetic scope explicitly; DO NOT relax signed bridge RBAC.
sql(f"""insert into public.vinculos_papel_escopo(
 ator_id,concessionaria_id,papel)
 values({U(g1)},{U(store_a)},'gestor')""")
if sql(f"""select count(*) from public.vinculos_papel_escopo
 where ator_id={U(g1)} and concessionaria_id={U(store_a)}
 and papel='gestor' and valido_ate is null""")!="1":
    raise AssertionError("I55 missing explicit current manager shop grant in test fixture")
# Two new fictional customers and real S0 cycle transitions: no I49 mocks.
lead55a="e7550000-0000-4000-8000-000000000001"
lead55b="e7550000-0000-4000-8000-000000000002"
cycle55a="e7550000-0000-4000-8000-000000000011"
cycle55b="e7550000-0000-4000-8000-000000000012"
sql(f"""
 insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('{lead55a}',{U(store_a)},'+558188550001'),
        ('{lead55b}',{U(store_a)},'+558188550002');
 insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values('{cycle55a}',{U(store_a)},'{lead55a}','aguardando primeiro disparo'),
        ('{cycle55b}',{U(store_a)},'{lead55b}','aguardando primeiro disparo');
""")
assert sql(f"select count(*) from prumo_private.s0_fila_humana where ciclo_id in ('{cycle55a}'::uuid,'{cycle55b}'::uuid)")=="0"
sql(f"""update public.ciclos_comerciais set status_comercial='em atendimento pelo operador'
 where id in ('{cycle55a}'::uuid,'{cycle55b}'::uuid);""")
assert sql(f"select count(*) from prumo_private.s0_fila_humana where ciclo_id in ('{cycle55a}'::uuid,'{cycle55b}'::uuid) and estado='pendente'")=="2"
print("PASS S1QUEUE-157: explicit S0 event creates queue, mere unassigned lead does not")
app55=LocalSignedCanonicalQueueGateway(gateway_dsn,SupabaseGoTrueVerifier(api,anon),
                                      signer=signer.client,key_id=new_key)
server55=serve_http_policy_local(app55,allowed_commands=("fila","assumir_fila"),
                                  max_requests=120,window_seconds=60)
threading.Thread(target=server55.serve_forever,daemon=True).start()
url55="http://127.0.0.1:"+str(server55.server_address[1])
def queue55(token,shop=store_a):
    return http("POST","/s1/fila",bearer=token,
                body={"loja_id":shop},base=url55)
def claim55(token,cycle,version=1,shop=store_a,extra=None):
    body={"loja_id":shop,"ciclo_id":cycle,"versao_esperada":version}
    if extra:body.update(extra)
    return http("POST","/s1/assumir_fila",bearer=token,body=body,base=url55)
try:
    status,data=queue55(token53)
    ok(status,data,"QUEUE_LIST")
    items=data["items"]
    got={x["ciclo_id"] for x in items}
    assert {cycle55a,cycle55b}.issubset(got),(status,data)
    assert len(items)<=25
    for item in items:
        assert set(item)=={"concessionaria_id","lead_id","ciclo_id","versao"}
    assert "telefone" not in str(data).lower() and "conteudo" not in str(data).lower()
    print("PASS S1QUEUE-158: authorized manager sees capped minimal S0 queue, no PII/messages")
    status,_=queue55(token_g2)
    assert status==403,("I55 other-team list",status)
    status,_=claim55(token_g2,cycle55a)
    assert status==403,("I55 other-team claim",status)
    print("PASS S1QUEUE-159: other-team/cross-store manager fails both LIST and CLAIM")
    for payload in (
       {"loja_id":store_a,"ator_id":g1},
       {"loja_id":store_a,"ciclo_id":cycle55a},
    ):
        status,_=http("POST","/s1/fila",bearer=token53,body=payload,base=url55)
        assert status==400,status
    status,_=claim55(token53,cycle55a,extra={"destino_id":o3})
    assert status==400,status
    status,_=claim55(token53,cycle55a,version=True)
    assert status==400,status
    status,_=http("GET","/s1/fila",bearer=token53,base=url55)
    assert status==405,status
    print("PASS S1QUEUE-160: strict fields, forbidden actor/target, boolean CAS and method")
    status,data=claim55(token53,cycle55a)
    ok(status,data,"CLAIMED_BY_MANAGER")
    assert data["version"]==2
    assert sql(f"select count(*) from public.atribuicoes_humanas a "
               f"join public.casos_humanos h on h.id=a.caso_id "
               f"where h.ciclo_id={U(cycle55a)} and a.operador_id={U(g1)} "
               "and a.encerrada_em is null")=="1"
    status,data=claim55(token53,cycle55a)
    assert status==409,(status,data)
    assert sql(f"select count(*) from public.casos_humanos where ciclo_id={U(cycle55a)}")=="1"
    assert sql(f"select count(*) from prumo_private.s0_fila_humana_eventos "
               f"where ciclo_id={U(cycle55a)} and resultado='ASSUMIDO'")=="1"
    print("PASS S1QUEUE-161: signed CAS claim creates exactly one S0 case/owner/audit and returns 409 on replay")
    principal=SupabaseGoTrueVerifier(api,anon).verify("Bearer "+token53)
    signed=app55.proof(principal,uuid.UUID(store_a),uuid.UUID(cycle55b),1,"Bearer "+token53)
    with psycopg.connect(gateway_dsn,connect_timeout=5) as connection:
        with connection.cursor() as cur:
            cur.execute(_SQL_QUEUE,signed)
            assert cur.fetchone()[0]["outcome"]=="CLAIMED_BY_MANAGER"
    try:
        with psycopg.connect(gateway_dsn,connect_timeout=5) as connection:
            with connection.cursor() as cur:
                cur.execute(_SQL_QUEUE,signed)
    except psycopg.Error as exc:
        assert exc.sqlstate=="42501",exc
    else:
        raise AssertionError("I55 nonce replay accepted")
    print("PASS S1QUEUE-162: signed claim and HMAC nonce replay denied inside privileged SQL")
    # Grant may expire WHILE an operation waits: bank validation is now after-lock.
    sql(f"""update public.vinculos_papel_escopo set valido_ate=clock_timestamp()
        where ator_id={U(g1)} and concessionaria_id={U(store_a)}
        and papel='gestor' and valido_ate is null""")
    status,_=queue55(token53)
    assert status==403,status
    status,_=claim55(token53,cycle55b,version=2)
    assert status==403,status
    sql(f"""update public.vinculos_papel_escopo set valido_ate=null
         where ator_id={U(g1)} and concessionaria_id={U(store_a)}
         and papel='gestor' and valido_ate is not null""")
    status,data=queue55(token53)
    ok(status,data,"QUEUE_LIST")
    print("PASS S1QUEUE-163: manager revocation takes effect on same JWT and restoring grant restores minimal list")
    status,_=http("POST","/rest/v1/rpc/invocar_fila_v55",
          bearer=token53,body={"p_loja":store_a},base=api)
    assert status in (401,403,404),status
    status,_=http("POST","/rest/v1/s0_fila_humana",
          bearer=token53,body={"concessionaria_id":store_a},base=api)
    assert status in (401,403,404),status
    with psycopg.connect(gateway_dsn,connect_timeout=5) as dbconn:
        with dbconn.cursor() as cur:
            try:
                cur.execute("select count(*) from prumo_private.s0_fila_humana")
            except psycopg.Error as exc:
                assert exc.sqlstate=="42501",exc
            else:
                raise AssertionError("I55 signed login reads private queue")
    print("PASS S1QUEUE-164: REST and signed SQL login cannot bypass private queue privileges")
finally:
    server55.shutdown()
    server55.server_close()
print("I55 8/8 E2E real local GoTrue and signed S0 queue; no hosted deployment")
