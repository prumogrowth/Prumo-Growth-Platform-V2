\set ON_ERROR_STOP on
-- I63 PG17 acceptance: canonical S0 + I61, no historic fixture I55.
-- PG17 tests use auth.uid() GUC per role, all synthetic rows rollback.
begin;
insert into auth.users(id)
 select ('86310000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,5) i;
insert into public.atores(id) select id from auth.users where id::text like '86310000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like '86310000-%';
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values('86310000-0000-4000-8000-000000000001','86310000-0000-4000-8000-000000000002'),
 ('86310000-0000-4000-8000-000000000001','86310000-0000-4000-8000-000000000003'),
 ('86310000-0000-4000-8000-000000000004','86310000-0000-4000-8000-000000000005');
insert into public.concessionarias(id,nome_operacional)
 values('86320000-0000-4000-8000-000000000001','I63 Shop A'),
 ('86320000-0000-4000-8000-000000000002','I63 Shop B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('86310000-0000-4000-8000-000000000002','86320000-0000-4000-8000-000000000001','operador'),
 ('86310000-0000-4000-8000-000000000005','86320000-0000-4000-8000-000000000001','operador'),
 ('86310000-0000-4000-8000-000000000005','86320000-0000-4000-8000-000000000002','operador'),
 -- Broad manager grant must NEVER trump restrictive case-specific RLS.
 ('86310000-0000-4000-8000-000000000004','86320000-0000-4000-8000-000000000001','gestor');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('86330000-0000-4000-8000-000000000001','86320000-0000-4000-8000-000000000001','+5581863000001'),
 ('86330000-0000-4000-8000-000000000002','86320000-0000-4000-8000-000000000001','+5581863000002'),
 ('86330000-0000-4000-8000-000000000003','86320000-0000-4000-8000-000000000002','+5581863000003');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('86340000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i=4 then '86320000-0000-4000-8000-000000000002'::uuid
 else '86320000-0000-4000-8000-000000000001'::uuid end,
 ('86330000-0000-4000-8000-'||lpad((case when i=4 then 3 when i=3 then 2 when i=2 then 1 else i end)::text,12,'0'))::uuid,
 'aguardando primeiro disparo'
 from generate_series(1,4) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('86350000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 c.concessionaria_id,c.lead_id,c.id
 from public.ciclos_comerciais c
 join generate_series(1,4) i on c.id=
 ('86340000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.atribuicoes_humanas(id,concessionaria_id,caso_id,operador_id)
 values('86360000-0000-4000-8000-000000000001','86320000-0000-4000-8000-000000000001',
 '86350000-0000-4000-8000-000000000001','86310000-0000-4000-8000-000000000002'),
 ('86360000-0000-4000-8000-000000000003','86320000-0000-4000-8000-000000000001',
 '86350000-0000-4000-8000-000000000003','86310000-0000-4000-8000-000000000005'),
 ('86360000-0000-4000-8000-000000000004','86320000-0000-4000-8000-000000000002',
 '86350000-0000-4000-8000-000000000004','86310000-0000-4000-8000-000000000005');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
 values('86370000-0000-4000-8000-000000000001','86320000-0000-4000-8000-000000000001','i63-sim-A'),
 ('86370000-0000-4000-8000-000000000002','86320000-0000-4000-8000-000000000002','i63-sim-B');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 values('86380000-0000-4000-8000-000000000001','86320000-0000-4000-8000-000000000001',
 '86330000-0000-4000-8000-000000000001','86370000-0000-4000-8000-000000000001',
 '86350000-0000-4000-8000-000000000001'),
 ('86380000-0000-4000-8000-000000000002','86320000-0000-4000-8000-000000000001',
 '86330000-0000-4000-8000-000000000001','86370000-0000-4000-8000-000000000001',null),
 ('86380000-0000-4000-8000-000000000003','86320000-0000-4000-8000-000000000001',
 '86330000-0000-4000-8000-000000000002','86370000-0000-4000-8000-000000000001',null),
 ('86380000-0000-4000-8000-000000000004','86320000-0000-4000-8000-000000000002',
 '86330000-0000-4000-8000-000000000003','86370000-0000-4000-8000-000000000002',null);
insert into public.mensagens(id,concessionaria_id,conversa_id,canal_id,caso_id,
 direcao,origem,conteudo_sintetico,id_externo)
 select ('86390000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 co.concessionaria_id,co.id,co.canal_id,co.caso_id,'entrada','simulado',
 'i63 test '||i,'i63-pg-'||i
 from generate_series(1,4) i
 join public.conversas co on co.id=
 ('86380000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;

-- Additional broad manager grant and D2 synthetic rows for I64 isolation.
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('86310000-0000-4000-8000-000000000001',
        '86320000-0000-4000-8000-000000000001','gestor');
insert into public.lotes_importacao(id,concessionaria_id,chave_importacao)
 values('86400000-0000-4000-8000-000000000001',
        '86320000-0000-4000-8000-000000000001','i64-bulk-A');
insert into public.itens_lote(concessionaria_id,lote_id,ordinal_linha,lead_id)
 values('86320000-0000-4000-8000-000000000001',
        '86400000-0000-4000-8000-000000000001',1,
        '86330000-0000-4000-8000-000000000001');
insert into public.reencontros_lote(concessionaria_id,lote_id,lead_id)
 values('86320000-0000-4000-8000-000000000001',
        '86400000-0000-4000-8000-000000000001',
        '86330000-0000-4000-8000-000000000001');
insert into public.eventos_status_comercial(concessionaria_id,ciclo_id,
 versao_ciclo_apos,status_anterior,status_posterior)
 values('86320000-0000-4000-8000-000000000001',
        '86340000-0000-4000-8000-000000000001',
        2,'aguardando primeiro disparo','primeiro disparo enviado');

\ir s1_087_rls_excecao_canonica_local_only.sql
-- PROVE actual pre-existing S0 gap: manager of other team with shop-wide
-- grant can read direct leads, cycles and bulk metadata despite I63 case deny.
set local role authenticated;
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000004',true);
do $t$ begin
 if (select count(*) from public.leads_loja
  where concessionaria_id='86320000-0000-4000-8000-000000000001')<>2
 or (select count(*) from public.ciclos_comerciais
  where concessionaria_id='86320000-0000-4000-8000-000000000001')<>3
 or not exists(select 1 from public.canais_loja where id='86370000-0000-4000-8000-000000000001')
 or not exists(select 1 from public.lotes_importacao where id='86400000-0000-4000-8000-000000000001')
 or not exists(select 1 from public.itens_lote where lote_id='86400000-0000-4000-8000-000000000001')
 or not exists(select 1 from public.reencontros_lote where lote_id='86400000-0000-4000-8000-000000000001')
 or not exists(select 1 from public.eventos_status_comercial
  where ciclo_id='86340000-0000-4000-8000-000000000001')
 or exists(select 1 from public.casos_humanos where id='86350000-0000-4000-8000-000000000001')
 then raise exception 'I64 expected indirect S0 leakage not reproduced';end if;
end $t$;
reset role;
\echo 'PASS I64-01: reproduced indirect S0 store-grant visibility despite I63 restricted case'

\ir s1_089_s0_indirect_read_boundary_local_only.sql
-- Manager 004 supervises only op005, who owns lead002/storeA case003.
-- Same store-wide grant must NOT reveal lead001/cycles001-002 any longer.
set local role authenticated;
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000004',true);
do $t$ begin
 if (select count(*) from public.leads_loja where id::text like '86330000-%')<>1
 or not exists(select 1 from public.leads_loja where id='86330000-0000-4000-8000-000000000002')
 or (select count(*) from public.ciclos_comerciais where id::text like '86340000-%')<>1
 or not exists(select 1 from public.ciclos_comerciais where id='86340000-0000-4000-8000-000000000003')
 then raise exception 'I64 foreign manager still sees case-unrelated leads/cycles';end if;
end $t$;
\echo 'PASS I64-02: foreign team manager grant constrained to supervised contact and cycle'
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000001',true);
do $t$ begin
 if (select count(*) from public.leads_loja where id::text like '86330000-%')<>1
 or not exists(select 1 from public.leads_loja where id='86330000-0000-4000-8000-000000000001')
 or (select count(*) from public.ciclos_comerciais where id::text like '86340000-%')<>2
 then raise exception 'I64 authorized manager lost same-contact cycles or saw foreign lead';end if;
end $t$;
\echo 'PASS I64-03: current supervisor with S0 manager grant retains exactly same-contact D2 read'

-- Five broad D2 bulk surfaces are quarantined until per-object authorization
-- is specified. Neither team-specific managers nor consultants may read them.
do $t$ begin
 if exists(select 1 from public.canais_loja where id::text like '86370000-%')
 or exists(select 1 from public.lotes_importacao where id='86400000-0000-4000-8000-000000000001')
 or exists(select 1 from public.itens_lote where lote_id='86400000-0000-4000-8000-000000000001')
 or exists(select 1 from public.reencontros_lote where lote_id='86400000-0000-4000-8000-000000000001')
 or exists(select 1 from public.eventos_status_comercial where ciclo_id='86340000-0000-4000-8000-000000000001')
 then raise exception 'I64 bulk manager read not quarantined';end if;
end $t$;
\echo 'PASS I64-04: five S0 bulk surfaces quarantined even for legitimate manager'
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000003',true);
do $t$ begin
 if exists(select 1 from public.leads_loja where id::text like '86330000-%')
 or exists(select 1 from public.ciclos_comerciais where id::text like '86340000-%')
 or exists(select 1 from public.canais_loja where id::text like '86370000-%')
 then raise exception 'I64 no-grant consultant gained direct D2 access';end if;
end $t$;
reset role;
\echo 'PASS I64-05: exceptional consultant without store grant gains no direct lead/cycle/bulk select'

-- Authorized canonical transfer keeps case history from I63 but DOES NOT
-- manufacture S0 lead/cycle permission (no permissive policy added).
select prumo_private.s1_mover_excecao_caso_i61(
 '86310000-0000-4000-8000-000000000001',
 '86320000-0000-4000-8000-000000000001',
 '86350000-0000-4000-8000-000000000001',
 '86360000-0000-4000-8000-000000000001',
 '86310000-0000-4000-8000-000000000003');
set local role authenticated;
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000003',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like '86350000-%')<>2
 or exists(select 1 from public.leads_loja where id::text like '86330000-%')
 or exists(select 1 from public.ciclos_comerciais where id::text like '86340000-%')
 then raise exception 'I64 transfer broadened D2 direct read or lost case';end if;
end $t$;
reset role;
\echo 'PASS I64-06: canonical exception keeps case history but creates no raw S0 lead/cycle right'

select prumo_private.s1_revogar_excecao_i61(
 '86310000-0000-4000-8000-000000000001',
 (select id from prumo_private.s1_excecoes_caso_i61
   where operador_id='86310000-0000-4000-8000-000000000003'
   and revogada_em is null));
set local role authenticated;
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000003',true);
do $t$ begin
 if exists(select 1 from public.casos_humanos where id::text like '86350000-%')
 or exists(select 1 from public.leads_loja where id::text like '86330000-%')
 or exists(select 1 from public.ciclos_comerciais where id::text like '86340000-%')
 then raise exception 'I64 revoke left stale read or D2 privilege';end if;
end $t$;
reset role;
\echo 'PASS I64-07: revoke cuts case history, no lead/cycle side channel on same JWT'

do $t$ begin
 if (select count(*) from pg_catalog.pg_policies where schemaname='public'
  and policyname like 's1_64_%')<>7
 or (select count(*) from pg_catalog.pg_policies where schemaname='public'
  and policyname like 's1_63_canon_%')<>8
 or exists(select 1 from pg_catalog.pg_policies where schemaname='public'
  and policyname like 's1_64_%' and permissive<>'RESTRICTIVE')
 or has_table_privilege('authenticated','prumo_private.s1_excecoes_caso_i61','SELECT')
 or exists(select 1 from pg_catalog.pg_policies
  where schemaname='public' and policyname like 's1_64_%'
  and cmd<>'SELECT')
 then raise exception 'I64 policy/ACL audit mismatch';end if;
end $t$;
\echo 'PASS I64-08: 7 restrictive SELECT-only candidate policies, 8 I63 preserved, no private grant'

-- I65 catalog inventory and deliberate hostile RPC/view injection inside same rollback.
\ir s1_091_rpc_view_surface_guard_local_only.sql
-- I66 follows I65 baseline probes, quarantines only the legacy facade ACL.
\ir s1_093_legacy_interface_acl_quarantine_aceite.sql
-- I67: restore only row-addressable admin items/recontacts/events with team scope.
\ir s1_095_admin_row_scoped_aceite.sql
\ir s1_097_admin_projection_invoker_aceite.sql
\ir s1_099_admin_export_bounded_aceite.sql
\ir s1_101_admin_export_quota_aceite.sql
\ir s1_103_export_rolling_refusals_aceite.sql
\ir s1_105_export_ledger_unexposed_aceite.sql
\ir s1_107_export_executor_aceite.sql
rollback;
\echo 'I64 S0 indirect exposure PG17 8/8; I65 8/8; I66 8/8; I67 8/8; I68 9/9; I69 9/9; I70 9/9; I71 9/9; I72 6/6; I73 6/6; all synthetic objects and policies rolled back'
