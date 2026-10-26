-- I72 PG17 synthetic acceptance, nested after I71; outer I64 transaction ROLLBACK.
\ir s1_104_export_ledger_unexposed_local_only.sql
\echo 'PASS I72-01: reservation ledger moved outside published public schema; same RLS and grants'
do $check$ begin
 if to_regclass('public.s1_70_export_reservas') is not null
 or (select count(*) from pg_catalog.pg_policies
   where schemaname='prumo_export_ledger' and policyname='s1_70_reserva_propria')<>1
 or has_schema_privilege('authenticated','prumo_private','USAGE')
 then raise exception 'I72_DIRECT_SURFACE_REMAINED';end if;
end $check$;
\echo 'PASS I72-02: no public relation, existing restrictive auth boundary remains'

-- Legitimate manager can still invoke the original invoker function using
-- RLS; the PRIVATE ledger tracks only accepted requests.
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000004',true);
do $check$ declare a integer;b integer;s jsonb;begin
 select count(*) into a from prumo_export_ledger.s1_70_export_reservas;
 -- SELECT grant is intentionally absent: count must be checked as postgres,
 -- not by this user. The attempted SELECT above must be denied.
 raise exception 'I72_AUTHENTICATED_DIRECT_SELECT_NOT_DENIED';
exception when insufficient_privilege then
 s:=public.s1_71_exportar_resumo('lotes',
  '86320000-0000-4000-8000-000000000001',null,1);
 if s->>'estado'<>'OK' or jsonb_array_length(s->'linhas')<>1 then
  raise exception 'I72_INVOKER_EXPORT_BROKEN: %',s;end if;
end $check$;
reset role;
\echo 'PASS I72-03: manager original invoker export succeeds with no direct SELECT on ledger'
do $check$begin
 if not exists(select 1 from prumo_export_ledger.s1_70_export_reservas
  where ator_id='86310000-0000-4000-8000-000000000004' and tipo='lotes')
 then raise exception 'I72_ACCEPTED_RESERVATION_NOT_PERSISTED';end if;
end $check$;
\echo 'PASS I72-04: successful export still persists accepted reservation in internal ledger'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000003',true);
do $check$declare s jsonb;begin
 s:=public.s1_71_exportar_resumo('lotes',
 '86320000-0000-4000-8000-000000000001',null,1);
 if s->>'estado'<>'VAZIO' then
  raise exception 'I72_UNAUTHORIZED_EXPORTED: %',s;end if;
end $check$;
reset role;
\echo 'PASS I72-05: consultant without manager grant remains denied under same RLS'

do $check$declare aged_id bigint;removed bigint;begin
 select min(id) into aged_id from prumo_export_ledger.s1_70_export_reservas;
 update prumo_export_ledger.s1_70_export_reservas
 set registrada_em=pg_catalog.clock_timestamp()-interval '31 days'
 where id=aged_id;
 select aceitos_excluidos into removed
 from prumo_private.s1_71_purgar_registros(pg_catalog.clock_timestamp());
 if removed<>1 or exists(select 1 from prumo_export_ledger.s1_70_export_reservas
   where id=aged_id)
 then raise exception 'I72_RETENTION_OLD_TABLE_REFERENCE';end if;
end $check$;
\echo 'PASS I72-06: private I71 purge operates on relocated ledger without widening privileges'
