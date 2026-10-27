\set ON_ERROR_STOP on
-- S0-034B contract audit only. No ingress-to-C07 bridge and no Meta real IDs.
-- Every evento_externo_ficticio below is an INDEPENDENT LOCAL TEST token;
-- NEVER copy statuses[].id there (it identifies the message, not the event).
begin;
insert into auth.users(id) values ('b4710000-0000-4000-8000-000000000001');
insert into public.atores(id) values ('b4710000-0000-4000-8000-000000000001');
insert into public.concessionarias(id,nome_operacional) values
 ('b4720000-0000-4000-8000-000000000001','WA34B A fixture'),
 ('b4720000-0000-4000-8000-000000000002','WA34B B fixture');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('b4710000-0000-4000-8000-000000000001',
 'b4720000-0000-4000-8000-000000000001','gestor');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('b4730000-0000-4000-8000-000000000001',
  'b4720000-0000-4000-8000-000000000001','WA34B_EMISSOR_A1'),
 ('b4730000-0000-4000-8000-000000000002',
  'b4720000-0000-4000-8000-000000000001','WA34B_EMISSOR_A2'),
 ('b4730000-0000-4000-8000-000000000003',
  'b4720000-0000-4000-8000-000000000002','WA34B_EMISSOR_B');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('b4740000-0000-4000-8000-000000000001',
 'b4720000-0000-4000-8000-000000000001','+5581900003499');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id)
 values('b4750000-0000-4000-8000-000000000001',
 'b4720000-0000-4000-8000-000000000001',
 'b4740000-0000-4000-8000-000000000001');
insert into public.catalogo_templates_sinteticos(
 id,concessionaria_id,codigo,versao,aprovado_simulacao) values
 ('b4760000-0000-4000-8000-000000000001',
 'b4720000-0000-4000-8000-000000000001','WA34B',1,true);
insert into public.evidencias_elegibilidade_sinteticas(
 concessionaria_id,lead_id,canal_id,finalidade,referencia_ficticia) values
 ('b4720000-0000-4000-8000-000000000001',
 'b4740000-0000-4000-8000-000000000001',
 'b4730000-0000-4000-8000-000000000001',
 'recontato_comercial_sintetico','WA34B_FAKE_ONLY');

do $t$
declare v jsonb;v_envio uuid;
begin
 v:=prumo_private.agendar_recontatos_sinteticos(
 'b4710000-0000-4000-8000-000000000001',
 'b4720000-0000-4000-8000-000000000001',
 'b4750000-0000-4000-8000-000000000001',
 'b4730000-0000-4000-8000-000000000001',
 'WA34B_PLAN',
 jsonb_build_array(jsonb_build_object(
  'template_id','b4760000-0000-4000-8000-000000000001',
  'agendado_em',(statement_timestamp()+interval '1 day')::text)));
 if v->>'outcome'<>'APPLIED' then raise exception 'FAIL WA34B fixture plan';end if;
 select id into v_envio from public.envios_template_sinteticos
 where concessionaria_id='b4720000-0000-4000-8000-000000000001';
 v:=prumo_private.reservar_envio_sintetico(
 'b4720000-0000-4000-8000-000000000001',v_envio,
 statement_timestamp()+interval '2 days');
 if v->>'outcome'<>'RESERVED_SIMULATED' then
  raise exception 'FAIL WA34B fixture reservation';end if;
 v:=prumo_private.vincular_referencia_c07_sintetica(
 'b4720000-0000-4000-8000-000000000001',v_envio,
 'b4730000-0000-4000-8000-000000000001','wamid.WA34B.OUT1');
 if v->>'outcome'<>'APPLIED' then raise exception 'FAIL WA34B provider fixture ref';end if;
end $t$;

-- One statuses[].id (message ID) can carry several logical observations.
-- Only local synthetic occurrence IDs are passed into legacy C07 p_evento.
do $t$
declare a jsonb;b jsonb;c jsonb;d jsonb;r jsonb;
 v_t timestamptz:='2026-10-18T12:00:00Z'::timestamptz;
begin
 a:=prumo_private.registrar_callback_c07_sintetico(
  'b4730000-0000-4000-8000-000000000001',
  'wamid.WA34B.OUT1','WA34B-LOCAL-001','ENVIADO_SIMULADO',v_t);
 b:=prumo_private.registrar_callback_c07_sintetico(
  'b4730000-0000-4000-8000-000000000001',
  'wamid.WA34B.OUT1','WA34B-LOCAL-002','ENTREGUE_SIMULADO',
  v_t+interval '1 minute');
 -- Same message ID + status + timestamp, but two distinct local *events*.
 c:=prumo_private.registrar_callback_c07_sintetico(
  'b4730000-0000-4000-8000-000000000001',
  'wamid.WA34B.OUT1','WA34B-LOCAL-003','ENTREGUE_SIMULADO',
  v_t+interval '1 minute');
 d:=prumo_private.registrar_callback_c07_sintetico(
  'b4730000-0000-4000-8000-000000000001',
  'wamid.WA34B.OUT1','WA34B-LOCAL-004','LIDO_SIMULADO',
  v_t-interval '1 minute');
 r:=prumo_private.registrar_callback_c07_sintetico(
  'b4730000-0000-4000-8000-000000000001',
  'wamid.WA34B.OUT1','WA34B-LOCAL-002','ENTREGUE_SIMULADO',
  v_t+interval '1 minute');
 if a->>'outcome'<>'APPLIED' or b->>'outcome'<>'APPLIED'
 or c->>'outcome'<>'APPLIED' or d->>'outcome'<>'APPLIED'
 or (d->>'fora_de_ordem')::boolean is distinct from true
 or r->>'outcome'<>'ALREADY_APPLIED'
 or (select count(*) from public.eventos_callback_sinteticos
   where concessionaria_id='b4720000-0000-4000-8000-000000000001'
   and correlacao_externa_ficticia='wamid.WA34B.OUT1')<>4
 or not exists(select 1 from public.envios_template_sinteticos
   where correlacao_externa_ficticia='wamid.WA34B.OUT1'
   and callback_enviado_simulado and callback_entregue_simulado
   and callback_lido_simulado and estado='reservado')
 or (select status_comercial from public.ciclos_comerciais
   where id='b4750000-0000-4000-8000-000000000001')
   <>'aguardando primeiro disparo'
 then raise exception 'FAIL WA34B-CB-01 observation preservation';end if;
end $t$;
\echo 'PASS WA34B-CB-01: um message ID comporta varias observacoes, repeticoes e evento atrasado'

-- Reusing statuses[].id itself as an event ID would NOT be safe:
-- the legacy synthetic API throws conflict for the second status.
do $t$
declare a jsonb;v_t timestamptz:='2026-10-18T13:00:00Z'::timestamptz;
begin
 a:=prumo_private.registrar_callback_c07_sintetico(
  'b4730000-0000-4000-8000-000000000001',
  'wamid.WA34B.OUT1','wamid.BAD_AS_EVENT_ID','ACEITO_SIMULADO',v_t);
 if a->>'outcome'<>'APPLIED' then raise exception 'FAIL WA34B-CB-02 first observation';end if;
 begin
  perform prumo_private.registrar_callback_c07_sintetico(
   'b4730000-0000-4000-8000-000000000001',
   'wamid.WA34B.OUT1','wamid.BAD_AS_EVENT_ID','ENVIADO_SIMULADO',
   v_t+interval '1 minute');
  raise exception 'FAIL WA34B-CB-02 invalid reuse was accepted';
 exception when unique_violation then null;end;
 if (select count(*) from public.eventos_callback_sinteticos
   where evento_externo_ficticio='wamid.BAD_AS_EVENT_ID')<>1
 then raise exception 'FAIL WA34B-CB-02 conflict not preserved';end if;
end $t$;
\echo 'PASS WA34B-CB-02: p_evento nao pode receber statuses[].id como ID unico de callback'

-- A callback on another channel in the SAME shop or same provider ID on
-- another shop must not borrow A1's matched outbound attempt.
do $t$
declare a jsonb;b jsonb;
begin
 a:=prumo_private.registrar_callback_c07_sintetico(
  'b4730000-0000-4000-8000-000000000002',
  'wamid.WA34B.OUT1','WA34B-A2-UNKNOWN','ENTREGUE_SIMULADO',
  '2026-10-18T14:00:00Z'::timestamptz);
 b:=prumo_private.registrar_callback_c07_sintetico(
  'b4730000-0000-4000-8000-000000000003',
  'wamid.WA34B.OUT1','WA34B-B-UNKNOWN','ENTREGUE_SIMULADO',
  '2026-10-18T14:00:00Z'::timestamptz);
 if a->>'outcome'<>'PENDING_RECONCILIATION'
 or b->>'outcome'<>'PENDING_RECONCILIATION'
 or (select count(*) from public.pendencias_reconciliacao_c07_sinteticas p
   join public.eventos_callback_sinteticos c
   on c.concessionaria_id=p.concessionaria_id and c.id=p.evento_id
   where c.evento_externo_ficticio in ('WA34B-A2-UNKNOWN','WA34B-B-UNKNOWN')
   and p.categoria='SEM_CORRELACAO')<>2
 then raise exception 'FAIL WA34B-CB-03 cross scope';end if;
end $t$;
\echo 'PASS WA34B-CB-03: desconhecido fica pendente sem vazamento entre canal ou loja'

-- A deliberate negative characterization test of the S0/030 fixture ingress.
-- Same status + provider timestamp => same unique key; differing fixture
-- payloads cause a conflict. This is a BLOCKER, not a Meta dedupe proof.
do $t$
declare v jsonb;v_first jsonb;v_second jsonb;
begin
 insert into prumo_private.meta_apps_fixture_s0(app_ref,concessionaria_id)
 values('FIXTURE_WA34B_APP','b4720000-0000-4000-8000-000000000001');
 insert into prumo_private.meta_canais_fixture_s0(
 app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref)
 values('FIXTURE_WA34B_APP','b4720000-0000-4000-8000-000000000001',
 'b4730000-0000-4000-8000-000000000001',
 'FIXTURE_WA34B_WABA','FIXTURE_WA34B_PHONE');
 v_first:=jsonb_build_object('app_ref','FIXTURE_WA34B_APP',
  'waba_id','FIXTURE_WA34B_WABA','phone_number_id','FIXTURE_WA34B_PHONE',
  'event_kind','status_callback','provider_message_id','wamid.WA34B.OUT1',
  'provider_kind','delivered','provider_timestamp','2026-10-18T12:01:00Z',
  'payload_fixture',jsonb_build_object('fixture_ref','FIXTURE_WA34B_STATUS_1'));
 v_second:=v_first||jsonb_build_object(
  'payload_fixture',jsonb_build_object('fixture_ref','FIXTURE_WA34B_STATUS_2'));
 v:=prumo_private.aceitar_lote_multicanal_fixture_s0(jsonb_build_array(v_first));
 if (v->>'accepted')::integer<>1 then raise exception 'FAIL WA34B-CB-04 first fixture';end if;
 v:=prumo_private.aceitar_lote_multicanal_fixture_s0(jsonb_build_array(v_first));
 if (v->>'duplicates')::integer<>1 then raise exception 'FAIL WA34B-CB-04 duplicate fixture';end if;
 begin
  perform prumo_private.aceitar_lote_multicanal_fixture_s0(jsonb_build_array(v_second));
  raise exception 'FAIL WA34B-CB-04 changed marker silently discarded';
 exception when unique_violation then null;end;
 if (select count(*) from prumo_private.inbox_eventos_s0
   where provider_message_id_s0='wamid.WA34B.OUT1'
   and tipo='status_callback')<>1
 then raise exception 'FAIL WA34B-CB-04 unexpected fixture insert';end if;
end $t$;
\echo 'PASS WA34B-CB-04: limite S0-030 demonstrado (NAO autoriza dedupe Meta)'
rollback;
