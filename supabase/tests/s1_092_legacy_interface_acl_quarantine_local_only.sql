-- I66 LOCAL candidate only: retire the three 051 legacy JWT SQL facades.
-- Does not alter bodies/owners, S0 tables, S1 membership, signed I62 or RLS.
-- Installed after I65 on synthetic PostgreSQL and GoTrue ephemeral stack.
do $prereq$
declare v_expected int;
begin
 if current_user<>'postgres'
 or pg_catalog.to_regnamespace('prumo_s1_interface') is null
 then raise exception 'I66_UNEXPECTED_INSTALL_CONTEXT' using errcode='42501';end if;
 select count(*) into v_expected
 from pg_catalog.pg_proc p
 join pg_catalog.pg_namespace n on n.oid=p.pronamespace
 where n.nspname='prumo_s1_interface'
 and p.prosecdef
 and pg_catalog.pg_get_userbyid(p.proowner)='postgres'
 and p.oid in (
  'prumo_s1_interface.s1_mover_atendimento_sessao(uuid,uuid,uuid,uuid)'::regprocedure,
  'prumo_s1_interface.s1_pausar_operador_sessao(uuid,text)'::regprocedure,
  'prumo_s1_interface.s1_reativar_operador_sessao(uuid)'::regprocedure
 );
 if v_expected<>3
 or (select count(*) from pg_catalog.pg_proc p
     join pg_catalog.pg_namespace n on n.oid=p.pronamespace
     where n.nspname='prumo_s1_interface')<>3
 then raise exception 'I66_LEGACY_FACADE_INVENTORY_DRIFT' using errcode='42501';end if;
end $prereq$;
-- Revoke PUBLIC/default EXECUTE as well as direct grants: SQL SECURITY DEFINER
-- privileges are not a safe substitute for a gateway-bound signed command.
revoke all on all functions in schema prumo_s1_interface
 from public,anon,authenticated,service_role;
revoke all on schema prumo_s1_interface
 from public,anon,authenticated,service_role;

do $post$
declare v_role text;v_oid oid;v_error text;
begin
 foreach v_role in array array['PUBLIC','anon','authenticated','service_role'] loop
  if pg_catalog.has_schema_privilege(v_role,'prumo_s1_interface','USAGE') then
    raise exception 'I66_SCHEMA_CLIENT_USAGE: %',v_role using errcode='42501';end if;
  for v_oid in
   select p.oid from pg_catalog.pg_proc p
   join pg_catalog.pg_namespace n on n.oid=p.pronamespace
   where n.nspname='prumo_s1_interface'
  loop
    if pg_catalog.has_function_privilege(v_role,v_oid,'EXECUTE') then
      raise exception 'I66_LEGACY_FUNCTION_EXECUTE: % %',
       v_role,v_oid using errcode='42501';end if;
  end loop;
 end loop;
 if pg_catalog.has_schema_privilege('authenticated','prumo_private','USAGE')
 or pg_catalog.has_table_privilege('authenticated',
       'prumo_private.s1_excecoes_caso_i61','SELECT')
 or (select count(*) from pg_catalog.pg_policies
    where schemaname='public' and policyname like 's1_63_canon_%')<>8
 or (select count(*) from pg_catalog.pg_policies
    where schemaname='public' and policyname like 's1_64_%')<>7
 then raise exception 'I66_RLS_OR_PRIVATE_BOUNDARY_REGRESSION' using errcode='42501';end if;
end $post$;
