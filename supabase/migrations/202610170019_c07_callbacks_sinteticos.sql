-- C07 INTERNAL SIMULATION ONLY. No Meta transport, signature or real proof.
-- Commercial state is NEVER changed by these technical callback observations.

alter table public.envios_template_sinteticos
 add column correlacao_externa_ficticia text
    check(correlacao_externa_ficticia ~ '^[A-Za-z0-9_.:-]{1,120}$'),
 add column callback_aceito_simulado boolean not null default false,
 add column callback_enviado_simulado boolean not null default false,
 add column callback_entregue_simulado boolean not null default false,
 add column callback_lido_simulado boolean not null default false,
 add column callback_falhou_simulado boolean not null default false,
 add column callback_incerto_simulado boolean not null default false;
create unique index envio_correlacao_ficticia_unique
 on public.envios_template_sinteticos(concessionaria_id,correlacao_externa_ficticia)
 where correlacao_externa_ficticia is not null;

create table public.eventos_callback_sinteticos (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 canal_id uuid not null,
 envio_id uuid,
 correlacao_externa_ficticia text not null
   check(correlacao_externa_ficticia ~ '^[A-Za-z0-9_.:-]{1,120}$'),
 evento_externo_ficticio text not null
   check(evento_externo_ficticio ~ '^[A-Za-z0-9_.:-]{1,120}$'),
 estado_reportado text not null check(estado_reportado in
 ('ACEITO_SIMULADO','ENVIADO_SIMULADO','ENTREGUE_SIMULADO',
  'LIDO_SIMULADO','FALHOU_SIMULADO','INCERTO_SIMULADO')),
 instante_evento timestamptz not null,
 recebido_em timestamptz not null default statement_timestamp(),
 fora_de_ordem boolean not null default false,
 resultado text not null check(resultado in ('CORRELACIONADO','PENDENTE_RECONCILIACAO')),
 fingerprint text not null,
 unique(concessionaria_id,id),
 unique(concessionaria_id,canal_id,evento_externo_ficticio),
 foreign key(concessionaria_id,canal_id)
    references public.canais_loja(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,envio_id)
    references public.envios_template_sinteticos(concessionaria_id,id) on delete restrict
);
create index eventos_callback_pendentes_sinteticos_idx
 on public.eventos_callback_sinteticos(concessionaria_id,recebido_em)
 where resultado='PENDENTE_RECONCILIACAO';
create index eventos_callback_envio_sinteticos_idx
 on public.eventos_callback_sinteticos(concessionaria_id,envio_id,recebido_em);
alter table public.eventos_callback_sinteticos enable row level security;
revoke all on public.eventos_callback_sinteticos from public,anon,authenticated,service_role;
grant select on public.eventos_callback_sinteticos to authenticated;
create policy callbacks_read_gestor_sintetico on public.eventos_callback_sinteticos
 for select to authenticated using(exists(
 select 1 from public.vinculos_papel_escopo v
 where v.ator_id=(select auth.uid()) and v.concessionaria_id=eventos_callback_sinteticos.concessionaria_id
 and v.papel='gestor' and v.valido_desde<=statement_timestamp()
 and (v.valido_ate is null or v.valido_ate>statement_timestamp())));

-- Bind a TEST-ONLY provider-like id to a previously reserved attempt.
-- Attaching is NOT a request, acceptance, send or delivery.
create function prumo_private.vincular_referencia_c07_sintetica(
 p_loja uuid,p_envio uuid,p_canal uuid,p_correlacao text
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_lead uuid;v_plano uuid;v_canal uuid;v_estado text;v_correlacao text;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_correlacao is null or p_correlacao !~ '^[A-Za-z0-9_.:-]{1,120}$'
 then raise exception 'INVALID_CORRELATION' using errcode='22023';end if;
 select p.lead_id,p.id,p.canal_id into v_lead,v_plano,v_canal
 from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p
 on p.concessionaria_id=e.concessionaria_id and p.id=e.plano_id
 where e.concessionaria_id=p_loja and e.id=p_envio;
 if v_lead is null or v_canal is distinct from p_canal
 then raise exception 'FORBIDDEN_SCOPE' using errcode='42501';end if;
 perform 1 from public.leads_loja where concessionaria_id=p_loja and id=v_lead for update;
 perform 1 from public.planos_recontato_sinteticos
 where concessionaria_id=p_loja and id=v_plano for update;
 select estado,correlacao_externa_ficticia into v_estado,v_correlacao
 from public.envios_template_sinteticos
 where concessionaria_id=p_loja and id=p_envio for update;
 if v_correlacao is not null then
  if v_correlacao=p_correlacao
  then return jsonb_build_object('outcome','ALREADY_APPLIED','transmissao_externa','DESABILITADA');end if;
  raise exception 'CONFLICT_IDEMPOTENCY_KEY' using errcode='23505';
 end if;
 if v_estado<>'reservado' or not exists(
  select 1 from public.planos_recontato_sinteticos
  where concessionaria_id=p_loja and id=v_plano and estado='ativo')
 then raise exception 'NOT_ELIGIBLE_SIMULATION' using errcode='22023';end if;
 update public.envios_template_sinteticos set correlacao_externa_ficticia=p_correlacao
 where concessionaria_id=p_loja and id=p_envio;
 return jsonb_build_object('outcome','APPLIED','transmissao_externa','DESABILITADA');
end $fn$;

-- Every technical observation is retained; out-of-order notifications never
-- downgrade flags or mutate technical reservation/commercial status.
-- Unmatched references stay pending for later authorized reconciliation.
create function prumo_private.registrar_callback_c07_sintetico(
 p_canal uuid,p_correlacao text,p_evento text,p_status text,p_instante timestamptz
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_loja uuid;v_evento record;v_fingerprint text;v_envio uuid;v_plano uuid;
 v_lead uuid;v_late boolean:=false;v_status_valido boolean;v_id uuid;v_resultado text;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_correlacao is null or p_correlacao !~ '^[A-Za-z0-9_.:-]{1,120}$'
 or p_evento is null or p_evento !~ '^[A-Za-z0-9_.:-]{1,120}$'
 or p_status is null or p_status not in
 ('ACEITO_SIMULADO','ENVIADO_SIMULADO','ENTREGUE_SIMULADO',
  'LIDO_SIMULADO','FALHOU_SIMULADO','INCERTO_SIMULADO')
 or p_instante is null
 then raise exception 'INVALID_CALLBACK_SYNTHETIC' using errcode='22023';end if;
 select c.concessionaria_id into v_loja from public.canais_loja c
 join public.concessionarias l on l.id=c.concessionaria_id
 where c.id=p_canal and c.modo='simulado' and l.ativo;
 if v_loja is null then raise exception 'UNKNOWN_CHANNEL' using errcode='22023';end if;
 v_fingerprint:=pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
  pg_catalog.jsonb_build_object('correlacao',p_correlacao,'status',p_status,
   'instante',p_instante)::text,'UTF8')),'hex');
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended(p_canal::text||':'||p_evento,1707));
 select id,correlacao_externa_ficticia,estado_reportado,instante_evento,fingerprint
  into v_evento from public.eventos_callback_sinteticos
 where concessionaria_id=v_loja and canal_id=p_canal and evento_externo_ficticio=p_evento;
 if found then
  if v_evento.fingerprint is distinct from v_fingerprint
  then raise exception 'CONFLICT_IDEMPOTENCY_KEY' using errcode='23505';end if;
  return jsonb_build_object('outcome','ALREADY_APPLIED','evento_id',v_evento.id,
     'transmissao_externa','DESABILITADA');end if;

 -- Lookup only within the callback's OWN channel and concessionaire.
 select e.id,p.id,p.lead_id into v_envio,v_plano,v_lead
 from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p
 on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 where e.concessionaria_id=v_loja and p.canal_id=p_canal
   and e.correlacao_externa_ficticia=p_correlacao;
 if v_envio is not null then
  perform 1 from public.leads_loja where concessionaria_id=v_loja and id=v_lead for update;
  perform 1 from public.planos_recontato_sinteticos
  where concessionaria_id=v_loja and id=v_plano for update;
  perform 1 from public.envios_template_sinteticos
  where concessionaria_id=v_loja and id=v_envio for update;
  select exists(
   select 1 from public.eventos_callback_sinteticos e
   where e.concessionaria_id=v_loja and e.envio_id=v_envio
    and e.instante_evento>p_instante
  ) into v_late;
  v_resultado:='CORRELACIONADO';
 else
  v_resultado:='PENDENTE_RECONCILIACAO';
 end if;
 insert into public.eventos_callback_sinteticos(
 concessionaria_id,canal_id,envio_id,correlacao_externa_ficticia,
 evento_externo_ficticio,estado_reportado,instante_evento,fora_de_ordem,
 resultado,fingerprint)
 values(v_loja,p_canal,v_envio,p_correlacao,p_evento,p_status,p_instante,
 v_late,v_resultado,v_fingerprint) returning id into v_id;
 if v_envio is not null then
  update public.envios_template_sinteticos set
   callback_aceito_simulado=callback_aceito_simulado or p_status='ACEITO_SIMULADO',
   callback_enviado_simulado=callback_enviado_simulado or p_status='ENVIADO_SIMULADO',
   callback_entregue_simulado=callback_entregue_simulado or p_status='ENTREGUE_SIMULADO',
   callback_lido_simulado=callback_lido_simulado or p_status='LIDO_SIMULADO',
   callback_falhou_simulado=callback_falhou_simulado or p_status='FALHOU_SIMULADO',
   callback_incerto_simulado=callback_incerto_simulado or p_status='INCERTO_SIMULADO'
  where concessionaria_id=v_loja and id=v_envio;
 end if;
 return jsonb_build_object('outcome',case when v_envio is null then 'PENDING_RECONCILIATION' else 'APPLIED' end,
  'evento_id',v_id,'envio_id',v_envio,'fora_de_ordem',v_late,
  'comprovacao_real','NENHUMA','transmissao_externa','DESABILITADA');
end $fn$;

revoke all on function prumo_private.vincular_referencia_c07_sintetica(uuid,uuid,uuid,text)
 from public,anon,authenticated,service_role;
revoke all on function prumo_private.registrar_callback_c07_sintetico(uuid,text,text,text,timestamptz)
 from public,anon,authenticated,service_role;
