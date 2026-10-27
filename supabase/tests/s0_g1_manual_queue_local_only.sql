-- G1 / Issue #17. Disposable PG17 only, AFTER current canonical S1 I54-I62.
-- Manual queue -> own-team consultant. Not auto-dispatch, self-claim or transfer.
begin;
do $install$ begin
 if current_setting('prumo.g1_disposable',true) is distinct from 'YES'
 or current_user<>'postgres' or session_user<>'postgres' or current_database()<>'postgres'
 or current_setting('server_version_num')::int/10000<>17
 or to_regprocedure('prumo_private.s1_prova_excecao_i61(uuid,uuid,uuid,uuid)') is null
 or to_regprocedure('prumo_private.cfi01_session_valid_local(uuid,uuid)') is null
 then raise exception 'G1_DISPOSABLE_CANONICAL_PREREQUISITES' using errcode='42501';end if;
end $install$;

-- Preserve every I56 value; distinguish manual handoff in the SAME ledger.
do $event_contract$
declare v_def text;v_values text[];
begin
 select pg_catalog.pg_get_constraintdef(c.oid) into v_def from pg_catalog.pg_constraint c
 where c.conrelid='prumo_private.s0_fila_humana_eventos'::regclass and c.conname='s0_fila_evento_i56';
 select array_agg(m[1] order by m[1]) into v_values
 from pg_catalog.regexp_matches(v_def,'''([^'']*)''','g') m;
 if v_values is distinct from array['ASSUMIDO','DISTRIBUIDO','PENDENTE','RECONCILIADO']
 then raise exception 'G1_UNKNOWN_QUEUE_EVENT_CONTRACT' using errcode='42501';end if;
end $event_contract$;
alter table prumo_private.s0_fila_humana_eventos drop constraint s0_fila_evento_i56;
alter table prumo_private.s0_fila_humana_eventos add constraint s0_fila_evento_i56
 check(resultado in ('PENDENTE','ASSUMIDO','DISTRIBUIDO','RECONCILIADO','ENCAMINHADO'));

create table prumo_private.g1_manual_requests_local (
 id uuid primary key default gen_random_uuid(),
 gestor_id uuid not null,session_id uuid not null,concessionaria_id uuid not null,
 ciclo_id uuid not null,lead_id uuid not null,consultor_id uuid not null,
 versao_esperada bigint not null,chave_idempotencia text not null,
 caso_id uuid not null references public.casos_humanos(id),
 atribuicao_id uuid not null references public.atribuicoes_humanas(id),
 excecao_id uuid references prumo_private.s1_excecoes_caso_i61(id),
 criado_em timestamptz not null default clock_timestamp(),
 unique(gestor_id,concessionaria_id,chave_idempotencia)
);
create table prumo_private.g1_manual_audit_local (
 nonce uuid primary key references prumo_private.cfi01_consumed_nonces_local(nonce),
 request_id uuid not null references prumo_private.g1_manual_requests_local(id),
 session_id uuid not null,resultado text not null
 check(resultado in ('MANUAL_ASSIGNED','ALREADY_MANUAL_ASSIGNED')),
 criado_em timestamptz not null default clock_timestamp()
);
alter table prumo_private.g1_manual_requests_local enable row level security;
alter table prumo_private.g1_manual_audit_local enable row level security;
revoke all on prumo_private.g1_manual_requests_local,prumo_private.g1_manual_audit_local
 from public,anon,authenticated,service_role,prumo_cfi01_pgtest_login;
create trigger g1_request_immutable before update or delete or truncate
 on prumo_private.g1_manual_requests_local for each statement
 execute function prumo_private.cfi01_immutable_fact_local();
create trigger g1_audit_immutable before update or delete or truncate
 on prumo_private.g1_manual_audit_local for each statement
 execute function prumo_private.cfi01_immutable_fact_local();

-- Existing canonical triggers/commands explicitly require current_user=postgres.
-- As I55/I62, keep this NARROW private bridge; no direct EXECUTE for SQL login.
-- Do not relax/rewrite those S1 guards or give the application postgres rights.
create function prumo_private.g1_manual_bridge_local(
 p_gestor uuid,p_session uuid,p_loja uuid,p_ciclo uuid,p_destino uuid,
 p_versao bigint,p_request_key text,p_nonce uuid
) returns jsonb language plpgsql security definer set search_path='' as $bridge$
declare q record;r record;v_lead uuid;v_status text;v_case uuid;v_assignment uuid;
 v_exception uuid;v_id uuid;v_general boolean;v_outcome text;v_count integer;
begin
 if session_user<>'prumo_cfi01_pgtest_login'
 or not prumo_private.cfi01_session_valid_local(p_gestor,p_session)
 then raise exception 'G1_LIVE_SESSION_REQUIRED' using errcode='42501';end if;
 if p_gestor=p_destino then raise exception 'G1_USE_SELF_CLAIM' using errcode='P3102';end if;
 -- Cycle SHARE precedes lead: the I56 status writer already holds cycle
 -- while taking lead. FK KEY SHARE in old claim/auto paths is compatible.
 select c.lead_id,c.status_comercial into v_lead,v_status from public.ciclos_comerciais c
 where c.concessionaria_id=p_loja and c.id=p_ciclo for share of c;
 if not found then raise exception 'G1_NO_CYCLE' using errcode='42501';end if;
 perform 1 from public.leads_loja l where l.id=v_lead and l.concessionaria_id=p_loja for update of l;
 if not found then raise exception 'G1_NO_LEAD' using errcode='42501';end if;
 select f.* into q from prumo_private.s0_fila_humana f
 where f.concessionaria_id=p_loja and f.ciclo_id=p_ciclo for update of f;
 if not found then raise exception 'G1_NO_CANONICAL_QUEUE_SIGNAL' using errcode='42501';end if;
 -- Lock IDs without eligibility predicates, then re-read committed state.
 perform 1 from public.equipe_prumo_s1 e
 where e.ator_id in (p_gestor,p_destino) order by e.ator_id for share of e;
 select count(*) into v_count from public.equipe_prumo_s1 e
 where e.ator_id in (p_gestor,p_destino) and e.estado='ativo';
 if v_count<>2 then raise exception 'G1_INACTIVE_TEAM' using errcode='42501';end if;
 perform 1 from prumo_private.s1_gestor_operadores g
 where g.operador_id=p_destino order by g.id for share of g;
 if not exists(select 1 from prumo_private.s1_gestor_operadores g
  where g.gestor_id=p_gestor and g.operador_id=p_destino and g.encerrado_em is null)
 or exists(select 1 from prumo_private.s1_gestor_operadores g
  where g.gestor_id=p_destino and g.encerrado_em is null)
 or exists(select 1 from prumo_private.s1_responsaveis_plataforma rp
  where rp.ator_id=p_destino and rp.ativo)
 then raise exception 'G1_DESTINATION_NOT_OWN_CONSULTANT' using errcode='P3102';end if;
 perform prumo_private.s0_fila_exigir_gestor_i58(p_gestor,p_loja);
 perform 1 from public.vinculos_papel_escopo v
 where v.ator_id=p_destino and v.concessionaria_id=p_loja order by v.id for share of v;
 -- Same team row fence as s1_definir_intake/I52; cannot bypass with I61.
 if exists(select 1 from prumo_private.s1_intake_estado d where d.operador_id=p_destino and d.pausado)
 then raise exception 'G1_DESTINATION_INTAKE_PAUSED' using errcode='P3101';end if;
 select exists(select 1 from public.vinculos_papel_escopo v
  where v.ator_id=p_destino and v.concessionaria_id=p_loja and v.papel='operador'
   and v.valido_desde<=clock_timestamp() and (v.valido_ate is null or v.valido_ate>clock_timestamp())) into v_general;
 if not v_general and exists(select 1 from public.vinculos_papel_escopo v
  where v.ator_id=p_destino and v.concessionaria_id=p_loja
  and v.valido_desde<=clock_timestamp() and (v.valido_ate is null or v.valido_ate>clock_timestamp()))
 then raise exception 'G1_NON_CONSULTANT_STORE_ROLE' using errcode='P3102';end if;
 -- Wall-clock validity can change while waiting on another destination row.
 -- Locks already held are re-entrant; no new lower-ranked resource is added.
 perform prumo_private.s0_fila_exigir_gestor_i58(p_gestor,p_loja);
 if not prumo_private.cfi01_session_valid_local(p_gestor,p_session)
 then raise exception 'G1_SESSION_EXPIRED_DURING_WAIT' using errcode='42501';end if;

 select x.* into r from prumo_private.g1_manual_requests_local x
 where x.gestor_id=p_gestor and x.concessionaria_id=p_loja and x.chave_idempotencia=p_request_key;
 if found then
  if r.ciclo_id<>p_ciclo or r.consultor_id<>p_destino or r.versao_esperada<>p_versao
  then raise exception 'G1_IDEMPOTENCY_CONFLICT' using errcode='23505';end if;
  if q.estado<>'atribuido' or q.caso_id<>r.caso_id or q.atribuicao_id<>r.atribuicao_id
   or q.versao<>p_versao+1
   or not exists(select 1 from public.atribuicoes_humanas a
    where a.id=r.atribuicao_id and a.caso_id=r.caso_id and a.operador_id=p_destino and a.encerrada_em is null)
  then raise exception 'G1_REPLAY_SOURCE_CHANGED' using errcode='40001';end if;
  if (r.excecao_id is null and not v_general)
   or (r.excecao_id is not null and not prumo_private.s1_prova_excecao_i61(p_loja,r.caso_id,r.atribuicao_id,p_destino))
  then raise exception 'G1_REPLAY_AUTHORITY_REVOKED' using errcode='42501';end if;
  v_id:=r.id;v_case:=r.caso_id;v_assignment:=r.atribuicao_id;v_exception:=r.excecao_id;
  v_outcome:='ALREADY_MANUAL_ASSIGNED';
 else
  if q.estado<>'pendente' or q.versao<>p_versao then
   raise exception 'G1_QUEUE_CAS_CONFLICT' using errcode='40001';end if;
  if exists(select 1 from public.casos_humanos h
   where h.concessionaria_id=p_loja and h.lead_id=v_lead)
  then raise exception 'G1_ALREADY_HAS_CASE' using errcode='P3103';end if;
  if v_status not in ('em atendimento pelo operador','cadastro enviado ao operador')
  then raise exception 'G1_QUEUE_SIGNAL_STALE' using errcode='40001';end if;
  insert into public.casos_humanos(concessionaria_id,lead_id,ciclo_id)
   values(p_loja,v_lead,p_ciclo) returning id into v_case;
  v_assignment:=gen_random_uuid();
  if not v_general then
   -- Reuse I61's deferred assignment FK: exception precedes INSERT whose
   -- unchanged S0/I52/I57/I61 triggers verify this exact assignment UUID.
   insert into prumo_private.s1_excecoes_caso_i61(
    concessionaria_id,caso_id,atribuicao_id,operador_id,gestor_id)
   values(p_loja,v_case,v_assignment,p_destino,p_gestor) returning id into v_exception;
  end if;
  insert into public.atribuicoes_humanas(id,concessionaria_id,caso_id,operador_id)
   values(v_assignment,p_loja,v_case,p_destino);
  if v_exception is not null then
   insert into prumo_private.s1_excecoes_caso_eventos_i61(excecao_id,evento,solicitante_id)
   values(v_exception,'CRIADA',p_gestor);
  end if;
  update prumo_private.s0_fila_humana set estado='atribuido',versao=versao+1,
   caso_id=v_case,atribuicao_id=v_assignment,atualizado_em=clock_timestamp()
  where concessionaria_id=p_loja and ciclo_id=p_ciclo;
  insert into prumo_private.s0_fila_humana_eventos(
   concessionaria_id,lead_id,ciclo_id,versao_anterior,versao_nova,resultado,
   solicitante_id,operador_id,caso_id,atribuicao_id)
  values(p_loja,v_lead,p_ciclo,p_versao,p_versao+1,'ENCAMINHADO',p_gestor,p_destino,v_case,v_assignment);
  insert into prumo_private.g1_manual_requests_local(
   gestor_id,session_id,concessionaria_id,ciclo_id,lead_id,consultor_id,
   versao_esperada,chave_idempotencia,caso_id,atribuicao_id,excecao_id)
  values(p_gestor,p_session,p_loja,p_ciclo,v_lead,p_destino,p_versao,p_request_key,v_case,v_assignment,v_exception)
  returning id into v_id;
  v_outcome:='MANUAL_ASSIGNED';
 end if;
 insert into prumo_private.g1_manual_audit_local(nonce,request_id,session_id,resultado)
 values(p_nonce,v_id,p_session,v_outcome);
 return jsonb_build_object('outcome',v_outcome,'request_id',v_id,'store_id',p_loja,
  'cycle_id',p_ciclo,'consultant_id',p_destino,'case_id',v_case,'assignment_id',v_assignment,
  'exception_id',v_exception,'version',p_versao+1);
end $bridge$;
revoke all on function prumo_private.g1_manual_bridge_local(uuid,uuid,uuid,uuid,uuid,bigint,text,uuid)
 from public,anon,authenticated,service_role,prumo_cfi01_pgtest_login;

create role prumo_s0_g1_executor_local nologin noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
grant usage on schema prumo_private to prumo_s0_g1_executor_local;
grant execute on function prumo_private.g1_manual_bridge_local(uuid,uuid,uuid,uuid,uuid,bigint,text,uuid)
 to prumo_s0_g1_executor_local;
grant select(key_id,secret,active),update(key_id) on prumo_private.cfi01_signing_keys_local to prumo_s0_g1_executor_local;
create policy g1_key_read on prumo_private.cfi01_signing_keys_local for select to prumo_s0_g1_executor_local using(true);
create policy g1_key_lock on prumo_private.cfi01_signing_keys_local for update to prumo_s0_g1_executor_local using(true) with check(false);
grant insert(nonce,key_id),select(nonce) on prumo_private.cfi01_consumed_nonces_local to prumo_s0_g1_executor_local;
create policy g1_nonce_insert on prumo_private.cfi01_consumed_nonces_local for insert to prumo_s0_g1_executor_local with check(true);
create policy g1_nonce_read on prumo_private.cfi01_consumed_nonces_local for select to prumo_s0_g1_executor_local using(true);
do $crypto$ declare s name;begin
 select n.nspname into s from pg_extension e join pg_namespace n on n.oid=e.extnamespace where e.extname='pgcrypto';
 execute format('grant usage on schema %I to prumo_s0_g1_executor_local',s);
 execute format('grant execute on function %I.hmac(bytea,bytea,text) to prumo_s0_g1_executor_local',s);
end $crypto$;
create function prumo_private.g1_manual_signed_local(
 p_actor uuid,p_session uuid,p_shop uuid,p_cycle uuid,p_destination uuid,p_version bigint,p_request_key text,
 p_key uuid,p_issued bigint,p_nonce uuid,p_mac text
) returns jsonb language plpgsql security definer set search_path='' as $signed$
declare v_key bytea;v_schema name;v_mac bytea;v_material text;v_nonce uuid;v_result jsonb;
begin
 if session_user<>'prumo_cfi01_pgtest_login' or p_actor is null or p_session is null
 or p_shop is null or p_cycle is null or p_destination is null or p_version is null
 or p_version<1 or p_version>=9223372036854775807 or p_key is null or p_nonce is null
 or p_request_key is null or p_request_key !~ '^[A-Za-z0-9._:-]{8,128}$'
 or p_issued is null or p_issued<extract(epoch from clock_timestamp())::bigint-30
 or p_issued>extract(epoch from clock_timestamp())::bigint+5
 or p_mac is null or p_mac !~ '^[0-9a-f]{64}$'
 then raise exception 'G1_PROOF_INVALID' using errcode='42501';end if;
 select k.secret into v_key from prumo_private.cfi01_signing_keys_local k where k.key_id=p_key and k.active for share;
 if v_key is null then raise exception 'G1_KEY_REVOKED' using errcode='42501';end if;
 select n.nspname into v_schema from pg_catalog.pg_extension e join pg_catalog.pg_namespace n on n.oid=e.extnamespace where e.extname='pgcrypto';
 v_material:=concat_ws('|','s0-g1-manual-queue-local-v1',p_actor::text,p_session::text,p_shop::text,
  p_cycle::text,p_destination::text,p_version::text,p_request_key,p_key::text,p_issued::text,p_nonce::text);
 execute format('select %I.hmac($1,$2,''sha256'')',v_schema) into v_mac using convert_to(v_material,'UTF8'),v_key;
 if v_mac is distinct from decode(p_mac,'hex') then raise exception 'G1_MAC_INVALID' using errcode='42501';end if;
 insert into prumo_private.cfi01_consumed_nonces_local(nonce,key_id)
 values(p_nonce,p_key) on conflict do nothing returning nonce into v_nonce;
 if v_nonce is null then raise exception 'G1_NONCE_REPLAY' using errcode='42501';end if;
 v_result:=prumo_private.g1_manual_bridge_local(p_actor,p_session,p_shop,p_cycle,p_destination,p_version,p_request_key,p_nonce);
 if p_issued<extract(epoch from clock_timestamp())::bigint-30
 then raise exception 'G1_PROOF_EXPIRED_DURING_WAIT' using errcode='42501';end if;
 if v_result->>'outcome' not in ('MANUAL_ASSIGNED','ALREADY_MANUAL_ASSIGNED')
 then raise exception 'G1_BAD_RESULT' using errcode='42501';end if;
 return v_result;
end $signed$;
revoke all on function prumo_private.g1_manual_signed_local(uuid,uuid,uuid,uuid,uuid,bigint,text,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role;
grant execute on function prumo_private.g1_manual_signed_local(uuid,uuid,uuid,uuid,uuid,bigint,text,uuid,bigint,uuid,text)
 to prumo_cfi01_pgtest_login;
grant create on schema prumo_private to prumo_s0_g1_executor_local;
grant prumo_s0_g1_executor_local to postgres with inherit false,set true;
alter function prumo_private.g1_manual_signed_local(uuid,uuid,uuid,uuid,uuid,bigint,text,uuid,bigint,uuid,text)
 owner to prumo_s0_g1_executor_local;
revoke prumo_s0_g1_executor_local from postgres;
revoke create on schema prumo_private from prumo_s0_g1_executor_local;
commit;
