-- S0/034A: closing A33-01/02/03 on purely synthetic C02-bound jobs.
-- Not a Meta receipt, C07 adapter, operational worker or hosted migration.
-- All constraints are additive to 001-033. Existing generic fixture tasks
-- without a C02 attachment retain the S0/032 synthetic lifecycle.

-- A33-03: every proof ties its channel to the very same event and message.
alter table prumo_private.inbox_eventos_s0
 add constraint inbox_evento_loja_canal_id_uniq_s0
 unique(concessionaria_id,canal_id,id);
alter table public.mensagens
 add constraint mensagens_loja_canal_id_uniq_s0
 unique(concessionaria_id,canal_id,id);
alter table prumo_private.inbox_c02_fixture_s0
 add constraint inbox_c02_evento_canal_s0
 foreign key(concessionaria_id,canal_id,inbox_id)
 references prumo_private.inbox_eventos_s0(concessionaria_id,canal_id,id);
alter table prumo_private.aplicacoes_c02_inbox_s0
 add constraint aplicacao_c02_evento_canal_s0
 foreign key(concessionaria_id,canal_id,inbox_id)
 references prumo_private.inbox_eventos_s0(concessionaria_id,canal_id,id),
 add constraint aplicacao_c02_mensagem_canal_s0
 foreign key(concessionaria_id,canal_id,mensagem_id)
 references public.mensagens(concessionaria_id,canal_id,id);

-- A33-02: terminal cause and audit must preserve distinct identity review
-- categories. They are TECHNICAL reasons, not new commercial states.
alter table prumo_private.tarefas_ingresso_s0
 drop constraint tarefas_ingresso_s0_motivo_terminal_s0_check,
 add constraint tarefas_ingresso_s0_motivo_terminal_s0_check
 check(motivo_terminal_s0 is null or motivo_terminal_s0 in
 ('FALHA_RETRY_SEGURA','FALHA_DEFINITIVA','RESULTADO_INCERTO',
 'LEASE_EXPIRADO_INCERTO','SEM_EFEITO_FIXTURE','IDENTITY_CONFLICT','NEEDS_REVIEW'));
alter table prumo_private.historico_tarefas_ingresso_s0
 drop constraint historico_tarefas_ingresso_s0_acao_check,
 add constraint historico_tarefas_ingresso_s0_acao_check
 check(acao in (
 'RESERVA','APLICADO_SINTETICO','FALHA_RETRY_SEGURA','FALHA_DEFINITIVA',
 'RESULTADO_INCERTO','EXPIRADO_QUARENTENA','EXPIRADO_SEM_EFEITO_FIXTURE',
 'EXPIRADO_DEFINITIVO','IDENTITY_CONFLICT','NEEDS_REVIEW'));

-- A33-01/03: proof itself must belong to the recorded inbound message
-- on the correct channel AND carry the same external ID and fixture text.
create function prumo_private.validar_prova_c02_s0()
returns trigger language plpgsql security invoker set search_path='' as $fn$
declare v_id text;v_texto text;v_direcao text;v_msg_id text;
begin
 select f.id_externo_sintetico,f.texto_sintetico
 into v_id,v_texto
 from prumo_private.inbox_c02_fixture_s0 f
 where f.concessionaria_id=new.concessionaria_id
   and f.canal_id=new.canal_id and f.inbox_id=new.inbox_id;
 if not found then
  raise exception 'MISSING_C02_FIXTURE_PROOF' using errcode='23514';end if;
 select m.direcao,m.id_externo,m.conteudo_sintetico
 into v_direcao,v_msg_id,v_texto
 from public.mensagens m
 where m.concessionaria_id=new.concessionaria_id
   and m.canal_id=new.canal_id and m.id=new.mensagem_id;
 if not found or v_direcao<>'entrada' or v_msg_id is distinct from v_id
   or v_texto is distinct from (
    select f.texto_sintetico from prumo_private.inbox_c02_fixture_s0 f
    where f.concessionaria_id=new.concessionaria_id and f.inbox_id=new.inbox_id)
 then raise exception 'INVALID_C02_MESSAGE_PROOF' using errcode='23514';end if;
 return new;
end $fn$;
create trigger aplicacao_c02_prova_sem_desvio_s0
 before insert or update on prumo_private.aplicacoes_c02_inbox_s0
 for each row execute function prumo_private.validar_prova_c02_s0();

-- Independent database-level guard: even a direct UPDATE of the task to
-- APPLIED cannot skip the C02 proof if that inbox has a C02 attachment.
create function prumo_private.validar_applied_com_prova_s0()
returns trigger language plpgsql security invoker set search_path='' as $fn$
begin
 if exists(select 1 from prumo_private.inbox_c02_fixture_s0 f
  where f.concessionaria_id=new.concessionaria_id and f.inbox_id=new.inbox_id)
 and not exists(select 1 from prumo_private.aplicacoes_c02_inbox_s0 a
  where a.concessionaria_id=new.concessionaria_id and a.inbox_id=new.inbox_id
    and a.worker_fixture=old.lease_worker
    and a.versao_reserva=old.versao)
 then raise exception 'C02_PROOF_REQUIRED' using errcode='23514';end if;
 return new;
end $fn$;
create trigger tarefa_c02_applied_exige_prova_s0
 before update of estado on prumo_private.tarefas_ingresso_s0
 for each row when (new.estado='APPLIED')
 execute function prumo_private.validar_applied_com_prova_s0();


-- Replace the established 032 result handler without changing its signature.
create or replace function prumo_private.registrar_resultado_ingresso_s0(
 p_loja uuid,p_canal uuid,p_inbox uuid,p_worker uuid,
 p_versao bigint,p_resultado text
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_t record;v_estado text;v_proxima timestamptz;v_motivo text;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_loja is null or p_canal is null or p_inbox is null or p_worker is null
 or p_versao is null or p_versao<2 or p_resultado is null
 or p_resultado not in ('APLICADO_SINTETICO','FALHA_RETRY_SEGURA',
   'FALHA_DEFINITIVA','RESULTADO_INCERTO','IDENTITY_CONFLICT','NEEDS_REVIEW')
 then raise exception 'INVALID_WORKER_RESULT' using errcode='22023';end if;
 select t.* into v_t from prumo_private.tarefas_ingresso_s0 t
 join prumo_private.inbox_eventos_s0 i
  on i.id=t.inbox_id and i.concessionaria_id=t.concessionaria_id
 join public.canais_loja c
  on c.id=i.canal_id and c.concessionaria_id=i.concessionaria_id
 where t.concessionaria_id=p_loja and i.canal_id=p_canal
   and t.inbox_id=p_inbox and c.modo='simulado'
 for update of t;
 if not found then raise exception 'INVALID_WORKER_SCOPE' using errcode='42501';end if;
 if exists(select 1 from prumo_private.historico_tarefas_ingresso_s0 h
  where h.concessionaria_id=p_loja and h.inbox_id=p_inbox
    and h.versao_antes=p_versao and h.acao=p_resultado
    and h.ator_fixture=p_worker)
 then return pg_catalog.jsonb_build_object('outcome','ALREADY_RECORDED');end if;
 if v_t.estado<>'LEASED' or v_t.versao<>p_versao
 or v_t.lease_worker is distinct from p_worker
 or v_t.lease_ate<=pg_catalog.clock_timestamp()
 then raise exception 'STALE_OR_EXPIRED_LEASE' using errcode='40001';end if;
 -- C02-bound jobs have an additional proof obligation: the generic
 -- lifecycle function cannot bypass the atomic C02 application path.
 if p_resultado='APLICADO_SINTETICO'
   and exists(select 1 from prumo_private.inbox_c02_fixture_s0 f
     where f.concessionaria_id=p_loja and f.canal_id=p_canal and f.inbox_id=p_inbox)
   and not exists(select 1 from prumo_private.aplicacoes_c02_inbox_s0 a
     where a.concessionaria_id=p_loja and a.canal_id=p_canal and a.inbox_id=p_inbox
       and a.worker_fixture=p_worker and a.versao_reserva=p_versao)
 then raise exception 'C02_PROOF_REQUIRED' using errcode='23514';end if;
 -- Review is not an uncertain provider-side effect. Require the durable
 -- pending identity record with the exact synthetic input and reason.
 if p_resultado in ('IDENTITY_CONFLICT','NEEDS_REVIEW')
   and not exists(
    select 1 from prumo_private.inbox_c02_fixture_s0 f
    join prumo_private.pendencias_identidade_s0 p
      on p.concessionaria_id=f.concessionaria_id
      and p.canal_id=f.canal_id and p.id_externo=f.id_externo_sintetico
    where f.concessionaria_id=p_loja and f.canal_id=p_canal and f.inbox_id=p_inbox
      and p.telefone_sintetico=f.telefone_sintetico
      and p.texto_sintetico=f.texto_sintetico and p.motivo=p_resultado)
 then raise exception 'IDENTITY_PENDING_PROOF_REQUIRED' using errcode='23514';end if;
 v_proxima:=null;
 v_motivo:=case when p_resultado='APLICADO_SINTETICO' then null
   else p_resultado end;
 v_estado:=case p_resultado
  when 'APLICADO_SINTETICO' then 'APPLIED'
  when 'RESULTADO_INCERTO' then 'QUARANTINED'
  when 'IDENTITY_CONFLICT' then 'QUARANTINED'
  when 'NEEDS_REVIEW' then 'QUARANTINED'
  when 'FALHA_DEFINITIVA' then 'DEAD_LETTER'
  when 'FALHA_RETRY_SEGURA' then
   case when v_t.tentativas>=3 then 'DEAD_LETTER' else 'RETRY_PENDING' end end;
 if v_estado='RETRY_PENDING' then
  v_proxima:=pg_catalog.clock_timestamp()+
   case when v_t.tentativas=1 then interval '15 seconds'
    else interval '60 seconds' end;
 end if;
 update prumo_private.tarefas_ingresso_s0
 set estado=v_estado,versao=v_t.versao+1,
  lease_worker=null,lease_ate=null,proxima_tentativa_em=v_proxima,
  motivo_terminal_s0=v_motivo,
  concluido_em=case when v_estado in ('APPLIED','DEAD_LETTER','QUARANTINED')
   then pg_catalog.clock_timestamp() else null end
 where concessionaria_id=p_loja and inbox_id=p_inbox;
 insert into prumo_private.historico_tarefas_ingresso_s0(
  concessionaria_id,inbox_id,versao_antes,versao_depois,
  estado_antes,estado_depois,acao,ator_fixture)
 values(p_loja,p_inbox,v_t.versao,v_t.versao+1,
 'LEASED',v_estado,p_resultado,p_worker);
 return pg_catalog.jsonb_build_object('outcome','RECORDED',
  'estado',v_estado,'versao',v_t.versao+1,'tentativas',v_t.tentativas);
end $fn$;

-- Replace the established 033 C02 handler without changing its signature.
create or replace function prumo_private.aplicar_inbox_c02_s0(
 p_loja uuid,p_canal uuid,p_inbox uuid,p_worker uuid,p_versao bigint
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_job record;v_old record;v_c02 jsonb;v_settle jsonb;v_msg uuid;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_loja is null or p_canal is null or p_inbox is null
 or p_worker is null or p_versao is null or p_versao<2
 then raise exception 'INVALID_C02_APPLY_ARGS' using errcode='22023';end if;
 select t.estado,t.versao,t.lease_worker,t.lease_ate,
  f.telefone_sintetico,f.id_externo_sintetico,f.texto_sintetico,
  f.mobile_confirmado_fixture
 into v_job
 from prumo_private.tarefas_ingresso_s0 t
 join prumo_private.inbox_eventos_s0 i
  on i.id=t.inbox_id and i.concessionaria_id=t.concessionaria_id
 join prumo_private.inbox_c02_fixture_s0 f
  on f.inbox_id=i.id and f.concessionaria_id=i.concessionaria_id
  and f.canal_id=i.canal_id
 join public.canais_loja c on c.id=i.canal_id and c.concessionaria_id=i.concessionaria_id
 join public.concessionarias l on l.id=i.concessionaria_id
 where t.concessionaria_id=p_loja and t.inbox_id=p_inbox
  and i.canal_id=p_canal and i.tipo='inbound_message'
  and i.payload_fixture_s0 is not null and i.app_fixture_ref is not null
  and i.provider_message_id_s0=f.id_externo_sintetico
  and i.chave_evento='in:'||f.id_externo_sintetico
  and c.modo='simulado' and l.ativo
 for update of t;
 if not found then
  raise exception 'INVALID_C02_APPLY_SCOPE' using errcode='42501';end if;
 select * into v_old from prumo_private.aplicacoes_c02_inbox_s0
 where concessionaria_id=p_loja and inbox_id=p_inbox;
 if found then
  if v_job.estado='APPLIED' and v_old.canal_id=p_canal
   and v_old.worker_fixture=p_worker and v_old.versao_reserva=p_versao
  then return pg_catalog.jsonb_build_object('outcome','ALREADY_APPLIED',
   'mensagem_id',v_old.mensagem_id);end if;
  raise exception 'STALE_OR_DIFFERENT_APPLY' using errcode='40001';
 end if;
 if v_job.estado<>'LEASED' or v_job.versao<>p_versao
  or v_job.lease_worker is distinct from p_worker
  or v_job.lease_ate<=pg_catalog.clock_timestamp()
 then raise exception 'STALE_OR_EXPIRED_LEASE' using errcode='40001';end if;

 v_c02:=prumo_private.receber_mensagem_identidade_s0(
  p_canal,v_job.telefone_sintetico,v_job.id_externo_sintetico,
  v_job.texto_sintetico,v_job.mobile_confirmado_fixture);
 -- Preserve the identity pendency AND quarantine in the same commit:
 -- these are not uncertain external sends and do not create C02 messages.
 if v_c02->>'outcome' in ('IDENTITY_CONFLICT','NEEDS_REVIEW') then
  v_settle:=prumo_private.registrar_resultado_ingresso_s0(
   p_loja,p_canal,p_inbox,p_worker,p_versao,v_c02->>'outcome');
  if v_settle->>'outcome'<>'RECORDED' or v_settle->>'estado'<>'QUARANTINED'
  then raise exception 'C02_REVIEW_SETTLEMENT_FAILED' using errcode='40001';end if;
  return pg_catalog.jsonb_build_object('outcome','QUARANTINED_IDENTITY',
    'motivo',v_c02->>'outcome','tarefa_versao',v_settle->>'versao');
 end if;
 if v_c02->>'outcome' not in ('APPLIED','ALREADY_APPLIED')
   or v_c02->>'mensagem_id' is null
 then raise exception 'INVALID_C02_RESULT' using errcode='22023';end if;
 v_msg:=(v_c02->>'mensagem_id')::uuid;
 -- Commit the proof first; the settlement function and independent
 -- task trigger both demand its presence before APPLIED.
 insert into prumo_private.aplicacoes_c02_inbox_s0(
  concessionaria_id,canal_id,inbox_id,mensagem_id,worker_fixture,
  versao_reserva,resultado_c02)
 values(p_loja,p_canal,p_inbox,v_msg,p_worker,p_versao,v_c02->>'outcome');
 v_settle:=prumo_private.registrar_resultado_ingresso_s0(
  p_loja,p_canal,p_inbox,p_worker,p_versao,'APLICADO_SINTETICO');
 if v_settle->>'outcome'<>'RECORDED' or v_settle->>'estado'<>'APPLIED'
 then raise exception 'C02_SETTLEMENT_REJECTED' using errcode='40001';end if;
 return pg_catalog.jsonb_build_object(
  'outcome','APPLIED_ATOMIC','mensagem_id',v_msg,
  'c02_outcome',v_c02->>'outcome','tarefa_versao',v_settle->>'versao',
  'roteamento',v_c02->>'roteamento');
end $fn$;

revoke all on function prumo_private.validar_prova_c02_s0(),
 prumo_private.validar_applied_com_prova_s0(),
 prumo_private.registrar_resultado_ingresso_s0(uuid,uuid,uuid,uuid,bigint,text),
 prumo_private.aplicar_inbox_c02_s0(uuid,uuid,uuid,uuid,bigint)
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
