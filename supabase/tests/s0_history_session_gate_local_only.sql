-- S0 experimental history READ barrier. LOCAL DISPOSABLE PG17 ONLY.
-- After the PR #9/#13 CFI fixtures. No hosted migration or commercial grant.
begin;
do $guard$
begin
 if current_setting('prumo.history_disposable',true) is distinct from 'YES'
 or current_user <> 'postgres' or session_user <> 'postgres'
 or current_setting('server_version_num')::int / 10000 <> 17
 or current_database() <> 'postgres'
 or to_regprocedure('prumo_private.cfi01_session_valid_local(uuid,uuid)') is null
 then raise exception 'S0_HISTORY_DISPOSABLE_INSTALL_REQUIRED' using errcode='42501'; end if;
end $guard$;

-- Separate unexposed namespace: do not grant authenticated usage on the
-- existing prumo_private schema or EXECUTE on its arbitrary-tuple CFI helper.
create schema prumo_history_local authorization postgres;
revoke all on schema prumo_history_local from public,anon,authenticated,service_role;
grant usage on schema prumo_history_local to authenticated;

-- The trusted PostgREST JWT context is the ONLY source of actor/session.
-- No caller arguments and no metadata, commercial ACL or SQL login authority.
-- postgres ownership is the existing auth.sessions access limitation of #9;
-- this wrapper returns one boolean and delegates to the SAME locking helper.
create function prumo_history_local.session_valid()
returns boolean language plpgsql security definer set search_path=''
as $session$
declare v_claims jsonb; v_actor uuid; v_session uuid; v_exp numeric;
begin
 v_claims := auth.jwt();
 if v_claims->>'role' is distinct from 'authenticated'
 or v_claims->>'is_anonymous' = 'true'
 or coalesce(v_claims->>'session_id','') !~
   '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
 or coalesce(v_claims->>'exp','') !~ '^[0-9]{1,19}$'
 then return false; end if;
 v_actor := auth.uid();
 v_session := (v_claims->>'session_id')::uuid;
 v_exp := (v_claims->>'exp')::numeric;
 if v_actor is null
 or v_exp <= pg_catalog.date_part('epoch',pg_catalog.clock_timestamp())
 then return false; end if;
 if not prumo_private.cfi01_session_valid_local(v_actor,v_session)
 then return false; end if;
 -- The session lock may have waited; do not admit an expired JWT afterwards.
 return v_exp > pg_catalog.date_part('epoch',pg_catalog.clock_timestamp());
end $session$;
revoke all on function prumo_history_local.session_valid()
 from public,anon,authenticated,service_role;
grant execute on function prumo_history_local.session_valid() to authenticated;

-- AND with existing S0 and candidate S1/I63 policies. Never a permissive
-- alternative, and never change INSERT/UPDATE/DELETE rights or their meaning.
-- Uncorrelated SELECT makes a single session check/lock per statement plan,
-- rather than one auth.sessions lookup per history row.
do $policies$
declare v_table text;
begin
 foreach v_table in array array[
  'leads_loja','ciclos_comerciais','casos_humanos','atribuicoes_humanas',
  'conversas','mensagens','itens_lote','reencontros_lote',
  'eventos_status_comercial','lotes_importacao','canais_loja'
 ] loop
  if not exists(select 1 from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid=c.relnamespace
    where n.nspname='public' and c.relname=v_table and c.relrowsecurity)
  then raise exception 'S0_HISTORY_RLS_PREREQUISITE_REQUIRED' using errcode='42501'; end if;
  execute pg_catalog.format(
   'create policy s0_history_live_session on public.%I as restrictive
    for select to authenticated using ((select prumo_history_local.session_valid()))',v_table);
 end loop;
end $policies$;
commit;
