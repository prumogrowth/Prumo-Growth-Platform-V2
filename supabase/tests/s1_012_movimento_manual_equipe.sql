\set ON_ERROR_STOP on
-- S1M-01..12: intervenção de gestor sobre casos da equipe, nao lojas dele.
-- PG17 sintético descartável, transação revertida ao concluir.
begin;
insert into auth.users(id)
 select ('b1120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,8) i;
insert into public.atores(id) select id from auth.users where id::text like 'b1120000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like 'b1120000-%';
insert into prumo_private.s1_responsaveis_plataforma(ator_id)
 values('b1120000-0000-4000-8000-000000000006');
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values
 ('b1120000-0000-4000-8000-000000000001','b1120000-0000-4000-8000-000000000003'),
 ('b1120000-0000-4000-8000-000000000001','b1120000-0000-4000-8000-000000000004'),
 ('b1120000-0000-4000-8000-000000000001','b1120000-0000-4000-8000-000000000007'),
 ('b1120000-0000-4000-8000-000000000002','b1120000-0000-4000-8000-000000000005');
insert into public.concessionarias(id,nome_operacional) values
 ('b2120000-0000-4000-8000-000000000001','S1M loja A'),
 ('b2120000-0000-4000-8000-000000000002','S1M loja B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 select ('b1120000-0000-4000-8000-'||lpad(operador::text,12,'0'))::uuid,
 ('b2120000-0000-4000-8000-'||lpad(loja::text,12,'0'))::uuid,'operador'
 from (values (3,1),(3,2),(4,1),(4,2),(5,1),(5,2),(7,1),(8,2)) x(operador,loja);
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('b3120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('b2120000-0000-4000-8000-'||lpad((case when i in (2,3,5) then 2 else 1 end)::text,12,'0'))::uuid,
 '+5581981100'||lpad(i::text,4,'0') from generate_series(1,7) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('b4120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 l.concessionaria_id,l.id,
 case when i in (4,5) then 'vendido' else 'em atendimento pelo operador' end
 from generate_series(1,7) i join public.leads_loja l
 on l.id=('b3120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id,motivo_simulado)
 select ('b5120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 c.concessionaria_id,c.lead_id,c.id,
 case when i=5 then 'retorno_pos_venda' else null end
 from generate_series(1,7) i join public.ciclos_comerciais c
 on c.id=('b4120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select h.concessionaria_id,h.id,
 case when i=6 then 'b1120000-0000-4000-8000-000000000005'::uuid
 else 'b1120000-0000-4000-8000-000000000003'::uuid end
 from generate_series(1,7) i
 join public.casos_humanos h
 on h.id=('b5120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
\echo 'PASS S1M-01: duas equipes e operadores A+B; gestores sem grants das lojas'
do $t$ declare prev uuid; result jsonb;begin
 select id into prev from public.atribuicoes_humanas
 where caso_id='b5120000-0000-4000-8000-000000000001' and encerrada_em is null;
 result:=prumo_private.s1_mover_atendimento_da_equipe(
  'b1120000-0000-4000-8000-000000000001',
  'b2120000-0000-4000-8000-000000000001',
  'b5120000-0000-4000-8000-000000000001',
  prev,'b1120000-0000-4000-8000-000000000004');
 if result->>'outcome'<>'MOVED'
 or (select count(*) from public.atribuicoes_humanas
   where caso_id='b5120000-0000-4000-8000-000000000001'
   and encerrada_em is null and operador_id='b1120000-0000-4000-8000-000000000004')<>1
 then raise exception 'S1M-02 failed %',result;end if;
end $t$;
\echo 'PASS S1M-02: gestor sem loja própria move atendimento A dentro da equipe'
do $t$ declare prev uuid;begin
 select id into prev from public.atribuicoes_humanas
 where caso_id='b5120000-0000-4000-8000-000000000002' and encerrada_em is null;
 perform prumo_private.s1_mover_atendimento_da_equipe(
  'b1120000-0000-4000-8000-000000000001',
  'b2120000-0000-4000-8000-000000000002',
  'b5120000-0000-4000-8000-000000000002',
  prev,'b1120000-0000-4000-8000-000000000004');
 if (select count(*) from public.atribuicoes_humanas
  where caso_id='b5120000-0000-4000-8000-000000000002'
   and encerrada_em is null and operador_id='b1120000-0000-4000-8000-000000000004')<>1
 then raise exception 'S1M-03 B move failed';end if;
end $t$;
\echo 'PASS S1M-03: gestor mantém mesma chefia nos casos de A e B'
do $t$ declare prev uuid;begin
 select id into prev from public.atribuicoes_humanas
 where caso_id='b5120000-0000-4000-8000-000000000003' and encerrada_em is null;
 begin
  perform prumo_private.s1_mover_atendimento_da_equipe(
   'b1120000-0000-4000-8000-000000000001',
   'b2120000-0000-4000-8000-000000000002',
   'b5120000-0000-4000-8000-000000000003',
   prev,'b1120000-0000-4000-8000-000000000007');
  raise exception 'S1M-04 operator without B grant received B';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1M-04: operador da equipe sem grant B não recebe caso B'
do $t$ declare prev uuid;begin
 select id into prev from public.atribuicoes_humanas
 where caso_id='b5120000-0000-4000-8000-000000000007' and encerrada_em is null;
 begin
  perform prumo_private.s1_mover_atendimento_da_equipe(
   'b1120000-0000-4000-8000-000000000001',
   'b2120000-0000-4000-8000-000000000001',
   'b5120000-0000-4000-8000-000000000007',
   prev,'b1120000-0000-4000-8000-000000000005');
  raise exception 'S1M-05 other team got case';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1M-05: gestor não transfere para operador de OUTRA equipe'
do $t$ declare prev uuid;begin
 select id into prev from public.atribuicoes_humanas
 where caso_id='b5120000-0000-4000-8000-000000000006' and encerrada_em is null;
 begin
  perform prumo_private.s1_mover_atendimento_da_equipe(
   'b1120000-0000-4000-8000-000000000001',
   'b2120000-0000-4000-8000-000000000001',
   'b5120000-0000-4000-8000-000000000006',
   prev,'b1120000-0000-4000-8000-000000000004');
  raise exception 'S1M-06 managed someone elses operator';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1M-06: gestor não retira caso de operador fora da própria equipe'
do $t$ declare prev uuid;begin
 select id into prev from public.atribuicoes_humanas
 where caso_id='b5120000-0000-4000-8000-000000000004' and encerrada_em is null;
 begin
  perform prumo_private.s1_mover_atendimento_da_equipe(
   'b1120000-0000-4000-8000-000000000001',
   'b2120000-0000-4000-8000-000000000001',
   'b5120000-0000-4000-8000-000000000004',
   prev,'b1120000-0000-4000-8000-000000000004');
  raise exception 'S1M-07 historical sale reopened';
 exception when check_violation then null;end;
end $t$;
\echo 'PASS S1M-07: venda terminal original não é reaberta pela movimentação'
do $t$ declare prev uuid;begin
 select id into prev from public.atribuicoes_humanas
 where caso_id='b5120000-0000-4000-8000-000000000005' and encerrada_em is null;
 perform prumo_private.s1_mover_atendimento_da_equipe(
  'b1120000-0000-4000-8000-000000000001',
  'b2120000-0000-4000-8000-000000000002',
  'b5120000-0000-4000-8000-000000000005',
  prev,'b1120000-0000-4000-8000-000000000004');
 if (select status_comercial from public.ciclos_comerciais
  where id='b4120000-0000-4000-8000-000000000005')<>'vendido'
 or (select count(*) from public.atribuicoes_humanas
  where caso_id='b5120000-0000-4000-8000-000000000005'
  and operador_id='b1120000-0000-4000-8000-000000000004'
  and encerrada_em is null)<>1 then
  raise exception 'S1M-08 pós-venda humano lost';end if;
end $t$;
\echo 'PASS S1M-08: pós-venda humano move sem alterar o ciclo vendido'
do $t$ declare prev uuid;begin
 select id into prev from public.atribuicoes_humanas
 where caso_id='b5120000-0000-4000-8000-000000000001'
 and encerrada_em is not null limit 1;
 begin
  perform prumo_private.s1_mover_atendimento_da_equipe(
   'b1120000-0000-4000-8000-000000000001',
   'b2120000-0000-4000-8000-000000000001',
   'b5120000-0000-4000-8000-000000000001',
   prev,'b1120000-0000-4000-8000-000000000003');
  raise exception 'S1M-09 replay moved case backward';
 exception when invalid_parameter_value then null;end;
end $t$;
\echo 'PASS S1M-09: replay com id de atribuição antiga não reverte caso'
do $t$ declare prev uuid;begin
 select id into prev from public.atribuicoes_humanas
 where caso_id='b5120000-0000-4000-8000-000000000003' and encerrada_em is null;
 begin
  perform prumo_private.s1_mover_atendimento_da_equipe(
   'b1120000-0000-4000-8000-000000000001',
   'b2120000-0000-4000-8000-000000000001',
   'b5120000-0000-4000-8000-000000000003',
   prev,'b1120000-0000-4000-8000-000000000004');
  raise exception 'S1M-10 cross-shop move';
 exception when invalid_parameter_value then null;end;
end $t$;
\echo 'PASS S1M-10: um caso B não aceita mover usando loja A'
do $t$ begin
 if (select count(*) from prumo_private.s1_movimentos_manuais_historico
  where caso_id::text like 'b5120000-%')<>3
 or (select count(*) from public.atribuicoes_humanas
  where caso_id in ('b5120000-0000-4000-8000-000000000001',
   'b5120000-0000-4000-8000-000000000002',
   'b5120000-0000-4000-8000-000000000005')
   and encerrada_em is null)<>3
 or (select count(*) from public.vinculos_papel_escopo
  where ator_id='b1120000-0000-4000-8000-000000000004')<>2
 then raise exception 'S1M-11 move duplicated or changed grants';end if;
 begin
  delete from prumo_private.s1_movimentos_manuais_historico;
  raise exception 'S1M-11 history deletable';
 exception when check_violation then null;end;
end $t$;
\echo 'PASS S1M-11: 3 movimentos auditados e histórico append-only'
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 'b1120000-0000-4000-8000-000000000001',true);
do $t$ begin
 begin
  perform prumo_private.s1_mover_atendimento_da_equipe(
   'b1120000-0000-4000-8000-000000000006',
   'b2120000-0000-4000-8000-000000000001',
   'b5120000-0000-4000-8000-000000000007',
   '00000000-0000-4000-8000-000000000000',
   'b1120000-0000-4000-8000-000000000004');
  raise exception 'S1M-12 fake caller usable';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1M-12: função com solicitante explícito não exposta a authenticated'
reset role;
rollback;
