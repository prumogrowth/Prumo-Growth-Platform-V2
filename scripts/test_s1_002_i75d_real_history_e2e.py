"""I75D real-GoTrue extensions of the I63 test-only historical RLS.

Two phases run within I63's existing ephemeral signed-exception lifetime.
Do not load PR #12 fixtures, mutate S0's session access or promote I63 to
migration. IDs/phone are synthetic. Never deployed/hosted.
"""
if os.environ.get("CI") != "true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL") != "YES":
    raise AssertionError("I75D_ONLY_DISPOSABLE_REAL_GOTRUE")
if any(urlparse(u).hostname not in ("127.0.0.1","localhost","::1") for u in (api,db)):
    raise AssertionError("I75D_REFUSES_REMOTE")
if phase75 == "before_revocation":
    # The original I63 case63h was deliberately unassigned: historical
    # SELECT is contextual only through the active exception on case63.
    oldconv75="e7750000-0000-4000-8000-000000000011"
    oldmsg75="e7750000-0000-4000-8000-000000000012"
    foreignlead75="e7750000-0000-4000-8000-000000000021"
    foreigncycle75="e7750000-0000-4000-8000-000000000022"
    foreigncase75="e7750000-0000-4000-8000-000000000023"
    foreignconv75="e7750000-0000-4000-8000-000000000024"
    foreignmsg75="e7750000-0000-4000-8000-000000000025"
    foreignchannel75="e7750000-0000-4000-8000-000000000026"
    sql(f"""
    insert into public.conversas(
      id,concessionaria_id,lead_id,canal_id,caso_id)
    values('{oldconv75}',{U(store_a)},'{lead63}',{U(channel63)},'{case63h}');
    insert into public.mensagens(
      id,concessionaria_id,conversa_id,canal_id,caso_id,
      direcao,origem,conteudo_sintetico,id_externo)
    values('{oldmsg75}',{U(store_a)},'{oldconv75}',{U(channel63)},'{case63h}',
      'entrada','simulado','I75D older-cycle synthetic text','i75d-old');
    insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
    values('{foreignchannel75}',{U(store_b)},'i75d-foreign-channel');
    insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
    values('{foreignlead75}',{U(store_b)},'+5581886300001');
    insert into public.ciclos_comerciais(id,concessionaria_id,lead_id)
    values('{foreigncycle75}',{U(store_b)},'{foreignlead75}');
    insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
    values('{foreigncase75}',{U(store_b)},'{foreignlead75}','{foreigncycle75}');
    insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
    values('{foreignconv75}',{U(store_b)},'{foreignlead75}',
       '{foreignchannel75}','{foreigncase75}');
    insert into public.mensagens(
      id,concessionaria_id,conversa_id,canal_id,caso_id,
      direcao,origem,conteudo_sintetico,id_externo)
    values('{foreignmsg75}',{U(store_b)},'{foreignconv75}','{foreignchannel75}',
      '{foreigncase75}','entrada','simulado',
      'I75D foreign same-number synthetic text','i75d-foreign');
    """)
    assert sql(f"select count(*) from public.leads_loja a join public.leads_loja b "
       f"on a.telefone_cliente_normalizado=b.telefone_cliente_normalizado "
       f"where a.id='{lead63}' and b.id='{foreignlead75}' "
       "and a.concessionaria_id<>b.concessionaria_id")=="1"
    assert get63("conversas",tok6,(oldconv75,foreignconv75))=={oldconv75}
    assert get63("mensagens",tok6,(oldmsg75,foreignmsg75))=={oldmsg75}
    print("PASS I75D-E2E-01: same-current-contact older CASE and cycle readable using real GoTrue exception")
    assert get63("casos_humanos",tok6,(case63h,foreigncase75))=={case63h}
    assert get63("conversas",tok6,(foreignconv75,))==set()
    assert get63("mensagens",tok6,(foreignmsg75,))==set()
    print("PASS I75D-E2E-02: different store with identical phone denied across case, conversation and message")
    assert get63("mensagens",token_g2,(oldmsg75,foreignmsg75))==set()
    assert get63("conversas",token_g2,(oldconv75,foreignconv75))==set()
    print("PASS I75D-E2E-03: other-team manager cannot get earlier conversation via store-wide grant")

    # Old-case content remains readable, yet historical SELECT must never
    # grant INSERT in a past case or infer dispatch through Meta.
    body75={"concessionaria_id":store_a,"conversa_id":oldconv75,
       "canal_id":channel63,"caso_id":case63h,"direcao":"saida",
       "origem":"simulado","conteudo_sintetico":"I75D denied historical send",
       "enviada_por":op6}
    status75,error75=http("POST","/rest/v1/mensagens",
       bearer=tok6,base=api,body=body75)
    assert status75 in (400,401,403),(status75,error75)
    assert sql("select count(*) from public.mensagens "
       "where conteudo_sintetico='I75D denied historical send'")=="0"
    print("PASS I75D-E2E-04: contextual historical SELECT does not authorize historical INSERT")

    # Actual columns returned by S0's laboratory grants: inspect shape, not
    # infer that D3/D4 or real-media minimization has been approved.
    status75,content75=http("GET",
      "/rest/v1/mensagens?select=id,conteudo_sintetico&id=eq."+oldmsg75,
      bearer=tok6,base=api)
    assert status75==200 and len(content75)==1,(status75,content75)
    assert content75[0]["conteudo_sintetico"]=="I75D older-cycle synthetic text"
    print("PASS I75D-E2E-05: synthetic raw text visibility inventoried; D3/D4 field minimization NOT certified")

elif phase75 == "after_revocation":
    assert get63("casos_humanos",tok6,(case63h,foreigncase75))==set()
    assert get63("conversas",tok6,(oldconv75,foreignconv75))==set()
    assert get63("mensagens",tok6,(oldmsg75,foreignmsg75))==set()
    print("PASS I75D-E2E-06: signed I61 revoke cuts older-cycle history on same live GoTrue JWT")

    # All additional seeded objects removed in reverse FK dependency order
    # WITHOUT changing the original I63 fixture or its subsequent I64 tests.
    sql(f"""
    delete from public.mensagens where id in ('{oldmsg75}','{foreignmsg75}');
    delete from public.conversas where id in ('{oldconv75}','{foreignconv75}');
    delete from public.casos_humanos where id='{foreigncase75}';
    delete from public.ciclos_comerciais where id='{foreigncycle75}';
    delete from public.leads_loja where id='{foreignlead75}';
    delete from public.canais_loja where id='{foreignchannel75}';
    """)
    assert sql("select count(*) from public.mensagens where id::text like 'e7750000-%'")=="0"
    assert sql("select count(*) from public.conversas where id::text like 'e7750000-%'")=="0"
    assert sql("select count(*) from public.leads_loja where id='{foreignlead75}'")=="0"
    assert sql("select count(*) from pg_catalog.pg_policy "
       "where polname like 's1_63_canon_%'")=="8"
    print("PASS I75D-E2E-07: extra histories torn down; 8 candidate I63 policies unchanged")
else:
    raise AssertionError("I75D_UNKNOWN_PHASE")
