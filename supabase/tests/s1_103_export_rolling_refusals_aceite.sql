-- I71 acceptance after I70, shared I63-I70 PG17 transaction ROLLBACK.
-- I70 finished with manager 004 grant expired.
update public.vinculos_papel_escopo set valido_ate=null
 where ator_id='86310000-0000-4000-8000-000000000004'
 and concessionaria_id='86320000-0000-4000-8000-000000000001'
 and papel='gestor' and valido_ate is not null;
\ir s1_102_export_rolling_refusals_local_only.sql
\echo 'PASS I71-01: rolling ledger and private refusal aggregate installed, legacy RPC closed'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000001',true);
do $verify$declare s jsonb;begin
 s:=public.s1_71_exportar_resumo('lotes',
 '86320000-0000-4000-8000-000000000001',null,1);
 if s->>'estado'<>'LIMITE_ATINGIDO' or s->'linhas'<>'[]'::jsonb
 then raise exception 'I71_EXISTING_60MIN_NOT_COUNTED: %',s;end if;
end $verify$;
reset role;
do $verify$begin
 if (select coalesce(sum(total),0) from prumo_private.s1_71_export_recusas
 where ator_id='86310000-0000-4000-8000-000000000001'
 and tipo='lotes')<>1
 then raise exception 'I71_REFUSAL_NOT_PERSISTED';end if;
end $verify$;
\echo 'PASS I71-02: old I70 accepted requests enforce rolling limit; denial is durably recorded'

-- Cross hour rollover simulation: change old accepted time to 61min ago,
-- proving that fixed-hour I70 state no longer gates I71, but trailing 60m does.
update public.s1_70_export_reservas
 set registrada_em=pg_catalog.clock_timestamp()-interval '61 minutes'
 where ator_id='86310000-0000-4000-8000-000000000001' and tipo='lotes';
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000001',true);
do $verify$declare s jsonb;begin
 s:=public.s1_71_exportar_resumo('lotes',
  '86320000-0000-4000-8000-000000000001',null,1);
 if s->>'estado'<>'OK' or jsonb_array_length(s->'linhas')<>1
 then raise exception 'I71_ROLLING_EXPIRY_FAILED: %',s;end if;
end $verify$;
reset role;
\echo 'PASS I71-03: request accepted after prior 60-minute window expires'

-- The trailing window is NOT a fixed hour bucket: 3 old reservations
-- timestamped 59min ago + 1 fresh = 4 used even across hour boundary.
update public.s1_70_export_reservas
 set registrada_em=pg_catalog.clock_timestamp()-interval '59 minutes'
 where ator_id='86310000-0000-4000-8000-000000000001' and tipo='lotes'
 and registrada_em<pg_catalog.clock_timestamp()-interval '60 minutes';
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000001',true);
do $verify$ declare s jsonb;begin
 s:=public.s1_71_exportar_resumo('lotes',
 '86320000-0000-4000-8000-000000000001',null,1);
 if s->>'estado'<>'LIMITE_ATINGIDO' then
 raise exception 'I71_HOUR_BOUNDARY_BYPASS: %',s;end if;
end $verify$;
reset role;
\echo 'PASS I71-04: 59-minute requests remain counted despite fixed hour boundary'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000004',true);
do $verify$ declare s jsonb;begin
 s:=public.s1_71_exportar_resumo('lotes',
 '86320000-0000-4000-8000-000000000001',null,1);
 if s->>'estado'<>'OK' or jsonb_array_length(s->'linhas')<>1 then
 raise exception 'I71_MGR4_OWN_REMAINING_BUDGET_WRONG: %',s;end if;
 s:=public.s1_71_exportar_resumo('canais',
 '86320000-0000-4000-8000-000000000001',null,1);
 if s->>'estado'<>'OK' or jsonb_array_length(s->'linhas')<>1
 then raise exception 'I71_MANAGER_OTHER_KIND_DENIED: %',s;end if;
end $verify$;
reset role;
\echo 'PASS I71-05: per-type and per-actor rolling quotas remain independent; second manager retains own budget'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000003',true);
do $verify$declare s jsonb;begin
 s:=public.s1_71_exportar_resumo('lotes',
 '86320000-0000-4000-8000-000000000001',null,1);
 if s->>'estado'<>'VAZIO' or s->'linhas'<>'[]'::jsonb
 then raise exception 'I71_CONSULTANT_INFO_LEAK';end if;
 begin
 perform * from public.s1_69_exportar_lotes(
  '86320000-0000-4000-8000-000000000001',null,1);
 raise exception 'I71_OLD_RPC_STILL_ACCESSIBLE';
 exception when insufficient_privilege then null;end;
end $verify$;
reset role;
\echo 'PASS I71-06: exception-only consultant learns no exports and old I69 bypass closed'

do $verify$begin
 if (select count(*) from pg_catalog.pg_attribute a
 join pg_catalog.pg_class c on c.oid=a.attrelid
 join pg_catalog.pg_namespace ns on ns.oid=c.relnamespace
 where ns.nspname='prumo_private' and c.relname='s1_71_export_recusas'
  and a.attname in ('lead_id','caso_id','telefone','conteudo','nome','email'))<>0
 or (select count(*) from prumo_s1_i65_test.exposicoes())<>0
 or has_table_privilege('authenticated','prumo_private.s1_71_export_recusas','SELECT')
 then raise exception 'I71_PRIVATE_DENIAL_AUDIT_EXPOSED';end if;
end $verify$;
\echo 'PASS I71-07: declined audit has only technical aggregate fields, no RLS bypass'

-- Retention test: preserve recent data, explicitly age one accepted row
-- and one refusal aggregate. PURGE is an intentional admin-only command.
update public.s1_70_export_reservas set
 registrada_em=pg_catalog.clock_timestamp()-interval '31 days'
 where id=(select min(id) from public.s1_70_export_reservas);
update prumo_private.s1_71_export_recusas set
 ultima_em=pg_catalog.clock_timestamp()-interval '31 days'
 where ator_id='86310000-0000-4000-8000-000000000001' and tipo='lotes';
do $verify$ declare a bigint;b bigint;begin
 select aceitos_excluidos,recusas_excluidas into a,b
 from prumo_private.s1_71_purgar_registros(pg_catalog.clock_timestamp());
 if a<>1 or b<>1 then raise exception 'I71_RETENTION_NOT_EXACT: % %',a,b;end if;
 if (select count(*) from public.s1_70_export_reservas)=0 then
 raise exception 'I71_RECENT_ACCEPTED_AUDIT_PURGED';end if;
end $verify$;
\echo 'PASS I71-08: explicit admin retention removes >30-day accepted and refused records only'

do $verify$begin
 if (select count(*) from pg_catalog.pg_policies
 where schemaname='public' and policyname like 's1_67_%')<>3
 or (select count(*) from pg_catalog.pg_policies
 where schemaname='public' and policyname like 's1_63_canon_%')<>8
 or has_function_privilege('authenticated',
  'prumo_private.s1_71_purgar_registros(timestamptz)','EXECUTE')
 or has_schema_privilege('authenticated','prumo_s1_interface','USAGE')
 then raise exception 'I71_PRIOR_RLS_OR_ADMIN_PURGE_LEAK';end if;
end $verify$;
\echo 'PASS I71-09: I63-I70 RLS maintained, admin-only retention never public'
