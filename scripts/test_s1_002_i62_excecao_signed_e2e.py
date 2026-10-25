"""I62 after I55, before I53 rotates signer: real JWT + separated HMAC."""
from backend.s1_gateway_excecao_caso_local import LocalSignedCaseExceptionGateway,_SQL_EXC62
import psycopg

sql(path="supabase/migrations/202610190058_s0_conversa_integridade_contato.sql")
sql(path="supabase/migrations/202610190059_s0_s1_excecao_caso_canonica.sql")
sql(path="supabase/tests/s1_086_excecao_assinada_local_only.sql")
op6,tok6,_,_=person("i62-consultant")
sql(f"""insert into public.atores(id) values({U(op6)});
insert into public.equipe_prumo_s1(ator_id,estado) values({U(op6)},'ativo');
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
values({U(g1)},{U(op6)});""")
lead62="e7620000-0000-4000-8000-000000000001"
cycle62="e7620000-0000-4000-8000-000000000002"
case62="e7620000-0000-4000-8000-000000000003"
attr62="e7620000-0000-4000-8000-000000000004"
sql(f"""insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('{lead62}',{U(store_a)},'+5581886200001');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values('{cycle62}',{U(store_a)},'{lead62}','aguardando primeiro disparo');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 values('{case62}',{U(store_a)},'{lead62}','{cycle62}');
insert into public.atribuicoes_humanas(id,concessionaria_id,caso_id,operador_id)
 values('{attr62}',{U(store_a)},'{case62}',{U(o3)});""")
app62=LocalSignedCaseExceptionGateway(
 gateway_dsn,SupabaseGoTrueVerifier(api,anon),signer=signer.client,key_id=new_key)
server62=serve_http_policy_local(app62,
 allowed_commands=("mover_excecao","revogar_excecao"),max_requests=80,window_seconds=60)
threading.Thread(target=server62.serve_forever,daemon=True).start()
url62="http://127.0.0.1:"+str(server62.server_address[1])
def move62(token,extra=None):
 body={"loja_id":store_a,"caso_id":case62,
       "atribuicao_esperada_id":attr62,"destino_id":op6}
 if extra:body.update(extra)
 return http("POST","/s1/mover_excecao",bearer=token,body=body,base=url62)
try:
 status,data=move62(token_g2)
 assert status==403,("I62 other manager",status)
 status,_=move62(tok6)
 assert status==403,("I62 consultant pretended manager",status)
 print("PASS I62-E2E-01: GoTrue identity derives manager; other team and consultant cannot move case")

 status,_=move62(token53,{"gestor_id":g1})
 assert status==400,status
 status,_=http("POST","/s1/revogar_excecao",bearer=token53,
  body={"excecao_id":case62,"ator_id":g1},base=url62)
 assert status==400,status
 print("PASS I62-E2E-02: strict HTTP forbids caller-supplied gestor/ator IDs")

 status,data=move62(token53)
 assert status==200,(status,data)
 assert data["outcome"]=="MOVED_CASE_EXCEPTION"
 exception_id=data["exception_id"]
 assignment=data["assignment_id"]
 assert sql(f"select count(*) from public.atribuicoes_humanas where id={U(assignment)} "
            f"and operador_id={U(op6)} and encerrada_em is null")=="1"
 assert sql(f"select count(*) from public.vinculos_papel_escopo "
            f"where ator_id={U(op6)} and concessionaria_id={U(store_a)}")=="0"
 print("PASS I62-E2E-03: signed current manager transfers one canonical S0 case without store grant")

 principal=SupabaseGoTrueVerifier(api,anon).verify("Bearer "+token53)
 proof=app62.proof(principal,"REVOKE",(uuid.UUID(exception_id),None,None,None),
     "Bearer "+token53)
 bad=list(proof);bad[2]="MOVE"
 try:
  with psycopg.connect(gateway_dsn,connect_timeout=5) as conn:
   with conn.cursor() as cur:cur.execute(_SQL_EXC62,bad)
 except psycopg.Error as e:assert e.sqlstate=="42501",e.sqlstate
 else:raise AssertionError("I62 changed operation on signed proof")
 print("PASS I62-E2E-04: HMAC operation domain prevents revoke-to-move modification")

 with psycopg.connect(gateway_dsn,connect_timeout=5) as conn:
  with conn.cursor() as cur:
   cur.execute(_SQL_EXC62,proof)
   assert cur.fetchone()[0]["outcome"]=="REVOKED_CASE_ACCESS"
 try:
  with psycopg.connect(gateway_dsn,connect_timeout=5) as conn:
   with conn.cursor() as cur:cur.execute(_SQL_EXC62,proof)
 except psycopg.Error as e:assert e.sqlstate=="42501",e.sqlstate
 else:raise AssertionError("I62 nonce replay accepted")
 print("PASS I62-E2E-05: signed revoke cuts grant, replay denied inside executor")

 status,_=http("POST","/rest/v1/rpc/invocar_excecao_i62",bearer=token53,
                body={"p_ator":g1},base=api)
 assert status in (401,403,404),status
 with psycopg.connect(gateway_dsn,connect_timeout=5) as conn:
  with conn.cursor() as cur:
   try:cur.execute("select count(*) from prumo_private.s1_excecoes_caso_i61")
   except psycopg.Error as e:assert e.sqlstate=="42501",e.sqlstate
   else:raise AssertionError("I62 login reads private data")
 print("PASS I62-E2E-06: PostgREST and signed SQL login cannot inspect private exception table")
finally:
 server62.shutdown();server62.server_close()
print("I62 6/6 real GoTrue and independent mTLS HMAC tests in disposable CI")
