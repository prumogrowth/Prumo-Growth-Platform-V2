-- C04 candidato: evidência SIMULADA de elegibilidade por loja + emissor + finalidade.
-- Importação e inbound NÃO criam comprovação nem restauram opt-in.
-- Política entre concessionárias, bases jurídicas e exigências Meta continuam [R/V].
create table public.evidencias_elegibilidade_sinteticas (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 lead_id uuid not null,
 canal_id uuid not null,
 finalidade text not null check(finalidade='recontato_comercial_sintetico'),
 estado text not null default 'verificada_simulada'
   check(estado in ('verificada_simulada','revogada')),
 referencia_ficticia text not null check(length(btrim(referencia_ficticia)) between 5 and 120),
 criado_em timestamptz not null default now(),
 unique(concessionaria_id,lead_id,canal_id,finalidade),
 foreign key(concessionaria_id,lead_id)
   references public.leads_loja(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,canal_id)
   references public.canais_loja(concessionaria_id,id) on delete restrict
);
create table public.supressoes_contato_sinteticas (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 lead_id uuid not null,
 canal_id uuid not null,
 finalidade text not null check(finalidade='recontato_comercial_sintetico'),
 evento_origem text not null check(length(btrim(evento_origem)) between 1 and 120),
 criado_em timestamptz not null default now(),
 unique(concessionaria_id,canal_id,evento_origem),
 foreign key(concessionaria_id,lead_id)
   references public.leads_loja(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,canal_id)
   references public.canais_loja(concessionaria_id,id) on delete restrict
);
create index supressoes_contato_lookup on public.supressoes_contato_sinteticas(
 concessionaria_id,lead_id,canal_id,finalidade);
alter table public.planos_recontato_sinteticos
 add column finalidade text not null default 'recontato_comercial_sintetico'
 check(finalidade='recontato_comercial_sintetico');
alter table public.evidencias_elegibilidade_sinteticas enable row level security;
alter table public.supressoes_contato_sinteticas enable row level security;
revoke all on public.evidencias_elegibilidade_sinteticas,
 public.supressoes_contato_sinteticas from public,anon,authenticated;
grant select on public.evidencias_elegibilidade_sinteticas,
 public.supressoes_contato_sinteticas to authenticated;
create policy elegibilidade_select_gestor on public.evidencias_elegibilidade_sinteticas
 for select to authenticated using(exists(
  select 1 from public.vinculos_papel_escopo v
  where v.ator_id=(select auth.uid())
  and v.concessionaria_id=evidencias_elegibilidade_sinteticas.concessionaria_id
  and v.papel='gestor' and v.valido_desde<=statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>statement_timestamp())
 ));
create policy supressoes_select_gestor on public.supressoes_contato_sinteticas
 for select to authenticated using(exists(
  select 1 from public.vinculos_papel_escopo v
  where v.ator_id=(select auth.uid())
  and v.concessionaria_id=supressoes_contato_sinteticas.concessionaria_id
  and v.papel='gestor' and v.valido_desde<=statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>statement_timestamp())
 ));
-- Only fictional evidence enables fictional reservations. No real outbound authorization.
create or replace function prumo_private.agendar_recontatos_sinteticos(
 p_ator uuid,p_loja uuid,p_ciclo uuid,p_canal uuid,p_chave text,p_tentativas jsonb
) returns jsonb language plpgsql security invoker set search_path=''
as $$
declare v_lead uuid; v_status text; v_plano uuid; v_hash text; v_prev text;
 v_ordem int:=0; v_tentativa jsonb; v_template uuid; v_hora timestamptz; v_prev_hora timestamptz;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501'; end if;
 if p_chave is null or length(btrim(p_chave)) not between 1 and 160
 or jsonb_typeof(p_tentativas) is distinct from 'array'
 or jsonb_array_length(p_tentativas) not between 1 and 5
 then raise exception 'INVALID_PLAN' using errcode='22023'; end if;
 if not exists(select 1 from public.vinculos_papel_escopo v
  where v.ator_id=p_ator and v.concessionaria_id=p_loja and v.papel='gestor'
  and v.valido_desde<=statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>statement_timestamp()))
 then raise exception 'FORBIDDEN_SCOPE' using errcode='42501'; end if;
 select c.lead_id into v_lead from public.ciclos_comerciais c
  where c.id=p_ciclo and c.concessionaria_id=p_loja;
 if v_lead is null then raise exception 'UNKNOWN_CYCLE_SCOPE' using errcode='42501'; end if;
 perform 1 from public.leads_loja
  where concessionaria_id=p_loja and id=v_lead for update;
 v_hash:=encode(sha256(convert_to(jsonb_build_object('ciclo_id',p_ciclo,'canal_id',p_canal,'tentativas',p_tentativas)::text,'UTF8')),'hex');
 select id,fingerprint into v_plano,v_prev from public.planos_recontato_sinteticos
  where concessionaria_id=p_loja and chave_idempotencia=p_chave;
 if found then
  if v_prev is distinct from v_hash then
   raise exception 'CONFLICT_IDEMPOTENCY_KEY' using errcode='23505'; end if;
  return jsonb_build_object('outcome','ALREADY_APPLIED','plano_id',v_plano); end if;
 select status_comercial into v_status from public.ciclos_comerciais
  where concessionaria_id=p_loja and id=p_ciclo for update;
 if not exists(
  select 1 from public.evidencias_elegibilidade_sinteticas ev
  where ev.concessionaria_id=p_loja and ev.lead_id=v_lead
    and ev.canal_id=p_canal and ev.finalidade='recontato_comercial_sintetico'
    and ev.estado='verificada_simulada'
 ) or exists(
  select 1 from public.supressoes_contato_sinteticas sp
  where sp.concessionaria_id=p_loja and sp.lead_id=v_lead
    and sp.canal_id=p_canal and sp.finalidade='recontato_comercial_sintetico'
 )
 then raise exception 'ELIGIBILITY_NOT_DEMONSTRATED' using errcode='22023'; end if;
 if v_status not in ('aguardando primeiro disparo','primeiro disparo enviado','em atendimento pela IA')
  or exists(select 1 from public.casos_humanos h where h.concessionaria_id=p_loja and h.ciclo_id=p_ciclo)
  or exists(select 1 from public.planos_recontato_sinteticos p
    where p.concessionaria_id=p_loja and p.ciclo_id=p_ciclo and p.estado='ativo')
  or not exists(select 1 from public.canais_loja ch
    where ch.concessionaria_id=p_loja and ch.id=p_canal and ch.modo='simulado')
 then raise exception 'NOT_ELIGIBLE_SIMULATION' using errcode='22023'; end if;
 -- Synthetic-only: no real consent, Meta approval, timezone or opt-out proof asserted.
 insert into public.planos_recontato_sinteticos(
 concessionaria_id,lead_id,ciclo_id,canal_id,chave_idempotencia,fingerprint)
 values(p_loja,v_lead,p_ciclo,p_canal,p_chave,v_hash) returning id into v_plano;
 for v_tentativa in select value from jsonb_array_elements(p_tentativas) loop
  v_ordem:=v_ordem+1;
  if jsonb_typeof(v_tentativa) is distinct from 'object'
     or jsonb_typeof(v_tentativa->'template_id') is distinct from 'string'
     or jsonb_typeof(v_tentativa->'agendado_em') is distinct from 'string'
  then raise exception 'INVALID_PLAN_ITEM' using errcode='22023'; end if;
  begin
   v_template:=(v_tentativa->>'template_id')::uuid;
   v_hora:=(v_tentativa->>'agendado_em')::timestamptz;
  exception when others then raise exception 'INVALID_PLAN_ITEM' using errcode='22023'; end;
  if v_hora <= statement_timestamp() or (v_prev_hora is not null and v_hora <= v_prev_hora) or not exists(
   select 1 from public.catalogo_templates_sinteticos t
   where t.id=v_template and t.concessionaria_id=p_loja and t.aprovado_simulacao)
  then raise exception 'UNAPPROVED_OR_PAST_TEMPLATE' using errcode='22023'; end if;
  insert into public.envios_template_sinteticos(
    concessionaria_id,plano_id,template_id,ordem,agendado_em,chave_idempotencia)
  values(p_loja,v_plano,v_template,v_ordem,v_hora,p_chave||':'||v_ordem);
  v_prev_hora:=v_hora;
 end loop;
 return jsonb_build_object('outcome','APPLIED','plano_id',v_plano,'envios',v_ordem,
   'transmissao_externa','DESABILITADA');
end $$;

create or replace function prumo_private.reservar_envio_sintetico(
 p_loja uuid,p_envio uuid,p_referencia timestamptz
) returns jsonb language plpgsql security invoker set search_path=''
as $$
declare v_lead uuid; v_plan uuid; v_state text; v_status text; v_hora timestamptz;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501'; end if;
 select p.lead_id,p.id into v_lead,v_plan
 from public.envios_template_sinteticos e join public.planos_recontato_sinteticos p
 on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 where e.concessionaria_id=p_loja and e.id=p_envio;
 if v_lead is null then raise exception 'UNKNOWN_SEND_SCOPE' using errcode='42501'; end if;
 perform 1 from public.leads_loja
 where concessionaria_id=p_loja and id=v_lead for update;
 perform 1 from public.planos_recontato_sinteticos
 where concessionaria_id=p_loja and id=v_plan for update;
 select e.estado,e.agendado_em,c.status_comercial into v_state,v_hora,v_status
 from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 join public.ciclos_comerciais c on c.id=p.ciclo_id and c.concessionaria_id=p.concessionaria_id
 where e.concessionaria_id=p_loja and e.id=p_envio
 and p.estado='ativo' for update of e;
 if not exists(
  select 1 from public.planos_recontato_sinteticos p
  join public.evidencias_elegibilidade_sinteticas ev
    on ev.concessionaria_id=p.concessionaria_id
   and ev.lead_id=p.lead_id and ev.canal_id=p.canal_id and ev.finalidade=p.finalidade
  where p.id=v_plan and p.concessionaria_id=p_loja
    and ev.estado='verificada_simulada'
 ) or exists(
  select 1 from public.planos_recontato_sinteticos p
  join public.supressoes_contato_sinteticas sp
    on sp.concessionaria_id=p.concessionaria_id
   and sp.lead_id=p.lead_id and sp.canal_id=p.canal_id and sp.finalidade=p.finalidade
  where p.id=v_plan and p.concessionaria_id=p_loja
 ) then return jsonb_build_object('outcome','NOT_ELIGIBLE','reason','C04_BLOCKED',
   'transmissao_externa','DESABILITADA'); end if;
 if not found or v_state<>'programado'
 or v_hora>p_referencia or v_status not in
 ('aguardando primeiro disparo','primeiro disparo enviado','em atendimento pela IA')
 or exists(select 1 from public.casos_humanos h
    join public.planos_recontato_sinteticos p on p.ciclo_id=h.ciclo_id
    and p.concessionaria_id=h.concessionaria_id
    where p.concessionaria_id=p_loja and p.id=v_plan)
 or not exists (select 1 from public.envios_template_sinteticos e
    join public.catalogo_templates_sinteticos t
      on t.id=e.template_id and t.concessionaria_id=e.concessionaria_id
    join public.planos_recontato_sinteticos p
      on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
    join public.canais_loja ch
      on ch.id=p.canal_id and ch.concessionaria_id=p.concessionaria_id
    where e.concessionaria_id=p_loja and e.id=p_envio
      and t.aprovado_simulacao and ch.modo='simulado')
 then return jsonb_build_object('outcome','NOT_ELIGIBLE','transmissao_externa','DESABILITADA'); end if;
 update public.envios_template_sinteticos
 set estado='reservado',reservado_em=statement_timestamp()
 where concessionaria_id=p_loja and id=p_envio;
 insert into public.eventos_envio_template_sinteticos(
 concessionaria_id,envio_id,estado_anterior,estado_posterior,motivo)
 values(p_loja,p_envio,'programado','reservado','ensaio_reserva');
 return jsonb_build_object('outcome','RESERVED_SIMULATED','transmissao_externa','DESABILITADA');
end $$;

-- C04 tri-state; simulated evidence is NEVER proof for real Meta operations.
create function prumo_private.verificar_contato_sintetico(
 p_loja uuid,p_lead uuid,p_canal uuid,p_finalidade text
) returns jsonb language plpgsql security invoker set search_path=''
as $
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501'; end if;
 if p_finalidade is distinct from 'recontato_comercial_sintetico'
 or not exists(select 1 from public.leads_loja l
    where l.concessionaria_id=p_loja and l.id=p_lead)
 or not exists(select 1 from public.canais_loja c
    where c.concessionaria_id=p_loja and c.id=p_canal)
 then return jsonb_build_object('decisao','INDETERMINADO',
    'motivo','ESCOPO_OU_FINALIDADE_NAO_VERIFICADA','real','DEPENDENCY_UNVERIFIED'); end if;
 if exists(select 1 from public.supressoes_contato_sinteticas sp
    where sp.concessionaria_id=p_loja and sp.lead_id=p_lead
    and sp.canal_id=p_canal and sp.finalidade=p_finalidade)
 then return jsonb_build_object('decisao','INELEGIVEL','motivo','OPT_OUT',
   'real','DEPENDENCY_UNVERIFIED'); end if;
 if exists(select 1 from public.evidencias_elegibilidade_sinteticas e
    where e.concessionaria_id=p_loja and e.lead_id=p_lead
    and e.canal_id=p_canal and e.finalidade=p_finalidade
    and e.estado='verificada_simulada')
 then return jsonb_build_object('decisao','ELEGIVEL_SOMENTE_SIMULACAO',
   'motivo','EVIDENCIA_FICTICIA','real','DEPENDENCY_UNVERIFIED'); end if;
 return jsonb_build_object('decisao','INDETERMINADO',
    'motivo','SEM_EVIDENCIA','real','DEPENDENCY_UNVERIFIED');
end $;

-- Register a scoped synthetic opt-out. Never delete historical plans or messages.
-- Atomic with pending cancellation and concurrent reservation via lead lock.
create function prumo_private.registrar_optout_sintetico(
 p_loja uuid,p_lead uuid,p_canal uuid,p_finalidade text,p_evento text
) returns jsonb language plpgsql security invoker set search_path=''
as $$
declare v_old record; v_plan record; v_env record; v_count integer:=0;
 v_plans integer:=0;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501'; end if;
 if p_finalidade is distinct from 'recontato_comercial_sintetico'
  or p_evento is null or length(btrim(p_evento)) not between 1 and 120
 then raise exception 'INVALID_OPTOUT' using errcode='22023'; end if;
 perform 1 from public.leads_loja l
 where l.id=p_lead and l.concessionaria_id=p_loja for update;
 if not found then raise exception 'FORBIDDEN_SCOPE' using errcode='42501'; end if;
 if not exists(select 1 from public.canais_loja c
 where c.id=p_canal and c.concessionaria_id=p_loja)
 then raise exception 'FORBIDDEN_CHANNEL_SCOPE' using errcode='42501'; end if;
 select lead_id,finalidade into v_old from public.supressoes_contato_sinteticas
 where concessionaria_id=p_loja and canal_id=p_canal and evento_origem=p_evento;
 if found then
  if v_old.lead_id is distinct from p_lead
   or v_old.finalidade is distinct from p_finalidade
  then raise exception 'CONFLICT_IDEMPOTENCY_KEY' using errcode='23505'; end if;
  return jsonb_build_object('outcome','ALREADY_APPLIED',
    'transmissao_externa','DESABILITADA'); end if;
 insert into public.supressoes_contato_sinteticas(
 concessionaria_id,lead_id,canal_id,finalidade,evento_origem)
 values(p_loja,p_lead,p_canal,p_finalidade,p_evento);
 for v_plan in
  select id from public.planos_recontato_sinteticos
  where concessionaria_id=p_loja and lead_id=p_lead and canal_id=p_canal
   and finalidade=p_finalidade and estado='ativo'
  order by id for update
 loop
  for v_env in select id,estado from public.envios_template_sinteticos
    where concessionaria_id=p_loja and plano_id=v_plan.id
     and estado in ('programado','reservado') order by id for update
  loop
   update public.envios_template_sinteticos
     set estado='cancelado',cancelado_em=statement_timestamp()
     where concessionaria_id=p_loja and id=v_env.id;
   insert into public.eventos_envio_template_sinteticos(
     concessionaria_id,envio_id,estado_anterior,estado_posterior,motivo)
   values(p_loja,v_env.id,v_env.estado,'cancelado','opt_out_simulado');
   v_count:=v_count+1;
  end loop;
  update public.planos_recontato_sinteticos
   set estado='cancelado',cancelado_em=statement_timestamp(),
     motivo_cancelamento='opt_out_simulado',versao=versao+1
   where concessionaria_id=p_loja and id=v_plan.id;
  v_plans:=v_plans+1;
 end loop;
 return jsonb_build_object('outcome','APPLIED','planos_cancelados',v_plans,
   'envios_cancelados',v_count,'transmissao_externa','DESABILITADA');
end $$;

revoke all on all functions in schema prumo_private
 from public,anon,authenticated,service_role;
