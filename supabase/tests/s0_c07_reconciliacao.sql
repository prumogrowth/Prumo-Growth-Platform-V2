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


do $fixture$
declare r jsonb;v_envio uuid;v_envio_b uuid;v_instante timestamptz;
begin
 r:=prumo_private.agendar_recontatos_sinteticos(
 'c1000000-0000-4000-8000-000000000071','c2000000-0000-4000-8000-000000000071',
 'c5000000-0000-4000-8000-000000000071','c3000000-0000-4000-8000-000000000071',
 'RECON-A',jsonb_build_array(
 jsonb_build_object('template_id','c6000000-0000-4000-8000-000000000071',
 'agendado_em',(statement_timestamp()+interval '1 day')::text),
 jsonb_build_object('template_id','c6000000-0000-4000-8000-000000000071',
 'agendado_em',(statement_timestamp()+interval '2 days')::text)));
 if r->>'outcome'<>'APPLIED' then raise exception 'FAIL C07-RECON fixture A';end if;
 r:=prumo_private.agendar_recontatos_sinteticos(
 'c1000000-0000-4000-8000-000000000072','c2000000-0000-4000-8000-000000000072',
 'c5000000-0000-4000-8000-000000000072','c3000000-0000-4000-8000-000000000072',
 'RECON-B',jsonb_build_array(jsonb_build_object(
 'template_id','c6000000-0000-4000-8000-000000000072',
 'agendado_em',(statement_timestamp()+interval '1 day')::text)));
 if r->>'outcome'<>'APPLIED' then raise exception 'FAIL C07-RECON fixture B';end if;
 select e.id into v_envio from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p
 on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 where p.chave_idempotencia='RECON-A' and e.ordem=1;
 select e.id into v_envio_b from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p
 on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 where p.chave_idempotencia='RECON-B' and e.ordem=1;
 r:=prumo_private.reservar_envio_sintetico(
 'c2000000-0000-4000-8000-000000000071',v_envio,statement_timestamp()+interval '4 days');
 if r->>'outcome'<>'RESERVED_SIMULATED' then raise exception 'FAIL reserve A';end if;
 r:=prumo_private.reservar_envio_sintetico(
 'c2000000-0000-4000-8000-000000000072',v_envio_b,statement_timestamp()+interval '4 days');
 if r->>'outcome'<>'RESERVED_SIMULATED' then raise exception 'FAIL reserve B';end if;
 r:=prumo_private.vincular_referencia_c07_sintetica(
 'c2000000-0000-4000-8000-000000000072',v_envio_b,
 'c3000000-0000-4000-8000-000000000072','provider-B');
 -- Callback arrives BEFORE A is bound to its fictitious provider reference.
 v_instante:=statement_timestamp()-interval '1 hour';
 r:=prumo_private.registrar_callback_c07_sintetico(
 'c3000000-0000-4000-8000-000000000071','provider-A',
 'A-unknown','INCERTO_SIMULADO',v_instante);
 if r->>'outcome'<>'PENDING_RECONCILIATION' then
  raise exception 'FAIL unknown callback became linked';end if;
 r:=prumo_private.registrar_callback_c07_sintetico(
 'c3000000-0000-4000-8000-000000000071','provider-A',
 'A-unknown','INCERTO_SIMULADO',v_instante);
 if r->>'outcome'<>'ALREADY_APPLIED' then
  raise exception 'FAIL duplicate unknown';end if;
 -- The exact same fictitious reference in B is NOT attached to A.
 r:=prumo_private.registrar_callback_c07_sintetico(
 'c3000000-0000-4000-8000-000000000072','provider-A',
 'B-unknown','FALHOU_SIMULADO',v_instante);
 if r->>'outcome'<>'PENDING_RECONCILIATION' then
  raise exception 'FAIL cross shop callback';end if;
 r:=prumo_private.vincular_referencia_c07_sintetica(
 'c2000000-0000-4000-8000-000000000071',v_envio,
 'c3000000-0000-4000-8000-000000000071','provider-A');
 if r->>'outcome'<>'APPLIED' then raise exception 'FAIL late reference';end if;
 r:=prumo_private.registrar_callback_c07_sintetico(
 'c3000000-0000-4000-8000-000000000071','provider-A',
 'A-fail-1','FALHOU_SIMULADO',v_instante+interval '1 minute');
 r:=prumo_private.registrar_callback_c07_sintetico(
 'c3000000-0000-4000-8000-000000000071','provider-A',
 'A-fail-2','FALHOU_SIMULADO',v_instante+interval '2 minutes');
 r:=prumo_private.registrar_callback_c07_sintetico(
 'c3000000-0000-4000-8000-000000000071','provider-A',
 'A-sent-after-fail','ENVIADO_SIMULADO',v_instante+interval '3 minutes');
 if (select count(*) from public.pendencias_reconciliacao_c07_sinteticas
     where concessionaria_id='c2000000-0000-4000-8000-000000000071')<>4
 or (select count(*) from public.pendencias_reconciliacao_c07_sinteticas
     where concessionaria_id='c2000000-0000-4000-8000-000000000072')<>1
 or not exists(select 1 from public.pendencias_reconciliacao_c07_sinteticas
     where categoria='SINAIS_CONTRADITORIOS'
     and concessionaria_id='c2000000-0000-4000-8000-000000000071')
 then raise exception 'FAIL callback triage lost/duplicated pending cases';end if;
end $fixture$;
\echo 'PASS C07-REC-01: triagem de incerto, falha, contradicao e callback desconhecido sem duplicar'

do $verify$
declare r jsonb;v_second uuid;
begin
 r:=prumo_private.diagnosticar_falhas_c07_sintetico(
 'c2000000-0000-4000-8000-000000000071',
 'c5000000-0000-4000-8000-000000000071');
 if (r->>'falhas_reportadas_tentativas_distintas')::integer<>1
  or (r->>'tentativas_com_incerteza')::integer<>0
  or r->>'falhas_qualificadas'<>'NAO_AVALIADAS_DEC_15'
  or r->>'reenvio_automatico'<>'PROIBIDO'
 then raise exception 'FAIL diagnostics qualified duplicates as two failures';end if;
 select e.id into v_second from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p
 on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 where p.chave_idempotencia='RECON-A' and e.ordem=2;
 r:=prumo_private.reservar_envio_sintetico(
 'c2000000-0000-4000-8000-000000000071',
 v_second,statement_timestamp()+interval '4 days');
 if r->>'outcome'<>'NOT_ELIGIBLE'
  or r->>'reason'<>'C07_REVIEW_REQUIRED_NO_AUTOMATIC_RETRY'
  or (select estado from public.envios_template_sinteticos where id=v_second)<>'programado'
 then raise exception 'FAIL blind retry after uncertain/failure';end if;
end $verify$;
\echo 'PASS C07-REC-02: duas falhas do mesmo envio contam uma tentativa, bloqueio de nova reserva'

-- The original plan still says 'ativo' when a prior attempt has failed.
-- An idempotent replay MUST NOT report it as currently executable.
do $replay$
declare v_data jsonb;v_r jsonb;
begin
 select jsonb_agg(jsonb_build_object(
  'template_id',e.template_id::text,'agendado_em',e.agendado_em::text)
  order by e.ordem) into v_data
 from public.planos_recontato_sinteticos p
 join public.envios_template_sinteticos e
  on e.concessionaria_id=p.concessionaria_id and e.plano_id=p.id
 where p.concessionaria_id='c2000000-0000-4000-8000-000000000071'
  and p.chave_idempotencia='RECON-A';
 v_r:=prumo_private.agendar_recontatos_sinteticos(
 'c1000000-0000-4000-8000-000000000071',
 'c2000000-0000-4000-8000-000000000071',
 'c5000000-0000-4000-8000-000000000071',
 'c3000000-0000-4000-8000-000000000071','RECON-A',v_data);
 if v_r->>'outcome'<>'ALREADY_APPLIED'
  or v_r->>'estado_plano'<>'ativo'
  or (v_r->>'executavel_simulacao')::boolean is distinct from false
 then raise exception 'FAIL audit C07 replay still claims execution permitted';end if;
end $replay$;
\echo 'PASS C07-AUD-01: replay de plano ativo com falha retorna nao executavel'


do $review$
declare v_unknown uuid;v_failure uuid;v_A uuid;v_B uuid;
 r jsonb;
begin
 select id into v_unknown from public.pendencias_reconciliacao_c07_sinteticas
 where concessionaria_id='c2000000-0000-4000-8000-000000000071'
  and categoria='SEM_CORRELACAO';
 select id into v_failure from public.pendencias_reconciliacao_c07_sinteticas
 where concessionaria_id='c2000000-0000-4000-8000-000000000071'
  and categoria='FALHA_REPORTADA' order by id limit 1;
 select e.id into v_A from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p on p.id=e.plano_id
 and p.concessionaria_id=e.concessionaria_id
 where p.chave_idempotencia='RECON-A' and e.ordem=1;
 select e.id into v_B from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p on p.id=e.plano_id
 and p.concessionaria_id=e.concessionaria_id
 where p.chave_idempotencia='RECON-B' and e.ordem=1;
 begin
  perform prumo_private.conciliar_pendencia_c07_sintetica(
   'c1000000-0000-4000-8000-000000000072',
   'c2000000-0000-4000-8000-000000000071',
   v_unknown,1,'VINCULAR_SINTETICAMENTE','Revisao ficticia por gestor B',v_A);
  raise exception 'FAIL gestor B reconciliou A';
 exception when insufficient_privilege then null;end;
 begin
  perform prumo_private.conciliar_pendencia_c07_sintetica(
   'c1000000-0000-4000-8000-000000000071',
   'c2000000-0000-4000-8000-000000000071',
   v_unknown,1,'VINCULAR_SINTETICAMENTE','Vinculo cruzado nunca permitido',v_B);
  raise exception 'FAIL cross-shop reconciliation';
 exception when insufficient_privilege then null;end;
 r:=prumo_private.conciliar_pendencia_c07_sintetica(
  'c1000000-0000-4000-8000-000000000071',
  'c2000000-0000-4000-8000-000000000071',
  v_unknown,1,'VINCULAR_SINTETICAMENTE','Referencia ficticia conferida no mesmo canal',v_A);
 if r->>'outcome'<>'APPLIED' or r->>'comprovacao_real'<>'NENHUMA'
 then raise exception 'FAIL valid manual binding';end if;
 r:=prumo_private.conciliar_pendencia_c07_sintetica(
  'c1000000-0000-4000-8000-000000000071',
  'c2000000-0000-4000-8000-000000000071',
  v_unknown,1,'VINCULAR_SINTETICAMENTE','Referencia ficticia conferida no mesmo canal',v_A);
 if r->>'outcome'<>'ALREADY_APPLIED' then
  raise exception 'FAIL replay reconciler';end if;
 begin
  perform prumo_private.conciliar_pendencia_c07_sintetica(
   'c1000000-0000-4000-8000-000000000071',
   'c2000000-0000-4000-8000-000000000071',
   v_unknown,1,'ENCERRAR_SEM_PROVA','Tentativa com versao antiga',null);
  raise exception 'FAIL stale reconciliation altered decision';
 exception when serialization_failure then null;end;
 r:=prumo_private.conciliar_pendencia_c07_sintetica(
  'c1000000-0000-4000-8000-000000000071',
  'c2000000-0000-4000-8000-000000000071',
  v_failure,1,'ENCERRAR_SEM_PROVA','Falha ficticia nao comprova envio',null);
 if r->>'outcome'<>'APPLIED' then raise exception 'FAIL failure closure';end if;
 r:=prumo_private.conciliar_pendencia_c07_sintetica(
  'c1000000-0000-4000-8000-000000000071',
  'c2000000-0000-4000-8000-000000000071',
  v_failure,1,'ENCERRAR_SEM_PROVA','Falha ficticia nao comprova envio',null);
 if r->>'outcome'<>'ALREADY_APPLIED' then
  raise exception 'FAIL replay failure closure';end if;
 if (select count(*) from public.auditoria_reconciliacao_c07_sintetica)<>2
 or (select count(*) from public.associacoes_callback_c07_sinteticas)<>1
 or not exists(select 1 from public.eventos_callback_sinteticos
  where evento_externo_ficticio='A-unknown'
    and resultado='PENDENTE_RECONCILIACAO' and envio_id is null)
 then raise exception 'FAIL immutable observation or reconciliation history';end if;
 r:=prumo_private.diagnosticar_falhas_c07_sintetico(
 'c2000000-0000-4000-8000-000000000071',
 'c5000000-0000-4000-8000-000000000071');
 if (r->>'tentativas_com_incerteza')::integer<>1
 then raise exception 'FAIL manually bound uncertainty not in diagnostic';end if;
end $review$;
\echo 'PASS C07-REC-03: conciliacao com versao/escopo, auditoria imutavel e replay idempotente'

do $caution$
declare r jsonb;v_plano uuid;
begin
 select id into v_plano from public.planos_recontato_sinteticos
 where chave_idempotencia='RECON-A';
 r:=prumo_private.cancelar_plano_gestor_sintetico(
 'c1000000-0000-4000-8000-000000000071',
 'c2000000-0000-4000-8000-000000000071',v_plano,1);
 if r->>'outcome'<>'APPLIED' then raise exception 'FAIL cancellation fixture';end if;
 begin
  perform prumo_private.agendar_recontatos_sinteticos(
   'c1000000-0000-4000-8000-000000000071','c2000000-0000-4000-8000-000000000071',
   'c5000000-0000-4000-8000-000000000071','c3000000-0000-4000-8000-000000000071',
   'RETRY-BLIND-BLOCKED',jsonb_build_array(jsonb_build_object(
   'template_id','c6000000-0000-4000-8000-000000000071',
   'agendado_em',(statement_timestamp()+interval '5 days')::text)));
  raise exception 'FAIL new plan after failure';
 exception when invalid_parameter_value then null;end;
 if (select count(*) from public.planos_recontato_sinteticos
   where ciclo_id='c5000000-0000-4000-8000-000000000071')<>1
 or (select status_comercial from public.ciclos_comerciais
     where id='c5000000-0000-4000-8000-000000000071')<>'aguardando primeiro disparo'
 then raise exception 'FAIL no-retry/stopwatch invariant';end if;
end $caution$;
\echo 'PASS C07-REC-04: historico de falha bloqueia novo plano mesmo apos fechamento da revisao'

set local role authenticated;
select set_config('request.jwt.claim.sub','c1000000-0000-4000-8000-000000000071',true);
do $scopes$ begin
 if (select count(*) from public.pendencias_reconciliacao_c07_sinteticas)<>4
 or (select count(*) from public.auditoria_reconciliacao_c07_sintetica)<>2
 or (select count(*) from public.associacoes_callback_c07_sinteticas)<>1
 then raise exception 'FAIL manager A cannot see own review records';end if;
 begin
  update public.pendencias_reconciliacao_c07_sinteticas
   set estado='encerrada' where 1=1;
  raise exception 'FAIL manager bypassed private reconciliation';
 exception when insufficient_privilege then null;end;
end $scopes$;
select set_config('request.jwt.claim.sub','c1000000-0000-4000-8000-000000000072',true);
do $scopes$ begin
 if (select count(*) from public.pendencias_reconciliacao_c07_sinteticas)<>1
 or (select count(*) from public.auditoria_reconciliacao_c07_sintetica)<>0
 or (select count(*) from public.associacoes_callback_c07_sinteticas)<>0
 then raise exception 'FAIL manager B accessed A review';end if;
end $scopes$;
reset role;
\echo 'PASS C07-REC-05: RLS de pendencias, associacoes e auditoria por concessionaria'
rollback;
