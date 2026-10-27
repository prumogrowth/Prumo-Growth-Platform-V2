-- I79/G2, additive experimental delta. ONLY disposable PG17 after PR20/I61.
begin;
do $guard$ begin
 if current_user<>'postgres' or session_user<>'postgres'
 or current_setting('prumo.i79_disposable',true) is distinct from 'YES'
 or current_database()<>'postgres' or current_setting('server_version_num')::int/10000<>17
 or to_regprocedure('prumo_private.g1_manual_signed_local(uuid,uuid,uuid,uuid,uuid,bigint,text,uuid,bigint,uuid,text)') is null
 then raise exception 'I79_DISPOSABLE_ONLY' using errcode='42501';end if;
end $guard$;

-- One professional identity, not another authentication/permission catalogue.
-- Legacy unclassified rows remain NULL, never inferred from shop grants/children.
alter table public.equipe_prumo_s1 add column cargo text
 check(cargo in ('diretor','gestor','consultor'));
update public.equipe_prumo_s1 e set cargo='diretor'
 where exists(select 1 from prumo_private.s1_responsaveis_plataforma r where r.ator_id=e.ator_id);
create function prumo_private.s1_i79_cargo(p_actor uuid)
returns text language sql stable security invoker set search_path='' as $$
 select e.cargo from public.equipe_prumo_s1 e where e.ator_id=p_actor
$$;

create function prumo_private.s1_i79_validar_profissional(p_actor uuid)
returns void language plpgsql security invoker set search_path='' as $$
declare e record;
begin
 select * into e from public.equipe_prumo_s1 where ator_id=p_actor;
 if not found then return;end if;
 -- Lock before eligibility reads: close deferred-constraint write skew between
 -- consultant activation and concurrent manager/account revocation.
 perform 1 from prumo_private.s1_gestor_operadores g join public.equipe_prumo_s1 m on m.ator_id=g.gestor_id
 where g.operador_id=p_actor and g.encerrado_em is null order by m.ator_id for share of m;
 perform 1 from prumo_private.s1_gestor_operadores g join public.equipe_prumo_s1 c on c.ator_id=g.operador_id
 where g.gestor_id=p_actor and g.encerrado_em is null order by c.ator_id for share of c;
 if e.cargo='diretor' and not exists(select 1 from prumo_private.s1_responsaveis_plataforma r where r.ator_id=p_actor)
 then raise exception 'I79_DIRECTOR_IDENTITY_REQUIRES_EXISTING_AUTHORITY' using errcode='23514';end if;
 if e.cargo in ('gestor','consultor') and exists(select 1 from prumo_private.s1_responsaveis_plataforma r where r.ator_id=p_actor)
 then raise exception 'I79_DIRECTOR_ROLE_CONFLICT' using errcode='23514';end if;
 if e.cargo='consultor' and e.estado='ativo' and (
  select count(*) from prumo_private.s1_gestor_operadores g
  join public.equipe_prumo_s1 m on m.ator_id=g.gestor_id
  where g.operador_id=p_actor and g.encerrado_em is null and m.estado='ativo' and m.cargo='gestor')<>1
 then raise exception 'I79_ACTIVE_CONSULTANT_REQUIRES_ONE_ACTIVE_MANAGER' using errcode='23514';end if;
 if e.cargo in ('gestor','diretor') and exists(select 1 from prumo_private.s1_gestor_operadores g where g.operador_id=p_actor and g.encerrado_em is null)
 then raise exception 'I79_NON_CONSULTANT_CANNOT_BE_SUBORDINATE' using errcode='23514';end if;
 -- A manager cannot become inactive while classified active consultants depend on it.
 if exists(select 1 from prumo_private.s1_gestor_operadores g
  join public.equipe_prumo_s1 c on c.ator_id=g.operador_id
  where g.gestor_id=p_actor and g.encerrado_em is null and c.cargo='consultor' and c.estado='ativo')
  and (e.cargo is distinct from 'gestor' or e.estado<>'ativo')
 then raise exception 'I79_MANAGER_STILL_HAS_ACTIVE_CONSULTANTS' using errcode='23514';end if;
end $$;
create function prumo_private.s1_i79_consistencia()
returns trigger language plpgsql security invoker set search_path='' as $$
begin
 if tg_table_name='equipe_prumo_s1' then
  perform prumo_private.s1_i79_validar_profissional(new.ator_id);
 else
  if tg_op<>'INSERT' then
   perform prumo_private.s1_i79_validar_profissional(old.operador_id);
   perform prumo_private.s1_i79_validar_profissional(old.gestor_id);
  end if;
  if tg_op<>'DELETE' then
   perform prumo_private.s1_i79_validar_profissional(new.operador_id);
   perform prumo_private.s1_i79_validar_profissional(new.gestor_id);
  end if;
 end if;
 return null;
end $$;
create constraint trigger s1_i79_professional_commit after insert or update on public.equipe_prumo_s1
 deferrable initially deferred for each row execute function prumo_private.s1_i79_consistencia();
create constraint trigger s1_i79_manager_commit after insert or update or delete on prumo_private.s1_gestor_operadores
 deferrable initially deferred for each row execute function prumo_private.s1_i79_consistencia();

-- All writers, including trusted SQL, share the SAME account-row fence as intake.
create function prumo_private.s1_i79_relacao_lock()
returns trigger language plpgsql security invoker set search_path='' as $$
declare g uuid;c uuid;
begin
 if tg_op='DELETE' then raise exception 'I79_RELATION_HISTORY_IMMUTABLE' using errcode='23514';end if;
 if tg_op='UPDATE' and (new.id is distinct from old.id or new.gestor_id is distinct from old.gestor_id
  or new.operador_id is distinct from old.operador_id or new.atribuido_em is distinct from old.atribuido_em
  or old.encerrado_em is not null)
 then raise exception 'I79_RELATION_HISTORY_IMMUTABLE' using errcode='23514';end if;
 g:=new.gestor_id;c:=new.operador_id;
 perform 1 from public.equipe_prumo_s1 e where e.ator_id in(g,c) order by e.ator_id for update;
 return new;
end $$;
create trigger s1_i79_relation_fence before insert or update or delete on prumo_private.s1_gestor_operadores
 for each row execute function prumo_private.s1_i79_relacao_lock();

-- Canonical S0 assignment boundary. No unclassified legacy actor gets NEW leads.
create function prumo_private.s1_i79_assignment_guard()
returns trigger language plpgsql security invoker set search_path='' as $$
declare role_name text;
begin
 if tg_op='UPDATE' and new.operador_id is not distinct from old.operador_id
 and new.caso_id is not distinct from old.caso_id and new.concessionaria_id is not distinct from old.concessionaria_id then return new;end if;
 perform 1 from public.equipe_prumo_s1 e where e.ator_id=new.operador_id for share;
 role_name:=prumo_private.s1_i79_cargo(new.operador_id);
 if role_name is null or role_name not in ('gestor','consultor') then
  raise exception 'I79_DESTINATION_UNCLASSIFIED' using errcode='23514';end if;
 perform prumo_private.s1_i79_validar_profissional(new.operador_id);
 return new;
end $$;
create trigger s1_i79_assignment before insert or update of operador_id,caso_id,concessionaria_id on public.atribuicoes_humanas
 for each row execute function prumo_private.s1_i79_assignment_guard();

-- G1 already holds account/team locks. Enforce explicit roles on BOTH fresh
-- handoffs and live idempotent replays, without rewriting its certified runtime.
create function prumo_private.s1_i79_g1_guard()
returns trigger language plpgsql security invoker set search_path='' as $$
declare r record;
begin
 if tg_table_name='g1_manual_requests_local' then r:=new;
 else select * into r from prumo_private.g1_manual_requests_local where id=new.request_id;end if;
 if prumo_private.s1_i79_cargo(r.gestor_id) is distinct from 'gestor'
 or prumo_private.s1_i79_cargo(r.consultor_id) is distinct from 'consultor'
 then raise exception 'I79_G1_EXPLICIT_ROLES_REQUIRED' using errcode='23514';end if;
 perform prumo_private.s1_i79_validar_profissional(r.consultor_id);
 return new;
end $$;
create trigger s1_i79_g1_request before insert on prumo_private.g1_manual_requests_local
 for each row execute function prumo_private.s1_i79_g1_guard();
create trigger s1_i79_g1_replay before insert on prumo_private.g1_manual_audit_local
 for each row execute function prumo_private.s1_i79_g1_guard();

-- Classified administrative activation is NOT legacy case recovery.
-- Preserve the old path for historical regressions, without enabling it for I79.
create or replace function prumo_private.s1_recuperar_apos_ativacao()
returns trigger language plpgsql security invoker set search_path='' as $$
declare r record;
begin
 if new.cargo is not null then return new;end if;
 if new.estado='ativo' and (tg_op='INSERT' or old.estado is distinct from new.estado) then
  for r in select distinct v.concessionaria_id from public.vinculos_papel_escopo v
   where v.ator_id=new.ator_id and v.papel='operador' and v.valido_desde<=statement_timestamp()
   and (v.valido_ate is null or v.valido_ate>statement_timestamp()) order by v.concessionaria_id
  loop perform prumo_private.s1_recuperar_fila_protegida(r.concessionaria_id,25);end loop;
 end if;
 return new;
end $$;

create table prumo_private.s1_i79_requests (
 id uuid primary key default gen_random_uuid(),diretor_id uuid not null,
 request_key text not null,payload jsonb not null,receipt jsonb not null,
 criado_em timestamptz not null default clock_timestamp(),unique(diretor_id,request_key)
);
create table prumo_private.s1_i79_audit (
 nonce uuid primary key references prumo_private.cfi01_consumed_nonces_local(nonce),
 request_id uuid not null references prumo_private.s1_i79_requests(id),session_id uuid not null,
 resultado text not null check(resultado in('APPLIED','ALREADY_APPLIED')),
 criado_em timestamptz not null default clock_timestamp()
);
alter table prumo_private.s1_i79_requests enable row level security;
alter table prumo_private.s1_i79_audit enable row level security;
revoke all on prumo_private.s1_i79_requests,prumo_private.s1_i79_audit from public,anon,authenticated,service_role,prumo_cfi01_pgtest_login;
create trigger s1_i79_request_immutable before update or delete or truncate on prumo_private.s1_i79_requests
 for each statement execute function prumo_private.cfi01_immutable_fact_local();
create trigger s1_i79_audit_immutable before update or delete or truncate on prumo_private.s1_i79_audit
 for each statement execute function prumo_private.cfi01_immutable_fact_local();

create function prumo_private.s1_i79_admin_bridge(
 p_actor uuid,p_session uuid,p_action text,p_target uuid,p_cargo text,p_manager uuid,
 p_previous bigint,p_request text,p_nonce uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare e record;r record;v_old_manager uuid;v_relation bigint;v_receipt jsonb;v_payload jsonb;
begin
 if session_user<>'prumo_cfi01_pgtest_login' or p_actor=p_target
 or not prumo_private.cfi01_session_valid_local(p_actor,p_session)
 then raise exception 'I79_SESSION_REQUIRED' using errcode='42501';end if;
 if p_action='TRANSFER' then
  select gestor_id into v_old_manager from prumo_private.s1_gestor_operadores
   where id=p_previous and operador_id=p_target;
 end if;
 -- Common actor row serializes absent-team-row REGISTERs too. NO KEY UPDATE
 -- remains compatible with the FK checks used by existing case writers.
 perform 1 from public.atores a where a.id in(p_actor,p_target,p_manager,v_old_manager)
 order by a.id for no key update;
 perform 1 from public.equipe_prumo_s1 x where x.ator_id in(p_actor,p_target,p_manager,v_old_manager)
 order by x.ator_id for update;
 perform 1 from prumo_private.s1_responsaveis_plataforma d where d.ator_id=p_actor for share;
 if not exists(select 1 from public.equipe_prumo_s1 x join prumo_private.s1_responsaveis_plataforma d on d.ator_id=x.ator_id
  where x.ator_id=p_actor and x.cargo='diretor' and x.estado='ativo' and d.ativo)
 or not prumo_private.cfi01_session_valid_local(p_actor,p_session)
 then raise exception 'I79_DIRECTOR_REQUIRED' using errcode='42501';end if;
 v_payload:=jsonb_build_array(p_action,p_target,p_cargo,p_manager,p_previous);
 -- Director row lock serializes same-key requests even across different targets.
 select * into r from prumo_private.s1_i79_requests where diretor_id=p_actor and request_key=p_request;
 if found then
  if r.payload<>v_payload then raise exception 'I79_IDEMPOTENCY_CONFLICT' using errcode='23505';end if;
  if p_action<>'REGISTER' and not exists(select 1 from public.equipe_prumo_s1 x
   where x.ator_id=p_target and x.estado='ativo' and x.cargo=p_cargo)
  then raise exception 'I79_REPLAY_TARGET_REVOKED' using errcode='42501';end if;
  if p_manager is not null and not exists(select 1 from public.equipe_prumo_s1 x
   where x.ator_id=p_manager and x.estado='ativo' and x.cargo='gestor')
  then raise exception 'I79_REPLAY_MANAGER_REVOKED' using errcode='42501';end if;
  -- A receipt never restores an old management relation or authority.
  if r.receipt->>'relationship_id' is not null and not exists(
   select 1 from prumo_private.s1_gestor_operadores g
   where g.id=(r.receipt->>'relationship_id')::bigint and g.operador_id=p_target and g.encerrado_em is null)
  then raise exception 'I79_REPLAY_SOURCE_CHANGED' using errcode='40001';end if;
  v_receipt:=r.receipt||jsonb_build_object('outcome','ALREADY_APPLIED');
 else
  select * into e from public.equipe_prumo_s1 where ator_id=p_target;
  if p_action='REGISTER' then
   if found then raise exception 'I79_ALREADY_REGISTERED' using errcode='40001';end if;
   perform 1 from auth.users u where u.id=p_target for share;
   if not found then raise exception 'I79_AUTH_IDENTITY_REQUIRED' using errcode='42501';end if;
   insert into public.atores(id) values(p_target) on conflict do nothing;
   insert into public.equipe_prumo_s1(ator_id,cargo,estado) values(p_target,p_cargo,'pendente');
  else
   if not found then raise exception 'I79_NOT_REGISTERED' using errcode='42501';end if;
   if p_action='ACTIVATE' and (e.estado<>'pendente' or e.cargo<>p_cargo)
   then raise exception 'I79_STALE_ACTIVATION' using errcode='40001';end if;
   if p_action='TRANSFER' and (e.estado<>'ativo' or e.cargo<>'consultor')
   then raise exception 'I79_TARGET_NOT_ACTIVE_CONSULTANT' using errcode='42501';end if;
   if p_cargo='consultor' then
    if p_manager in(p_target,p_actor) or not exists(select 1 from public.equipe_prumo_s1 x
     where x.ator_id=p_manager and x.cargo='gestor' and x.estado='ativo')
    then raise exception 'I79_ACTIVE_MANAGER_REQUIRED' using errcode='42501';end if;
    select id into v_relation from prumo_private.s1_gestor_operadores where operador_id=p_target and encerrado_em is null for update;
    if coalesce(v_relation,0)<>p_previous then raise exception 'I79_STALE_RELATION' using errcode='40001';end if;
    if p_action='TRANSFER' then
     if v_old_manager=p_manager then raise exception 'I79_SAME_MANAGER' using errcode='40001';end if;
     update prumo_private.s1_gestor_operadores set encerrado_em=greatest(atribuido_em,clock_timestamp()) where id=v_relation;
    end if;
    insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values(p_manager,p_target) returning id into v_relation;
   end if;
   if p_action='ACTIVATE' then update public.equipe_prumo_s1 set estado='ativo' where ator_id=p_target;end if;
  end if;
  v_receipt:=jsonb_build_object('outcome','APPLIED','request_id',gen_random_uuid(),'action',p_action,
   'target_id',p_target,'cargo',p_cargo,'manager_id',p_manager,
   'previous_relationship_id',p_previous::text,'relationship_id',v_relation::text);
  insert into prumo_private.s1_i79_requests(id,diretor_id,request_key,payload,receipt)
   values((v_receipt->>'request_id')::uuid,p_actor,p_request,v_payload,v_receipt);
 end if;
 insert into prumo_private.s1_i79_audit(nonce,request_id,session_id,resultado)
 values(p_nonce,(v_receipt->>'request_id')::uuid,p_session,v_receipt->>'outcome');
 return v_receipt;
end $$;
revoke all on function prumo_private.s1_i79_admin_bridge(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid) from public,anon,authenticated,service_role,prumo_cfi01_pgtest_login;
grant execute on function prumo_private.s1_i79_admin_bridge(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid) to prumo_s0_g1_executor_local;

create function prumo_private.s1_i79_admin_signed(
 p_actor uuid,p_session uuid,p_action text,p_target uuid,p_cargo text,p_manager uuid,p_previous bigint,p_request text,
 p_key uuid,p_issued bigint,p_nonce uuid,p_mac text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_secret bytea;v_schema name;v_material text;v_mac bytea;v_nonce uuid;v_result jsonb;
begin
 if session_user<>'prumo_cfi01_pgtest_login' or p_actor is null or p_session is null or p_target is null
 or p_action is null or p_action not in('REGISTER','ACTIVATE','TRANSFER') or p_cargo is null or p_cargo not in('gestor','consultor')
 or p_previous is null or p_previous<0 or p_request is null or p_request !~ '^[A-Za-z0-9._:-]{8,128}$'
 or (p_action='REGISTER' and (p_manager is not null or p_previous<>0))
 or (p_action='ACTIVATE' and (p_previous<>0 or (p_cargo='gestor' and p_manager is not null) or (p_cargo='consultor' and p_manager is null)))
 or (p_action='TRANSFER' and (p_cargo<>'consultor' or p_manager is null or p_previous<1))
 or p_key is null or p_nonce is null or p_issued is null or p_mac is null or p_mac !~ '^[0-9a-f]{64}$'
 or p_issued<extract(epoch from clock_timestamp())::bigint-30 or p_issued>extract(epoch from clock_timestamp())::bigint+5
 then raise exception 'I79_INVALID_PROOF' using errcode='42501';end if;
 select secret into v_secret from prumo_private.cfi01_signing_keys_local where key_id=p_key and active for share;
 if v_secret is null then raise exception 'I79_KEY_REVOKED' using errcode='42501';end if;
 select n.nspname into v_schema from pg_extension e join pg_namespace n on n.oid=e.extnamespace where e.extname='pgcrypto';
 v_material:=concat_ws('|','s0-s1-i79-admin-v1',p_actor::text,p_session::text,p_action,p_target::text,p_cargo,
  coalesce(p_manager::text,'-'),p_previous::text,p_request,p_key::text,p_issued::text,p_nonce::text);
 execute format('select %I.hmac($1,$2,''sha256'')',v_schema) into v_mac using convert_to(v_material,'UTF8'),v_secret;
 if v_mac is distinct from decode(p_mac,'hex') then raise exception 'I79_BAD_MAC' using errcode='42501';end if;
 insert into prumo_private.cfi01_consumed_nonces_local(nonce,key_id) values(p_nonce,p_key)
 on conflict do nothing returning nonce into v_nonce;
 if v_nonce is null then raise exception 'I79_REPLAY' using errcode='42501';end if;
 v_result:=prumo_private.s1_i79_admin_bridge(p_actor,p_session,p_action,p_target,p_cargo,p_manager,p_previous,p_request,p_nonce);
 if p_issued<extract(epoch from clock_timestamp())::bigint-30 then raise exception 'I79_PROOF_EXPIRED_AFTER_WAIT' using errcode='42501';end if;
 return v_result;
end $$;
revoke all on function prumo_private.s1_i79_admin_signed(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid,bigint,uuid,text) from public,anon,authenticated,service_role;
grant execute on function prumo_private.s1_i79_admin_signed(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid,bigint,uuid,text) to prumo_cfi01_pgtest_login;
grant create on schema prumo_private to prumo_s0_g1_executor_local;
grant prumo_s0_g1_executor_local to postgres with inherit false,set true;
alter function prumo_private.s1_i79_admin_signed(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid,bigint,uuid,text) owner to prumo_s0_g1_executor_local;
revoke prumo_s0_g1_executor_local from postgres;
revoke create on schema prumo_private from prumo_s0_g1_executor_local;
revoke all on function prumo_private.s1_i79_cargo(uuid),prumo_private.s1_i79_validar_profissional(uuid),
 prumo_private.s1_i79_consistencia(),prumo_private.s1_i79_relacao_lock(),prumo_private.s1_i79_assignment_guard(),prumo_private.s1_i79_g1_guard()
 from public,anon,authenticated,service_role,prumo_cfi01_pgtest_login;
commit;
