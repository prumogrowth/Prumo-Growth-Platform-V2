-- I73: privileged SQL executor instead of direct authenticated ledger grants.
-- TEST-ONLY. Apply AFTER I72; never deploy to hosted Supabase.
do $pre$ begin
 if current_user<>'postgres'
 or to_regclass('prumo_export_ledger.s1_70_export_reservas') is null
 or to_regprocedure('public.s1_71_exportar_resumo(text,uuid,uuid,integer)') is null
 or to_regrole('prumo_s1_export_executor') is not null
 or not pg_catalog.has_column_privilege('authenticated',
   'prumo_export_ledger.s1_70_export_reservas','ator_id','INSERT')
 then raise exception 'I73_EXIGE_I72_CANDIDATA' using errcode='42501';end if;
end $pre$;

-- The executor has no LOGIN; only a separately provisioned gateway login
-- may SET ROLE into it. Authenticated must never be a member of executor.
create role prumo_s1_export_executor nologin inherit;
grant authenticated to prumo_s1_export_executor;

revoke execute on function public.s1_71_exportar_resumo(text,uuid,uuid,integer)
 from public,anon,authenticated,service_role;
revoke insert(ator_id,concessionaria_id,tipo,unidades_reservadas)
 on prumo_export_ledger.s1_70_export_reservas from authenticated;
revoke usage on schema prumo_export_ledger from authenticated;

grant usage on schema prumo_export_ledger to prumo_s1_export_executor;
grant insert(ator_id,concessionaria_id,tipo,unidades_reservadas)
 on prumo_export_ledger.s1_70_export_reservas to prumo_s1_export_executor;
grant execute on function public.s1_71_exportar_resumo(text,uuid,uuid,integer)
 to prumo_s1_export_executor;

-- This one-purpose checker is SECURITY DEFINER but NOT in public or any
-- PostgREST-exposed schema, and is callable only by the executor.
create schema prumo_export_auth;
revoke all on schema prumo_export_auth from public,anon,authenticated,service_role;
grant usage on schema prumo_export_auth to prumo_s1_export_executor;
create function prumo_export_auth.sessao_ativa(p_ator uuid,p_sessao uuid)
returns boolean language sql volatile security definer set search_path=''
as $$
 select p_ator is not null and p_sessao is not null
 and exists(select 1 from auth.sessions s
   where s.id=p_sessao and s.user_id=p_ator for key share)
$$;
revoke all on function prumo_export_auth.sessao_ativa(uuid,uuid)
 from public,anon,authenticated,service_role;
grant execute on function prumo_export_auth.sessao_ativa(uuid,uuid)
 to prumo_s1_export_executor;

do $audit$ begin
 if pg_catalog.has_function_privilege('authenticated',
    'public.s1_71_exportar_resumo(text,uuid,uuid,integer)','EXECUTE')
 or pg_catalog.has_column_privilege('authenticated',
    'prumo_export_ledger.s1_70_export_reservas','ator_id','INSERT')
 or pg_catalog.has_schema_privilege('authenticated','prumo_export_ledger','USAGE')
 or pg_catalog.has_schema_privilege('authenticated','prumo_export_auth','USAGE')
 or pg_catalog.has_schema_privilege('service_role','prumo_export_auth','USAGE')
 or pg_catalog.has_function_privilege('authenticated',
    'prumo_export_auth.sessao_ativa(uuid,uuid)','EXECUTE')
 or not pg_catalog.has_function_privilege('prumo_s1_export_executor',
    'public.s1_71_exportar_resumo(text,uuid,uuid,integer)','EXECUTE')
 or not pg_catalog.has_column_privilege('prumo_s1_export_executor',
    'prumo_export_ledger.s1_70_export_reservas','ator_id','INSERT')
 or pg_catalog.has_table_privilege('prumo_s1_export_executor',
    'prumo_export_ledger.s1_70_export_reservas','SELECT')
 or pg_catalog.pg_has_role('authenticated','prumo_s1_export_executor','MEMBER')
 or not pg_catalog.pg_has_role('prumo_s1_export_executor','authenticated','MEMBER')
 or (select count(*) from pg_catalog.pg_proc
     where oid='public.s1_71_exportar_resumo(text,uuid,uuid,integer)'::regprocedure
      and not prosecdef and provolatile='v')<>1
 or (select count(*) from pg_catalog.pg_proc
     where oid='prumo_export_auth.sessao_ativa(uuid,uuid)'::regprocedure
      and prosecdef)=0
 then raise exception 'I73_EXECUTOR_ACL_INSEGURO' using errcode='42501';end if;
end $audit$;
