#!/usr/bin/env python3
"""CFI-01 verification with REAL local Supabase GoTrue and physical PG17.

Uses the Supabase CLI's throwaway Auth + PostgREST + database, never remote.
No production keys, hosted database, customer messages, API OpenAI or Meta.
The CFI01 database adapter remains postgres-privileged LOCAL ONLY.
"""
import base64
import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import uuid

from backend.s0_cfi01_authenticated_commands_local import CommandState
from backend.s0_cfi01_atomic_commands_local import S0CFI01AtomicCommandsLocal

def demand(condition, message):
    if not condition:
        raise AssertionError("CFI01_AUTH_REAL_LOCAL: " + message)

def local_env():
    proc=subprocess.run(
        ["supabase","status","--output","env"], check=True,
        capture_output=True,text=True)
    values={}
    for line in proc.stdout.splitlines():
        if "=" in line and not line.startswith("#"):
            name,value=line.split("=",1)
            values[name.strip()]=value.strip().strip('"').strip("'")
    for name in ("API_URL","ANON_KEY","DB_URL"):
        demand(bool(values.get(name)), "missing local CLI config "+name)
    api=urllib.parse.urlsplit(values["API_URL"])
    db=urllib.parse.urlsplit(values["DB_URL"])
    demand(api.scheme=="http" and api.hostname in ("localhost","127.0.0.1","::1"),
           "auth must be HTTP loopback")
    demand(db.scheme in ("postgresql","postgres") and
           db.hostname in ("localhost","127.0.0.1","::1") and
           db.port == 54322 and db.path=="/postgres" and db.username=="postgres" and
           not db.query and not db.fragment, "DB must be disposable Supabase local port 54322")
    return values

def request(api,key,method,path,payload=None,token=None):
    raw=None if payload is None else json.dumps(payload).encode("utf-8")
    headers={"apikey":key,"Content-Type":"application/json"}
    if token is not None:
        headers["Authorization"]="Bearer "+token
    q=urllib.request.Request(api+path,data=raw,headers=headers,method=method)
    try:
        with urllib.request.urlopen(q,timeout=10) as response:
            data=response.read(65536)
            return response.status,(json.loads(data) if data else {})
    except urllib.error.HTTPError as e:
        return e.code,{}

def register(api,key):
    email="prumo-cfi01-"+uuid.uuid4().hex[:18]+"@example.invalid"
    passwd="Only-Local-CFI01-Test!X8b2"
    status,body=request(api,key,"POST","/auth/v1/signup",
                        {"email":email,"password":passwd})
    demand(status in (200,201) and bool(body.get("user")),"real GoTrue signup failed")
    status,body=request(api,key,"POST","/auth/v1/token?grant_type=password",
                        {"email":email,"password":passwd})
    demand(status==200 and bool(body.get("access_token")),"real GoTrue login failed")
    return uuid.UUID(body["user"]["id"]),body["access_token"]

def sql_file(db,path):
    subprocess.run(["psql","-X","-q","-v","ON_ERROR_STOP=1",db,"-f",path],
                   check=True,stdout=subprocess.DEVNULL)

def main():
    local=local_env()
    api,key,db=local["API_URL"],local["ANON_KEY"],local["DB_URL"]
    # Isolated opt-in for /postgres ONLY at Supabase CLI local port 54322.
    os.environ["PRUMO_CFI01_SUPABASE_LOCAL_AUTH_TEST"]="1"
    sql_file(db,"supabase/tests/s0_cfi01_s1_038_reference_local_only.sql")
    sql_file(db,"supabase/tests/s0_cfi01_human_closure_table_local_only.sql")
    sql_file(db,"supabase/tests/s0_cfi01_signed_prerequisite_local_only.sql")
    sql_file(db,"supabase/tests/s0_cfi01_atomic_owner_local_only.sql")
    import psycopg
    operator,token=register(api,key)
    outsider,outsider_token=register(api,key)
    store=uuid.uuid4();lead=uuid.uuid4();cycle=uuid.uuid4()
    case=uuid.uuid4();assignment=uuid.uuid4();channel=uuid.uuid4()
    conversation=uuid.uuid4();msg=uuid.uuid4()
    with psycopg.connect(db) as connection:
        with connection.cursor() as c:
            c.execute("insert into public.atores(id) values (%s),(%s)",(operator,outsider))
            c.execute("""insert into public.concessionarias(id,nome_operacional)
                         values (%s,'S0 CFI01 AUTH CI')""",(store,))
            c.execute("""insert into public.vinculos_papel_escopo
                         (ator_id,concessionaria_id,papel)
                         values (%s,%s,'operador')""",(operator,store))
            c.execute("""insert into public.leads_loja
                         (id,concessionaria_id,telefone_cliente_normalizado)
                         values (%s,%s,'+5581999888877')""",(lead,store))
            c.execute("""insert into public.ciclos_comerciais
                         (id,concessionaria_id,lead_id,status_comercial,versao_registro)
                         values (%s,%s,%s,'em atendimento pelo operador',1)""",
                      (cycle,store,lead))
            c.execute("""insert into public.casos_humanos
                         (id,concessionaria_id,lead_id,ciclo_id)
                         values (%s,%s,%s,%s)""",(case,store,lead,cycle))
            c.execute("""insert into public.atribuicoes_humanas
                         (id,concessionaria_id,caso_id,operador_id)
                         values (%s,%s,%s,%s)""",(assignment,store,case,operator))
            c.execute("""insert into public.equipe_prumo_s1(ator_id,estado)
                         values (%s,'ativo'),(%s,'ativo')""",(operator,outsider))
            c.execute("""insert into public.canais_loja
                         (id,concessionaria_id,identificador_emissor)
                         values (%s,%s,%s)""",(channel,store,str(channel)))
            c.execute("""insert into public.conversas
                         (id,concessionaria_id,lead_id,canal_id,caso_id)
                         values (%s,%s,%s,%s,%s)""",
                      (conversation,store,lead,channel,case))
            c.execute("""insert into public.mensagens
                         (id,concessionaria_id,conversa_id,canal_id,caso_id,
                          direcao,origem,conteudo_sintetico,id_externo)
                         values (%s,%s,%s,%s,%s,'entrada','simulado',
                                 'frase ficticia no CI',%s)""",
                      (msg,store,conversation,channel,case,str(msg)))

    # Real GoTrue + signed nonce/HMAC with one atomic transaction under
    # the restricted SQL login; owner is NOLOGIN/NOSUPERUSER subject to RLS.
    # All keys and role data are synthetic and this remains LAB-ONLY.
    u=urllib.parse.urlsplit(db)
    restricted=(f"postgresql://prumo_cfi01_pgtest_login:"
                f"cf-i01-disposable-test-only-not-production@{u.hostname}:{u.port}/postgres")
    gate=S0CFI01AtomicCommandsLocal(
        api,key,restricted,
        key_id=uuid.UUID("cfeed000-0000-4000-8000-000000000001"),
        signing_key=bytes.fromhex(
          "1160b59cd3466f55112233445566778899aabbccddeeff001122334455667788"))
    payload=dict(case_ref=str(case),expected_cycle_version=1,
                 idempotency_key='real-gotrue-cfi01-key')
    result=gate.execute("Bearer "+token,"capture_human_closure",payload)
    if result.state is not CommandState.CAPTURED_LOCAL_ONLY:
        # DISPOSABLE AUTH-CI DIAGNOSTIC ONLY. Do not print JWT, keys,
        # identifiers, input payload, SQL or personal data.
        import hashlib, hmac, time
        from backend.s0_cfi01_atomic_commands_local import _ATOMIC_SQL
        principal=gate._identity.verify("Bearer "+token)
        issued=int(time.time())
        nonce=uuid.uuid4()
        material=gate._material('capture_human_closure',principal,case,1,None,
                                payload['idempotency_key'],gate._key_id,issued,nonce)
        proof=hmac.new(gate._secret,material,hashlib.sha256).hexdigest()
        try:
            with psycopg.connect(restricted,connect_timeout=5) as diagnostic_db:
                diagnostic_db.execute(_ATOMIC_SQL,(
                    'capture_human_closure',operator,principal.session_id,
                    case,1,None,payload['idempotency_key'],gate._key_id,
                    issued,nonce,proof)).fetchall()
            raise AssertionError("Unexpected raw SQL success after DENIED")
        except psycopg.Error as error:
            name=(getattr(error.diag,'message_primary',None) or '')
            # Permit only a narrow code from our private SQL or generic ACL
            # diagnostic, never values or generated SQL.
            reason=(name if name.startswith('CFI01_ATOMIC_') else
                    'DATABASE_ACL_OR_RLS_ERROR')
            print('CFI01_LAB_DIAGNOSTIC:',error.sqlstate,reason)
    demand(result.state is CommandState.CAPTURED_LOCAL_ONLY
           and bool(result.closure_event_ref),
           "real token failed to capture; state="+result.state.value)
    print("PASS CFI01-AUTH-01 real GoTrue bearer + S0/S1 PG17 capture")

    recheck_payload={**payload,"closure_event_ref":result.closure_event_ref}
    second=gate.execute("Bearer "+token,"recheck_human_closure",recheck_payload)
    demand(second.state is CommandState.VERIFIED_REVIEW_ONLY_LOCAL,
           "real GoTrue recheck not verified")
    print("PASS CFI01-AUTH-02 verified real token on separate post-F03 recheck")

    stranger=gate.execute("Bearer "+outsider_token,"capture_human_closure",payload)
    demand(stranger.state is CommandState.DENIED,"other authenticated user gained assigned case")
    print("PASS CFI01-AUTH-03 authenticated outside operator blocked from case")

    # Change the authenticated JWT's actual payload bytes but keep its
    # original signature. Flipping one trailing Base64URL character is NOT
    # reliable: unused padding bits can decode to identical bytes.
    parts=token.split(".")
    demand(len(parts)==3,"GoTrue JWT did not contain three segments")
    old_payload=base64.urlsafe_b64decode(
        parts[1]+"="*((-len(parts[1]))%4))
    fake_claims=json.loads(old_payload)
    fake_claims["sub"]=str(outsider)
    forged_payload=base64.urlsafe_b64encode(
        json.dumps(fake_claims,separators=(",",":")).encode()
    ).decode().rstrip("=")
    demand(forged_payload != parts[1],"JWT mutation did not change payload")
    tampered=".".join((parts[0],forged_payload,parts[2]))
    invalid=gate.execute("Bearer "+tampered,"capture_human_closure",payload)
    demand(invalid.state is CommandState.DENIED,"tampered genuine JWT passed GoTrue")
    print("PASS CFI01-AUTH-04 invalid signature rejected by real GoTrue")

    with psycopg.connect(db) as connection:
        connection.execute("update public.equipe_prumo_s1 set estado='suspenso' where ator_id=%s",
                           (operator,))
    denied=gate.execute("Bearer "+token,"recheck_human_closure",recheck_payload)
    demand(denied.state in (CommandState.DENIED,CommandState.BLOCKED_S1),
           "team suspension ignored by signed preflight or full recheck")
    print("PASS CFI01-AUTH-05 team suspension revokes review with same GoTrue JWT")

    with psycopg.connect(db) as connection:
        connection.execute("update public.equipe_prumo_s1 set estado='ativo' where ator_id=%s",
                           (operator,))
        new_msg=uuid.uuid4()
        connection.execute("""insert into public.mensagens
            (id,concessionaria_id,conversa_id,canal_id,caso_id,
             direcao,origem,conteudo_sintetico,id_externo)
             values (%s,%s,%s,%s,%s,'entrada','simulado','novo inbound',%s)""",
            (new_msg,store,conversation,channel,case,str(new_msg)))
    stale=gate.execute("Bearer "+token,"recheck_human_closure",recheck_payload)
    demand(stale.state is CommandState.STALE,"new inbound did not invalidate receipt")
    print("PASS CFI01-AUTH-06 changed conversation invalidates F03 review")

    with psycopg.connect(db) as connection:
        connection.execute("delete from auth.sessions where user_id=%s",(operator,))
    revoked=gate.execute("Bearer "+token,"recheck_human_closure",recheck_payload)
    demand(revoked.state is CommandState.DENIED,"revoked GoTrue session retained authority")
    print("PASS CFI01-AUTH-07 GoTrue session deletion revokes review")

    with psycopg.connect(db) as connection:
        count=connection.execute("""select count(*) from
            prumo_private.cfi01_human_closure_events_local
            where caso_id=%s""",(case,)).fetchone()[0]
        commercial=connection.execute(
            "select status_comercial from public.ciclos_comerciais where id=%s",
            (cycle,)).fetchone()[0]
    demand(count==1 and commercial=="em atendimento pelo operador",
           "unexpected duplicate receipt or commercial status mutation")
    print("PASS CFI01-AUTH-08 exactly one technical receipt and no sale/bank state")

if __name__=="__main__":
    main()
