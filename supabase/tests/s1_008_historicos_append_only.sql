\set ON_ERROR_STOP on
-- S1H-01..07: auditoria append-only, fixtures ficticias, transacao descartada.
begin;
insert into auth.users(id) values
 ('e1020000-0000-4000-8000-000000000001'),
 ('e1020000-0000-4000-8000-000000000002');
insert into public.atores(id)
 select id from auth.users where id::text like 'e1020000-%';
insert into public.concessionarias(id,nome_operacional) values
 ('e2020000-0000-4000-8000-000000000001','S1H loja sintetica');
insert into public.equipe_prumo_s1(ator_id,estado) values
 ('e1020000-0000-4000-8000-000000000001','ativo'),
 ('e1020000-0000-4000-8000-000000000002','pendente');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('e1020000-0000-4000-8000-000000000001','e2020000-0000-4000-8000-000000000001','operador'),
 ('e1020000-0000-4000-8000-000000000002','e2020000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('e3020000-0000-4000-8000-000000000001','e2020000-0000-4000-8000-000000000001','+5581989000001');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial) values
 ('e4020000-0000-4000-8000-000000000001','e2020000-0000-4000-8000-000000000001','e3020000-0000-4000-8000-000000000001','em atendimento pelo operador');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id) values
 ('e5020000-0000-4000-8000-000000000001','e2020000-0000-4000-8000-000000000001','e3020000-0000-4000-8000-000000000001','e4020000-0000-4000-8000-000000000001');
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id) values
 ('e2020000-0000-4000-8000-000000000001','e5020000-0000-4000-8000-000000000001','e1020000-0000-4000-8000-000000000001');
\echo 'PASS S1H-01: titular inicial e dois estados de equipe registrados'
-- Eventos reais de negocio continuam acrescentando as linhas de historico.
update public.equipe_prumo_s1 set estado='suspenso'
 where ator_id='e1020000-0000-4000-8000-000000000001';
do $h$ begin
 if (select count(*) from prumo_private.s1_remanejamento_historico
  where caso_id='e5020000-0000-4000-8000-000000000001'
   and resultado='FILA_PROTEGIDA')<>1
 or (select count(*) from prumo_private.s1_remanejamento_pendencias
  where caso_id='e5020000-0000-4000-8000-000000000001')<>1
 then raise exception 'S1H-02 remanejamento parou ao proteger historico';end if;
end $h$;
\echo 'PASS S1H-02: suspensao gerou historia e fila normalmente'
update public.equipe_prumo_s1 set estado='ativo'
 where ator_id='e1020000-0000-4000-8000-000000000002';
do $h$ begin
 if (select count(*) from prumo_private.s1_recuperacao_fila_historico
  where caso_id='e5020000-0000-4000-8000-000000000001'
   and resultado='RECUPERADO')<>1
 or (select count(*) from public.atribuicoes_humanas
  where caso_id='e5020000-0000-4000-8000-000000000001'
   and operador_id='e1020000-0000-4000-8000-000000000002'
   and encerrada_em is null)<>1
 then raise exception 'S1H-03 recuperacao parou ao proteger historico';end if;
end $h$;
\echo 'PASS S1H-03: ativacao gerou historia e nova atribuicao normalmente'
-- Cada historico deve resistir ate a operacao privilegiada direta.
do $h$
declare r record;v_state text;
begin
 for r in
  select * from (values
   ('public.equipe_prumo_eventos_s1','estado_posterior = estado_posterior'),
   ('prumo_private.s1_remanejamento_historico','resultado = resultado'),
   ('prumo_private.s1_recuperacao_fila_historico','resultado = resultado')
  ) as x(tab,col)
 loop
  begin
   execute pg_catalog.format('UPDATE %s SET %s',r.tab,r.col);
   raise exception 'S1H-04 UPDATE not protected %',r.tab;
  exception when check_violation then
   get stacked diagnostics v_state = message_text;
   if v_state <> 'HISTORICO_S1_IMUTAVEL' then
    raise exception 'S1H-04 wrong update guard %: %',r.tab,v_state;
   end if;
  end;
 end loop;
end $h$;
\echo 'PASS S1H-04: update negado nas tres trilhas, inclusive no-op e dono postgres'
do $h$
declare r record;v_state text;
begin
 for r in select tab from (values
  ('public.equipe_prumo_eventos_s1'),
  ('prumo_private.s1_remanejamento_historico'),
  ('prumo_private.s1_recuperacao_fila_historico')) x(tab)
 loop
  begin
   execute pg_catalog.format('DELETE FROM %s',r.tab);
   raise exception 'S1H-05 DELETE not protected %',r.tab;
  exception when check_violation then
   get stacked diagnostics v_state = message_text;
   if v_state <> 'HISTORICO_S1_IMUTAVEL' then
    raise exception 'S1H-05 wrong delete guard %: %',r.tab,v_state;
   end if;
  end;
 end loop;
end $h$;
\echo 'PASS S1H-05: delete negado nas tres trilhas, sem apagar eventos'
do $h$
declare r record;v_state text;
begin
 for r in select tab from (values
  ('public.equipe_prumo_eventos_s1'),
  ('prumo_private.s1_remanejamento_historico'),
  ('prumo_private.s1_recuperacao_fila_historico')) x(tab)
 loop
  begin
   execute pg_catalog.format('TRUNCATE %s',r.tab);
   raise exception 'S1H-06 TRUNCATE not protected %',r.tab;
  exception when check_violation then
   get stacked diagnostics v_state = message_text;
   if v_state <> 'HISTORICO_S1_IMUTAVEL' then
    raise exception 'S1H-06 wrong truncate guard %: %',r.tab,v_state;
   end if;
  end;
 end loop;
end $h$;
\echo 'PASS S1H-06: truncate negado nas tres trilhas'
do $h$
begin
 if (select count(*) from public.equipe_prumo_eventos_s1
  where ator_id::text like 'e1020000-%')<>4
 or (select count(*) from prumo_private.s1_remanejamento_historico
  where caso_id='e5020000-0000-4000-8000-000000000001')<>1
 or (select count(*) from prumo_private.s1_recuperacao_fila_historico
  where caso_id='e5020000-0000-4000-8000-000000000001')<>1
 then raise exception 'S1H-07 conteudo foi alterado';end if;
end $h$;
\echo 'PASS S1H-07: linhas originais de historico conservadas'
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub','e1020000-0000-4000-8000-000000000002',true);
do $h$ begin
 if (select count(*) from public.casos_humanos)<>1
 then raise exception 'S1H-08 atribuido perdeu leitura legitima';end if;
 begin
  perform 1 from public.equipe_prumo_eventos_s1 limit 1;
  raise exception 'S1H-08 eventos expos a authenticated';
 exception when insufficient_privilege then null;end;
end $h$;
\echo 'PASS S1H-08: leitura autorizada do caso, mas historico RH nao exposto'
reset role;
rollback;
