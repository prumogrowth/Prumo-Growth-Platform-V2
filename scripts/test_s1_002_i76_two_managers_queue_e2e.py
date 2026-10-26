"""I76 G1: real GoTrue, two unrelated managers explicitly authorized to one
unowned S0 queue; independent signed HTTP LIST/CLAIM and revocation.
Executed inside the existing I55 ephemeral stack; never production.
"""
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL")!="YES":
    raise AssertionError("I76_REQUIRES_EPHEMERAL_GOTRUE")
if any(urlparse(x).hostname not in ("127.0.0.1","localhost","::1") for x in (api,db)):
    raise AssertionError("I76_REFUSES_REMOTE_URL")
lead76a="e7760000-0000-4000-8000-000000000001"
lead76b="e7760000-0000-4000-8000-000000000002"
cycle76a="e7760000-0000-4000-8000-000000000011"
cycle76b="e7760000-0000-4000-8000-000000000012"
# G1 exception: QUEUE visibility by explicit store permission, without
# assigning consultants to the foreign manager's team.
assert sql(f"""select count(*) from prumo_private.s1_gestor_operadores r1
 join prumo_private.s1_gestor_operadores r2
  on r1.operador_id=r2.operador_id
 where r1.gestor_id={U(g1)} and r2.gestor_id={U(g2)}
 and r1.encerrado_em is null and r2.encerrado_em is null""")=="0"
assert sql(f"""select count(*) from public.vinculos_papel_escopo
 where ator_id={U(g2)} and concessionaria_id={U(store_a)}
 and papel='gestor' and valido_ate is null""")=="0"
st76,_=queue55(token_g2)
assert st76==403,("I76 manager without store authorization",st76)
print("PASS I76-G1-01: distinct manager teams and unauthorized foreign manager denied")

sql(f"""
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('{lead76a}',{U(store_a)},'+558188760001'),
       ('{lead76b}',{U(store_a)},'+558188760002');
insert into public.ciclos_comerciais(
 id,concessionaria_id,lead_id,status_comercial)
 values('{cycle76a}',{U(store_a)},'{lead76a}','aguardando primeiro disparo'),
       ('{cycle76b}',{U(store_a)},'{lead76b}','aguardando primeiro disparo');
""")
assert sql(f"select count(*) from prumo_private.s0_fila_humana "
 f"where ciclo_id in ('{cycle76a}','{cycle76b}')")=="0"
sql(f"""update public.ciclos_comerciais
 set status_comercial='em atendimento pelo operador'
 where id in ('{cycle76a}','{cycle76b}')""")
assert sql(f"select count(*) from prumo_private.s0_fila_humana where "
 f"ciclo_id in ('{cycle76a}','{cycle76b}') and estado='pendente' and versao=1")=="2"
print("PASS I76-G1-02: both unowned leads require explicit canonical S0 signal")
sql(f"""insert into public.vinculos_papel_escopo(
 ator_id,concessionaria_id,papel)
 values({U(g2)},{U(store_a)},'gestor')""")
st76,d76=queue55(token_g2)
ok(st76,d76,"QUEUE_LIST")
assert cycle76a in {x["ciclo_id"] for x in d76["items"]}
assert cycle76b in {x["ciclo_id"] for x in d76["items"]}
assert all(set(x)=={"concessionaria_id","lead_id","ciclo_id","versao"}
           for x in d76["items"])
st76,d76=queue55(token53)
ok(st76,d76,"QUEUE_LIST")
assert {cycle76a,cycle76b}.issubset({x["ciclo_id"] for x in d76["items"]})
assert sql(f"""select count(*) from prumo_private.s1_gestor_operadores r1
 join prumo_private.s1_gestor_operadores r2
  on r1.operador_id=r2.operador_id
 where r1.gestor_id={U(g1)} and r2.gestor_id={U(g2)}
 and r1.encerrado_em is null and r2.encerrado_em is null""")=="0"
print("PASS I76-G1-03: two distinct teams with explicit shop grant list same four-field unowned queue")

st76,d76=claim55(token_g2,cycle76a)
ok(st76,d76,"CLAIMED_BY_MANAGER")
st76,err76=claim55(token53,cycle76a)
assert st76==409,(st76,err76)
assert sql(f"""select count(*) from public.casos_humanos
 where ciclo_id='{cycle76a}'""")=="1"
assert sql(f"""select count(*) from public.atribuicoes_humanas a
 join public.casos_humanos h on h.id=a.caso_id
 where h.ciclo_id='{cycle76a}' and a.operador_id={U(g2)}
 and a.encerrada_em is null""")=="1"
assert sql(f"""select count(*) from prumo_private.s0_fila_humana_eventos
 where ciclo_id='{cycle76a}' and resultado='ASSUMIDO'
 and solicitante_id={U(g2)}""")=="1"
print("PASS I76-G1-04: foreign-team manager wins signed CAS; other manager conflicts, one owner and audit")

st76,d76=queue55(token53)
ok(st76,d76,"QUEUE_LIST")
assert cycle76a not in {x["ciclo_id"] for x in d76["items"]}
assert cycle76b in {x["ciclo_id"] for x in d76["items"]}
print("PASS I76-G1-05: claimed lead disappears; unrelated pending lead stays available")

# The special permission is a manager's store grant, NOT a consultant
# cross-team membership and NOT a case-level exception for past assignments.
sql(f"""delete from public.vinculos_papel_escopo
 where ator_id={U(g2)} and concessionaria_id={U(store_a)}
 and papel='gestor'""")
st76,_=queue55(token_g2)
assert st76==403,st76
st76,_=claim55(token_g2,cycle76b)
assert st76==403,st76
assert sql(f"select count(*) from public.casos_humanos "
 f"where ciclo_id='{cycle76b}'")=="0"
assert sql(f"select estado||':'||versao from prumo_private.s0_fila_humana "
 f"where ciclo_id='{cycle76b}'")=="pendente:1"
print("PASS I76-G1-06: removing second manager grant revokes LIST/CLAIM on same GoTrue JWT")

st76,d76=claim55(token53,cycle76b)
ok(st76,d76,"CLAIMED_BY_MANAGER")
st76,_=claim55(token_g2,cycle76b)
assert st76==403,st76
assert sql(f"""select count(*) from public.atribuicoes_humanas a
 join public.casos_humanos h on h.id=a.caso_id
 where h.ciclo_id='{cycle76b}' and a.operador_id={U(g1)}
 and a.encerrada_em is null""")=="1"
assert sql(f"select count(*) from public.casos_humanos "
 f"where ciclo_id in ('{cycle76a}','{cycle76b}')")=="2"
assert sql(f"""select count(*) from prumo_private.s0_fila_humana_eventos
 where ciclo_id in ('{cycle76a}','{cycle76b}')
 and resultado='ASSUMIDO'""")=="2"
assert sql(f"""select count(*) from public.vinculos_papel_escopo
 where ator_id={U(g2)} and concessionaria_id={U(store_a)}
 and papel='gestor'""")=="0"
print("PASS I76-G1-07: original manager claims remaining lead; two isolated owners, two audits, test grant removed")
print("I76 7/7 real GoTrue S0 canonical queue acceptance, no S0 code mutation")
