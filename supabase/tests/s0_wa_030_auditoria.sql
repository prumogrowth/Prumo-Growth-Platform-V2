\set ON_ERROR_STOP on
begin;
insert into public.concessionarias(id,nome_operacional) values
 ('d2000000-0000-4000-8000-000000000001','WA30 loja A ficticia'),
 ('d2000000-0000-4000-8000-000000000002','WA30 loja B ficticia');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('d3000000-0000-4000-8000-000000000001','d2000000-0000-4000-8000-000000000001','WA30_CANAL_A'),
 ('d3000000-0000-4000-8000-000000000002','d2000000-0000-4000-8000-000000000002','WA30_CANAL_B');

-- A-01: pending replay must preserve evidence and fail if body/number changes.
do $x$
declare a jsonb;b jsonb;
begin
 a:=prumo_private.receber_mensagem_identidade_s0(
 'd3000000-0000-4000-8000-000000000001','+558122223333','FIXED.A','FIXTURE_ONLY',false);
 b:=prumo_private.receber_mensagem_identidade_s0(
 'd3000000-0000-4000-8000-000000000001','+5581922223333','PENDING.A','FIXTURE_CONFLICT',true);
 if a->>'outcome'<>'APPLIED' or b->>'outcome'<>'NEEDS_REVIEW'
 then raise exception 'FAIL WA30-ID-01: missing pending';end if;
 b:=prumo_private.receber_mensagem_identidade_s0(
 'd3000000-0000-4000-8000-000000000001','+5581922223333','PENDING.A','FIXTURE_CONFLICT',true);
 if b->>'replay'<>'ALREADY_PENDING' then
 raise exception 'FAIL WA30-ID-01: pending replay';end if;
 begin
  perform prumo_private.receber_mensagem_identidade_s0(
  'd3000000-0000-4000-8000-000000000001',
  '+5581922223333','PENDING.A','ALTERED_FIXTURE',true);
  raise exception 'FAIL WA30-ID-01: content mismatch accepted';
 exception when unique_violation then null;end;
 begin
  perform prumo_private.receber_mensagem_identidade_s0(
  'd3000000-0000-4000-8000-000000000001',
  '+5581922223334','PENDING.A','FIXTURE_CONFLICT',true);
  raise exception 'FAIL WA30-ID-01: sender mismatch accepted';
 exception when unique_violation then null;end;
 if (select count(*) from prumo_private.pendencias_identidade_s0
   where concessionaria_id='d2000000-0000-4000-8000-000000000001')<>1
 or (select texto_sintetico from prumo_private.pendencias_identidade_s0
     where id_externo='PENDING.A')<>'FIXTURE_CONFLICT'
 then raise exception 'FAIL WA30-ID-01: pending data mutated';end if;
end $x$;
\echo 'PASS WA30-ID-01: replay pendente identico e aceito; conflitos rejeitados sem sobrescrita'

-- A-05: event cannot claim alias for a different lead within the same shop.
do $x$
declare v_alias uuid;v_other uuid;
begin
 select a.id into v_alias from prumo_private.aliases_identidade_s0 a
 where a.concessionaria_id='d2000000-0000-4000-8000-000000000001'
 and a.numero_sintetico='+558122223333';
 insert into public.leads_loja(concessionaria_id,telefone_cliente_normalizado)
 values('d2000000-0000-4000-8000-000000000001','+558133334444')
 returning id into v_other;
 begin
 insert into prumo_private.eventos_identidade_s0(concessionaria_id,lead_id,alias_id,decisao)
 values('d2000000-0000-4000-8000-000000000001',
 v_other,v_alias,'MATCH_EXACT');
 raise exception 'FAIL WA30-ID-02: identity event crossed leads';
 exception when foreign_key_violation then null;end;
 begin
 insert into prumo_private.aliases_identidade_s0(
 concessionaria_id,lead_id,numero_sintetico,origem,
 mobile_confirmado_sintetico,chave_variante_sintetica)
 values('d2000000-0000-4000-8000-000000000001',
 v_other,'+558155556666','CANAL_SINTETICO',true,null);
 raise exception 'FAIL WA30-ID-02: inconsistent evidence accepted';
 exception when check_violation then null;end;
end $x$;
\echo 'PASS WA30-ID-02: FK composta protege alias/lead e prova de variante consistente'

insert into prumo_private.meta_apps_fixture_s0(app_ref,concessionaria_id) values
 ('FIXTURE_APP_A','d2000000-0000-4000-8000-000000000001'),
 ('FIXTURE_APP_B','d2000000-0000-4000-8000-000000000002');
insert into prumo_private.meta_canais_fixture_s0(
 app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref) values
 ('FIXTURE_APP_A','d2000000-0000-4000-8000-000000000001',
  'd3000000-0000-4000-8000-000000000001','FIXTURE_WABA_A','FIXTURE_PHONE_A'),
 ('FIXTURE_APP_B','d2000000-0000-4000-8000-000000000002',
  'd3000000-0000-4000-8000-000000000002','FIXTURE_WABA_B','FIXTURE_PHONE_B');

-- A-02/03: one transaction for mixed-channel batch with actual fixture payload.
do $x$
declare a jsonb;b jsonb;v_items jsonb;
begin
 v_items:=jsonb_build_array(
 jsonb_build_object('app_ref','FIXTURE_APP_A','waba_id','FIXTURE_WABA_A','phone_number_id','FIXTURE_PHONE_A',
   'event_kind','inbound_message','provider_message_id','wamid.A1',
   'provider_kind','text','provider_timestamp','2026-10-18T00:00:00Z',
   'payload_fixture',jsonb_build_object('fixture_ref','FIXTURE_EVENT_A1')),
 jsonb_build_object('app_ref','FIXTURE_APP_B','waba_id','FIXTURE_WABA_B','phone_number_id','FIXTURE_PHONE_B',
   'event_kind','inbound_message','provider_message_id','wamid.B1',
   'provider_kind','text','provider_timestamp','2026-10-18T00:00:01Z',
   'payload_fixture',jsonb_build_object('fixture_ref','FIXTURE_EVENT_B1')),
 jsonb_build_object('app_ref','FIXTURE_APP_A','waba_id','FIXTURE_WABA_A','phone_number_id','FIXTURE_PHONE_A',
   'event_kind','status_callback','provider_message_id','wamid.SAME',
   'provider_kind','sent','provider_timestamp','2026-10-18T00:00:02Z',
   'payload_fixture',jsonb_build_object('fixture_ref','FIXTURE_STATUS_A1')),
 jsonb_build_object('app_ref','FIXTURE_APP_A','waba_id','FIXTURE_WABA_A','phone_number_id','FIXTURE_PHONE_A',
   'event_kind','status_callback','provider_message_id','wamid.SAME',
   'provider_kind','delivered','provider_timestamp','2026-10-18T00:00:03Z',
   'payload_fixture',jsonb_build_object('fixture_ref','FIXTURE_STATUS_A2')));
 a:=prumo_private.aceitar_lote_multicanal_fixture_s0(v_items);
 b:=prumo_private.aceitar_lote_multicanal_fixture_s0(v_items);
 if a->>'outcome'<>'FIXTURE_BATCH_STORED' or (a->>'accepted')::integer<>4
 or (b->>'duplicates')::integer<>4
 or (select count(*) from prumo_private.inbox_eventos_s0)<>4
 or (select count(*) from prumo_private.tarefas_ingresso_s0)<>4
 or (select count(*) from prumo_private.inbox_eventos_s0
    where payload_fixture_s0 is not null and app_fixture_ref like 'FIXTURE_%')<>4
 or (select count(distinct concessionaria_id) from prumo_private.inbox_eventos_s0)<>2
 or (select count(*) from prumo_private.inbox_eventos_s0
    where provider_message_id_s0='wamid.SAME')<>2
 then raise exception 'FAIL WA30-IN-01: multi-channel/durable fixture';end if;
 -- Same provider message ID / key with divergent fixture content is rejected.
 begin
 perform prumo_private.aceitar_lote_multicanal_fixture_s0(
 jsonb_build_array(v_items->0 || jsonb_build_object(
 'payload_fixture',jsonb_build_object('fixture_ref','FIXTURE_CHANGED'))));
 raise exception 'FAIL WA30-IN-01: mutated replay accepted';
 exception when unique_violation then null;end;
end $x$;
\echo 'PASS WA30-IN-01: 2 lojas em 1 transacao, 2 statuses distintos e replay de payload'

do $x$
declare v_first jsonb;v_bad jsonb;
begin
 v_first:=jsonb_build_object('app_ref','FIXTURE_APP_A','waba_id','FIXTURE_WABA_A',
  'phone_number_id','FIXTURE_PHONE_A','event_kind','inbound_message',
  'provider_message_id','wamid.ROLLBACK','provider_kind','text',
  'provider_timestamp','2026-10-18T01:00:00Z',
  'payload_fixture',jsonb_build_object('fixture_ref','FIXTURE_ROLLBACK'));
 v_bad:=v_first || jsonb_build_object('app_ref','FIXTURE_APP_B');
 begin
  perform prumo_private.aceitar_lote_multicanal_fixture_s0(
    jsonb_build_array(v_first,v_bad));
  raise exception 'FAIL WA30-IN-02: wrong app/waba accepted';
 exception when insufficient_privilege then null;end;
 if exists(select 1 from prumo_private.inbox_eventos_s0
 where provider_message_id_s0='wamid.ROLLBACK')
 then raise exception 'FAIL WA30-IN-02: partial commit';end if;
 begin
  perform prumo_private.aceitar_lote_multicanal_fixture_s0(jsonb_build_array(
    v_first || jsonb_build_object('concessionaria_id','d2000000-0000-4000-8000-000000000002')));
  raise exception 'FAIL WA30-IN-02: untrusted shop accepted';
 exception when invalid_parameter_value then null;end;
end $x$;
\echo 'PASS WA30-IN-02: spoof de loja/app negado e rollback integral'

do $sec$
begin
 if has_function_privilege('authenticated',
    'prumo_private.aceitar_lote_multicanal_fixture_s0(jsonb)','EXECUTE')
 or has_function_privilege('service_role',
    'prumo_private.aceitar_lote_multicanal_fixture_s0(jsonb)','EXECUTE')
 or has_table_privilege('anon',
    'prumo_private.meta_apps_fixture_s0','SELECT')
 or has_table_privilege('prumo_s0_gateway',
    'prumo_private.meta_canais_fixture_s0','INSERT')
 then raise exception 'FAIL WA30-SEC-01: fixture exposed';end if;
end $sec$;
\echo 'PASS WA30-SEC-01: registro Meta sintetico e batch inacessiveis a papeis publicos'
rollback;
