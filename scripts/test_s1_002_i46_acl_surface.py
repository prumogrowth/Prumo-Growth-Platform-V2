"""I46: further S0 D2 ACL surface, tested with I44/I45 real GoTrue JWTs.
S1 candidate policies are applied only to disposable Supabase CLI PostgreSQL.
Administrative fixture SQL is NOT the actual actor-authorized flow.
"""
if os.environ.get("CI") != "true" or os.environ.get("PRUMO_S1_I44_EPHEMERAL") != "YES":
    raise AssertionError("I46 refused non-ephemeral infrastructure")
if not all(k in globals() for k in ("sql","rows","cases","actors","obj","m1","m4")):
    raise AssertionError("I46 must follow I44+I45")
LOT=obj("62880000",1)
IT1,IT2,IT3=(obj("62890000",i) for i in (1,2,3))
RE2,RE4=(obj("62900000",i) for i in (2,4))
EV1,EV2,EV3=(obj("62910000",i) for i in (1,2,3))
sql(f"""
begin;
-- Restore same-store managerial concession after I45 revoked it.
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values ('{M1}','{LA}','gestor'),('{M4}','{LA}','gestor');
insert into public.lotes_importacao(id,concessionaria_id,chave_importacao)
 values ('{LOT}','{LA}','i46-mixed-store-batch');
insert into public.itens_lote(id,concessionaria_id,lote_id,ordinal_linha,lead_id)
 values('{IT1}','{LA}','{LOT}',1,'{L1}'),
       ('{IT2}','{LA}','{LOT}',2,'{L2}'),
       ('{IT3}','{LA}','{LOT}',3,'{L4}');
insert into public.reencontros_lote(id,concessionaria_id,lote_id,lead_id)
 values('{RE2}','{LA}','{LOT}','{L2}'),
       ('{RE4}','{LA}','{LOT}','{L4}');
insert into public.eventos_status_comercial(id,concessionaria_id,ciclo_id,
 versao_ciclo_apos,status_anterior,status_posterior)
 values ('{EV1}','{LA}','{CY1}',2,
         'em atendimento pelo operador','em atendimento pelo operador'),
        ('{EV2}','{LA}','{CY2}',2,
         'em atendimento pelo operador','em atendimento pelo operador'),
        ('{EV3}','{LA}','{CY3}',2,
         'em atendimento pelo operador','em atendimento pelo operador');
commit;
""")
assert cases(m1) == {CB} and cases(m4) == {CA,CB,CC,CD}
for token in (m1,m4):
    assert rows("lotes_importacao",token) == {LOT}
    assert rows("itens_lote",token) == {IT1,IT2,IT3}
    assert rows("reencontros_lote",token) == {RE2,RE4}
    assert rows("eventos_status_comercial",token) == {EV1,EV2,EV3}
print("PASS I46-01: real JWT reproduces cross-team import/reencounter/status leakage via S0 store grants")

sql(file="supabase/tests/s1_066_proto_d2_surface_local_only.sql")
assert rows("lotes_importacao",m1) == set()
assert rows("lotes_importacao",m4) == set()
assert rows("itens_lote",m1) == {IT1}
assert rows("itens_lote",m4) == {IT1,IT2}
assert rows("reencontros_lote",m1) == set()
assert rows("reencontros_lote",m4) == {RE2}
assert rows("eventos_status_comercial",m1) == {EV2}
assert rows("eventos_status_comercial",m4) == {EV1,EV2,EV3}
print("PASS I46-02: scoped line/reencounter/status read; mixed batch header fails closed")

sql(f"delete from public.vinculos_papel_escopo where "
    f"ator_id in ('{M1}'::uuid,'{M4}'::uuid) "
    f"and concessionaria_id='{LA}'::uuid and papel='gestor'")
assert rows("itens_lote",m1) == {IT1}
assert rows("itens_lote",m4) == {IT1,IT2}
assert rows("eventos_status_comercial",m1) == {EV2}
assert rows("eventos_status_comercial",m4) == {EV1,EV2,EV3}
print("PASS I46-03: removing broad store grant retains only team-related D2 access")

# Effective team access is rechecked against the database, not cached in JWT.
sql(f"update prumo_private.s1_gestor_operadores "
    f"set encerrado_em=statement_timestamp() "
    f"where gestor_id='{M1}' and operador_id='{C3}' and encerrado_em is null")
assert cases(m1) == set()
for table in ("lotes_importacao","itens_lote","reencontros_lote",
              "eventos_status_comercial"):
    assert rows(table,m1) == set()
assert rows("itens_lote",m4) == {IT1,IT2}
print("PASS I46-04: loss of team supervision revokes D2 read with unchanged GoTrue JWT")

for table,body in (
    ("itens_lote",{"concessionaria_id":LA,"lote_id":LOT,"ordinal_linha":9,"lead_id":L1}),
    ("eventos_status_comercial",{"concessionaria_id":LA,"ciclo_id":CY1,
      "versao_ciclo_apos":9,"status_anterior":"em atendimento pelo operador",
      "status_posterior":"em atendimento pelo operador"})):
    status,_=http("POST","/rest/v1/"+table,token=m4,body=body)
    assert status in (401,403), "I46 unexpected DML permission on "+table
assert sql("select count(*) from public.itens_lote "
           f"where concessionaria_id='{LA}'::uuid") == "3"
print("PASS I46-05: authenticated PostgREST cannot mutate S0 D2 through I46 candidate")

catalog=sql("select count(*) from pg_catalog.pg_policies "
            "where schemaname='public' and policyname like 's1_66_%'")
assert catalog == "7", "I46 expected seven reversible, lab-only policies"
assert rows("lotes_importacao",out) == set()
assert rows("itens_lote",out) == set()
assert rows("reencontros_lote",out) == set()
assert rows("eventos_status_comercial",out) == set()
print("PASS I46-06: seven candidate policies enumerated; unassigned outsider stays denied")
print("S1-002/I46: 6/6 scoped D2 ACL assertions with real GoTrue/PostgREST in disposable stack.")
