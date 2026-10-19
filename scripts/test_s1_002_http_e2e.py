#!/usr/bin/env python3
"""S1-002/I18: E2E somente local CI (GoTrue, PostgREST e migrations REAIS).
Test-only public bridges; NEVER use against hosted Supabase or production.
"""
import json
import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

api = os.environ["API_URL"].rstrip("/")
db = os.environ["DB_URL"]
anon = os.environ["ANON_KEY"]
if os.environ.get("CI") != "true" or os.environ.get("PRUMO_S1_I18_EPHEMERAL") != "YES":
    raise SystemExit("RECUSADO: exige CI e PRUMO_S1_I18_EPHEMERAL=YES")
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

def http(method, route, bearer=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"apikey": anon, "Authorization": "Bearer " + (bearer or anon)}
    if body is not None:
        headers["Content-Type"] = "application/json"
    try:
        with urlopen(Request(api + route, data=data, headers=headers, method=method), timeout=20) as r:
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
    return http("POST", "/rest/v1/rpc/s1_i18_" + name,
                bearer=token, body=kwargs)

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
print("PASS S1E2E-01: S0/S1 migrations reais aplicadas no Supabase efemero (" +
      str(len(paths)) + " arquivos)")

sql(path="supabase/tests/s1_018_bridge_http_local_only.sql")
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
print("PASS S1E2E-02: cinco contas GoTrue, gestores por equipe e grants A/B reais")

status, data = rpc("pausar", token_g2, p_operador=o3,
                   p_motivo_codigo="AUSENCIA_TEMPORARIA")
blocked(status, "gestor de outra equipe pausou operador")
print("PASS S1E2E-03: gestor alheio negado via JWT real")

status, data = rpc("mover", token_g1, p_loja=store_a,p_caso=case_a,
                   p_atribuicao_esperada=prev_a,p_destino=o4)
ok(status,data,"MOVED")
if data.get("case_id") != case_a:
    raise AssertionError("caso HTTP movimentado incorretamente")
print("PASS S1E2E-04: gestor sem grant da loja move caso A dentro da equipe")

status, _ = rpc("mover", token_g1, p_loja=store_a,p_caso=case_a,
                p_atribuicao_esperada=prev_a,p_destino=o4)
blocked(status, "replay da atribuicao anterior")
print("PASS S1E2E-05: replay de movimento obsoleto negado")

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
print("PASS S1E2E-06: pausa global redistribuiu B e preservou grants A/B")

status, _ = rpc("reativar", token_g2,p_operador=o3)
blocked(status,"G2 reativou O3")
print("PASS S1E2E-07: chefe alheio nao reativa operador")

status, _ = http("POST","/auth/v1/logout",bearer=token_g1)
if status not in (200,204):
    raise AssertionError("logout gestor falhou")
status, _ = rpc("reativar",token_g1,p_operador=o3)
blocked(status,"gestor com JWT revogado reativou")
print("PASS S1E2E-08: logout GoTrue impede reativacao de equipe")

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
print("PASS S1E2E-09: sessao nova reativa sem recuperar carteira antiga")

if sql("select (not has_schema_privilege('authenticated','prumo_private','USAGE') and not has_table_privilege('authenticated','auth.sessions','SELECT'))::text") != "true":
    raise AssertionError("privilegios privados ampliados")
for name in ("s1_mover_atendimento_sessao","s1_pausar_operador_sessao","s1_reativar_operador_sessao"):
    status, _ = http("POST","/rest/v1/rpc/"+name,bearer=login["access_token"],body={})
    if status != 404:
        raise AssertionError("fachada real indevidamente publicada "+name)
print("PASS S1E2E-10: fachadas I14 privadas, pontes apenas na stack isolada")
print("S1-002/I18: 10/10 provas E2E autenticadas com funcoes de negocio REAIS.")
