-- S0 isolation: the HMAC verifier no longer runs as postgres.
-- IMPORTANT: the signed domain entrypoints remain postgres-owned until a
-- separate review; this is an incremental privilege reduction, NOT prod-ready.
--
-- No real keys or remote configuration are created.
do $role$
begin
 if not exists(select 1 from pg_catalog.pg_roles
   where rolname='prumo_s0_signer') then
  create role prumo_s0_signer nologin noinherit
   nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
 end if;
 if not exists(select 1 from pg_catalog.pg_roles
   where rolname='prumo_s0_signer' and not rolcanlogin
   and not rolinherit and not rolsuper and not rolcreatedb
   and not rolcreaterole and not rolreplication and not rolbypassrls)
 then
  raise exception 'UNSAFE_EXISTING_SIGNER_ROLE' using errcode='42501';
 end if;
 -- Dedicated verifier must not be reachable via inherited role membership.
 if exists(
  select 1 from pg_catalog.pg_auth_members am
  where am.roleid='prumo_s0_signer'::regrole
 )
 then raise exception 'SIGNER_ROLE_MUST_NOT_HAVE_MEMBERS' using errcode='42501';end if;
end $role$;

revoke all on schema prumo_private from prumo_s0_signer;
grant usage on schema prumo_private to prumo_s0_signer;

-- Restrict access to the few columns needed by HMAC verification.
grant select(chave_id,segredo,ativo,valido_desde,valido_ate)
 on prumo_private.gateway_chaves_assinatura_s0 to prumo_s0_signer;
grant insert(nonce,chave_id),select(nonce)
 on prumo_private.gateway_provas_usadas_s0 to prumo_s0_signer;
grant execute on function prumo_private.gateway_material_assinatura_s0(
 text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,bigint,uuid)
 to prumo_s0_signer;

-- pgcrypto may have already been installed in public on local PostgreSQL,
-- or in prumo_crypto in a fresh hosted Supabase instance.
do $ext$
declare v_schema name;
begin
 select n.nspname into v_schema from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace
 where e.extname='pgcrypto';
 if v_schema is null then
  raise exception 'PGCRYPTO_NOT_INSTALLED' using errcode='42501';end if;
 execute pg_catalog.format('grant usage on schema %I to prumo_s0_signer',v_schema);
 execute pg_catalog.format(
  'grant execute on function %I.hmac(bytea,bytea,text) to prumo_s0_signer',v_schema);
end $ext$;

-- Change ONLY the signature validator owner. This isolated role can read HMAC
-- material and consume nonces, but cannot access leads, sessions, domain
-- transitions, key rotation, or key-history audit directly.
alter function prumo_private.gateway_validar_prova_s0(
 text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)
 owner to prumo_s0_signer;

revoke all on function prumo_private.gateway_validar_prova_s0(
 text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s0_gateway;

-- None of the pgcrypto/material grants are exposed as domain API operations.
-- prumo_s0_gateway still executes ONLY the two signed gateway entrypoints.
