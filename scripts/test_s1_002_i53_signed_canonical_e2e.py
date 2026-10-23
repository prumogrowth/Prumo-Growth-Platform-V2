"""I53: real local GoTrue + HMAC INTAKE53 -> canonical S0/S1 migration.
Run only inside the I37 disposable signer lifetime, after legacy 148 setup.
"""
from backend.s1_gateway_intake_canonical_local import (
    LocalSignedCanonicalIntakeGateway, _SQL_CANONICAL_INTAKE
)
from backend.s1_gateway_intake_signed_local import _SQL_INTAKE
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL")!="YES":
    raise AssertionError("I53 only in disposable I37 CI")
# I52 intentionally breaks the legacy suspend-account command: only load it
# AFTER the historical I18–I37 tests that still require old behavior.
sql(path="supabase/migrations/202610190053_s0_s1_intake_atribuicao_guard.sql")
sql(path="supabase/tests/s1_077_intake_assinado_canonico_local_only.sql")
app53=LocalSignedCanonicalIntakeGateway(
    gateway_dsn,SupabaseGoTrueVerifier(api,anon),
    signer=signer.client,key_id=new_key)
server53=serve_http_policy_local(app53,allowed_commands=("intake",),
                                 max_requests=100,window_seconds=60)
threading.Thread(target=server53.serve_forever,daemon=True).start()
gateway_url53="http://127.0.0.1:"+str(server53.server_address[1])
def intake53(token,operator,paused,version,extra=None):
    body={"operador_id":operator,"pausar":paused,"versao_esperada":version}
    if extra:body.update(extra)
    return http("POST","/s1/intake",bearer=token,body=body,base=gateway_url53)
# Dedicated cases avoid assuming any disposition of I18–I37 old workflow data.
lead_old="e5330000-0000-4000-8000-000000000001"
lead_other="e5330000-0000-4000-8000-000000000002"
lead_new="e5330000-0000-4000-8000-000000000003"
cy_old="e5440000-0000-4000-8000-000000000001"
cy_other="e5440000-0000-4000-8000-000000000002"
cy_new="e5440000-0000-4000-8000-000000000003"
case_old="e5550000-0000-4000-8000-000000000001"
case_other="e5550000-0000-4000-8000-000000000002"
case_new="e5550000-0000-4000-8000-000000000003"
try:
    # The last I37 action left O3 paused at legacy revision 4. Migration 053
    # MUST carry the paused bit and revision forward before switching guards.
    prior_state=sql(f"select pausado::text||':'||versao "
                    f"from prumo_private.s1_intake_estado where operador_id={U(o3)}")
    if prior_state!="true:4":
        raise AssertionError("I53 lost previously paused consultant or version: "+prior_state)
    token53=login["access_token"]
    status,data=intake53(token53,o3,False,4)
    ok(status,data,"INTAKE_RESUMED")
    if data["version"]!=5:
        raise AssertionError("I53 version migration did not resume from 4")
    status,_=call_intake(token53,o3,False,4)
    if status!=403:
        raise AssertionError("I53 old signed gateway still writes a split-brain intake state")
    sql(f"""
    insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
    values('{lead_old}',{U(store_a)},'+5581999995301'),
    ('{lead_other}',{U(store_a)},'+5581999995302'),
    ('{lead_new}',{U(store_a)},'+5581999995303');
    insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
    values('{cy_old}',{U(store_a)},'{lead_old}','em atendimento pelo operador'),
    ('{cy_other}',{U(store_a)},'{lead_other}','em atendimento pelo operador'),
    ('{cy_new}',{U(store_a)},'{lead_new}','em atendimento pelo operador');
    insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
    values('{case_old}',{U(store_a)},'{lead_old}','{cy_old}'),
    ('{case_other}',{U(store_a)},'{lead_other}','{cy_other}'),
    ('{case_new}',{U(store_a)},'{lead_new}','{cy_new}');
    insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
    values({U(store_a)},{U(case_old)},{U(o3)}),
          ({U(store_a)},{U(case_other)},{U(o4)});
    """)
    print("PASS S1CANON-149: legacy pause/version migrated atomically; old signed gateway disabled")

    status,data=intake53(token53,o3,True,5)
    ok(status,data,"INTAKE_PAUSED")
    assert data["version"]==6 and data["redistribution"]=="DEFERRED_S0_HUMAN_PROOF"
    assert sql(f"select estado from public.equipe_prumo_s1 where ator_id={U(o3)}")=="ativo"
    assert sql(f"select count(*) from public.atribuicoes_humanas "
               f"where caso_id={U(case_old)} and operador_id={U(o3)} "
               "and encerrada_em is null")=="1"
    print("PASS S1CANON-150: real JWT + independent signer pauses intake only, old case retained")

    status,data=intake53(token53,o3,True,6)
    ok(status,data,"ALREADY_APPLIED")
    assert data["version"]==6
    status,data=intake53(token53,o3,False,5)
    if status!=409 or data.get("outcome")!="CONFLICT":
        raise AssertionError("I53 CAS stale version not 409: "+str((status,data)))
    print("PASS S1CANON-151: idempotent retry and stale-version HTTP 409")

    status,data=intake53(token_g2,o3,False,6)
    if status!=403:
        raise AssertionError("I53 manager from other team changed intake "+str(status))
    status,data=intake53(token53,o3,False,6,{"motivo_codigo":"NÃO_PERMITIDO"})
    if status!=400:
        raise AssertionError("I53 accepted unknown reason field")
    print("PASS S1CANON-152: cross-team manager denied and JSON field allowlist enforced")

    try:
        sql(f"insert into public.atribuicoes_humanas("
          f"concessionaria_id,caso_id,operador_id) values("
          f"{U(store_a)},{U(case_new)},{U(o3)})")
    except RuntimeError as exc:
        if "DESTINO_COM_INTAKE_PAUSADO" not in str(exc):raise
    else:
        raise AssertionError("I53 canonical S0 direct assignment bypassed intake pause")
    old_assign=sql(f"select id from public.atribuicoes_humanas "
                   f"where caso_id={U(case_other)} and encerrada_em is null")
    try:
        sql(f"select prumo_private.s1_mover_atendimento_da_equipe("
            f"{U(g1)},{U(store_a)},{U(case_other)},"
            f"{U(old_assign)},{U(o3)})")
    except RuntimeError as exc:
        if "DESTINO_COM_INTAKE_PAUSADO" not in str(exc):raise
    else:
        raise AssertionError("I53 manual S1 assignment bypassed canonical S0 gate")
    assert sql(f"select count(*) from public.atribuicoes_humanas "
               f"where caso_id={U(case_other)} and operador_id={U(o4)} "
               f"and encerrada_em is null")=="1"
    assert sql(f"select count(*) from public.atribuicoes_humanas "
               f"where caso_id={U(case_new)}")=="0"
    print("PASS S1CANON-153: BOTH S0 direct write and S1 manual transfer deny paused destination")

    principal53=SupabaseGoTrueVerifier(api,anon).verify("Bearer "+token53)
    legacy=app.proof(principal53,uuid.UUID(o3),False,6,"Bearer "+token53)
    import psycopg
    try:
        with psycopg.connect(gateway_dsn,connect_timeout=5) as dbc:
            with dbc.cursor() as cur:
                cur.execute(_SQL_CANONICAL_INTAKE,legacy)
    except psycopg.Error as exc:
        if exc.sqlstate!="42501":raise
    else:
        raise AssertionError("I53 accepted legacy I37 INTAKE HMAC for INTAKE53 command")
    signed53=app53.proof(principal53,uuid.UUID(o3),True,6,"Bearer "+token53)
    with psycopg.connect(gateway_dsn,connect_timeout=5) as dbc:
        with dbc.cursor() as cur:
            cur.execute(_SQL_CANONICAL_INTAKE,signed53)
            assert cur.fetchone()[0]["outcome"]=="ALREADY_APPLIED"
    try:
        with psycopg.connect(gateway_dsn,connect_timeout=5) as dbc:
            with dbc.cursor() as cur:
                cur.execute(_SQL_CANONICAL_INTAKE,signed53)
    except psycopg.Error as exc:
        if exc.sqlstate!="42501":raise
    else:
        raise AssertionError("I53 replayed HMAC nonce changed canonical intake")
    print("PASS S1CANON-154: distinct HMAC command-domain, valid v53 and nonce replay denial")

    status,data=intake53(token53,o3,False,6)
    ok(status,data,"INTAKE_RESUMED")
    assert data["version"]==7
    sql(f"insert into public.atribuicoes_humanas("
        f"concessionaria_id,caso_id,operador_id) values("
        f"{U(store_a)},{U(case_new)},{U(o3)})")
    assert sql(f"select count(*) from public.atribuicoes_humanas "
               f"where caso_id={U(case_new)} and operador_id={U(o3)} "
               f"and encerrada_em is null")=="1"
    assert sql(f"select count(*) from prumo_private.s1_intake_eventos "
               f"where operador_id={U(o3)}")=="3"
    print("PASS S1CANON-155: signed resume enables canonical S0 assignment, three audit events")

    # Browser and SQL signed login must not touch internal business functions.
    status,_=http("POST","/rest/v1/rpc/s1_definir_intake",
        bearer=token53,body={"p_gestor":g1,"p_operador":o3,
                             "p_pausado":True,"p_versao_esperada":7})
    if status not in (401,403,404):
        raise AssertionError("I53 direct internal intake RPC exposed")
    status,_=http("POST","/s1/pausar",bearer=token53,
        body={"operador_id":o3,"motivo_codigo":"AUSENCIA_TEMPORARIA"},
        base=gateway_url53)
    if status!=404:raise AssertionError("I53 exposed obsolete pause endpoint")
    assert sql("select count(*) from pg_catalog.pg_proc p "
       "join pg_catalog.pg_namespace n on n.oid=p.pronamespace "
       "where n.nspname='prumo_private' and p.proname='s1_definir_intake' "
       "and pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE')")=="0"
    print("PASS S1CANON-156: private command and obsolete HTTP routes closed to clients")
    # I37-147/148 must survive cutover, but against the canonical signed
    # route: the old v37 bridge is deliberately disabled to avoid split brain.
    signer.revoke(new_key)
    status,_=intake53(token53,o3,True,7)
    if status!=403:
        raise AssertionError("I53 revoked HMAC signer key was accepted")
    print("PASS S1INTAKE-147: canonical signed intake denies revoked signer key")
    signer.close()
    status,_=intake53(token53,o3,True,7)
    if status!=503:
        raise AssertionError("I53 offline signer did not fail closed")
    print("PASS S1INTAKE-148: canonical signed intake unavailable without signer")
finally:
    server53.shutdown()
    server53.server_close()
print("S1-002/I53: 8/8 canonical real-GoTrue tests, INTAKE53 HMAC domain separation; disposable CI.")
