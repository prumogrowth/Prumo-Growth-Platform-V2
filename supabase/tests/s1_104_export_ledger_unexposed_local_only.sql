-- I72 EXPERIMENTAL PG17 / ephemeral GoTrue ONLY. Never a production migration.
-- Isolate the reservation ledger from the exposed PostgREST schema while
-- keeping the authenticated invoker RPC and row-level insert checks.
-- The new schema must NOT be added to pgrst.db_schemas.
do $pre$ begin
 if current_user <> 'postgres'
 or to_regclass('public.s1_70_export_reservas') is null
 or to_regclass('prumo_export_ledger.s1_70_export_reservas') is not null
 or to_regprocedure('public.s1_71_exportar_resumo(text,uuid,uuid,integer)') is null
 or to_regprocedure('prumo_private.s1_71_purgar_registros(timestamptz)') is null
 or not has_table_privilege('authenticated','public.s1_70_export_reservas','INSERT')
 or not exists(select 1 from pg_catalog.pg_policies
   where schemaname='public' and tablename='s1_70_export_reservas'
   and policyname='s1_70_reserva_propria')
 then raise exception 'I72_EXIGE_FIXTURE_I71_INTEGRA' using errcode='42501';
 end if;
end $pre$;

create schema prumo_export_ledger;
revoke all on schema prumo_export_ledger from public,anon,authenticated,service_role;
grant usage on schema prumo_export_ledger to authenticated;

-- Same OID, data, trigger, RLS, column INSERT grant and indexes.
-- Moving the relation removes its direct table endpoint from an API whose
-- ONLY exposed application schema is public.
alter table public.s1_70_export_reservas set schema prumo_export_ledger;

-- These three audited I71 bodies reference the old qualified relation.
-- Recompile exact original definitions with ONLY the literal relation name
-- substituted. No caller input, role escalation or public definer is added.
do $rebind$
declare p regprocedure;old_ddl text;new_ddl text;
begin
 foreach p in array array[
  'prumo_private.s1_70_reserva_gatilho()'::regprocedure,
  'public.s1_71_exportar_resumo(text,uuid,uuid,integer)'::regprocedure,
  'prumo_private.s1_71_purgar_registros(timestamptz)'::regprocedure
 ] loop
  old_ddl:=pg_catalog.pg_get_functiondef(p::oid);
  if pg_catalog.strpos(old_ddl,'public.s1_70_export_reservas')=0 then
   raise exception 'I72_EXPECTED_QUALIFIED_REFERENCE_MISSING: %',p
     using errcode='42501';
  end if;
  new_ddl:=pg_catalog.replace(old_ddl,'public.s1_70_export_reservas',
    'prumo_export_ledger.s1_70_export_reservas');
  execute new_ddl;
 end loop;
end $rebind$;

do $audit$ begin
 if to_regclass('public.s1_70_export_reservas') is not null
 or to_regclass('prumo_export_ledger.s1_70_export_reservas') is null
 or not has_schema_privilege('authenticated','prumo_export_ledger','USAGE')
 or has_schema_privilege('anon','prumo_export_ledger','USAGE')
 or has_schema_privilege('service_role','prumo_export_ledger','USAGE')
 or not has_table_privilege('authenticated',
   'prumo_export_ledger.s1_70_export_reservas','INSERT')
 or has_table_privilege('authenticated',
   'prumo_export_ledger.s1_70_export_reservas','SELECT')
 or has_table_privilege('authenticated',
   'prumo_export_ledger.s1_70_export_reservas','UPDATE')
 or has_table_privilege('authenticated',
   'prumo_export_ledger.s1_70_export_reservas','DELETE')
 or not (select relrowsecurity from pg_catalog.pg_class
   where oid='prumo_export_ledger.s1_70_export_reservas'::regclass)
 or not exists(select 1 from pg_catalog.pg_policies
   where schemaname='prumo_export_ledger' and tablename='s1_70_export_reservas'
   and policyname='s1_70_reserva_propria')
 or (select count(*) from pg_catalog.pg_proc
    where oid='public.s1_71_exportar_resumo(text,uuid,uuid,integer)'::regprocedure
    and not prosecdef and provolatile='v')<>1
 or has_function_privilege('anon',
    'public.s1_71_exportar_resumo(text,uuid,uuid,integer)','EXECUTE')
 or has_function_privilege('authenticated',
    'public.s1_69_exportar_lotes(uuid,uuid,integer)','EXECUTE')
 or has_function_privilege('authenticated',
    'public.s1_69_exportar_canais(uuid,uuid,integer)','EXECUTE')
 or exists(select 1 from pg_catalog.pg_proc
  where oid in (
    'prumo_private.s1_70_reserva_gatilho()'::regprocedure,
    'public.s1_71_exportar_resumo(text,uuid,uuid,integer)'::regprocedure,
    'prumo_private.s1_71_purgar_registros(timestamptz)'::regprocedure)
   and pg_catalog.strpos(pg_catalog.pg_get_functiondef(oid),
     'public.s1_70_export_reservas')>0)
 then raise exception 'I72_LEDGER_ISOLATION_ACL_REGRESSION' using errcode='42501';
 end if;
end $audit$;
