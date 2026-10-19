\set ON_ERROR_STOP on
-- WA40: disposable PG17 only. Requires S0/030+040, all data rolled back.
begin;
insert into public.concessionarias(id,nome_operacional) values
 ('e2000000-0000-4000-8000-000000000001','WA40 loja A ficticia'),
 ('e2000000-0000-4000-8000-000000000002','WA40 loja B ficticia');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('e3000000-0000-4000-8000-000000000001','e2000000-0000-4000-8000-000000000001','WA40_EMISSOR_A1'),
 ('e3000000-0000-4000-8000-000000000002','e2000000-0000-4000-8000-000000000001','WA40_EMISSOR_A2'),
 ('e3000000-0000-4000-8000-000000000003','e2000000-0000-4000-8000-000000000002','WA40_EMISSOR_B1'),
 ('e3000000-0000-4000-8000-000000000004','e2000000-0000-4000-8000-000000000001','WA40_EMISSOR_A3'),
 ('e3000000-0000-4000-8000-000000000005','e2000000-0000-4000-8000-000000000002','WA40_EMISSOR_B2');
insert into prumo_private.meta_apps_fixture_s0(app_ref,concessionaria_id) values
 ('FIXTURE_WA40_APP_A','e2000000-0000-4000-8000-000000000001'),
 ('FIXTURE_WA40_APP_B','e2000000-0000-4000-8000-000000000002');
insert into prumo_private.meta_canais_fixture_s0(
 app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref) values
 ('FIXTURE_WA40_APP_A','e2000000-0000-4000-8000-000000000001',
  'e3000000-0000-4000-8000-000000000001','FIXTURE_WA40_WABA_A','FIXTURE_WA40_PHONE_A1'),
 ('FIXTURE_WA40_APP_A','e2000000-0000-4000-8000-000000000001',
  'e3000000-0000-4000-8000-000000000002','FIXTURE_WA40_WABA_A','FIXTURE_WA40_PHONE_A2'),
 ('FIXTURE_WA40_APP_B','e2000000-0000-4000-8000-000000000002',
  'e3000000-0000-4000-8000-000000000003','FIXTURE_WA40_WABA_B','FIXTURE_WA40_PHONE_B1');

-- WA40-01: same channel may not be associated with a second sender.
do $wa40$
begin
 begin
  insert into prumo_private.meta_canais_fixture_s0(
    app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref)
  values('FIXTURE_WA40_APP_A','e2000000-0000-4000-8000-000000000001',
    'e3000000-0000-4000-8000-000000000001',
    'FIXTURE_WA40_WABA_ALT','FIXTURE_WA40_PHONE_ALT');
  raise exception 'FAIL WA40-01: a channel acquired a second sender';
 exception when unique_violation then null;
 end;
 if (select count(*) from prumo_private.meta_canais_fixture_s0
      where canal_id='e3000000-0000-4000-8000-000000000001')<>1
 then raise exception 'FAIL WA40-01: inconsistent registry'; end if;
end $wa40$;
\echo 'PASS WA40-01: one WABA/phone binding per internal channel'

-- WA40-02: the reverse binding is exclusive even across channel IDs.
do $wa40$
begin
 begin
  insert into prumo_private.meta_canais_fixture_s0(
    app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref)
  values('FIXTURE_WA40_APP_A','e2000000-0000-4000-8000-000000000001',
    'e3000000-0000-4000-8000-000000000004',
    'FIXTURE_WA40_WABA_A','FIXTURE_WA40_PHONE_A1');
  raise exception 'FAIL WA40-02: same sender assigned to second channel';
 exception when unique_violation then null;
 end;
end $wa40$;
\echo 'PASS WA40-02: one channel per WABA/phone binding'

-- WA40-03: a Meta App cannot be rebound to another dealership.
do $wa40$
begin
 begin
  insert into prumo_private.meta_canais_fixture_s0(
    app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref)
  values('FIXTURE_WA40_APP_A','e2000000-0000-4000-8000-000000000002',
    'e3000000-0000-4000-8000-000000000005',
    'FIXTURE_WA40_WABA_FAKE','FIXTURE_WA40_PHONE_CROSS');
  raise exception 'FAIL WA40-03: cross-shop app binding accepted';
 exception when foreign_key_violation then null;
 end;
end $wa40$;
\echo 'PASS WA40-03: Meta App dealership ownership enforced'

-- WA40-04: two legitimate channels in the SAME App/dealership work in S0,
-- without authorizing a real provider, token or HTTP acknowledgement.
do $wa40$
declare batch jsonb; accepted jsonb; replay jsonb;
begin
 batch:=jsonb_build_array(
   jsonb_build_object('app_ref','FIXTURE_WA40_APP_A',
     'waba_id','FIXTURE_WA40_WABA_A','phone_number_id','FIXTURE_WA40_PHONE_A1',
     'event_kind','inbound_message','provider_message_id','wamid.WA40.A1',
     'provider_kind','text','provider_timestamp','2026-10-19T12:00:00Z',
     'payload_fixture',jsonb_build_object('fixture_ref','FIXTURE_WA40_EVENT1')),
   jsonb_build_object('app_ref','FIXTURE_WA40_APP_A',
     'waba_id','FIXTURE_WA40_WABA_A','phone_number_id','FIXTURE_WA40_PHONE_A2',
     'event_kind','status_callback','provider_message_id','wamid.WA40.OUT',
     'provider_kind','sent','provider_timestamp','2026-10-19T12:00:01Z',
     'payload_fixture',jsonb_build_object('fixture_ref','FIXTURE_WA40_EVENT2'))
 );
 accepted:=prumo_private.aceitar_lote_multicanal_fixture_s0(batch);
 replay:=prumo_private.aceitar_lote_multicanal_fixture_s0(batch);
 if accepted->>'outcome'<>'FIXTURE_BATCH_STORED'
 or (accepted->>'accepted')::int<>2 or (replay->>'duplicates')::int<>2
 or (select count(*) from prumo_private.inbox_eventos_s0
      where provider_message_id_s0 like 'wamid.WA40.%')<>2
 or (select count(*) from prumo_private.tarefas_ingresso_s0 t
     join prumo_private.inbox_eventos_s0 i on i.id=t.inbox_id
     where i.provider_message_id_s0 like 'wamid.WA40.%')<>2
 or (select count(distinct canal_id) from prumo_private.inbox_eventos_s0
     where provider_message_id_s0 like 'wamid.WA40.%')<>2
 then raise exception 'FAIL WA40-04: same-shop, two-sender ingress';end if;
end $wa40$;
\echo 'PASS WA40-04: two senders, same dealership, unique inbox+task+replay'

-- WA40-05: the fixture is private and still NEVER a provider ACK.
do $wa40$
begin
 if has_table_privilege('authenticated','prumo_private.meta_canais_fixture_s0','INSERT')
 or has_table_privilege('service_role','prumo_private.meta_canais_fixture_s0','SELECT')
 or has_function_privilege('prumo_s0_gateway',
     'prumo_private.aceitar_lote_multicanal_fixture_s0(jsonb)','EXECUTE')
 then raise exception 'FAIL WA40-05: private fixture exposed';end if;
end $wa40$;
\echo 'PASS WA40-05: no public or gateway access to synthetic Meta registry'
rollback;
