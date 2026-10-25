-- I68 PG17, inside canonical I64-I67 outer transaction and rollback.
-- I67 leaves manager 004 grant expired, restore before projection comparisons.
update public.vinculos_papel_escopo set valido_ate=null
 where ator_id='86310000-0000-4000-8000-000000000004'
 and concessionaria_id='86320000-0000-4000-8000-000000000001'
 and papel='gestor' and valido_ate is not null;
\ir s1_096_admin_projection_invoker_candidate_local_only.sql
\echo 'PASS I68-01: invoker views and column-only grants installed without changing I67 RLS'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000001',true);
do $test$ declare got bigint;begin
 select itens_autorizados into got from public.s1_68_lotes_equipe
 where lote_ref='86400000-0000-4000-8000-000000000001';
 if got<>1 then raise exception 'I68_MGR1_SEES_FOREIGN_BATCH_COUNT:%',got;end if;
 if (select count(*) from public.itens_lote
   where lote_id='86400000-0000-4000-8000-000000000001')<>1
 then raise exception 'I68_MGR1_RAW_SCOPE_FAILED';end if;
end $test$;
\echo 'PASS I68-02: manager A sees only own accepted row and its own share of mixed-lot count'

select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000004',true);
do $test$ declare got bigint;begin
 select itens_autorizados into got from public.s1_68_lotes_equipe
 where lote_ref='86400000-0000-4000-8000-000000000001';
 if got<>1 then raise exception 'I68_MGR4_SEES_FOREIGN_BATCH_COUNT:%',got;end if;
 if (select count(*) from public.itens_lote
    where lote_id='86400000-0000-4000-8000-000000000001')<>1
 then raise exception 'I68_MGR4_ROW_SCOPE_FAILED';end if;
end $test$;
\echo 'PASS I68-03: manager B on same lot sees precisely own count, not global batch metadata'

-- Reject SELECT * and specifically withheld columns: RLS alone would not.
do $test$ begin
 begin
 execute 'select id from public.itens_lote limit 1';
 raise exception 'I68_LEAK_ITEM_PK';
 exception when insufficient_privilege then null;end;
 begin
 execute 'select motivo_rejeicao from public.itens_lote limit 1';
 raise exception 'I68_LEAK_REJECTION_REASON';
 exception when insufficient_privilege then null;end;
 begin
 execute 'select motivo from public.reencontros_lote limit 1';
 raise exception 'I68_LEAK_RECONTACT_REASON';
 exception when insufficient_privilege then null;end;
 begin
 execute 'select status_anterior from public.eventos_status_comercial limit 1';
 raise exception 'I68_LEAK_PREVIOUS_STATUS';
 exception when insufficient_privilege then null;end;
end $test$;
\echo 'PASS I68-04: raw PK/rejected reason/recontact reason/previous status all blocked even on owned rows'

select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000001',true);
do $test$ declare got bigint;begin
 select conversas_autorizadas into got from public.s1_68_canais_equipe
 where canal_ref='86370000-0000-4000-8000-000000000001';
 if got<>2 then raise exception 'I68_MGR1_CHANNEL_COUNT:%',got;end if;
 if exists(select 1 from public.canais_loja
     where id='86370000-0000-4000-8000-000000000001')
 or exists(select 1 from public.lotes_importacao
     where id='86400000-0000-4000-8000-000000000001')
 then raise exception 'I68_SHARED_HEADER_LEAKED';end if;
end $test$;
\echo 'PASS I68-05: channel summary counts caller-visible conversations, no headers or emitter identifiers'

select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000004',true);
do $test$ declare got bigint;begin
 select conversas_autorizadas into got from public.s1_68_canais_equipe
 where canal_ref='86370000-0000-4000-8000-000000000001';
 if got<>1 then raise exception 'I68_MGR4_CHANNEL_COUNT:%',got;end if;
end $test$;
\echo 'PASS I68-06: second manager sees one own conversation, not other team same-channel history'

select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000003',true);
do $test$ begin
 if exists(select 1 from public.s1_68_lotes_equipe)
 or exists(select 1 from public.s1_68_canais_equipe)
 then raise exception 'I68_CONSULTANT_SEES_ADMIN_SUMMARY';end if;
end $test$;
reset role;
\echo 'PASS I68-07: exception-only consultant denied both admin summaries'

update public.vinculos_papel_escopo set valido_ate=pg_catalog.clock_timestamp()
 where ator_id='86310000-0000-4000-8000-000000000004'
 and concessionaria_id='86320000-0000-4000-8000-000000000001'
 and papel='gestor' and valido_ate is null;
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000004',true);
do $test$ begin
 if exists(select 1 from public.s1_68_lotes_equipe)
 or exists(select 1 from public.s1_68_canais_equipe)
 then raise exception 'I68_REVOKED_GRANT_LEAKS_SUMMARY';end if;
end $test$;
reset role;
\echo 'PASS I68-08: same manager/session loses both summaries immediately after grant expiry'

do $test$ begin
 if (select count(*) from prumo_s1_i65_test.exposicoes())<>0
 or (select count(*) from pg_catalog.pg_policies
      where schemaname='public' and policyname like 's1_63_canon_%')<>8
 or (select count(*) from pg_catalog.pg_policies
      where schemaname='public' and policyname like 's1_64_%')<>4
 or (select count(*) from pg_catalog.pg_policies
      where schemaname='public' and policyname like 's1_67_%')<>3
 or pg_catalog.has_schema_privilege('authenticated','prumo_s1_interface','USAGE')
 then raise exception 'I68_OWNER_VIEW_OR_PREVIOUS_SECURITY_GATE_REGRESSION';end if;
end $test$;
\echo 'PASS I68-09: no catalog owner-view leak; I63-I67 RLS/ACL boundaries intact'
