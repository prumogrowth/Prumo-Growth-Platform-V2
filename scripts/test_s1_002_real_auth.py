#!/usr/bin/env python3
"""I16: teste REAL de GoTrue/PostgREST no Supabase local descartável.
Nunca apontar para Supabase hospedado; sem dados comerciais ou env de produção.
"""
import base64
import json
import os
import subprocess
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

api_url = os.environ["API_URL"].rstrip("/")
db_url = os.environ["DB_URL"]
anon_key = os.environ["ANON_KEY"]
service_key = os.environ["SERVICE_ROLE_KEY"]

if os.environ.get("CI") != "true" or os.environ.get("PRUMO_S1_I16_EPHEMERAL") != "YES":
    raise SystemExit("RECUSADO: CI e PRUMO_S1_I16_EPHEMERAL=YES obrigatorios")
for url in (api_url, db_url):
    parsed = urlparse(url)
    if parsed.hostname not in ("127.0.0.1", "localhost", "::1"):
        raise SystemExit("RECUSADO: endereco deve ser estritamente loopback")
if urlparse(db_url).path not in ("/postgres",):
    raise SystemExit("RECUSADO: banco local Supabase postgres esperado")

def psql(sql=None, file=None):
    args = ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-t", "-A", db_url]
    if sql is not None:
        args += ["-c", sql]
    else:
        args += ["-f", file]
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError("falha SQL fixture I16: " + result.stderr[-1800:])
    return result.stdout.strip()

# Executa apenas objetos de fixtures na instancia local, nunca migrations hospedadas.
psql(file="supabase/tests/s1_016_integracao_gotrue_fixture.sql")
psql(file="supabase/migrations/202610190051_s1_sessao_autorizacao_privada.sql")
psql(file="supabase/migrations/202610190052_s1_verificacao_sessao_gotrue.sql")
psql(file="supabase/tests/s1_016_integracao_gotrue_probe.sql")

def http(method, path, token=None, body=None, extra=None):
    payload = json.dumps(body).encode() if body is not None else None
    headers = {"apikey": anon_key, "Authorization": "Bearer " + (token or anon_key)}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if extra:
        headers.update(extra)
    req = Request(api_url + path, data=payload, headers=headers, method=method)
    try:
        with urlopen(req, timeout=15) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as err:
        raw = err.read().decode()
        try:
            data = json.loads(raw)
        except ValueError:
            data = {"error": raw[:200]}
        return err.code, data

def assert_blocked(status, context):
    if status < 400:
        raise AssertionError(context + ": esperado bloqueio HTTP; obtido " + str(status))

def login():
    status, data = http(
        "POST", "/auth/v1/token?grant_type=password",
        body={"email": "s1-i16@example.test", "password": "SyntheticOnlyPassword_2026!"})
    if status != 200 or not data.get("access_token"):
        raise AssertionError("GoTrue login negado: HTTP " + str(status) + " " + str(data)[:250])
    return data["access_token"], data["user"]["id"]

def jwt_payload(token):
    encoded = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))

status, signup = http(
    "POST", "/auth/v1/signup",
    body={"email": "s1-i16@example.test", "password": "SyntheticOnlyPassword_2026!"})
if status not in (200, 201) or not signup.get("user"):
    raise AssertionError("GoTrue signup local negado: HTTP " + str(status) + " " + str(signup)[:250])
token, user_id = login()
user_uuid = str(uuid.UUID(user_id))
claims = jwt_payload(token)
session_id = str(uuid.UUID(claims["session_id"]))
assert claims["sub"] == user_uuid and claims["role"] == "authenticated"
print("PASS S1HTTP-01: GoTrue real assinou JWT com session_id, role e sub")

count = psql("SELECT count(*) FROM auth.sessions WHERE id='" + session_id
             + "'::uuid AND user_id='" + user_uuid + "'::uuid")
if count != "1":
    raise AssertionError("GoTrue nao criou auth.sessions correspondente: " + count)
psql("INSERT INTO public.atores(id) VALUES ('" + user_uuid + "'::uuid)")
print("PASS S1HTTP-02: sessao e usuario existem em auth.sessions real")

def probe(token):
    return http("POST", "/rest/v1/rpc/s1_i16_prova_sessao", token=token, body={})

# Espera curto periodo para o PostgREST atualizar cache das RPC criadas.
for attempt in range(12):
    status, data = probe(token)
    if status == 200:
        break
    if status == 404 and attempt < 11:
        time.sleep(1)
    else:
        raise AssertionError("RPC canario com token valido HTTP "
                             + str(status) + " " + str(data)[:250])
if data.get("autorizado") is not True or data.get("ator_id") != user_uuid:
    raise AssertionError("helper 052 nao verificou o ator real")
print("PASS S1HTTP-03: PostgREST chamou helper I15 com JWT GoTrue autentico")

status, _ = probe(anon_key)
assert_blocked(status, "anon")
print("PASS S1HTTP-04: anon nao executa canario de sessao")

status, _ = probe(service_key)
assert_blocked(status, "service_role")
print("PASS S1HTTP-05: service_role nao executa canario de sessao")

parts = token.split(".")
parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
status, _ = probe(".".join(parts))
assert_blocked(status, "assinatura JWT adulterada")
print("PASS S1HTTP-06: assinatura JWT adulterada rejeitada em HTTP")

header, payload, signature = token.split(".")
forged = dict(claims)
forged["app_metadata"] = {"papel": "responsavel"}
forged["sub"] = "00000000-0000-4000-8000-000000000999"
new_payload = base64.urlsafe_b64encode(
    json.dumps(forged, separators=(",", ":")).encode()).decode().rstrip("=")
status, _ = probe(header + "." + new_payload + "." + signature)
assert_blocked(status, "JWT claims adulteradas")
print("PASS S1HTTP-07: claims editadas sem assinatura valida rejeitadas")

for name, args in [
    ("s1_mover_atendimento_sessao", {"p_loja": None, "p_caso": None,
       "p_atribuicao_esperada": None, "p_destino": None}),
    ("s1_pausar_operador_sessao", {"p_operador": None, "p_motivo_codigo": None}),
    ("s1_reativar_operador_sessao", {"p_operador": None}),
]:
    status, _ = http("POST", "/rest/v1/rpc/" + name, token=token, body=args)
    if status != 404:
        raise AssertionError("RPC privado acessivel pelo public HTTP "
                             + name + " status=" + str(status))
print("PASS S1HTTP-08: tres fachadas I14 ausentes do schema public API")

status, _ = http("POST", "/rest/v1/rpc/s1_pausar_operador_sessao",
                 token=token, body={"p_operador": None, "p_motivo_codigo": None},
                 extra={"Content-Profile": "prumo_s1_interface"})
if status != 406:
    raise AssertionError("schema de interface indevidamente exposto; HTTP " + str(status))
print("PASS S1HTTP-09: PostgREST nao expoe prumo_s1_interface por profile")

checks = psql("""
select (
 has_schema_privilege('authenticated','prumo_s1_interface','USAGE')
 and not has_schema_privilege('authenticated','prumo_private','USAGE')
 and not has_schema_privilege('anon','prumo_s1_interface','USAGE')
 and not has_schema_privilege('service_role','prumo_s1_interface','USAGE')
 and not has_function_privilege('authenticated',
   'prumo_private.s1_exigir_identidade_sessao()','EXECUTE')
 and not has_table_privilege('authenticated','auth.sessions','SELECT')
)::text
""")
if checks != "true":
    raise AssertionError("ACL privada alterada: " + checks)
print("PASS S1HTTP-10: privilegios reais de Postgres continuam restritos")

status, _ = http("POST", "/auth/v1/logout", token=token)
if status not in (200, 204):
    raise AssertionError("GoTrue logout HTTP " + str(status))
count = psql("SELECT count(*) FROM auth.sessions WHERE id='" + session_id + "'::uuid")
if count != "0":
    raise AssertionError("logout GoTrue nao excluiu sessao real")
print("PASS S1HTTP-11: logout GoTrue remove auth.sessions")

status, _ = probe(token)
assert_blocked(status, "JWT assinado anteriormente apos logout")
print("PASS S1HTTP-12: JWT assinado ainda nao expirado bloqueado apos logout")

token2, user2 = login()
if user2 != user_uuid or jwt_payload(token2)["session_id"] == session_id:
    raise AssertionError("novo login nao criou sessao diferente")
status, data = probe(token2)
if status != 200 or data.get("ator_id") != user_uuid:
    raise AssertionError("nova sessao legitima nao pode autenticar")
print("PASS S1HTTP-13: novo login autentico restaura acesso sem restaurar sessao revogada")
print("S1-002/I16: 13/13 provas HTTP reais, APENAS ambiente descartavel.")
