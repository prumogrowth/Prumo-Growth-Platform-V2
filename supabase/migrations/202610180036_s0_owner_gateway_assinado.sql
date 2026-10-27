-- S0/036: lower ONLY the signed gateway entrypoints' owner.
-- The privileged legacy domain wrappers remain postgres-owned on purpose:
-- their SECURITY INVOKER commercial routines still check current_user=postgres.
-- This does NOT certify end-to-end least privilege or any public API.
-- Only synthetic local PG17 / local managed Supabase; no production secrets.
do $role$
begin
 if current_user<>'postgres' then
  raise exception 'UNEXPECTED_MIGRATION_ROLE' using errcode='42501';end if;
 if not exists(select 1 from pg_catalog.pg_roles
  where rolname='prumo_s0_signed_executor') then
  create role prumo_s0_signed_executor nologin noinherit
   nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
 end if;
 if not exists(select 1 from pg_catalog.pg_roles
  where rolname='prumo_s0_signed_executor' and not rolcanlogin
   and not rolinherit and not rolsuper and not rolcreatedb
   and not rolcreaterole and not rolreplication and not rolbypassrls)
 then raise exception 'UNSAFE_EXISTING_EXECUTOR' using errcode='42501';end if;
 if exists(select 1 from pg_catalog.pg_auth_members am
  join pg_catalog.pg_roles mr on mr.oid=am.member
  where am.roleid='prumo_s0_signed_executor'::regrole
    and mr.rolname not in ('postgres','supabase_admin'))
 then raise exception 'EXECUTOR_ROLE_GRANTED_TO_UNTRUSTED_MEMBER'
  using errcode='42501';end if;
 -- Managed Supabase postgres may be non-superuser; SET TRUE is required
 -- for ALTER OWNER. Do not modify the reserved supabase_admin membership.
 execute 'grant prumo_s0_signed_executor to postgres with inherit false, set true';
end $role$;

revoke all on schema prumo_private from prumo_s0_signed_executor;
grant usage on schema prumo_private to prumo_s0_signed_executor;

-- The executor has NO auth.sessions SELECT or commercial-table grants.
-- Only postgres-owned legacy functions can check session, store and version.
-- Do not change their SECURITY DEFINER owner or the domain function guards.
grant execute on function prumo_private.gateway_cancelar_plano_s0(
 uuid,uuid,uuid,uuid,bigint) to prumo_s0_signed_executor;
grant execute on function prumo_private.gateway_conciliar_c07_s0(
 uuid,uuid,uuid,uuid,bigint,text,text,uuid) to prumo_s0_signed_executor;

-- Signer is a separate owner from 027. The managed migration role is not
-- the owner, so grant verifier EXECUTE by temporarily SET ROLE signer.
do $delegate$
begin
 execute 'set local role prumo_s0_signer';
 execute 'grant execute on function prumo_private.gateway_validar_prova_s0(
 text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)
 to prumo_s0_signed_executor';
 execute 'reset role';
end $delegate$;

-- Remove external/default grants BEFORE ownership transfer, because
-- managed Supabase postgres cannot later revoke on another role's function.
revoke all on function prumo_private.gateway_cancelar_plano_assinado_s0(
 uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s0_signer;
revoke all on function prumo_private.gateway_conciliar_c07_assinado_s0(
 uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s0_signer;
-- Keep the existing narrow signed-only gateway EXECUTE grants intact.
-- Temporary CREATE is transactional and explicitly revoked in same block.
do $owner$
begin
 execute 'grant create on schema prumo_private to prumo_s0_signed_executor';
 execute 'alter function prumo_private.gateway_cancelar_plano_assinado_s0(
 uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)
 owner to prumo_s0_signed_executor';
 execute 'alter function prumo_private.gateway_conciliar_c07_assinado_s0(
 uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)
 owner to prumo_s0_signed_executor';
 execute 'revoke create on schema prumo_private from prumo_s0_signed_executor';
end $owner$;

-- Invariant: raw domain wrappers cannot be called by SQL gateway, browser
-- roles or the HMAC signer; the isolated executor owns just signed entrypoints.
-- Full commercial-owner reduction is a separate gate.
