\set ON_ERROR_STOP on
-- I54: real S0 human-handoff signal, versioned queue and canonical I52 guard.
-- All synthetic data. Entire proof rolls back on disposable PG17.
begin;
insert into auth.users(id)
 select ('78510000-0000-4000-8000-'||pg_catalog.lpad(i::text,12,'0'))::uuid
 from pg_catalog.generate_series(1,4) i;
insert into public.atores(id) select id from auth.users
 where id::text like '78510000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like '78510000-%';
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values('78510000-0000-4000-8000-000000000001','78510000-0000-4000-8000-000000000003'),
 ('78510000-0000-4000-8000-000000000001','78510000-0000-4000-8000-000000000004');
insert into public.concessionarias(id,nome_operacional)
 values('78520000-0000-4000-8000-000000000001','I54 Loja A'),
 ('78520000-0000-4000-8000-000000000002','I54 Loja B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('78510000-0000-4000-8000-000000000001','78520000-0000-4000-8000-000000000001','gestor'),
 ('78510000-0000-4000-8000-000000000002','78520000-0000-4000-8000-000000000002','gestor'),
 ('78510000-0000-4000-8000-000000000003','78520000-0000-4000-8000-000000000001','operador'),
 ('78510000-0000-4000-8000-000000000004','78520000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('78530000-0000-4000-8000-'||pg_catalog.lpad(i::text,12,'0'))::uuid,
 case when i=4 then '78520000-0000-4000-8000-000000000002'::uuid
 else '78520000-0000-4000-8000-000000000001'::uuid end,
 '+55818854'||pg_catalog.lpad(i::text,5,'0')
 from pg_catalog.generate_series(1,6) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('78540000-0000-4000-8000-'||pg_catalog.lpad(i::text,12,'0'))::uuid,
 case when i=4 then '78520000-0000-4000-8000-000000000002'::uuid
 else '78520000-0000-4000-8000-000000000001'::uuid end,
 ('78530000-0000-4000-8000-'||pg_catalog.lpad(i::text,12,'0'))::uuid,
 'aguardando primeiro disparo'
 from pg_catalog.generate_series(1,6) i;
do $t$
begin
 if exists(select 1 from prumo_private.s0_fila_humana
   where ciclo_id::text like '78540000-%') then
  raise exception 'I54 fabricated queue from absence of case without signal';end if;
end $t$;
\echo 'PASS I54-01: leads and cycles without explicit human event are NOT a queue'

-- Once a human case already exists, no new case-less queue may appear.
insert into public.casos_humanos(concessionaria_id,lead_id,ciclo_id)
 values('78520000-0000-4000-8000-000000000001',
 '78530000-0000-4000-8000-000000000005',
 '78540000-0000-4000-8000-000000000005');
update public.ciclos_comerciais set status_comercial='em atendimento pelo operador'
 where id in ('78540000-0000-4000-8000-000000000001',
 '78540000-0000-4000-8000-000000000002',
 '78540000-0000-4000-8000-000000000003',
 '78540000-0000-4000-8000-000000000004',
 '78540000-0000-4000-8000-000000000005',
 '78540000-0000-4000-8000-000000000006');
do $t$
begin
 if (select count(*) from prumo_private.s0_fila_humana
  where ciclo_id::text like '78540000-%' and estado='pendente')<>5
 or (select count(*) from prumo_private.s0_fila_humana_eventos
  where ciclo_id::text like '78540000-%' and resultado='PENDENTE')<>5
 or exists(select 1 from prumo_private.s0_fila_humana
  where ciclo_id='78540000-0000-4000-8000-000000000005') then
  raise exception 'I54 S0 handoff signal invalid or old case shown in queue';end if;
end $t$;
\echo 'PASS I54-02: S0 commercial status explicitly produces five durable minimal queue events'

-- Pausing C1 must eliminate them from auto-distribution across ALL teams.
select prumo_private.s1_definir_intake(
 '78510000-0000-4000-8000-000000000001',
 '78510000-0000-4000-8000-000000000003',true,1);
do $t$
declare r jsonb;
begin
 r:=prumo_private.s0_fila_distribuir(
 '78520000-0000-4000-8000-000000000001',
 '78540000-0000-4000-8000-000000000001',1);
 if r->>'outcome'<>'ASSIGNED_NEW'
 or r->>'operator_id'<>'78510000-0000-4000-8000-000000000004'
 or (select count(*) from public.atribuicoes_humanas a
   join public.casos_humanos h on h.id=a.caso_id
   where h.ciclo_id='78540000-0000-4000-8000-000000000001'
   and a.operador_id='78510000-0000-4000-8000-000000000004'
   and a.encerrada_em is null)<>1 then
  raise exception 'I54 assigned to paused or unauthorized consultant: %',r;end if;
 if (prumo_private.s0_fila_distribuir(
 '78520000-0000-4000-8000-000000000001',
 '78540000-0000-4000-8000-000000000001',1)->>'outcome')<>'CONFLICT'
 then raise exception 'I54 accepted duplicate distribution';end if;
end $t$;
\echo 'PASS I54-03: S0 auto-dispatch creates one real case/assignment, skips paused C1, CAS replay conflicts'

do $t$
declare r jsonb;
begin
 begin
 perform prumo_private.s0_fila_assumir(
 '78510000-0000-4000-8000-000000000002',
 '78520000-0000-4000-8000-000000000001',
 '78540000-0000-4000-8000-000000000002',1);
 raise exception 'I54 cross-store manager claimed unauthorized lead';
 exception when insufficient_privilege then null;end;
 r:=prumo_private.s0_fila_assumir(
 '78510000-0000-4000-8000-000000000001',
 '78520000-0000-4000-8000-000000000001',
 '78540000-0000-4000-8000-000000000002',1);
 if r->>'outcome'<>'CLAIMED_BY_MANAGER' or
 (select count(*) from public.atribuicoes_humanas a
  join public.casos_humanos h on h.id=a.caso_id
  where h.ciclo_id='78540000-0000-4000-8000-000000000002'
    and a.operador_id='78510000-0000-4000-8000-000000000001'
    and a.encerrada_em is null)<>1
 then raise exception 'I54 manual claim failed: %',r;end if;
end $t$;
\echo 'PASS I54-04: real manual manager claim requires exact shop, creates canonical case and assignment'

select prumo_private.s1_definir_intake(
 '78510000-0000-4000-8000-000000000001',
 '78510000-0000-4000-8000-000000000004',true,1);
do $t$
declare r jsonb;
begin
 r:=prumo_private.s0_fila_distribuir(
 '78520000-0000-4000-8000-000000000001',
 '78540000-0000-4000-8000-000000000003',1);
 if r->>'outcome'<>'QUEUED_UNOWNED'
 or exists(select 1 from public.casos_humanos h
  where h.ciclo_id='78540000-0000-4000-8000-000000000003')
 or (select count(*) from prumo_private.s0_fila_humana
   where ciclo_id='78540000-0000-4000-8000-000000000003'
   and estado='pendente' and versao=1)<>1 then
  raise exception 'I54 failed to preserve unowned queue: %',r;end if;
end $t$;
\echo 'PASS I54-05: no eligible consultant => queue remains pending, no case/owner fabricated'

select prumo_private.s1_definir_intake(
 '78510000-0000-4000-8000-000000000001',
 '78510000-0000-4000-8000-000000000004',false,2);
do $t$
declare r jsonb;
begin
 r:=prumo_private.s0_fila_distribuir(
 '78520000-0000-4000-8000-000000000001',
 '78540000-0000-4000-8000-000000000003',1);
 if r->>'outcome'<>'ASSIGNED_NEW'
 or r->>'operator_id'<>'78510000-0000-4000-8000-000000000004'
 then raise exception 'I54 intake resume not re-admitted: %',r;end if;
end $t$;
\echo 'PASS I54-06: resumed consultant can receive previously queued case once, CAS'

do $t$
declare r jsonb;
begin
 -- Shop B has no eligible consultant; manager B may claim personally.
 r:=prumo_private.s0_fila_distribuir(
 '78520000-0000-4000-8000-000000000002',
 '78540000-0000-4000-8000-000000000004',1);
 if r->>'outcome'<>'QUEUED_UNOWNED'
 then raise exception 'I54 cross-tenant candidate leaked: %',r;end if;
 begin
 perform prumo_private.s0_fila_assumir(
 '78510000-0000-4000-8000-000000000001',
 '78520000-0000-4000-8000-000000000002',
 '78540000-0000-4000-8000-000000000004',1);
 raise exception 'I54 manager A claimed B';
 exception when insufficient_privilege then null;end;
 r:=prumo_private.s0_fila_assumir(
 '78510000-0000-4000-8000-000000000002',
 '78520000-0000-4000-8000-000000000002',
 '78540000-0000-4000-8000-000000000004',1);
 if r->>'outcome'<>'CLAIMED_BY_MANAGER'
 then raise exception 'I54 B manager claim failed: %',r;end if;
end $t$;
\echo 'PASS I54-07: no cross-store assignment; only own manager can claim own shop'

do $t$
begin
 if (select count(*) from prumo_private.s0_fila_humana_eventos
  where ciclo_id::text like '78540000-%' and resultado='DISTRIBUIDO')<>2
 or (select count(*) from prumo_private.s0_fila_humana_eventos
  where ciclo_id::text like '78540000-%' and resultado='ASSUMIDO')<>2
 or (select count(*) from prumo_private.s0_fila_humana
  where ciclo_id::text like '78540000-%' and estado='atribuido')<>4
 or (select count(*) from public.casos_humanos h
  join public.atribuicoes_humanas a on a.caso_id=h.id
  where h.ciclo_id::text like '78540000-%' and a.encerrada_em is null)<>4
 or has_table_privilege('authenticated','prumo_private.s0_fila_humana','SELECT')
 or has_function_privilege('authenticated',
  'prumo_private.s0_fila_assumir(uuid,uuid,uuid,bigint)','EXECUTE')
 then raise exception 'I54 queue audit, unique ownership or ACL gap';end if;
end $t$;
\echo 'PASS I54-08: append-only handoff audit, four unique owners, no authenticated direct SQL privilege'
rollback;
\echo 'I54 8/8 PASS on real S0/S1 tables, all fictitious and rolled back'
