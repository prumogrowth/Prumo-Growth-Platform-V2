-- S2 foundation / simulated C05+C08. No real sender, no Meta, no actual templates.
-- Technical scheduling states MUST NOT be commercial status.
create table public.catalogo_templates_sinteticos (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null references public.concessionarias(id) on delete restrict,
 codigo text not null check(length(btrim(codigo))>0),
 versao integer not null check(versao>0),
 aprovado_simulacao boolean not null default false,
 criado_em timestamptz not null default now(),
 unique(concessionaria_id,id),
 unique(concessionaria_id,codigo,versao)
);
create table public.planos_recontato_sinteticos (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 lead_id uuid not null,
 ciclo_id uuid not null,
 canal_id uuid not null,
 chave_idempotencia text not null check(length(btrim(chave_idempotencia))>0),
 fingerprint text not null,
 estado text not null default 'ativo' check(estado in ('ativo','cancelado')),
 versao bigint not null default 1 check(versao>0),
 motivo_cancelamento text,
 criado_em timestamptz not null default now(),
 cancelado_em timestamptz,
 unique(concessionaria_id,id),
 unique(concessionaria_id,chave_idempotencia),
 foreign key(concessionaria_id,ciclo_id,lead_id)
  references public.ciclos_comerciais(concessionaria_id,id,lead_id) on delete restrict,
 foreign key(concessionaria_id,canal_id)
  references public.canais_loja(concessionaria_id,id) on delete restrict,
 check((estado='ativo' and motivo_cancelamento is null and cancelado_em is null)
    or (estado='cancelado' and motivo_cancelamento is not null and cancelado_em is not null))
);
create unique index so_um_plano_ativo_por_ciclo
 on public.planos_recontato_sinteticos(concessionaria_id,ciclo_id) where estado='ativo';
create index planos_ativos_por_lead
 on public.planos_recontato_sinteticos(concessionaria_id,lead_id,estado);
create table public.envios_template_sinteticos (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 plano_id uuid not null,
 template_id uuid not null,
 ordem integer not null check(ordem between 1 and 5),
 agendado_em timestamptz not null,
 estado text not null default 'programado'
    check(estado in ('programado','reservado','cancelado')),
 chave_idempotencia text not null,
 reservado_em timestamptz,
 cancelado_em timestamptz,
 criado_em timestamptz not null default now(),
 unique(concessionaria_id,id),
 unique(concessionaria_id,plano_id,ordem),
 unique(concessionaria_id,chave_idempotencia),
 foreign key(concessionaria_id,plano_id)
   references public.planos_recontato_sinteticos(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,template_id)
   references public.catalogo_templates_sinteticos(concessionaria_id,id) on delete restrict,
 check((estado='programado' and reservado_em is null and cancelado_em is null)
    or (estado='reservado' and reservado_em is not null and cancelado_em is null)
    or (estado='cancelado' and cancelado_em is not null))
);
create index fila_envios_simulados
 on public.envios_template_sinteticos(concessionaria_id,agendado_em)
 where estado='programado';
create table public.eventos_envio_template_sinteticos (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 envio_id uuid not null,
 estado_anterior text not null,
 estado_posterior text not null,
 motivo text not null,
 criado_em timestamptz not null default now(),
 foreign key(concessionaria_id,envio_id)
   references public.envios_template_sinteticos(concessionaria_id,id) on delete restrict
);
create index eventos_envio_simulados_idx
 on public.eventos_envio_template_sinteticos(concessionaria_id,envio_id,criado_em);
alter table public.catalogo_templates_sinteticos enable row level security;
alter table public.planos_recontato_sinteticos enable row level security;
alter table public.envios_template_sinteticos enable row level security;
alter table public.eventos_envio_template_sinteticos enable row level security;
revoke all on public.catalogo_templates_sinteticos,public.planos_recontato_sinteticos,
 public.envios_template_sinteticos,public.eventos_envio_template_sinteticos
 from public,anon,authenticated;
grant select on public.catalogo_templates_sinteticos,public.planos_recontato_sinteticos,
 public.envios_template_sinteticos,public.eventos_envio_template_sinteticos to authenticated;
-- Technical D2 metadata only for active store managers; no operator global view.
create policy templates_read_gestor on public.catalogo_templates_sinteticos for select to authenticated
 using(exists(select 1 from public.vinculos_papel_escopo v
 where v.ator_id=(select auth.uid()) and v.concessionaria_id=catalogo_templates_sinteticos.concessionaria_id
 and v.papel='gestor' and v.valido_desde<=statement_timestamp()
 and (v.valido_ate is null or v.valido_ate>statement_timestamp())));
create policy planos_read_gestor on public.planos_recontato_sinteticos for select to authenticated
 using(exists(select 1 from public.vinculos_papel_escopo v
 where v.ator_id=(select auth.uid()) and v.concessionaria_id=planos_recontato_sinteticos.concessionaria_id
 and v.papel='gestor' and v.valido_desde<=statement_timestamp()
 and (v.valido_ate is null or v.valido_ate>statement_timestamp())));
create policy envios_read_gestor on public.envios_template_sinteticos for select to authenticated
 using(exists(select 1 from public.vinculos_papel_escopo v
 where v.ator_id=(select auth.uid()) and v.concessionaria_id=envios_template_sinteticos.concessionaria_id
 and v.papel='gestor' and v.valido_desde<=statement_timestamp()
 and (v.valido_ate is null or v.valido_ate>statement_timestamp())));
create policy eventos_envio_read_gestor on public.eventos_envio_template_sinteticos for select to authenticated
 using(exists(select 1 from public.vinculos_papel_escopo v
 where v.ator_id=(select auth.uid()) and v.concessionaria_id=eventos_envio_template_sinteticos.concessionaria_id
 and v.papel='gestor' and v.valido_desde<=statement_timestamp()
 and (v.valido_ate is null or v.valido_ate>statement_timestamp())));

-- C08 internal cancellation: serialize on lead; never claim external dispatch cancellation.
create function prumo_private.cancelar_recontatos_sinteticos(
 p_loja uuid,p_lead uuid,p_motivo text
) returns jsonb language plpgsql security invoker set search_path=''
as $$
declare v_plan record; v_env record; v_cancelados integer:=0; v_planos integer:=0;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501'; end if;
 if p_motivo not in ('resposta_cliente','handoff','opt_out_simulado','desfecho','cancelamento_gestor')
 then raise exception 'INVALID_CANCEL_REASON' using errcode='22023'; end if;
 -- Lock order: lead -> plan -> attempt, identical in create/reserve/C02 flows.
 perform 1 from public.leads_loja l where l.concessionaria_id=p_loja and l.id=p_lead for update;
 if not found then raise exception 'UNKNOWN_LEAD_SCOPE' using errcode='42501'; end if;
 for v_plan in
  select p.id from public.planos_recontato_sinteticos p
  where p.concessionaria_id=p_loja and p.lead_id=p_lead and p.estado='ativo'
  order by p.id for update
 loop
  for v_env in
    select e.id,e.estado from public.envios_template_sinteticos e
    where e.concessionaria_id=p_loja and e.plano_id=v_plan.id
      and e.estado in ('programado','reservado')
    order by e.id for update
  loop
   update public.envios_template_sinteticos
     set estado='cancelado',cancelado_em=statement_timestamp()
   where concessionaria_id=p_loja and id=v_env.id;
   insert into public.eventos_envio_template_sinteticos(
     concessionaria_id,envio_id,estado_anterior,estado_posterior,motivo)
   values(p_loja,v_env.id,v_env.estado,'cancelado',p_motivo);
   v_cancelados:=v_cancelados+1;
  end loop;
  update public.planos_recontato_sinteticos
     set estado='cancelado',versao=versao+1,motivo_cancelamento=p_motivo,
         cancelado_em=statement_timestamp()
   where concessionaria_id=p_loja and id=v_plan.id;
  v_planos:=v_planos+1;
 end loop;
 return jsonb_build_object('outcome','APPLIED','planos_cancelados',v_planos,
   'envios_cancelados',v_cancelados,'transmissao_externa','DESABILITADA');
end $$;

-- C05 simulated planner. No AI, no text generation, no permission to send.
create function prumo_private.agendar_recontatos_sinteticos(
 p_ator uuid,p_loja uuid,p_ciclo uuid,p_canal uuid,p_chave text,p_tentativas jsonb
) returns jsonb language plpgsql security invoker set search_path=''
as $$
declare v_lead uuid; v_status text; v_plano uuid; v_hash text; v_prev text;
 v_ordem int:=0; v_tentativa jsonb; v_template uuid; v_hora timestamptz;
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
 v_hash:=encode(sha256(convert_to(p_tentativas::text,'UTF8')),'hex');
 select id,fingerprint into v_plano,v_prev from public.planos_recontato_sinteticos
  where concessionaria_id=p_loja and chave_idempotencia=p_chave;
 if found then
  if v_prev is distinct from v_hash then
   raise exception 'CONFLICT_IDEMPOTENCY_KEY' using errcode='23505'; end if;
  return jsonb_build_object('outcome','ALREADY_APPLIED','plano_id',v_plano); end if;
 select status_comercial into v_status from public.ciclos_comerciais
  where concessionaria_id=p_loja and id=p_ciclo for update;
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
  if v_hora <= statement_timestamp() or not exists(
   select 1 from public.catalogo_templates_sinteticos t
   where t.id=v_template and t.concessionaria_id=p_loja and t.aprovado_simulacao)
  then raise exception 'UNAPPROVED_OR_PAST_TEMPLATE' using errcode='22023'; end if;
  insert into public.envios_template_sinteticos(
    concessionaria_id,plano_id,template_id,ordem,agendado_em,chave_idempotencia)
  values(p_loja,v_plano,v_template,v_ordem,v_hora,p_chave||':'||v_ordem);
 end loop;
 return jsonb_build_object('outcome','APPLIED','plano_id',v_plano,'envios',v_ordem,
   'transmissao_externa','DESABILITADA');
end $$;

-- Dry-run reservation only: never transmits, never records 'sent/delivered'.
create function prumo_private.reservar_envio_sintetico(
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
 if not found or v_state<>'programado'
 or v_hora>p_referencia or v_status not in
 ('aguardando primeiro disparo','primeiro disparo enviado','em atendimento pela IA')
 or exists(select 1 from public.casos_humanos h
    join public.planos_recontato_sinteticos p on p.ciclo_id=h.ciclo_id
    and p.concessionaria_id=h.concessionaria_id
    where p.concessionaria_id=p_loja and p.id=v_plan)
 then return jsonb_build_object('outcome','NOT_ELIGIBLE','transmissao_externa','DESABILITADA'); end if;
 update public.envios_template_sinteticos
 set estado='reservado',reservado_em=statement_timestamp()
 where concessionaria_id=p_loja and id=p_envio;
 insert into public.eventos_envio_template_sinteticos(
 concessionaria_id,envio_id,estado_anterior,estado_posterior,motivo)
 values(p_loja,p_envio,'programado','reservado','ensaio_reserva');
 return jsonb_build_object('outcome','RESERVED_SIMULATED','transmissao_externa','DESABILITADA');
end $$;

revoke all on all functions in schema prumo_private from public,anon,authenticated,service_role;
