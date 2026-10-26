-- I73 synthetic PostgreSQL 17, after I72, inside outer I64 rollback.
\ir s1_106_export_executor_local_only.sql
\echo 'PASS I73-01: executor NOLOGIN installed; public invoker and ledger INSERT denied to authenticated'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000004',true);
do $check$ begin
 begin
  perform public.s1_71_exportar_resumo('lotes',
   '86320000-0000-4000-8000-000000000001',null,1);
  raise exception 'I73_DIRECT_RPC_PERMITTED';
 exception when insufficient_privilege then null;end;
 begin
  insert into prumo_export_ledger.s1_70_export_reservas(
    ator_id,concessionaria_id,tipo,unidades_reservadas)
  values('86310000-0000-4000-8000-000000000004',
   '86320000-0000-4000-8000-000000000001','lotes',1);
  raise exception 'I73_DIRECT_SQL_INSERT_PERMITTED';
 exception when insufficient_privilege then null;end;
 begin
  perform prumo_export_auth.sessao_ativa(
   '86310000-0000-4000-8000-000000000004',
   '00000000-0000-4000-8000-000000000001');
  raise exception 'I73_PRIVATE_SESSION_CHECK_EXPOSED';
 exception when insufficient_privilege then null;end;
end $check$;
reset role;
\echo 'PASS I73-02: authenticated SQL cannot call export, insert reservation or inspect private session checker'

-- Fake auth.sessions fixture is present on the local PG17 stack; do not
-- manufacture identity for a real HTTP user in product code.
set local role prumo_s1_export_executor;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000004',true);
do $check$ declare s jsonb;begin
 s:=public.s1_71_exportar_resumo('lotes',
  '86320000-0000-4000-8000-000000000001',null,1);
 if s->>'estado'<>'OK' or jsonb_array_length(s->'linhas')<>1
 then raise exception 'I73_EXECUTOR_CANNOT_EXPORT: %',s;end if;
end $check$;
reset role;
\echo 'PASS I73-03: dedicated executor inherits S0 RLS and consumes quota through existing invoker'

do $check$ begin
 if not exists(select 1 from prumo_export_ledger.s1_70_export_reservas
  where ator_id='86310000-0000-4000-8000-000000000004' and tipo='lotes')
 then raise exception 'I73_RESERVA_NAO_REGISTRADA';end if;
end $check$;
\echo 'PASS I73-04: accepted export still persists quota reservation in internal ledger'

set local role prumo_s1_export_executor;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000003',true);
do $check$ declare s jsonb;begin
 s:=public.s1_71_exportar_resumo('lotes',
  '86320000-0000-4000-8000-000000000001',null,1);
 if s->>'estado'<>'VAZIO' then
  raise exception 'I73_EXECUTOR_RLS_BYPASS: %',s;end if;
end $check$;
reset role;
\echo 'PASS I73-05: executor never bypasses manager/team/store RLS for exception-only consultant'

do $check$ begin
 if pg_catalog.has_function_privilege('anon',
  'public.s1_71_exportar_resumo(text,uuid,uuid,integer)','EXECUTE')
 or pg_catalog.has_function_privilege('service_role',
  'public.s1_71_exportar_resumo(text,uuid,uuid,integer)','EXECUTE')
 or pg_catalog.has_schema_privilege('authenticated','prumo_export_auth','USAGE')
 or (select count(*) from prumo_s1_i65_test.exposicoes())<>0
 then raise exception 'I73_RPC_OR_DEFINER_LEAK';end if;
end $check$;
\echo 'PASS I73-06: anon, service_role and authenticated cannot reach privileged helper or exported RPC'
