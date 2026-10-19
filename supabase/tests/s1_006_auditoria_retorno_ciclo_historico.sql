\set ON_ERROR_STOP on
-- AUD-01: casos HUMANOS vinculados a ciclos historicos vendidos/perdidos
-- nao podem sumir ao suspender operador. Somente dados ficticios; ROLLBACK.
begin;
insert into auth.users(id)
 select ('d1020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,3) i;
insert into public.atores(id) select id from auth.users where id::text like 'd1020000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,case when id::text like '%000000000003' then 'pendente' else 'ativo' end
 from public.atores where id::text like 'd1020000-%';
insert into public.concessionarias(id,nome_operacional) values
 ('d2020000-0000-4000-8000-000000000001','AUD Loja A'),
 ('d2020000-0000-4000-8000-000000000002','AUD Loja B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values
 ('d1020000-0000-4000-8000-000000000001','d2020000-0000-4000-8000-000000000001','operador'),
 ('d1020000-0000-4000-8000-000000000001','d2020000-0000-4000-8000-000000000002','operador'),
 ('d1020000-0000-4000-8000-000000000002','d2020000-0000-4000-8000-000000000001','operador'),
 ('d1020000-0000-4000-8000-000000000003','d2020000-0000-4000-8000-000000000002','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('d3020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i<=5 then 'd2020000-0000-4000-8000-000000000001'::uuid
 else 'd2020000-0000-4000-8000-000000000002'::uuid end,
 '+5581983000'||lpad(i::text,4,'0') from generate_series(1,7) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('d4020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 l.concessionaria_id,l.id,
 case when i in (1,2,6,7) then 'vendido'
 when i in (3,4) then 'perdido' else 'cadastro enviado ao banco' end
 from generate_series(1,7) i
 join public.leads_loja l on l.id=('d3020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id,motivo_simulado)
 select ('d5020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 c.concessionaria_id,c.lead_id,c.id,
 case when i in(2,6) then 'retorno_pos_venda'
 when i=4 then 'revisao_humana'
 when i=5 then 'retorno_pos_remessa' else null end
 from generate_series(1,7) i
 join public.ciclos_comerciais c on c.id=('d4020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select concessionaria_id,id,'d1020000-0000-4000-8000-000000000001'
 from public.casos_humanos where id::text like 'd5020000-%';
\echo 'PASS AUD1-01: novos casos de retorno e casos terminais historicos criados'
update public.equipe_prumo_s1 set estado='suspenso'
 where ator_id='d1020000-0000-4000-8000-000000000001';
do $chk$
begin
 if (select count(*) from public.atribuicoes_humanas
  where operador_id='d1020000-0000-4000-8000-000000000002'
   and encerrada_em is null and caso_id::text like 'd5020000-%')<>3
 or (select count(*) from prumo_private.s1_remanejamento_historico
  where caso_id::text like 'd5020000-%' and resultado='REDISTRIBUIDO')<>3
 or (select count(*) from prumo_private.s1_remanejamento_historico
  where caso_id::text like 'd5020000-%' and resultado='ENCERRADO_HISTORICO')<>3
 or (select count(*) from prumo_private.s1_remanejamento_pendencias
  where caso_id::text like 'd5020000-%')<>1
 then raise exception 'AUD1-02 suspensao descartou retorno humano';end if;
 if exists(select 1 from public.atribuicoes_humanas
  where operador_id='d1020000-0000-4000-8000-000000000001'
   and encerrada_em is null and caso_id::text like 'd5020000-%')
 then raise exception 'AUD1-02 suspenso ficou titular';end if;
end $chk$;
\echo 'PASS AUD1-02: pos-venda, revisao pos-perda e pos-remessa em A seguem humanos'
do $chk$
begin
 if (select count(*) from public.atribuicoes_humanas
  where caso_id in ('d5020000-0000-4000-8000-000000000001',
   'd5020000-0000-4000-8000-000000000003',
   'd5020000-0000-4000-8000-000000000007')
  and encerrada_em is null)<>0
 or (select count(*) from public.atribuicoes_humanas
  where caso_id in ('d5020000-0000-4000-8000-000000000002',
   'd5020000-0000-4000-8000-000000000004',
   'd5020000-0000-4000-8000-000000000005')
  and encerrada_em is null)<>3
 then raise exception 'AUD1-03 razao de retorno confundida com ciclo antigo';end if;
end $chk$;
\echo 'PASS AUD1-03: marcador S0 determina caso reaberto, nao somente status comercial'
-- Em B retorno pos-venda sem outro operador fica protegido. Ativar O3 B recupera.
update public.equipe_prumo_s1 set estado='ativo'
 where ator_id='d1020000-0000-4000-8000-000000000003';
do $chk$
begin
 if (select count(*) from public.atribuicoes_humanas
  where caso_id='d5020000-0000-4000-8000-000000000006'
  and operador_id='d1020000-0000-4000-8000-000000000003'
  and encerrada_em is null)<>1
 or exists(select 1 from prumo_private.s1_remanejamento_pendencias
  where caso_id='d5020000-0000-4000-8000-000000000006')
 or (select count(*) from prumo_private.s1_recuperacao_fila_historico
  where caso_id='d5020000-0000-4000-8000-000000000006'
   and resultado='RECUPERADO')<>1
 then raise exception 'AUD1-04 pos-venda na fila nao recuperado';end if;
 if (select status_comercial from public.ciclos_comerciais
   where id='d4020000-0000-4000-8000-000000000006')<>'vendido'
 then raise exception 'AUD1-04 reescreveu ciclo vendido';end if;
end $chk$;
\echo 'PASS AUD1-04: fila pos-venda B recuperada sem alterar venda historica'
-- Injetar pendencia historica de ciclo vendido sem nova solicitacao:
-- nao abrir automaticamente uma fila comercial, apenas encerrar residual.
insert into prumo_private.s1_remanejamento_pendencias(
 concessionaria_id,caso_id,operador_anterior,motivo)
 values('d2020000-0000-4000-8000-000000000002',
 'd5020000-0000-4000-8000-000000000007',
 'd1020000-0000-4000-8000-000000000001','EQUIPE_INATIVA');
do $chk$ declare j jsonb;
begin
 j:=prumo_private.s1_recuperar_fila_protegida(
  'd2020000-0000-4000-8000-000000000002',25);
 if (j->>'terminal_closed')::integer<>1
 or (select count(*) from public.atribuicoes_humanas
  where caso_id='d5020000-0000-4000-8000-000000000007'
   and encerrada_em is null)<>0
 then raise exception 'AUD1-05 vendeu novamente por fila %',j;end if;
end $chk$;
\echo 'PASS AUD1-05: historico terminal comum nao renasce ao processar fila'
set local role authenticated;
select set_config('request.jwt.claim.sub','d1020000-0000-4000-8000-000000000003',true);
do $chk$
begin
 if (select count(*) from public.casos_humanos)<>1
 or exists(select 1 from public.casos_humanos
    where concessionaria_id='d2020000-0000-4000-8000-000000000001')
 then raise exception 'AUD1-06 vazamento A para B';end if;
end $chk$;
\echo 'PASS AUD1-06: operador B enxerga apenas retorno humano B'
reset role;
do $chk$ begin
 if (select count(*) from public.ciclos_comerciais
  where id::text like 'd4020000-%' and status_comercial in ('vendido','perdido'))<>6
 then raise exception 'AUD1-07 ciclo original foi alterado';end if;
end $chk$;
\echo 'PASS AUD1-07: nenhum ciclo antigo reclassificado por remanejamento'
rollback;
