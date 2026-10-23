-- WA40 / S0-044: synthetic M2M receipt with PostgreSQL HMAC+nonce+S0-043 append.
-- OFFLINE PG17 ONLY. No operational LOGIN, vault key, Supabase deployment,
-- Meta webhook/API, Graph send, Meta ACK, service account provisioning.
-- Do not reuse GoTrue human S0/025 signatures/keys or S1 user roles.

do $wa40_role$
begin
 if current_user <> 'postgres' then
  raise exception 'WA40_LOCAL_MIGRATION_ONLY' using errcode='42501';
 end if;
 if not exists(select 1 from pg_catalog.pg_roles
   where rolname='prumo_s0_meta_ingress_lab') then
  create role prumo_s0_meta_ingress_lab
   nologin noinherit nosuperuser nocreatedb nocreaterole
   noreplication nobypassrls;
 end if;
 if not exists(select 1 from pg_catalog.pg_roles
  where rolname='prumo_s0_meta_ingress_lab' and not rolcanlogin
   and not rolinherit and not rolsuper and not rolcreatedb
   and not rolcreaterole and not rolreplication and not rolbypassrls)
 then raise exception 'UNSAFE_META_INGRESS_ROLE' using errcode='42501';end if;
 if exists(select 1 from pg_catalog.pg_auth_members am
  join pg_catalog.pg_roles r on r.oid=am.member
  where am.roleid='prumo_s0_meta_ingress_lab'::regrole
   and r.rolname not in ('postgres','supabase_admin'))
 then raise exception 'META_INGRESS_ROLE_DELEGATED' using errcode='42501';end if;
end $wa40_role$;
grant usage on schema prumo_private to prumo_s0_meta_ingress_lab;

create table prumo_private.meta_servico_chaves_fixture_s0 (
 chave_id uuid primary key,
 app_technical_ref text not null check(app_technical_ref ~ '^[0-9]{5,25}$'),
 segredo bytea not null check(octet_length(segredo) between 32 and 128),
 valido_desde timestamptz not null,
 valido_ate timestamptz not null,
 ativo boolean not null default false,
 check(valido_ate>valido_desde)
);
create table prumo_private.meta_servico_nonces_fixture_s0 (
 nonce uuid primary key,
 chave_id uuid not null references prumo_private.meta_servico_chaves_fixture_s0(chave_id),
 consumido_em timestamptz not null default clock_timestamp()
);
alter table prumo_private.meta_servico_chaves_fixture_s0 enable row level security;
alter table prumo_private.meta_servico_nonces_fixture_s0 enable row level security;
revoke all on prumo_private.meta_servico_chaves_fixture_s0,
 prumo_private.meta_servico_nonces_fixture_s0
 from public,anon,authenticated,service_role,prumo_s0_gateway,
 prumo_s0_signer,prumo_s0_signed_executor,prumo_s0_meta_ingress_lab;

-- Canonical unambiguous encoding: caller text fields are validated before
-- verification; none permit a '|'. Signed material includes ALL scope fields,
-- purpose, key ID, UNIX issue time and nonce. This is a LAB protocol, NOT WA34
-- wire compatibility and not proof Meta's own webhook HMAC was verified.
create function prumo_private.meta_material_handoff_fixture_s0(
 p_chave uuid,p_app text,p_waba text,p_phone text,p_canal uuid,
 p_intencao uuid,p_attempt text,p_correlation text,p_recipient text,
 p_wamid text,p_event text,p_kind text,p_body_hash text,
 p_emitido bigint,p_nonce uuid
) returns text language sql immutable set search_path='' as $wa40_m$
 select pg_catalog.concat_ws('|','prumo-meta-handoff-lab-v1','FORENSIC_APPEND_ONLY',
 p_chave::text,p_app,p_waba,p_phone,p_canal::text,p_intencao::text,
 p_attempt,p_correlation,p_recipient,p_wamid,p_event,p_kind,p_body_hash,
 p_emitido::text,p_nonce::text)
$wa40_m$;
revoke all on function prumo_private.meta_material_handoff_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid)
 from public,anon,authenticated,service_role,prumo_s0_gateway,
 prumo_s0_signer,prumo_s0_signed_executor,prumo_s0_meta_ingress_lab;

-- This SECURITY DEFINER mock boundary runs as postgres only in the PG17
-- disposable fixture. The caller must have the NONLOGIN lab role AND a
-- separately-held (fictional) HMAC. No role grants for underlying tables.
-- A real service identity and least-privileged owner remain BLOCKING.
create function prumo_private.meta_arquivar_handoff_assinado_fixture_s0(
 p_chave uuid,p_app text,p_waba text,p_phone text,p_canal uuid,
 p_intencao uuid,p_attempt text,p_correlation text,p_recipient text,
 p_wamid text,p_event text,p_kind text,p_body_hash text,
 p_emitido bigint,p_nonce uuid,p_mac text
) returns jsonb language plpgsql security definer set search_path='' as $wa40$
declare v_key bytea;v_now bigint;v_since timestamptz;
 v_exp timestamptz;v_secret_schema name;v_expected bytea;v_text text;
 v_used uuid;v_out jsonb;
begin
 -- Real SET ROLE is simulated in PG17. We never authorize PUBLIC, JWT or S1
 -- user roles. session_user remains postgres during this synthetic test.
 if session_user <> 'postgres' or
    current_setting('role') <> 'prumo_s0_meta_ingress_lab'
 then raise exception 'META_SERVICE_ROLE_DENIED' using errcode='42501';end if;
 if p_chave is null or p_canal is null or p_intencao is null
  or p_nonce is null or p_emitido is null
  or p_app is null or p_app !~ '^[0-9]{5,25}$'
  or p_waba is null or p_waba !~ '^[0-9]{5,25}$'
  or p_phone is null or p_phone !~ '^[0-9]{5,25}$'
  or p_attempt is null or p_attempt !~ '^[A-Za-z0-9_.:-]{1,128}$'
  or p_correlation is null or p_correlation !~ '^[A-Za-z0-9_.:-]{1,128}$'
  or p_recipient is null or p_recipient !~ '^[0-9]{8,15}$'
  or p_wamid is null or p_wamid !~ '^wamid\.[A-Za-z0-9+/_=:.-]+$'
  or length(p_wamid) not between 7 and 1030
  or p_event is null or p_event !~ '^[A-Za-z0-9_.:-]{1,128}$'
  or p_kind is null or p_kind not in ('sent','delivered','read','failed')
  or p_body_hash is null or p_body_hash !~ '^[a-f0-9]{64}$'
  or p_mac is null or p_mac !~ '^[a-f0-9]{64}$'
 then raise exception 'META_HANDOFF_INVALID' using errcode='42501';end if;

 v_now:=extract(epoch from pg_catalog.clock_timestamp())::bigint;
 if p_emitido < v_now-30 or p_emitido > v_now+5 then
  raise exception 'META_HANDOFF_EXPIRED' using errcode='42501';end if;

 -- Locked key forces revoke (by postgres) to serialize with verification.
 select k.segredo,k.valido_desde,k.valido_ate
 into v_key,v_since,v_exp
 from prumo_private.meta_servico_chaves_fixture_s0 k
 where k.chave_id=p_chave and k.app_technical_ref=p_app and k.ativo
 for share;
 if not found or v_since>pg_catalog.to_timestamp(p_emitido)
  or v_exp<=pg_catalog.clock_timestamp()
 then raise exception 'META_HANDOFF_KEY_DENIED' using errcode='42501';end if;

 select n.nspname into v_secret_schema
 from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace
 where e.extname='pgcrypto';
 if v_secret_schema is null then
  raise exception 'META_HMAC_UNAVAILABLE' using errcode='42501';end if;
 v_text:=prumo_private.meta_material_handoff_fixture_s0(
  p_chave,p_app,p_waba,p_phone,p_canal,p_intencao,p_attempt,
  p_correlation,p_recipient,p_wamid,p_event,p_kind,p_body_hash,p_emitido,p_nonce);
 execute pg_catalog.format('select %I.hmac($1,$2,''sha256'')',
   v_secret_schema) into v_expected using
   pg_catalog.convert_to(v_text,'UTF8'),v_key;
 if v_expected is distinct from pg_catalog.decode(p_mac,'hex') then
  raise exception 'META_HANDOFF_BAD_MAC' using errcode='42501';end if;

 insert into prumo_private.meta_servico_nonces_fixture_s0(nonce,chave_id)
 values(p_nonce,p_chave) on conflict do nothing returning nonce into v_used;
 if v_used is null then
  raise exception 'META_HANDOFF_REPLAY' using errcode='42501';end if;
 v_out:=prumo_private.archivar_status_meta_tecnico_fixture_s0(
  p_app,p_waba,p_phone,p_canal,p_intencao,p_attempt,p_correlation,
  p_recipient,p_wamid,p_event,p_kind,p_body_hash);
 if v_out->>'outcome'='LAB_SCOPE_DENIED' then
  raise exception 'META_HANDOFF_SCOPE_DENIED' using errcode='42501';end if;
 if v_out->>'outcome' not in (
  'LAB_OBSERVED_UNVERIFIED','LAB_LATE_UNVERIFIED','LAB_EXACT_BODY_REPLAY',
  'LAB_BODY_VARIANT_QUARANTINED','LAB_KIND_CONFLICT_QUARANTINED') then
  raise exception 'META_HANDOFF_UNEXPECTED_RESULT' using errcode='42501';end if;
 -- Same transaction: any exception rolls back nonce + forensic append.
 return v_out || pg_catalog.jsonb_build_object(
  'service_authenticated',false,'s0_production_authorized',false,
  'handoff_contract','WA40_PG17_LAB_ONLY');
end $wa40$;

revoke all on function prumo_private.meta_arquivar_handoff_assinado_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s0_gateway,
 prumo_s0_signer,prumo_s0_signed_executor,prumo_s0_meta_ingress_lab;
grant execute on function prumo_private.meta_arquivar_handoff_assinado_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 to prumo_s0_meta_ingress_lab;

-- Never make a permanent DB login for this role. Supabase service_role is
-- intentionally NOT granted this function. This migration remains local only.
