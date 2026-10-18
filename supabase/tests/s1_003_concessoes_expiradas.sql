\set ON_ERROR_STOP on
-- S1X-01..07: expiracao natural SEM UPDATE de grant.
-- Dados sintéticos, ROLLBACK integral; migration 040 ja aplicada.
begin;
insert into auth.users(id) values
 ('71020000-0000-4000-8000-000000000001'),
 ('71020000-0000-4000-8000-000000000002');
insert into public.atores(id)
 select id from auth.users where id::text like '71020000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like '71020000-%';
insert into public.concessionarias(id,nome_operacional) values
 ('72020000-0000-4000-8000-000000000001','S1X Loja A'),
 ('72020000-0000-4000-8000-000000000002','S1X Loja B'),
 ('72020000-0000-4000-8000-000000000003','S1X Loja C');
-- Usuario O1 mantem A; em B/C grant expira pelo relogio, sem trigger UPDATE.
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel,valido_ate)
 values
 ('71020000-0000-4000-8000-000000000001','72020000-0000-4000-8000-000000000001','operador',null),
 ('71020000-0000-4000-8000-000000000001','72020000-0000-4000-8000-000000000002','operador',statement_timestamp()+interval '300 milliseconds'),
 ('71020000-0000-4000-8000-000000000001','72020000-0000-4000-8000-000000000003','operador',statement_timestamp()+interval '300 milliseconds'),
 ('71020000-0000-4000-8000-000000000002','72020000-0000-4000-8000-000000000002','operador',null);
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('73020000-0000-4000-8000-000000000001','72020000-0000-4000-8000-000000000001','+5581000099991'),
 ('73020000-0000-4000-8000-000000000002','72020000-0000-4000-8000-000000000002','+5581000099991'),
 ('73020000-0000-4000-8000-000000000003','72020000-0000-4000-8000-000000000003','+5581000099991');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial) values
 ('74020000-0000-4000-8000-000000000001','72020000-0000-4000-8000-000000000001','73020000-0000-4000-8000-000000000001','em atendimento pelo operador'),
 ('74020000-0000-4000-8000-000000000002','72020000-0000-4000-8000-000000000002','73020000-0000-4000-8000-000000000002','em atendimento pelo operador'),
 ('74020000-0000-4000-8000-000000000003','72020000-0000-4000-8000-000000000003','73020000-0000-4000-8000-000000000003','em atendimento pelo operador');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id) values
 ('75020000-0000-4000-8000-000000000001','72020000-0000-4000-8000-000000000001','73020000-0000-4000-8000-000000000001','74020000-0000-4000-8000-000000000001'),
 ('75020000-0000-4000-8000-000000000002','72020000-0000-4000-8000-000000000002','73020000-0000-4000-8000-000000000002','74020000-0000-4000-8000-000000000002'),
 ('75020000-0000-4000-8000-000000000003','72020000-0000-4000-8000-000000000003','73020000-0000-4000-8000-000000000003','74020000-0000-4000-8000-000000000003');
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select concessionaria_id,id,'71020000-0000-4000-8000-000000000001'
 from public.casos_humanos where id::text like '75020000-%';
\echo 'PASS S1X-01: três atribuições válidas antes do vencimento'
select pg_sleep(0.45);
-- Antes da reconciliacao, a concessao de B/C ja foi perdida;
-- RLS restringe acesso mesmo que a atribuicao ainda esteja ativa.
set local role authenticated;
select set_config('request.jwt.claim.sub','71020000-0000-4000-8000-000000000001',true);
do $chk$
begin
 if (select count(*) from public.casos_humanos)<>1 then
  raise exception 'S1X-02 RLS nao respeita expiração pelo relogio';end if;
end $chk$;
\echo 'PASS S1X-02: RLS nega B/C antes de reconciliar, preserva A'
reset role;
do $chk$
begin
 if (select count(*) from public.atribuicoes_humanas
  where operador_id='71020000-0000-4000-8000-000000000001'
  and encerrada_em is null)<>3
 then raise exception 'S1X-03 evento indevido de expiracao';end if;
end $chk$;
\echo 'PASS S1X-03: sem UPDATE, atribuições aguardavam varredura'
do $chk$
declare v jsonb;
begin
 v:=prumo_private.s1_reconciliar_elegibilidade_vencida(1);
 if (v->>'groups_checked')::integer<>1
 or (v->>'cases_reassigned_or_closed')::integer<>1
 then raise exception 'S1X-04 batch 1 retorno %',v;end if;
 v:=prumo_private.s1_reconciliar_elegibilidade_vencida(1);
 if (v->>'groups_checked')::integer<>1
 or (v->>'cases_reassigned_or_closed')::integer<>1
 then raise exception 'S1X-04 batch 2 retorno %',v;end if;
 v:=prumo_private.s1_reconciliar_elegibilidade_vencida(1);
 if (v->>'groups_checked')::integer<>0
 or (v->>'cases_reassigned_or_closed')::integer<>0
 then raise exception 'S1X-04 repetição não idempotente %',v;end if;
end $chk$;
\echo 'PASS S1X-04: lotes limitados, remanejamento e rerun idempotente'
do $chk$
begin
 if (select count(*) from public.atribuicoes_humanas a
  where a.encerrada_em is null and a.operador_id='71020000-0000-4000-8000-000000000001'
  and a.concessionaria_id='72020000-0000-4000-8000-000000000001')<>1
 or (select count(*) from public.atribuicoes_humanas a
  where a.encerrada_em is null and a.operador_id='71020000-0000-4000-8000-000000000002'
  and a.concessionaria_id='72020000-0000-4000-8000-000000000002')<>1
 or (select count(*) from prumo_private.s1_remanejamento_pendencias p
  where p.concessionaria_id='72020000-0000-4000-8000-000000000003')<>1
 or (select count(*) from prumo_private.s1_remanejamento_historico h
  where h.operador_anterior='71020000-0000-4000-8000-000000000001'
   and h.motivo='ESCOPO_REVOGADO')<>2
 then raise exception 'S1X-05 A preservada, B redistribuida, C fila: falhou';end if;
end $chk$;
\echo 'PASS S1X-05: loja A preservada, B realocada, C fila protegida'
set local role authenticated;
select set_config('request.jwt.claim.sub','71020000-0000-4000-8000-000000000002',true);
do $chk$
begin
 if (select count(*) from public.casos_humanos)<>1
 then raise exception 'S1X-06 destino nao tem caso B autorizado';end if;
 begin
  perform prumo_private.s1_reconciliar_elegibilidade_vencida(1);
  raise exception 'S1X-06 chamada publica indevida';
 exception when insufficient_privilege then null;end;
end $chk$;
\echo 'PASS S1X-06: somente B acessível ao novo operador; runner privado negado'
reset role;
do $chk$
begin
 begin
  perform prumo_private.s1_reconciliar_elegibilidade_vencida(0);
  raise exception 'S1X-07 aceitou lote 0';
 exception when invalid_parameter_value then null;end;
end $chk$;
\echo 'PASS S1X-07: lote inválido recusado'
rollback;
