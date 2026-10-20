\set ON_ERROR_STOP on
-- WA-14 / S0-041: PG17 LOCAL/DISPOSABLE ONLY; requires S0 migrations through 041.
-- Tests are rolled back; never use a hosted Supabase connection.
begin;
insert into public.concessionarias(id,nome_operacional) values
 ('f2100000-0000-4000-8000-000000000001','WA14 shop A synthetic'),
 ('f2100000-0000-4000-8000-000000000002','WA14 shop B synthetic');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('f3100000-0000-4000-8000-000000000001','f2100000-0000-4000-8000-000000000001','WA14_EMITTER_A1'),
 ('f3100000-0000-4000-8000-000000000002','f2100000-0000-4000-8000-000000000001','WA14_EMITTER_A2'),
 ('f3100000-0000-4000-8000-000000000003','f2100000-0000-4000-8000-000000000002','WA14_EMITTER_B');
insert into prumo_private.meta_apps_fixture_s0(app_ref,concessionaria_id) values
 ('FIXTURE_WA14_APP_A','f2100000-0000-4000-8000-000000000001'),
 ('FIXTURE_WA14_APP_B','f2100000-0000-4000-8000-000000000002');
insert into prumo_private.meta_canais_fixture_s0(
 app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref) values
 ('FIXTURE_WA14_APP_A','f2100000-0000-4000-8000-000000000001',
  'f3100000-0000-4000-8000-000000000001','FIXTURE_WA14_WABA_A','FIXTURE_WA14_PHONE_A1'),
 ('FIXTURE_WA14_APP_A','f2100000-0000-4000-8000-000000000001',
  'f3100000-0000-4000-8000-000000000002','FIXTURE_WA14_WABA_A','FIXTURE_WA14_PHONE_A2'),
 ('FIXTURE_WA14_APP_B','f2100000-0000-4000-8000-000000000002',
  'f3100000-0000-4000-8000-000000000003','FIXTURE_WA14_WABA_B','FIXTURE_WA14_PHONE_B');
insert into prumo_private.outbox_intencoes_s0(
 id,concessionaria_id,canal_id,contrato,chave_idempotencia,versao_estado_sintetica) values
 ('f4100000-0000-4000-8000-000000000001','f2100000-0000-4000-8000-000000000001',
  'f3100000-0000-4000-8000-000000000001','C03','WA14_INTENT_A',1),
 ('f4100000-0000-4000-8000-000000000002','f2100000-0000-4000-8000-000000000001',
  'f3100000-0000-4000-8000-000000000001','C12','WA14_INTENT_A_NEXT',2),
 ('f4100000-0000-4000-8000-000000000003','f2100000-0000-4000-8000-000000000001',
  'f3100000-0000-4000-8000-000000000002','C06','WA14_INTENT_A2',1),
 ('f4100000-0000-4000-8000-000000000004','f2100000-0000-4000-8000-000000000002',
  'f3100000-0000-4000-8000-000000000003','C03','WA14_INTENT_B',1);

do $wa14$
declare r jsonb; v_change record; q jsonb; baseline int;
begin
  -- WA14-01: authoritative S0 mapping + blocked intent + synthetic accepted HTTP.
  r:=prumo_private.registrar_vinculo_meta_fixture_s0(
    'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000001',
    'f4100000-0000-4000-8000-000000000001','ATTEMPT_A','CORR_A',
    '5581900000000','wamid.WA14.SAME',200);
  q:=prumo_private.consultar_vinculo_meta_fixture_s0(
    'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000001',
    'f4100000-0000-4000-8000-000000000001','ATTEMPT_A','CORR_A',
    '5581900000000','wamid.WA14.SAME');
  if r->>'outcome'<>'LAB_BOUND' or q->>'outcome'<>'LAB_FOUND_EXACT'
     or (r->>'ack_allowed')::boolean or (r->>'retry_external')::boolean
     or (q->>'production_authorized')::boolean then
    raise exception 'FAIL WA14-01: scoped write/recovery';end if;
  raise notice 'PASS WA14-01: exact scoped synthetic binding';

  -- WA14-02: identical replay preserves ONE record.
  r:=prumo_private.registrar_vinculo_meta_fixture_s0(
    'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000001',
    'f4100000-0000-4000-8000-000000000001','ATTEMPT_A','CORR_A',
    '5581900000000','wamid.WA14.SAME',200);
  if r->>'outcome'<>'LAB_REPLAY' or
     (select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0)<>1
    then raise exception 'FAIL WA14-02: replay created duplicate';end if;
  raise notice 'PASS WA14-02: exact idempotent replay';

  -- WA14-03: inverse attempt uniqueness.
  begin
    perform prumo_private.registrar_vinculo_meta_fixture_s0(
      'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000001',
      'f4100000-0000-4000-8000-000000000001','ATTEMPT_A','CORR_A',
      '5581900000000','wamid.WA14.SECOND',200);
    raise exception 'FAIL WA14-03: one attempt linked to two wamids';
  exception when unique_violation then null;end;
  raise notice 'PASS WA14-03: inverse attempt uniqueness';

  -- WA14-04: forward scoped wamid uniqueness.
  begin
    perform prumo_private.registrar_vinculo_meta_fixture_s0(
      'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000001',
      'f4100000-0000-4000-8000-000000000002','ATTEMPT_B','CORR_B',
      '5581900000000','wamid.WA14.SAME',200);
    raise exception 'FAIL WA14-04: one wamid re-owned by second attempt';
  exception when unique_violation then null;end;
  raise notice 'PASS WA14-04: forward scoped wamid uniqueness';

  -- WA14-05: same keys, changed correlation/recipient/status are NOT replay.
  for v_change in select value from pg_catalog.jsonb_array_elements(pg_catalog.jsonb_build_array(
    pg_catalog.jsonb_build_object('correlation','CORR_CHANGED','recipient','5581900000000','http',200),
    pg_catalog.jsonb_build_object('correlation','CORR_A','recipient','5581999999999','http',200),
    pg_catalog.jsonb_build_object('correlation','CORR_A','recipient','5581900000000','http',202))) as t(value)
  loop
    begin
      perform prumo_private.registrar_vinculo_meta_fixture_s0(
        'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000001',
        'f4100000-0000-4000-8000-000000000001','ATTEMPT_A',
        v_change.value->>'correlation',v_change.value->>'recipient','wamid.WA14.SAME',(v_change.value->>'http')::integer);
      raise exception 'FAIL WA14-05: altered binding accepted';
    exception when unique_violation then null;end;
  end loop;
  raise notice 'PASS WA14-05: exact tuple immutable';

  -- WA14-06: spoofed App on another concessionaria's channel denied.
  begin
    perform prumo_private.registrar_vinculo_meta_fixture_s0(
      'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000003',
      'f4100000-0000-4000-8000-000000000004','ATTEMPT_BAD','CORR_BAD',
      '5581900000000','wamid.WA14.BAD',200);
    raise exception 'FAIL WA14-06: spoofed App/channel accepted';
  exception when insufficient_privilege then null;end;
  raise notice 'PASS WA14-06: strict App/channel ownership';

  -- WA14-07: same wamid may belong to another tenant (different App/sender).
  r:=prumo_private.registrar_vinculo_meta_fixture_s0(
    'FIXTURE_WA14_APP_B','f3100000-0000-4000-8000-000000000003',
    'f4100000-0000-4000-8000-000000000004','ATTEMPT_A','CORR_B_SHOP',
    '5581900000000','wamid.WA14.SAME',200);
  if r->>'outcome'<>'LAB_BOUND' or
     (select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0)<>2
     then raise exception 'FAIL WA14-07: tenants not isolated';end if;
  raise notice 'PASS WA14-07: distinct Apps, same opaque wamid';

  -- WA14-08: same App, second sender has independent wamid namespace.
  r:=prumo_private.registrar_vinculo_meta_fixture_s0(
    'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000002',
    'f4100000-0000-4000-8000-000000000003','ATTEMPT_A2','CORR_A2',
    '5581900000000','wamid.WA14.SAME',200);
  if r->>'outcome'<>'LAB_BOUND' or
     (select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0)<>3
     then raise exception 'FAIL WA14-08: sender scope collided';end if;
  raise notice 'PASS WA14-08: same App, distinct sender allowed';

  -- WA14-09: absent read-only recovery is NEVER a resend authorization.
  baseline:=(select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0);
  q:=prumo_private.consultar_vinculo_meta_fixture_s0(
    'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000001',
    'f4100000-0000-4000-8000-000000000002','NEVER_SENT','NEVER_CORR',
    '5581900000000','wamid.WA14.ABSENT');
  if q->>'outcome'<>'LAB_ABSENT' or (q->>'retry_external')::boolean
   or (select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0)<>baseline
    then raise exception 'FAIL WA14-09: read altered bindings';end if;
  raise notice 'PASS WA14-09: non-mutating uncertain result recovery';

  -- WA14-10: contradictory recovery is not matched.
  q:=prumo_private.consultar_vinculo_meta_fixture_s0(
    'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000001',
    'f4100000-0000-4000-8000-000000000001','ATTEMPT_A','CORR_FORGED',
    '5581900000000','wamid.WA14.SAME');
  if q->>'outcome'<>'LAB_CONFLICT' then
    raise exception 'FAIL WA14-10: mismatched recovery';end if;
  raise notice 'PASS WA14-10: mismatch cannot masquerade as exact';

  -- WA14-11: invalid Graph evidence is rejected BEFORE table insertion.
  begin
    perform prumo_private.registrar_vinculo_meta_fixture_s0(
      'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000001',
      'f4100000-0000-4000-8000-000000000002','ATTEMPT_BAD','CORR_BAD',
      '5581900000000','not-a-wamid',200);
    raise exception 'FAIL WA14-11: non-wamid accepted';
  exception when invalid_parameter_value then null;end;
  begin
    perform prumo_private.registrar_vinculo_meta_fixture_s0(
      'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000001',
      'f4100000-0000-4000-8000-000000000002','ATTEMPT_BAD','CORR_BAD',
      '5581900000000','wamid.WA14.BAD',503);
    raise exception 'FAIL WA14-11: non-2xx accepted';
  exception when invalid_parameter_value then null;end;
  raise notice 'PASS WA14-11: malformed evidence fails closed';

  -- WA14-12: FK prevents directly injecting a forged WABA/phone tuple.
  begin
    insert into prumo_private.meta_vinculos_tentativa_fixture_s0(
      app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref,intencao_id,
      attempt_ref,correlation_ref,recipient_verified,provider_message_id,graph_http_status)
    values('FIXTURE_WA14_APP_A','f2100000-0000-4000-8000-000000000001',
      'f3100000-0000-4000-8000-000000000001','FIXTURE_WA14_WABA_FAKE',
      'FIXTURE_WA14_PHONE_A1','f4100000-0000-4000-8000-000000000002',
      'DIRECT_BAD','DIRECT_CORR','5581900000000','wamid.DIRECT_BAD',200);
    raise exception 'FAIL WA14-12: forged sender inserted';
  exception when foreign_key_violation then null;end;
  raise notice 'PASS WA14-12: composite FK protects authenticated sender fixture';

  -- WA14-13: cancelled outbox intent cannot accept a NEW observation.
  update prumo_private.outbox_intencoes_s0 set estado='CANCELADA'
    where id='f4100000-0000-4000-8000-000000000002';
  begin
    perform prumo_private.registrar_vinculo_meta_fixture_s0(
      'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000001',
      'f4100000-0000-4000-8000-000000000002','ATTEMPT_C','CORR_C',
      '5581900000000','wamid.WA14.C',200);
    raise exception 'FAIL WA14-13: cancelled intent accepted';
  exception when insufficient_privilege then null;end;
  raise notice 'PASS WA14-13: outbox cancellation gate';

  -- WA14-14: exception rollback is all-or-none within a transaction sub-block.
  baseline:=(select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0);
  begin
    perform prumo_private.registrar_vinculo_meta_fixture_s0(
      'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000002',
      'f4100000-0000-4000-8000-000000000003','ATTEMPT_ATOMIC','CORR_ATOMIC',
      '5581900000000','wamid.WA14.ATOMIC',200);
    perform prumo_private.registrar_vinculo_meta_fixture_s0(
      'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000002',
      'f4100000-0000-4000-8000-000000000003','ATTEMPT_ATOMIC','CORR_ATOMIC',
      '5581900000000','UNSAFE',200);
    raise exception 'FAIL WA14-14: expected invalid second item';
  exception when invalid_parameter_value then null;end;
  if (select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0)<>baseline
    then raise exception 'FAIL WA14-14: partial transaction observed';end if;
  raise notice 'PASS WA14-14: statement failure rolls back synthetic multi-write';
end $wa14$;

do $wa14$
begin
  -- WA14-15: PostgreSQL ACL/RLS and fixture no-ACK guardrails.
  if not (select relrowsecurity from pg_catalog.pg_class
      where oid='prumo_private.meta_vinculos_tentativa_fixture_s0'::regclass)
   or has_table_privilege('anon','prumo_private.meta_vinculos_tentativa_fixture_s0','SELECT')
   or has_table_privilege('authenticated','prumo_private.meta_vinculos_tentativa_fixture_s0','INSERT')
   or has_table_privilege('service_role','prumo_private.meta_vinculos_tentativa_fixture_s0','SELECT')
   or has_function_privilege('authenticated',
     'prumo_private.registrar_vinculo_meta_fixture_s0(text,uuid,uuid,text,text,text,text,integer)','EXECUTE')
   or has_function_privilege('service_role',
     'prumo_private.consultar_vinculo_meta_fixture_s0(text,uuid,uuid,text,text,text,text)','EXECUTE')
  then raise exception 'FAIL WA14-15: privacy / RLS / ACL';end if;
  raise notice 'PASS WA14-15: private-only S0 fixture with no public entrypoint';
end $wa14$;

-- WA14-16: PostgreSQL-safe wamid length gate at exact 1024-character edge.
-- This catches the old invalid regex {1,1024} (PG bound max is 255).
do $wa14_limit$
declare v_exact text; v_too_long text; result jsonb;
begin
  v_exact:='wamid.'||repeat('A',1024);
  v_too_long:='wamid.'||repeat('A',1025);
  result:=prumo_private.registrar_vinculo_meta_fixture_s0(
    'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000002',
    'f4100000-0000-4000-8000-000000000003','ATTEMPT_MAX','CORR_MAX',
    '5581900000000',v_exact,200);
  if result->>'outcome'<>'LAB_BOUND'
    or (prumo_private.consultar_vinculo_meta_fixture_s0(
      'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000002',
      'f4100000-0000-4000-8000-000000000003','ATTEMPT_MAX','CORR_MAX',
      '5581900000000',v_exact))->>'outcome'<>'LAB_FOUND_EXACT'
  then raise exception 'FAIL WA14-16: 1024-digit base wamid edge';end if;
  begin
    perform prumo_private.registrar_vinculo_meta_fixture_s0(
      'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000002',
      'f4100000-0000-4000-8000-000000000003','ATTEMPT_TOO_LONG','CORR_TOO_LONG',
      '5581900000000',v_too_long,200);
    raise exception 'FAIL WA14-16: 1025 payload accepted';
  exception when invalid_parameter_value then null;end;
  begin
    perform prumo_private.consultar_vinculo_meta_fixture_s0(
      'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000002',
      'f4100000-0000-4000-8000-000000000003','ATTEMPT_TOO_LONG','CORR_TOO_LONG',
      '5581900000000','wamid.');
    raise exception 'FAIL WA14-16: empty payload accepted';
  exception when invalid_parameter_value then null;end;
  if (select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0
      where attempt_ref in ('ATTEMPT_MAX','ATTEMPT_TOO_LONG'))<>1
  then raise exception 'FAIL WA14-16: length validation changed row counts';end if;
  raise notice 'PASS WA14-16: 1024 accepted, 1025 and empty rejected';
end $wa14_limit$;


-- WA14-17: accepted bindings are append-only: UPDATE, DELETE, TRUNCATE
-- cannot bypass bidirectional uniqueness by direct privileged SQL mutation.
do $wa14_immutable_test$
declare previous integer; recovered jsonb;
begin
  select count(*) into previous
    from prumo_private.meta_vinculos_tentativa_fixture_s0;
  begin
    update prumo_private.meta_vinculos_tentativa_fixture_s0
    set provider_message_id='wamid.WA14.FORGED_REWRITE'
    where app_ref='FIXTURE_WA14_APP_A' and attempt_ref='ATTEMPT_A';
    raise exception 'FAIL WA14-17: direct UPDATE bypassed immutability';
  exception when insufficient_privilege then
    if sqlerrm <> 'IMMUTABLE_TECHNICAL_BINDING' then raise; end if;
  end;
  begin
    delete from prumo_private.meta_vinculos_tentativa_fixture_s0
    where app_ref='FIXTURE_WA14_APP_A' and attempt_ref='ATTEMPT_A';
    raise exception 'FAIL WA14-17: direct DELETE bypassed immutability';
  exception when insufficient_privilege then
    if sqlerrm <> 'IMMUTABLE_TECHNICAL_BINDING' then raise; end if;
  end;
  begin
    truncate table prumo_private.meta_vinculos_tentativa_fixture_s0;
    raise exception 'FAIL WA14-17: direct TRUNCATE bypassed immutability';
  exception when insufficient_privilege then
    if sqlerrm <> 'IMMUTABLE_TECHNICAL_BINDING' then raise; end if;
  end;
  if (select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0)<>previous
  then raise exception 'FAIL WA14-17: a forbidden mutation changed the ledger';end if;
  recovered:=prumo_private.consultar_vinculo_meta_fixture_s0(
    'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000001',
    'f4100000-0000-4000-8000-000000000001','ATTEMPT_A','CORR_A',
    '5581900000000','wamid.WA14.SAME');
  if recovered->>'outcome'<>'LAB_FOUND_EXACT'
  then raise exception 'FAIL WA14-17: original binding was not retained';end if;
  raise notice 'PASS WA14-17: UPDATE/DELETE/TRUNCATE denied; original binding intact';
end $wa14_immutable_test$;


-- WA14-18: recovery MUST verify that requested intent belongs to the
-- same App/dealership/channel. A forged or absent intent is not LAB_ABSENT.
do $wa14_recovery_scope$
declare v_bad uuid; initial_count bigint; r jsonb;
begin
  select count(*) into initial_count
    from prumo_private.meta_vinculos_tentativa_fixture_s0;
  foreach v_bad in array ARRAY[
    'f4100000-0000-4000-8000-000000000003'::uuid, -- same shop, other channel
    'f4100000-0000-4000-8000-000000000004'::uuid, -- different shop/App
    'f4100000-0000-4000-8000-000000000099'::uuid  -- nonexisting intent
  ] loop
    begin
      perform prumo_private.consultar_vinculo_meta_fixture_s0(
        'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000001',
        v_bad,'ATTEMPT_MISSING','CORR_MISSING',
        '5581900000000','wamid.WA14.MISSING');
      raise exception 'FAIL WA14-18: mismatched outbox intent yielded a normal recovery';
    exception when insufficient_privilege then
      if sqlerrm <> 'UNTRUSTED_FIXTURE_SCOPE' then raise;end if;
    end;
  end loop;

  -- Genuine current-shop/current-channel intent with NO binding remains
  -- a read-only LAB_ABSENT; never permission to resend Graph.
  r:=prumo_private.consultar_vinculo_meta_fixture_s0(
    'FIXTURE_WA14_APP_A','f3100000-0000-4000-8000-000000000001',
    'f4100000-0000-4000-8000-000000000002',
    'ATTEMPT_MISSING','CORR_MISSING',
    '5581900000000','wamid.WA14.MISSING');
  if r->>'outcome' <> 'LAB_ABSENT'
    or (r->>'retry_external')::boolean
    or (select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0) <> initial_count
  then raise exception 'FAIL WA14-18: recovery changed ledger or authorized retry';end if;
  raise notice 'PASS WA14-18: recovery verifies intent owner, never treats spoof as ABSENT';
end $wa14_recovery_scope$;

rollback;
