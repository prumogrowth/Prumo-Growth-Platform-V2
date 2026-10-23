-- S0/S1-002 I52: canonical ingress gate at S0 human-assignment boundary.
-- This NEW migration is intentionally applied only to disposable PG17 CI until
-- integrated review. Historic S0 migrations 001-037 remain unchanged.
-- A2 [D]: no new case/lead may be assigned to a consultant with intake paused.
-- Paused actors retain pre-existing cases; the account is NOT suspended.

-- The legacy intake fixture and the new canonical guard change in ONE transaction.
begin;
create table prumo_private.s1_intake_estado (
 operador_id uuid primary key references public.equipe_prumo_s1(ator_id),
 pausado boolean not null default false,
 versao bigint not null default 1 check(versao>=1),
 atualizado_em timestamptz not null default pg_catalog.statement_timestamp()
);
create table prumo_private.s1_intake_eventos (
 id bigint generated always as identity primary key,
 solicitante_id uuid not null references public.atores(id),
 operador_id uuid not null references public.atores(id),
 versao_anterior bigint not null,
 versao_nova bigint not null,
 pausado boolean not null,
 ocorrido_em timestamptz not null default pg_catalog.statement_timestamp(),
 check(versao_nova=versao_anterior+1)
);
alter table prumo_private.s1_intake_estado enable row level security;
alter table prumo_private.s1_intake_eventos enable row level security;
revoke all on prumo_private.s1_intake_estado,prumo_private.s1_intake_eventos
 from public,anon,authenticated,service_role;
revoke all on sequence prumo_private.s1_intake_eventos_id_seq
 from public,anon,authenticated,service_role;

-- No self-service write. Only trusted gateway executor can call this
-- internal routine. Identity parameters MUST be derived from verified session.
-- The account row lock is the single serialization point with S0's
-- assignment BEFORE trigger; grants/team data remain a separate authority.
create function prumo_private.s1_definir_intake(
 p_gestor uuid,p_operador uuid,p_pausado boolean,p_versao_esperada bigint)
returns jsonb language plpgsql security invoker set search_path='' as $f$
declare v_versao bigint;v_pausado boolean;
begin
 if current_user<>'postgres' then
  raise exception 'INTAKE_EXECUTOR_INTERNO' using errcode='42501';end if;
 if p_gestor is null or p_operador is null or p_pausado is null
 or p_versao_esperada is null or p_versao_esperada<1
 or p_gestor=p_operador then
  raise exception 'INTAKE_PARAMETROS_INVALIDOS' using errcode='22023';end if;
 -- Serializes account status changes, intake writes and S0 assignments.
 perform 1 from public.equipe_prumo_s1 e
  where e.ator_id in (p_gestor,p_operador)
  order by e.ator_id for update of e;
 if (select count(*) from public.equipe_prumo_s1 e
  where e.ator_id in (p_gestor,p_operador) and e.estado='ativo')<>2 then
  raise exception 'INTAKE_EQUIPE_INATIVA' using errcode='42501';end if;
 perform 1 from prumo_private.s1_gestor_operadores g
 where g.gestor_id=p_gestor and g.operador_id=p_operador
 and g.encerrado_em is null for share of g;
 if not found then raise exception 'INTAKE_GESTOR_SEM_EQUIPE'
  using errcode='42501';end if;
 insert into prumo_private.s1_intake_estado(operador_id)
 values(p_operador) on conflict(operador_id) do nothing;
 select d.pausado,d.versao into v_pausado,v_versao
 from prumo_private.s1_intake_estado d
 where d.operador_id=p_operador for update;
 if v_versao<>p_versao_esperada then
  raise exception 'INTAKE_VERSAO_OBSOLETA' using errcode='22023';end if;
 if v_pausado=p_pausado then
  return pg_catalog.jsonb_build_object('outcome','ALREADY_APPLIED',
    'operator_id',p_operador,'intake_paused',v_pausado,'version',v_versao);
 end if;
 update prumo_private.s1_intake_estado
 set pausado=p_pausado,versao=v_versao+1,
 atualizado_em=pg_catalog.statement_timestamp()
 where operador_id=p_operador;
 insert into prumo_private.s1_intake_eventos(
 solicitante_id,operador_id,versao_anterior,versao_nova,pausado)
 values(p_gestor,p_operador,v_versao,v_versao+1,p_pausado);
 return pg_catalog.jsonb_build_object(
  'outcome',case when p_pausado then 'INTAKE_PAUSED' else 'INTAKE_RESUMED' end,
  'operator_id',p_operador,'intake_paused',p_pausado,'version',v_versao+1,
  'redistribution','DEFERRED_S0_HUMAN_PROOF');
end $f$;

-- Atomic cut-over if the previous intake-only table was installed.
-- Keep paused=TRUE and monotonic version. Old audit rows remain preserved
-- in their legacy table; old writes are locked during the transition.
do $cutover$
begin
 if pg_catalog.to_regclass('prumo_private.s1_disponibilidade_leads_10') is not null then
  lock table prumo_private.s1_disponibilidade_leads_10 in access exclusive mode;
  insert into prumo_private.s1_intake_estado(
   operador_id,pausado,versao,atualizado_em)
  select d.operador_id,d.pausado,d.versao,pg_catalog.statement_timestamp()
   from prumo_private.s1_disponibilidade_leads_10 d
  on conflict(operador_id) do update set
   pausado=excluded.pausado,versao=excluded.versao,
   atualizado_em=excluded.atualizado_em;
  drop trigger if exists s1_10_guard_novos_leads
   on public.atribuicoes_humanas;
 end if;
end $cutover$;

-- S0 owns this canonical table. The new trigger is an integration gate,
-- not a separate mock queue. All INSERT paths (manual, automatic, replay,
-- exception) converge here, including S1 old functions.
create function prumo_private.s0_s1_guard_intake_atribuicao()
returns trigger language plpgsql security invoker set search_path='' as $f$
declare v_estado text;
begin
 if tg_op='UPDATE'
   and new.operador_id is not distinct from old.operador_id
   and new.caso_id is not distinct from old.caso_id
   and new.concessionaria_id is not distinct from old.concessionaria_id then
  return new; -- closing or auditing existing assignments cannot be blocked.
 end if;
 -- Same lock used by s1_definir_intake. After waiting on the lock, this
 -- statement reads the committed intake state instead of trusting UI/JWT.
 select e.estado into v_estado from public.equipe_prumo_s1 e
  where e.ator_id=new.operador_id for share of e;
 if v_estado is distinct from 'ativo' then
  raise exception 'DESTINO_SEM_CONTA_ATIVA' using errcode='23514';end if;
 if exists(select 1 from prumo_private.s1_intake_estado d
    where d.operador_id=new.operador_id and d.pausado) then
  raise exception 'DESTINO_COM_INTAKE_PAUSADO' using errcode='23514';end if;
 return new;
end $f$;
create trigger s0_s1_guard_intake_atribuicao
 before insert or update of operador_id,concessionaria_id,caso_id
 on public.atribuicoes_humanas
 for each row execute function prumo_private.s0_s1_guard_intake_atribuicao();

-- Historical global-pause functions S1/048 suspend the ACCOUNT and trigger
-- blanket reassignment; that contradicts the current intake-only contract.
-- Fail closed until clients are migrated to the new versioned intake API.
create or replace function prumo_private.s1_pausar_operador_da_equipe(
 p_solicitante uuid,p_operador uuid,p_motivo_codigo text)
returns jsonb language plpgsql security invoker set search_path='' as $f$
begin
 raise exception 'PAUSA_GLOBAL_LEGADA_DESABILITADA_USAR_INTAKE'
 using errcode='42501';
end $f$;
create or replace function prumo_private.s1_reativar_operador_da_equipe(
 p_solicitante uuid,p_operador uuid)
returns jsonb language plpgsql security invoker set search_path='' as $f$
begin
 raise exception 'RETOMADA_GLOBAL_LEGADA_DESABILITADA_USAR_INTAKE'
 using errcode='42501';
end $f$;

revoke all on function
 prumo_private.s1_definir_intake(uuid,uuid,boolean,bigint),
 prumo_private.s0_s1_guard_intake_atribuicao(),
 prumo_private.s1_pausar_operador_da_equipe(uuid,uuid,text),
 prumo_private.s1_reativar_operador_da_equipe(uuid,uuid)
 from public,anon,authenticated,service_role;
commit;
