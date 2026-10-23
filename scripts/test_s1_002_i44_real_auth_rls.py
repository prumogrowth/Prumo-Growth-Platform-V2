#!/usr/bin/env python3
"""I44: real GoTrue JWT + PostgREST over shared I43 RLS on ephemeral S0 tables.

This is NOT a migration, deployment, or S0 product integration test.
No synthetic JWT: all actor tokens come from GoTrue login.
"""
import json
import os
import subprocess
import time
import uuid
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

if os.environ.get("CI") != "true" or os.environ.get("PRUMO_S1_I44_EPHEMERAL") != "YES":
    raise SystemExit("I44 REFUSAL: disposable CI stack flags missing")
API = os.environ["API_URL"].rstrip("/")
DB = os.environ["DB_URL"]
ANON = os.environ["ANON_KEY"]
for value in (API, DB):
    u = urlparse(value)
    if u.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise SystemExit("I44 REFUSAL: network endpoint not loopback")
if urlparse(DB).path != "/postgres" or urlparse(API).scheme != "http":
    raise SystemExit("I44 REFUSAL: expected ephemeral Supabase CLI topology")

def sql(statement=None, file=None):
    args = ["psql", "-X", "-v", "ON_ERROR_STOP=1", "-qAt", DB]
    if statement is not None:
        args += ["-c", statement]
    else:
        args += ["-f", file]
    p = subprocess.run(args, text=True, capture_output=True, check=False)
    if p.returncode:
        raise AssertionError("I44 SQL error: " + p.stderr[-1100:])
    return p.stdout.strip()

def http(method, path, token=None, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"apikey": ANON, "Authorization": "Bearer " + (token or ANON)}
    if data is not None:
        headers["Content-Type"] = "application/json"
        headers["Prefer"] = "return=minimal"
    req = Request(API + path, data=data, method=method, headers=headers)
    try:
        with urlopen(req, timeout=20) as resp:
            b = resp.read().decode()
            return resp.status, (json.loads(b) if b else None)
    except HTTPError as err:
        # Avoid printing body content; it might eventually contain PII.
        return err.code, None

def actor(label):
    email = "s1-i44-" + label + "@example.test"
    password = "SyntheticOnly_I44_2026!"
    status, data = http("POST", "/auth/v1/signup",
                        body={"email": email, "password": password})
    if status not in (200, 201) or not data or not data.get("user"):
        raise AssertionError("I44 GoTrue signup " + label + " HTTP " + str(status))
    status, data = http("POST", "/auth/v1/token?grant_type=password",
                        body={"email": email, "password": password})
    if status != 200 or not data or not data.get("access_token"):
        raise AssertionError("I44 GoTrue password login " + label + " HTTP " + str(status))
    uid = str(uuid.UUID(data["user"]["id"]))
    return uid, data["access_token"]

# Install real foundation, baseline RLS and exact shared I43 policy candidates.
sql(file="supabase/tests/s1_064_gotrue_rls_setup_local_only.sql")
actors = {name: actor(name) for name in ("m1", "c2", "c3", "m4", "c5", "outsider")}
M1, C2, C3, M4, C5, OUT = (actors[n][0] for n in
                           ("m1", "c2", "c3", "m4", "c5", "outsider"))

LA = "62220000-0000-4000-8000-000000000001"
LB = "62220000-0000-4000-8000-000000000002"
def obj(prefix, number):
    return prefix + "-0000-4000-8000-" + str(number).zfill(12)

# All interpolated actor UUIDs were parsed through uuid.UUID above.
sql(f"""
begin;
insert into public.atores(id) values
 ('{M1}'),('{C2}'),('{C3}'),('{M4}'),('{C5}'),('{OUT}');
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id in
 ('{M1}','{C2}','{C3}','{M4}','{C5}','{OUT}');
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values('{M1}','{C2}'),('{M1}','{C3}'),('{M4}','{C5}');
insert into public.concessionarias(id,nome_operacional)
 values('{LA}','I44 loja A ficticia'),('{LB}','I44 loja B ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values ('{C2}','{LA}','operador'),('{C2}','{LB}','operador'),
 ('{C5}','{LA}','operador'),('{C3}','{LA}','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values ('{obj("62330000",1)}','{LA}','+5581888844441'),
 ('{obj("62330000",2)}','{LA}','+5581888844442'),
 ('{obj("62330000",3)}','{LB}','+5581888844441');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('62440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i=4 then '{LB}'::uuid else '{LA}'::uuid end,
 case when i in (1,2) then '{obj("62330000",1)}'::uuid
 when i=3 then '{obj("62330000",2)}'::uuid
 else '{obj("62330000",3)}'::uuid end,
 'em atendimento pelo operador' from generate_series(1,4) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('62550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 c.concessionaria_id,c.lead_id,c.id from generate_series(1,4) i
 join public.ciclos_comerciais c on c.id=
 ('62440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
 values('62660000-0000-4000-8000-000000000001','{LA}','i44-synthetic-A'),
       ('62660000-0000-4000-8000-000000000002','{LB}','i44-synthetic-B');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 select ('62770000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 h.concessionaria_id,h.lead_id,
 case when i=4 then '62660000-0000-4000-8000-000000000002'::uuid
 else '62660000-0000-4000-8000-000000000001'::uuid end,h.id
 from generate_series(1,4) i join public.casos_humanos h on
 h.id=('62550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
 direcao,origem,conteudo_sintetico,id_externo)
 select co.concessionaria_id,co.id,co.canal_id,co.caso_id,
 'entrada','simulado','I44 example '||i,'i44-in-'||i
 from generate_series(1,4) i join public.conversas co on
 co.id=('62770000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select h.concessionaria_id,h.id,
 case when right(h.id::text,1)='3' then '{C5}'::uuid else '{C2}'::uuid end
 from public.casos_humanos h where h.id::text like '62550000-%';
update public.atribuicoes_humanas
 set encerrada_em=greatest(atribuida_em,statement_timestamp())
 where caso_id='62550000-0000-4000-8000-000000000001';
update public.atribuicoes_humanas
 set encerrada_em=greatest(atribuida_em,statement_timestamp())
 where caso_id='62550000-0000-4000-8000-000000000002';
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('{LA}','62550000-0000-4000-8000-000000000002','{C3}');
insert into prumo_private.s1_excecoes_55(
 concessionaria_id,caso_id,atribuicao_id,operador_id,gestor_id)
 select a.concessionaria_id,a.caso_id,a.id,a.operador_id,'{M1}'::uuid
 from public.atribuicoes_humanas a where a.caso_id=
 '62550000-0000-4000-8000-000000000002'
 and a.operador_id='{C3}' and a.encerrada_em is null;
-- Retira grant temporario de provisionamento; entitlement continua por caso.
delete from public.vinculos_papel_escopo where ator_id='{C3}';
commit;
""")
if sql("select count(*) from public.vinculos_papel_escopo where ator_id='"
       + C3 + "'::uuid") != "0":
    raise AssertionError("I44 accidentally granted store access")
print("PASS I44-01: six real GoTrue accounts, S0 rows, no broad store grant for exceptional operator")

sql("notify pgrst, 'reload schema'")
def rows(table, token=None, key="id"):
    for attempt in range(12):
        status, data = http("GET", "/rest/v1/" + table + "?select=" + key,
                            token=token)
        if status == 404 and attempt < 11:
            time.sleep(1)
            continue
        if status != 200 or not isinstance(data, list):
            raise AssertionError("I44 GET " + table + " HTTP " + str(status))
        return {str(row[key]) for row in data}
    raise AssertionError("I44 PostgREST schema cache failed: " + table)

def cases(token=None):
    return rows("casos_humanos", token)

CA, CB, CC, CD = (obj("62550000", i) for i in range(1, 5))
m1, c2, c3, m4, c5, out = (actors[k][1] for k in
                           ("m1", "c2", "c3", "m4", "c5", "outsider"))

assert cases(m1) == {CA, CB, CD}, "I44 M1 lost historical team cases or leaked cross-team"
assert cases(m4) == {CC}, "I44 M4 leaked another team"
assert cases(c2) == {CD}, "I44 previous owner recovered case from store grant"
assert cases(c5) == {CC}, "I44 ordinary case owner lost case"
assert cases(out) == set(), "I44 outsider bypassed RLS"
assert len(rows("conversas", m1)) == 3
assert len(rows("mensagens", m1)) == 3
print("PASS I44-02: real JWT Gestor reads current/history of own team only (no store grant)")

assert cases(c3) == {CA, CB}, "I44 per-case exception lacks same-contact history"
assert len(rows("conversas", c3)) == 2
assert len(rows("mensagens", c3)) == 2
assert len(rows("atribuicoes_humanas", c3)) == 1
assert len(rows("s1_62_historico_contato_resumo", c3, key="caso_id")) == 2
for table in ("leads_loja", "ciclos_comerciais", "concessionarias", "canais_loja"):
    assert not rows(table, c3), "I44 exceptional operator gained broad access: " + table
print("PASS I44-03: real JWT exceptional operator sees only case and same-contact history")

status, public_rows = http("GET", "/rest/v1/casos_humanos?select=id")
if status not in (401, 403) and not (status == 200 and public_rows == []):
    raise AssertionError("I44 anon read cases HTTP " + str(status))
status, _ = http("POST", "/rest/v1/mensagens", c3, {
    "concessionaria_id": LA,
    "conversa_id": obj("62770000", 1),
    "canal_id": obj("62660000", 1),
    "caso_id": CA,
    "direcao": "saida",
    "origem": "simulado",
    "conteudo_sintetico": "I44 forbidden write to historical case",
    "enviada_por": C3,
})
if status < 400:
    raise AssertionError("I44 exception sent from historical case HTTP " + str(status))
status, _ = http("POST", "/rest/v1/mensagens", c3, {
    "concessionaria_id": LA,
    "conversa_id": obj("62770000", 2),
    "canal_id": obj("62660000", 1),
    "caso_id": CB,
    "direcao": "saida",
    "origem": "simulado",
    "conteudo_sintetico": "I44 synthetic current case response",
    "enviada_por": C3,
})
if status not in (200, 201, 204):
    raise AssertionError("I44 current case write denied HTTP " + str(status))
print("PASS I44-04: real REST writes denied for history; current assigned case accepted")

# Explicit DB-side revocation is simulated by trusted postgres executor.
n = sql("with changed as (update prumo_private.s1_excecoes_55 "
        "set revogada_em=statement_timestamp() "
        "where operador_id='" + C3 + "'::uuid and revogada_em is null "
        "returning id) select count(*) from changed")
if n != "1":
    raise AssertionError("I44 expected exactly one revoked entitlement")
assert cases(c3) == set(), "I44 revocation did not cut real REST case read"
assert not rows("conversas", c3)
assert not rows("mensagens", c3)
assert not rows("s1_62_historico_contato_resumo", c3, key="caso_id")
status, _ = http("POST", "/rest/v1/mensagens", c3, {
    "concessionaria_id": LA,
    "conversa_id": obj("62770000", 2),
    "canal_id": obj("62660000", 1),
    "caso_id": CB,
    "direcao": "saida",
    "origem": "simulado",
    "conteudo_sintetico": "I44 prohibited post-revocation",
    "enviada_por": C3,
})
if status < 400:
    raise AssertionError("I44 revoked operator sent message HTTP " + str(status))
assert cases(m1) == {CA, CB, CD}
assert cases(m4) == {CC}
assert sql("select count(*) from public.atribuicoes_humanas where "
           "caso_id='" + CB + "'::uuid and encerrada_em is null") == "1"
print("PASS I44-05: real REST JWT loses case/history/send immediately after revocation; manager and S0 ownership preserved")

parts = c3.split(".")
parts[2] = ("Z" if parts[2][0] != "Z" else "Y") + parts[2][1:]
status, _ = http("GET", "/rest/v1/casos_humanos?select=id",
                 token=".".join(parts))
if status != 401:
    raise AssertionError("I44 modified GoTrue JWT was not rejected")
print("PASS I44-06: REST rejected tampered real GoTrue JWT")

# No identity token, password or key appears in CI output.
print("S1-002/I44: real GoTrue+PostgREST per-case RLS 6/6 scenarios in disposable local stack.")


# I45 runs only after I44's successful six checks on this disposable stack.
from pathlib import Path
_i45 = Path("scripts/test_s1_002_i45_scope_audit.py")
exec(compile(_i45.read_text(encoding="utf-8"), str(_i45), "exec"), globals())


# I46: independent indirect-D2 ACL regression with same local GoTrue identities.
from pathlib import Path
_i46 = Path("scripts/test_s1_002_i46_acl_surface.py")
exec(compile(_i46.read_text(encoding="utf-8"), str(_i46), "exec"), globals())


# I47: audit post-038 objects with same loopback stack and real GoTrue JWTs.
from pathlib import Path
_i47 = Path("scripts/test_s1_002_i47_indirect_acl.py")
exec(compile(_i47.read_text(encoding="utf-8"), str(_i47), "exec"), globals())


# I48: real-auth eligibility and case-less negative regressions, same ephemeral stack.
import runpy
runpy.run_path('scripts/test_s1_002_i48_optout_acl.py', init_globals=globals())
