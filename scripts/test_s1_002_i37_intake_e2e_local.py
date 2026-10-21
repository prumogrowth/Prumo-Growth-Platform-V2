#!/usr/bin/env python3
"""S1-002/I37: E2E somente local CI (GoTrue, PostgREST e migrations REAIS).
Test-only public bridges; NEVER use against hosted Supabase or production.
"""
import json
import secrets
import base64
import os
import re
import subprocess
import time
import threading
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse, urlsplit, urlunsplit
from backend.s1_gateway_intake_signed_local import LocalSignedIntakeOnlyGateway, _SQL_INTAKE
from backend.s1_gateway_local import _SQL
from backend.s1_gateway_http_policy_local import serve_http_policy_local
from backend.s1_gateway_signed_local import LocalSignedTeamGateway, _SQL_SIGNED
from backend.s1_signer_process_local import LocalSignerSupervisor, LocalSeparatedSignerGateway
from backend.s1_signer_independent_gotrue_local import LocalIndependentlyAuthenticatedGateway
from backend.s1_signer_mtls_local import LocalMutualTlsSignerSupervisor, LocalMutualTlsSignerClient
from backend.s1_i27_ephemeral_certificates import create_local_certificates, certificate_fingerprint
from backend.s1_i28_rotating_certificates import create_rotating_certificates
from backend.s1_signer_mtls_rotation_local import LocalRotatingTlsSignerSupervisor
from backend.s1_signer_mtls_persistent_local import LocalPersistentTlsSignerSupervisor
from backend.s1_i30_signed_revocation_authority_local import LocalRevocationAuthoritySupervisor
from backend.s1_i31_monotonic_witness_local import LocalMonotonicWitnessSupervisor
from backend.s1_i31_witness_authority_local import LocalWitnessBackedRevocationSupervisor, bootstrap_i31_authority
from backend.s1_signer_mtls_authority_local import LocalAuthorityBackedSignerSupervisor
from backend.s1_i29_persistent_certificate_store import LocalCertificateState,RevocationStateUnavailable
from pathlib import Path
import shutil
import tempfile
import socket
import ssl
from backend.s1_gateway_signed_local import _proof_material, _action_args
from backend.identity_boundary import Denied, IdentityUnavailable
from backend.identity_boundary import SupabaseGoTrueVerifier, Principal
from urllib.request import Request, urlopen

if __name__ == '__main__':
    api = os.environ["API_URL"].rstrip("/")
    db = os.environ["DB_URL"]
    anon = os.environ["ANON_KEY"]
    if os.environ.get("CI") != "true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL") != "YES":
        raise SystemExit("RECUSADO: exige CI e PRUMO_S1_I37_EPHEMERAL=YES")
    for url in (api, db):
        if urlparse(url).hostname not in ("localhost", "127.0.0.1", "::1"):
            raise SystemExit("RECUSADO: somente loopback")
    if urlparse(db).path != "/postgres":
        raise SystemExit("RECUSADO: somente banco local /postgres")

    def sql(statement=None, path=None):
        args = ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-t", "-A", db]
        args += ["-c", statement] if statement is not None else ["-f", str(path)]
        p = subprocess.run(args, capture_output=True, text=True)
        if p.returncode:
            raise RuntimeError("I18 SQL " + str(path or "fixture") + ": " + p.stderr[-2000:])
        return p.stdout.strip()

    def http(method, route, bearer=None, body=None, base=None):
        data = json.dumps(body).encode() if body is not None else None
        headers = {"apikey": anon, "Authorization": "Bearer " + (bearer or anon)}
        if body is not None:
            headers["Content-Type"] = "application/json"
        try:
            with urlopen(Request((base or api) + route, data=data, headers=headers, method=method), timeout=20) as r:
                raw = r.read().decode()
                return r.status, json.loads(raw) if raw else {}
        except HTTPError as e:
            raw = e.read().decode()
            try:
                response = json.loads(raw)
            except ValueError:
                response = {"message": raw[:180]}
            return e.code, response

    def person(label):
        email = f"s1-i18-{label}@example.test"
        password = "SyntheticI18_Local_2026!"
        status, reg = http("POST", "/auth/v1/signup",
                           body={"email": email, "password": password})
        if status not in (200, 201) or "user" not in reg:
            raise AssertionError("signup local " + label + ": " + str(status))
        status, info = http("POST", "/auth/v1/token?grant_type=password",
                            body={"email": email, "password": password})
        if status != 200 or "access_token" not in info:
            raise AssertionError("login local " + label + ": " + str(status))
        return str(uuid.UUID(info["user"]["id"])), info["access_token"], email, password

    def rpc(name, token, **kwargs):
        mapping = {
            "p_loja": "loja_id",
            "p_caso": "caso_id",
            "p_atribuicao_esperada": "atribuicao_esperada_id",
            "p_destino": "destino_id",
            "p_operador": "operador_id",
            "p_motivo_codigo": "motivo_codigo",
        }
        body = {mapping.get(key, key): val for key, val in kwargs.items()}
        return http("POST", "/s1/" + name, bearer=token, body=body, base=gateway_url)


    def ok(status, data, outcome):
        if status != 200 or data.get("outcome") != outcome:
            raise AssertionError("esperado " + outcome + "; HTTP=" + str(status)
                                 + " corpo=" + str(data)[:250])

    def blocked(status, message):
        if status < 400:
            raise AssertionError("BYPASS: " + message + " status " + str(status))

    # Aplicar as migracoes reais, sem bootstrap_fake_auth e sem testes S0/S1
    # que gravam fixtures de PG17. Nenhuma migration adicional é inventada.
    source_runners = [
        "scripts/run-s0-local.sh",
        "scripts/run-s1-002-local.sh",
        "scripts/run-s1-002-i12-local.sh",
    ]
    paths = []
    for runner in source_runners:
        code = Path(runner).read_text(encoding="utf-8")
        paths.extend(re.findall(r"supabase/migrations/[A-Za-z0-9_.-]+\.sql", code))
    paths.append("supabase/migrations/202610190052_s1_verificacao_sessao_gotrue.sql")
    paths = sorted(set(paths))
    if len(paths) < 45 or not paths[0].endswith("202610170001_s0_foundation.sql"):
        raise AssertionError("listagem das migrations incompleta: " + str(len(paths)))
    for migration in paths:
        sql(path=migration)
    print("PASS S1WITNESS-01: S0/S1 migrations reais aplicadas no Supabase efemero (" +
          str(len(paths)) + " arquivos)")

    # A fixture I20 (não migration) cria só a role SQL test-only e funções
    # SECURITY DEFINER em schema privado, sem acesso authenticated e SEM RPC.
    sql(path="supabase/tests/s1_020_signed_gateway_local_only.sql")
    key_id = uuid.uuid4()
    secret = secrets.token_bytes(32)
    sql(
        "insert into prumo_s1_signed_i20.chaves(id,segredo,valido_desde,valido_ate) "
        f"values ('{key_id}'::uuid, decode('{secret.hex()}','hex'), "
        "clock_timestamp() - interval '1 minute', clock_timestamp() + interval '10 minutes')"
    )
    # I21: altera ownership apenas depois de inserir chave aleatoria no
    # banco de teste. A role executor e NOLOGIN e nao e assumivel pelo login SQL.
    sql(path="supabase/tests/s1_021_executor_owner_local_only.sql")
    # I22 transacional: custodio da chave sem acesso a negocio/nonce
    sql(path="supabase/tests/s1_022_chave_custodio_separado_local_only.sql")
    # I24: auditoria sem segredo, CAS e funcoes administrativas somente em CI
    sql(path="supabase/tests/s1_024_ciclo_chaves_auditoria_local_only.sql")
    parts = urlsplit(db)
    gateway_dsn = urlunsplit((
        parts.scheme,
        "prumo_s1_signed_login_ci:I20_Temporary_Only_Not_Production_2026!@" +
        parts.hostname + ":" + str(parts.port),
        "/postgres", "", "",
    ))
    gateway = LocalSignedTeamGateway(
        gateway_dsn, SupabaseGoTrueVerifier(api, anon),
        key_id=key_id, signing_key=secret,
    )
    server = serve_http_policy_local(gateway, max_requests=200, window_seconds=60)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    gateway_url = "http://127.0.0.1:" + str(server.server_address[1])

    g1, token_g1, email_g1, pw_g1 = person("gestor1")
    g2, token_g2, _, _ = person("gestor2")
    o3, _, _, _ = person("operador3")
    o4, _, _, _ = person("operador4")
    o5, _, _, _ = person("operador5")
    store_a = "c2180000-0000-4000-8000-000000000001"
    store_b = "c2180000-0000-4000-8000-000000000002"
    case_a = "c5180000-0000-4000-8000-000000000001"
    case_b = "c5180000-0000-4000-8000-000000000002"
    def U(value):
        return "'" + str(uuid.UUID(value)) + "'::uuid"

    # Insercao administrativa SOMENTE por postgres no CI, jamais endpoint.
    sql(f"""
    insert into public.atores(id) values ({U(g1)}),({U(g2)}),({U(o3)}),({U(o4)}),({U(o5)});
    insert into public.equipe_prumo_s1(ator_id,estado) values
     ({U(g1)},'ativo'),({U(g2)},'ativo'),({U(o3)},'ativo'),({U(o4)},'ativo'),({U(o5)},'ativo');
    insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values
     ({U(g1)},{U(o3)}),({U(g1)},{U(o4)}),({U(g2)},{U(o5)});
    insert into public.concessionarias(id,nome_operacional) values
     ({U(store_a)},'I18 Loja A'),({U(store_b)},'I18 Loja B');
    insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
     ({U(o3)},{U(store_a)},'operador'),
     ({U(o3)},{U(store_b)},'operador'),
     ({U(o4)},{U(store_a)},'operador'),
     ({U(o4)},{U(store_b)},'operador'),
     ({U(o5)},{U(store_a)},'operador');
    insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
     ('c3180000-0000-4000-8000-000000000001',{U(store_a)},'+5581981501011'),
     ('c3180000-0000-4000-8000-000000000002',{U(store_b)},'+5581981501012');
    insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial) values
     ('c4180000-0000-4000-8000-000000000001',{U(store_a)},
      'c3180000-0000-4000-8000-000000000001','em atendimento pelo operador'),
     ('c4180000-0000-4000-8000-000000000002',{U(store_b)},
      'c3180000-0000-4000-8000-000000000002','em atendimento pelo operador');
    insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id) values
     ({U(case_a)},{U(store_a)},'c3180000-0000-4000-8000-000000000001',
      'c4180000-0000-4000-8000-000000000001'),
     ({U(case_b)},{U(store_b)},'c3180000-0000-4000-8000-000000000002',
      'c4180000-0000-4000-8000-000000000002');
    insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id) values
     ({U(store_a)},{U(case_a)},{U(o3)}),({U(store_b)},{U(case_b)},{U(o3)});
    """)
    prev_a = str(uuid.UUID(sql(f"select id from public.atribuicoes_humanas where caso_id={U(case_a)} and encerrada_em is null")))
    print("PASS S1WITNESS-02: cinco contas GoTrue, gestores por equipe e grants A/B reais")

    status, data = rpc("pausar", token_g2, p_operador=o3,
                       p_motivo_codigo="AUSENCIA_TEMPORARIA")
    blocked(status, "gestor de outra equipe pausou operador")
    print("PASS S1WITNESS-03: gestor alheio negado via JWT real")

    status, data = rpc("mover", token_g1, p_loja=store_a,p_caso=case_a,
                       p_atribuicao_esperada=prev_a,p_destino=o4)
    ok(status,data,"MOVED")
    if data.get("case_id") != case_a:
        raise AssertionError("caso HTTP movimentado incorretamente")
    print("PASS S1WITNESS-04: gestor sem grant da loja move caso A dentro da equipe")

    status, _ = rpc("mover", token_g1, p_loja=store_a,p_caso=case_a,
                    p_atribuicao_esperada=prev_a,p_destino=o4)
    blocked(status, "replay da atribuicao anterior")
    print("PASS S1WITNESS-05: replay de movimento obsoleto negado")

    status, data = rpc("pausar", token_g1,p_operador=o3,
                       p_motivo_codigo="AUSENCIA_TEMPORARIA")
    ok(status,data,"PAUSED_GLOBAL")
    state = sql(f"select estado from public.equipe_prumo_s1 where ator_id={U(o3)}")
    if state != "suspenso":
        raise AssertionError("pausa nao global")
    state_b = sql(f"select operador_id from public.atribuicoes_humanas where caso_id={U(case_b)} and encerrada_em is null")
    if state_b != o4:
        raise AssertionError("redistribuicao B nao chegou ao O4: " + state_b)
    grants = sql(f"select count(*) from public.vinculos_papel_escopo where ator_id={U(o3)}")
    if grants != "2":
        raise AssertionError("pausa apagou grants")
    print("PASS S1WITNESS-06: pausa global redistribuiu B e preservou grants A/B")

    status, _ = rpc("reativar", token_g2,p_operador=o3)
    blocked(status,"G2 reativou O3")
    print("PASS S1WITNESS-07: chefe alheio nao reativa operador")

    status, _ = http("POST","/auth/v1/logout",bearer=token_g1)
    if status not in (200,204):
        raise AssertionError("logout gestor falhou")
    status, _ = rpc("reativar",token_g1,p_operador=o3)
    blocked(status,"gestor com JWT revogado reativou")
    print("PASS S1WITNESS-08: logout GoTrue impede reativacao de equipe")

    status, login = http("POST","/auth/v1/token?grant_type=password",
                         body={"email":email_g1,"password":pw_g1})
    if status != 200:
        raise AssertionError("login novo G1 negado")
    status, data = rpc("reativar",login["access_token"],p_operador=o3)
    ok(status,data,"ACTIVE_GLOBAL")
    if sql(f"select count(*) from public.atribuicoes_humanas where operador_id={U(o3)} and encerrada_em is null") != "0":
        raise AssertionError("retorno recuperou automaticamente carteira antiga")
    if sql(f"select count(*) from prumo_private.s1_pausas_operadores_historico where solicitante_id={U(g1)} and operador_id={U(o3)}") != "2":
        raise AssertionError("historico de autoria real incompleto")
    print("PASS S1WITNESS-09: sessao nova reativa sem recuperar carteira antiga")

    if sql("select (not has_schema_privilege('authenticated','prumo_private','USAGE') and not has_table_privilege('authenticated','auth.sessions','SELECT'))::text") != "true":
        raise AssertionError("privilegios privados ampliados")
    for name in ("s1_mover_atendimento_sessao","s1_pausar_operador_sessao","s1_reativar_operador_sessao"):
        status, _ = http("POST","/rest/v1/rpc/"+name,bearer=login["access_token"],body={})
        if status != 404:
            raise AssertionError("fachada real indevidamente publicada "+name)
    print("PASS S1WITNESS-10: fachadas S1 privadas, SEM pontes RPC publicas")
    print("S1-002/I31: operacoes reais com gateway assinado e sem RPC.")

    # I19-11: não aceita autoria, sessão, role ou SQL no corpo do cliente.
    status, _ = rpc("pausar", token_g2, p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA", actor_id=g1)
    if status != 400:
        raise AssertionError("gateway permitiu campo actor_id extra")
    print("PASS S1WITNESS-11: input proibe actor_id e parametros adicionais")

    # I19-12: service_role não representa usuário GoTrue.
    status, _ = rpc("reativar", os.environ["SERVICE_ROLE_KEY"], p_operador=o3)
    blocked(status, "service_role virou gestor")
    print("PASS S1WITNESS-12: service_role nao atravessa verificacao de usuario GoTrue")

    # I19-13: credencial SQL limitada não pode ler dados/sessões nem executar
    # as funções de negócio privadas diretamente.
    import psycopg
    with psycopg.connect(gateway_dsn, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                select
                  not has_schema_privilege(current_user,'prumo_private','USAGE'),
                  not has_table_privilege(current_user, (
                    select c.oid from pg_catalog.pg_class c
                    join pg_catalog.pg_namespace n on n.oid=c.relnamespace
                    where n.nspname='auth' and c.relname='sessions'
                  ),'SELECT'),
                  not has_schema_privilege(current_user,'prumo_s1_interface','USAGE'),
                  not pg_has_role(current_user,'postgres','MEMBER')
            """)
            flags = cur.fetchone()
            if not all(flag is True for flag in flags):
                raise AssertionError("I19 role SQL elevada, gates=" + str(flags))
            cur.execute("select pg_has_role(current_user,'authenticated','SET')")
            if cur.fetchone()[0] is not False:
                raise AssertionError("role SQL I20 pode assumir authenticated indevidamente")
    print("PASS S1WITNESS-13: login SQL isolado sem authenticated, postgres e acesso direto")

    for name in ("mover", "pausar", "reativar"):
        status, _ = http("POST", "/rest/v1/rpc/s1_i18_" + name,
                          bearer=login["access_token"], body={})
        if status != 404:
            raise AssertionError("ponte I18 indevidamente criada no I19 " + name)
    print("PASS S1WITNESS-14: banco I19 nao possui canarios publicos I18")
    # Testes adversariais com LOGIN SQL comprometido, mas SEM segredo HMAC.
    # Conexão restrita pode conhecer pares (ator,sessao) sem poder se passar
    # pelo backend assinador. Nunca gravar segredo no log nem em migration.
    import psycopg
    from psycopg import Error

    def raw_call(proof):
        with psycopg.connect(gateway_dsn, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_SIGNED, proof)
                return cur.fetchone()[0]

    def denied_proof(proof, label):
        try:
            raw_call(proof)
        except psycopg.Error as e:
            if e.sqlstate != "42501":
                raise AssertionError(label + ": SQLSTATE inesperado " + str(e.sqlstate))
            return
        raise AssertionError(label + ": prova invalida aceita")

    principal = gateway.gotrue.verify("Bearer " + login["access_token"])
    params = (uuid.UUID(o3), "AUSENCIA_TEMPORARIA")
    valid_proof = gateway.proof(principal,"pausar",params)
    invalid_mac = (*valid_proof[:-1], "0" * 64 if valid_proof[-1] != "0" * 64 else "f" * 64)
    denied_proof(invalid_mac,"HMAC ausente/incorreto de login SQL")
    print("PASS S1WITNESS-15: credencial SQL com ator e sessao nao forja HMAC")

    # Prova válida não permite trocar ator/alvo/operador.
    tampered = list(valid_proof)
    tampered[1] = uuid.UUID(g2)
    denied_proof(tuple(tampered), "substituicao do solicitante")
    tampered = list(valid_proof)
    tampered[7] = uuid.UUID(o4)
    denied_proof(tuple(tampered), "substituicao do operador")
    print("PASS S1WITNESS-16: assinatura vincula ator e alvo")

    old_proof = gateway.proof(principal,"pausar",params,issued=int(time.time())-120)
    denied_proof(old_proof, "assinatura com validade vencida")
    future_proof = gateway.proof(principal,"pausar",params,issued=int(time.time())+60)
    denied_proof(future_proof,"assinatura com clock muito adiantado")
    print("PASS S1WITNESS-17: epoch curto bloqueia replay temporal")

    # Primeiro comando assinado tem efeito real; o mesmo nonce é consumido.
    first = raw_call(valid_proof)
    if first.get("outcome") != "PAUSED_GLOBAL":
        raise AssertionError("comando com prova assinada valida nao pausou")
    denied_proof(valid_proof, "reutilizacao de nonce em operação já executada")
    if sql(f"select count(*) from prumo_s1_signed_i20.nonces where id='{valid_proof[-2]}'::uuid") != "1":
        raise AssertionError("nonce nao foi consumido exatamente uma vez")
    status, response = rpc("reativar", login["access_token"], p_operador=o3)
    ok(status, response, "ACTIVE_GLOBAL")
    print("PASS S1WITNESS-18: nonce nao reutilizavel, efeito unico confirmado")

    # Simula uma prova assinada POR ERRO para sessão antiga já revogada:
    # helper I15 deve revalidar auth.sessions mesmo com HMAC correta.
    mid = token_g1.split(".")[1]
    old_claims = json.loads(base64.urlsafe_b64decode(mid + "=" * (-len(mid) % 4)))
    revoked = Principal(uuid.UUID(g1), uuid.UUID(old_claims["session_id"]))
    revoked_proof = gateway.proof(revoked,"pausar",params)
    denied_proof(revoked_proof, "sessao GoTrue revogada com HMAC valida")
    print("PASS S1WITNESS-19: HMAC nao ignora revogacao de sessao GoTrue")

    # Sem SET ROLE authenticated, login SQL nao cria GUC util para executar as
    # funcoes antigas. Nem possui SELECT em chaves nem bypass de nonce.
    with psycopg.connect(gateway_dsn, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                select
                  not has_schema_privilege(current_user,'prumo_private','USAGE'),
                  not has_schema_privilege(current_user,'prumo_s1_interface','USAGE'),
                  not pg_has_role(current_user,'authenticated','MEMBER'),
                  not has_table_privilege(current_user, (
                    select c.oid from pg_catalog.pg_class c
                    join pg_catalog.pg_namespace n on n.oid=c.relnamespace
                    where n.nspname='prumo_s1_signed_i20' and c.relname='chaves'
                  ), 'SELECT')
            """)
            if not all(v is True for v in cur.fetchone()):
                raise AssertionError("login I20 tem privilegios nao autorizados")
    try:
        with psycopg.connect(gateway_dsn, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("set local role authenticated")
    except psycopg.Error as e:
        if e.sqlstate != "42501":
            raise AssertionError("SET ROLE erro inesperado " + str(e.sqlstate))
    else:
        raise AssertionError("login I20 conseguiu assumir authenticated")
    print("PASS S1WITNESS-20: login SQL nao assume role JWT nem le segredo")

    # Revogar chave no postgres efemero deve bloquear comando, sem writes S1.
    sql("select prumo_s1_signed_i20.revogar_chave_i24("
        f"'{key_id}'::uuid,1,'ROTACAO_PLANEJADA')")
    status, _ = rpc("pausar", login["access_token"], p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA")
    blocked(status,"chave de assinatura revogada")
    if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid") != "ativo":
        raise AssertionError("chave revogada alterou equipe")
    print("PASS S1WITNESS-21: chave revogada bloqueia sem efeito de negocio")


    # I21-22: owner da fachada assinada nao e o superprivilegiado postgres.
    owner = sql("""
    select pg_catalog.pg_get_userbyid(p.proowner)
    from pg_catalog.pg_proc p
    where p.oid='prumo_s1_signed_i20.invocar(
    text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)'::regprocedure
    """)
    if owner != "prumo_s1_i21_executor":
        raise AssertionError("I21 invocar continua owned por " + owner)
    owners = sql("""
    select string_agg(c.relname||'='||pg_catalog.pg_get_userbyid(c.relowner),','
     order by c.relname)
    from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid=c.relnamespace
    where n.nspname='prumo_s1_signed_i20'
     and c.relname in ('chaves','nonces')
    """)
    if owners != "chaves=prumo_s1_i22_custodio,nonces=prumo_s1_i21_executor":
        raise AssertionError("I22 tabelas com custodias erradas: " + owners)
    print("PASS S1WITNESS-22: executor possui invocar/nonce; custodio possui chaves")

    # I21-23: role não é de login, nem herda autoridade e não tem poderes de
    # alterar a estrutura, contornar RLS ou criar outros papéis.
    flags = sql("""
    select (
      not rolcanlogin and not rolinherit and not rolsuper and not rolcreatedb
      and not rolcreaterole and not rolreplication and not rolbypassrls
    )::text from pg_catalog.pg_roles where rolname='prumo_s1_i21_executor'
    """)
    if flags != "true":
        raise AssertionError("I21 executor com privilegios globais inesperados")
    print("PASS S1WITNESS-23: executor isolado sem login, superuser ou bypassrls")

    # I21-24: o login SQL não pode se tornar executor, consultar chaves ou
    # modificar nonces. O esquema dedicado nao pode receber CREATE.
    with psycopg.connect(gateway_dsn, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("""
              select
                not pg_has_role(current_user,'prumo_s1_i21_executor','MEMBER'),
                not pg_has_role(current_user,'prumo_s1_i21_executor','SET'),
                not has_table_privilege(current_user,(
                  select c.oid from pg_catalog.pg_class c
                  join pg_catalog.pg_namespace n on n.oid=c.relnamespace
                  where n.nspname='prumo_s1_signed_i20' and c.relname='nonces'
                ),'INSERT'),
                not has_schema_privilege(current_user,'prumo_s1_signed_i20','CREATE')
            """)
            if not all(item is True for item in cur.fetchone()):
                raise AssertionError("I21 login SQL contorna ownership")
    try:
        with psycopg.connect(gateway_dsn, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("set local role prumo_s1_i21_executor")
    except psycopg.Error as e:
        if e.sqlstate != "42501":
            raise AssertionError("I21 SET ROLE erro inesperado " + str(e.sqlstate))
    else:
        raise AssertionError("I21 login SQL assumiu role definer")
    print("PASS S1WITNESS-24: login SQL nao consegue SET ROLE executor nem DML chaves")

    # I21-25: role proprietaria NAO pode ler/sobrescrever dominio S0/S1,
    # criar objetos no schema assinado ou ler auth.sessions diretamente.
    isolated = sql("""
    select (
     not has_table_privilege('prumo_s1_i21_executor','public.leads_loja','SELECT')
     and not has_table_privilege('prumo_s1_i21_executor','public.equipe_prumo_s1','UPDATE')
     and not has_table_privilege('prumo_s1_i21_executor','auth.sessions','SELECT')
     and not has_schema_privilege('prumo_s1_i21_executor','prumo_private','USAGE')
     and not has_schema_privilege('prumo_s1_i21_executor','prumo_s1_signed_i20','CREATE')
     and pg_has_role('postgres','prumo_s1_i21_executor','SET')
    )::text
    """)
    if isolated != "true":
        raise AssertionError("I21 role obteve acesso amplo ao dominio")
    print("PASS S1WITNESS-25: owner novo sem acesso bruto a dados ou funcoes privadas")

    # I21-26: as tres funcoes legadas continuam propriedade de postgres;
    # nenhum schema public habilitado para gestao.
    legacy = sql("""
    select (
     count(*)=3
     and bool_and(pg_catalog.pg_get_userbyid(p.proowner)='postgres')
    ) from pg_catalog.pg_proc p
    join pg_catalog.pg_namespace n on n.oid=p.pronamespace
    where n.nspname='prumo_s1_interface'
     and p.proname in ('s1_mover_atendimento_sessao',
        's1_pausar_operador_sessao','s1_reativar_operador_sessao')
    """)
    if legacy != "t":
        raise AssertionError("I21 alterou owner das fachadas I14")
    print("PASS S1WITNESS-26: regras e owners I14 preservados")

    # I21-27: apos desativacao da chave antiga (S1KEY-21), uma chave NOVA,
    # exclusivamente gerada no runner e provisionada por postgres, restaura
    # autorizacao: verifica que menor privilegio nao quebrou rotacao.
    new_key_id = uuid.uuid4()
    new_secret = secrets.token_bytes(32)
    sql(
        "select prumo_s1_signed_i20.provisionar_chave_i24("
        f"'{new_key_id}'::uuid, decode('{new_secret.hex()}','hex'), "
        "clock_timestamp() - interval '1 minute', clock_timestamp() + interval '10 minutes', "
        "'ROTACAO_PLANEJADA')"
    )
    gateway.key_id = new_key_id
    gateway.signing_key = new_secret
    status, data = rpc("pausar",login["access_token"],p_operador=o3,
                       p_motivo_codigo="AUSENCIA_TEMPORARIA")
    ok(status,data,"PAUSED_GLOBAL")
    status, data = rpc("reativar",login["access_token"],p_operador=o3)
    ok(status,data,"ACTIVE_GLOBAL")
    print("PASS S1WITNESS-27: chave nova rotacionada sem privilegio postgres no invocar")

    # I22-28: proprietario da funcao de verificacao nao possui comandos S1,
    # e seu corpo nao devolve segredo. A custodia e NOLOGIN e segregada.
    verifier_owner = sql("""
    select pg_catalog.pg_get_userbyid(p.proowner)
    from pg_catalog.pg_proc p
    where p.oid='prumo_s1_signed_i20.verificar_hmac(
    text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)'::regprocedure
    """)
    if verifier_owner != "prumo_s1_i22_custodio":
        raise AssertionError("I22 verificador com owner indevido")
    flag = sql("""
    select (not rolcanlogin and not rolinherit and not rolsuper
     and not rolbypassrls and not rolcreaterole and not rolcreatedb
     and not rolreplication)::text
    from pg_catalog.pg_roles where rolname='prumo_s1_i22_custodio'
    """)
    if flag != "true":
        raise AssertionError("I22 role custodio insegura")
    print("PASS S1WITNESS-28: verificador e chave com custodio NOLOGIN independente")

    # I22-29: executor so chama verificador; SELECT/UPDATE da chave sao negados.
    acl=sql("""
    select (
     not has_table_privilege('prumo_s1_i21_executor','prumo_s1_signed_i20.chaves','SELECT')
     and not has_table_privilege('prumo_s1_i21_executor','prumo_s1_signed_i20.chaves','UPDATE')
     and not has_table_privilege('prumo_s1_i21_executor','prumo_s1_signed_i20.chaves','DELETE')
     and not has_table_privilege('prumo_s1_i21_executor','prumo_s1_signed_i20.chaves','INSERT')
     and has_function_privilege('prumo_s1_i21_executor',
       'prumo_s1_signed_i20.verificar_hmac(text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)','EXECUTE')
    )::text
    """)
    if acl != "true":
        raise AssertionError("I22 executor obteve acesso direto a chave")
    print("PASS S1WITNESS-29: executor sem SELECT/DML na chave, apenas EXECUTE do verificador")

    # I22-30: custodia da chave nao pode consumir nonce, operar S1 nem consultar
    # dados de negocio. Nenhuma role acessa o segredo por ponte publica.
    custody=sql("""
    select (
     not has_table_privilege('prumo_s1_i22_custodio','prumo_s1_signed_i20.nonces','INSERT')
     and not has_table_privilege('prumo_s1_i22_custodio','public.leads_loja','SELECT')
     and not has_table_privilege('prumo_s1_i22_custodio','auth.sessions','SELECT')
     and not has_schema_privilege('prumo_s1_i22_custodio','prumo_s1_interface','USAGE')
     and not has_function_privilege('prumo_s1_i22_custodio',
      'prumo_s1_signed_i20.invocar(text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)','EXECUTE')
     and not pg_has_role('prumo_s1_i21_executor','prumo_s1_i22_custodio','SET')
     and not pg_has_role('prumo_s1_signed_login_ci','prumo_s1_i22_custodio','SET')
    )::text
    """)
    if custody != "true":
        raise AssertionError("I22 custodio pode operar negocio/sessao")
    print("PASS S1WITNESS-30: custodio sem interfaces S1, auth.sessions e nonce")

    # I22-31: com a role do executor (somente assumivel por admin CI),
    # SELECT e UPDATE direto na chave devem falhar, sem vazamento do segredo.
    def denied_role_query(role, statement):
        try:
            sql("begin; set local role " + role + "; " + statement + "; commit;")
        except RuntimeError as e:
            if "permission denied" not in str(e):
                raise AssertionError("I22 SQL negação inesperada: " + str(e)[-450:])
            return
        raise AssertionError("I22 comando foi autorizado indevidamente")
    denied_role_query("prumo_s1_i21_executor",
        "select segredo from prumo_s1_signed_i20.chaves limit 1")
    denied_role_query("prumo_s1_i21_executor",
        f"update prumo_s1_signed_i20.chaves set ativo=true where id='{new_key_id}'::uuid")
    print("PASS S1WITNESS-31: executor não exfiltra nem altera chave por SQL")

    # I22-32: sob login de aplicação, SET ROLE de custodio falha e a função
    # verificadora não fica exposta ao cliente (apenas invocar).
    with psycopg.connect(gateway_dsn, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("""
              select
               not pg_has_role(current_user,'prumo_s1_i22_custodio','SET'),
               not has_function_privilege(current_user,
                 'prumo_s1_signed_i20.verificar_hmac(
                  text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)',
                 'EXECUTE'),
               not has_table_privilege(current_user, (
                 select c.oid from pg_catalog.pg_class c
                 join pg_catalog.pg_namespace n on n.oid=c.relnamespace
                 where n.nspname='prumo_s1_signed_i20' and c.relname='chaves'
               ), 'SELECT')
            """)
            if not all(x is True for x in cur.fetchone()):
                raise AssertionError("I22 gateway SQL ganhou acesso a custodio")
    print("PASS S1WITNESS-32: cliente SQL sem SET ROLE custodio ou EXECUTE verificador")

    # I22-33: nem mesmo o custodio possui CREATE no schema nem o executor ganha
    # ownership de chave apos a rotação administrativa.
    ddl=sql("""
    select (
     not has_schema_privilege('prumo_s1_i22_custodio','prumo_s1_signed_i20','CREATE')
     and not has_schema_privilege('prumo_s1_i21_executor','prumo_s1_signed_i20','CREATE')
     and pg_catalog.pg_get_userbyid(
       (select c.relowner from pg_catalog.pg_class c
         where c.oid='prumo_s1_signed_i20.chaves'::regclass))='prumo_s1_i22_custodio'
    )::text
    """)
    if ddl != "true":
        raise AssertionError("I22 custodia mudou apos rotacao")
    print("PASS S1WITNESS-33: ownership e CREATE seguem separados apos rotacao")

    # I23: Requisicoes HTTP malformadas NAO chegam ao GoTrue nem ao banco.
    # Estados comerciais devem permanecer intactos apos todos os bloqueios.
    import http.client as http_client
    def hostile_http(headers=None, body=None, method="POST", path="/s1/pausar",
                     duplicate=()):
        conn=http_client.HTTPConnection("127.0.0.1",server.server_address[1],timeout=6)
        payload = (body if body is not None else
                   json.dumps({"operador_id":o3,"motivo_codigo":"AUSENCIA_TEMPORARIA"}))
        b=payload.encode() if isinstance(payload,str) else payload
        base_headers={
            "Host": "127.0.0.1:" + str(server.server_address[1]),
            "Authorization": "Bearer " + login["access_token"],
            "Content-Type": "application/json",
            "Content-Length": str(len(b))
        }
        base_headers.update(headers or {})
        conn.putrequest(method,path,skip_host=True,skip_accept_encoding=True)
        for name,value in base_headers.items():
            conn.putheader(name,value)
        for name,value in duplicate:
            conn.putheader(name,value)
        conn.endheaders()
        if method=="POST" and b:
            conn.send(b)
        rsp=conn.getresponse()
        raw=rsp.read()
        status=rsp.status
        hdrs=dict(rsp.getheaders())
        conn.close()
        return status, json.loads(raw), hdrs

    status,data,headers=hostile_http(method="GET",body="")
    if status!=405 or headers.get("Allow")!="POST":
        raise AssertionError("I23 GET nao foi negado")
    print("PASS S1WITNESS-34: somente POST e permitido")

    status,data,headers=hostile_http(headers={"Origin":"https://evil.example"})
    if status!=403 or "Access-Control-Allow-Origin" in headers:
        raise AssertionError("I23 origem externa autorizada")
    print("PASS S1WITNESS-35: Origin externo e CORS cross-site proibidos")

    status,data,_=hostile_http(headers={"Cookie":"auth=forged"})
    if status!=400:
        raise AssertionError("I23 cookie em vez de Bearer nao negado")
    print("PASS S1WITNESS-36: cookies desabilitados e Bearer independente")

    status,data,_=hostile_http(headers={"X-Forwarded-For":"127.0.0.1"})
    if status!=400:
        raise AssertionError("I23 header proxy do usuario foi confiado")
    print("PASS S1WITNESS-37: forwarded headers de cliente rejeitados")

    status,data,_=hostile_http(duplicate=(("Authorization", "Bearer " + token_g2),))
    if status!=400:
        raise AssertionError("I23 autorizacoes ambiguas aceitas")
    print("PASS S1WITNESS-38: Authorization duplicado negado")

    status,data,_=hostile_http(body='{"operador_id":"'+o3+'","operador_id":"'+o4+'","motivo_codigo":"AUSENCIA_TEMPORARIA"}')
    if status!=400:
        raise AssertionError("I23 JSON com chaves duplicadas aceito")
    print("PASS S1WITNESS-39: parser JSON rejeita propriedades repetidas")

    status,data,headers=hostile_http(headers={"Transfer-Encoding":"chunked"})
    if status!=400:
        raise AssertionError("I23 transfer encoding ambigua aceita")
    if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
        raise AssertionError("I23 pedido hostil causou pausa")
    if headers.get("Cache-Control")!="no-store" or headers.get("X-Content-Type-Options")!="nosniff":
        raise AssertionError("I23 faltou header de protecao")
    print("PASS S1WITNESS-40: TE ambigua rejeitada, sem mudanca comercial e com no-store")

    # I24 - ciclo de vida versionado e auditoria, sem segredo em logs/HTTP.
    # Credencial administrativa é APENAS postgres local do runner efêmero.
    import concurrent.futures

    def admin_call(statement, expected_state=None):
        import psycopg
        try:
            with psycopg.connect(db, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute(statement)
                    if expected_state is not None:
                        raise AssertionError("I24 operacao proibida executou: " + expected_state)
                    return cur.fetchone()[0] if cur.description else None
        except psycopg.Error as e:
            if expected_state is None:
                raise
            if e.sqlstate != expected_state:
                raise AssertionError("I24 SQLSTATE incorreto: " + str(e.sqlstate)) from None
            return None

    # I24-41: provisionamento e revogacao registrados sem dados de clientes.
    events = sql("""
    select string_agg(evento||':'||motivo_codigo||':'||versao,',' order by id)
    from prumo_s1_signed_i20.auditoria_chaves_i24
    """)
    if events != "PROVISIONADA:BOOTSTRAP_CI:1,REVOGADA:ROTACAO_PLANEJADA:2,PROVISIONADA:ROTACAO_PLANEJADA:1":
        raise AssertionError("I24 historico incorreto " + events)
    print("PASS S1WITNESS-41: trilha inicia, revoga e rotaciona sem conter segredo")

    # I24-42: stale version perde mesmo com requisicao administrativa legitima.
    admin_call(
        "select prumo_s1_signed_i20.revogar_chave_i24("
        f"'{key_id}'::uuid,1,'ROTACAO_PLANEJADA')",
        "40001")
    print("PASS S1WITNESS-42: compare-and-swap rejeita versao antiga")

    # I24-43: mesmo com a versao atual, chave revogada nao volta a ser ativa.
    admin_call(
        "select prumo_s1_signed_i20.revogar_chave_i24("
        f"'{key_id}'::uuid,2,'ROTACAO_PLANEJADA')",
        "22023")
    print("PASS S1WITNESS-43: estado revogado terminal pelo contrato administrativo")

    # I24-44: motivo arbitrario rejeitado, sem escrita em auditoria.
    admin_call(
        "select prumo_s1_signed_i20.revogar_chave_i24("
        f"'{new_key_id}'::uuid,1,'TEXTO_LIVRE_NAO_PERMITIDO')",
        "22023")
    if sql("select count(*) from prumo_s1_signed_i20.auditoria_chaves_i24")!="3":
        raise AssertionError("I24 negativa criou evento")
    print("PASS S1WITNESS-44: motivo livre bloqueado, sem evento espurio")

    # I24-45: chave curta e janela temporal invalida nao sao provisionadas.
    bad_id=uuid.uuid4()
    admin_call(
      "select prumo_s1_signed_i20.provisionar_chave_i24("
      f"'{bad_id}'::uuid,decode('abcd','hex'),"
      "clock_timestamp(),clock_timestamp()+interval '10 minutes',"
      "'ROTACAO_PLANEJADA')","22023")
    admin_call(
      "select prumo_s1_signed_i20.provisionar_chave_i24("
      f"'{bad_id}'::uuid,decode('{secrets.token_bytes(32).hex()}','hex'),"
      "clock_timestamp(),clock_timestamp()-interval '1 minute',"
      "'ROTACAO_PLANEJADA')","22023")
    if sql(f"select count(*) from prumo_s1_signed_i20.chaves where id='{bad_id}'::uuid")!="0":
        raise AssertionError("I24 material rejeitado persistiu")
    print("PASS S1WITNESS-45: bytes insuficientes e validade incorreta rejeitados")

    # I24-46: chave antiga segue valida durante sobreposicao. Nova chave
    # nao entra no gateway ate que esteja presente no verificador.
    overlap_id=uuid.uuid4()
    overlap_secret=secrets.token_bytes(32)
    admin_call(
        "select prumo_s1_signed_i20.provisionar_chave_i24("
        f"'{overlap_id}'::uuid,decode('{overlap_secret.hex()}','hex'),"
        "clock_timestamp()-interval '1 minute',"
        "clock_timestamp()+interval '10 minutes','ROTACAO_PLANEJADA')")
    status,data=rpc("pausar",login["access_token"],p_operador=o3,
                   p_motivo_codigo="AUSENCIA_TEMPORARIA")
    ok(status,data,"PAUSED_GLOBAL")
    status,data=rpc("reativar",login["access_token"],p_operador=o3)
    ok(status,data,"ACTIVE_GLOBAL")
    gateway.key_id=overlap_id
    gateway.signing_key=overlap_secret
    status,data=rpc("pausar",login["access_token"],p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA")
    ok(status,data,"PAUSED_GLOBAL")
    status,data=rpc("reativar",login["access_token"],p_operador=o3)
    ok(status,data,"ACTIVE_GLOBAL")
    print("PASS S1WITNESS-46: overlap e troca controlada entre duas chaves validas")

    # I24-47: revoga a chave anterior sem interromper a nova.
    admin_call(
        "select prumo_s1_signed_i20.revogar_chave_i24("
        f"'{new_key_id}'::uuid,1,'ROTACAO_PLANEJADA')")
    gateway.key_id=new_key_id
    gateway.signing_key=new_secret
    status,_=rpc("pausar",login["access_token"],p_operador=o3,
                  p_motivo_codigo="AUSENCIA_TEMPORARIA")
    blocked(status,"chave antiga permaneceu valida")
    gateway.key_id=overlap_id
    gateway.signing_key=overlap_secret
    status,data=rpc("pausar",login["access_token"],p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA")
    ok(status,data,"PAUSED_GLOBAL")
    status,data=rpc("reativar",login["access_token"],p_operador=o3)
    ok(status,data,"ACTIVE_GLOBAL")
    print("PASS S1WITNESS-47: chave anterior revogada e sucessora mantida operacional")

    # I24-48: login SQL nao pode executar APIs de rotacao, nem SELECT audit.
    import psycopg
    with psycopg.connect(gateway_dsn, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("""
            select
              not has_function_privilege(current_user,
               'prumo_s1_signed_i20.provisionar_chave_i24(
                  uuid,bytea,timestamptz,timestamptz,text)','EXECUTE'),
              not has_function_privilege(current_user,
               'prumo_s1_signed_i20.revogar_chave_i24(uuid,bigint,text)','EXECUTE'),
              not has_table_privilege(current_user,
               'prumo_s1_signed_i20.auditoria_chaves_i24','SELECT'),
              not pg_has_role(current_user,'prumo_s1_i22_custodio','SET')
            """)
            if not all(x is True for x in cur.fetchone()):
                raise AssertionError("I24 acesso indevido pelo SQL gateway")
    print("PASS S1WITNESS-48: login SQL sem APIs administrativas ou auditoria")

    # I24-49: mesmo id+versao em duas transacoes: apenas UMA revogacao vence.
    race_id=uuid.uuid4()
    admin_call(
        "select prumo_s1_signed_i20.provisionar_chave_i24("
        f"'{race_id}'::uuid,decode('{secrets.token_bytes(32).hex()}','hex'),"
        "clock_timestamp()-interval '1 minute',"
        "clock_timestamp()+interval '10 minutes','ROTACAO_PLANEJADA')")
    barrier=threading.Barrier(2)
    def compete(_):
        barrier.wait(timeout=10)
        try:
            admin_call("select prumo_s1_signed_i20.revogar_chave_i24("
                       f"'{race_id}'::uuid,1,'RISCO_COMPROMETIMENTO')")
            return "APPLIED"
        except psycopg.Error as err:
            return err.sqlstate
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(compete,range(2)))
    if sorted(outcomes)!=["40001","APPLIED"]:
        raise AssertionError("I24 CAS concorrente falhou: " + str(outcomes))
    if sql(f"select count(*) from prumo_s1_signed_i20.auditoria_chaves_i24 where chave_id='{race_id}'::uuid and evento='REVOGADA'")!="1":
        raise AssertionError("I24 dupla revogacao entrou na auditoria")
    print("PASS S1WITNESS-49: concorrencia CAS serializada, revogacao e evento uma vez")

    # I24-50: auditoria sem campos sensiveis e sem privilegios do executor.
    columns=sql("""
    select string_agg(column_name,',' order by ordinal_position)
    from information_schema.columns
    where table_schema='prumo_s1_signed_i20' and table_name='auditoria_chaves_i24'
    """)
    if columns!="id,chave_id,evento,versao,motivo_codigo,ocorrido_em":
        raise AssertionError("I24 audit contem campos nao permitidos: "+columns)
    acl=sql("""
    select (
     not has_table_privilege('prumo_s1_i21_executor',
      'prumo_s1_signed_i20.auditoria_chaves_i24','INSERT')
     and not has_table_privilege('prumo_s1_i21_executor',
      'prumo_s1_signed_i20.auditoria_chaves_i24','SELECT')
     and not has_schema_privilege('prumo_s1_i22_custodio',
      'prumo_s1_signed_i20','CREATE')
     and pg_catalog.pg_get_userbyid(
      (select c.relowner from pg_catalog.pg_class c
       where c.oid='prumo_s1_signed_i20.auditoria_chaves_i24'::regclass)
     )='prumo_s1_i22_custodio'
    )::text
    """)
    if acl!="true":
        raise AssertionError("I24 segregacao da auditoria nao comprovada")
    print("PASS S1WITNESS-50: auditoria minimizada e segregada do executor")

    server.shutdown()
    server.server_close()

    # I25 - somente no CI: processo assinador separado via IPC, sem chave em
    # LocalSeparatedSignerGateway. Supervisor + control pipe ficam no runner.
    # O processo do signer recebe bytes de chave pela control pipe local,
    # nunca do HTTP e nunca retorna segredo.
    signer_key_id = uuid.uuid4()
    signer_secret = secrets.token_bytes(32)
    admin_call(
     "select prumo_s1_signed_i20.provisionar_chave_i24("
     f"'{signer_key_id}'::uuid,decode('{signer_secret.hex()}','hex'),"
     "clock_timestamp()-interval '1 minute',"
     "clock_timestamp()+interval '10 minutes','ROTACAO_PLANEJADA')")
    signer = LocalSignerSupervisor()
    assert signer.load(signer_key_id, signer_secret)
    split_gateway=LocalSeparatedSignerGateway(
     gateway_dsn, SupabaseGoTrueVerifier(api,anon),
     signer=signer.client,key_id=signer_key_id)
    if "signing_key" in vars(split_gateway) or "_control" in vars(split_gateway):
        raise AssertionError("I25 gateway tem segredo ou canal privilegiado")
    server = serve_http_policy_local(split_gateway,max_requests=150,window_seconds=60)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    gateway_url = "http://127.0.0.1:" + str(server.server_address[1])
    print("PASS S1WITNESS-51: chave HMAC fora do objeto gateway e controle fora do HTTP")

    status,data=rpc("pausar",login["access_token"],p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA")
    ok(status,data,"PAUSED_GLOBAL")
    status,data=rpc("reativar",login["access_token"],p_operador=o3)
    ok(status,data,"ACTIVE_GLOBAL")
    print("PASS S1WITNESS-52: assinador filho separado permite gestao GoTrue real")

    signer.terminate()
    status,data=rpc("pausar",login["access_token"],p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA")
    if status!=503 or data.get("error")!="UNAVAILABLE":
        raise AssertionError("I25 queda de processo assinador nao falhou fechado: "+str(status))
    if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
        raise AssertionError("I25 falha do assinador alterou operador")
    print("PASS S1WITNESS-53: perda do processo bloqueia HTTP e preserva equipe")

    # Reiniciar processo NAO lhe da acesso as chaves do processo encerrado.
    signer_recovered=LocalSignerSupervisor()
    split_gateway.signer=signer_recovered.client
    status,data=rpc("pausar",login["access_token"],p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA")
    if status!=403 or data.get("error")!="DENIED":
        raise AssertionError("I25 nova instancia recuperou chave sem provisionamento")
    print("PASS S1WITNESS-54: processo novo inicia sem segredo antigo")

    # A recuperacao nao reativa chaves antigas nem reutiliza identificadores.
    # Provisionar id novo em DB, carregar bytes do runner no processo novo,
    # so entao mudar key id no gateway. Simulacao, SEM KMS/Vault/backup real.
    recovery_id=uuid.uuid4()
    recovery_secret=secrets.token_bytes(32)
    admin_call(
     "select prumo_s1_signed_i20.provisionar_chave_i24("
     f"'{recovery_id}'::uuid,decode('{recovery_secret.hex()}','hex'),"
     "clock_timestamp()-interval '1 minute',"
     "clock_timestamp()+interval '10 minutes','FALHA_OPERACIONAL')")
    if not signer_recovered.load(recovery_id,recovery_secret):
        raise AssertionError("I25 processo novo nao recebeu chave sintetica")
    split_gateway.key_id=recovery_id
    status,data=rpc("pausar",login["access_token"],p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA")
    ok(status,data,"PAUSED_GLOBAL")
    status,data=rpc("reativar",login["access_token"],p_operador=o3)
    ok(status,data,"ACTIVE_GLOBAL")
    print("PASS S1WITNESS-55: nova chave valida recupera operacoes apos pane")

    # Uma assinatura gerada por processo reativado na chave velha ainda e
    # negada no PostgreSQL apos revogacao pelo custodio.
    admin_call("select prumo_s1_signed_i20.revogar_chave_i24("
               f"'{signer_key_id}'::uuid,1,'FALHA_OPERACIONAL')")
    if not signer_recovered.load(signer_key_id,signer_secret):
        raise AssertionError("I25 test local nao carregou chave comprometida")
    split_gateway.key_id=signer_key_id
    status,data=rpc("pausar",login["access_token"],p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA")
    if status!=403:
        raise AssertionError("I25 banco aceitou assinatura de chave revogada")
    split_gateway.key_id=recovery_id
    print("PASS S1WITNESS-56: chave revogada no banco continua negada apesar de HMAC correta")

    # Mesmo durante pane, rejeicao de Bearer/GoTrue antecede qualquer IPC
    # (simulamos signer indisponivel para verificar a ordem dos bloqueios).
    old_client=split_gateway.signer
    class DenySigningOnUse:
        def sign(self,*_args):
            raise AssertionError("signer nao poderia ser chamado com Bearer invalido")
    split_gateway.signer=DenySigningOnUse()
    status,data=rpc("pausar","invalid-token",p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA")
    if status!=403:
        raise AssertionError("I25 bearer invalido alcançou assinador")
    split_gateway.signer=old_client
    print("PASS S1WITNESS-57: autenticacao GoTrue acontece antes de qualquer assinatura")

    # O canal de controle tem efeito sobre assinador, mas nao pode ser invocado
    # pela interface HTTP do gateway. Revogacao no assinador e fail-closed.
    if not signer_recovered.revoke(recovery_id):
        raise AssertionError("I25 revogacao em memoria negada")
    status,data=rpc("pausar",login["access_token"],p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA")
    if status!=403:
        raise AssertionError("I25 signer em memoria revogado permitiu pausa")
    print("PASS S1WITNESS-58: revogacao em processo impede assinatura sem tocar dominio")

    # Recuperacao invalida/duplicada: o processo nao altera segredo de uma chave
    # ja carregada. Sem chave nova, fail-closed.
    if signer_recovered.load(signer_key_id,bytes(reversed(range(32)))):
        raise AssertionError("I25 chave preexistente foi sobrescrita")
    status,data=rpc("pausar",login["access_token"],p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA")
    if status!=403:
        raise AssertionError("I25 sobrescrita de signer reabilitou comando")
    print("PASS S1WITNESS-59: id da chave nao admite troca silenciosa em memoria")

    audit_count=sql(f"""
    select count(*) from prumo_s1_signed_i20.auditoria_chaves_i24
    where chave_id in ('{signer_key_id}'::uuid,'{recovery_id}'::uuid)
     and motivo_codigo='FALHA_OPERACIONAL'
    """)
    if audit_count!="2":
        raise AssertionError("I25 auditoria recovery incompleta: "+audit_count)
    if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
        raise AssertionError("I25 recuperacao deixou equipe pausada")
    print("PASS S1WITNESS-60: auditoria minimizada e estado da equipe preservados")

    server.shutdown()
    server.server_close()
    signer_recovered.close()
    signer.close()
    # I26: cada SIGN requer agora GoTrue independente dentro do worker,
    # ainda que atacante tenha pipe de SIGN e credencial SQL. Sem token real
    # nao e possivel assinar identidade/sessao escolhida pelo atacante.
    verified_key=uuid.uuid4()
    verified_secret=secrets.token_bytes(32)
    admin_call(
     "select prumo_s1_signed_i20.provisionar_chave_i24("
     f"'{verified_key}'::uuid,decode('{verified_secret.hex()}','hex'),"
     "clock_timestamp()-interval '1 minute',"
     "clock_timestamp()+interval '10 minutes','ROTACAO_PLANEJADA')")
    verified_signer=LocalSignerSupervisor(independent_auth_url=api,
                                         publishable_key=anon)
    if not verified_signer.load(verified_key,verified_secret):
        raise AssertionError("I26 signer nao recebeu chave sintética")
    checked_gateway=LocalIndependentlyAuthenticatedGateway(
        gateway_dsn,SupabaseGoTrueVerifier(api,anon),
        signer=verified_signer.client,key_id=verified_key)
    if "signing_key" in vars(checked_gateway) or "_control" in vars(checked_gateway):
        raise AssertionError("I26 gateway expoe material ou canal de controle")
    server = serve_http_policy_local(checked_gateway,max_requests=200,window_seconds=60)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    gateway_url = "http://127.0.0.1:" + str(server.server_address[1])
    print("PASS S1WITNESS-61: child GoTrue configurado local, sem segredo no gateway")

    status,data=rpc("pausar",login["access_token"],p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA")
    ok(status,data,"PAUSED_GLOBAL")
    status,data=rpc("reativar",login["access_token"],p_operador=o3)
    ok(status,data,"ACTIVE_GLOBAL")
    print("PASS S1WITNESS-62: gestor autenticado opera com segunda validacao GoTrue")

    gp=SupabaseGoTrueVerifier(api,anon).verify("Bearer "+login["access_token"])
    args=_action_args("pausar",(uuid.UUID(o3),"AUSENCIA_TEMPORARIA"))
    def material_for(actor,session):
        return _proof_material("PAUSAR",actor,session,args,
                               int(time.time()),uuid.uuid4())

    try:
        verified_signer.client.sign(verified_key,
                                   material_for(gp.actor_id,gp.session_id))
    except Denied:
        pass
    else:
        raise AssertionError("I26 IPC assinou sem bearer")
    print("PASS S1WITNESS-63: atacante com pipe e SQL nao assina sem Bearer")

    try:
        verified_signer.client.sign(verified_key,
                                   material_for(gp.actor_id,gp.session_id),
                                   "Bearer invalidstring")
    except Denied:
        pass
    else:
        raise AssertionError("I26 IPC aceitou bearer invalido")
    print("PASS S1WITNESS-64: token falso no canal IPC bloqueado pelo proprio filho")

    try:
        verified_signer.client.sign(verified_key,
                                   material_for(uuid.UUID(g2),gp.session_id),
                                   "Bearer "+login["access_token"])
    except Denied:
        pass
    else:
        raise AssertionError("I26 assinou actor_id forjado")
    print("PASS S1WITNESS-65: assinatura cruza sub do GoTrue com ator do material")

    try:
        verified_signer.client.sign(verified_key,
                                   material_for(gp.actor_id,uuid.uuid4()),
                                   "Bearer "+login["access_token"])
    except Denied:
        pass
    else:
        raise AssertionError("I26 assinou sessao inventada")
    print("PASS S1WITNESS-66: assinatura cruza session_id do GoTrue com material")

    try:
        verified_signer.client.sign(verified_key,
                                   material_for(gp.actor_id,gp.session_id),
                                   "Bearer "+token_g2)
    except Denied:
        pass
    else:
        raise AssertionError("I26 token autentico de outro usuario forjou gestor")
    print("PASS S1WITNESS-67: bearer de outro usuario nao personifica gestor")

    # Um bearer autentico da outra equipe pode obter HMAC somente para seu
    # proprio ator; a regra gerencial I14 continua negando a equipe alheia.
    status,data=rpc("pausar",token_g2,p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA")
    blocked(status,"equipe alheia nao pode pausar mesmo com assinatura I26")
    if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
        raise AssertionError("I26 token outra equipe afetou operador")
    print("PASS S1WITNESS-68: sessao autentica de equipe alheia falha em RBAC DB")

    offline_key=uuid.uuid4()
    offline_secret=secrets.token_bytes(32)
    bad_supervisor=LocalSignerSupervisor(
        independent_auth_url="http://127.0.0.1:1",publishable_key=anon)
    if not bad_supervisor.load(offline_key,offline_secret):
        raise AssertionError("I26 signer indisponivel sem chave")
    try:
        try:
            bad_supervisor.client.sign(offline_key,
                          material_for(gp.actor_id,gp.session_id),
                          "Bearer "+login["access_token"])
        except IdentityUnavailable:
            pass
        else:
            raise AssertionError("I26 assinou sem acesso à autoridade GoTrue")
    finally:
        bad_supervisor.close()
    print("PASS S1WITNESS-69: indisponibilidade GoTrue do assinador falha fechada")

    verified_signer.terminate()
    status,data=rpc("pausar",login["access_token"],p_operador=o3,
                    p_motivo_codigo="AUSENCIA_TEMPORARIA")
    if status!=503 or data.get("error")!="UNAVAILABLE":
        raise AssertionError("I26 processo encerrado nao retornou 503")
    if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
        raise AssertionError("I26 processo encerrado alterou negocio")
    print("PASS S1WITNESS-70: pane do assinador autenticador bloqueia sem efeito")

    server.shutdown()
    server.server_close()
    verified_signer.close()
    # I27: autenticacao mutua real em TLS local, GoTrue independente no
    # assinador, HMAC no banco; todos os certificados gerados pelo runner.
    with tempfile.TemporaryDirectory(prefix="s1-i27-mtls-") as cert_dir:
        pki = create_local_certificates(cert_dir)
        mtls_key=uuid.uuid4()
        mtls_secret=secrets.token_bytes(32)
        admin_call(
         "select prumo_s1_signed_i20.provisionar_chave_i24("
         f"'{mtls_key}'::uuid,decode('{mtls_secret.hex()}','hex'),"
         "clock_timestamp()-interval '1 minute',"
         "clock_timestamp()+interval '10 minutes','ROTACAO_PLANEJADA')")
        mtls_signer=LocalMutualTlsSignerSupervisor(
            independent_auth_url=api,publishable_key=anon,
            ca=pki["ca"],
            server_cert=pki["signer"]["cert"],
            server_key=pki["signer"]["key"],
            gateway_cert=pki["gateway"]["cert"],
            gateway_key=pki["gateway"]["key"],
            gateway_fingerprint=certificate_fingerprint(pki["gateway"]["cert"]),
            server_fingerprint=certificate_fingerprint(pki["signer"]["cert"]))
        try:
            if not mtls_signer.load(mtls_key,mtls_secret):
                raise AssertionError("I27 carga de chave local falhou")
            mtls_gateway=LocalIndependentlyAuthenticatedGateway(
                gateway_dsn,SupabaseGoTrueVerifier(api,anon),
                signer=mtls_signer.client,key_id=mtls_key)
            if "signing_key" in vars(mtls_gateway) or "_control" in vars(mtls_gateway):
                raise AssertionError("I27 chave/controle no gateway")
            if mtls_signer.client._port <= 0:
                raise AssertionError("I27 endpoint TLS indisponivel")
            print("PASS S1WITNESS-71: PKI descartavel, identities distintas e sem chave HMAC no gateway")

            server=serve_http_policy_local(mtls_gateway,max_requests=200,window_seconds=60)
            threading.Thread(target=server.serve_forever,daemon=True).start()
            gateway_url="http://127.0.0.1:"+str(server.server_address[1])
            try:
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                print("PASS S1WITNESS-72: gestor autenticado executa transacao real atraves de mTLS")

                attacker=LocalMutualTlsSignerClient(
                    port=mtls_signer.client._port,ca=pki["ca"],
                    cert=pki["intruder"]["cert"],key=pki["intruder"]["key"],
                    process=mtls_signer._process,
                    expected_server_fingerprint=certificate_fingerprint(pki["signer"]["cert"]))
                try:
                    attacker.sign(mtls_key,material_for(gp.actor_id,gp.session_id),
                                  "Bearer "+login["access_token"])
                except IdentityUnavailable:
                    pass
                else:
                    raise AssertionError("I27 certificado de intruso foi aceito")
                print("PASS S1WITNESS-73: certificado confiavel da mesma CA, mas outra identidade, negado")

                no_cert=ssl.create_default_context(
                    ssl.Purpose.SERVER_AUTH,cafile=pki["ca"])
                try:
                    with socket.create_connection(("127.0.0.1",mtls_signer.client._port),
                                                  timeout=4) as raw:
                        raw.settimeout(4)
                        with no_cert.wrap_socket(raw,server_hostname="localhost") as client:
                            client.sendall(bytes([0,0,0,2]) + b"{}")
                            data=client.recv(32)
                            if data:
                                raise AssertionError("I27 sem cert recebeu resposta de assinador")
                except (OSError,ssl.SSLError):
                    pass
                print("PASS S1WITNESS-74: mTLS rejeita cliente sem certificado")

                false_pin=LocalMutualTlsSignerClient(
                    port=mtls_signer.client._port,ca=pki["ca"],
                    cert=pki["gateway"]["cert"],key=pki["gateway"]["key"],
                    process=mtls_signer._process,
                    expected_server_fingerprint="0"*64)
                try:
                    false_pin.sign(mtls_key,material_for(gp.actor_id,gp.session_id),
                                   "Bearer "+login["access_token"])
                except IdentityUnavailable:
                    pass
                else:
                    raise AssertionError("I27 gateway ignorou pin do signer")
                print("PASS S1WITNESS-75: gateway rejeita servidor com identidade diferente")

                try:
                    mtls_signer.client.sign(mtls_key,
                       material_for(uuid.UUID(g2),gp.session_id),
                       "Bearer "+login["access_token"])
                except Denied:
                    pass
                else:
                    raise AssertionError("I27 ator falso em canal TLS autenticado")
                print("PASS S1WITNESS-76: TLS nao substitui vinculacao GoTrue ao ator")

                try:
                    mtls_signer.client.sign(mtls_key,
                       material_for(gp.actor_id,uuid.uuid4()),
                       "Bearer "+login["access_token"])
                except Denied:
                    pass
                else:
                    raise AssertionError("I27 sessao falsa em canal TLS autenticado")
                print("PASS S1WITNESS-77: GoTrue no filho recusa session_id inventada")

                status,data=rpc("pausar",token_g2,p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                blocked(status,"I27 cross-team com mTLS")
                if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
                    raise AssertionError("I27 cross-team alterou a equipe")
                print("PASS S1WITNESS-78: mTLS nao contorna governanca RBAC S1")

                if not mtls_signer.revoke(mtls_key):
                    raise AssertionError("I27 chave de signer nao revogada")
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                if status!=403:
                    raise AssertionError("I27 revogacao nao bloqueou assinatura")
                print("PASS S1WITNESS-79: revogacao no processo impede nova assinatura mTLS")

                mtls_signer.terminate()
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                if status!=503 or data.get("error")!="UNAVAILABLE":
                    raise AssertionError("I27 processo mTLS morto nao falhou fechado")
                if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
                    raise AssertionError("I27 pane alterou equipe")
                print("PASS S1WITNESS-80: pane do processo TLS bloqueia sem efeito comercial")
            finally:
                server.shutdown()
                server.server_close()
        finally:
            mtls_signer.close()
    # I28: autorizacao CAS, rotacao de identidades TLS e revogacao terminal
    # sem tocar na PKI real ou no Supabase hospedado.
    with tempfile.TemporaryDirectory(prefix="s1-i28-rotation-") as cert_dir:
        rot_pki=create_rotating_certificates(cert_dir)
        old_fp=certificate_fingerprint(rot_pki["gateway"]["cert"])
        next_fp=certificate_fingerprint(rot_pki["gateway_next"]["cert"])
        rot_key=uuid.uuid4()
        rot_secret=secrets.token_bytes(32)
        admin_call(
            "select prumo_s1_signed_i20.provisionar_chave_i24("
            f"'{rot_key}'::uuid,decode('{rot_secret.hex()}','hex'),"
            "clock_timestamp()-interval '1 minute',"
            "clock_timestamp()+interval '10 minutes','ROTACAO_PLANEJADA')")
        rot_signer=LocalRotatingTlsSignerSupervisor(
            independent_auth_url=api,publishable_key=anon,
            ca=rot_pki["ca"],server_cert=rot_pki["signer"]["cert"],
            server_key=rot_pki["signer"]["key"],
            gateway_cert=rot_pki["gateway"]["cert"],
            gateway_key=rot_pki["gateway"]["key"],
            gateway_fingerprint=old_fp,
            server_fingerprint=certificate_fingerprint(rot_pki["signer"]["cert"]))
        try:
            if not rot_signer.load(rot_key,rot_secret):
                raise AssertionError("I28 chave HMAC nao foi provisionada")
            new_client=rot_signer.client_with_certificate(
                rot_pki["gateway_next"]["cert"],rot_pki["gateway_next"]["key"])
            other_client=rot_signer.client_with_certificate(
                rot_pki["gateway_rogue"]["cert"],rot_pki["gateway_rogue"]["key"])
            rot_gateway=LocalIndependentlyAuthenticatedGateway(
                gateway_dsn,SupabaseGoTrueVerifier(api,anon),
                signer=rot_signer.client,key_id=rot_key)
            if "signing_key" in vars(rot_gateway) or "_control" in vars(rot_gateway):
                raise AssertionError("I28 segredo/controle vazou para gateway")
            print("PASS S1WITNESS-81: PKI efemera, supervisor com estado CAS e gateway sem segredo")

            server=serve_http_policy_local(rot_gateway,max_requests=200,window_seconds=60)
            threading.Thread(target=server.serve_forever,daemon=True).start()
            gateway_url="http://127.0.0.1:"+str(server.server_address[1])
            try:
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                print("PASS S1WITNESS-82: certificado gateway inicial opera atraves GoTrue e DB reais")

                try:
                    new_client.sign(rot_key,material_for(gp.actor_id,gp.session_id),
                                    "Bearer "+login["access_token"])
                except IdentityUnavailable:
                    pass
                else:
                    raise AssertionError("I28 sucessor antes de stage foi aceito")
                print("PASS S1WITNESS-83: certificado novo nao recebe privilegio sem stage")

                if rot_signer.stage_certificate(next_fp,1)!=("STAGED",2):
                    raise AssertionError("I28 versao CAS stage inesperada")
                if rot_signer.rotation_status()["active_count"]!=2:
                    raise AssertionError("I28 overlap nao abriu duas identidades")
                print("PASS S1WITNESS-84: autorizacao de sucessor CAS cria overlap limitado")

                for client in (rot_signer.client,new_client):
                    material=material_for(gp.actor_id,gp.session_id)
                    signed=client.sign(rot_key,material,"Bearer "+login["access_token"])
                    import hashlib, hmac
                    if signed!=hmac.new(rot_secret,material,hashlib.sha256).hexdigest():
                        raise AssertionError("I28 overlap assinatura incorreta")
                rot_gateway.signer=new_client
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                print("PASS S1WITNESS-85: old+new funcionam, sucessor conclui gesto gerencial")

                if rot_signer.revoke_certificate(old_fp,1)!=("STALE",2):
                    raise AssertionError("I28 revogacao CAS obsoleta autorizada")
                print("PASS S1WITNESS-86: revisao CAS desatualizada nao muda permissao")

                if rot_signer.revoke_certificate(old_fp,2)!=("REVOKED",3):
                    raise AssertionError("I28 nao revogou gateway antigo")
                try:
                    rot_signer.client.sign(rot_key,material_for(gp.actor_id,gp.session_id),
                                           "Bearer "+login["access_token"])
                except IdentityUnavailable:
                    pass
                else:
                    raise AssertionError("I28 antigo continuou assinando")
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                print("PASS S1WITNESS-87: revoga gateway anterior e sucessor segue operacional")

                if rot_signer.stage_certificate(old_fp,3)!=("DENIED",3):
                    raise AssertionError("I28 identidade revogada foi reativada")
                print("PASS S1WITNESS-88: certificado revogado tem bloqueio terminal")

                try:
                    other_client.sign(rot_key,material_for(gp.actor_id,gp.session_id),
                                       "Bearer "+login["access_token"])
                except IdentityUnavailable:
                    pass
                else:
                    raise AssertionError("I28 certificado de outro cliente passou")
                print("PASS S1WITNESS-89: identidade da mesma CA fora da lista negada")

                audit=rot_signer.rotation_status()
                if audit["events"]!=[(2,"CERT_STAGED"),(3,"CERT_REVOKED")]:
                    raise AssertionError("I28 historico de lifecycle inesperado")
                if old_fp in str(audit) or next_fp in str(audit) or login["access_token"] in str(audit):
                    raise AssertionError("I28 auditoria vazou material de identidade")
                if audit["version"]!=3 or audit["active_count"]!=1 or audit["revoked_count"]!=1:
                    raise AssertionError("I28 status de custodia inconsistente")
                print("PASS S1WITNESS-90: auditoria em memoria minima sem certificado ou JWT")

                try:
                    new_client.sign(rot_key,material_for(gp.actor_id,gp.session_id),
                                    "Bearer invalid-token")
                except Denied:
                    pass
                else:
                    raise AssertionError("I28 mTLS admitiu bearer falso")
                print("PASS S1WITNESS-91: mTLS nao substitui GoTrue independente no signer")

                status,data=rpc("pausar",token_g2,p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                blocked(status,"I28 RBAC equipes distintas")
                if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
                    raise AssertionError("I28 equipe alheia afetou negocio")
                print("PASS S1WITNESS-92: RBAC interequipe preservado no sucessor TLS")

                if rot_signer.revoke_certificate(next_fp,3)!=("REVOKED",4):
                    raise AssertionError("I28 revogacao emergencial falhou")
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                if status!=503 or data.get("error")!="UNAVAILABLE":
                    raise AssertionError("I28 sem gateway valido nao falhou fechado")
                if rot_signer.stage_certificate(old_fp,4)!=("DENIED",4):
                    raise AssertionError("I28 revogado antigo renasceu")
                status_admin=rot_signer.rotation_status()
                if status_admin["active_count"]!=0 or status_admin["revoked_count"]!=2:
                    raise AssertionError("I28 revogacao emergencia inconsistente")
                if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
                    raise AssertionError("I28 pane de certificados alterou equipe")
                print("PASS S1WITNESS-93: revogacao emergencial total falha fechada e preserva equipe")
            finally:
                server.shutdown()
                server.server_close()
        finally:
            rot_signer.close()
    # I29: registro de revogacao SQLITE externo ao assinador e persistente
    # APENAS enquanto existir o diretorio temporario descartavel do CI.
    with tempfile.TemporaryDirectory(prefix="s1-i29-state-") as folder:
        certs=create_rotating_certificates(folder)
        oldfp=certificate_fingerprint(certs["gateway"]["cert"])
        nextfp=certificate_fingerprint(certs["gateway_next"]["cert"])
        filepath=Path(folder)/"certificate-revocation.sqlite3"
        adminstore=LocalCertificateState(filepath)
        adminstore.initialize(oldfp)
        oldkey=uuid.uuid4()
        secret=secrets.token_bytes(32)
        admin_call(
            "select prumo_s1_signed_i20.provisionar_chave_i24("
            f"'{oldkey}'::uuid,decode('{secret.hex()}','hex'),"
            "clock_timestamp()-interval '1 minute',"
            "clock_timestamp()+interval '10 minutes','FALHA_OPERACIONAL')")
        def start_persisted():
            return LocalPersistentTlsSignerSupervisor(
                independent_auth_url=api,publishable_key=anon,
                ca=certs["ca"],server_cert=certs["signer"]["cert"],
                server_key=certs["signer"]["key"],
                gateway_cert=certs["gateway"]["cert"],
                gateway_key=certs["gateway"]["key"],
                gateway_fingerprint=oldfp,
                server_fingerprint=certificate_fingerprint(certs["signer"]["cert"]),
                state_path=filepath)
        persisted=start_persisted()
        try:
            if not persisted.load(oldkey,secret):
                raise AssertionError("I29 HMAC sintetico nao carregou")
            if adminstore.status()["version"]!=1:
                raise AssertionError("I29 snapshot inicial incongruente")
            try:
                adminstore.initialize(oldfp)
            except FileExistsError:
                pass
            else:
                raise AssertionError("I29 overwrite de revogacao aceito")
            print("PASS S1WITNESS-94: bootstrap unico e estado fora do processo")

            live_gateway=LocalIndependentlyAuthenticatedGateway(
                gateway_dsn,SupabaseGoTrueVerifier(api,anon),
                signer=persisted.client,key_id=oldkey)
            server=serve_http_policy_local(live_gateway,max_requests=200,window_seconds=60)
            threading.Thread(target=server.serve_forever,daemon=True).start()
            gateway_url="http://127.0.0.1:"+str(server.server_address[1])
            try:
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                print("PASS S1WITNESS-95: gestor legitimo opera por signer lendo ledger")

                successor=persisted.client_with_certificate(
                    certs["gateway_next"]["cert"],certs["gateway_next"]["key"])
                if persisted.stage_certificate(nextfp,1)!=("STAGED",2):
                    raise AssertionError("I29 CAS de sucessor falhou")
                live_gateway.signer=successor
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                print("PASS S1WITNESS-96: sucessora do ledger executa comandos reais")

                if persisted.revoke_certificate(oldfp,2)!=("REVOKED",3):
                    raise AssertionError("I29 tombstone nao persistiu")
                try:
                    persisted.client.sign(oldkey,
                        material_for(gp.actor_id,gp.session_id),
                        "Bearer "+login["access_token"])
                except IdentityUnavailable:
                    pass
                else:
                    raise AssertionError("I29 certificado antigo continuou valido")
                print("PASS S1WITNESS-97: tombstone bloqueia certificado velho")

                persisted.close()
                persisted=start_persisted()
                if not persisted.load(oldkey,secret):
                    raise AssertionError("I29 restart sem carga de HMAC")
                successor=persisted.client_with_certificate(
                    certs["gateway_next"]["cert"],certs["gateway_next"]["key"])
                live_gateway.signer=successor
                try:
                    persisted.client.sign(oldkey,material_for(gp.actor_id,gp.session_id),
                                          "Bearer "+login["access_token"])
                except IdentityUnavailable:
                    pass
                else:
                    raise AssertionError("I29 restart apagou tombstone")
                print("PASS S1WITNESS-98: reinicio nao restaura identidade revogada")

                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                print("PASS S1WITNESS-99: assinatura continua com sucessor apos restart")

                backup=Path(folder)/"snapshot-3.backup"
                shutil.copy2(filepath,backup)
                filepath.unlink()
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                if status!=503 or data.get("error")!="UNAVAILABLE":
                    raise AssertionError("I29 arquivo removido permitiu acao")
                if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
                    raise AssertionError("I29 arquivo removido alterou equipe")
                print("PASS S1WITNESS-100: ledger ausente causa fail-closed sem mudar equipe")

                persisted.close()
                try:
                    persisted=start_persisted()
                except RevocationStateUnavailable:
                    pass
                else:
                    persisted.close()
                    raise AssertionError("I29 estado vazio reabriu sem tombstones")
                shutil.copy2(backup,filepath)
                persisted=start_persisted()
                persisted.load(oldkey,secret)
                live_gateway.signer=persisted.client_with_certificate(
                    certs["gateway_next"]["cert"],certs["gateway_next"]["key"])
                print("PASS S1WITNESS-101: reinicio sem ledger bloqueado e recovery explicito")

                filepath.write_bytes(b"not a sqlite database")
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                if status!=503:
                    raise AssertionError("I29 corrupcao permitiu comando")
                shutil.copy2(backup,filepath)
                print("PASS S1WITNESS-102: ledger corrompido impede assinatura")

                if persisted.stage_certificate(oldfp,3)!=("DENIED",3):
                    raise AssertionError("I29 certificado previamente revogado renasceu")
                if persisted.revoke_certificate(nextfp,2)!=("STALE",3):
                    raise AssertionError("I29 CAS stale aceito")
                print("PASS S1WITNESS-103: bloqueio terminal e CAS apos recovery")

                status,data=rpc("pausar",token_g2,p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                blocked(status,"I29 RBAC de equipe alheia")
                st=persisted.rotation_status()
                if st["events"]!=[(2,"CERT_STAGED"),(3,"CERT_REVOKED")]:
                    raise AssertionError("I29 audit foi perdido")
                if oldfp in str(st) or nextfp in str(st) or login["access_token"] in str(st):
                    raise AssertionError("I29 audit expôs segredo")
                print("PASS S1WITNESS-104: historico minimo persistido e RBAC intacto")

                if persisted.revoke_certificate(nextfp,3)!=("REVOKED",4):
                    raise AssertionError("I29 revogacao emergencial falhou")
                persisted.close()
                persisted=start_persisted()
                persisted.load(oldkey,secret)
                live_gateway.signer=persisted.client_with_certificate(
                    certs["gateway_next"]["cert"],certs["gateway_next"]["key"])
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                if status!=503 or data.get("error")!="UNAVAILABLE":
                    raise AssertionError("I29 revogacao total foi ignorada no restart")
                if persisted.rotation_status()["active_count"]!=0:
                    raise AssertionError("I29 revogacao total nao persistiu")
                if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
                    raise AssertionError("I29 emergencia alterou equipe")
                print("PASS S1WITNESS-105: emergencia sobrevive a restart e preserva equipe")
            finally:
                server.shutdown()
                server.server_close()
        finally:
            persisted.close()
    # I30: autoridade independente com MAC do snapshot e watermark.
    # Mantem chave MAC dentro do processo autoridade (nao no signer),
    # usando um snapshot SQLite e sidecar HMAC ambos descartaveis no CI.
    with tempfile.TemporaryDirectory(prefix="s1-i30-authority-") as folder:
        pki=create_rotating_certificates(folder)
        first=certificate_fingerprint(pki["gateway"]["cert"])
        second=certificate_fingerprint(pki["gateway_next"]["cert"])
        rogue=certificate_fingerprint(pki["gateway_rogue"]["cert"])
        db_path=Path(folder)/"cert-ledger.sqlite3"
        checkpoint=Path(folder)/"cert-ledger.mac.json"
        LocalCertificateState(db_path).initialize(first)
        authority_key=secrets.token_bytes(32)
        def start_authority(initial=False):
            return LocalRevocationAuthoritySupervisor(
                db_path=db_path,checkpoint_path=checkpoint,secret=authority_key,
                bootstrap=initial,initial_fp=first)
        auth=start_authority(initial=True)
        authsigner=None
        def new_signer():
            return LocalAuthorityBackedSignerSupervisor(
                independent_auth_url=api,publishable_key=anon,
                ca=pki["ca"],server_cert=pki["signer"]["cert"],
                server_key=pki["signer"]["key"],
                gateway_cert=pki["gateway"]["cert"],
                gateway_key=pki["gateway"]["key"],
                gateway_fingerprint=first,
                server_fingerprint=certificate_fingerprint(pki["signer"]["cert"]),
                checker=auth.client)
        authsigner=new_signer()
        test_key=uuid.uuid4()
        test_secret=secrets.token_bytes(32)
        admin_call(
            "select prumo_s1_signed_i20.provisionar_chave_i24("
            f"'{test_key}'::uuid,decode('{test_secret.hex()}','hex'),"
            "clock_timestamp()-interval '1 minute',"
            "clock_timestamp()+interval '10 minutes','ROTACAO_PLANEJADA')")
        try:
            if not authsigner.load(test_key,test_secret):
                raise AssertionError("I30 HMAC synthetic load falhou")
            if auth.status()["version"]!=1:
                raise AssertionError("I30 bootstrap invalido")
            if hasattr(authsigner,"stage_certificate") or hasattr(authsigner,"_state"):
                raise AssertionError("I30 signer tem autoridade administrativa")
            print("PASS S1WITNESS-106: autoridade em processo proprio, snapshot MAC e signer sem admin")

            live=LocalIndependentlyAuthenticatedGateway(
                gateway_dsn,SupabaseGoTrueVerifier(api,anon),
                signer=authsigner.client,key_id=test_key)
            server=serve_http_policy_local(live,max_requests=200,window_seconds=60)
            threading.Thread(target=server.serve_forever,daemon=True).start()
            gateway_url="http://127.0.0.1:"+str(server.server_address[1])
            try:
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                print("PASS S1WITNESS-107: GoTrue real, mTLS e SQL autorizados com authority CHECK")

                old_db=Path(folder)/"old-state.bak"
                old_mac=Path(folder)/"old-mac.bak"
                shutil.copy2(db_path,old_db)
                shutil.copy2(checkpoint,old_mac)
                successor=authsigner.client_with_certificate(
                    pki["gateway_next"]["cert"],pki["gateway_next"]["key"])
                try:
                    successor.sign(test_key,material_for(gp.actor_id,gp.session_id),
                                   "Bearer "+login["access_token"])
                except IdentityUnavailable:
                    pass
                else:
                    raise AssertionError("I30 sucessor sem stage autorizado")
                print("PASS S1WITNESS-108: sucessor nao autorizado negado por autoridade")

                if auth.stage_certificate(second,1)!=("STAGED",2):
                    raise AssertionError("I30 stage CAS")
                live.signer=successor
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                print("PASS S1WITNESS-109: sucessor liberado por controle CAS externo")

                if auth.revoke_certificate(first,2)!=("REVOKED",3):
                    raise AssertionError("I30 revogacao do gateway antigo")
                try:
                    authsigner.client.sign(test_key,material_for(gp.actor_id,gp.session_id),
                                          "Bearer "+login["access_token"])
                except IdentityUnavailable:
                    pass
                else:
                    raise AssertionError("I30 certificado revogado obteve HMAC")
                print("PASS S1WITNESS-110: revogado recusado com MAC de snapshot atual")

                # Snapshot atual de recovery a partir de dois arquivos.
                current_db=Path(folder)/"cur-state.bak"
                current_mac=Path(folder)/"cur-mac.bak"
                shutil.copy2(db_path,current_db)
                shutil.copy2(checkpoint,current_mac)
                authsigner.close()
                authsigner=new_signer()
                authsigner.load(test_key,test_secret)
                live.signer=authsigner.client_with_certificate(
                    pki["gateway_next"]["cert"],pki["gateway_next"]["key"])
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                print("PASS S1WITNESS-111: restart do signer nao reinicia authority/watermark")

                # Violacao nao assinada em SQLite: integrity_check continua OK,
                # mas o MAC do snapshot precisa detectar adulteracao.
                import sqlite3
                with sqlite3.connect(db_path) as ledger_connection:
                    ledger_connection.execute("UPDATE certificates SET state='ACTIVE' WHERE fingerprint=?",(first,))
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                if status!=503 or data.get("error")!="UNAVAILABLE":
                    raise AssertionError("I30 adulteracao sem MAC nao falhou fechada")
                if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
                    raise AssertionError("I30 alteracao indevida da equipe")
                shutil.copy2(current_db,db_path)
                print("PASS S1WITNESS-112: SQLite consistente mas adulterado falha no MAC")

                checkpoint.write_text('{"revision":3,"mac":"'+'0'*64+'"}')
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                if status!=503:
                    raise AssertionError("I30 checkpoint MAC adulterado foi aceito")
                shutil.copy2(current_mac,checkpoint)
                print("PASS S1WITNESS-113: MAC adulterado falha fechado no signin")

                # Antiga foto COMPLETA (SQLite+MAC validos para versao 1).
                # A authority viva ja observou versao 3, impedindo retrocesso.
                shutil.copy2(old_db,db_path)
                shutil.copy2(old_mac,checkpoint)
                try:
                    authsigner.client.sign(test_key,material_for(gp.actor_id,gp.session_id),
                                          "Bearer "+login["access_token"])
                except IdentityUnavailable:
                    pass
                else:
                    raise AssertionError("I30 rollback autenticado antigo foi aceito")
                shutil.copy2(current_db,db_path)
                shutil.copy2(current_mac,checkpoint)
                print("PASS S1WITNESS-114: rollback MAC+SQLite nao reverte watermark da authority viva")

                authsigner.close()
                authsigner=new_signer()
                authsigner.load(test_key,test_secret)
                live.signer=authsigner.client_with_certificate(
                    pki["gateway_next"]["cert"],pki["gateway_next"]["key"])
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                print("PASS S1WITNESS-115: recovery explicito com estado autenticado")

                if auth.revoke_certificate(first,1)!=("STALE",3):
                    raise AssertionError("I30 CAS antigo modificou estado")
                if auth.stage_certificate(first,3)!=("DENIED",3):
                    raise AssertionError("I30 revogado foi reabilitado")
                print("PASS S1WITNESS-116: CAS stale e revogado irreversivel")

                rogue_client=authsigner.client_with_certificate(
                    pki["gateway_rogue"]["cert"],pki["gateway_rogue"]["key"])
                try:
                    rogue_client.sign(test_key,material_for(gp.actor_id,gp.session_id),
                                      "Bearer "+login["access_token"])
                except IdentityUnavailable:
                    pass
                else:
                    raise AssertionError("I30 identidade rogue obteve assinatura")
                status,data=rpc("pausar",token_g2,p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                blocked(status,"I30 RBAC")
                print("PASS S1WITNESS-117: issuer sozinho nao libera outro client/RBAC")

                st=auth.status()
                if st["events"]!=[(2,"CERT_STAGED"),(3,"CERT_REVOKED")]:
                    raise AssertionError("I30 audit inconsistente")
                if first in str(st) or second in str(st) or login["access_token"] in str(st):
                    raise AssertionError("I30 status vazou material sensivel")
                print("PASS S1WITNESS-118: status privado sem fingerprints/Bearer")

                authsigner.close()
                auth.close()
                # Reinicio honesto da authority com checkpoint atual assinado.
                auth=start_authority()
                authsigner=new_signer()
                authsigner.load(test_key,test_secret)
                live.signer=authsigner.client_with_certificate(
                    pki["gateway_next"]["cert"],pki["gateway_next"]["key"])
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                print("PASS S1WITNESS-119: restart da authority exige checkpoint atual e preserva revogado")

                if auth.revoke_certificate(second,3)!=("REVOKED",4):
                    raise AssertionError("I30 emergencia sem efeito")
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                if status!=503:
                    raise AssertionError("I30 emergencia nao bloqueou assinaturas")
                if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
                    raise AssertionError("I30 emergencia mutou equipe")
                print("PASS S1WITNESS-120: revogacao total autentica falha fechada e preserva equipe")
            finally:
                server.shutdown()
                server.server_close()
        finally:
            if authsigner is not None:authsigner.close()
            auth.close()
    # I31: testemunha com chave separada e revisao monotônica,
    # independente do ciclo de vida da authority e do signer.
    with tempfile.TemporaryDirectory(prefix="s1-i31-witness-") as folder:
        certs=create_rotating_certificates(folder)
        original=certificate_fingerprint(certs["gateway"]["cert"])
        successor_fp=certificate_fingerprint(certs["gateway_next"]["cert"])
        ledger_path=Path(folder)/"cert-ledger.sqlite3"
        auth_check=Path(folder)/"auth-mac.json"
        witness_path=Path(folder)/"independent-witness.json"
        LocalCertificateState(ledger_path).initialize(original)
        auth_secret=secrets.token_bytes(32)
        witness_secret=secrets.token_bytes(32)
        bootstrap_i31_authority(ledger_path,auth_check,witness_path,
                                auth_secret,witness_secret)
        witness=LocalMonotonicWitnessSupervisor(
            path=witness_path,secret=witness_secret)
        def new_auth():
            return LocalWitnessBackedRevocationSupervisor(
                db_path=ledger_path,checkpoint_path=auth_check,
                secret=auth_secret,witness_client=witness.client)
        auth=new_auth()
        def new_signer():
            return LocalAuthorityBackedSignerSupervisor(
                independent_auth_url=api,publishable_key=anon,
                ca=certs["ca"],server_cert=certs["signer"]["cert"],
                server_key=certs["signer"]["key"],
                gateway_cert=certs["gateway"]["cert"],
                gateway_key=certs["gateway"]["key"],
                gateway_fingerprint=original,
                server_fingerprint=certificate_fingerprint(certs["signer"]["cert"]),
                checker=auth.client)
        signer=new_signer()
        signed_id=uuid.uuid4()
        signed_secret=secrets.token_bytes(32)
        admin_call(
            "select prumo_s1_signed_i20.provisionar_chave_i24("
            f"'{signed_id}'::uuid,decode('{signed_secret.hex()}','hex'),"
            "clock_timestamp()-interval '1 minute',"
            "clock_timestamp()+interval '10 minutes','ROTACAO_PLANEJADA')")
        try:
            if not signer.load(signed_id,signed_secret):
                raise AssertionError("I31 signer HMAC nao provisionado")
            if auth.status()["version"]!=1 or witness.status()!=1:
                raise AssertionError("I31 revisoes de bootstrap inconsistentes")
            if hasattr(signer,"_witness") or hasattr(signer,"stage_certificate"):
                raise AssertionError("I31 signer expos canal admin")
            print("PASS S1WITNESS-121: witness separado rev1, authority e signer segregados")

            app=LocalIndependentlyAuthenticatedGateway(
                gateway_dsn,SupabaseGoTrueVerifier(api,anon),
                signer=signer.client,key_id=signed_id)
            server=serve_http_policy_local(app,max_requests=200,window_seconds=60)
            threading.Thread(target=server.serve_forever,daemon=True).start()
            gateway_url="http://127.0.0.1:"+str(server.server_address[1])
            try:
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                print("PASS S1WITNESS-122: GoTrue e HMAC operam somente apos witness CHECK")

                prev_db=Path(folder)/"snapshot-old.sqlite3"
                prev_mac=Path(folder)/"snapshot-old.mac.json"
                shutil.copy2(ledger_path,prev_db)
                shutil.copy2(auth_check,prev_mac)
                if auth.stage_certificate(successor_fp,1)!=("STAGED",2):
                    raise AssertionError("I31 stage de sucessor falhou")
                if auth.revoke_certificate(original,2)!=("REVOKED",3):
                    raise AssertionError("I31 revogacao nao avancou testemunha")
                if witness.status()!=3:
                    raise AssertionError("I31 witness nao avancou ao rev3")
                print("PASS S1WITNESS-123: CAS de rotacao atualiza ledger e witness")

                new_client=signer.client_with_certificate(
                    certs["gateway_next"]["cert"],certs["gateway_next"]["key"])
                app.signer=new_client
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                try:
                    signer.client.sign(signed_id,material_for(gp.actor_id,gp.session_id),
                                       "Bearer "+login["access_token"])
                except IdentityUnavailable:
                    pass
                else:raise AssertionError("I31 certificado anterior validou HMAC")
                print("PASS S1WITNESS-124: sucessor opera e revogado e negado")

                latest_db=Path(folder)/"snapshot-current.sqlite3"
                latest_mac=Path(folder)/"snapshot-current.mac.json"
                shutil.copy2(ledger_path,latest_db)
                shutil.copy2(auth_check,latest_mac)
                signer.close()
                auth.close()
                shutil.copy2(prev_db,ledger_path)
                shutil.copy2(prev_mac,auth_check)
                try:
                    invalid=new_auth()
                except IdentityUnavailable:
                    pass
                else:
                    invalid.close()
                    raise AssertionError("I31 rollback rev1 aceito apos restart da authority")
                print("PASS S1WITNESS-125: par SQLite+MAC antigo bloqueado apos reiniciar authority")

                shutil.copy2(latest_db,ledger_path)
                shutil.copy2(latest_mac,auth_check)
                auth=new_auth()
                signer=new_signer()
                if not signer.load(signed_id,signed_secret):
                    raise AssertionError("I31 recovery HMAC")
                app.signer=signer.client_with_certificate(
                    certs["gateway_next"]["cert"],certs["gateway_next"]["key"])
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                print("PASS S1WITNESS-126: recovery explicito no estado autenticado atual")

                import sqlite3
                with sqlite3.connect(ledger_path) as ledger_connection:
                    ledger_connection.execute("UPDATE certificates SET state='ACTIVE' WHERE fingerprint=?",(original,))
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                if status!=503 or data.get("error")!="UNAVAILABLE":
                    raise AssertionError("I31 SQLite adulterado liberou operador")
                shutil.copy2(latest_db,ledger_path)
                print("PASS S1WITNESS-127: adulteracao nao autenticada fecha operacao")

                witness_backup=Path(folder)/"witness-current.bak"
                shutil.copy2(witness_path,witness_backup)
                witness_path.write_text('{"revision":3,"digest":"'+'0'*64+'","mac":"'+'0'*64+'"}')
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                if status!=503:
                    raise AssertionError("I31 witness adulterado aceito")
                shutil.copy2(witness_backup,witness_path)
                print("PASS S1WITNESS-128: MAC proprio da testemunha bloqueia adulteracao")

                status,data=rpc("pausar",token_g2,p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                blocked(status,"I31 RBAC")
                if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
                    raise AssertionError("I31 auditoria alterou equipe")
                print("PASS S1WITNESS-129: RBAC gerencial e estado de equipe preservados")

                signer.close()
                auth.close()
                witness.close()
                witness=LocalMonotonicWitnessSupervisor(
                    path=witness_path,secret=witness_secret)
                auth=new_auth()
                signer=new_signer()
                if not signer.load(signed_id,signed_secret):
                    raise AssertionError("I31 signer apos reinicio witness")
                app.signer=signer.client_with_certificate(
                    certs["gateway_next"]["cert"],certs["gateway_next"]["key"])
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                ok(status,data,"PAUSED_GLOBAL")
                status,data=rpc("reativar",login["access_token"],p_operador=o3)
                ok(status,data,"ACTIVE_GLOBAL")
                if witness.status()!=3:
                    raise AssertionError("I31 witness perde revision apos restart honesto")
                print("PASS S1WITNESS-130: reinicio honesto witness+authority com rev3")

                if auth.revoke_certificate(successor_fp,3)!=("REVOKED",4):
                    raise AssertionError("I31 revogacao emergencia nao persistida")
                if witness.status()!=4:
                    raise AssertionError("I31 witness nao observou rev4")
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                if status!=503 or data.get("error")!="UNAVAILABLE":
                    raise AssertionError("I31 emergencia nao falhou fechada")
                print("PASS S1WITNESS-131: revogacao emergencial permanece no witness rev4")

                signer.close()
                auth.close()
                auth=new_auth()
                signer=new_signer()
                signer.load(signed_id,signed_secret)
                app.signer=signer.client_with_certificate(
                    certs["gateway_next"]["cert"],certs["gateway_next"]["key"])
                status,data=rpc("pausar",login["access_token"],p_operador=o3,
                                p_motivo_codigo="AUSENCIA_TEMPORARIA")
                if status!=503:
                    raise AssertionError("I31 revogado resurrect apos restart")
                if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
                    raise AssertionError("I31 emergencia mudou dominio comercial")
                print("PASS S1WITNESS-132: revogacao total sobrevive autoridade e signer restart")
            finally:
                server.shutdown()
                server.server_close()
        finally:
            try:signer.close()
            except Exception:pass
            try:auth.close()
            except Exception:pass
            witness.close()
    print("S1-002/I31: 132/132 verificacoes E2E GoTrue/HMAC/witness local.")
    # I37 installs only local SQL after all historical I31 verification.
    # Signed v37 reuses the I22 custody and I31 signer/witness safety stack.
    sql(path="supabase/tests/s1_053_issue10_disponibilidade_local_only.sql")
    sql(path="supabase/tests/s1_057_issue10_gateway_assinado_local_only.sql")
    print("PASS S1INTAKE-133: fixture I37 loaded after historical 132 gates")

    with tempfile.TemporaryDirectory(prefix="s1-i37-intake-") as folder:
        certs=create_rotating_certificates(folder)
        fp=certificate_fingerprint(certs["gateway"]["cert"])
        state=Path(folder)/"cert-ledger.sqlite3"
        checkpoint=Path(folder)/"authority-mac.json"
        witness_file=Path(folder)/"witness-mac.json"
        LocalCertificateState(state).initialize(fp)
        authority_key=secrets.token_bytes(32)
        witness_key=secrets.token_bytes(32)
        bootstrap_i31_authority(state,checkpoint,witness_file,authority_key,witness_key)
        witness=LocalMonotonicWitnessSupervisor(path=witness_file,secret=witness_key)
        authority=LocalWitnessBackedRevocationSupervisor(
            db_path=state,checkpoint_path=checkpoint,
            secret=authority_key,witness_client=witness.client)
        signer=LocalAuthorityBackedSignerSupervisor(
            independent_auth_url=api,publishable_key=anon,
            ca=certs["ca"],server_cert=certs["signer"]["cert"],
            server_key=certs["signer"]["key"],gateway_cert=certs["gateway"]["cert"],
            gateway_key=certs["gateway"]["key"],gateway_fingerprint=fp,
            server_fingerprint=certificate_fingerprint(certs["signer"]["cert"]),
            checker=authority.client)
        new_key=uuid.uuid4()
        new_secret=secrets.token_bytes(32)
        admin_call(
            "select prumo_s1_signed_i20.provisionar_chave_i24("
            f"'{new_key}'::uuid,decode('{new_secret.hex()}','hex'),"
            "clock_timestamp()-interval '1 minute',"
            "clock_timestamp()+interval '10 minutes','ROTACAO_PLANEJADA')")
        if not signer.load(new_key,new_secret):
            raise AssertionError("I37 signer key not loaded")
        app=LocalSignedIntakeOnlyGateway(
            gateway_dsn,SupabaseGoTrueVerifier(api,anon),
            signer=signer.client,key_id=new_key)
        server=serve_http_policy_local(app,allowed_commands=("intake",),
                                       max_requests=200,window_seconds=60)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        gateway_url="http://127.0.0.1:"+str(server.server_address[1])
        def call_intake(token,operator,paused,version,extra=None):
            body={"operador_id":operator,"pausar":paused,"versao_esperada":version}
            if extra:body.update(extra)
            return http("POST","/s1/intake",bearer=token,body=body,base=gateway_url)
        try:
            token=login["access_token"]
            assert authority.status()["version"]==1 and witness.status()==1
            status,data=call_intake(token,o3,True,1)
            ok(status,data,"INTAKE_PAUSED")
            assert data["version"]==2 and data["redistribution"]=="DEFERRED_S0_PROOF"
            print("PASS S1INTAKE-134: GoTrue real + signer mTLS + I22 HMAC + CAS pause")
            if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
                raise AssertionError("I37 pause suspended account")
            print("PASS S1INTAKE-135: pause keeps account ACTIVE")
            if sql(f"select count(*) from public.vinculos_papel_escopo where ator_id='{o3}'::uuid")=="0":
                raise AssertionError("I37 grants lost")
            print("PASS S1INTAKE-136: grants preserved, no redistribution claim")
            status,data=call_intake(token,o3,True,2)
            ok(status,data,"ALREADY_APPLIED")
            assert data["version"]==2
            print("PASS S1INTAKE-137: retry idempotent with exact current version")
            status,data=call_intake(token,o3,False,1)
            if status!=409 or data.get("outcome")!="CONFLICT":
                raise AssertionError("I37 stale version not HTTP409 "+str((status,data)))
            print("PASS S1INTAKE-138: stale CAS maps to HTTP 409, no mutation")
            status,data=call_intake(token_g2,o3,False,2)
            if status!=403:raise AssertionError("I37 other manager accepted")
            print("PASS S1INTAKE-139: cross-team manager forbidden")
            status,data=call_intake(token,o3,False,2,{"motivo_codigo":"AUSENCIA"})
            if status!=400:raise AssertionError("I37 accepted reason")
            status,data=call_intake(token,o3,False,True)
            if status!=400:raise AssertionError("I37 accepted boolean version")
            print("PASS S1INTAKE-140: no reason allowed, strict JSON and version")
            status,data=http("POST","/s1/pausar",bearer=token,
                             body={"operador_id":o3,"motivo_codigo":"AUSENCIA_TEMPORARIA"},base=gateway_url)
            if status!=404:raise AssertionError("I37 exposed legacy pause route")
            status,data=http("POST","/s1/reativar",bearer=token,
                             body={"operador_id":o3},base=gateway_url)
            if status!=404:raise AssertionError("I37 exposed legacy resume route")
            print("PASS S1INTAKE-141: HTTP rejects legacy suspend-account routes")
            status,data=call_intake(token,o3,False,2)
            ok(status,data,"INTAKE_RESUMED")
            assert data["version"]==3 and data["intake_paused"] is False
            print("PASS S1INTAKE-142: resume restores intake only, version3")
            principal=SupabaseGoTrueVerifier(api,anon).verify("Bearer "+token)
            proof=app.proof(principal,uuid.UUID(o3),True,3,"Bearer "+token)
            import psycopg
            with psycopg.connect(gateway_dsn,connect_timeout=5) as dbconn:
                with dbconn.cursor() as cur:
                    cur.execute(_SQL_INTAKE,proof)
                    result=cur.fetchone()[0]
                    if result["outcome"]!="INTAKE_PAUSED" or result["version"]!=4:
                        raise AssertionError("I37 direct signed request invalid")
            print("PASS S1INTAKE-143: raw signed command must be authenticated and committed")
            try:
                with psycopg.connect(gateway_dsn,connect_timeout=5) as dbconn:
                    with dbconn.cursor() as cur:cur.execute(_SQL_INTAKE,proof)
            except psycopg.Error as e:
                if e.sqlstate!="42501":raise
            else:raise AssertionError("I37 replay nonce accepted")
            print("PASS S1INTAKE-144: SQL nonce replay blocked")
            altered=list(proof);altered[3]=False
            try:
                with psycopg.connect(gateway_dsn,connect_timeout=5) as dbconn:
                    with dbconn.cursor() as cur:cur.execute(_SQL_INTAKE,altered)
            except psycopg.Error as e:
                if e.sqlstate!="42501":raise
            else:raise AssertionError("I37 unsigned action modification accepted")
            print("PASS S1INTAKE-145: HMAC binds pause boolean and version")
            if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
                raise AssertionError("I37 changed account by SQL")
            if sql(f"select versao from prumo_private.s1_disponibilidade_leads_10 where operador_id='{o3}'::uuid")!="4":
                raise AssertionError("I37 stale/replay affected revision")
            print("PASS S1INTAKE-146: failed calls did not change CAS or account")
            status,data=call_intake(token,o3,True,4)
            ok(status,data,"ALREADY_APPLIED")
            signer.revoke(new_key)
            status,data=call_intake(token,o3,False,4)
            if status!=403:raise AssertionError("I37 revoked signer key used")
            print("PASS S1INTAKE-147: signer HMAC key revocation blocks new requests")
            signer.close()
            status,data=call_intake(token,o3,False,4)
            if status!=503:raise AssertionError("I37 signer down not fail-closed")
            print("PASS S1INTAKE-148: signer unavailable means HTTP 503")
        finally:
            server.shutdown()
            server.server_close()
            signer.close()
            authority.close()
            witness.close()
    print("S1-002/I37: 132 older E2E and 16 new I37 gates PASS.")

