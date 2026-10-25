-- I65 catalog attack-surface scanner and adversarial probes.
-- Included inside I64's BEGIN/ROLLBACK, PG17 ephemeral ONLY.
-- No permanent function, policy, grant or view is created.
create schema prumo_s1_i65_test authorization postgres;
revoke all on schema prumo_s1_i65_test from public,anon,authenticated,service_role;

create function prumo_s1_i65_test.exposicoes()
returns table(tipo text,objeto text)
language sql stable security invoker set search_path='' as $scan$
 -- An exposed PUBLIC SECURITY DEFINER routine can run as the owner and
 -- bypass private objects or RLS, even with a strong SELECT policy.
 select 'PUBLIC_DEFINER_RPC'::text,
  pg_catalog.concat(n.nspname,'.',p.proname,'(',
    pg_catalog.pg_get_function_identity_arguments(p.oid),')')::text
 from pg_catalog.pg_proc p
 join pg_catalog.pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.prosecdef
  and (pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE')
    or pg_catalog.has_function_privilege('anon',p.oid,'EXECUTE'))
  and (pg_catalog.has_schema_privilege('authenticated',n.oid,'USAGE')
    or pg_catalog.has_schema_privilege('anon',n.oid,'USAGE'))
 union all
 -- Normal (owner-rights) views do not enforce the original caller's RLS.
 -- SECURITY BARRIER alone is not an invoker-RLS guarantee.
 select 'PUBLIC_OWNER_VIEW'::text,
    pg_catalog.concat(n.nspname,'.',c.relname)::text
 from pg_catalog.pg_class c
 join pg_catalog.pg_namespace n on n.oid=c.relnamespace
 where n.nspname='public' and c.relkind in ('v','m')
  and (pg_catalog.has_table_privilege('authenticated',c.oid,'SELECT')
    or pg_catalog.has_table_privilege('anon',c.oid,'SELECT'))
  and not ('security_invoker=true'=any(
      coalesce(c.reloptions,array[]::text[])))
 union all
 -- Even perfect EXECUTE ACLs are insufficient if exposed client roles
 -- gain USAGE on the entire legacy privileged schema.
 select 'PRIVATE_SCHEMA_USAGE'::text,n.nspname::text
 from pg_catalog.pg_namespace n
 where n.nspname='prumo_private'
  and (pg_catalog.has_schema_privilege('authenticated',n.oid,'USAGE')
   or pg_catalog.has_schema_privilege('anon',n.oid,'USAGE'));
$scan$;
revoke all on function prumo_s1_i65_test.exposicoes()
 from public,anon,authenticated,service_role;

