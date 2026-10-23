-- I54: S0 human-handoff queue anchored in REAL S0 lead/cycle, not I49 mock.
-- TESTED ONLY in disposable PG17 until signed command owner is integrated.
-- Business signal: status -> human-attention state. No signal == no queue.
create table prumo_private.s0_fila_humana (
 concessionaria_id uuid not null,
 lead_id uuid not null,
 ciclo_id uuid not null,
 estado text not null default 'pendente' check (estado in ('pendente','atribuido')),
 versao bigint not null default 1 check(versao>=1),
 caso_id uuid,
 atribuicao_id uuid references public.atribuicoes_humanas(id),
 criado_em timestamptz not null default pg_catalog.statement_timestamp(),
 atualizado_em timestamptz not null default pg_catalog.statement_timestamp(),
 primary key(concessionaria_id,ciclo_id),
 foreign key(concessionaria_id,ciclo_id,lead_id)
   references public.ciclos_comerciais(concessionaria_id,id,lead_id),
 foreign key(concessionaria_id,caso_id,lead_id)
   references public.casos_humanos(concessionaria_id,id,lead_id),
 check ((estado='pendente' and caso_id is null and atribuicao_id is null)
 or (estado='atribuido' and caso_id is not null and atribuicao_id is not null))
);
create index s0_fila_humana_pendente_loja on prumo_private.s0_fila_humana(
 concessionaria_id,criado_em,ciclo_id) where estado='pendente';
create table prumo_private.s0_fila_humana_eventos (
 id bigint generated always as identity primary key,
 concessionaria_id uuid not null,
 lead_id uuid not null,
 ciclo_id uuid not null,
 versao_anterior bigint,
 versao_nova bigint not null check(versao_nova>=1),
 resultado text not null check(resultado in ('PENDENTE','ASSUMIDO','DISTRIBUIDO')),
 solicitante_id uuid references public.atores(id),
 operador_id uuid references public.atores(id),
 caso_id uuid,
 atribuicao_id uuid,
 criado_em timestamptz not null default pg_catalog.statement_timestamp(),
 foreign key(concessionaria_id,ciclo_id,lead_id)
  references public.ciclos_comerciais(concessionaria_id,id,lead_id)
);
alter table prumo_private.s0_fila_humana enable row level security;
alter table prumo_private.s0_fila_humana_eventos enable row level security;
revoke all on prumo_private.s0_fila_humana,prumo_private.s0_fila_humana_eventos
 from public,anon,authenticated,service_role;
revoke all on sequence prumo_private.s0_fila_humana_eventos_id_seq
 from public,anon,authenticated,service_role;

-- Only explicit S0 human-handoff statuses produce an event. The status
-- transition and queue insertion commit atomically; a generic lead without
-- a case does NOT automatically enter the team queue.
create function prumo_private.s0_fila_registrar_sinal()
returns trigger language plpgsql security invoker set search_path='' as $f$
begin
 if current_user<>'postgres' then
  raise exception 'S0_FILA_EXECUTOR_INTERNO' using errcode='42501';end if;
 if new.status_comercial not in
    ('em atendimento pelo operador','cadastro enviado ao operador') then
  return new;
 end if;
 if tg_op='UPDATE' and new.status_comercial is not distinct from old.status_comercial
 then return new;end if;
 -- A prior human case for the contact (even on older cycle) is NOT queueable.
 if exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=new.concessionaria_id and h.lead_id=new.lead_id)
 then return new;end if;
 insert into prumo_private.s0_fila_humana(concessionaria_id,lead_id,ciclo_id)
 values(new.concessionaria_id,new.lead_id,new.id)
 on conflict(concessionaria_id,ciclo_id) do nothing;
 if found then
  insert into prumo_private.s0_fila_humana_eventos(
   concessionaria_id,lead_id,ciclo_id,versao_nova,resultado)
  values(new.concessionaria_id,new.lead_id,new.id,1,'PENDENTE');
 end if;
 return new;
end $f$;
create trigger s0_fila_sinal_ingresso
 after insert or update of status_comercial on public.ciclos_comerciais
 for each row execute function prumo_private.s0_fila_registrar_sinal();

-- Internal S0 operation. No public RPC, no customer exposure.
-- Serializes lead -> queue -> case -> assignment; identity of the claiming
-- manager MUST come from the trusted signed gateway (not JSON fields).
create function prumo_private.s0_fila_assumir(
 p_gestor uuid,p_loja uuid,p_ciclo uuid,p_versao bigint)
returns jsonb language plpgsql security invoker set search_path='' as $f$
declare q record;v_caso uuid;v_atr uuid;
begin
 if current_user<>'postgres' then
  raise exception 'S0_FILA_EXECUTOR_INTERNO' using errcode='42501';end if;
 if p_gestor is null or p_loja is null or p_ciclo is null
  or p_versao is null or p_versao<1 then
  raise exception 'S0_FILA_PARAMETROS_INVALIDOS' using errcode='22023';end if;
 -- Versioned queue is an explicit S0 event, not a naked missing-case inference.
 select q0.lead_id into q from prumo_private.s0_fila_humana q0
  where q0.concessionaria_id=p_loja and q0.ciclo_id=p_ciclo;
 if not found then raise exception 'S0_FILA_NAO_EXISTE' using errcode='22023';end if;
 perform 1 from public.leads_loja l where l.concessionaria_id=p_loja
  and l.id=q.lead_id for update of l;
 if not found then raise exception 'S0_LEAD_NAO_EXISTE' using errcode='22023';end if;
 select f.* into q from prumo_private.s0_fila_humana f
  where f.concessionaria_id=p_loja and f.ciclo_id=p_ciclo for update of f;
 if q.estado<>'pendente' or q.versao<>p_versao then
  return pg_catalog.jsonb_build_object('outcome','CONFLICT');end if;
 -- Lock manager, store and grant AFTER the lead; protect against revocation.
 perform 1 from public.equipe_prumo_s1 e
 join public.vinculos_papel_escopo v on v.ator_id=e.ator_id
  and v.concessionaria_id=p_loja and v.papel='gestor'
  and v.valido_desde<=pg_catalog.statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
 join public.concessionarias l on l.id=v.concessionaria_id and l.ativo
 where e.ator_id=p_gestor and e.estado='ativo'
 for share of e,v,l;
 if not found then raise exception 'S0_FILA_GESTOR_SEM_LOJA'
   using errcode='42501';end if;
 -- A Gestor cannot claim to themselves if intake explicitly paused.
 -- The canonical I52 guard is also enforced on the assignment INSERT.
 if exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.lead_id=q.lead_id) then
  return pg_catalog.jsonb_build_object('outcome','ALREADY_HAS_CASE');
 end if;
 if not exists(select 1 from public.ciclos_comerciais c
  where c.concessionaria_id=p_loja and c.id=p_ciclo and c.lead_id=q.lead_id
  and c.status_comercial in
   ('em atendimento pelo operador','cadastro enviado ao operador'))
 then raise exception 'S0_FILA_SINAL_EXPIRADO' using errcode='23514';end if;
 insert into public.casos_humanos(concessionaria_id,lead_id,ciclo_id)
  values(p_loja,q.lead_id,p_ciclo) returning id into v_caso;
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
  values(p_loja,v_caso,p_gestor) returning id into v_atr;
 update prumo_private.s0_fila_humana set estado='atribuido',versao=versao+1,
  caso_id=v_caso,atribuicao_id=v_atr,atualizado_em=pg_catalog.statement_timestamp()
 where concessionaria_id=p_loja and ciclo_id=p_ciclo;
 insert into prumo_private.s0_fila_humana_eventos(
 concessionaria_id,lead_id,ciclo_id,versao_anterior,versao_nova,
 resultado,solicitante_id,operador_id,caso_id,atribuicao_id)
 values(p_loja,q.lead_id,p_ciclo,p_versao,p_versao+1,
 'ASSUMIDO',p_gestor,p_gestor,v_caso,v_atr);
 return pg_catalog.jsonb_build_object('outcome','CLAIMED_BY_MANAGER',
  'case_id',v_caso,'assignment_id',v_atr,'version',p_versao+1);
end $f$;

-- Auto-dispatch a signalled case-less lead. Never pick a paused destination;
-- all cross-team consultants with CURRENT shop grant can be considered.
-- Actor eligibility and intake are locked and revalidated by the canonical
-- BEFORE INSERT trigger; no non-real queue claim rights delegated to clients.
create function prumo_private.s0_fila_distribuir(
 p_loja uuid,p_ciclo uuid,p_versao bigint)
returns jsonb language plpgsql security invoker set search_path='' as $f$
declare q record;v_destino uuid;v_caso uuid;v_atr uuid;
begin
 if current_user<>'postgres' then
  raise exception 'S0_FILA_EXECUTOR_INTERNO' using errcode='42501';end if;
 if p_loja is null or p_ciclo is null or p_versao is null or p_versao<1
 then raise exception 'S0_FILA_PARAMETROS_INVALIDOS' using errcode='22023';end if;
 select f.lead_id into q from prumo_private.s0_fila_humana f
  where f.concessionaria_id=p_loja and f.ciclo_id=p_ciclo;
 if not found then raise exception 'S0_FILA_NAO_EXISTE' using errcode='22023';end if;
 perform 1 from public.leads_loja l where l.concessionaria_id=p_loja
  and l.id=q.lead_id for update of l;
 if not found then raise exception 'S0_LEAD_NAO_EXISTE' using errcode='22023';end if;
 select f.* into q from prumo_private.s0_fila_humana f
  where f.concessionaria_id=p_loja and f.ciclo_id=p_ciclo for update of f;
 if q.estado<>'pendente' or q.versao<>p_versao then
  return pg_catalog.jsonb_build_object('outcome','CONFLICT');end if;
 if exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.lead_id=q.lead_id) then
  return pg_catalog.jsonb_build_object('outcome','ALREADY_HAS_CASE');end if;
 if not exists(select 1 from public.ciclos_comerciais c
  where c.concessionaria_id=p_loja and c.id=p_ciclo and c.lead_id=q.lead_id
  and c.status_comercial in
   ('em atendimento pelo operador','cadastro enviado ao operador'))
 then raise exception 'S0_FILA_SINAL_EXPIRADO' using errcode='23514';end if;
 select e.ator_id into v_destino from public.equipe_prumo_s1 e
 join prumo_private.s1_gestor_operadores g on g.operador_id=e.ator_id
  and g.encerrado_em is null
 join public.equipe_prumo_s1 chefe on chefe.ator_id=g.gestor_id
  and chefe.estado='ativo'
 join public.vinculos_papel_escopo v on v.ator_id=e.ator_id
  and v.concessionaria_id=p_loja and v.papel='operador'
  and v.valido_desde<=pg_catalog.statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
 join public.concessionarias l on l.id=p_loja and l.ativo
 left join prumo_private.s1_intake_estado d on d.operador_id=e.ator_id
 where e.estado='ativo' and coalesce(d.pausado,false)=false
 order by (select count(*) from public.atribuicoes_humanas a
    where a.operador_id=e.ator_id and a.encerrada_em is null),e.ator_id
 limit 1 for share of e,g,chefe,v,l;
 if v_destino is null then
  return pg_catalog.jsonb_build_object('outcome','QUEUED_UNOWNED',
    'version',q.versao);end if;
 insert into public.casos_humanos(concessionaria_id,lead_id,ciclo_id)
  values(p_loja,q.lead_id,p_ciclo) returning id into v_caso;
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
  values(p_loja,v_caso,v_destino) returning id into v_atr;
 update prumo_private.s0_fila_humana set estado='atribuido',versao=versao+1,
  caso_id=v_caso,atribuicao_id=v_atr,atualizado_em=pg_catalog.statement_timestamp()
  where concessionaria_id=p_loja and ciclo_id=p_ciclo;
 insert into prumo_private.s0_fila_humana_eventos(
 concessionaria_id,lead_id,ciclo_id,versao_anterior,versao_nova,
 resultado,operador_id,caso_id,atribuicao_id)
 values(p_loja,q.lead_id,p_ciclo,p_versao,p_versao+1,
 'DISTRIBUIDO',v_destino,v_caso,v_atr);
 return pg_catalog.jsonb_build_object('outcome','ASSIGNED_NEW',
  'operator_id',v_destino,'case_id',v_caso,'assignment_id',v_atr,
  'version',p_versao+1);
end $f$;

revoke all on function
 prumo_private.s0_fila_registrar_sinal(),
 prumo_private.s0_fila_assumir(uuid,uuid,uuid,bigint),
 prumo_private.s0_fila_distribuir(uuid,uuid,bigint)
 from public,anon,authenticated,service_role;
