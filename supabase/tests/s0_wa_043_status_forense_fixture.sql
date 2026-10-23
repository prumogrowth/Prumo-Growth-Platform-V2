\set ON_ERROR_STOP on
-- WA39: physically query EXISTING S0 registry 040/041/042 and write only
-- to additive S0/043 forensic tables. ROLLBACK: no persisted test data.
begin;
insert into public.concessionarias(id,nome_operacional) values
 ('f6200000-0000-4000-8000-000000000001','WA39 shop A'),
 ('f6200000-0000-4000-8000-000000000002','WA39 shop B');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('f6300000-0000-4000-8000-000000000001','f6200000-0000-4000-8000-000000000001','WA39_A'),
 ('f6300000-0000-4000-8000-000000000002','f6200000-0000-4000-8000-000000000002','WA39_B');
insert into prumo_private.meta_apps_fixture_s0(
 app_ref,concessionaria_id,app_technical_ref) values
 ('FIXTURE_WA39_A','f6200000-0000-4000-8000-000000000001','12345000001'),
 ('FIXTURE_WA39_B','f6200000-0000-4000-8000-000000000002','12345000002');
insert into prumo_private.meta_canais_fixture_s0(
 app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref,
 waba_technical_ref,phone_technical_ref) values
 ('FIXTURE_WA39_A','f6200000-0000-4000-8000-000000000001',
  'f6300000-0000-4000-8000-000000000001','FIXTURE_WA39_WABA_A','FIXTURE_WA39_PHONE_A',
  '22345000001','32345000001'),
 ('FIXTURE_WA39_B','f6200000-0000-4000-8000-000000000002',
  'f6300000-0000-4000-8000-000000000002','FIXTURE_WA39_WABA_B','FIXTURE_WA39_PHONE_B',
  '22345000002','32345000002');
insert into prumo_private.outbox_intencoes_s0(
 id,concessionaria_id,canal_id,contrato,chave_idempotencia,
 versao_estado_sintetica) values
 ('f6400000-0000-4000-8000-000000000001',
  'f6200000-0000-4000-8000-000000000001',
  'f6300000-0000-4000-8000-000000000001','C03','WA39_A',1),
 ('f6400000-0000-4000-8000-000000000002',
  'f6200000-0000-4000-8000-000000000002',
  'f6300000-0000-4000-8000-000000000002','C03','WA39_B',1);
select prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
 '12345000001','22345000001','32345000001',
 'f6300000-0000-4000-8000-000000000001',
 'f6400000-0000-4000-8000-000000000001',
 'ATTEMPT_A','CORR_A','5581900000000','wamid.WA39.SHARED',200);
select prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
 '12345000002','22345000002','32345000002',
 'f6300000-0000-4000-8000-000000000002',
 'f6400000-0000-4000-8000-000000000002',
 'ATTEMPT_B','CORR_B','5581900000000','wamid.WA39.SHARED',200);
do $wa39_tests$
declare v jsonb; before_count integer; 
 a uuid:='f6300000-0000-4000-8000-000000000001';
 b uuid:='f6300000-0000-4000-8000-000000000002';
 i_a uuid:='f6400000-0000-4000-8000-000000000001';
 i_b uuid:='f6400000-0000-4000-8000-000000000002';
 h_a text:=repeat('a',64);h_b text:=repeat('b',64);
begin
 -- All calls use REAL S0 scope, not an independent WA33 shadow registry.
 v:=prumo_private.archivar_status_meta_tecnico_fixture_s0(
  '12345000001','22345000001','32345000001',a,i_a,'ATTEMPT_A','CORR_A',
  '5581900000000','wamid.WA39.SHARED','EVT_1','delivered',h_a);
 if v->>'outcome'<>'LAB_OBSERVED_UNVERIFIED' then
  raise exception 'WA39-01 unexpected initial %',v;end if;
 raise notice 'WA39-01 PASS';
 if (v->>'ack_allowed')::boolean or (v->>'send_authorized')::boolean
   or (v->>'delivery_confirmed')::boolean then raise exception 'WA39-02 unsafe';end if;
 raise notice 'WA39-02 PASS';
 v:=prumo_private.archivar_status_meta_tecnico_fixture_s0(
  '12345000001','22345000001','32345000001',a,i_a,'ATTEMPT_A','CORR_A',
  '5581900000000','wamid.WA39.SHARED','EVT_1','delivered',h_a);
 if v->>'outcome'<>'LAB_EXACT_BODY_REPLAY' then raise exception 'WA39-03 %',v;end if;
 raise notice 'WA39-03 PASS';
 v:=prumo_private.archivar_status_meta_tecnico_fixture_s0(
  '12345000001','22345000001','32345000001',a,i_a,'ATTEMPT_A','CORR_A',
  '5581900000000','wamid.WA39.SHARED','EVT_1','delivered',h_b);
 if v->>'outcome'<>'LAB_BODY_VARIANT_QUARANTINED' then
  raise exception 'WA39-04 %',v;end if;
 raise notice 'WA39-04 PASS';
 v:=prumo_private.archivar_status_meta_tecnico_fixture_s0(
  '12345000001','22345000001','32345000001',a,i_a,'ATTEMPT_A','CORR_A',
  '5581900000000','wamid.WA39.SHARED','EVT_1','failed',h_a);
 if v->>'outcome'<>'LAB_KIND_CONFLICT_QUARANTINED' then
  raise exception 'WA39-05 %',v;end if;
 raise notice 'WA39-05 PASS';
 if (select count(*) from prumo_private.meta_status_forense_fixture_s0
      where event_ref='EVT_1')<>2 or
    (select count(*) from prumo_private.meta_status_conflitos_fixture_s0
      where event_ref='EVT_1')<>1
 then raise exception 'WA39-06 forensic rows';end if;
 raise notice 'WA39-06 PASS';

 before_count:=(select count(*) from prumo_private.meta_status_forense_fixture_s0);
 v:=prumo_private.archivar_status_meta_tecnico_fixture_s0(
  '12345000002','22345000002','32345000002',b,i_b,'ATTEMPT_B','CORR_B',
  '5581900000000','wamid.WA39.SHARED','EVT_1','delivered',h_a);
 if v->>'outcome'<>'LAB_OBSERVED_UNVERIFIED' or
  (select count(*) from prumo_private.meta_status_forense_fixture_s0)
  <>before_count+1 then raise exception 'WA39-07 tenant isolation';end if;
 raise notice 'WA39-07 PASS';

 v:=prumo_private.archivar_status_meta_tecnico_fixture_s0(
  '12345000002','22345000002','32345000002',a,i_a,'ATTEMPT_A','CORR_A',
  '5581900000000','wamid.WA39.SHARED','EVT_INVALID','delivered',h_a);
 if v->>'outcome'<>'LAB_SCOPE_DENIED' then raise exception 'WA39-08 cross-tenant';end if;
 raise notice 'WA39-08 PASS';
 v:=prumo_private.archivar_status_meta_tecnico_fixture_s0(
  '12345000001','22345000001','32345000001',a,i_a,'ATTEMPT_A','CORR_A',
  '5581999999999','wamid.WA39.SHARED','EVT_INVALID','delivered',h_a);
 if v->>'outcome'<>'LAB_SCOPE_DENIED' then raise exception 'WA39-09 recipient';end if;
 raise notice 'WA39-09 PASS';
 v:=prumo_private.archivar_status_meta_tecnico_fixture_s0(
  '12345000001','22345000001','32345000001',a,i_a,'ATTEMPT_FORGED','CORR_A',
  '5581900000000','wamid.WA39.SHARED','EVT_INVALID','delivered',h_a);
 if v->>'outcome'<>'LAB_SCOPE_DENIED' then raise exception 'WA39-10 attempt';end if;
 raise notice 'WA39-10 PASS';
 if (select count(*) from prumo_private.meta_status_forense_fixture_s0)
   <>before_count+1 then raise exception 'WA39-11 denied write';end if;
 raise notice 'WA39-11 PASS';

 update prumo_private.outbox_intencoes_s0 set estado='CANCELADA' where id=i_a;
 v:=prumo_private.archivar_status_meta_tecnico_fixture_s0(
  '12345000001','22345000001','32345000001',a,i_a,'ATTEMPT_A','CORR_A',
  '5581900000000','wamid.WA39.SHARED','EVT_LATE','read',h_a);
 if v->>'outcome'<>'LAB_LATE_UNVERIFIED' then raise exception 'WA39-12 late %',v;end if;
 raise notice 'WA39-12 PASS';
 begin
  perform prumo_private.archivar_status_meta_tecnico_fixture_s0(
   '12345000001','22345000001','32345000001',a,i_a,'ATTEMPT_A','CORR_A',
   '5581900000000','wamid.WA39.SHARED','EVT_BAD','delivered','INVALID');
  raise exception 'WA39-13 invalid digest allowed';
 exception when invalid_parameter_value then
  if sqlerrm<>'INVALID_STATUS_FIXTURE' then raise;end if;
 end;
 raise notice 'WA39-13 PASS';
 begin
  perform prumo_private.archivar_status_meta_tecnico_fixture_s0(
   '12345000001','22345000001','32345000001',a,i_a,'ATTEMPT_A','CORR_A',
   '5581900000000','wamid.WA39.SHARED','EVT_BAD','GRAPH_SEND',h_a);
  raise exception 'WA39-14 kind allowed';
 exception when invalid_parameter_value then
  if sqlerrm<>'INVALID_STATUS_FIXTURE' then raise;end if;
 end;
 raise notice 'WA39-14 PASS';
 begin
  update prumo_private.meta_status_forense_fixture_s0
   set provider_status='sent' where event_ref='EVT_1';
  raise exception 'WA39-15 update allowed';
 exception when insufficient_privilege then
  if sqlerrm<>'IMMUTABLE_TECHNICAL_BINDING' then raise;end if;
 end;
 raise notice 'WA39-15 PASS';
 if has_table_privilege('anon','prumo_private.meta_status_forense_fixture_s0','SELECT')
  or has_table_privilege('authenticated','prumo_private.meta_status_forense_fixture_s0','INSERT')
  or has_table_privilege('service_role','prumo_private.meta_status_conflitos_fixture_s0','SELECT')
  or has_function_privilege('prumo_s0_gateway',
    'prumo_private.archivar_status_meta_tecnico_fixture_s0(text,text,text,uuid,uuid,text,text,text,text,text,text,text)',
    'EXECUTE')
 then raise exception 'WA39-16 inappropriate privilege';end if;
 raise notice 'WA39-16 PASS';
 if (select count(*) from prumo_private.meta_status_forense_fixture_s0
     where ack_allowed or send_authorized or retry_external
       or production_authorized or delivery_confirmed or
       case_transition_authorized or definitive_failure_count_increment)<>0
 then raise exception 'WA39-17 false authorizations';end if;
 raise notice 'WA39-17 PASS';
 if (select count(*) from prumo_private.inbox_eventos_s0
   where chave_evento like 'EVT_%')<>0 then
  raise exception 'WA39-18 touched S0 inbox';end if;
 raise notice 'WA39-18 PASS';
end $wa39_tests$;
rollback;
