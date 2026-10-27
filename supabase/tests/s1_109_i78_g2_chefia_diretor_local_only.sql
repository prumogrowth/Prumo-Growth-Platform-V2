\set ON_ERROR_STOP on
-- I78/G2. Exclusive PG17 disposal; no hosted migrations, no authenticated RPC.
-- Current binding: S1 functional contract 22/10 + A2 23/10. I11 original
-- "global suspension" semantics are HISTORICAL, NOT product requirements.
begin;
set local lock_timeout='4s';
set local statement_timeout='15s';

do $i78$ declare idx record;
begin
 select i.indisunique as is_unique,pg_catalog.pg_get_expr(i.indpred,i.indrelid) as predicate,
  pg_catalog.pg_get_indexdef(c.oid) as definition
 into idx
 from pg_catalog.pg_class c
 join pg_catalog.pg_index i on i.indexrelid=c.oid
 where c.oid=to_regclass('prumo_private.s1_um_gestor_ativo_por_operador');
 if not found or not idx.is_unique
 or idx.predicate not ilike '%encerrado_em IS NULL%'
 or idx.definition not ilike '%(operador_id)%'
 then raise exception 'I78_ACTIVE_MANAGER_INDEX_DRIFT';end if;
end $i78$;
\echo 'PASS I78-G2-01: existing partial unique index enforces AT MOST one active principal manager'

insert into auth.users(id)
select ('f1780000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
from generate_series(1,7) i;
insert into public.atores(id)
select id from auth.users where id::text like 'f1780000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
select id,'ativo' from public.atores where id::text like 'f1780000-%';
insert into prumo_private.s1_responsaveis_plataforma(ator_id) values
('f1780000-0000-4000-8000-000000000001');
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values
('f1780000-0000-4000-8000-000000000002','f1780000-0000-4000-8000-000000000004'),
('f1780000-0000-4000-8000-000000000003','f1780000-0000-4000-8000-000000000005');

do $i78$ begin
 if not prumo_private.s1_pode_administrar_operador(
  'f1780000-0000-4000-8000-000000000001',null,'adicionar_operador',
  'f1780000-0000-4000-8000-000000000006')
 or prumo_private.s1_pode_administrar_operador(
  'f1780000-0000-4000-8000-000000000002',null,'adicionar_operador',
  'f1780000-0000-4000-8000-000000000006')
 or prumo_private.s1_pode_administrar_operador(
  'f1780000-0000-4000-8000-000000000002',null,'adicionar_gestor',
  'f1780000-0000-4000-8000-000000000006')
 or prumo_private.s1_pode_administrar_operador(
  'f1780000-0000-4000-8000-000000000003',null,'suspender_temporariamente',
  'f1780000-0000-4000-8000-000000000004')
 then raise exception 'I78_DIRECTOR_MANAGER_BOUNDARY_DRIFT';end if;
end $i78$;
\echo 'PASS I78-G2-02: existing Director-only onboarding and Gestor team boundaries preserved'

do $i78$ begin
 begin
  insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values
  ('f1780000-0000-4000-8000-000000000003','f1780000-0000-4000-8000-000000000004');
  raise exception 'I78_DUPLICATE_ACCEPTED';
 exception when unique_violation then null; end;
 if (select count(*) from prumo_private.s1_gestor_operadores
     where operador_id='f1780000-0000-4000-8000-000000000004'
      and encerrado_em is null)<>1
 then raise exception 'I78_DUPLICATE_ACTIVE_AFTER_NEGATIVE';end if;
end $i78$;
\echo 'PASS I78-G2-03: second simultaneous ACTIVE management link rejected, no side effect'

do $i78$ begin
 -- This is a positive detection of a REAL gap, not acceptance of the product
 -- requirement exactly one. Director/onboarding lifecycle still unimplemented.
 if (select count(*) from prumo_private.s1_gestor_operadores
     where operador_id='f1780000-0000-4000-8000-000000000006'
       and encerrado_em is null)<>0
 then raise exception 'I78_FIXTURE_ORPHAN_INCORRECT';end if;
 if (select estado from public.equipe_prumo_s1
     where ator_id='f1780000-0000-4000-8000-000000000006')<>'ativo'
 then raise exception 'I78_ORPHAN_NOT_ACTIVE';end if;
end $i78$;
\echo 'PASS I78-G2-04: ACTIVE consultant without manager is structurally possible; EXACTLY ONE is NOT certified'

-- Test-only atomically versioned principal transfer. Never an official endpoint.
-- Qualification of a new Gestor with no existing subordinate remains a separate
-- identity/onboarding contract; this test uses an existing verified Gestor.
create function pg_temp.i78_transferir_chefia(
 p_diretor uuid,p_consultor uuid,p_anterior bigint,p_destino uuid)
returns text language plpgsql security invoker set search_path='' as $g$
declare n integer; old_manager uuid;current_rel bigint;
begin
 if current_user<>'postgres' or session_user<>'postgres' then
  raise exception 'I78_INTERNAL_ONLY' using errcode='42501';end if;
 if p_diretor is null or p_consultor is null or p_anterior is null
 or p_destino is null then raise exception 'I78_BAD_ARGUMENT' using errcode='22023';end if;
 -- Same person lock first; group relation changes below serialize through this row.
 perform 1 from public.equipe_prumo_s1 e
  where e.ator_id in (p_diretor,p_consultor,p_destino)
  order by e.ator_id for update of e;
 select count(*) into n from public.equipe_prumo_s1 e
  where e.ator_id in (p_diretor,p_consultor,p_destino) and e.estado='ativo';
 if n<>3 then raise exception 'I78_INACTIVE_ACTOR' using errcode='42501';end if;
 perform 1 from prumo_private.s1_responsaveis_plataforma r
  where r.ator_id=p_diretor and r.ativo for share of r;
 if not found then raise exception 'I78_DIRECTOR_REQUIRED' using errcode='42501';end if;
 if p_consultor=p_destino or p_consultor=p_diretor or p_destino=p_diretor
 or exists(select 1 from prumo_private.s1_responsaveis_plataforma r
       where r.ator_id=p_destino and r.ativo)
 or not exists(select 1 from prumo_private.s1_gestor_operadores s
       where s.gestor_id=p_destino and s.encerrado_em is null)
 then raise exception 'I78_DESTINATION_NOT_VERIFIED_MANAGER' using errcode='42501';end if;
 select g.id,g.gestor_id into current_rel,old_manager
  from prumo_private.s1_gestor_operadores g
  where g.operador_id=p_consultor and g.encerrado_em is null
  for update of g;
 if current_rel is distinct from p_anterior then
  raise exception 'I78_STALE_MANAGEMENT' using errcode='40001';end if;
 if old_manager=p_destino then
  raise exception 'I78_ALREADY_MANAGER' using errcode='40001';end if;
 update prumo_private.s1_gestor_operadores
  set encerrado_em=greatest(atribuido_em,pg_catalog.clock_timestamp())
  where id=current_rel and encerrado_em is null;
 insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values(p_destino,p_consultor);
 return 'TRANSFERRED_TEST_ONLY';
end $g$;

do $i78$ declare prev bigint;
begin
 select id into prev from prumo_private.s1_gestor_operadores
  where operador_id='f1780000-0000-4000-8000-000000000004' and encerrado_em is null;
 begin
  perform pg_temp.i78_transferir_chefia(
    'f1780000-0000-4000-8000-000000000002',
    'f1780000-0000-4000-8000-000000000004',prev,
    'f1780000-0000-4000-8000-000000000003');
  raise exception 'I78_MANAGER_WAS_DIRECTOR';
 exception when insufficient_privilege then null; end;
 if (select count(*) from prumo_private.s1_gestor_operadores
  where operador_id='f1780000-0000-4000-8000-000000000004' and encerrado_em is null)<>1
 then raise exception 'I78_DENIAL_CHANGED_CHEFIA';end if;
end $i78$;
\echo 'PASS I78-G2-05: test-only principal transfer denies Gestor acting as Diretor and preserves owner'

do $i78$ declare prev bigint;result text;
begin
 select id into prev from prumo_private.s1_gestor_operadores
  where operador_id='f1780000-0000-4000-8000-000000000004' and encerrado_em is null;
 result:=pg_temp.i78_transferir_chefia(
  'f1780000-0000-4000-8000-000000000001',
  'f1780000-0000-4000-8000-000000000004',prev,
  'f1780000-0000-4000-8000-000000000003');
 if result<>'TRANSFERRED_TEST_ONLY'
 or (select count(*) from prumo_private.s1_gestor_operadores
  where operador_id='f1780000-0000-4000-8000-000000000004'
    and encerrado_em is null and gestor_id='f1780000-0000-4000-8000-000000000003')<>1
 or (select count(*) from prumo_private.s1_gestor_operadores
  where operador_id='f1780000-0000-4000-8000-000000000004'
    and encerrado_em is not null)<>1
 then raise exception 'I78_TRANSFER_RESULT_INCORRECT';end if;
end $i78$;
\echo 'PASS I78-G2-06: Director-only candidate transfer keeps one active manager and closes old link'

-- Keep the previous manager credential observable by assigning a different
-- synthetic consultant; otherwise the conservative temporary role check
-- refuses the old manager BEFORE the intentionally stale CAS is reached.
-- I78-G2-04 already established that a formerly active orphan can exist.
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values('f1780000-0000-4000-8000-000000000002',
        'f1780000-0000-4000-8000-000000000006');

do $i78$ declare stale bigint;
begin
 select id into stale from prumo_private.s1_gestor_operadores
  where operador_id='f1780000-0000-4000-8000-000000000004'
    and encerrado_em is not null order by id limit 1;
 begin
  perform pg_temp.i78_transferir_chefia(
  'f1780000-0000-4000-8000-000000000001',
  'f1780000-0000-4000-8000-000000000004',stale,
  'f1780000-0000-4000-8000-000000000002');
  raise exception 'I78_STALE_CAS_ACCEPTED';
 exception when serialization_failure then null; end;
 if (select count(*) from prumo_private.s1_gestor_operadores
  where operador_id='f1780000-0000-4000-8000-000000000004' and encerrado_em is null)<>1
 then raise exception 'I78_STALE_CREATED_EXTRA_MANAGER';end if;
end $i78$;
\echo 'PASS I78-G2-07: stale principal CAS is rejected, unique active manager preserved'

do $i78$ begin
 if pg_catalog.has_table_privilege('authenticated',
  'prumo_private.s1_gestor_operadores','INSERT')
 or pg_catalog.has_table_privilege('authenticated',
  'prumo_private.s1_gestor_operadores','UPDATE')
 or pg_catalog.has_table_privilege('authenticated',
  'prumo_private.s1_responsaveis_plataforma','INSERT')
 then raise exception 'I78_DIRECT_API_DML_EXPOSURE';end if;
end $i78$;
\echo 'PASS I78-G2-08: no direct authenticated DML on authority or manager-link tables'

rollback;
\echo 'I78 8/8 tests in PG17 rollback, candidate function never persisted; G2 operationally PARTIAL'
