-- I86 manual-policy laboratory instrument. NOT a hosted migration or RPC.
begin;
do $install$
begin
 if current_user<>'postgres' or session_user<>'postgres'
 or current_database()<>'postgres' or current_setting('server_version_num')::int/10000<>17
 or current_setting('transaction_isolation')<>'read committed'
 or coalesce((select shobj_description(oid,'pg_database') from pg_database
  where datname=current_database()) like 'PRUMO_I84_DISPOSABLE:%',false) is not true
 then raise exception 'I86M_DISPOSABLE_INSTALLER_REQUIRED' using errcode='42501';end if;
end $install$;
create schema prumo_i86_manual;
revoke all on schema prumo_i86_manual from public,anon,authenticated,service_role,
 prumo_s1_admin_edge_local,prumo_cfi01_pgtest_login;

create table prumo_i86_manual.acts(
 act_id uuid primary key,
 payload jsonb not null,
 result jsonb not null,
 transaction_xid xid8 not null default pg_current_xact_id(),
 recorded_at timestamptz not null default clock_timestamp()
);
create table prumo_i86_manual.audit(
 act_id uuid primary key references prumo_i86_manual.acts(act_id),
 operator_record_ref text not null,
 manual_record_ref text not null,
 evidence_sha256 text not null,
 sql_session_principal text not null,
 sql_effective_principal text not null,
 backend_pid integer not null,
 client_addr inet,
 recorded_at timestamptz not null default clock_timestamp()
);
alter table prumo_i86_manual.acts enable row level security;
alter table prumo_i86_manual.acts force row level security;
alter table prumo_i86_manual.audit enable row level security;
alter table prumo_i86_manual.audit force row level security;

create function prumo_i86_manual.guard()
returns void language plpgsql security invoker set search_path='' as $guard$
begin
 -- SQL identity is NOT a proof of human presence. Its custody is external.
 -- No JWT/metadata, role membership, application_name or "manual=true" GUC.
 if current_user<>'postgres' or session_user<>'postgres'
 or current_database()<>'postgres' or current_setting('server_version_num')::int/10000<>17
 or current_setting('transaction_isolation')<>'read committed'
 or coalesce((select pg_catalog.shobj_description(oid,'pg_database') from pg_catalog.pg_database
  where datname=pg_catalog.current_database()) like 'PRUMO_I84_DISPOSABLE:%',false) is not true
 then raise exception 'I86M_PRIVILEGED_OPERATOR_CONTEXT_REQUIRED' using errcode='42501';end if;
end $guard$;

create function prumo_i86_manual.immutable()
returns trigger language plpgsql security invoker set search_path='' as $immutable$
begin raise exception 'I86M_MANUAL_EVIDENCE_IMMUTABLE' using errcode='42501';end $immutable$;
create trigger immutable_rows before update or delete on prumo_i86_manual.acts
 for each statement execute function prumo_i86_manual.immutable();
create trigger immutable_truncate before truncate on prumo_i86_manual.acts
 for each statement execute function prumo_i86_manual.immutable();
create trigger immutable_rows before update or delete on prumo_i86_manual.audit
 for each statement execute function prumo_i86_manual.immutable();
create trigger immutable_truncate before truncate on prumo_i86_manual.audit
 for each statement execute function prumo_i86_manual.immutable();

create function prumo_i86_manual.subject_state(p_target uuid)
returns jsonb language plpgsql security invoker set search_path='' as $state$
declare value jsonb;
begin
 perform prumo_i86_manual.guard();
 if p_target is null then raise exception 'I86M_TARGET_REQUIRED' using errcode='22023';end if;
 select pg_catalog.jsonb_build_object(
  'target_id',p_target::text,'auth_exists',u.id is not null,
  'auth_usable',coalesce(u.deleted_at is null and (u.banned_until is null or u.banned_until<=pg_catalog.clock_timestamp()),false) and u.id is not null,
  'actor_exists',a.id is not null,'actor_revision',a.xmin::text,
  'cargo',t.cargo,'estado',t.estado,'team_revision',t.xmin::text,
  'competence_exists',d.ator_id is not null,'competence_active',coalesce(d.ativo,false),
  'competence_revision',d.xmin::text)
 into value
 from (select p_target id) seed
 left join auth.users u on u.id=seed.id
 left join public.atores a on a.id=seed.id
 left join public.equipe_prumo_s1 t on t.ator_id=seed.id
 left join prumo_private.s1_responsaveis_plataforma d on d.ator_id=seed.id;
 return value;
end $state$;

create function prumo_i86_manual.state_hash(p_state jsonb)
returns text language sql immutable security invoker set search_path='' as $hash$
 select pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(p_state::text,'UTF8')),'hex')
$hash$;

create function prumo_i86_manual.inspect_subject(p_target uuid)
returns jsonb language plpgsql security invoker set search_path='' as $inspect$
declare value jsonb;
begin
 perform prumo_i86_manual.guard();
 value:=prumo_i86_manual.subject_state(p_target);
 return pg_catalog.jsonb_build_object('version','prumo.i86.manual.v1','state',value,
  'expected_sha256',prumo_i86_manual.state_hash(value),
  'observed_at',pg_catalog.clock_timestamp(),'authorizes_action',false);
end $inspect$;

create function prumo_i86_manual.apply_act(
 p_act uuid,p_action text,p_target uuid,p_expected_sha256 text,
 p_operator_record_ref text,p_manual_record_ref text,p_evidence_sha256 text)
returns jsonb language plpgsql security invoker set search_path=''
set lock_timeout='8s' as $apply$
declare prior prumo_i86_manual.acts%rowtype;payload jsonb;before_state jsonb;
 after_state jsonb;before_hash text;after_hash text;result jsonb;retired integer:=0;
begin
 perform prumo_i86_manual.guard();
 if p_act is null or p_target is null
 or p_action is null or p_action not in('APPOINT','REVOKE','REACTIVATE')
 or p_expected_sha256 is null or p_expected_sha256!~'^[0-9a-f]{64}$'
 or p_operator_record_ref is null or p_operator_record_ref!~'^[A-Za-z0-9._:-]{8,128}$'
 or p_manual_record_ref is null or p_manual_record_ref!~'^[A-Za-z0-9._:-]{8,128}$'
 or p_evidence_sha256 is null or p_evidence_sha256!~'^[0-9a-f]{64}$'
 then raise exception 'I86M_INVALID_MANUAL_ACT' using errcode='22023';end if;
 payload:=pg_catalog.jsonb_build_array(p_action,p_target,p_expected_sha256,
  p_operator_record_ref,p_manual_record_ref,p_evidence_sha256);
 -- These namespace-specific locks never participate in ordinary I79/I80.
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('i86-manual-act|'||p_act::text,0));
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('i86-manual-subject|'||p_target::text,0));
 -- Revocation follows the certified session -> actor -> team -> competence
 -- direction. Table lock prevents phantom session creation during the cut.
 if p_action='REVOKE' then
  lock table auth.sessions in share row exclusive mode;
  perform 1 from auth.sessions where user_id=p_target order by id for update;
 end if;
 -- Auth writers may acquire users before sessions; NEVER wait inversely.
 perform 1 from auth.users where id=p_target for share nowait;
 if not found then raise exception 'I86M_AUTH_IDENTITY_REQUIRED' using errcode='42501';end if;
 perform 1 from public.atores where id=p_target for no key update;
 perform 1 from public.equipe_prumo_s1 where ator_id=p_target for update;
 perform 1 from prumo_private.s1_responsaveis_plataforma where ator_id=p_target for update;
 before_state:=prumo_i86_manual.subject_state(p_target);
 if p_action<>'REVOKE' and not (before_state->>'auth_usable')::boolean
 then raise exception 'I86M_AUTH_IDENTITY_UNUSABLE' using errcode='42501';end if;
 before_hash:=prumo_i86_manual.state_hash(before_state);
 select * into prior from prumo_i86_manual.acts where act_id=p_act;
 if found then
  if prior.payload<>payload then raise exception 'I86M_IDEMPOTENCY_CONFLICT' using errcode='23505';end if;
  if before_hash<>prior.result->>'after_sha256'
  then raise exception 'I86M_ACT_STATE_CHANGED' using errcode='40001';end if;
  return pg_catalog.jsonb_build_object('state','ALREADY_RECORDED_IN_TRANSACTION',
   'caller_commit_required',true,'act',prior.result);
 end if;
 if before_hash<>p_expected_sha256
 then raise exception 'I86M_STALE_CONTEXT' using errcode='40001';end if;
 if p_action='APPOINT' then
  -- No reclassification of established staff or reopening I85 bootstrap.
  if (before_state->>'actor_exists')::boolean or before_state->>'cargo' is not null
  or (before_state->>'competence_exists')::boolean
  then raise exception 'I86M_UNBOUND_IDENTITY_REQUIRED' using errcode='23514';end if;
  insert into public.atores(id) values(p_target);
  insert into prumo_private.s1_responsaveis_plataforma(ator_id) values(p_target);
  insert into public.equipe_prumo_s1(ator_id,cargo,estado) values(p_target,'diretor','ativo');
 else
  if not (before_state->>'actor_exists')::boolean
  or before_state->>'cargo' is distinct from 'diretor'
  or before_state->>'estado' is distinct from 'ativo'
  or not (before_state->>'competence_exists')::boolean
  then raise exception 'I86M_CANONICAL_DIRECTOR_REQUIRED' using errcode='23514';end if;
  if p_action='REVOKE' then
   if not (before_state->>'competence_active')::boolean
   then raise exception 'I86M_ALREADY_INACTIVE_REVIEW_REQUIRED' using errcode='23514';end if;
   update prumo_private.s1_responsaveis_plataforma set ativo=false where ator_id=p_target;
   delete from auth.sessions where user_id=p_target;
   get diagnostics retired=row_count;
  else
   if (before_state->>'competence_active')::boolean
   then raise exception 'I86M_ALREADY_ACTIVE_REVIEW_REQUIRED' using errcode='23514';end if;
   update prumo_private.s1_responsaveis_plataforma set ativo=true where ator_id=p_target;
  end if;
 end if;
 -- Keep original domain and deferred constraints. No SET CONSTRAINTS bypass.
 perform prumo_private.s1_i79_validar_profissional(p_target);
 after_state:=prumo_i86_manual.subject_state(p_target);
 after_hash:=prumo_i86_manual.state_hash(after_state);
 result:=pg_catalog.jsonb_build_object('version','prumo.i86.manual.v1',
  'act_id',p_act::text,'action',p_action,'target_id',p_target::text,
  'before_sha256',before_hash,'after_sha256',after_hash,
  'competence_active',(after_state->>'competence_active')::boolean,
  'retired_session_count',retired,'applied_at',pg_catalog.clock_timestamp());
 insert into prumo_i86_manual.acts(act_id,payload,result) values(p_act,payload,result);
 insert into prumo_i86_manual.audit(act_id,operator_record_ref,manual_record_ref,evidence_sha256,
  sql_session_principal,sql_effective_principal,backend_pid,client_addr)
 values(p_act,p_operator_record_ref,p_manual_record_ref,p_evidence_sha256,
  session_user,current_user,pg_catalog.pg_backend_pid(),pg_catalog.inet_client_addr());
 return pg_catalog.jsonb_build_object('state','RECORDED_IN_TRANSACTION',
  'caller_commit_required',true,'act',result);
end $apply$;

create function prumo_i86_manual.reconcile_act(p_act uuid,p_evidence_sha256 text)
returns jsonb language plpgsql security invoker set search_path='' as $reconcile$
declare prior record;value jsonb;
begin
 perform prumo_i86_manual.guard();
 if p_act is null or p_evidence_sha256 is null or p_evidence_sha256!~'^[0-9a-f]{64}$'
 then raise exception 'I86M_RECONCILE_INPUT_REQUIRED' using errcode='22023';end if;
 -- Wait for an uncertain in-flight act, never execute it again.
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('i86-manual-act|'||p_act::text,0));
 select a.*,u.evidence_sha256 into prior from prumo_i86_manual.acts a
 join prumo_i86_manual.audit u using(act_id) where a.act_id=p_act;
 if not found then
  return pg_catalog.jsonb_build_object('state','NOT_PROVEN','reapplied',false);
 end if;
 if prior.evidence_sha256<>p_evidence_sha256
 then raise exception 'I86M_EVIDENCE_MISMATCH' using errcode='42501';end if;
 -- MVCC cannot expose another transaction's uncommitted ledger row. Reject
 -- our OWN uncommitted act explicitly; no global transaction-status privilege.
 if prior.transaction_xid=pg_catalog.pg_current_xact_id_if_assigned() then
  return pg_catalog.jsonb_build_object('state','COMMIT_NOT_PROVEN','reapplied',false);
 end if;
 value:=prumo_i86_manual.subject_state((prior.result->>'target_id')::uuid);
 if prumo_i86_manual.state_hash(value)<>prior.result->>'after_sha256' then
  return pg_catalog.jsonb_build_object('state','COMMITTED_STATE_CHANGED',
   'act',prior.result,'current_state_matches',false,'reapplied',false);
 end if;
 return pg_catalog.jsonb_build_object('state','COMMITTED_CURRENT_STATE_VERIFIED',
  'act',prior.result,'current_state_matches',true,'reapplied',false);
end $reconcile$;

revoke all on all tables in schema prumo_i86_manual from public,anon,authenticated,
 service_role,prumo_s1_admin_edge_local,prumo_cfi01_pgtest_login;
revoke all on all sequences in schema prumo_i86_manual from public,anon,authenticated,
 service_role,prumo_s1_admin_edge_local,prumo_cfi01_pgtest_login;
revoke all on all functions in schema prumo_i86_manual from public,anon,authenticated,
 service_role,prumo_s1_admin_edge_local,prumo_cfi01_pgtest_login;
commit;
