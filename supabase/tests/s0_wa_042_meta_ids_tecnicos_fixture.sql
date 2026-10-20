\set ON_ERROR_STOP on
-- S0/042 WA15A technical Meta ID binding; LOCAL PG17 only. All ROLLBACK.
begin;
insert into public.concessionarias(id,nome_operacional) values
 ('f5200000-0000-4000-8000-000000000001','WA15 tenant A'),
 ('f5200000-0000-4000-8000-000000000002','WA15 tenant B');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('f5300000-0000-4000-8000-000000000001','f5200000-0000-4000-8000-000000000001','WA15_A1'),
 ('f5300000-0000-4000-8000-000000000002','f5200000-0000-4000-8000-000000000001','WA15_A2'),
 ('f5300000-0000-4000-8000-000000000003','f5200000-0000-4000-8000-000000000002','WA15_B');
insert into prumo_private.meta_apps_fixture_s0(app_ref,concessionaria_id,app_technical_ref) values
 ('FIXTURE_WA15_APP_A','f5200000-0000-4000-8000-000000000001','12345678901'),
 ('FIXTURE_WA15_APP_B','f5200000-0000-4000-8000-000000000002','22345678901');
insert into prumo_private.meta_canais_fixture_s0(
 app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref,
 waba_technical_ref,phone_technical_ref) values
 ('FIXTURE_WA15_APP_A','f5200000-0000-4000-8000-000000000001',
  'f5300000-0000-4000-8000-000000000001','FIXTURE_WA15_WABA_A','FIXTURE_WA15_PHONE_A1',
  '33345678901','55545678901'),
 ('FIXTURE_WA15_APP_A','f5200000-0000-4000-8000-000000000001',
  'f5300000-0000-4000-8000-000000000002','FIXTURE_WA15_WABA_A','FIXTURE_WA15_PHONE_A2',
  '33345678901','66645678901'),
 ('FIXTURE_WA15_APP_B','f5200000-0000-4000-8000-000000000002',
  'f5300000-0000-4000-8000-000000000003','FIXTURE_WA15_WABA_B','FIXTURE_WA15_PHONE_B',
  '44445678901','77745678901');
insert into prumo_private.outbox_intencoes_s0(
 id,concessionaria_id,canal_id,contrato,chave_idempotencia,versao_estado_sintetica) values
 ('f5400000-0000-4000-8000-000000000001','f5200000-0000-4000-8000-000000000001',
  'f5300000-0000-4000-8000-000000000001','C03','WA15_A1',1),
 ('f5400000-0000-4000-8000-000000000002','f5200000-0000-4000-8000-000000000001',
  'f5300000-0000-4000-8000-000000000002','C06','WA15_A2',1),
 ('f5400000-0000-4000-8000-000000000003','f5200000-0000-4000-8000-000000000002',
  'f5300000-0000-4000-8000-000000000003','C12','WA15_B',1),
 ('f5400000-0000-4000-8000-000000000004','f5200000-0000-4000-8000-000000000001',
  'f5300000-0000-4000-8000-000000000001','C03','WA15_A1_CANCEL',1);

do $wa15$
declare v jsonb; count_before integer; failed boolean;
begin
  -- WA15-01: the existing S0 registry resolves numeric App/WABA/phone into
  -- its true fixture aliases. No supplied dealership or WABA alias is stored.
  v:=prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
    '12345678901','33345678901','55545678901',
    'f5300000-0000-4000-8000-000000000001',
    'f5400000-0000-4000-8000-000000000001',
    'ATTEMPT_A','CORR_A','5581900000000','wamid.WA15.ONE',200);
  if v->>'outcome'<>'LAB_BOUND' or (v->>'ack_allowed')::boolean
    or (select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0
      where app_ref='FIXTURE_WA15_APP_A' and waba_ref='FIXTURE_WA15_WABA_A'
      and phone_number_ref='FIXTURE_WA15_PHONE_A1')<>1
  then raise exception 'FAIL WA15-01: untrusted mapping or ack';end if;
  raise notice 'PASS WA15-01: trusted S0 mapping persists numeric Meta scope';

  -- WA15-02: read-only exact match; no Graph retries even after commit loss.
  v:=prumo_private.consultar_vinculo_meta_tecnico_fixture_s0(
    '12345678901','33345678901','55545678901',
    'f5300000-0000-4000-8000-000000000001',
    'f5400000-0000-4000-8000-000000000001',
    'ATTEMPT_A','CORR_A','5581900000000','wamid.WA15.ONE');
  if v->>'outcome'<>'LAB_FOUND_EXACT'
     or (v->>'retry_external')::boolean or (v->>'production_authorized')::boolean
  then raise exception 'FAIL WA15-02: exact recovery';end if;
  raise notice 'PASS WA15-02: read-only exact scoped recovery';

  -- WA15-03: equal replay is one row, returns LAB_REPLAY.
  v:=prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
    '12345678901','33345678901','55545678901',
    'f5300000-0000-4000-8000-000000000001',
    'f5400000-0000-4000-8000-000000000001',
    'ATTEMPT_A','CORR_A','5581900000000','wamid.WA15.ONE',200);
  if v->>'outcome'<>'LAB_REPLAY' or
    (select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0
       where attempt_ref='ATTEMPT_A')<>1
  then raise exception 'FAIL WA15-03: replay';end if;
  raise notice 'PASS WA15-03: idempotent exact replay';

  -- WA15-04: same attempt cannot take another wamid, even through adapter.
  begin
    perform prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
      '12345678901','33345678901','55545678901',
      'f5300000-0000-4000-8000-000000000001',
      'f5400000-0000-4000-8000-000000000001',
      'ATTEMPT_A','CORR_A','5581900000000','wamid.WA15.OTHER',200);
    raise exception 'FAIL WA15-04: accepted distinct wamid';
  exception when unique_violation then
    if sqlerrm <> 'CONFLICT_TECHNICAL_BINDING' then raise;end if;
  end;
  raise notice 'PASS WA15-04: one attempt cannot map to two wamids';

  -- WA15-05: same scoped wamid cannot map to another attempt.
  begin
    perform prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
      '12345678901','33345678901','55545678901',
      'f5300000-0000-4000-8000-000000000001',
      'f5400000-0000-4000-8000-000000000001',
      'ATTEMPT_OTHER','CORR_OTHER','5581900000000','wamid.WA15.ONE',200);
    raise exception 'FAIL WA15-05: accepted distinct attempt';
  exception when unique_violation then
    if sqlerrm <> 'CONFLICT_TECHNICAL_BINDING' then raise;end if;
  end;
  raise notice 'PASS WA15-05: one wamid cannot map to two attempts';

  -- WA15-06: reject mixed technical tuple: App, WABA, sender or channel.
  count_before:=(select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0);
  for v in select value from jsonb_array_elements(
    jsonb_build_array(
     jsonb_build_array('22345678901','33345678901','55545678901','f5300000-0000-4000-8000-000000000001'),
     jsonb_build_array('12345678901','44445678901','55545678901','f5300000-0000-4000-8000-000000000001'),
     jsonb_build_array('12345678901','33345678901','77745678901','f5300000-0000-4000-8000-000000000001'),
     jsonb_build_array('12345678901','33345678901','55545678901','f5300000-0000-4000-8000-000000000002')
    )) as q(value) loop
    begin
      perform prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
       v->>0,v->>1,v->>2,(v->>3)::uuid,
       'f5400000-0000-4000-8000-000000000001',
       'ATTEMPT_FORGED','CORR_FORGED','5581900000000','wamid.WA15.FORGED',200);
      raise exception 'FAIL WA15-06: mixed technical Meta scope accepted';
    exception when insufficient_privilege then
      if sqlerrm<>'UNMAPPED_META_TECHNICAL_SCOPE' then raise;end if;
    end;
  end loop;
  if (select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0)<>count_before
  then raise exception 'FAIL WA15-06: bad scope created rows';end if;
  raise notice 'PASS WA15-06: mismatch App/WABA/phone/channel rejected';

  -- WA15-07: one WABA can serve two different senders of ONE App.
  v:=prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
    '12345678901','33345678901','66645678901',
    'f5300000-0000-4000-8000-000000000002',
    'f5400000-0000-4000-8000-000000000002',
    'ATTEMPT_A2','CORR_A2','5581900000000','wamid.WA15.ONE',200);
  if v->>'outcome'<>'LAB_BOUND' then raise exception 'FAIL WA15-07';end if;
  raise notice 'PASS WA15-07: same WABA, second sender isolated';

  -- WA15-08: same opaque wamid under another shop/App is independent.
  v:=prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
    '22345678901','44445678901','77745678901',
    'f5300000-0000-4000-8000-000000000003',
    'f5400000-0000-4000-8000-000000000003',
    'ATTEMPT_A','CORR_B','5581900000000','wamid.WA15.ONE',200);
  if v->>'outcome'<>'LAB_BOUND' then raise exception 'FAIL WA15-08';end if;
  raise notice 'PASS WA15-08: cross-tenant same opaque wamid isolated';

  -- WA15-09: right Meta IDs but wrong internal intent must fail.
  begin
    perform prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
      '12345678901','33345678901','55545678901',
      'f5300000-0000-4000-8000-000000000001',
      'f5400000-0000-4000-8000-000000000002',
      'ATTEMPT_FAKE','CORR_FAKE','5581900000000','wamid.WA15.FAKE',200);
    raise exception 'FAIL WA15-09: wrong channel intent accepted';
  exception when insufficient_privilege then
    if sqlerrm<>'UNTRUSTED_OR_INACTIVE_FIXTURE_SCOPE' then raise;end if;
  end;
  raise notice 'PASS WA15-09: wrong S0 intent denied';

  -- WA15-10: after writing, technical aliases must stay immutable.
  begin
    update prumo_private.meta_apps_fixture_s0
    set app_technical_ref='92345678901' where app_ref='FIXTURE_WA15_APP_A';
    raise exception 'FAIL WA15-10: remapped bound App';
  exception when insufficient_privilege then
    if sqlerrm<>'BOUND_META_ALIAS_IMMUTABLE' then raise;end if;
  end;
  begin
    update prumo_private.meta_canais_fixture_s0
    set phone_technical_ref='95545678901'
    where phone_number_ref='FIXTURE_WA15_PHONE_A1';
    raise exception 'FAIL WA15-10: remapped bound sender';
  exception when insufficient_privilege then
    if sqlerrm<>'BOUND_META_ALIAS_IMMUTABLE' then raise;end if;
  end;
  raise notice 'PASS WA15-10: bound aliases immutable';

  -- WA15-11: replay/read after cancellation is historical ONLY, not sending.
  update prumo_private.outbox_intencoes_s0 set estado='CANCELADA'
     where id='f5400000-0000-4000-8000-000000000001';
  v:=prumo_private.consultar_vinculo_meta_tecnico_fixture_s0(
    '12345678901','33345678901','55545678901',
    'f5300000-0000-4000-8000-000000000001',
    'f5400000-0000-4000-8000-000000000001',
    'ATTEMPT_A','CORR_A','5581900000000','wamid.WA15.ONE');
  if v->>'outcome'<>'LAB_FOUND_EXACT' or (v->>'retry_external')::boolean
  then raise exception 'FAIL WA15-11: cancelled historical recovery';end if;
  begin
    perform prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
      '12345678901','33345678901','55545678901',
      'f5300000-0000-4000-8000-000000000001',
      'f5400000-0000-4000-8000-000000000001',
      'ATTEMPT_NEW','CORR_NEW','5581900000000','wamid.WA15.NEW',200);
    raise exception 'FAIL WA15-11: cancelled new attempt accepted';
  exception when insufficient_privilege then
    if sqlerrm<>'UNTRUSTED_OR_INACTIVE_FIXTURE_SCOPE' then raise;end if;
  end;
  raise notice 'PASS WA15-11: historical read after cancellation; no new binding';

  -- WA15-12: absent valid intent is read-only, with no authority.
  count_before:=(select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0);
  v:=prumo_private.consultar_vinculo_meta_tecnico_fixture_s0(
    '12345678901','33345678901','55545678901',
    'f5300000-0000-4000-8000-000000000001',
    'f5400000-0000-4000-8000-000000000004',
    'ATTEMPT_ABSENT','CORR_ABSENT','5581900000000','wamid.WA15.ABSENT');
  if v->>'outcome'<>'LAB_ABSENT'
    or (v->>'ack_allowed')::boolean
    or (v->>'retry_external')::boolean
    or (v->>'production_authorized')::boolean
    or (select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0)<>count_before
  then raise exception 'FAIL WA15-12: absent recovery authorized retry';end if;
  raise notice 'PASS WA15-12: absent read does not authorize retry';

  -- WA15-13: identical numeric phone cannot be reused cross-App.
  begin
    update prumo_private.meta_canais_fixture_s0
    set phone_technical_ref='55545678901'
    where phone_number_ref='FIXTURE_WA15_PHONE_B';
    raise exception 'FAIL WA15-13: numeric sender reused';
  exception when unique_violation then null;end;
  raise notice 'PASS WA15-13: technical sender unique globally';

  -- WA15-14: WABA cannot be silently moved across two Apps.
  begin
    update prumo_private.meta_canais_fixture_s0
    set waba_technical_ref='33345678901'
    where phone_number_ref='FIXTURE_WA15_PHONE_B';
    raise exception 'FAIL WA15-14: WABA shared across Apps';
  exception when unique_violation then
    if sqlerrm<>'WABA_TECHNICAL_OWNER_CONFLICT' then raise;end if;
  end;
  raise notice 'PASS WA15-14: WABA owner constrained to single App';

  -- WA15-15: public/exposed roles cannot reach new functions.
  if has_function_privilege('anon',
       'prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(text,text,text,uuid,uuid,text,text,text,text,integer)','EXECUTE')
     or has_function_privilege('authenticated',
       'prumo_private.consultar_vinculo_meta_tecnico_fixture_s0(text,text,text,uuid,uuid,text,text,text,text)','EXECUTE')
     or has_function_privilege('service_role',
       'prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(text,text,text,uuid,uuid,text,text,text,text,integer)','EXECUTE')
  then raise exception 'FAIL WA15-15: exposed ACL';end if;
  raise notice 'PASS WA15-15: private-only technical adapter with no RPC grant';
end $wa15$;
rollback;
