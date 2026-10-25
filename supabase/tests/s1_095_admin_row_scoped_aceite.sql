-- I67 PG17 test-only. Included inside I64/I65/I66 BEGIN/ROLLBACK.
-- Same mixed batch contains one assigned lead for each distinct manager.
insert into public.itens_lote(
 concessionaria_id,lote_id,ordinal_linha,lead_id,resultado)
 values('86320000-0000-4000-8000-000000000001',
 '86400000-0000-4000-8000-000000000001',2,
 '86330000-0000-4000-8000-000000000002','aceito');
insert into public.itens_lote(
 concessionaria_id,lote_id,ordinal_linha,lead_id,resultado,motivo_rejeicao)
 values('86320000-0000-4000-8000-000000000001',
 '86400000-0000-4000-8000-000000000001',3,
 null,'rejeitado','TELEFONE_INVALIDO');
insert into public.reencontros_lote(concessionaria_id,lote_id,lead_id)
 values('86320000-0000-4000-8000-000000000001',
 '86400000-0000-4000-8000-000000000001',
 '86330000-0000-4000-8000-000000000002');
insert into public.eventos_status_comercial(concessionaria_id,ciclo_id,
 versao_ciclo_apos,status_anterior,status_posterior)
 values('86320000-0000-4000-8000-000000000001',
 '86340000-0000-4000-8000-000000000003',
 2,'aguardando primeiro disparo','primeiro disparo enviado');
do $gate$ begin
 if (select count(*) from public.itens_lote
   where lote_id='86400000-0000-4000-8000-000000000001')<>3
 or (select count(*) from public.reencontros_lote
   where lote_id='86400000-0000-4000-8000-000000000001')<>2
 then raise exception 'I67_MIXED_BATCH_FIXTURE_INVALID';end if;
end $gate$;
\echo 'PASS I67-01: mixed-store batch fixture has two team leads and a rejected anonymous line'

-- I66 still in effect, five administrative objects denied until candidate.
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000004',true);
do $gate$ begin
 if exists(select 1 from public.itens_lote
   where lote_id='86400000-0000-4000-8000-000000000001')
 or exists(select 1 from public.reencontros_lote
   where lote_id='86400000-0000-4000-8000-000000000001')
 or exists(select 1 from public.eventos_status_comercial
   where ciclo_id='86340000-0000-4000-8000-000000000003')
 then raise exception 'I67_I64_QUARANTINE_UNEXPECTEDLY_OPEN';end if;
end $gate$;
reset role;
\echo 'PASS I67-02: I64 original quarantine closed all three row-addressable collections'

\ir s1_094_admin_row_scoped_candidate_local_only.sql

-- Manager 004 has store A grant but supervises ONLY op005 -> lead002.
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000004',true);
do $gate$ begin
 if (select count(*) from public.itens_lote
   where lote_id='86400000-0000-4000-8000-000000000001')<>1
 or not exists(select 1 from public.itens_lote
   where lote_id='86400000-0000-4000-8000-000000000001' and ordinal_linha=2)
 or (select count(*) from public.reencontros_lote
   where lote_id='86400000-0000-4000-8000-000000000001')<>1
 or not exists(select 1 from public.reencontros_lote
   where lead_id='86330000-0000-4000-8000-000000000002')
 or (select count(*) from public.eventos_status_comercial
   where ciclo_id in('86340000-0000-4000-8000-000000000001',
                      '86340000-0000-4000-8000-000000000003'))<>1
 or exists(select 1 from public.eventos_status_comercial
   where ciclo_id='86340000-0000-4000-8000-000000000001')
 then raise exception 'I67_MANAGER_004_LEAKS_OTHER_TEAM_ROW';end if;
end $gate$;
\echo 'PASS I67-03: manager 004 sees only accepted item, recontact and event for own supervised contact'

select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000001',true);
do $gate$ begin
 if (select count(*) from public.itens_lote
   where lote_id='86400000-0000-4000-8000-000000000001')<>1
 or not exists(select 1 from public.itens_lote
   where lote_id='86400000-0000-4000-8000-000000000001' and ordinal_linha=1)
 or (select count(*) from public.reencontros_lote
   where lote_id='86400000-0000-4000-8000-000000000001')<>1
 or (select count(*) from public.eventos_status_comercial
   where ciclo_id in('86340000-0000-4000-8000-000000000001',
                      '86340000-0000-4000-8000-000000000003'))<>1
 or exists(select 1 from public.itens_lote where resultado='rejeitado')
 then raise exception 'I67_MANAGER_001_LEAKS_OTHER_TEAM_OR_REJECTED';end if;
end $gate$;
\echo 'PASS I67-04: manager 001 sees only own contact within same lot, rejected row hidden'

do $gate$ begin
 if exists(select 1 from public.lotes_importacao
     where id='86400000-0000-4000-8000-000000000001')
 or exists(select 1 from public.canais_loja
     where id='86370000-0000-4000-8000-000000000001')
 then raise exception 'I67_SHARED_BATCH_OR_CHANNEL_EXPOSED';end if;
end $gate$;
\echo 'PASS I67-05: full lot and shared channel remain unreadable even to legitimate manager'

select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000003',true);
do $gate$ begin
 if exists(select 1 from public.itens_lote
   where lote_id='86400000-0000-4000-8000-000000000001')
 or exists(select 1 from public.reencontros_lote
   where lote_id='86400000-0000-4000-8000-000000000001')
 or exists(select 1 from public.eventos_status_comercial
   where ciclo_id='86340000-0000-4000-8000-000000000001')
 then raise exception 'I67_CONSULTANT_WITHOUT_STORE_GRANT_GOT_ADMIN_READ';end if;
end $gate$;
reset role;
\echo 'PASS I67-06: no raw administrative SELECT granted to exception-only consultant'

-- A manager losing store grant or team supervisor relationship must lose reads.
update public.vinculos_papel_escopo
 set valido_ate=pg_catalog.clock_timestamp()
 where ator_id='86310000-0000-4000-8000-000000000004'
  and concessionaria_id='86320000-0000-4000-8000-000000000001'
  and papel='gestor' and valido_ate is null;
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000004',true);
do $gate$ begin
 if exists(select 1 from public.itens_lote
   where lote_id='86400000-0000-4000-8000-000000000001')
 or exists(select 1 from public.reencontros_lote
   where lote_id='86400000-0000-4000-8000-000000000001')
 or exists(select 1 from public.eventos_status_comercial
   where ciclo_id='86340000-0000-4000-8000-000000000003')
 then raise exception 'I67_REVOKED_MANAGER_READ_ADMIN';end if;
end $gate$;
reset role;
\echo 'PASS I67-07: same identity loses administrative row reads immediately after shop grant expires'

do $gate$ begin
 if (select count(*) from pg_catalog.pg_policies
  where schemaname='public' and policyname like 's1_67_%')<>3
 or (select count(*) from pg_catalog.pg_policies
  where schemaname='public' and policyname like 's1_64_%')<>4
 or (select count(*) from pg_catalog.pg_policies
  where schemaname='public' and policyname like 's1_63_canon_%')<>8
 or pg_catalog.has_schema_privilege('authenticated','prumo_s1_interface','USAGE')
 or pg_catalog.has_table_privilege('authenticated',
  'prumo_private.s1_excecoes_caso_i61','SELECT')
 then raise exception 'I67_RLS_OR_LEGACY_REGRESSION';end if;
end $gate$;
\echo 'PASS I67-08: restrictive-only scoped policies, quarantined headers and I66 legacy closure retained'
