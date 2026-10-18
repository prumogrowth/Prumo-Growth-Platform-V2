\set ON_ERROR_STOP on
-- S1Q-01..10: recuperacao automatica de fila sob grants reais sinteticos.
-- PG17 local, transacao revertida integralmente; migration 042 aplicada.
begin;
insert into auth.users(id)
 select ('a1020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,4) i;
insert into public.atores(id)
 select id from auth.users where id::text like 'a1020000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id, case when id::text like '%000000000002' then 'pendente' else 'ativo' end
 from public.atores where id::text like 'a1020000-%';
insert into public.concessionarias(id,nome_operacional) values
 ('a2020000-0000-4000-8000-000000000001','S1Q Loja A ficticia'),
 ('a2020000-0000-4000-8000-000000000002','S1Q Loja B ficticia');
-- O1 responsavel inicial em A+B, O2 pendente em A, O3 apenas gestor A.
-- O4 ativo, sem concessao; seu grant B chegara depois.
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values
 ('a1020000-0000-4000-8000-000000000001','a2020000-0000-4000-8000-000000000001','operador'),
 ('a1020000-0000-4000-8000-000000000001','a2020000-0000-4000-8000-000000000002','operador'),
 ('a1020000-0000-4000-8000-000000000002','a2020000-0000-4000-8000-000000000001','operador'),
 ('a1020000-0000-4000-8000-000000000003','a2020000-0000-4000-8000-000000000001','gestor');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('a3020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i<=2 then 'a2020000-0000-4000-8000-000000000001'::uuid
 else 'a2020000-0000-4000-8000-000000000002'::uuid end,
 '+5581986000'||lpad(i::text,4,'0') from generate_series(1,4) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('a4020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 l.concessionaria_id,l.id,'em atendimento pelo operador'
 from generate_series(1,4) i
 join public.leads_loja l on l.id=('a3020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('a5020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 c.concessionaria_id,c.lead_id,c.id
 from generate_series(1,4) i
 join public.ciclos_comerciais c on c.id=('a4020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select concessionaria_id,id,'a1020000-0000-4000-8000-000000000001'
 from public.casos_humanos where id::text like 'a5020000-%';
\echo 'PASS S1Q-01: dois atendimentos A, dois B e operador elegivel pendente'
update public.equipe_prumo_s1 set estado='suspenso'
 where ator_id='a1020000-0000-4000-8000-000000000001';
do $t$ begin
 if (select count(*) from prumo_private.s1_remanejamento_pendencias
  where caso_id::text like 'a5020000-%')<>4
 or exists(select 1 from public.atribuicoes_humanas
  where caso_id::text like 'a5020000-%' and encerrada_em is null)
 then raise exception 'S1Q-02 casos nao protegidos';end if;
end $t$;
\echo 'PASS S1Q-02: suspensao protege quatro casos, gestor nao recebe automaticamente'
-- Reativacao O1 sem alternativo nao restaura sua propria carteira.
update public.equipe_prumo_s1 set estado='ativo'
 where ator_id='a1020000-0000-4000-8000-000000000001';
do $t$ begin
 if (select count(*) from prumo_private.s1_remanejamento_pendencias
  where caso_id::text like 'a5020000-%')<>4
 or exists(select 1 from public.atribuicoes_humanas
  where operador_id='a1020000-0000-4000-8000-000000000001'
   and encerrada_em is null and caso_id::text like 'a5020000-%')
 then raise exception 'S1Q-03 restaurou titular antigo';end if;
end $t$;
\echo 'PASS S1Q-03: reativar ex-operador nao recupera seus casos automaticamente'
-- A ativacao O2 dispara recuperacao de A; O1 nao e candidato por caso.
update public.equipe_prumo_s1 set estado='ativo'
 where ator_id='a1020000-0000-4000-8000-000000000002';
do $t$ begin
 if (select count(*) from public.atribuicoes_humanas
  where operador_id='a1020000-0000-4000-8000-000000000002'
   and encerrada_em is null and caso_id::text like 'a5020000-%')<>2
 or (select count(*) from prumo_private.s1_remanejamento_pendencias
  where caso_id::text like 'a5020000-%')<>2
 or (select count(*) from prumo_private.s1_recuperacao_fila_historico
  where caso_id::text like 'a5020000-%' and resultado='RECUPERADO')<>2
 then raise exception 'S1Q-04 ativacao nao recuperou A';end if;
end $t$;
\echo 'PASS S1Q-04: ativar operador autorizado recupera somente A automaticamente'
-- B: um ciclo agora foi vendido; gatilho de concessao nao deve reabrir.
update public.ciclos_comerciais set status_comercial='vendido'
 where id='a4020000-0000-4000-8000-000000000004';
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('a1020000-0000-4000-8000-000000000004',
        'a2020000-0000-4000-8000-000000000002','operador');
do $t$ begin
 if (select count(*) from prumo_private.s1_remanejamento_pendencias
  where caso_id::text like 'a5020000-%')<>0
 or (select count(*) from public.atribuicoes_humanas
  where caso_id='a5020000-0000-4000-8000-000000000003'
   and encerrada_em is null
   and operador_id='a1020000-0000-4000-8000-000000000004')<>1
 or exists(select 1 from public.atribuicoes_humanas
  where caso_id='a5020000-0000-4000-8000-000000000004' and encerrada_em is null)
 or (select count(*) from prumo_private.s1_recuperacao_fila_historico
  where caso_id::text like 'a5020000-%' and resultado='TERMINAL')<>1
 then raise exception 'S1Q-05 B ou venda incorreta';end if;
 if (select status_comercial from public.ciclos_comerciais
  where id='a4020000-0000-4000-8000-000000000004')<>'vendido'
 then raise exception 'S1Q-05 venda alterada';end if;
end $t$;
\echo 'PASS S1Q-05: grant novo recupera B; vendido permanece terminal e sem dono'
-- Inject synthetic stale pending while active assignment already exists.
insert into prumo_private.s1_remanejamento_pendencias(
 concessionaria_id,caso_id,operador_anterior,motivo)
 values('a2020000-0000-4000-8000-000000000001',
        'a5020000-0000-4000-8000-000000000001',
        'a1020000-0000-4000-8000-000000000001','EQUIPE_INATIVA');
do $t$ declare r jsonb;begin
 r:=prumo_private.s1_recuperar_fila_protegida(
   'a2020000-0000-4000-8000-000000000001',10);
 if (r->>'already_assigned')::integer<>1
 or (select count(*) from public.atribuicoes_humanas
  where caso_id='a5020000-0000-4000-8000-000000000001'
  and encerrada_em is null)<>1
 then raise exception 'S1Q-06 stale gerou atribuicao duplicada %',r;end if;
end $t$;
\echo 'PASS S1Q-06: pendencia stale limpa sem segundo titular'
do $t$ declare r jsonb;begin
 r:=prumo_private.s1_recuperar_fila_protegida(
  'a2020000-0000-4000-8000-000000000001',10);
 if (r->>'reassigned')::integer<>0 or (r->>'inspected')::integer<>0
 or (select count(*) from prumo_private.s1_recuperacao_fila_historico
  where caso_id::text like 'a5020000-%')<>5
 then raise exception 'S1Q-07 rerun nao idempotente %',r;end if;
end $t$;
\echo 'PASS S1Q-07: reexecucao nao duplica historico'
-- A mesma linha nao pode ser lida por uma concessionaria diferente.
set local role authenticated;
select set_config('request.jwt.claim.sub','a1020000-0000-4000-8000-000000000004',true);
do $t$ begin
 if (select count(*) from public.casos_humanos)<>1
 or exists(select 1 from public.casos_humanos
  where concessionaria_id='a2020000-0000-4000-8000-000000000001')
 then raise exception 'S1Q-08 vazamento multiloja';end if;
end $t$;
\echo 'PASS S1Q-08: receptor B somente enxerga B'
do $t$ begin
 begin
  perform prumo_private.s1_recuperar_fila_protegida(
   'a2020000-0000-4000-8000-000000000001',1);
  raise exception 'S1Q-09 authenticated acionou rotina privada';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1Q-09: operador autenticado nao executa recuperacao privada'
reset role;
do $t$ begin
 begin
  perform prumo_private.s1_recuperar_fila_protegida(null,10);
  raise exception 'S1Q-10 nulo aceito';
 exception when invalid_parameter_value then null;end;
 begin
  perform prumo_private.s1_recuperar_fila_protegida(
   'a2020000-0000-4000-8000-000000000001',0);
  raise exception 'S1Q-10 lote zero aceito';
 exception when invalid_parameter_value then null;end;
end $t$;
\echo 'PASS S1Q-10: entrada invalida recusada'
rollback;
