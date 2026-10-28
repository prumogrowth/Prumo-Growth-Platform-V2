-- I86 lab evidence only. Not a migration, domain command or hosted installer.
do $guard$
begin
 if current_user<>'postgres' or session_user<>'postgres'
 or current_setting('server_version_num')::int/10000<>17
 or coalesce((select shobj_description(oid,'pg_database') from pg_database
     where datname=current_database()) like 'PRUMO_I84_DISPOSABLE:%',false) is not true
 then raise exception 'I86_OWNED_DISPOSABLE_INSTALLER_REQUIRED' using errcode='42501';end if;
end $guard$;
create schema prumo_i86_lab;
revoke all on schema prumo_i86_lab from public,anon,authenticated,service_role,
 prumo_s1_admin_edge_local;
create table prumo_i86_lab.observations(
 id uuid primary key,
 actor_id uuid not null,
 session_id uuid not null,
 request_key text not null check(request_key ~ '^[A-Za-z0-9._:-]{8,128}$'),
 request jsonb not null,
 state jsonb not null,
 state_sha256 text not null check(state_sha256 ~ '^[0-9a-f]{64}$'),
 observed_at timestamptz not null,
 governance_state text not null check(governance_state='PENDING_DECISION'),
 unique(actor_id,session_id,request_key)
);
create table prumo_i86_lab.audit(
 id bigint generated always as identity primary key,
 observation_id uuid not null references prumo_i86_lab.observations(id),
 event text not null check(event in('OBSERVED','OBSERVATION_REPLAYED')),
 recorded_at timestamptz not null default clock_timestamp()
);
alter table prumo_i86_lab.observations enable row level security;
alter table prumo_i86_lab.observations force row level security;
alter table prumo_i86_lab.audit enable row level security;
alter table prumo_i86_lab.audit force row level security;
create function prumo_i86_lab.immutable() returns trigger
language plpgsql security invoker set search_path='' as $immutable$
begin
 raise exception 'I86_EVIDENCE_IMMUTABLE' using errcode='42501';
end $immutable$;
create trigger immutable_rows before update or delete on prumo_i86_lab.observations
 for each statement execute function prumo_i86_lab.immutable();
create trigger immutable_truncate before truncate on prumo_i86_lab.observations
 for each statement execute function prumo_i86_lab.immutable();
create trigger immutable_rows before update or delete on prumo_i86_lab.audit
 for each statement execute function prumo_i86_lab.immutable();
create trigger immutable_truncate before truncate on prumo_i86_lab.audit
 for each statement execute function prumo_i86_lab.immutable();
revoke all on all tables in schema prumo_i86_lab from public,anon,authenticated,
 service_role,prumo_s1_admin_edge_local;
revoke all on all sequences in schema prumo_i86_lab from public,anon,authenticated,
 service_role,prumo_s1_admin_edge_local;
revoke all on all functions in schema prumo_i86_lab from public,anon,authenticated,
 service_role,prumo_s1_admin_edge_local;
