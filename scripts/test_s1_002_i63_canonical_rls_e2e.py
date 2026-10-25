"""I63 candidate only: I61 ledger + I62 signed transfer + actual GoTrue JWT RLS.

Runs from I62 E2E after signed stack has been initialized, BEFORE key revoke.
Only Supabase CLI loopback and synthetic data. Never production RLS.
"""
from backend.s1_gateway_excecao_caso_local import LocalSignedCaseExceptionGateway
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL")!="YES":
 raise AssertionError("I63 disposable CI required")
sql(path="supabase/tests/s1_087_rls_excecao_canonica_local_only.sql")
lead63="e7630000-0000-4000-8000-000000000001"
cycle63="e7630000-0000-4000-8000-000000000002"
cycle63h="e7630000-0000-4000-8000-000000000003"
case63="e7630000-0000-4000-8000-000000000004"
case63h="e7630000-0000-4000-8000-000000000005"
attr63="e7630000-0000-4000-8000-000000000006"
conv63="e7630000-0000-4000-8000-000000000007"
conv63pre="e7630000-0000-4000-8000-000000000008"
msg63="e7630000-0000-4000-8000-000000000009"
msg63pre="e7630000-0000-4000-8000-000000000010"
channel63=sql(f"select id from public.canais_loja where concessionaria_id={U(store_a)} order by id limit 1")
if not channel63:raise AssertionError("I63 S0 shop missing simulation channel")
sql(f"""
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('{lead63}',{U(store_a)},'+5581886300001');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values('{cycle63}',{U(store_a)},'{lead63}','aguardando primeiro disparo'),
 ('{cycle63h}',{U(store_a)},'{lead63}','aguardando primeiro disparo');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 values('{case63}',{U(store_a)},'{lead63}','{cycle63}'),
 ('{case63h}',{U(store_a)},'{lead63}','{cycle63h}');
insert into public.atribuicoes_humanas(id,concessionaria_id,caso_id,operador_id)
 values('{attr63}',{U(store_a)},'{case63}',{U(o3)});
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 values('{conv63}',{U(store_a)},'{lead63}',{U(channel63)},'{case63}'),
 ('{conv63pre}',{U(store_a)},'{lead63}',{U(channel63)},null);
insert into public.mensagens(
 id,concessionaria_id,conversa_id,canal_id,caso_id,
 direcao,origem,conteudo_sintetico,id_externo)
 values('{msg63}',{U(store_a)},'{conv63}',{U(channel63)},'{case63}',
 'entrada','simulado','I63 current case synthetic','i63-current'),
 ('{msg63pre}',{U(store_a)},'{conv63pre}',{U(channel63)},null,
 'entrada','simulado','I63 pre-case synthetic','i63-pre');
""")
def get63(table, token, ids):
 allowed=",".join(ids)
 status,records=http("GET",f"/rest/v1/{table}?select=id&id=in.({allowed})",
  bearer=token,base=api)
 assert status==200,(table,status,str(records)[:180])
 return {row["id"] for row in records}
def scope63(token):
 return (get63("casos_humanos",token,(case63,case63h)),
         get63("conversas",token,(conv63,conv63pre)),
         get63("mensagens",token,(msg63,msg63pre)))
assert scope63(tok6)==(set(),set(),set())
print("PASS I63-E2E-01: GoTrue JWT alone/team membership does not expose ungranted S0 history")

app63=LocalSignedCaseExceptionGateway(
 gateway_dsn,SupabaseGoTrueVerifier(api,anon),signer=signer.client,key_id=new_key)
server63=serve_http_policy_local(app63,
 allowed_commands=("mover_excecao","revogar_excecao"),max_requests=40,window_seconds=60)
threading.Thread(target=server63.serve_forever,daemon=True).start()
url63="http://127.0.0.1:"+str(server63.server_address[1])
try:
 status,answer=http("POST","/s1/mover_excecao",bearer=token53,base=url63,
  body={"loja_id":store_a,"caso_id":case63,
        "atribuicao_esperada_id":attr63,"destino_id":op6})
 assert status==200 and answer["outcome"]=="MOVED_CASE_EXCEPTION",(status,answer)
 exception63=answer["exception_id"]
 assert scope63(tok6)==({case63,case63h},{conv63,conv63pre},{msg63,msg63pre})
 print("PASS I63-E2E-02: signed I62 transfer unlocks current/same-contact/pre-case history under real JWT")
 assert scope63(token_g2)==(set(),set(),set())
 print("PASS I63-E2E-03: other team manager cannot read assigned consultant's contact history")
 # A2 pause: no new intake, but existing case and read history are retained.
 result=sql(f"select prumo_private.s1_definir_intake({U(g1)},{U(op6)},true,1)")
 if "INTAKE_PAUSED" not in result:raise AssertionError("I63 failed canonical A2 pause "+result)
 assert scope63(tok6)==({case63,case63h},{conv63,conv63pre},{msg63,msg63pre})
 print("PASS I63-E2E-04: paused intake does not erase authorized historical reads")
 status,data=http("POST","/s1/revogar_excecao",bearer=token53,base=url63,
  body={"excecao_id":exception63})
 assert status==200 and data=={"outcome":"REVOKED_CASE_ACCESS"},(status,data)
 assert scope63(tok6)==(set(),set(),set())
 assert sql(f"select count(*) from prumo_private.s1_excecoes_caso_eventos_i61 "
   f"where excecao_id={U(exception63)} and evento='REVOGADA'")=="1"
 print("PASS I63-E2E-05: signed revoke instantly removes S0 history on the SAME real JWT; audit once")
 status,_=http("POST","/rest/v1/rpc/caso",bearer=tok6,base=api,
  body={"p_loja":store_a,"p_caso":case63,"p_lead":lead63})
 assert status in (401,403,404),status
 print("PASS I63-E2E-06: private boolean policy function not exposed as public PostgREST RPC")
finally:
 server63.shutdown();server63.server_close()
print("I63 6/6 real GoTrue signed canonical exception RLS tests; disposable only")
