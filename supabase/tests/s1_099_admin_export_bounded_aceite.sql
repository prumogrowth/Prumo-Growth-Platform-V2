-- I69 PG17 - after I68, before outer rollback. Synthetic 2nd lot/channel.
-- Restore manager 004 shop grant that I68's revoke test expired.
update public.vinculos_papel_escopo set valido_ate=null
 where ator_id='86310000-0000-4000-8000-000000000004'
 and concessionaria_id='86320000-0000-4000-8000-000000000001'
 and papel='gestor' and valido_ate is not null;
insert into public.lotes_importacao(id,concessionaria_id,chave_importacao)
 values('86400000-0000-4000-8000-000000000002',
        '86320000-0000-4000-8000-000000000001','i69-second-A');
insert into public.itens_lote(concessionaria_id,lote_id,ordinal_linha,lead_id,resultado)
 values('86320000-0000-4000-8000-000000000001',
        '86400000-0000-4000-8000-000000000002',1,
        '86330000-0000-4000-8000-000000000001','aceito');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
 values('86370000-0000-4000-8000-000000000003',
        '86320000-0000-4000-8000-000000000001','i69-channel-A');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 values('86380000-0000-4000-8000-000000000005',
       '86320000-0000-4000-8000-000000000001',
       '86330000-0000-4000-8000-000000000001',
       '86370000-0000-4000-8000-000000000003',
       '86350000-0000-4000-8000-000000000001');
\ir s1_098_admin_export_bounded_candidate_local_only.sql
\echo 'PASS I69-01: invoker-only bounded export installed, direct I68 view scans removed'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000001',true);
do $gate$ declare got uuid; n bigint; begin
 select lote_ref,itens_autorizados into got,n from
 public.s1_69_exportar_lotes('86320000-0000-4000-8000-000000000001',null,1);
 if got<>'86400000-0000-4000-8000-000000000001' or n<>1
 or (select count(*) from public.s1_69_exportar_lotes(
     '86320000-0000-4000-8000-000000000001',null,1))<>1
 then raise exception 'I69_FIRST_BATCH_PAGE_LEAK';end if;
 select lote_ref,itens_autorizados into got,n from
 public.s1_69_exportar_lotes('86320000-0000-4000-8000-000000000001',got,1);
 if got<>'86400000-0000-4000-8000-000000000002' or n<>1
 then raise exception 'I69_SECOND_BATCH_PAGE_WRONG';end if;
 if exists(select 1 from public.s1_69_exportar_lotes(
   '86320000-0000-4000-8000-000000000001',got,1))
 then raise exception 'I69_BATCH_PAGES_REPEAT';end if;
end $gate$;
\echo 'PASS I69-02: deterministic one-row keyset pages, no repetitions and own-team counts'

do $gate$ declare got uuid; n bigint;begin
 select canal_ref,conversas_autorizadas into got,n from
 public.s1_69_exportar_canais('86320000-0000-4000-8000-000000000001',null,1);
 if got<>'86370000-0000-4000-8000-000000000001' or n<>2
 then raise exception 'I69_FIRST_CHANNEL_PAGE_WRONG';end if;
 select canal_ref,conversas_autorizadas into got,n from
 public.s1_69_exportar_canais('86320000-0000-4000-8000-000000000001',got,1);
 if got<>'86370000-0000-4000-8000-000000000003' or n<>1
 then raise exception 'I69_SECOND_CHANNEL_PAGE_WRONG';end if;
 if exists(select 1 from public.s1_69_exportar_canais(
   '86320000-0000-4000-8000-000000000001',got,1))
 then raise exception 'I69_CHANNEL_PAGES_REPEAT';end if;
end $gate$;
\echo 'PASS I69-03: channel keyset pages include only own conversations, not foreign team'

select pg_catalog.set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000004',true);
do $gate$ begin
 if (select count(*) from public.s1_69_exportar_lotes(
   '86320000-0000-4000-8000-000000000001',null,20))<>1
 or (select itens_autorizados from public.s1_69_exportar_lotes(
   '86320000-0000-4000-8000-000000000001',null,20))<>1
 or (select conversas_autorizadas from public.s1_69_exportar_canais(
   '86320000-0000-4000-8000-000000000001',null,20))<>1
 or exists(select 1 from public.s1_69_exportar_lotes(
   '86320000-0000-4000-8000-000000000002',null,20))
 then raise exception 'I69_FOREIGN_TEAM_OR_STORE_ENUMERATION';end if;
end $gate$;
\echo 'PASS I69-04: foreign-team manager sees own share only; cross-store filter returns empty'

do $gate$ begin
 for i in 1..2 loop
 begin
 if i=1 then
  perform * from public.s1_69_exportar_lotes(
     '86320000-0000-4000-8000-000000000001',null,0);
 else
  perform * from public.s1_69_exportar_canais(
     '86320000-0000-4000-8000-000000000001',null,21);
 end if;
 raise exception 'I69_INVALID_LIMIT_ACCEPTED';
 exception when invalid_parameter_value then null;end;
 end loop;
 begin
  perform * from public.s1_69_exportar_lotes(
      '86320000-0000-4000-8000-000000000001',null,null);
  raise exception 'I69_NULL_LIMIT_ACCEPTED';
 exception when invalid_parameter_value then null;end;
 begin
  perform * from public.s1_69_exportar_canais(null,null,1);
  raise exception 'I69_NULL_SHOP_ACCEPTED';
 exception when invalid_parameter_value then null;end;
end $gate$;
\echo 'PASS I69-05: bounds 1..20, NULL/zero/21 and absent shop fail-closed'

do $gate$ begin
 begin
  perform 1 from public.s1_68_lotes_equipe;
  raise exception 'I69_DIRECT_LOT_VIEW_EXPOSURE';
 exception when insufficient_privilege then null;end;
 begin
  perform 1 from public.s1_68_canais_equipe;
  raise exception 'I69_DIRECT_CHANNEL_VIEW_EXPOSURE';
 exception when insufficient_privilege then null;end;
end $gate$;
\echo 'PASS I69-06: direct unlimited I68 views cannot be SELECTed after RPC cutover'

select pg_catalog.set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000003',true);
do $gate$ begin
 if exists(select 1 from public.s1_69_exportar_lotes(
    '86320000-0000-4000-8000-000000000001',null,20))
 or exists(select 1 from public.s1_69_exportar_canais(
    '86320000-0000-4000-8000-000000000001',null,20))
 then raise exception 'I69_EXCEPTION_ONLY_CONSULTANT_ADMIN_EXPORT';end if;
end $gate$;
reset role;
\echo 'PASS I69-07: exception-only consultant does not gain administrative exports'

update public.vinculos_papel_escopo set valido_ate=pg_catalog.clock_timestamp()
 where ator_id='86310000-0000-4000-8000-000000000004'
 and concessionaria_id='86320000-0000-4000-8000-000000000001'
 and papel='gestor' and valido_ate is null;
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000004',true);
do $gate$ begin
 if exists(select 1 from public.s1_69_exportar_lotes(
    '86320000-0000-4000-8000-000000000001',null,20))
 or exists(select 1 from public.s1_69_exportar_canais(
    '86320000-0000-4000-8000-000000000001',null,20))
 then raise exception 'I69_REVOKED_STORE_GRANT_EXPORT';end if;
end $gate$;
reset role;
\echo 'PASS I69-08: expired grant stops both exports immediately with unchanged session'

do $gate$ begin
 if pg_catalog.has_function_privilege('anon',
   'public.s1_69_exportar_lotes(uuid,uuid,integer)','EXECUTE')
 or pg_catalog.has_function_privilege('anon',
   'public.s1_69_exportar_canais(uuid,uuid,integer)','EXECUTE')
 or (select count(*) from prumo_s1_i65_test.exposicoes())<>0
 or pg_catalog.has_schema_privilege('authenticated','prumo_s1_interface','USAGE')
 or (select count(*) from pg_catalog.pg_policies
    where schemaname='public' and policyname like 's1_67_%')<>3
 or pg_catalog.has_table_privilege('authenticated','public.canais_loja','SELECT')=false
 then raise exception 'I69_PRIVILEGE_OR_RLS_DRIFT';end if;
end $gate$;
\echo 'PASS I69-09: no definer/owner view leaks, I66 ACL and I67 RLS unchanged'
