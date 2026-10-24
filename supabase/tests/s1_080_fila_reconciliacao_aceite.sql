\set ON_ERROR_STOP on
-- I56 PG17 disposable acceptance, synthetic customers, transaction rollback.
begin;
insert into auth.users(id) values('78710000-0000-4000-8000-000000000001');
insert into public.atores(id) values('78710000-0000-4000-8000-000000000001');
insert into public.equipe_prumo_s1(ator_id,estado) values('78710000-0000-4000-8000-000000000001','ativo');
insert into public.concessionarias(id,nome_operacional) values('78720000-0000-4000-8000-000000000001','I56 disposable');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('78710000-0000-4000-8000-000000000001','78720000-0000-4000-8000-000000000001','gestor');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('78730000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 '78720000-0000-4000-8000-000000000001',
 '+55818856'||lpad(i::text,5,'0') from generate_series(1,3) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('78740000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 '78720000-0000-4000-8000-000000000001',
 ('78730000-0000-4000-8000-'||lpad((case when i=4 then 3 else i end)::text,12,'0'))::uuid,
 'aguardando primeiro disparo' from generate_series(1,4) i;
do $t$ begin
 if exists(select 1 from prumo_private.s0_fila_humana where ciclo_id::text like '78740000-%')
 then raise exception 'I56 false signal';end if;
end $t$;
\echo 'PASS I56-01: no explicit signal => no queue'
update public.ciclos_comerciais set status_comercial='em atendimento pelo operador'
 where id::text like '78740000-%';
insert into public.casos_humanos(concessionaria_id,lead_id,ciclo_id)
 values('78720000-0000-4000-8000-000000000001','78730000-0000-4000-8000-000000000001','78740000-0000-4000-8000-000000000001');
set constraints s0_fila_reconciliar_i56 immediate;
do $t$ begin
 if (select estado||':'||versao from prumo_private.s0_fila_humana
 where ciclo_id='78740000-0000-4000-8000-000000000001')<>'reconciliado:2'
 or (select count(*) from prumo_private.s0_fila_humana_eventos
 where ciclo_id='78740000-0000-4000-8000-000000000001' and resultado='RECONCILIADO')<>1
 then raise exception 'I56 missing reconciliation';end if;
end $t$;
\echo 'PASS I56-02: external case reconciled and audited with CAS'
set constraints s0_fila_reconciliar_i56 deferred;
do $t$ declare v jsonb;begin
 v:=prumo_private.s0_fila_assumir('78710000-0000-4000-8000-000000000001',
 '78720000-0000-4000-8000-000000000001',
 '78740000-0000-4000-8000-000000000002',1);
 if v->>'outcome'<>'CLAIMED_BY_MANAGER' then raise exception 'I56 claim %',v;end if;
end $t$;
set constraints s0_fila_reconciliar_i56 immediate;
do $t$ begin
 if (select estado||':'||versao from prumo_private.s0_fila_humana
 where ciclo_id='78740000-0000-4000-8000-000000000002')<>'atribuido:2'
 or exists(select 1 from prumo_private.s0_fila_humana_eventos
 where ciclo_id='78740000-0000-4000-8000-000000000002' and resultado='RECONCILIADO')
 then raise exception 'I56 falsely reconciled claim';end if;
end $t$;
\echo 'PASS I56-03: legitimate I54 claim stays assigned, no false event'
do $t$ begin
 begin
  insert into public.casos_humanos(concessionaria_id,lead_id,ciclo_id)
  values('78720000-0000-4000-8000-000000000001',
  '78730000-0000-4000-8000-000000000002',
  '78740000-0000-4000-8000-000000000002');
  raise exception 'I56 duplicate accepted';
 exception when unique_violation then null;end;
end $t$;
\echo 'PASS I56-04: same-cycle second case rejected'
insert into public.casos_humanos(concessionaria_id,lead_id,ciclo_id)
 values('78720000-0000-4000-8000-000000000001','78730000-0000-4000-8000-000000000003','78740000-0000-4000-8000-000000000003');
do $t$ begin
 if (select count(*) from prumo_private.s0_fila_humana
 where ciclo_id in ('78740000-0000-4000-8000-000000000003',
 '78740000-0000-4000-8000-000000000004')
 and estado='reconciliado' and versao=2)<>2
 then raise exception 'I56 did not reconcile second cycle';end if;
end $t$;
\echo 'PASS I56-05: all pending cycles of same lead reconciled'
do $t$ declare v jsonb;begin
 v:=prumo_private.s0_fila_assumir('78710000-0000-4000-8000-000000000001',
 '78720000-0000-4000-8000-000000000001',
 '78740000-0000-4000-8000-000000000004',1);
 if v->>'outcome'<>'CONFLICT' then raise exception 'I56 stale CAS %',v;end if;
 if has_function_privilege('authenticated','prumo_private.s0_fila_reconciliar_i56()','EXECUTE')
 or has_function_privilege('authenticated','prumo_private.s0_caso_lead_lock_i56()','EXECUTE')
 then raise exception 'I56 direct caller access';end if;
end $t$;
\echo 'PASS I56-06: stale claim conflicts, trigger private'
rollback;
\echo 'I56 PG17 6/6 ACCEPTED (rollback)'
