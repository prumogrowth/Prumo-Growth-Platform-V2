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

do $gate$ begin
 if exists(select 1 from prumo_s1_i65_test.exposicoes())
 then raise exception 'I65_PREEXISTING_CATALOG_EXPOSURE: %',
  (select pg_catalog.string_agg(tipo||':'||objeto,', ')
     from prumo_s1_i65_test.exposicoes()) using errcode='42501';end if;
end $gate$;
\echo 'PASS I65-01: no public definer RPC, owner-rights public view or private-schema client USAGE in canonical S0/S1'

-- These are signed gateway dependencies, NOT public REST RPC endpoints.
-- The old S1 interface remains SQL-callable to authenticated in its own
-- schema; DO NOT classify this legacy capability as production-ready.
do $gate$ begin
 if not pg_catalog.has_schema_privilege(
      'authenticated','prumo_s1_interface','USAGE')
  or not pg_catalog.has_function_privilege('authenticated',
      'prumo_s1_interface.s1_mover_atendimento_sessao(uuid,uuid,uuid,uuid)',
      'EXECUTE')
  or pg_catalog.has_schema_privilege(
      'authenticated','prumo_private','USAGE')
  or pg_catalog.has_function_privilege('authenticated',
      'prumo_private.s1_mover_excecao_caso_i61(uuid,uuid,uuid,uuid,uuid)',
      'EXECUTE')
 then raise exception 'I65_LEGACY_GATEWAY_OR_PRIVATE_ACL_DRIFT'
  using errcode='42501';end if;
end $gate$;
\echo 'PASS I65-02: legacy S1 interface capability inventoried separately; I61 private move denied'

do $gate$ declare n int;begin
 select count(*) into n from pg_catalog.pg_proc p
 join pg_catalog.pg_namespace ns on ns.oid=p.pronamespace
 where ns.nspname='prumo_private' and p.prosecdef
  and not exists(select 1 from pg_catalog.unnest(
    coalesce(p.proconfig,array[]::text[])) as c(config)
    where c.config in ('search_path=','search_path=""'));
 if n<>0 then raise exception 'I65_PRIVATE_DEFINER_UNSAFE_SEARCHPATH_COUNT: %',
     n using errcode='42501';end if;
end $gate$;
\echo 'PASS I65-03: private SECURITY DEFINER functions retain empty search_path'

-- Inject TWO genuinely dangerous objects strictly inside PG17 rollback.
-- These are red-team controls to prove the scanner is not a vacuous 0=0.
create function public.i65_redteam_private_count()
returns bigint language sql stable security definer
set search_path='' as $leak$
 select count(*) from prumo_private.s1_excecoes_caso_i61;
$leak$;
grant execute on function public.i65_redteam_private_count()
 to authenticated;
create view public.i65_redteam_private_view as
 select id,concessionaria_id,caso_id from
 prumo_private.s1_excecoes_caso_i61;
grant select on public.i65_redteam_private_view to authenticated;

do $gate$ begin
 if (select count(*) from prumo_s1_i65_test.exposicoes())<>2
 or not exists(select 1 from prumo_s1_i65_test.exposicoes()
   where tipo='PUBLIC_DEFINER_RPC'
    and objeto like 'public.i65_redteam_private_count(%')
 or not exists(select 1 from prumo_s1_i65_test.exposicoes()
   where tipo='PUBLIC_OWNER_VIEW'
    and objeto='public.i65_redteam_private_view')
 then raise exception 'I65_SCANNER_FAILED_TO_DETECT_INJECTED_LEAK'
  using errcode='42501';end if;
end $gate$;
\echo 'PASS I65-04: scanner detects both malicious public RPC and owner-rights view'

set local role authenticated;
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000004',true);
do $gate$ begin
 if not (select public.i65_redteam_private_count()>0)
 or not exists(select 1 from public.i65_redteam_private_view)
 then raise exception 'I65_ATTACK_CONTROL_NOT_REACHABLE'
   using errcode='42501';end if;
 begin
  perform 1 from prumo_private.s1_excecoes_caso_i61;
  raise exception 'I65_DIRECT_PRIVATE_READ_UNEXPECTED';
 exception when insufficient_privilege then null;end;
end $gate$;
reset role;
\echo 'PASS I65-05: authenticated reader can exploit injected definer RPC/view but cannot SELECT private ledger directly'

-- Revoke both abilities and drop the synthetic attack primitives while
-- still inside the outer rollback. No data ever leave disposable CI.
revoke all on public.i65_redteam_private_view from public,anon,authenticated,service_role;
revoke all on function public.i65_redteam_private_count()
 from public,anon,authenticated,service_role;
do $gate$ begin
 if exists(select 1 from prumo_s1_i65_test.exposicoes())
 then raise exception 'I65_EXPOSURE_REMAINS_AFTER_REVOKE' using errcode='42501';end if;
end $gate$;
\echo 'PASS I65-06: revoke EXECUTE/SELECT removes both leaked capabilities from exposed catalog'

set local role authenticated;
do $gate$ begin
 begin
  perform public.i65_redteam_private_count();
  raise exception 'I65_REVOKED_RPC_STILL_EXECUTABLE';
 exception when insufficient_privilege then null;end;
 begin
  perform 1 from public.i65_redteam_private_view;
  raise exception 'I65_REVOKED_VIEW_STILL_READABLE';
 exception when insufficient_privilege then null;end;
end $gate$;
reset role;
\echo 'PASS I65-07: same SQL role denied public RPC/view after revoke'

do $gate$ begin
 if (select count(*) from pg_catalog.pg_policies where schemaname='public'
  and policyname like 's1_64_%')<>7
 or (select count(*) from pg_catalog.pg_policies where schemaname='public'
  and policyname like 's1_63_canon_%')<>8
 or pg_catalog.has_schema_privilege('authenticated','prumo_private','USAGE')
 then raise exception 'I65_PRIOR_RLS_OR_PRIVATE_ACL_REGRESSION'
  using errcode='42501';end if;
end $gate$;
\echo 'PASS I65-08: I63/I64 policies preserved, private schema remains inaccessible'
