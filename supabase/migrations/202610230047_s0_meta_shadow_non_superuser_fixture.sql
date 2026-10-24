-- WA48/S0-047: offline PostgreSQL 17 shadow M2M, no hosted deployment.
-- Additive: WA39-47 production-ineligible contracts remain untouched.
do $wa48$
begin
 if current_user <> 'postgres' or current_database() <> 'prumo_s0_test_ci'
 then raise exception 'WA48_OFFLINE_ONLY' using errcode='42501';end if;
 create role prumo_s0_meta_wa48_executor_lab nologin noinherit
  nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
 create role prumo_s0_meta_wa48_client_lab nologin noinherit
  nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
 grant prumo_s0_meta_wa48_executor_lab to postgres with inherit false,set true;
end $wa48$;
create table prumo_private.meta_wa48_shadow_keys_fixture_s0(
 key_id uuid primary key, app text not null check(app ~ '^[0-9]{5,25}$'),
 secret bytea not null check(octet_length(secret) between 32 and 128),
 active boolean not null, valid_from timestamptz not null,
 valid_until timestamptz not null,check(valid_until>valid_from));
create table prumo_private.meta_wa48_shadow_nonces_fixture_s0(
 nonce uuid primary key,key_id uuid not null references
 prumo_private.meta_wa48_shadow_keys_fixture_s0(key_id));
create table prumo_private.meta_wa48_shadow_receipts_fixture_s0(
 key_id uuid not null references prumo_private.meta_wa48_shadow_keys_fixture_s0(key_id),
 event_ref text not null,body_hash text not null,kind text not null,
 ack_allowed boolean not null default false check(not ack_allowed),
 send_authorized boolean not null default false check(not send_authorized),
 production_authorized boolean not null default false check(not production_authorized),
 primary key(key_id,event_ref,body_hash));
alter table prumo_private.meta_wa48_shadow_keys_fixture_s0 enable row level security;
alter table prumo_private.meta_wa48_shadow_nonces_fixture_s0 enable row level security;
alter table prumo_private.meta_wa48_shadow_receipts_fixture_s0 enable row level security;
grant usage on schema prumo_private to prumo_s0_meta_wa48_client_lab,prumo_s0_meta_wa48_executor_lab;
grant select(key_id,app,secret,active,valid_from,valid_until)
 on prumo_private.meta_wa48_shadow_keys_fixture_s0 to prumo_s0_meta_wa48_executor_lab;
grant insert(nonce,key_id),select(nonce) on prumo_private.meta_wa48_shadow_nonces_fixture_s0
 to prumo_s0_meta_wa48_executor_lab;
grant select(key_id,event_ref,body_hash,kind),insert(key_id,event_ref,body_hash,kind)
 on prumo_private.meta_wa48_shadow_receipts_fixture_s0 to prumo_s0_meta_wa48_executor_lab;
create policy wa48_key_read on prumo_private.meta_wa48_shadow_keys_fixture_s0
 for select to prumo_s0_meta_wa48_executor_lab using(true);
create policy wa48_nonce_insert on prumo_private.meta_wa48_shadow_nonces_fixture_s0
 for insert to prumo_s0_meta_wa48_executor_lab with check(true);
create policy wa48_nonce_read on prumo_private.meta_wa48_shadow_nonces_fixture_s0
 for select to prumo_s0_meta_wa48_executor_lab using(true);
create policy wa48_receipt_read on prumo_private.meta_wa48_shadow_receipts_fixture_s0
 for select to prumo_s0_meta_wa48_executor_lab using(true);
create policy wa48_receipt_insert on prumo_private.meta_wa48_shadow_receipts_fixture_s0
 for insert to prumo_s0_meta_wa48_executor_lab with check(true);
grant execute on function prumo_private.meta_material_handoff_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid)
 to prumo_s0_meta_wa48_executor_lab;
do $wa48_ext$
declare s name;
begin
 select n.nspname into s from pg_extension e join pg_namespace n
 on n.oid=e.extnamespace where e.extname='pgcrypto';
 if s is null then raise exception 'WA48_MISSING_PGCRYPTO';end if;
 execute format('grant usage on schema %I to prumo_s0_meta_wa48_executor_lab',s);
 execute format('grant execute on function %I.hmac(bytea,bytea,text) to prumo_s0_meta_wa48_executor_lab',s);
end $wa48_ext$;
grant create on schema prumo_private to prumo_s0_meta_wa48_executor_lab;
set role prumo_s0_meta_wa48_executor_lab;
create function prumo_private.meta_wa48_shadow_append_fixture_s0(
 p_key uuid,p_app text,p_waba text,p_phone text,p_channel uuid,
 p_intent uuid,p_attempt text,p_corr text,p_recipient text,p_wamid text,
 p_event text,p_kind text,p_hash text,p_issued bigint,p_nonce uuid,p_mac text)
returns jsonb language plpgsql security definer set search_path='' as $wa48_func$
declare secret_value bytea;v_from timestamptz;v_until timestamptz;
 v_expected bytea;v_schema name;v_nonce uuid;v_kind text;v_result text;
 v_now bigint;
begin
 if session_user <> 'prumo_s0_meta_wa48_client_lab' then
  raise exception 'WA48_LOGIN_DENIED' using errcode='42501';end if;
 if p_key is null or p_nonce is null or p_issued is null or
 p_mac is null or p_mac !~ '^[0-9a-f]{64}$'
 or p_app is null or p_app !~ '^[0-9]{5,25}$'
 or p_waba is null or p_waba !~ '^[0-9]{5,25}$'
 or p_phone is null or p_phone !~ '^[0-9]{5,25}$'
 or p_channel is null or p_intent is null
 or p_attempt is null or p_attempt !~ '^[A-Za-z0-9_.:-]{1,128}$'
 or p_corr is null or p_corr !~ '^[A-Za-z0-9_.:-]{1,128}$'
 or p_recipient is null or p_recipient !~ '^[0-9]{8,15}$'
 or p_wamid is null or p_wamid !~ '^wamid\.[A-Za-z0-9+/_=:.-]+
 or p_event is null or p_event !~ '^[A-Za-z0-9_.:-]{1,128}$'
 or p_kind is null or p_kind not in ('sent','delivered','read','failed')
 or p_hash is null or p_hash !~ '^[0-9a-f]{64}$'
 then raise exception 'WA48_INVALID' using errcode='42501';end if;
 v_now:=extract(epoch from clock_timestamp())::bigint;
 if p_issued < v_now-30 or p_issued > v_now+5 then
  raise exception 'WA48_EXPIRED' using errcode='42501';end if;
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended('wa48-key:'||p_key::text,48));
 select secret,valid_from,valid_until into secret_value,v_from,v_until
 from prumo_private.meta_wa48_shadow_keys_fixture_s0
 where key_id=p_key and app=p_app and active;
 if not found or v_from>pg_catalog.to_timestamp(p_issued)
 or v_until<=clock_timestamp() then
  raise exception 'WA48_KEY_DENIED' using errcode='42501';end if;
 select n.nspname into v_schema from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace where e.extname='pgcrypto';
 execute pg_catalog.format('select %I.hmac($1,$2,''sha256'')',v_schema)
 into v_expected using pg_catalog.convert_to(
  prumo_private.meta_material_handoff_fixture_s0(p_key,p_app,p_waba,p_phone,
  p_channel,p_intent,p_attempt,p_corr,p_recipient,p_wamid,p_event,p_kind,
  p_hash,p_issued,p_nonce),'UTF8'),secret_value;
 if v_expected is distinct from pg_catalog.decode(p_mac,'hex') then
  raise exception 'WA48_MAC_DENIED' using errcode='42501';end if;
 insert into prumo_private.meta_wa48_shadow_nonces_fixture_s0(nonce,key_id)
 values(p_nonce,p_key) on conflict do nothing returning nonce into v_nonce;
 if v_nonce is null then raise exception 'WA48_REPLAY' using errcode='42501';end if;
 select kind into v_kind from prumo_private.meta_wa48_shadow_receipts_fixture_s0
 where key_id=p_key and event_ref=p_event and body_hash=p_hash;
 if found then
  if v_kind<>p_kind then raise exception 'WA48_KIND_CONFLICT' using errcode='42501';end if;
  v_result:='LAB_EXACT_REPLAY';
 else
  select case when exists(select 1 from
   prumo_private.meta_wa48_shadow_receipts_fixture_s0
   where key_id=p_key and event_ref=p_event)
   then 'LAB_BODY_VARIANT_QUARANTINED' else 'LAB_SHADOW_OBSERVED' end into v_result;
  insert into prumo_private.meta_wa48_shadow_receipts_fixture_s0(
   key_id,event_ref,body_hash,kind) values(p_key,p_event,p_hash,p_kind);
 end if;
 return pg_catalog.jsonb_build_object('outcome',v_result,'lab_only',true,
  'service_authenticated',false,'ack_allowed',false,
  'send_authorized',false,'retry_external',false,
  'production_authorized',false,'delivery_confirmed',false,
  'case_transition_authorized',false,'s0_write_authorized',false);
end $wa48_func$;
reset role;
revoke create on schema prumo_private from prumo_s0_meta_wa48_executor_lab;
revoke all on function prumo_private.meta_wa48_shadow_append_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s0_meta_ingress_lab,
 prumo_s0_meta_wa48_executor_lab;
grant execute on function prumo_private.meta_wa48_shadow_append_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 to prumo_s0_meta_wa48_client_lab;
-- ADMIN-only revocation respects same transaction-scoped advisory key lock.
create function prumo_private.meta_wa48_shadow_revoke_fixture_s0(p_key uuid)
returns text language plpgsql security invoker set search_path='' as $wa48_revoke$
declare a boolean;
begin
 if current_user<>'postgres' or current_database()<>'prumo_s0_test_ci'
 then raise exception 'WA48_ADMIN_ONLY' using errcode='42501';end if;
 perform pg_catalog.pg_advisory_xact_lock(
 pg_catalog.hashtextextended('wa48-key:'||p_key::text,48));
 select active into a from prumo_private.meta_wa48_shadow_keys_fixture_s0
 where key_id=p_key for update;
 if not found then raise exception 'WA48_UNKNOWN_KEY' using errcode='42501';end if;
 if not a then return 'LAB_ALREADY_REVOKED';end if;
 update prumo_private.meta_wa48_shadow_keys_fixture_s0 set active=false where key_id=p_key;
 return 'LAB_REVOKED';
end $wa48_revoke$;
revoke all on function prumo_private.meta_wa48_shadow_revoke_fixture_s0(uuid)
 from public,anon,authenticated,service_role,
 prumo_s0_meta_wa48_client_lab,prumo_s0_meta_wa48_executor_lab;

 or pg_catalog.length(p_wamid) not between 7 and 1030
 or p_event is null or p_event !~ '^[A-Za-z0-9_.:-]{1,128}$'
 or p_kind is null or p_kind not in ('sent','delivered','read','failed')
 or p_hash is null or p_hash !~ '^[0-9a-f]{64}$'
 then raise exception 'WA48_INVALID' using errcode='42501';end if;
 v_now:=extract(epoch from clock_timestamp())::bigint;
 if p_issued < v_now-30 or p_issued > v_now+5 then
  raise exception 'WA48_EXPIRED' using errcode='42501';end if;
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended('wa48-key:'||p_key::text,48));
 select secret,valid_from,valid_until into secret_value,v_from,v_until
 from prumo_private.meta_wa48_shadow_keys_fixture_s0
 where key_id=p_key and app=p_app and active;
 if not found or v_from>pg_catalog.to_timestamp(p_issued)
 or v_until<=clock_timestamp() then
  raise exception 'WA48_KEY_DENIED' using errcode='42501';end if;
 select n.nspname into v_schema from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace where e.extname='pgcrypto';
 execute pg_catalog.format('select %I.hmac($1,$2,''sha256'')',v_schema)
 into v_expected using pg_catalog.convert_to(
  prumo_private.meta_material_handoff_fixture_s0(p_key,p_app,p_waba,p_phone,
  p_channel,p_intent,p_attempt,p_corr,p_recipient,p_wamid,p_event,p_kind,
  p_hash,p_issued,p_nonce),'UTF8'),secret_value;
 if v_expected is distinct from pg_catalog.decode(p_mac,'hex') then
  raise exception 'WA48_MAC_DENIED' using errcode='42501';end if;
 insert into prumo_private.meta_wa48_shadow_nonces_fixture_s0(nonce,key_id)
 values(p_nonce,p_key) on conflict do nothing returning nonce into v_nonce;
 if v_nonce is null then raise exception 'WA48_REPLAY' using errcode='42501';end if;
 select kind into v_kind from prumo_private.meta_wa48_shadow_receipts_fixture_s0
 where key_id=p_key and event_ref=p_event and body_hash=p_hash;
 if found then
  if v_kind<>p_kind then raise exception 'WA48_KIND_CONFLICT' using errcode='42501';end if;
  v_result:='LAB_EXACT_REPLAY';
 else
  select case when exists(select 1 from
   prumo_private.meta_wa48_shadow_receipts_fixture_s0
   where key_id=p_key and event_ref=p_event)
   then 'LAB_BODY_VARIANT_QUARANTINED' else 'LAB_SHADOW_OBSERVED' end into v_result;
  insert into prumo_private.meta_wa48_shadow_receipts_fixture_s0(
   key_id,event_ref,body_hash,kind) values(p_key,p_event,p_hash,p_kind);
 end if;
 return pg_catalog.jsonb_build_object('outcome',v_result,'lab_only',true,
  'service_authenticated',false,'ack_allowed',false,
  'send_authorized',false,'retry_external',false,
  'production_authorized',false,'delivery_confirmed',false,
  'case_transition_authorized',false,'s0_write_authorized',false);
end $wa48_func$;
reset role;
revoke create on schema prumo_private from prumo_s0_meta_wa48_executor_lab;
revoke all on function prumo_private.meta_wa48_shadow_append_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s0_meta_ingress_lab,
 prumo_s0_meta_wa48_executor_lab;
grant execute on function prumo_private.meta_wa48_shadow_append_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 to prumo_s0_meta_wa48_client_lab;
-- ADMIN-only revocation respects same transaction-scoped advisory key lock.
create function prumo_private.meta_wa48_shadow_revoke_fixture_s0(p_key uuid)
returns text language plpgsql security invoker set search_path='' as $wa48_revoke$
declare a boolean;
begin
 if current_user<>'postgres' or current_database()<>'prumo_s0_test_ci'
 then raise exception 'WA48_ADMIN_ONLY' using errcode='42501';end if;
 perform pg_catalog.pg_advisory_xact_lock(
 pg_catalog.hashtextextended('wa48-key:'||p_key::text,48));
 select active into a from prumo_private.meta_wa48_shadow_keys_fixture_s0
 where key_id=p_key for update;
 if not found then raise exception 'WA48_UNKNOWN_KEY' using errcode='42501';end if;
 if not a then return 'LAB_ALREADY_REVOKED';end if;
 update prumo_private.meta_wa48_shadow_keys_fixture_s0 set active=false where key_id=p_key;
 return 'LAB_REVOKED';
end $wa48_revoke$;
revoke all on function prumo_private.meta_wa48_shadow_revoke_fixture_s0(uuid)
 from public,anon,authenticated,service_role,
 prumo_s0_meta_wa48_client_lab,prumo_s0_meta_wa48_executor_lab;
