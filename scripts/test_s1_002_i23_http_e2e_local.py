#!/usr/bin/env python3
"""S1-002/I23: E2E somente local CI (GoTrue, PostgREST e migrations REAIS).
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
from backend.s1_gateway_local import _SQL
from backend.s1_gateway_http_policy_local import serve_http_policy_local
from backend.s1_gateway_signed_local import LocalSignedTeamGateway, _SQL_SIGNED
from backend.identity_boundary import SupabaseGoTrueVerifier, Principal
from urllib.request import Request, urlopen

api = os.environ["API_URL"].rstrip("/")
db = os.environ["DB_URL"]
anon = os.environ["ANON_KEY"]
if os.environ.get("CI") != "true" or os.environ.get("PRUMO_S1_I23_EPHEMERAL") != "YES":
    raise SystemExit("RECUSADO: exige CI e PRUMO_S1_I23_EPHEMERAL=YES")
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
print("PASS S1HTTP-01: S0/S1 migrations reais aplicadas no Supabase efemero (" +
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
print("PASS S1HTTP-02: cinco contas GoTrue, gestores por equipe e grants A/B reais")

status, data = rpc("pausar", token_g2, p_operador=o3,
                   p_motivo_codigo="AUSENCIA_TEMPORARIA")
blocked(status, "gestor de outra equipe pausou operador")
print("PASS S1HTTP-03: gestor alheio negado via JWT real")

status, data = rpc("mover", token_g1, p_loja=store_a,p_caso=case_a,
                   p_atribuicao_esperada=prev_a,p_destino=o4)
ok(status,data,"MOVED")
if data.get("case_id") != case_a:
    raise AssertionError("caso HTTP movimentado incorretamente")
print("PASS S1HTTP-04: gestor sem grant da loja move caso A dentro da equipe")

status, _ = rpc("mover", token_g1, p_loja=store_a,p_caso=case_a,
                p_atribuicao_esperada=prev_a,p_destino=o4)
blocked(status, "replay da atribuicao anterior")
print("PASS S1HTTP-05: replay de movimento obsoleto negado")

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
print("PASS S1HTTP-06: pausa global redistribuiu B e preservou grants A/B")

status, _ = rpc("reativar", token_g2,p_operador=o3)
blocked(status,"G2 reativou O3")
print("PASS S1HTTP-07: chefe alheio nao reativa operador")

status, _ = http("POST","/auth/v1/logout",bearer=token_g1)
if status not in (200,204):
    raise AssertionError("logout gestor falhou")
status, _ = rpc("reativar",token_g1,p_operador=o3)
blocked(status,"gestor com JWT revogado reativou")
print("PASS S1HTTP-08: logout GoTrue impede reativacao de equipe")

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
print("PASS S1HTTP-09: sessao nova reativa sem recuperar carteira antiga")

if sql("select (not has_schema_privilege('authenticated','prumo_private','USAGE') and not has_table_privilege('authenticated','auth.sessions','SELECT'))::text") != "true":
    raise AssertionError("privilegios privados ampliados")
for name in ("s1_mover_atendimento_sessao","s1_pausar_operador_sessao","s1_reativar_operador_sessao"):
    status, _ = http("POST","/rest/v1/rpc/"+name,bearer=login["access_token"],body={})
    if status != 404:
        raise AssertionError("fachada real indevidamente publicada "+name)
print("PASS S1HTTP-10: fachadas S1 privadas, SEM pontes RPC publicas")
print("S1-002/I23: operacoes reais com gateway assinado e sem RPC.")

# I19-11: não aceita autoria, sessão, role ou SQL no corpo do cliente.
status, _ = rpc("pausar", token_g2, p_operador=o3,
                p_motivo_codigo="AUSENCIA_TEMPORARIA", actor_id=g1)
if status != 400:
    raise AssertionError("gateway permitiu campo actor_id extra")
print("PASS S1HTTP-11: input proibe actor_id e parametros adicionais")

# I19-12: service_role não representa usuário GoTrue.
status, _ = rpc("reativar", os.environ["SERVICE_ROLE_KEY"], p_operador=o3)
blocked(status, "service_role virou gestor")
print("PASS S1HTTP-12: service_role nao atravessa verificacao de usuario GoTrue")

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
print("PASS S1HTTP-13: login SQL isolado sem authenticated, postgres e acesso direto")

for name in ("mover", "pausar", "reativar"):
    status, _ = http("POST", "/rest/v1/rpc/s1_i18_" + name,
                      bearer=login["access_token"], body={})
    if status != 404:
        raise AssertionError("ponte I18 indevidamente criada no I19 " + name)
print("PASS S1HTTP-14: banco I19 nao possui canarios publicos I18")
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
print("PASS S1HTTP-15: credencial SQL com ator e sessao nao forja HMAC")

# Prova válida não permite trocar ator/alvo/operador.
tampered = list(valid_proof)
tampered[1] = uuid.UUID(g2)
denied_proof(tuple(tampered), "substituicao do solicitante")
tampered = list(valid_proof)
tampered[7] = uuid.UUID(o4)
denied_proof(tuple(tampered), "substituicao do operador")
print("PASS S1HTTP-16: assinatura vincula ator e alvo")

old_proof = gateway.proof(principal,"pausar",params,issued=int(time.time())-120)
denied_proof(old_proof, "assinatura com validade vencida")
future_proof = gateway.proof(principal,"pausar",params,issued=int(time.time())+60)
denied_proof(future_proof,"assinatura com clock muito adiantado")
print("PASS S1HTTP-17: epoch curto bloqueia replay temporal")

# Primeiro comando assinado tem efeito real; o mesmo nonce é consumido.
first = raw_call(valid_proof)
if first.get("outcome") != "PAUSED_GLOBAL":
    raise AssertionError("comando com prova assinada valida nao pausou")
denied_proof(valid_proof, "reutilizacao de nonce em operação já executada")
if sql(f"select count(*) from prumo_s1_signed_i20.nonces where id='{valid_proof[-2]}'::uuid") != "1":
    raise AssertionError("nonce nao foi consumido exatamente uma vez")
status, response = rpc("reativar", login["access_token"], p_operador=o3)
ok(status, response, "ACTIVE_GLOBAL")
print("PASS S1HTTP-18: nonce nao reutilizavel, efeito unico confirmado")

# Simula uma prova assinada POR ERRO para sessão antiga já revogada:
# helper I15 deve revalidar auth.sessions mesmo com HMAC correta.
mid = token_g1.split(".")[1]
old_claims = json.loads(base64.urlsafe_b64decode(mid + "=" * (-len(mid) % 4)))
revoked = Principal(uuid.UUID(g1), uuid.UUID(old_claims["session_id"]))
revoked_proof = gateway.proof(revoked,"pausar",params)
denied_proof(revoked_proof, "sessao GoTrue revogada com HMAC valida")
print("PASS S1HTTP-19: HMAC nao ignora revogacao de sessao GoTrue")

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
print("PASS S1HTTP-20: login SQL nao assume role JWT nem le segredo")

# Revogar chave no postgres efemero deve bloquear comando, sem writes S1.
sql("begin; set local role prumo_s1_i22_custodio; "
    "select pg_catalog.pg_advisory_xact_lock("
    f"pg_catalog.hashtextextended('prumo-s1-key-v1:{key_id}',0)); "
    f"update prumo_s1_signed_i20.chaves set ativo=false where id='{key_id}'::uuid; "
    "commit;")
status, _ = rpc("pausar", login["access_token"], p_operador=o3,
                p_motivo_codigo="AUSENCIA_TEMPORARIA")
blocked(status,"chave de assinatura revogada")
if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid") != "ativo":
    raise AssertionError("chave revogada alterou equipe")
print("PASS S1HTTP-21: chave revogada bloqueia sem efeito de negocio")


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
print("PASS S1HTTP-22: executor possui invocar/nonce; custodio possui chaves")

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
print("PASS S1HTTP-23: executor isolado sem login, superuser ou bypassrls")

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
print("PASS S1HTTP-24: login SQL nao consegue SET ROLE executor nem DML chaves")

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
print("PASS S1HTTP-25: owner novo sem acesso bruto a dados ou funcoes privadas")

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
print("PASS S1HTTP-26: regras e owners I14 preservados")

# I21-27: apos desativacao da chave antiga (S1KEY-21), uma chave NOVA,
# exclusivamente gerada no runner e provisionada por postgres, restaura
# autorizacao: verifica que menor privilegio nao quebrou rotacao.
new_key_id = uuid.uuid4()
new_secret = secrets.token_bytes(32)
sql(
    "begin; set local role prumo_s1_i22_custodio; "
    "insert into prumo_s1_signed_i20.chaves(id,segredo,valido_desde,valido_ate) "
    f"values ('{new_key_id}'::uuid, decode('{new_secret.hex()}','hex'), "
    "clock_timestamp() - interval '1 minute', clock_timestamp() + interval '10 minutes'); "
    "commit;"
)
gateway.key_id = new_key_id
gateway.signing_key = new_secret
status, data = rpc("pausar",login["access_token"],p_operador=o3,
                   p_motivo_codigo="AUSENCIA_TEMPORARIA")
ok(status,data,"PAUSED_GLOBAL")
status, data = rpc("reativar",login["access_token"],p_operador=o3)
ok(status,data,"ACTIVE_GLOBAL")
print("PASS S1HTTP-27: chave nova rotacionada sem privilegio postgres no invocar")

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
print("PASS S1HTTP-28: verificador e chave com custodio NOLOGIN independente")

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
print("PASS S1HTTP-29: executor sem SELECT/DML na chave, apenas EXECUTE do verificador")

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
print("PASS S1HTTP-30: custodio sem interfaces S1, auth.sessions e nonce")

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
print("PASS S1HTTP-31: executor não exfiltra nem altera chave por SQL")

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
print("PASS S1HTTP-32: cliente SQL sem SET ROLE custodio ou EXECUTE verificador")

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
print("PASS S1HTTP-33: ownership e CREATE seguem separados apos rotacao")

# I23: Requisicoes HTTP malformadas NAO chegam ao GoTrue nem ao banco.
# Estados comerciais devem permanecer intactos apos todos os bloqueios.
import http.client
def hostile_http(headers=None, body=None, method="POST", path="/s1/pausar",
                 duplicate=()):
    conn=http.client.HTTPConnection("127.0.0.1",server.server_address[1],timeout=6)
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
print("PASS S1HTTP-34: somente POST e permitido")

status,data,headers=hostile_http(headers={"Origin":"https://evil.example"})
if status!=403 or "Access-Control-Allow-Origin" in headers:
    raise AssertionError("I23 origem externa autorizada")
print("PASS S1HTTP-35: Origin externo e CORS cross-site proibidos")

status,data,_=hostile_http(headers={"Cookie":"auth=forged"})
if status!=400:
    raise AssertionError("I23 cookie em vez de Bearer nao negado")
print("PASS S1HTTP-36: cookies desabilitados e Bearer independente")

status,data,_=hostile_http(headers={"X-Forwarded-For":"127.0.0.1"})
if status!=400:
    raise AssertionError("I23 header proxy do usuario foi confiado")
print("PASS S1HTTP-37: forwarded headers de cliente rejeitados")

status,data,_=hostile_http(duplicate=(("Authorization", "Bearer " + token_g2),))
if status!=400:
    raise AssertionError("I23 autorizacoes ambiguas aceitas")
print("PASS S1HTTP-38: Authorization duplicado negado")

status,data,_=hostile_http(body='{"operador_id":"'+o3+'","operador_id":"'+o4+'","motivo_codigo":"AUSENCIA_TEMPORARIA"}')
if status!=400:
    raise AssertionError("I23 JSON com chaves duplicadas aceito")
print("PASS S1HTTP-39: parser JSON rejeita propriedades repetidas")

status,data,headers=hostile_http(headers={"Transfer-Encoding":"chunked"})
if status!=400:
    raise AssertionError("I23 transfer encoding ambigua aceita")
if sql(f"select estado from public.equipe_prumo_s1 where ator_id='{o3}'::uuid")!="ativo":
    raise AssertionError("I23 pedido hostil causou pausa")
if headers.get("Cache-Control")!="no-store" or headers.get("X-Content-Type-Options")!="nosniff":
    raise AssertionError("I23 faltou header de protecao")
print("PASS S1HTTP-40: TE ambigua rejeitada, sem mudanca comercial e com no-store")

server.shutdown()
server.server_close()
print("S1-002/I23: 40/40 verificacoes E2E GoTrue/HMAC/HTTP locais.")
