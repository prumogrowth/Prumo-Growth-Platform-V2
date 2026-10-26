-- I74 PG17 acceptance: after I73, within outer synthetic rollback.
\ir s1_108_export_signed_executor_local_only.sql
\echo 'PASS I74-01: executor owned private signed entrypoint; no LOGIN membership'
set local role prumo_s1_export_signed_login_ci;
do $a$ begin
 begin
  perform public.s1_71_exportar_resumo('lotes',
    '86320000-0000-4000-8000-000000000001',null,1);
  raise exception 'I74_RAW_RPC_BYPASS';
 exception when insufficient_privilege then null;end;
 begin
  insert into prumo_export_ledger.s1_70_export_reservas(
   ator_id,concessionaria_id,tipo,unidades_reservadas)
   values('86310000-0000-4000-8000-000000000004',
   '86320000-0000-4000-8000-000000000001','lotes',1);
  raise exception 'I74_RAW_INSERT_BYPASS';
 exception when insufficient_privilege then null;end;
end $a$;
reset role;
\echo 'PASS I74-02: signed login cannot call raw invoker or insert reservation'

set local role prumo_s1_export_signed_login_ci;
do $a$ begin
 begin
  perform prumo_export_auth.exportar_assinado_i74(
   '86310000-0000-4000-8000-000000000004',
   '86310000-0000-4000-8000-000000000004','lotes',
   '86320000-0000-4000-8000-000000000001',null,1,
   '86310000-0000-4000-8000-000000000004',
   extract(epoch from clock_timestamp())::bigint,
   '86310000-0000-4000-8000-000000000005',
   repeat('0',64));
  raise exception 'I74_ZERO_MAC_BYPASS';
 exception when insufficient_privilege then null;end;
end $a$;
reset role;
\echo 'PASS I74-03: private signed function denies unknown key/unsigned proof'

do $a$ begin
 if has_schema_privilege('authenticated','prumo_export_auth','USAGE')
 or has_table_privilege('prumo_s1_export_signed_login_ci',
 'prumo_export_auth.chaves_i74','SELECT')
 or has_table_privilege('prumo_s1_export_signed_login_ci',
 'prumo_export_auth.nonces_i74','INSERT')
 or not (select relrowsecurity from pg_class
 where oid='prumo_export_auth.chaves_i74'::regclass)
 or not (select relrowsecurity from pg_class
 where oid='prumo_export_auth.nonces_i74'::regclass)
 then raise exception 'I74_SECRET_EXPOSED';end if;
end $a$;
\echo 'PASS I74-04: HMAC keys and nonce table private with RLS'

do $a$ begin
 if pg_has_role('authenticated','prumo_s1_export_executor','MEMBER')
 or has_function_privilege('anon',
 'prumo_export_auth.exportar_assinado_i74(uuid,uuid,text,uuid,uuid,integer,uuid,bigint,uuid,text)','EXECUTE')
 or has_function_privilege('service_role',
 'prumo_export_auth.exportar_assinado_i74(uuid,uuid,text,uuid,uuid,integer,uuid,bigint,uuid,text)','EXECUTE')
 or (select count(*) from pg_proc where oid=
 'public.s1_71_exportar_resumo(text,uuid,uuid,integer)'::regprocedure and prosecdef)>0
 then raise exception 'I74_PRIVILEGE_DRIFT';end if;
end $a$;
\echo 'PASS I74-05: public invoker and S0 RLS unchanged; no public definer leak'

do $a$begin
 if (select count(*) from prumo_s1_i65_test.exposicoes())<>0
 or has_schema_privilege('prumo_s1_export_signed_login_ci',
 'prumo_export_ledger','USAGE')
 then raise exception 'I74_I65_LEAK';end if;
end $a$;
\echo 'PASS I74-06: I65 ACL scanner clean and ledger hidden from signed login'
