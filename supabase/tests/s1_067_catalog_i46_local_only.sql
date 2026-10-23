\set ON_ERROR_STOP on
-- I46: catalog-level exposure census AFTER full PG17 S0/S1 runner.
-- Only reports expected findings; no DDL, DML or production changes.
do $audit$
declare
  v_public int; v_private int; v_public_rls int; v_public_auth_select int;
  v_missing_gate int; v_public_views int; v_executable_definers int;
  v_policy_count int; v_unprotected int;
begin
 select count(*) into v_public from pg_catalog.pg_class c
 join pg_catalog.pg_namespace n on n.oid=c.relnamespace
 where n.nspname='public' and c.relkind in ('r','p');
 select count(*) into v_private from pg_catalog.pg_class c
 join pg_catalog.pg_namespace n on n.oid=c.relnamespace
 where n.nspname='prumo_private' and c.relkind in ('r','p');
 select count(*) into v_public_rls from pg_catalog.pg_class c
 join pg_catalog.pg_namespace n on n.oid=c.relnamespace
 where n.nspname='public' and c.relkind in ('r','p') and c.relrowsecurity;
 select count(*) into v_public_auth_select from pg_catalog.pg_class c
 join pg_catalog.pg_namespace n on n.oid=c.relnamespace
 where n.nspname='public' and c.relkind in ('r','p')
 and pg_catalog.has_table_privilege('authenticated',c.oid,'SELECT');
 select count(*) into v_missing_gate from pg_catalog.pg_class c
 join pg_catalog.pg_namespace n on n.oid=c.relnamespace
 where n.nspname='public' and c.relkind in ('r','p')
 and pg_catalog.has_table_privilege('authenticated',c.oid,'SELECT')
 and not exists (select 1 from pg_catalog.pg_policy p
  where p.polrelid=c.oid and p.polname='s1_equipe_ativa_gate');
 select count(*) into v_unprotected from pg_catalog.pg_class c
 join pg_catalog.pg_namespace n on n.oid=c.relnamespace
 where n.nspname='public' and c.relkind in ('r','p')
 and pg_catalog.has_table_privilege('authenticated',c.oid,'SELECT')
 and not c.relrowsecurity;
 select count(*) into v_public_views from pg_catalog.pg_class c
 join pg_catalog.pg_namespace n on n.oid=c.relnamespace
 where n.nspname='public' and c.relkind='v';
 select count(*) into v_executable_definers from pg_catalog.pg_proc p
 join pg_catalog.pg_namespace n on n.oid=p.pronamespace
 where n.nspname in ('public','prumo_private')
 and p.prosecdef and pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE');
 select count(*) into v_policy_count from pg_catalog.pg_policy p
 join pg_catalog.pg_class c on c.oid=p.polrelid
 join pg_catalog.pg_namespace n on n.oid=c.relnamespace
 where n.nspname in ('public','prumo_private');
 raise notice 'I46-CATALOG public_tables=% private_tables=% public_rls=% auth_select_tables=% policies=% views=%',
  v_public,v_private,v_public_rls,v_public_auth_select,v_policy_count,v_public_views;
 raise notice 'I46-CATALOG auth_select_missing_s1_038_gate=% auth_select_without_rls=% authenticated_executable_definers=%',
  v_missing_gate,v_unprotected,v_executable_definers;
 if v_public_auth_select=0 or v_policy_count=0 then
  raise exception 'I46: catalog inaccessible or missing ACL baseline';
 end if;
 if v_unprotected<>0 then
  raise exception 'I46: authenticated table SELECT without RLS found';
 end if;
 raise notice 'PASS I46-CATALOG: PG17 catalog enumerated and public authenticated SELECT tables have RLS (not proof of team isolation)';
end
$audit$;
