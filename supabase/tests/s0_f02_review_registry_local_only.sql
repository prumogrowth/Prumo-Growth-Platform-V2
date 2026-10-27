-- Review-request intake ONLY. No operational ratification, C04 plan or send.
-- New disposable local PG17 stack, after the original CFI fixtures.
begin;
do $guard$ begin
 if current_setting('prumo.f02_disposable',true) is distinct from 'YES'
 or current_user<>'postgres' or session_user<>'postgres'
 or current_database()<>'postgres'
 or current_setting('server_version_num')::int/10000<>17
 or to_regprocedure('prumo_private.cfi01_session_valid_local(uuid,uuid)') is null
 then raise exception 'F02_DISPOSABLE_INSTALL_REQUIRED' using errcode='42501';end if;
end $guard$;

create role prumo_s0_f02_review_owner_local nologin noinherit
 nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
grant usage on schema public,prumo_private to prumo_s0_f02_review_owner_local;
grant select(key_id,secret,active),update(key_id)
 on prumo_private.cfi01_signing_keys_local to prumo_s0_f02_review_owner_local;
create policy f02_review_key_read on prumo_private.cfi01_signing_keys_local
 for select to prumo_s0_f02_review_owner_local using(true);
create policy f02_review_key_lock on prumo_private.cfi01_signing_keys_local
 for update to prumo_s0_f02_review_owner_local using(true) with check(false);
grant select(id,lead_id,concessionaria_id) on public.casos_humanos
 to prumo_s0_f02_review_owner_local;
grant select(caso_id,canal_id,concessionaria_id) on public.conversas
 to prumo_s0_f02_review_owner_local;
create policy f02_review_case_read on public.casos_humanos
 for select to prumo_s0_f02_review_owner_local using(true);
create policy f02_review_conversation_read on public.conversas
 for select to prumo_s0_f02_review_owner_local using(true);
do $crypto$
declare v_schema name;
begin
 select n.nspname into v_schema from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace where e.extname='pgcrypto';
 if v_schema is null then raise exception 'PGCRYPTO_REQUIRED';end if;
 execute pg_catalog.format('grant usage on schema %I to prumo_s0_f02_review_owner_local',v_schema);
 execute pg_catalog.format('grant execute on function %I.hmac(bytea,bytea,text),%I.digest(bytea,text) to prumo_s0_f02_review_owner_local',v_schema,v_schema);
end $crypto$;

-- Only a private NOLOGIN definer may reuse the existing signed CFI entry.
-- Temporary installer membership; no permanent application SET ROLE right.
grant prumo_cfi01_atomic_owner_local to postgres with inherit false,set true;
set local role prumo_cfi01_atomic_owner_local;
grant execute on function prumo_private.cfi01_atomic_signed_closure_local(
 text,uuid,uuid,uuid,bigint,uuid,text,uuid,bigint,uuid,text)
 to prumo_s0_f02_review_owner_local;
reset role;
revoke prumo_cfi01_atomic_owner_local from postgres;

create table prumo_private.f02_review_requests_local (
 id uuid primary key default gen_random_uuid(),
 store_id uuid not null,actor_id uuid not null,session_id uuid not null,
 case_id uuid not null,closure_id uuid not null references prumo_private.cfi01_human_closure_events_local(id),
 request_key text not null,body_sha256 text not null,request_sha256 text not null,
 -- Typed F02 claims only: no conversation content, token, secret or proof MAC.
 claimed_body jsonb not null,
 recorded_at timestamptz not null,expires_at timestamptz not null,
 last_checked_at timestamptz not null,
 state text not null check(state in ('PENDING_EVIDENCE','WITHDRAWN','EXPIRED')),
 revision integer not null default 1 check(revision>0),
 unique(store_id,actor_id,request_key),
 check(expires_at>recorded_at and last_checked_at>=recorded_at)
);
create table prumo_private.f02_review_audit_local (
 nonce uuid primary key references prumo_private.cfi01_consumed_nonces_local(nonce),
 request_id uuid not null references prumo_private.f02_review_requests_local(id),
 operation text not null check(operation in ('record','read','withdraw')),
 state text not null check(state in ('PENDING_EVIDENCE','WITHDRAWN','EXPIRED')),
 revision integer not null check(revision>0),server_at timestamptz not null
);
alter table prumo_private.f02_review_requests_local enable row level security;
alter table prumo_private.f02_review_audit_local enable row level security;
revoke all on prumo_private.f02_review_requests_local,prumo_private.f02_review_audit_local
 from public,anon,authenticated,service_role,prumo_cfi01_pgtest_login;
grant select,insert on prumo_private.f02_review_requests_local to prumo_s0_f02_review_owner_local;
grant update(state,revision,last_checked_at) on prumo_private.f02_review_requests_local to prumo_s0_f02_review_owner_local;
grant insert on prumo_private.f02_review_audit_local to prumo_s0_f02_review_owner_local;
create policy f02_review_read on prumo_private.f02_review_requests_local
 for select to prumo_s0_f02_review_owner_local using(true);
create policy f02_review_insert on prumo_private.f02_review_requests_local
 for insert to prumo_s0_f02_review_owner_local with check(true);
create policy f02_review_update on prumo_private.f02_review_requests_local
 for update to prumo_s0_f02_review_owner_local using(true) with check(true);
create policy f02_review_audit_insert on prumo_private.f02_review_audit_local
 for insert to prumo_s0_f02_review_owner_local with check(true);
create function prumo_private.f02_review_guard_update_local()
returns trigger language plpgsql security invoker set search_path='' as $guard$
begin
 if (pg_catalog.to_jsonb(new)-array['state','revision','last_checked_at'])
   is distinct from (pg_catalog.to_jsonb(old)-array['state','revision','last_checked_at'])
 or new.last_checked_at<old.last_checked_at
 or (new.state=old.state and new.revision<>old.revision)
 or (new.state<>old.state and (old.state<>'PENDING_EVIDENCE'
   or new.state not in ('WITHDRAWN','EXPIRED') or new.revision<>old.revision+1))
 then raise exception 'F02_REVIEW_IMMUTABLE_SCOPE_OR_TERMINAL_STATE' using errcode='42501';end if;
 return new;
end $guard$;
revoke all on function prumo_private.f02_review_guard_update_local() from public,anon,authenticated,service_role;
create trigger f02_review_guard_update before update on prumo_private.f02_review_requests_local
 for each row execute function prumo_private.f02_review_guard_update_local();
create trigger f02_review_no_delete before delete or truncate on prumo_private.f02_review_requests_local
 for each statement execute function prumo_private.cfi01_immutable_fact_local();
create trigger f02_review_audit_immutable before update or delete or truncate on prumo_private.f02_review_audit_local
 for each statement execute function prumo_private.cfi01_immutable_fact_local();

create function prumo_private.f02_review_signed_local(
 p_operation text,p_body text,p_expected_revision integer,
 p_actor uuid,p_session uuid,p_case uuid,p_cycle_version bigint,p_event uuid,
 p_capture_key text,p_key_id uuid,p_issued_at bigint,p_nonce uuid,
 p_cfi_mac text,p_review_mac text
) returns table(review_state text,review_id uuid,revision integer,observed_at timestamptz,
 request_sha256 text,expires_at timestamptz,
 state text,event_ref uuid,store_ref uuid,snapshot_sha256 text,message_watermark uuid,
 assignment_ref uuid,cycle_version bigint,message_count integer)
language plpgsql security definer set search_path='' as $fn$
declare v_schema name;v_key bytea;v_hash text;v_mac bytea;v_json jsonb;
 v_cfi record;v_row prumo_private.f02_review_requests_local%rowtype;
 v_now timestamptz;v_start timestamptz;v_end timestamptz;v_result text;
 v_shop uuid;v_lead uuid;v_channel uuid;v_request_key text;v_claim_hash text;
begin
 if session_user<>'prumo_cfi01_pgtest_login'
 or p_operation is null or p_operation not in ('record','read','withdraw')
 or p_body is null or pg_catalog.octet_length(p_body)>8192
 or p_review_mac is null or p_review_mac !~ '^[0-9a-f]{64}$'
 or (p_expected_revision is not null and p_expected_revision<1)
 or (p_operation='withdraw' and p_expected_revision is null)
 then raise exception 'F02_REVIEW_DENIED' using errcode='42501';end if;
 select n.nspname into v_schema from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace where e.extname='pgcrypto';
 select k.secret into v_key from prumo_private.cfi01_signing_keys_local k
 where k.key_id=p_key_id and k.active for share;
 if v_key is null or v_schema is null then
  raise exception 'F02_REVIEW_KEY_DENIED' using errcode='42501';end if;
 execute pg_catalog.format('select pg_catalog.encode(%I.digest(pg_catalog.convert_to($1,''UTF8''),''sha256''),''hex'')',v_schema)
 into v_hash using p_body;
 execute pg_catalog.format('select %I.hmac(pg_catalog.convert_to($1,''UTF8''),$2,''sha256'')',v_schema)
 into v_mac using pg_catalog.concat_ws('|','s0-f02-review-local-v1',p_operation,
  p_actor::text,p_session::text,p_case::text,p_cycle_version::text,p_event::text,
  p_capture_key,p_key_id::text,p_issued_at::text,p_nonce::text,v_hash,
  coalesce(p_expected_revision::text,'-')),v_key;
 if v_mac is distinct from pg_catalog.decode(p_review_mac,'hex') then
  raise exception 'F02_REVIEW_MAC_DENIED' using errcode='42501';end if;
 v_json:=p_body::jsonb;
 if pg_catalog.jsonb_typeof(v_json)<>'object'
 or (select count(*) from pg_catalog.jsonb_object_keys(v_json))<>6
 or not v_json ?& array['schema','request_sha256','evidence','proposal','requested_at','expires_at']
 or v_json->>'schema' is distinct from 'prumo.s0.f02.review.request/0.1-candidate'
 or v_json#>>'{proposal,action}' is distinct from 'REQUEST_S0_HUMAN_RATIFICATION_ONLY'
 or v_json#>>'{evidence,external_disposition}' is distinct from 'EXTERNAL_DISPATCH_UNVERIFIED'
 or v_json#>>'{evidence,human_operational_ratification}' is distinct from 'HUMAN_OPERATIONAL_AUTHORIZATION_NOT_RATIFIED'
 or v_json#>'{evidence,shop_id}' is distinct from v_json#>'{proposal,shop_id}'
 or v_json#>'{evidence,lead_id}' is distinct from v_json#>'{proposal,lead_id}'
 or v_json#>'{evidence,case_id}' is distinct from v_json#>'{proposal,case_id}'
 or v_json#>'{evidence,closure_id}' is distinct from v_json#>'{proposal,closure_id}'
 then raise exception 'F02_REVIEW_INPUT_INVALID' using errcode='42501';end if;
 v_shop:=(v_json#>>'{proposal,shop_id}')::uuid;
 v_lead:=(v_json#>>'{proposal,lead_id}')::uuid;
 v_channel:=(v_json#>>'{proposal,channel_id}')::uuid;
 v_request_key:=v_json#>>'{proposal,idempotency_key}';
 v_claim_hash:=v_json->>'request_sha256';
 v_start:=(v_json->>'requested_at')::timestamptz;
 v_end:=(v_json->>'expires_at')::timestamptz;
 if v_request_key is null or v_request_key !~ '^[A-Za-z0-9._:-]{8,128}$'
 or v_claim_hash is null or v_claim_hash !~ '^[0-9a-f]{64}$'
 or v_shop is null or v_lead is null or v_channel is null
 or (v_json#>>'{proposal,case_id}')::uuid is distinct from p_case
 or (v_json#>>'{proposal,closure_id}')::uuid is distinct from p_event
 or v_start is null or v_end is null or not pg_catalog.isfinite(v_start)
 or not pg_catalog.isfinite(v_end) or v_end<=v_start
 then raise exception 'F02_REVIEW_SCOPE_INVALID' using errcode='42501';end if;

 -- Reuse actual CFI HMAC/nonce, session FOR SHARE, S1, assignment, versions,
 -- messages and immutable receipt. Same connection and same transaction.
 select * into strict v_cfi from prumo_private.cfi01_atomic_signed_closure_local(
  'recheck_human_closure',p_actor,p_session,p_case,p_cycle_version,p_event,
  p_capture_key,p_key_id,p_issued_at,p_nonce,p_cfi_mac);
 if v_cfi.state<>'VERIFIED_REVIEW_ONLY_LOCAL' or v_cfi.store_ref<>v_shop
 or not exists(select 1 from public.casos_humanos h where h.id=p_case
  and h.concessionaria_id=v_shop and h.lead_id=v_lead)
 or not exists(select 1 from public.conversas c where c.caso_id=p_case
  and c.concessionaria_id=v_shop and c.canal_id=v_channel)
 then raise exception 'F02_REVIEW_SCOPE_DENIED' using errcode='42501';end if;

 -- CFI has already serialized the case. New registry row locks come LAST.
 v_now:=pg_catalog.clock_timestamp();
 select r.* into v_row from prumo_private.f02_review_requests_local r
 where r.store_id=v_shop and r.actor_id=p_actor and r.request_key=v_request_key
 for update;
 if not found then
  if p_operation<>'record' then raise exception 'F02_REVIEW_NOT_FOUND' using errcode='P2002';end if;
  if v_end<=v_now then raise exception 'F02_REVIEW_EXPIRED' using errcode='P2001';end if;
  if v_start>v_now then raise exception 'F02_REVIEW_FUTURE_WINDOW' using errcode='22007';end if;
  insert into prumo_private.f02_review_requests_local(
   store_id,actor_id,session_id,case_id,closure_id,request_key,body_sha256,
   request_sha256,claimed_body,recorded_at,expires_at,last_checked_at,state)
  values(v_shop,p_actor,p_session,p_case,p_event,v_request_key,v_hash,
   v_claim_hash,v_json,v_now,v_end,v_now,'PENDING_EVIDENCE') returning * into v_row;
  v_result:='RECORDED_REVIEW_ONLY';
 else
  if v_row.body_sha256<>v_hash or v_row.case_id<>p_case or v_row.closure_id<>p_event
  then raise exception 'F02_REVIEW_KEY_CONFLICT' using errcode='23505';end if;
  if v_now<v_row.last_checked_at then raise exception 'F02_REVIEW_CLOCK_REGRESSION' using errcode='P2003';end if;
  if p_expected_revision>v_row.revision
   or (p_operation='withdraw' and p_expected_revision<>v_row.revision)
  then raise exception 'F02_REVIEW_REVISION_STALE' using errcode='40001';end if;
  if v_row.state='PENDING_EVIDENCE' and (p_operation='withdraw' or v_now>=v_row.expires_at) then
   v_row.state:=case when v_now>=v_row.expires_at then 'EXPIRED' else 'WITHDRAWN' end;
   v_row.revision:=v_row.revision+1;
  end if;
  update prumo_private.f02_review_requests_local r
  set state=v_row.state,revision=v_row.revision,last_checked_at=v_now where r.id=v_row.id;
  v_result:=case when v_row.state='WITHDRAWN' then 'WITHDRAWN_REVIEW_ONLY'
   when v_row.state='EXPIRED' then 'EXPIRED_REVIEW_ONLY'
   when p_operation='record' then 'REPLAY_REVIEW_ONLY' else 'CURRENT_REVIEW_ONLY' end;
 end if;
 insert into prumo_private.f02_review_audit_local(nonce,request_id,operation,state,revision,server_at)
 values(p_nonce,v_row.id,p_operation,v_row.state,v_row.revision,v_now);
 return query select v_result,v_row.id,v_row.revision,v_now,v_row.request_sha256,v_row.expires_at,
  v_cfi.state,v_cfi.event_ref,v_cfi.store_ref,v_cfi.snapshot_sha256,
  v_cfi.message_watermark,v_cfi.assignment_ref,v_cfi.cycle_version,v_cfi.message_count;
end $fn$;
revoke all on function prumo_private.f02_review_signed_local(
 text,text,integer,uuid,uuid,uuid,bigint,uuid,text,uuid,bigint,uuid,text,text)
 from public,anon,authenticated,service_role;
grant execute on function prumo_private.f02_review_signed_local(
 text,text,integer,uuid,uuid,uuid,bigint,uuid,text,uuid,bigint,uuid,text,text)
 to prumo_cfi01_pgtest_login;
grant create on schema prumo_private to prumo_s0_f02_review_owner_local;
grant prumo_s0_f02_review_owner_local to postgres with inherit false,set true;
alter function prumo_private.f02_review_signed_local(
 text,text,integer,uuid,uuid,uuid,bigint,uuid,text,uuid,bigint,uuid,text,text)
 owner to prumo_s0_f02_review_owner_local;
revoke prumo_s0_f02_review_owner_local from postgres;
revoke create on schema prumo_private from prumo_s0_f02_review_owner_local;
commit;
