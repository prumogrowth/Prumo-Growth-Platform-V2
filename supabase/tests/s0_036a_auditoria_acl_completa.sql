\set ON_ERROR_STOP on
begin;
-- Audit all private routines, not just the two signed entrypoints. Default
-- EXECUTE for PUBLIC can silently grant prumo_s0_gateway access because it
-- has prumo_private USAGE, even when public API users lack schema USAGE.
do $acl$
declare v_error text;
begin
 select pg_catalog.string_agg(
    p.proname||'('||pg_catalog.pg_get_function_identity_arguments(p.oid)||')',
    ', ' order by p.proname)
 into v_error
 from pg_catalog.pg_proc p
 join pg_catalog.pg_namespace n on n.oid=p.pronamespace
 where n.nspname='prumo_private'
 and (
  pg_catalog.has_function_privilege('anon',p.oid,'EXECUTE')
  or pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE')
  or pg_catalog.has_function_privilege('service_role',p.oid,'EXECUTE')
  or (
   pg_catalog.has_function_privilege('prumo_s0_gateway',p.oid,'EXECUTE')
   and p.oid not in (
     'prumo_private.gateway_cancelar_plano_assinado_s0(uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)'::regprocedure::oid,
     'prumo_private.gateway_conciliar_c07_assinado_s0(uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)'::regprocedure::oid
   )
  )
 );
 if v_error is not null then
  raise exception 'FAIL AUD-036A-01 unexpected private EXECUTE: %',v_error;
 end if;
 if (select count(*) from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid=p.pronamespace
  where n.nspname='prumo_private'
  and pg_catalog.has_function_privilege('prumo_s0_gateway',p.oid,'EXECUTE'))<>2
 then raise exception 'FAIL AUD-036A-01 gateway does not have precisely two entrypoints';end if;
end $acl$;
\echo 'PASS AUD-036A-01: ALL private functions checked; gateway only two signed calls'

-- The HMAC signing role and narrow owner may only execute their explicitly
-- authorized dependencies. Their ownership privileges are not inherited.
do $acl$
declare v_error text;
begin
 select pg_catalog.string_agg(p.proname,', ' order by p.proname)
 into v_error
 from pg_catalog.pg_proc p
 join pg_catalog.pg_namespace n on n.oid=p.pronamespace
 where n.nspname='prumo_private'
 and (
 (pg_catalog.has_function_privilege('prumo_s0_signer',p.oid,'EXECUTE')
  and p.oid not in (
   'prumo_private.gateway_material_assinatura_s0(text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,bigint,uuid)'::regprocedure::oid,
   'prumo_private.gateway_validar_prova_s0(text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)'::regprocedure::oid
  ))
 or
 (pg_catalog.has_function_privilege('prumo_s0_signed_executor',p.oid,'EXECUTE')
  and p.oid not in (
   'prumo_private.gateway_validar_prova_s0(text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)'::regprocedure::oid,
   'prumo_private.gateway_cancelar_plano_s0(uuid,uuid,uuid,uuid,bigint)'::regprocedure::oid,
   'prumo_private.gateway_conciliar_c07_s0(uuid,uuid,uuid,uuid,bigint,text,text,uuid)'::regprocedure::oid,
   'prumo_private.gateway_cancelar_plano_assinado_s0(uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)'::regprocedure::oid,
   'prumo_private.gateway_conciliar_c07_assinado_s0(uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)'::regprocedure::oid
  ))
 );
 if v_error is not null then
  raise exception 'FAIL AUD-036A-02 unexpected delegated EXECUTE: %',v_error;
 end if;
end $acl$;
\echo 'PASS AUD-036A-02: signer/executor execute only necessary functions'

-- Security-definer functions must have an empty search_path, preventing
-- name-resolution attacks through attacker-controlled schemas.
do $acl$
declare v_error text;
begin
 select pg_catalog.string_agg(p.proname,', ' order by p.proname)
 into v_error from pg_catalog.pg_proc p
 join pg_catalog.pg_namespace n on n.oid=p.pronamespace
 where n.nspname='prumo_private' and p.prosecdef
 and not ('search_path=' = any(coalesce(p.proconfig,array[]::text[])));
 if v_error is not null then
  raise exception 'FAIL AUD-036A-03 unsafe search_path for SECURITY DEFINER: %',v_error;end if;
end $acl$;
\echo 'PASS AUD-036A-03: all private SECURITY DEFINER routines have empty search_path'

-- Explicitly prove the formerly default-public trigger routine is denied.
set local role prumo_s0_gateway;
do $acl$
begin
 begin
  perform prumo_private.auditar_rotacao_gateway_s0();
  raise exception 'FAIL AUD-036A-04 trigger function unexpectedly callable';
 exception when insufficient_privilege then null;end;
end $acl$;
reset role;
\echo 'PASS AUD-036A-04: gateway denied direct trigger routine EXECUTE'
rollback;
