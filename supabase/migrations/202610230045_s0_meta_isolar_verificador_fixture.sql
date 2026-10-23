-- S0/045 WA41: narrow offline Meta HMAC verifier; preserve WA40 protocol.
-- Isolates access to internal test keys and nonce; leaves the S0-043
-- domain append intentionally postgres-owned. NOT operational M2M/IAM.
-- Do not apply this laboratory migration to hosted Supabase.
do $wa41_role$
begin
 if current_user <> 'postgres' then
  raise exception 'WA41_LOCAL_MIGRATION_ONLY' using errcode='42501';
 end if;
 if not exists(select 1 from pg_catalog.pg_roles
  where rolname='prumo_s0_meta_signer_lab') then
  create role prumo_s0_meta_signer_lab nologin noinherit
   nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
 end if;
 if not exists(select 1 from pg_catalog.pg_roles
  where rolname='prumo_s0_meta_signer_lab'
   and not rolcanlogin and not rolinherit and not rolsuper
   and not rolcreatedb and not rolcreaterole and not rolreplication
   and not rolbypassrls)
 then raise exception 'WA41_UNSAFE_SIGNER_ROLE' using errcode='42501';end if;
 if exists(select 1 from pg_catalog.pg_auth_members am
  join pg_catalog.pg_roles m on m.oid=am.member
  where am.roleid='prumo_s0_meta_signer_lab'::regrole
   and m.rolname not in ('postgres','supabase_admin'))
 then raise exception 'WA41_SIGNER_GRANTED_UNTRUSTED' using errcode='42501';end if;
 execute 'grant prumo_s0_meta_signer_lab to postgres with inherit false, set true';
end $wa41_role$;

grant usage on schema prumo_private to prumo_s0_meta_signer_lab;
grant select(chave_id,app_technical_ref,segredo,valido_desde,valido_ate,ativo)
 on prumo_private.meta_servico_chaves_fixture_s0
 to prumo_s0_meta_signer_lab;
grant insert(nonce,chave_id),select(nonce)
 on prumo_private.meta_servico_nonces_fixture_s0
 to prumo_s0_meta_signer_lab;
-- PostgreSQL RLS is enabled; explicitly allow the narrow role to read
-- synthetic keys and insert/observe its synthetic replay nonces. No UPDATE.
create policy wa41_signer_keys_select on prumo_private.meta_servico_chaves_fixture_s0
 for select to prumo_s0_meta_signer_lab using (true);
create policy wa41_signer_nonces_insert on prumo_private.meta_servico_nonces_fixture_s0
 for insert to prumo_s0_meta_signer_lab with check (true);
create policy wa41_signer_nonces_select on prumo_private.meta_servico_nonces_fixture_s0
 for select to prumo_s0_meta_signer_lab using (true);
grant execute on function prumo_private.meta_material_handoff_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid)
 to prumo_s0_meta_signer_lab;

-- The signer is permitted ONLY this private HMAC verification and nonce
-- insertion. No S0 commercial, audit, inbox, WA39 or sending privileges.
do $wa41_crypto$
declare v_schema name;
begin
 select n.nspname into v_schema from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace
 where e.extname='pgcrypto';
 if v_schema is null then
  raise exception 'WA41_PGCRYPTO_MISSING' using errcode='42501';end if;
 execute pg_catalog.format(
  'grant usage on schema %I to prumo_s0_meta_signer_lab',v_schema);
 execute pg_catalog.format(
  'grant execute on function %I.hmac(bytea,bytea,text) to prumo_s0_meta_signer_lab',v_schema);
end $wa41_crypto$;

create function prumo_private.meta_verificar_handoff_fixture_s0(
 p_chave uuid,p_app text,p_waba text,p_phone text,p_canal uuid,
 p_intencao uuid,p_attempt text,p_correlation text,p_recipient text,
 p_wamid text,p_event text,p_kind text,p_body_hash text,
 p_emitido bigint,p_nonce uuid,p_mac text
) returns void language plpgsql security definer set search_path='' as $wa41_v$
declare v_secret bytea;v_from timestamptz;v_to timestamptz;
 v_now bigint;v_schema name;v_expected bytea;v_used uuid;
begin
 -- Outside the authorized outer WA40 wrapper, there is no signer entry.
 -- Synthetic PG17 SET ROLE is not an actual login authentication method.
 if session_user<>'postgres' or
  current_setting('role')<>'prumo_s0_meta_ingress_lab'
 then raise exception 'WA41_ROLE_DENIED' using errcode='42501';end if;
 if p_chave is null or p_nonce is null or p_emitido is null
  or p_mac is null or p_mac !~ '^[0-9a-f]{64}$'
 then raise exception 'WA41_INVALID' using errcode='42501';end if;
 v_now:=extract(epoch from pg_catalog.clock_timestamp())::bigint;
 if p_emitido<v_now-30 or p_emitido>v_now+5 then
  raise exception 'META_HANDOFF_EXPIRED' using errcode='42501';end if;
 -- Lock protocol for key revocation must be ratified before deployment.
 -- This SELECT intentionally avoids FOR SHARE: it would require UPDATE
 -- privileges on secret-bearing rows. Local CI also tests revoke cases.
 select segredo,valido_desde,valido_ate into v_secret,v_from,v_to
 from prumo_private.meta_servico_chaves_fixture_s0
 where chave_id=p_chave and app_technical_ref=p_app and ativo;
 if not found or v_from>pg_catalog.to_timestamp(p_emitido)
  or v_to<=pg_catalog.clock_timestamp() then
  raise exception 'META_HANDOFF_KEY_DENIED' using errcode='42501';end if;
 select n.nspname into v_schema from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace
 where e.extname='pgcrypto';
 if v_schema is null then raise exception 'META_HMAC_UNAVAILABLE' using errcode='42501';end if;
 execute pg_catalog.format('select %I.hmac($1,$2,''sha256'')',v_schema)
 into v_expected using pg_catalog.convert_to(
  prumo_private.meta_material_handoff_fixture_s0(
   p_chave,p_app,p_waba,p_phone,p_canal,p_intencao,p_attempt,
   p_correlation,p_recipient,p_wamid,p_event,p_kind,p_body_hash,
   p_emitido,p_nonce),'UTF8'),v_secret;
 if v_expected is distinct from pg_catalog.decode(p_mac,'hex') then
  raise exception 'META_HANDOFF_BAD_MAC' using errcode='42501';end if;
 insert into prumo_private.meta_servico_nonces_fixture_s0(nonce,chave_id)
 values(p_nonce,p_chave) on conflict do nothing returning nonce into v_used;
 if v_used is null then
  raise exception 'META_HANDOFF_REPLAY' using errcode='42501';end if;
end $wa41_v$;
revoke all on function prumo_private.meta_verificar_handoff_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s0_gateway,
 prumo_s0_signer,prumo_s0_signed_executor,prumo_s0_meta_ingress_lab;
do $wa41_owner$
begin
 execute 'grant create on schema prumo_private to prumo_s0_meta_signer_lab';
 execute 'alter function prumo_private.meta_verificar_handoff_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 owner to prumo_s0_meta_signer_lab';
 execute 'revoke create on schema prumo_private from prumo_s0_meta_signer_lab';
 execute 'set local role prumo_s0_meta_signer_lab';
 execute 'grant execute on function prumo_private.meta_verificar_handoff_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 to postgres';
 execute 'reset role';
end $wa41_owner$;

-- Move the HMAC / key / nonce step of WA40 under this separate low privilege
-- role. postgres remains the domain append owner in WA39; this is NOT full
-- privilege reduction, and is deliberately not deployable.
create or replace function prumo_private.meta_arquivar_handoff_assinado_fixture_s0(
 p_chave uuid,p_app text,p_waba text,p_phone text,p_canal uuid,
 p_intencao uuid,p_attempt text,p_correlation text,p_recipient text,
 p_wamid text,p_event text,p_kind text,p_body_hash text,
 p_emitido bigint,p_nonce uuid,p_mac text
) returns jsonb language plpgsql security definer set search_path='' as $wa41_outer$
declare v_out jsonb;
begin
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
 perform prumo_private.meta_verificar_handoff_fixture_s0(
  p_chave,p_app,p_waba,p_phone,p_canal,p_intencao,p_attempt,
  p_correlation,p_recipient,p_wamid,p_event,p_kind,p_body_hash,
  p_emitido,p_nonce,p_mac);
 v_out:=prumo_private.archivar_status_meta_tecnico_fixture_s0(
  p_app,p_waba,p_phone,p_canal,p_intencao,p_attempt,p_correlation,
  p_recipient,p_wamid,p_event,p_kind,p_body_hash);
 if v_out->>'outcome'='LAB_SCOPE_DENIED' then
  raise exception 'META_HANDOFF_SCOPE_DENIED' using errcode='42501';end if;
 if v_out->>'outcome' not in (
  'LAB_OBSERVED_UNVERIFIED','LAB_LATE_UNVERIFIED','LAB_EXACT_BODY_REPLAY',
  'LAB_BODY_VARIANT_QUARANTINED','LAB_KIND_CONFLICT_QUARANTINED') then
  raise exception 'META_HANDOFF_UNEXPECTED_RESULT' using errcode='42501';end if;
 return v_out || pg_catalog.jsonb_build_object(
  'service_authenticated',false,'s0_production_authorized',false,
  'handoff_contract','WA40_PG17_LAB_ONLY');
end $wa41_outer$;
