#!/usr/bin/env python3
"""Prumo S0 integration: GoTrue REAL (local) + PostgREST REAL (local), no external accounts.

Hard fail on all failed authorization assertions. Never prints token, email or key.
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


def fail(message):
    raise AssertionError(message)


def local_config():
    result = subprocess.run(
        ["supabase", "status", "--output", "env"], capture_output=True, text=True, check=True
    )
    config = {}
    for line in result.stdout.splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            config[k.strip()] = v.strip().strip('"').strip("'")
    for key in ("API_URL", "ANON_KEY", "DB_URL"):
        if not config.get(key):
            fail("Local Supabase status missing required key: " + key)
    if not re.match(r"^https?://(127[.]0[.]0[.]1|localhost):", config["API_URL"]):
        fail("Refusing non-local Supabase API")
    u = urllib.parse.urlparse(config["DB_URL"])
    if u.hostname not in ("localhost", "127.0.0.1", "::1") or u.path != "/postgres":
        fail("Refusing non-local Supabase database")
    return config


CONF = local_config()
API, ANON, DB = CONF["API_URL"], CONF["ANON_KEY"], CONF["DB_URL"]
PASSWORD = "Only-For-Local-Testing!A93v"


def http(method, path, token=None, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf8")
    headers = {"apikey": ANON, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(
        API + path, data=data, method=method, headers=headers
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        # Do not log response bodies: may contain provider details.
        return e.code, None


def new_actor(label):
    email = "prumo-ci-" + label + "@example.invalid"
    code, obj = http("POST", "/auth/v1/signup", payload={
        "email": email, "password": PASSWORD
    })
    if code not in (200, 201) or not isinstance(obj, dict) or not obj.get("user"):
        fail("Local GoTrue signup failed for " + label + ": " + str(code))
    code, login = http(
        "POST", "/auth/v1/token?grant_type=password",
        payload={"email": email, "password": PASSWORD}
    )
    if code != 200 or not login or not login.get("access_token"):
        fail("Local GoTrue password login failed for " + label + ": " + str(code))
    subject = str(uuid.UUID(login["user"]["id"]))
    if obj["user"]["id"] != subject:
        fail("GoTrue token user mismatch")
    return subject, login["access_token"]


def run_sql(sql):
    result = subprocess.run(
        ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", DB, "-c", sql],
        capture_output=True, text=True
    )
    if result.returncode:
        # SQL may contain synthetic IDs but no user data or secrets.
        fail("Local SQL fixture/test failed: " + result.stderr[-700:])


actors = {name: new_actor(name) for name in ("gestora", "gestorb", "operador", "outsider")}
A, B, OP, OUT = (actors[k][0] for k in ("gestora", "gestorb", "operador", "outsider"))
for subject in (A, B, OP, OUT):
    uuid.UUID(subject)

LOJA_A = "c2000000-0000-4000-8000-000000000001"
LOJA_B = "c2000000-0000-4000-8000-000000000002"
LEAD_A = "c3000000-0000-4000-8000-000000000001"
LEAD_B = "c3000000-0000-4000-8000-000000000002"
CICLO_A = "c4000000-0000-4000-8000-000000000001"
CICLO_B = "c4000000-0000-4000-8000-000000000002"
CANAL_A = "c5000000-0000-4000-8000-000000000001"
CANAL_B = "c5000000-0000-4000-8000-000000000002"
CASO_A = "c6000000-0000-4000-8000-000000000001"
CONV_A = "c7000000-0000-4000-8000-000000000001"
CONV_B = "c7000000-0000-4000-8000-000000000002"

run_sql(f"""
begin;
insert into public.atores(id) values ('{A}'),('{B}'),('{OP}'),('{OUT}');
insert into public.concessionarias(id,nome_operacional) values
('{LOJA_A}','A - sintetica'),('{LOJA_B}','B - sintetica');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
('{A}','{LOJA_A}','gestor'),('{B}','{LOJA_B}','gestor'),('{OP}','{LOJA_A}','operador');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
('{CANAL_A}','{LOJA_A}','emissor_sintetico_A'),
('{CANAL_B}','{LOJA_B}','emissor_sintetico_B');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
('{LEAD_A}','{LOJA_A}','+5581999000001'),
('{LEAD_B}','{LOJA_B}','+5581999000001');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
('{CICLO_A}','{LOJA_A}','{LEAD_A}'),
('{CICLO_B}','{LOJA_B}','{LEAD_B}');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
values('{CASO_A}','{LOJA_A}','{LEAD_A}','{CICLO_A}');
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
values('{LOJA_A}','{CASO_A}','{OP}');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id) values
('{CONV_A}','{LOJA_A}','{LEAD_A}','{CANAL_A}','{CASO_A}'),
('{CONV_B}','{LOJA_B}','{LEAD_B}','{CANAL_B}',null);
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,origem,
conteudo_sintetico,id_externo) values
('{LOJA_A}','{CONV_A}','{CANAL_A}','{CASO_A}','entrada','simulado','A teste','A-test1'),
('{LOJA_B}','{CONV_B}','{CANAL_B}',null,'entrada','simulado','B teste','B-test1');
insert into public.pendencias_inbound_simulado(concessionaria_id,canal_id,lead_id,mensagem_id,motivo)
select '{LOJA_A}','{CANAL_A}','{LEAD_A}',id,'MULTIPLOS_CICLOS'
from public.mensagens where concessionaria_id='{LOJA_A}' and id_externo='A-test1';
commit;
""")


# Recontatos: fixtures novas para verificar Data API real e isolamento A/B.
run_sql(f"""
begin;
insert into public.catalogo_templates_sinteticos(id,concessionaria_id,codigo,versao,aprovado_simulacao)
values ('d6000000-0000-4000-8000-000000000091','{LOJA_A}','TEST',1,true),
       ('d6000000-0000-4000-8000-000000000092','{LOJA_B}','TEST',1,true);
insert into public.planos_recontato_sinteticos(
 id,concessionaria_id,lead_id,ciclo_id,canal_id,chave_idempotencia,fingerprint)
values ('d7000000-0000-4000-8000-000000000091','{LOJA_A}','{LEAD_A}','{CICLO_A}','{CANAL_A}','auth-a','fixture_a'),
       ('d7000000-0000-4000-8000-000000000092','{LOJA_B}','{LEAD_B}','{CICLO_B}','{CANAL_B}','auth-b','fixture_b');
insert into public.envios_template_sinteticos(
 id,concessionaria_id,plano_id,template_id,ordem,agendado_em,chave_idempotencia)
values ('d8000000-0000-4000-8000-000000000091','{LOJA_A}',
  'd7000000-0000-4000-8000-000000000091',
  'd6000000-0000-4000-8000-000000000091',1,statement_timestamp()+interval '1 day','auth-a:1'),
       ('d8000000-0000-4000-8000-000000000092','{LOJA_B}',
  'd7000000-0000-4000-8000-000000000092',
  'd6000000-0000-4000-8000-000000000092',1,statement_timestamp()+interval '1 day','auth-b:1');
insert into public.eventos_envio_template_sinteticos(
 concessionaria_id,envio_id,estado_anterior,estado_posterior,motivo)
values ('{LOJA_A}','d8000000-0000-4000-8000-000000000091','preparado','programado','fixture'),
       ('{LOJA_B}','d8000000-0000-4000-8000-000000000092','preparado','programado','fixture');
commit;
""")


# Elegibilidade sintética: evidência só na mesma loja/canal; opt-out da loja A.
run_sql(f"""
insert into public.evidencias_elegibilidade_sinteticas(
 concessionaria_id,lead_id,canal_id,finalidade,referencia_ficticia)
values ('{LOJA_A}','{LEAD_A}','{CANAL_A}',
 'recontato_comercial_sintetico','AUTH_FICTICIO_A_01'),
 ('{LOJA_B}','{LEAD_B}','{CANAL_B}',
 'recontato_comercial_sintetico','AUTH_FICTICIO_B_01');
insert into public.supressoes_contato_sinteticas(
 concessionaria_id,lead_id,canal_id,finalidade,evento_origem)
values ('{LOJA_A}','{LEAD_A}','{CANAL_A}',
 'recontato_comercial_sintetico','AUTH_OPTOUT_A_01');
""")

# C07: eventos reais do PostgREST sobre tabelas sintéticas; não são webhooks Meta.
run_sql(f"""
select prumo_private.registrar_callback_c07_sintetico(
'{CANAL_A}','auth-unmatched-A','auth-c07-event-A','INCERTO_SIMULADO',statement_timestamp());
select prumo_private.registrar_callback_c07_sintetico(
'{CANAL_B}','auth-unmatched-B','auth-c07-event-B','FALHOU_SIMULADO',statement_timestamp());
update public.envios_template_sinteticos
set estado='reservado',reservado_em=statement_timestamp(),
    correlacao_externa_ficticia='auth-unmatched-A'
where concessionaria_id='{LOJA_A}'
  and id='d8000000-0000-4000-8000-000000000091';
select prumo_private.conciliar_pendencia_c07_sintetica(
'{A}','{LOJA_A}',
(select id from public.pendencias_reconciliacao_c07_sinteticas
 where concessionaria_id='{LOJA_A}'),
1,'VINCULAR_SINTETICAMENTE',
'Referencia ficticia confirmada apenas para teste REST',
'd8000000-0000-4000-8000-000000000091');
""")

def select(table, person=None):
    token = actors[person][1] if person else None
    return http("GET", "/rest/v1/" + table + "?select=*", token=token)


for person, shop in (("gestora", LOJA_A), ("gestorb", LOJA_B)):
    for table in ("leads_loja", "ciclos_comerciais", "conversas", "mensagens"):
        code, records = select(table, person)
        if code != 200 or len(records) != 1 or records[0]["concessionaria_id"] != shop:
            fail("ACC: gestor " + person + " crossed scope in " + table)
print("PASS AUTH-01: GoTrue login e REST/RLS gestoras A e B isoladas com cliente comum")

for table in ("leads_loja", "conversas", "mensagens"):
    code, records = select(table, "operador")
    if code != 200 or len(records) != 1 or records[0]["concessionaria_id"] != LOJA_A:
        fail("ACC: assigned operator cannot see only assigned case in " + table)
    code, records = select(table, "outsider")
    if code != 200 or records != []:
        fail("ACC: unlinked user was allowed data in " + table)
print("PASS AUTH-02: operador designado somente caso A; usuario sem vinculo bloqueado")
for name, expected in (("gestora", 1), ("gestorb", 0), ("operador", 0), ("outsider", 0)):
    code, rows = select("pendencias_inbound_simulado", name)
    if code != 200 or not isinstance(rows, list) or len(rows) != expected:
        fail("ACC: unauthorized review inbox disclosure for " + name)
print("PASS AUTH-07: pendencia C02 legivel apenas pela gestora da loja A")

schedule_tables = (
    "catalogo_templates_sinteticos",
    "planos_recontato_sinteticos",
    "envios_template_sinteticos",
    "eventos_envio_template_sinteticos",
)
for table in schedule_tables:
    for manager, store in (("gestora", LOJA_A), ("gestorb", LOJA_B)):
        code, rows = select(table, manager)
        if code != 200 or not isinstance(rows, list) or len(rows) != 1 or rows[0]["concessionaria_id"] != store:
            fail("ACC: schedule metadata scope violation for " + manager + " in " + table)
    for user in ("operador", "outsider"):
        code, rows = select(table, user)
        if code != 200 or rows != []:
            fail("ACC: schedule metadata leaked to " + user + " in " + table)
    code, _ = select(table)
    if code not in (401, 403):
        fail("ACC: anonymous schedule table exposed " + table)
    code, _ = http("POST", "/rest/v1/" + table, token=actors["gestora"][1], payload={})
    if code not in (401, 403):
        fail("ACC: direct schedule mutation allowed " + table)
print("PASS AUTH-08: recontatos 4 tabelas, RLS gestor A/B e negativa OP/anon/POST")

for table, counts in (
    ("evidencias_elegibilidade_sinteticas", (1, 1)),
    ("supressoes_contato_sinteticas", (1, 0)),
):
    for person, expected in zip(("gestora", "gestorb"), counts):
        code, rows = select(table, person)
        if code != 200 or not isinstance(rows, list) or len(rows) != expected:
            fail("ACC: C04 gestor wrong count " + person + "/" + table)
        shop = LOJA_A if person == "gestora" else LOJA_B
        if any(row["concessionaria_id"] != shop for row in rows):
            fail("ACC: C04 data leaked cross-shop " + table)
    for person in ("operador", "outsider"):
        code, rows = select(table, person)
        if code != 200 or rows != []:
            fail("ACC: C04 unauthorised reader " + person + "/" + table)
    code, _ = select(table)
    if code not in (401, 403):
        fail("ACC: C04 anonymous disclosure " + table)
    code, _ = http("POST", "/rest/v1/" + table,
                   token=actors["gestora"][1], payload={})
    if code not in (401, 403):
        fail("ACC: C04 user wrote evidence/suppression directly " + table)
print("PASS AUTH-10: C04 RLS gestor A/B, OP/anon negados e sem escrita REST")

review_tables = (
    ("eventos_callback_sinteticos", (1, 1)),
    ("pendencias_reconciliacao_c07_sinteticas", (1, 1)),
    ("associacoes_callback_c07_sinteticas", (1, 0)),
    ("auditoria_reconciliacao_c07_sintetica", (1, 0)),
)
for table, expected_counts in review_tables:
    for person, expected in zip(("gestora", "gestorb"), expected_counts):
        code, rows = select(table, person)
        if code != 200 or not isinstance(rows, list) or len(rows) != expected:
            fail("ACC: C07 REST scoping " + person + "/" + table)
        shop = LOJA_A if person == "gestora" else LOJA_B
        if any(row["concessionaria_id"] != shop for row in rows):
            fail("ACC: C07 cross-store disclosure in " + table)
    for person in ("operador", "outsider"):
        code, rows = select(table, person)
        if code != 200 or rows != []:
            fail("ACC: C07 unauthorized read " + person + "/" + table)
    code, _ = select(table)
    if code not in (401, 403):
        fail("ACC: C07 anon read " + table)
    code, _ = http("POST", "/rest/v1/" + table,
                   token=actors["gestora"][1], payload={})
    if code not in (401, 403):
        fail("ACC: C07 direct mutation " + table)
print("PASS AUTH-11: C07 callback/pendencias/vinculos/auditoria RLS A/B e POST negado")







for table in ("leads_loja", "conversas", "mensagens"):
    code, records = select(table)
    if code not in (401, 403):
        fail("ACC: anon readable " + table + " (HTTP " + str(code) + ")")
print("PASS AUTH-03: anon sem SELECT")

payload = {
    "concessionaria_id": LOJA_A, "conversa_id": CONV_A, "canal_id": CANAL_A,
    "caso_id": CASO_A, "direcao": "saida", "origem": "simulado",
    "conteudo_sintetico": "Resposta sintética local", "enviada_por": OP
}
code, _ = http("POST", "/rest/v1/mensagens", token=actors["operador"][1], payload=payload)
if code not in (200, 201):
    fail("ACC: assigned operator cannot write allowed synthetic reply, HTTP " + str(code))
for person in ("outsider", "gestorb"):
    code, _ = http("POST", "/rest/v1/mensagens", token=actors[person][1], payload=payload)
    if code not in (401, 403):
        fail("ACC: " + person + " wrote A message, HTTP " + str(code))
code, _ = http("POST", "/rest/v1/leads_loja", token=actors["gestora"][1], payload={
    "concessionaria_id": LOJA_A, "telefone_cliente_normalizado": "+5581999000044"
})
if code not in (401, 403):
    fail("ACC: browser wrote lead directly")
print("PASS AUTH-04: insert sintético designado autorizado, escrita interloja e em leads negadas")

# Revocation tested USING THE SAME JWT (no token refresh). No reliance on user metadata.
run_sql(f"""update public.atribuicoes_humanas set encerrada_em=statement_timestamp()
where concessionaria_id='{LOJA_A}' and caso_id='{CASO_A}' and encerrada_em is null;""")
for table in ("leads_loja", "conversas", "mensagens"):
    code, records = select(table, "operador")
    if code != 200 or records != []:
        fail("ACC: revoked operator with existing token reads " + table)
code, _ = http("POST", "/rest/v1/mensagens", token=actors["operador"][1], payload=payload)
if code not in (401, 403):
    fail("ACC: revoked operator still wrote with existing JWT")
print("PASS AUTH-05: remanejamento revoga leitura/escrita sem reemitir JWT")

run_sql(f"""update public.vinculos_papel_escopo set valido_ate=statement_timestamp()
where concessionaria_id='{LOJA_A}' and ator_id='{A}' and papel='gestor';""")
for table in ("leads_loja", "conversas", "mensagens"):
    code, records = select(table, "gestora")
    if code != 200 or records != []:
        fail("ACC: revoked manager with existing JWT reads " + table)
print("PASS AUTH-06: revogacao do vinculo do gestor prevalece sobre JWT ainda valido")
for table in schedule_tables:
    code, rows = select(table, "gestora")
    if code != 200 or rows != []:
        fail("ACC: revoked manager still reads schedule " + table)
print("PASS AUTH-09: revogacao do gestor remove leitura de todos recontatos com JWT existente")
for table, _ in review_tables:
    code, rows = select(table, "gestora")
    if code != 200 or rows != []:
        fail("ACC: revoked manager still reads C07 " + table)

for table in ("evidencias_elegibilidade_sinteticas", "supressoes_contato_sinteticas"):
    code, rows = select(table, "gestora")
    if code != 200 or rows != []:
        fail("ACC: revoked manager still accesses C04 " + table)

# AUTH-12: Trusted backend verifies GoTrue token, live session and database scope.
# No caller-controlled actor_id, no service credentials in client, no external API.
from backend.identity_boundary import (
    AuthenticatedCommands, Denied, InvalidCommand, PsycopgTrustedDatabase,
    SupabaseGoTrueVerifier,
)
import psycopg

verifier = SupabaseGoTrueVerifier(API, ANON)
adapter = AuthenticatedCommands(verifier, PsycopgTrustedDatabase(DB))
payload = {
    "loja_id": LOJA_B,
    "plano_id": "d7000000-0000-4000-8000-000000000092",
    "expected_version": 1,
}
# The manager of B is not revoked; the manager of A was revoked above.
verified_b = verifier.verify("Bearer " + actors["gestorb"][1])
if str(verified_b.actor_id) != B:
    fail("AUTH-12: identity is not issued by GoTrue")
try:
    adapter.execute("Bearer " + actors["gestorb"][1], "cancelar_plano",
                    dict(payload, actor_id=A))
    fail("AUTH-12: spoofed actor_id accepted")
except InvalidCommand:
    pass
for person in ("gestora", "outsider", "operador"):
    try:
        adapter.execute("Bearer " + actors[person][1], "cancelar_plano", payload)
        fail("AUTH-12: unauthorized actor cancelled B plan: " + person)
    except (Denied, psycopg.errors.InsufficientPrivilege):
        pass
result = adapter.execute("Bearer " + actors["gestorb"][1], "cancelar_plano", payload)
if result.get("outcome") != "APPLIED":
    fail("AUTH-12: verified manager B could not cancel local simulated plan")
again = adapter.execute("Bearer " + actors["gestorb"][1], "cancelar_plano", payload)
if again.get("outcome") != "ALREADY_APPLIED":
    fail("AUTH-12: repeated authorized operation not idempotent")
# AUTH-13: a separate LOCAL-only SQL login has no SELECT/DDL privilege.
# The role is provisioned only within this disposable Supabase container.
from backend.identity_boundary import PsycopgGatewayDatabase
run_sql("""
create role prumo_gateway_ci login password 'Test-Only-Synthetic-Gateway-2026!';
grant prumo_s0_gateway to prumo_gateway_ci;
insert into prumo_private.gateway_chaves_assinatura_s0(
 chave_id,segredo,valido_desde,valido_ate,ativo)
 values('f1000000-0000-4000-8000-000000000001',
 decode(repeat('a5',32),'hex'),statement_timestamp()-interval '1 hour',
 statement_timestamp()+interval '1 hour',false);
select prumo_private.alterar_estado_chave_gateway_s0(
 'f1000000-0000-4000-8000-000000000001',1,true,
 'Ativacao de chave exclusivamente ficticia');
""")
u = urllib.parse.urlsplit(DB)
gateway_dsn = ("postgresql://prumo_gateway_ci:"
    + urllib.parse.quote("Test-Only-Synthetic-Gateway-2026!", safe="")
    + "@" + u.hostname + ":" + str(u.port) + u.path)
with psycopg.connect(DB) as root:
    with root.cursor() as cur:
        cur.execute("""
          select p.id from public.pendencias_reconciliacao_c07_sinteticas p
          join public.eventos_callback_sinteticos e
            on e.concessionaria_id=p.concessionaria_id and e.id=p.evento_id
          where p.concessionaria_id=%s::uuid and e.evento_externo_ficticio='auth-c07-event-B'
        """, (LOJA_B,))
        pend_b = cur.fetchone()[0]
        cur.execute("""
          select count(*) from prumo_private.auditoria_gateway_s0
        """)
        if cur.fetchone()[0] != 0:
            fail("AUTH-13: unexpected gateway audit before request")
restricted_db = PsycopgGatewayDatabase(
    gateway_dsn,
    key_id=uuid.UUID("f1000000-0000-4000-8000-000000000001"),
    signing_key=bytes.fromhex("a5" * 32),
)
restricted_gateway = AuthenticatedCommands(verifier, restricted_db)
with psycopg.connect(gateway_dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("set local role prumo_s0_gateway")
        try:
            cur.execute("select count(*) from public.leads_loja")
            fail("AUTH-13: restricted role can read raw leads")
        except psycopg.errors.InsufficientPrivilege:
            pass
# AUTH-14: a stolen SQL login WITHOUT a separate HMAC key cannot call legacy
# privileged wrappers or forge a signed operation. No session UUID is a token.
with psycopg.connect(gateway_dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("set local role prumo_s0_gateway")
        try:
            cur.execute("""
              select prumo_private.gateway_conciliar_c07_s0(
              %s::uuid,%s::uuid,%s::uuid,%s::uuid,1::bigint,
              'ENCERRAR_SEM_PROVA','Teste de negativa ao legado sem prova',null)
            """, (B, str(verified_b.session_id), LOJA_B, str(pend_b)))
            fail("AUTH-14: legacy wrapper still callable by gateway")
        except psycopg.errors.InsufficientPrivilege:
            pass
with psycopg.connect(gateway_dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("set local role prumo_s0_gateway")
        try:
            cur.execute("""
              select prumo_private.gateway_conciliar_c07_assinado_s0(
              %s::uuid,%s::uuid,%s::uuid,%s::uuid,1::bigint,
              'ENCERRAR_SEM_PROVA','Teste de negativa ao login sem segunda chave',
              null,%s::uuid,%s::bigint,%s::uuid,%s::text)
            """, (B, str(verified_b.session_id), LOJA_B, str(pend_b),
                  "f1000000-0000-4000-8000-000000000001",
                  int(__import__("time").time()),
                  str(uuid.uuid4()), "0" * 64))
            fail("AUTH-14: gateway accepted unsigned SQL caller")
        except psycopg.errors.InsufficientPrivilege:
            pass
print("PASS AUTH-14: senha SQL isolada nao chama wrappers legadas ou sem HMAC")
# Failed SQL is rolled back on closing connection; no records are affected.
payload_b = {
    "loja_id": LOJA_B, "pendencia_id": str(pend_b), "expected_version": 1,
    "decisao": "ENCERRAR_SEM_PROVA",
    "justificativa": "Auditoria ficticia de comando escopado com papel limitado",
    "envio_id": None,
}
try:
    restricted_gateway.execute("Bearer " + actors["gestorb"][1],
                               "conciliar_c07", dict(payload_b, actor_id=A))
    fail("AUTH-13: actor_id injection reached restricted gateway")
except InvalidCommand:
    pass
try:
    restricted_gateway.execute("Bearer " + actors["gestorb"][1],
                               "conciliar_c07", dict(payload_b, loja_id=LOJA_A))
    fail("AUTH-13: B manager reconciled shop A")
except Denied:
    pass
result13 = restricted_gateway.execute("Bearer " + actors["gestorb"][1],
                                      "conciliar_c07", payload_b)
if result13.get("outcome") != "APPLIED":
    fail("AUTH-13: authorized gateway reconciliation denied")
result13again = restricted_gateway.execute("Bearer " + actors["gestorb"][1],
                                           "conciliar_c07", payload_b)
if result13again.get("outcome") != "ALREADY_APPLIED":
    fail("AUTH-13: replay of gateway reconciliation not idempotent")
with psycopg.connect(DB) as root:
    with root.cursor() as cur:
        cur.execute("""
          select resultado,count(*) from prumo_private.auditoria_gateway_s0
          where concessionaria_id=%s::uuid
          group by resultado order by resultado
        """, (LOJA_B,))
        if dict(cur.fetchall()) != {"APPLIED": 1, "ALREADY_APPLIED": 1}:
            fail("AUTH-13: successful and replay audit not atomic")
        cur.execute("select count(*) from prumo_private.gateway_provas_usadas_s0")
        if cur.fetchone()[0] != 2:
            fail("AUTH-14: nonce ledger missing two distinct successful proofs")
print("PASS AUTH-13: papel SQL restrito, vinculo sessao/gestor, RLS e auditoria atomica")

# Remove local Auth session: the old signed JWT cannot authorize another DB write.
run_sql(f"delete from auth.sessions where id='{verified_b.session_id}' and user_id='{B}';")
try:
    adapter.execute("Bearer " + actors["gestorb"][1], "cancelar_plano", payload)
    fail("AUTH-12: revoked session still authorized by privileged backend")
except Denied:
    pass
try:
    restricted_gateway.execute("Bearer " + actors["gestorb"][1], "conciliar_c07", payload_b)
    fail("AUTH-13: gateway accepted revoked session")
except Denied:
    pass
print("PASS AUTH-13-REVOKE: sessao revogada impede uso de role restrito")
print("PASS AUTH-12: GoTrue->sessao viva->funcao privada, ator autenticado e escopo/expiracao")





# AUTH-15/16: the accumulated S0/028..034 objects must remain restricted
# when all migrations are applied by the Supabase LOCAL managed stack.
# These tests do not create Meta apps, tokens, real messages, or public RPCs.
run_sql("""
do $audit$
declare
 v_table text;
 v_fn text;
 v_role text;
 v_count integer;
 v_oid oid;
begin
 foreach v_table in array array[
  'aliases_identidade_s0','eventos_identidade_s0',
  'pendencias_identidade_s0','inbox_eventos_s0',
  'tarefas_ingresso_s0','outbox_intencoes_s0',
  'meta_apps_fixture_s0','meta_canais_fixture_s0',
  'historico_tarefas_ingresso_s0','inbox_c02_fixture_s0',
  'aplicacoes_c02_inbox_s0'
 ] loop
  if to_regclass('prumo_private.'||v_table) is null then
    raise exception 'AUTH-15: private S0 table missing: %',v_table;
  end if;
  if not exists(
   select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
   where n.nspname='prumo_private' and c.relname=v_table
     and c.relrowsecurity
  ) then
   raise exception 'AUTH-15: RLS disabled on %',v_table;end if;
  foreach v_role in array array[
    'anon','authenticated','service_role','prumo_s0_gateway',
    'prumo_s0_signer'
  ] loop
   if has_table_privilege(v_role,'prumo_private.'||v_table,
      'SELECT,INSERT,UPDATE,DELETE') then
    raise exception 'AUTH-15: role % may access table %',v_role,v_table;
   end if;
  end loop;
 end loop;
 foreach v_fn in array array[
  'receber_mensagem_identidade_s0','importar_lote_identidade_s0',
  'aceitar_lote_ingresso_s0','aceitar_lote_multicanal_fixture_s0',
  'reservar_ingresso_s0','registrar_resultado_ingresso_s0',
  'reconciliar_lease_expirado_s0','anexar_fixture_c02_s0',
  'aplicar_inbox_c02_s0','validar_prova_c02_s0',
  'validar_applied_com_prova_s0'
 ] loop
  select count(*) into v_count from pg_proc p
   join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='prumo_private' and p.proname=v_fn;
  if v_count<1 then raise exception 'AUTH-15: function absent %',v_fn;end if;
  for v_oid in select p.oid from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='prumo_private' and p.proname=v_fn
  loop
   foreach v_role in array array[
    'anon','authenticated','service_role','prumo_s0_gateway',
    'prumo_s0_signer'
   ] loop
    if has_function_privilege(v_role,v_oid,'EXECUTE') then
     raise exception 'AUTH-15: role % can execute %',v_role,v_fn;
    end if;
   end loop;
  end loop;
 end loop;
 foreach v_fn in array array[
   'inbox_c02_evento_canal_s0','aplicacao_c02_evento_canal_s0',
   'aplicacao_c02_mensagem_canal_s0'
 ] loop
  if not exists(select 1 from pg_constraint where conname=v_fn
    and contype='f') then
   raise exception 'AUTH-15: cross-channel FK missing: %',v_fn;end if;
 end loop;
 if not exists(select 1 from pg_trigger
   where tgname='tarefa_c02_applied_exige_prova_s0' and tgenabled='O')
 or not exists(select 1 from pg_trigger
   where tgname='aplicacao_c02_prova_sem_desvio_s0' and tgenabled='O')
 then raise exception 'AUTH-15: C02 proof guard disabled';end if;
end $audit$;
""")
print("PASS AUTH-15: 028-034 tabelas RLS, FKs/guardas C02 e funcoes privadas sem grants")

# REST must not expose the private schema or its C02 bridge, even to a valid
# user with a manager JWT; no public proxy/worker has been approved.
for person in (None, "gestorb"):
    token = actors[person][1] if person else None
    for path in (
        "/rest/v1/inbox_c02_fixture_s0?select=*",
        "/rest/v1/aplicacoes_c02_inbox_s0?select=*",
    ):
        code, _ = http("GET", path, token=token)
        if code not in (401, 403, 404):
            fail("AUTH-16: private S0 table available from public REST")
    for path in (
        "/rest/v1/rpc/aplicar_inbox_c02_s0",
        "/rest/v1/rpc/registrar_resultado_ingresso_s0",
    ):
        code, _ = http("POST", path, token=token, payload={})
        if code not in (401, 403, 404):
            fail("AUTH-16: privileged S0 RPC available from public REST")
print("PASS AUTH-16: nenhuma tabela privada ou RPC C02/lease exposta ao REST")


# AUTH-17: signed gateway entrypoints have a non-login owner on Supabase
# managed postgres (non-superuser); legacy domain code still intentionally
# runs through postgres-owned wrappers until its separate privilege gate.
run_sql("""
do $auth17$
declare f oid;
begin
 if not exists(select 1 from pg_catalog.pg_roles
 where rolname='prumo_s0_signed_executor'
 and not rolcanlogin and not rolinherit and not rolsuper
 and not rolbypassrls and not rolcreatedb and not rolcreaterole)
 then raise exception 'AUTH-17: unsafe executor role';end if;
 if has_schema_privilege('prumo_s0_signed_executor','prumo_private','CREATE')
 or has_table_privilege('prumo_s0_signed_executor','auth.sessions','SELECT')
 or has_table_privilege('prumo_s0_signed_executor','public.leads_loja','SELECT')
 or has_table_privilege('prumo_s0_signed_executor',
 'prumo_private.gateway_chaves_assinatura_s0','SELECT')
 then raise exception 'AUTH-17: executor direct privileged grants';end if;
 foreach f in array array[
 'prumo_private.gateway_cancelar_plano_assinado_s0(uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)'::regprocedure::oid,
 'prumo_private.gateway_conciliar_c07_assinado_s0(uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)'::regprocedure::oid
 ] loop
  if not exists(select 1 from pg_catalog.pg_proc p where p.oid=f
   and p.prosecdef and pg_catalog.pg_get_userbyid(p.proowner)='prumo_s0_signed_executor')
  or not has_function_privilege('prumo_s0_gateway',f,'EXECUTE')
  or has_function_privilege('authenticated',f,'EXECUTE')
  or has_function_privilege('anon',f,'EXECUTE')
  or has_function_privilege('service_role',f,'EXECUTE')
  then raise exception 'AUTH-17: signed entrypoint owner/ACL';end if;
 end loop;
 if has_function_privilege('prumo_s0_gateway',
   'prumo_private.gateway_cancelar_plano_s0(uuid,uuid,uuid,uuid,bigint)','EXECUTE')
 or has_function_privilege('prumo_s0_gateway',
   'prumo_private.gateway_conciliar_c07_s0(uuid,uuid,uuid,uuid,bigint,text,text,uuid)','EXECUTE')
 then raise exception 'AUTH-17: old unsigned bypass';end if;
end $auth17$;
""")
for role in (None, "gestorb"):
    token = actors[role][1] if role else None
    for route in (
        "/rest/v1/rpc/gateway_cancelar_plano_assinado_s0",
        "/rest/v1/rpc/gateway_conciliar_c07_assinado_s0",
    ):
        code, _ = http("POST", route, token=token, payload={})
        if code not in (401, 403, 404):
            fail("AUTH-17: signed privileged gateway RPC publicly exposed")
print("PASS AUTH-17: Supabase managed admite owner assinado restrito sem REST publico")
