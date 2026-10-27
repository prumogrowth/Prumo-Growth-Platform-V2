\set ON_ERROR_STOP on
-- S0-037A: negative capability probes for the legacy commercial owner.
-- Disposable PostgreSQL transaction ONLY. No persistent roles, grants, data,
-- policy changes, webhook integration or ownership transfers.
begin;

do $gate$
declare v_legacy oid;v_dom oid;v_name text;
begin
 foreach v_legacy in array array[
  'prumo_private.gateway_cancelar_plano_s0(uuid,uuid,uuid,uuid,bigint)'::regprocedure::oid,
  'prumo_private.gateway_conciliar_c07_s0(uuid,uuid,uuid,uuid,bigint,text,text,uuid)'::regprocedure::oid
 ] loop
  if not exists(
    select 1 from pg_catalog.pg_proc p where p.oid=v_legacy
      and p.prosecdef and pg_catalog.pg_get_userbyid(p.proowner)='postgres'
      and (('search_path='=any(coalesce(p.proconfig,array[]::text[])))
        or ('search_path=""'=any(coalesce(p.proconfig,array[]::text[]))))
  ) then raise exception 'FAIL OWNER37-01: legacy wrapper owner/config changed';end if;
 end loop;
 foreach v_dom in array array[
  'prumo_private.cancelar_plano_gestor_sintetico(uuid,uuid,uuid,bigint)'::regprocedure::oid,
  'prumo_private.conciliar_pendencia_c07_sintetica(uuid,uuid,uuid,bigint,text,text,uuid)'::regprocedure::oid
 ] loop
  select proname into v_name from pg_catalog.pg_proc where oid=v_dom;
  if not exists(select 1 from pg_catalog.pg_proc p where p.oid=v_dom
       and not p.prosecdef and pg_catalog.pg_get_userbyid(p.proowner)='postgres'
       and pg_catalog.strpos(pg_catalog.lower(pg_catalog.pg_get_functiondef(p.oid)),
          'current_user')>0
       and pg_catalog.strpos(pg_catalog.lower(pg_catalog.pg_get_functiondef(p.oid)),
          'internal_only')>0)
  then raise exception 'FAIL OWNER37-01: domain guard absent for %',v_name;end if;
 end loop;
end $gate$;
\echo 'PASS OWNER37-01: two legacy definer wrappers and domain postgres-only guards verified'

-- Fail closed: an assigned no-login role may invoke ONLY the signed gate
-- indirectly; it has no table DML or raw domain permissions.
do $gate$
begin
 if has_function_privilege('prumo_s0_signed_executor',
    'prumo_private.cancelar_plano_gestor_sintetico(uuid,uuid,uuid,bigint)','EXECUTE')
 or has_function_privilege('prumo_s0_signed_executor',
    'prumo_private.conciliar_pendencia_c07_sintetica(uuid,uuid,uuid,bigint,text,text,uuid)','EXECUTE')
 or has_table_privilege('prumo_s0_signed_executor','public.leads_loja','SELECT')
 or has_table_privilege('prumo_s0_signed_executor',
      'public.planos_recontato_sinteticos','UPDATE')
 or has_table_privilege('prumo_s0_signed_executor',
      'public.pendencias_reconciliacao_c07_sinteticas','UPDATE')
 or has_table_privilege('prumo_s0_signed_executor',
      'prumo_private.auditoria_gateway_s0','INSERT')
 or (pg_catalog.to_regclass('auth.sessions') is not null
     and has_table_privilege('prumo_s0_signed_executor','auth.sessions','SELECT'))
 then raise exception 'FAIL OWNER37-02: executor has direct DML or domain';end if;
 if not has_function_privilege('prumo_s0_signed_executor',
    'prumo_private.gateway_cancelar_plano_s0(uuid,uuid,uuid,uuid,bigint)','EXECUTE')
 or not has_function_privilege('prumo_s0_signed_executor',
    'prumo_private.gateway_conciliar_c07_s0(uuid,uuid,uuid,uuid,bigint,text,text,uuid)','EXECUTE')
 then raise exception 'FAIL OWNER37-02: signed chain broken';end if;
end $gate$;
\echo 'PASS OWNER37-02: executor retains only delegated signed-chain capability'

-- Simulate a prospective NOLOGIN / NOBYPASSRLS owner without changing any
-- actual application role. All probe privileges and role vanish at rollback.
create role prumo_s0_probe_037a nologin noinherit
 nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
grant usage on schema prumo_private to prumo_s0_probe_037a;
grant execute on function prumo_private.cancelar_plano_gestor_sintetico(
 uuid,uuid,uuid,bigint) to prumo_s0_probe_037a;
grant execute on function prumo_private.conciliar_pendencia_c07_sintetica(
 uuid,uuid,uuid,bigint,text,text,uuid) to prumo_s0_probe_037a;

set local role prumo_s0_probe_037a;
do $probe$
begin
 if current_user<>'prumo_s0_probe_037a'
 then raise exception 'FAIL OWNER37-03: role switch invalid';end if;
 begin
  perform prumo_private.cancelar_plano_gestor_sintetico(null,null,null,null);
  raise exception 'FAIL OWNER37-03: cancellation accepted without postgres';
 exception when insufficient_privilege then
  if SQLERRM<>'INTERNAL_ONLY' then
   raise exception 'FAIL OWNER37-03 unexpected cancellation denial: %',SQLERRM;
  end if;
 end;
 begin
  perform prumo_private.conciliar_pendencia_c07_sintetica(
   null,null,null,null,null,null,null);
  raise exception 'FAIL OWNER37-03: reconciliation accepted without postgres';
 exception when insufficient_privilege then
  if SQLERRM<>'INTERNAL_ONLY' then
   raise exception 'FAIL OWNER37-03 unexpected reconciliation denial: %',SQLERRM;
  end if;
 end;
end $probe$;
reset role;
\echo 'PASS OWNER37-03: no-login nonprivileged owner cannot execute guarded domain functions'

-- Even temporarily granting SELECT does not give a role lacking the
-- authenticated policy unrestricted access through RLS.
insert into public.concessionarias(id,nome_operacional)
 values('c3700000-0000-4000-8000-000000000001','OWNER37 RLS ficticia');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('c3710000-0000-4000-8000-000000000001',
        'c3700000-0000-4000-8000-000000000001','+5581900003737');
do $gate$
begin
 if (select count(*) from public.leads_loja
  where id='c3710000-0000-4000-8000-000000000001')<>1
 then raise exception 'FAIL OWNER37-04: missing fixture for RLS check';end if;
 if not (select relrowsecurity from pg_catalog.pg_class
  where oid='public.leads_loja'::regclass)
 then raise exception 'FAIL OWNER37-04: leads RLS disabled';end if;
end $gate$;
grant select on public.leads_loja to prumo_s0_probe_037a;
set local role prumo_s0_probe_037a;
do $probe$
begin
 if (select count(*) from public.leads_loja
  where id='c3710000-0000-4000-8000-000000000001')<>0
 then raise exception 'FAIL OWNER37-04: unrestricted SELECT despite RLS';end if;
end $probe$;
reset role;
\echo 'PASS OWNER37-04: SELECT grant alone does not bypass row security'

-- Precondition for any future reassignment: domain rewrite, table rights,
-- WITH CHECK policies, auth.sessions access and the audit trigger chain must
-- be tested together. This gate is explicitly NOT a transfer test.
do $gate$
begin
 if not exists(select 1 from pg_catalog.pg_roles where
    rolname='prumo_s0_signed_executor' and not rolbypassrls
      and not rolcanlogin)
 then raise exception 'FAIL OWNER37-05: existing signed role was broadened';end if;
 if exists(select 1 from pg_catalog.pg_auth_members am
   where am.member='prumo_s0_probe_037a'::regrole
     and am.roleid='prumo_s0_signed_executor'::regrole)
 then raise exception 'FAIL OWNER37-05: probe inherits signed capability';end if;
end $gate$;
\echo 'PASS OWNER37-05: no persistent privilege granted and no owner transfer performed'
rollback;
