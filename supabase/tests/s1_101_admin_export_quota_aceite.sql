-- I70 PostgreSQL 17 synthetic quota/audit validation, all outer ROLLBACK.
-- I69 expires manager 004; restore for isolated manager budget.
update public.vinculos_papel_escopo set valido_ate=null
 where ator_id='86310000-0000-4000-8000-000000000004'
  and concessionaria_id='86320000-0000-4000-8000-000000000001'
  and papel='gestor' and valido_ate is not null;
\ir s1_100_admin_export_quota_local_only.sql
\echo 'PASS I70-01: quota trigger, private atomic counters and minimal audit installed'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000001',true);
do $test$ declare n integer;begin
 for n in 1..4 loop
  if (select count(*) from public.s1_69_exportar_lotes(
   '86320000-0000-4000-8000-000000000001',null,1))<>1
  then raise exception 'I70_LEGITIMATE_PAGE_MISSING';end if;
 end loop;
 begin
  perform * from public.s1_69_exportar_lotes(
   '86320000-0000-4000-8000-000000000001',null,1);
  raise exception 'I70_REPEAT_QUOTA_BYPASS';
 exception when invalid_parameter_value then
   if SQLERRM<>'I70_QUOTA_EXCEDIDA' then raise;end if;
 end;
end $test$;
reset role;
\echo 'PASS I70-02: repeated identical cursor consumes quota; 5th request denied'

do $test$ begin
 if (select requisicoes from prumo_private.s1_70_export_contadores
  where ator_id='86310000-0000-4000-8000-000000000001'
   and tipo='lotes')<>4
 or (select unidades_reservadas from prumo_private.s1_70_export_contadores
  where ator_id='86310000-0000-4000-8000-000000000001'
   and tipo='lotes')<>4
 or (select count(*) from public.s1_70_export_reservas
  where ator_id='86310000-0000-4000-8000-000000000001'
   and tipo='lotes')<>4
 then raise exception 'I70_QUOTA_AUDIT_NOT_ATOMIC';end if;
end $test$;
\echo 'PASS I70-03: private counter and write-only audit show exactly 4 successful reservations'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000001',true);
do $test$begin
 if (select count(*) from public.s1_69_exportar_canais(
   '86320000-0000-4000-8000-000000000001',null,20))<>2
 then raise exception 'I70_DIFFERENT_KIND_DENIED';end if;
 begin
  perform * from public.s1_69_exportar_canais(
   '86320000-0000-4000-8000-000000000001',null,11);
  raise exception 'I70_CUMULATIVE_UNIT_BYPASS';
 exception when invalid_parameter_value then
  if SQLERRM<>'I70_QUOTA_EXCEDIDA' then raise;end if;
 end;
 if (select count(*) from public.s1_69_exportar_canais(
   '86320000-0000-4000-8000-000000000001',null,10))<>2
 then raise exception 'I70_REMAINING_QUOTA_DENIED';end if;
end $test$;
reset role;
\echo 'PASS I70-04: per-kind independence; 20+11 denied, 20+10 accepted under 30 units'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000004',true);
do $test$ begin
 if (select count(*) from public.s1_69_exportar_lotes(
    '86320000-0000-4000-8000-000000000001',null,1))<>1
 then raise exception 'I70_OTHER_MANAGER_WRONG_QUOTA';end if;
 if exists(select 1 from public.s1_69_exportar_lotes(
   '86320000-0000-4000-8000-000000000002',null,1))
 then raise exception 'I70_CROSS_STORE_LEAK';end if;
end $test$;
reset role;
\echo 'PASS I70-05: independent manager quota and cross-store RLS preserved'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000001',true);
do $test$begin
 begin
  perform 1 from public.s1_70_export_reservas;
  raise exception 'I70_AUDIT_READ_ALLOWED';
 exception when insufficient_privilege then null;end;
 begin
  update public.s1_70_export_reservas set unidades_reservadas=0;
  raise exception 'I70_AUDIT_TAMPER_ALLOWED';
 exception when insufficient_privilege then null;end;
 begin
  insert into public.s1_70_export_reservas(
   ator_id,concessionaria_id,tipo,unidades_reservadas)
  values('86310000-0000-4000-8000-000000000004',
   '86320000-0000-4000-8000-000000000001','lotes',1);
  raise exception 'I70_FORGED_ACTOR_ALLOWED';
 exception when insufficient_privilege then null;end;
end $test$;
reset role;
\echo 'PASS I70-06: client cannot read, reset or forge another actor audit/quota'

do $test$ begin
 if exists(select 1 from information_schema.columns
  where table_schema='public' and table_name='s1_70_export_reservas'
   and column_name in ('lead_id','telefone','conteudo','mensagem','nome_cliente','caso_id','email'))
 or (select count(*) from prumo_s1_i65_test.exposicoes())<>0
 or (select count(*) from pg_catalog.pg_proc
  where oid='prumo_private.s1_70_reserva_gatilho()'::regprocedure
   and prosecdef)=0
 then raise exception 'I70_AUDIT_PII_OR_DEFINER_SURFACE';end if;
end $test$;
\echo 'PASS I70-07: accepted-reservation audit contains no customer fields; no publicly executable definer'

update public.vinculos_papel_escopo set valido_ate=pg_catalog.clock_timestamp()
 where ator_id='86310000-0000-4000-8000-000000000004'
  and concessionaria_id='86320000-0000-4000-8000-000000000001'
  and papel='gestor' and valido_ate is null;
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000004',true);
do $test$ begin
 if exists(select 1 from public.s1_69_exportar_lotes(
   '86320000-0000-4000-8000-000000000001',null,1))
 then raise exception 'I70_REVOKED_GRANT_EXPORT';end if;
end $test$;
reset role;
\echo 'PASS I70-08: revoked manager receives no rows without new reservation'

do $test$ begin
 if (select count(*) from pg_catalog.pg_policies
     where schemaname='public' and policyname like 's1_67_%')<>3
 or (select count(*) from pg_catalog.pg_policies
     where schemaname='public' and policyname like 's1_63_canon_%')<>8
 or pg_catalog.has_function_privilege('anon',
    'public.s1_69_exportar_lotes(uuid,uuid,integer)','EXECUTE')
 or pg_catalog.has_schema_privilege('authenticated','prumo_s1_interface','USAGE')
 or pg_catalog.has_table_privilege('authenticated','prumo_private.s1_70_export_contadores','SELECT')
 then raise exception 'I70_PRIOR_SCOPE_REGRESSION';end if;
end $test$;
\echo 'PASS I70-09: I63-I69 access boundaries, legacy ACL and private counter intact'
