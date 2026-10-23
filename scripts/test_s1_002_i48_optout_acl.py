"""I48: source-exact S0/016 DDL/RLS + real GoTrue/PostgREST negative tests.
Uses only the I44-I47 disposable stack. Not real eligibility/opt-out proof.
"""
from pathlib import Path
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I44_EPHEMERAL")!="YES":
    raise AssertionError("I48 requires disposable CI")
source=Path("supabase/migrations/202610170016_c04_elegibilidade_optout_sintetico.sql").read_text(encoding="utf-8")
boundary="-- Only fictional evidence enables fictional reservations."
if source.count(boundary)!=1 or "create policy supressoes_select_gestor" not in source.split(boundary)[0]:
    raise AssertionError("I48 source fragment no longer matches S0/016")
# Only S0/016 original DDL, RLS, GRANTs. Do not load later routine versions:
# its blanket REVOKE would invalidate earlier-in-lab S1 helpers.
sql(statement=source.split(boundary,1)[0])
EV1,EV2,EV4=(obj("62980000",i) for i in (1,2,4))
SP1,SP2,SP4=(obj("62990000",i) for i in (1,2,4))
sql(f"""
begin;
update public.equipe_prumo_s1 set estado='ativo' where ator_id='{M1}'::uuid;
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('{M1}','{LA}','gestor');
insert into public.evidencias_elegibilidade_sinteticas
 (id,concessionaria_id,lead_id,canal_id,finalidade,referencia_ficticia)
 values('{EV1}','{LA}','{L1}','{CH}','recontato_comercial_sintetico','I48-FAKE-1'),
 ('{EV2}','{LA}','{L2}','{CH}','recontato_comercial_sintetico','I48-FAKE-2'),
 ('{EV4}','{LA}','{L4}','{CH}','recontato_comercial_sintetico','I48-FAKE-4');
insert into public.supressoes_contato_sinteticas
 (id,concessionaria_id,lead_id,canal_id,finalidade,evento_origem)
 values('{SP1}','{LA}','{L1}','{CH}','recontato_comercial_sintetico','I48-SP-1'),
 ('{SP2}','{LA}','{L2}','{CH}','recontato_comercial_sintetico','I48-SP-2'),
 ('{SP4}','{LA}','{L4}','{CH}','recontato_comercial_sintetico','I48-SP-4');
commit;
""")
sql("notify pgrst, 'reload schema'")
for token in (m1,m4):
    assert rows("evidencias_elegibilidade_sinteticas",token)=={EV1,EV2,EV4}
    assert rows("supressoes_contato_sinteticas",token)=={SP1,SP2,SP4}
print("PASS I48-01: JWT reproduces S0/016 store-wide cross-team and no-case eligibility leak")

sql(f"update public.equipe_prumo_s1 set estado='suspenso' where ator_id='{M1}'::uuid")
assert not rows("evidencias_elegibilidade_sinteticas",m1)
assert not rows("supressoes_contato_sinteticas",m1)
sql(f"update public.equipe_prumo_s1 set estado='ativo' where ator_id='{M1}'::uuid")
print("PASS I48-02: nested S0 shop-grant RLS denies suspended manager before candidate")

sql(file="supabase/tests/s1_070_optout_escopo_local_only.sql")
assert rows("evidencias_elegibilidade_sinteticas",m1)=={EV1}
assert rows("supressoes_contato_sinteticas",m1)=={SP1}
assert rows("evidencias_elegibilidade_sinteticas",m4)=={EV1,EV2}
assert rows("supressoes_contato_sinteticas",m4)=={SP1,SP2}
assert not rows("evidencias_elegibilidade_sinteticas",out)
print("PASS I48-03: RLS scopes evidence and suppression by case/lead; orphan lead hidden")

sql(f"delete from public.vinculos_papel_escopo where "
    f"ator_id='{M1}'::uuid and concessionaria_id='{LA}'::uuid and papel='gestor'")
assert rows("evidencias_elegibilidade_sinteticas",m1)=={EV1}
assert rows("supressoes_contato_sinteticas",m1)=={SP1}
print("PASS I48-04: shop-grant revocation leaves team-authorized rows")

sql(f"update prumo_private.s1_gestor_operadores "
    f"set encerrado_em=statement_timestamp() where gestor_id='{M1}'::uuid "
    f"and operador_id='{C3}'::uuid and encerrado_em is null")
assert cases(m1)==set()
assert not rows("evidencias_elegibilidade_sinteticas",m1)
assert not rows("supressoes_contato_sinteticas",m1)
assert rows("evidencias_elegibilidade_sinteticas",m4)=={EV1,EV2}
print("PASS I48-05: team-revocation rescopes same real JWT immediately after COMMIT")

assert sql("select count(*) from public.mensagens "
    f"where conversa_id='{CNULL}'::uuid and caso_id is null")=="1"
for token in (m1,m4,c2,c3,out):
    status,body=http("GET",f"/rest/v1/mensagens?select=id&conversa_id=eq.{CNULL}",token=token)
    assert status==200 and body==[], "I48 unauthorized case-less message read"
for table,body in (
 ("evidencias_elegibilidade_sinteticas",{
  "concessionaria_id":LA,"lead_id":L1,"canal_id":CH,
  "finalidade":"recontato_comercial_sintetico","referencia_ficticia":"I48-FORGED"}),
 ("supressoes_contato_sinteticas",{
  "concessionaria_id":LA,"lead_id":L1,"canal_id":CH,
  "finalidade":"recontato_comercial_sintetico","evento_origem":"I48-FORGED"})):
    code,_=http("POST","/rest/v1/"+table,token=m4,body=body)
    assert code in (401,403), "I48 untrusted client could mutate eligibility"
assert sql("select count(*) from pg_catalog.pg_policies "
           "where schemaname='public' and policyname like 's1_70_%'")=="6"
print("PASS I48-06: case-less message denied, DML denied, six candidate policies enumerated")
print("S1-002/I48: 6/6 real-auth isolated checks; NOT S0 operational homologation.")
