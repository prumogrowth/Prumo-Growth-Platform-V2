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
# Remove local Auth session: the old signed JWT cannot authorize another DB write.
run_sql(f"delete from auth.sessions where id='{verified_b.session_id}' and user_id='{B}';")
try:
    adapter.execute("Bearer " + actors["gestorb"][1], "cancelar_plano", payload)
    fail("AUTH-12: revoked session still authorized by privileged backend")
except Denied:
    pass
print("PASS AUTH-12: GoTrue->sessao viva->funcao privada, ator autenticado e escopo/expiracao")



