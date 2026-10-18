-- S0/032: synthetic inbox lease lifecycle, versioned settlement and safety gates.
-- No C02/C07 executor, provider ACK, Meta sender, or operational worker principal.
-- SECURITY INVOKER with current_user=postgres, same boundary as S0/029.
alter table prumo_private.tarefas_ingresso_s0
 add column proxima_tentativa_em timestamptz,
 add column motivo_terminal_s0 text
   check (motivo_terminal_s0 is null or motivo_terminal_s0 in
    ('FALHA_RETRY_SEGURA','FALHA_DEFINITIVA','RESULTADO_INCERTO',
     'LEASE_EXPIRADO_INCERTO','SEM_EFEITO_FIXTURE')),
 add column concluido_em timestamptz,
 add constraint tarefa_s0_retry_clock_chk check (
  (estado='RETRY_PENDING' and proxima_tentativa_em is not null)
  or (estado<>'RETRY_PENDING' and proxima_tentativa_em is null));

-- Existing task schema had inbox_id PK; composite FK requires a unique key.
alter table prumo_private.tarefas_ingresso_s0
 add constraint tarefas_s0_loja_inbox_uniq unique(concessionaria_id,inbox_id);

create table prumo_private.historico_tarefas_ingresso_s0(
 id bigint generated always as identity primary key,
 concessionaria_id uuid not null,
 inbox_id uuid not null,
 versao_antes bigint not null check(versao_antes>=1),
 versao_depois bigint not null check(versao_depois=versao_antes+1),
 estado_antes text not null,
 estado_depois text not null,
 acao text not null check(acao in (
  'RESERVA','APLICADO_SINTETICO','FALHA_RETRY_SEGURA','FALHA_DEFINITIVA',
  'RESULTADO_INCERTO','EXPIRADO_QUARENTENA','EXPIRADO_SEM_EFEITO_FIXTURE',
  'EXPIRADO_DEFINITIVO')),
 ator_fixture uuid not null,
 registrado_em timestamptz not null default pg_catalog.clock_timestamp(),
 unique(concessionaria_id,inbox_id,versao_depois),
 foreign key(concessionaria_id,inbox_id)
  references prumo_private.tarefas_ingresso_s0(concessionaria_id,inbox_id)
);
alter table prumo_private.historico_tarefas_ingresso_s0 enable row level security;
revoke all on prumo_private.historico_tarefas_ingresso_s0
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
create function prumo_private.rejeitar_mutacao_historico_ingresso_s0()
returns trigger language plpgsql security invoker set search_path='' as $fn$
begin
 raise exception 'IMMUTABLE_INGRESS_AUDIT' using errcode='42501';
end $fn$;
create trigger historico_ingresso_sem_update_delete_s0
 before update or delete on prumo_private.historico_tarefas_ingresso_s0
 for each row execute function prumo_private.rejeitar_mutacao_historico_ingresso_s0();

-- Replace S0/029 reservation with fail-closed lease expiry handling.
-- Expired LEASED jobs are NEVER auto-reclaimed; manual fixture recovery
-- requires an explicit version and separately confirmed no-effect assertion.
create or replace function prumo_private.reservar_ingresso_s0(
 p_loja uuid,p_canal uuid,p_worker uuid
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_t record;v_ate timestamptz;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_loja is null or p_canal is null or p_worker is null or not exists(
 select 1 from public.canais_loja c join public.concessionarias l
 on l.id=c.concessionaria_id and l.ativo
 where c.id=p_canal and c.concessionaria_id=p_loja and c.modo='simulado')
 then raise exception 'INVALID_WORKER_SCOPE' using errcode='42501';end if;
 select t.inbox_id,t.versao,t.estado into v_t
 from prumo_private.tarefas_ingresso_s0 t
 join prumo_private.inbox_eventos_s0 i
  on i.id=t.inbox_id and i.concessionaria_id=t.concessionaria_id
 where t.concessionaria_id=p_loja and i.canal_id=p_canal
 and t.tentativas<3
 and (t.estado='READY'
  or (t.estado='RETRY_PENDING' and t.proxima_tentativa_em<=pg_catalog.clock_timestamp()))
 order by t.criado_em,t.inbox_id
 limit 1 for update of t skip locked;
 if not found then return pg_catalog.jsonb_build_object('outcome','EMPTY');end if;
 v_ate:=pg_catalog.clock_timestamp()+interval '30 seconds';
 update prumo_private.tarefas_ingresso_s0
 set estado='LEASED',lease_worker=p_worker,lease_ate=v_ate,
   proxima_tentativa_em=null,motivo_terminal_s0=null,
   versao=v_t.versao+1,tentativas=tentativas+1
 where inbox_id=v_t.inbox_id and concessionaria_id=p_loja;
 insert into prumo_private.historico_tarefas_ingresso_s0(
  concessionaria_id,inbox_id,versao_antes,versao_depois,
  estado_antes,estado_depois,acao,ator_fixture)
 values(p_loja,v_t.inbox_id,v_t.versao,v_t.versao+1,
   v_t.estado,'LEASED','RESERVA',p_worker);
 return pg_catalog.jsonb_build_object('outcome','LEASED',
  'inbox_id',v_t.inbox_id,'versao',v_t.versao+1,'tentativas',
  (select tentativas from prumo_private.tarefas_ingresso_s0
   where inbox_id=v_t.inbox_id),'lease_ate',v_ate);
end $fn$;

-- A result is ONLY a synthetic worker assertion. It does not apply the
-- commercial event or assert an external side effect.
create function prumo_private.registrar_resultado_ingresso_s0(
 p_loja uuid,p_canal uuid,p_inbox uuid,p_worker uuid,
 p_versao bigint,p_resultado text
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_t record;v_estado text;v_proxima timestamptz;v_motivo text;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_loja is null or p_canal is null or p_inbox is null or p_worker is null
 or p_versao is null or p_versao<2 or p_resultado is null
 or p_resultado not in ('APLICADO_SINTETICO','FALHA_RETRY_SEGURA',
   'FALHA_DEFINITIVA','RESULTADO_INCERTO')
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
 v_proxima:=null;
 v_motivo:=case when p_resultado='APLICADO_SINTETICO' then null
   else p_resultado end;
 v_estado:=case p_resultado
  when 'APLICADO_SINTETICO' then 'APPLIED'
  when 'RESULTADO_INCERTO' then 'QUARANTINED'
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

-- Explicit recovery for an expired lease only, performed as a controlled SQL
-- fixture. Does not confer real human authority based on p_revisor_fixture.
create function prumo_private.reconciliar_lease_expirado_s0(
 p_loja uuid,p_canal uuid,p_inbox uuid,p_versao bigint,
 p_revisor_fixture uuid,p_decisao text
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_t record;v_estado text;v_proxima timestamptz;v_acao text;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_loja is null or p_canal is null or p_inbox is null
 or p_versao is null or p_revisor_fixture is null
 or p_decisao is null or p_decisao not in (
  'QUARENTENA','SEM_EFEITO_FIXTURE','FALHA_DEFINITIVA')
 then raise exception 'INVALID_RECOVERY_ARGUMENT' using errcode='22023';end if;
 select t.* into v_t from prumo_private.tarefas_ingresso_s0 t
 join prumo_private.inbox_eventos_s0 i
  on i.concessionaria_id=t.concessionaria_id and i.id=t.inbox_id
 join public.canais_loja c
  on c.id=i.canal_id and c.concessionaria_id=i.concessionaria_id
 where t.concessionaria_id=p_loja and t.inbox_id=p_inbox
  and i.canal_id=p_canal and c.modo='simulado'
 for update of t;
 if not found then raise exception 'INVALID_WORKER_SCOPE' using errcode='42501';end if;
 if v_t.estado<>'LEASED' or v_t.versao<>p_versao
 or v_t.lease_ate>pg_catalog.clock_timestamp()
 then raise exception 'RECOVERY_VERSION_OR_LEASE_INVALID' using errcode='40001';end if;
 v_estado:=case p_decisao
  when 'QUARENTENA' then 'QUARANTINED'
  when 'FALHA_DEFINITIVA' then 'DEAD_LETTER'
  when 'SEM_EFEITO_FIXTURE' then
   case when v_t.tentativas>=3 then 'DEAD_LETTER' else 'RETRY_PENDING' end end;
 v_acao:=case p_decisao
  when 'QUARENTENA' then 'EXPIRADO_QUARENTENA'
  when 'FALHA_DEFINITIVA' then 'EXPIRADO_DEFINITIVO'
  when 'SEM_EFEITO_FIXTURE' then 'EXPIRADO_SEM_EFEITO_FIXTURE' end;
 v_proxima:=case when v_estado='RETRY_PENDING'
   then pg_catalog.clock_timestamp()+interval '15 seconds' else null end;
 update prumo_private.tarefas_ingresso_s0
 set estado=v_estado,versao=v_t.versao+1,lease_worker=null,
   lease_ate=null,proxima_tentativa_em=v_proxima,
   motivo_terminal_s0=case p_decisao
    when 'QUARENTENA' then 'LEASE_EXPIRADO_INCERTO'
    when 'SEM_EFEITO_FIXTURE' then 'SEM_EFEITO_FIXTURE'
    else 'FALHA_DEFINITIVA' end,
   concluido_em=case when v_estado='RETRY_PENDING'
    then null else pg_catalog.clock_timestamp() end
 where concessionaria_id=p_loja and inbox_id=p_inbox;
 insert into prumo_private.historico_tarefas_ingresso_s0(
  concessionaria_id,inbox_id,versao_antes,versao_depois,
  estado_antes,estado_depois,acao,ator_fixture)
 values(p_loja,p_inbox,v_t.versao,v_t.versao+1,
  'LEASED',v_estado,v_acao,p_revisor_fixture);
 return pg_catalog.jsonb_build_object('outcome','RECONCILED',
  'estado',v_estado,'versao',v_t.versao+1);
end $fn$;

revoke all on function prumo_private.rejeitar_mutacao_historico_ingresso_s0(),
 prumo_private.reservar_ingresso_s0(uuid,uuid,uuid),
 prumo_private.registrar_resultado_ingresso_s0(uuid,uuid,uuid,uuid,bigint,text),
 prumo_private.reconciliar_lease_expirado_s0(uuid,uuid,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
