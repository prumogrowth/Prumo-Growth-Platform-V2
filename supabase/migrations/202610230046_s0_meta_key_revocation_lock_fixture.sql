-- S0/046 WA42: offline key-revocation serialization, NO Meta API.
-- SQL-side scope only; S1 rights/assignment are outside this migration.
-- Never apply laboratory role/fixture migrations to hosted Supabase.
create function prumo_private.meta_revogar_chave_fixture_s0(p_chave uuid)
returns text language plpgsql security invoker set search_path='' as $wa42_revoke$
declare v_active boolean;
begin
 if current_user<>'postgres' then
  raise exception 'WA42_ADMIN_ONLY' using errcode='42501';end if;
 if p_chave is null then
  raise exception 'WA42_INVALID_KEY' using errcode='22023';end if;
 -- Identical transaction-scoped lock and namespace to signer verification.
 -- Admin revocation waits for in-flight signed receipts to COMMIT or ROLLBACK.
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended('wa42-meta-key:'||p_chave::text,42));
 select ativo into v_active
 from prumo_private.meta_servico_chaves_fixture_s0
 where chave_id=p_chave for update;
 if not found then
  raise exception 'WA42_UNKNOWN_KEY' using errcode='22023';end if;
 if not v_active then return 'LAB_ALREADY_REVOKED';end if;
 update prumo_private.meta_servico_chaves_fixture_s0
 set ativo=false where chave_id=p_chave;
 return 'LAB_REVOKED';
end $wa42_revoke$;
revoke all on function prumo_private.meta_revogar_chave_fixture_s0(uuid)
 from public,anon,authenticated,service_role,
 prumo_s0_gateway,prumo_s0_signer,prumo_s0_signed_executor,
 prumo_s0_meta_ingress_lab,prumo_s0_meta_signer_lab;

-- Existing verifier owner is the special NOLOGIN signer. Change the
-- implementation only as its owner, temporarily granting schema CREATE.
-- No permanently broadened grant and no new service login.
do $wa42_owner$
begin
 if current_user<>'postgres' then
  raise exception 'WA42_LOCAL_ADMIN_ONLY' using errcode='42501';end if;
 if (select p.proowner::regrole::text from pg_catalog.pg_proc p
   where p.oid='prumo_private.meta_verificar_handoff_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)'::regprocedure)
   <>'prumo_s0_meta_signer_lab'
 then raise exception 'WA42_SIGNER_OWNER_MISMATCH' using errcode='42501';end if;
 execute 'grant create on schema prumo_private to prumo_s0_meta_signer_lab';
 execute 'set local role prumo_s0_meta_signer_lab';
end $wa42_owner$;

create or replace function prumo_private.meta_verificar_handoff_fixture_s0(
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
 -- WA42: serialize verification through nonce COMMIT with revocation.
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended('wa42-meta-key:'||p_chave::text,42));
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

do $wa42_cleanup$
begin
 if current_user<>'prumo_s0_meta_signer_lab' then
  raise exception 'WA42_NOT_SIGNER' using errcode='42501';end if;
 execute 'reset role';
 execute 'revoke create on schema prumo_private from prumo_s0_meta_signer_lab';
end $wa42_cleanup$;
-- The wrapper/nonce/forensics interface remains unchanged: no Graph,
-- webhook HTTP ACK, machine LOGIN or production authorization.
