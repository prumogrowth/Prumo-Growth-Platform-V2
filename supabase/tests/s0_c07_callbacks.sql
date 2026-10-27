\set ON_ERROR_STOP on
begin;
insert into auth.users(id) values
 ('c1000000-0000-4000-8000-000000000071'),
 ('c1000000-0000-4000-8000-000000000072');
insert into public.atores(id) values
 ('c1000000-0000-4000-8000-000000000071'),
 ('c1000000-0000-4000-8000-000000000072');
insert into public.concessionarias(id,nome_operacional) values
 ('c2000000-0000-4000-8000-000000000071','C07 A ficticia'),
 ('c2000000-0000-4000-8000-000000000072','C07 B ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('c1000000-0000-4000-8000-000000000071','c2000000-0000-4000-8000-000000000071','gestor'),
 ('c1000000-0000-4000-8000-000000000072','c2000000-0000-4000-8000-000000000072','gestor');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('c3000000-0000-4000-8000-000000000071','c2000000-0000-4000-8000-000000000071','C07_EMISSOR_A'),
 ('c3000000-0000-4000-8000-000000000072','c2000000-0000-4000-8000-000000000072','C07_EMISSOR_B');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('c4000000-0000-4000-8000-000000000071','c2000000-0000-4000-8000-000000000071','+5581877000007'),
 ('c4000000-0000-4000-8000-000000000072','c2000000-0000-4000-8000-000000000072','+5581877000007');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
 ('c5000000-0000-4000-8000-000000000071','c2000000-0000-4000-8000-000000000071','c4000000-0000-4000-8000-000000000071'),
 ('c5000000-0000-4000-8000-000000000072','c2000000-0000-4000-8000-000000000072','c4000000-0000-4000-8000-000000000072');
insert into public.catalogo_templates_sinteticos(id,concessionaria_id,codigo,versao,aprovado_simulacao) values
 ('c6000000-0000-4000-8000-000000000071','c2000000-0000-4000-8000-000000000071','T',1,true),
 ('c6000000-0000-4000-8000-000000000072','c2000000-0000-4000-8000-000000000072','T',1,true);
insert into public.evidencias_elegibilidade_sinteticas(
 concessionaria_id,lead_id,canal_id,finalidade,referencia_ficticia) values
 ('c2000000-0000-4000-8000-000000000071','c4000000-0000-4000-8000-000000000071',
  'c3000000-0000-4000-8000-000000000071','recontato_comercial_sintetico','C07_FAKE_EVIDENCE_A'),
 ('c2000000-0000-4000-8000-000000000072','c4000000-0000-4000-8000-000000000072',
  'c3000000-0000-4000-8000-000000000072','recontato_comercial_sintetico','C07_FAKE_EVIDENCE_B');

do $case$
declare r jsonb; e uuid;
begin
 r:=prumo_private.agendar_recontatos_sinteticos(
 'c1000000-0000-4000-8000-000000000071','c2000000-0000-4000-8000-000000000071',
 'c5000000-0000-4000-8000-000000000071','c3000000-0000-4000-8000-000000000071',
 'C07-PLAN-A',jsonb_build_array(jsonb_build_object('template_id',
 'c6000000-0000-4000-8000-000000000071',
 'agendado_em',(statement_timestamp()+interval '1 day')::text)));
 select e0.id into e from public.envios_template_sinteticos e0
 where e0.concessionaria_id='c2000000-0000-4000-8000-000000000071';
 r:=prumo_private.reservar_envio_sintetico(
 'c2000000-0000-4000-8000-000000000071',e,statement_timestamp()+interval '2 days');
 if r->>'outcome'<>'RESERVED_SIMULATED' then raise exception 'FAIL C07 reservou A';end if;
 r:=prumo_private.vincular_referencia_c07_sintetica(
 'c2000000-0000-4000-8000-000000000071',e,
 'c3000000-0000-4000-8000-000000000071','same-fake-message-id');
 if r->>'outcome'<>'APPLIED' then raise exception 'FAIL C07 vinculo A';end if;
 r:=prumo_private.vincular_referencia_c07_sintetica(
 'c2000000-0000-4000-8000-000000000071',e,
 'c3000000-0000-4000-8000-000000000071','same-fake-message-id');
 if r->>'outcome'<>'ALREADY_APPLIED' then raise exception 'FAIL C07 idempotencia do vinculo';end if;
end $case$;
\echo 'PASS C07-01: correlacao simulada a envio reservado sem enviar'

do $case$
declare r jsonb; d timestamptz :=statement_timestamp()-interval '1 day';r2 jsonb;
begin
 r:=prumo_private.registrar_callback_c07_sintetico(
 'c3000000-0000-4000-8000-000000000071','same-fake-message-id',
 'event-accepted','ACEITO_SIMULADO',d);
 r2:=prumo_private.registrar_callback_c07_sintetico(
 'c3000000-0000-4000-8000-000000000071','same-fake-message-id',
 'event-accepted','ACEITO_SIMULADO',d);
 if r->>'outcome'<>'APPLIED' or r2->>'outcome'<>'ALREADY_APPLIED'
 then raise exception 'FAIL C07 evento idempotente';end if;
 begin
  perform prumo_private.registrar_callback_c07_sintetico(
   'c3000000-0000-4000-8000-000000000071','same-fake-message-id',
   'event-accepted','FALHOU_SIMULADO',d);
  raise exception 'FAIL C07 replay mesmo ID divergente';
 exception when unique_violation then null;end;
 r:=prumo_private.registrar_callback_c07_sintetico(
  'c3000000-0000-4000-8000-000000000071','same-fake-message-id',
  'event-read','LIDO_SIMULADO',d+interval '3 hours');
 r:=prumo_private.registrar_callback_c07_sintetico(
  'c3000000-0000-4000-8000-000000000071','same-fake-message-id',
  'event-sent','ENVIADO_SIMULADO',d+interval '1 hour');
 if (r->>'fora_de_ordem')::boolean is distinct from true
 then raise exception 'FAIL C07 callback fora ordem';end if;
 r:=prumo_private.registrar_callback_c07_sintetico(
  'c3000000-0000-4000-8000-000000000071','same-fake-message-id',
  'event-uncertain','INCERTO_SIMULADO',d+interval '2 hours');
 r:=prumo_private.registrar_callback_c07_sintetico(
  'c3000000-0000-4000-8000-000000000071','same-fake-message-id',
  'event-failed','FALHOU_SIMULADO',d+interval '2 hours');
 if not exists(select 1 from public.envios_template_sinteticos e where
   e.concessionaria_id='c2000000-0000-4000-8000-000000000071'
   and e.callback_aceito_simulado and e.callback_lido_simulado
   and e.callback_enviado_simulado and e.callback_incerto_simulado
   and e.callback_falhou_simulado and e.estado='reservado')
 or (select count(*) from public.eventos_callback_sinteticos
    where concessionaria_id='c2000000-0000-4000-8000-000000000071')<>5
 or (select status_comercial from public.ciclos_comerciais
    where id='c5000000-0000-4000-8000-000000000071')<>'aguardando primeiro disparo'
 then raise exception 'FAIL C07 mudou comercial ou perdeu eventos';end if;
end $case$;
\echo 'PASS C07-02: duplicidade, conflito, ordem tardia, falha/incerteza sem alterar comercial'

do $case$
declare r jsonb;
begin
 r:=prumo_private.registrar_callback_c07_sintetico(
 'c3000000-0000-4000-8000-000000000072',
 'same-fake-message-id','B-unknown','ENTREGUE_SIMULADO',statement_timestamp());
 if r->>'outcome'<>'PENDING_RECONCILIATION'
 or r->>'envio_id' is not null
 then raise exception 'FAIL C07 correlacao de A vazou em B';end if;
 r:=prumo_private.registrar_callback_c07_sintetico(
 'c3000000-0000-4000-8000-000000000071',
 'not-exists-fake','A-unknown','ACEITO_SIMULADO',statement_timestamp());
 if r->>'outcome'<>'PENDING_RECONCILIATION'
 or (select count(*) from public.eventos_callback_sinteticos
     where resultado='PENDENTE_RECONCILIACAO')<>2
 then raise exception 'FAIL C07 desconhecido nao preservado';end if;
 if (select count(*) from public.ciclos_comerciais)<>2
 then raise exception 'FAIL C07 criou ciclo fantasma';end if;
end $case$;
\echo 'PASS C07-03: callback nao correlacionado vai a pendencia, mesmo ID em outra loja isolado'

-- C07 late callback after opt-out must preserve original schedule cancellation.
do $case$
declare r jsonb;
begin
 r:=prumo_private.registrar_optout_sintetico(
 'c2000000-0000-4000-8000-000000000071',
 'c4000000-0000-4000-8000-000000000071',
 'c3000000-0000-4000-8000-000000000071',
 'recontato_comercial_sintetico','C07-OUT-1');
 if r->>'outcome'<>'APPLIED' then raise exception 'FAIL C07 optout fixture';end if;
 r:=prumo_private.registrar_callback_c07_sintetico(
 'c3000000-0000-4000-8000-000000000071','same-fake-message-id',
 'late-delivery','ENTREGUE_SIMULADO',statement_timestamp());
 if r->>'outcome'<>'APPLIED'
 or not exists(select 1 from public.envios_template_sinteticos
    where concessionaria_id='c2000000-0000-4000-8000-000000000071'
     and estado='cancelado' and callback_entregue_simulado)
 or (select status_comercial from public.ciclos_comerciais
     where id='c5000000-0000-4000-8000-000000000071')<>'aguardando primeiro disparo'
 then raise exception 'FAIL C07 callback tardio reativou envio cancelado';end if;
end $case$;
\echo 'PASS C07-04: callback apos optout preserva cancelamento e evento sem disparo'

set local role authenticated;
select set_config('request.jwt.claim.sub','c1000000-0000-4000-8000-000000000071',true);
do $case$ begin
 if (select count(*) from public.eventos_callback_sinteticos)<>7
 then raise exception 'FAIL C07 gestor A consulta callbacks';end if;
 begin
  insert into public.eventos_callback_sinteticos(concessionaria_id,canal_id,
    correlacao_externa_ficticia,evento_externo_ficticio,estado_reportado,
    instante_evento,resultado,fingerprint)
   values('c2000000-0000-4000-8000-000000000071',
   'c3000000-0000-4000-8000-000000000071','hack','hack','ACEITO_SIMULADO',
   statement_timestamp(),'PENDENTE_RECONCILIACAO','fake');
  raise exception 'FAIL C07 gestor escreveu callback';
 exception when insufficient_privilege then null;end;
end $case$;
select set_config('request.jwt.claim.sub','c1000000-0000-4000-8000-000000000072',true);
do $case$ begin
 if (select count(*) from public.eventos_callback_sinteticos)<>1
 then raise exception 'FAIL C07 vazamento callbacks A para B';end if;
end $case$;
reset role;
\echo 'PASS C07-05: RLS callbacks A/B e escrita por gestor negada'
rollback;
