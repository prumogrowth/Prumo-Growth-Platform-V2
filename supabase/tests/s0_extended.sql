\set ON_ERROR_STOP on
begin;
insert into auth.users(id) values
('10000000-0000-4000-8000-000000000011'),('10000000-0000-4000-8000-000000000012'),
('10000000-0000-4000-8000-000000000013'),('10000000-0000-4000-8000-000000000014');
insert into public.atores(id) select id from auth.users;
insert into public.concessionarias(id,nome_operacional) values
('20000000-0000-4000-8000-000000000011','Loja A ficticia'),
('20000000-0000-4000-8000-000000000012','Loja B ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
('10000000-0000-4000-8000-000000000011','20000000-0000-4000-8000-000000000011','gestor'),
('10000000-0000-4000-8000-000000000012','20000000-0000-4000-8000-000000000012','gestor'),
('10000000-0000-4000-8000-000000000013','20000000-0000-4000-8000-000000000011','operador'),
('10000000-0000-4000-8000-000000000014','20000000-0000-4000-8000-000000000011','operador');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
('40000000-0000-4000-8000-000000000011','20000000-0000-4000-8000-000000000011','TEST-A'),
('40000000-0000-4000-8000-000000000012','20000000-0000-4000-8000-000000000012','TEST-B');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
('30000000-0000-4000-8000-000000000011','20000000-0000-4000-8000-000000000011','+5500000000011'),
('30000000-0000-4000-8000-000000000012','20000000-0000-4000-8000-000000000012','+5500000000011');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
('50000000-0000-4000-8000-000000000011','20000000-0000-4000-8000-000000000011','30000000-0000-4000-8000-000000000011'),
('50000000-0000-4000-8000-000000000012','20000000-0000-4000-8000-000000000012','30000000-0000-4000-8000-000000000012');
insert into public.lotes_importacao(id,concessionaria_id,chave_importacao) values
('60000000-0000-4000-8000-000000000011','20000000-0000-4000-8000-000000000011','lote1'),
('60000000-0000-4000-8000-000000000012','20000000-0000-4000-8000-000000000011','lote2');
insert into public.lotes_importacao(concessionaria_id,chave_importacao)
 values('20000000-0000-4000-8000-000000000011','lote1') on conflict do nothing;
insert into public.itens_lote(concessionaria_id,lote_id,ordinal_linha,lead_id) values
('20000000-0000-4000-8000-000000000011','60000000-0000-4000-8000-000000000011',1,'30000000-0000-4000-8000-000000000011'),
('20000000-0000-4000-8000-000000000011','60000000-0000-4000-8000-000000000012',1,'30000000-0000-4000-8000-000000000011');
insert into public.itens_lote(concessionaria_id,lote_id,ordinal_linha,lead_id)
 values('20000000-0000-4000-8000-000000000011','60000000-0000-4000-8000-000000000011',1,'30000000-0000-4000-8000-000000000011') on conflict do nothing;
insert into public.reencontros_lote(concessionaria_id,lote_id,lead_id) values
('20000000-0000-4000-8000-000000000011','60000000-0000-4000-8000-000000000012','30000000-0000-4000-8000-000000000011');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id) values
('70000000-0000-4000-8000-000000000011','20000000-0000-4000-8000-000000000011','30000000-0000-4000-8000-000000000011','50000000-0000-4000-8000-000000000011'),
('70000000-0000-4000-8000-000000000012','20000000-0000-4000-8000-000000000012','30000000-0000-4000-8000-000000000012','50000000-0000-4000-8000-000000000012');
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id) values
('20000000-0000-4000-8000-000000000011','70000000-0000-4000-8000-000000000011','10000000-0000-4000-8000-000000000013');
do $$ begin
 begin
  insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id) values
  ('20000000-0000-4000-8000-000000000011','70000000-0000-4000-8000-000000000011','10000000-0000-4000-8000-000000000014');
  raise exception 'FAIL dupla atribuicao';
 exception when unique_violation then null; end;
 begin
  insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id) values
  ('20000000-0000-4000-8000-000000000012','70000000-0000-4000-8000-000000000012','10000000-0000-4000-8000-000000000013');
  raise exception 'FAIL atribuicao cruzada';
 exception when check_violation then null; end;
end $$;
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id) values
('80000000-0000-4000-8000-000000000011','20000000-0000-4000-8000-000000000011','30000000-0000-4000-8000-000000000011','40000000-0000-4000-8000-000000000011','70000000-0000-4000-8000-000000000011'),
('80000000-0000-4000-8000-000000000012','20000000-0000-4000-8000-000000000012','30000000-0000-4000-8000-000000000012','40000000-0000-4000-8000-000000000012','70000000-0000-4000-8000-000000000012'),
('80000000-0000-4000-8000-000000000013','20000000-0000-4000-8000-000000000011','30000000-0000-4000-8000-000000000011','40000000-0000-4000-8000-000000000011',null);
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,conteudo_sintetico,id_externo) values
('20000000-0000-4000-8000-000000000011','80000000-0000-4000-8000-000000000011','40000000-0000-4000-8000-000000000011','70000000-0000-4000-8000-000000000011','entrada','Mensagem A ficticia','ext-A-1'),
('20000000-0000-4000-8000-000000000012','80000000-0000-4000-8000-000000000012','40000000-0000-4000-8000-000000000012','70000000-0000-4000-8000-000000000012','entrada','Mensagem B ficticia','ext-B-1'),
('20000000-0000-4000-8000-000000000011','80000000-0000-4000-8000-000000000013','40000000-0000-4000-8000-000000000011',null,'entrada','IA ficticia','ext-A-ia');
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,conteudo_sintetico,id_externo)
 values('20000000-0000-4000-8000-000000000011','80000000-0000-4000-8000-000000000011','40000000-0000-4000-8000-000000000011','70000000-0000-4000-8000-000000000011','entrada','Mensagem A repetida','ext-A-1')
 on conflict do nothing;
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,conteudo_sintetico,id_externo)
 values('20000000-0000-4000-8000-000000000011','80000000-0000-4000-8000-000000000011','40000000-0000-4000-8000-000000000011','70000000-0000-4000-8000-000000000011','entrada','Mesmo texto permitido','ext-A-2');
do $$ begin
 if (select count(*) from public.lotes_importacao where concessionaria_id='20000000-0000-4000-8000-000000000011')<>2
 or (select count(*) from public.itens_lote)<>2
 or (select count(*) from public.reencontros_lote)<>1
 or (select count(*) from public.leads_loja)<>2
 or (select count(*) from public.conversas)<>3
 or (select count(*) from public.mensagens)<>4 then raise exception 'FAIL importacao/inbound'; end if;
 begin
 insert into public.mensagens(concessionaria_id,conversa_id,canal_id,direcao,conteudo_sintetico,id_externo) values
 ('20000000-0000-4000-8000-000000000011','80000000-0000-4000-8000-000000000012','40000000-0000-4000-8000-000000000011','entrada','cruzado','bad');
 raise exception 'FAIL mensagem cruzada';
 exception when foreign_key_violation then null; end;
end $$;
\echo 'PASS S0-A2/A5: lotes, reencontro, canal e inbound idempotentes'
set local role authenticated;
select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000011',true);
do $$ begin
 if (select count(*) from public.conversas)<>2 or (select count(*) from public.mensagens)<>3
 then raise exception 'FAIL gestor D2'; end if;
end $$;
\echo 'PASS AP41-01/02/03: gestor A le D2 proprio completo'
select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000012',true);
do $$ begin
 if (select count(*) from public.conversas)<>1 or (select count(*) from public.mensagens)<>1
 then raise exception 'FAIL B isolation'; end if;
end $$;
\echo 'PASS: gestor B so loja B'
select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000014',true);
do $$ begin
 if (select count(*) from public.conversas)<>0 then raise exception 'FAIL OP nao atribuido'; end if;
 begin
 insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,origem,conteudo_sintetico,enviada_por)
 values('20000000-0000-4000-8000-000000000011','80000000-0000-4000-8000-000000000011','40000000-0000-4000-8000-000000000011','70000000-0000-4000-8000-000000000011','saida','simulado','nao autorizado','10000000-0000-4000-8000-000000000014');
 raise exception 'FAIL OP escreveu';
 exception when insufficient_privilege then null; end;
end $$;
\echo 'PASS: operador sem caso nao le/escreve'
select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000013',true);
do $$ begin
 if (select count(*) from public.conversas)<>1 then raise exception 'FAIL OP atribuido'; end if;
end $$;
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,origem,conteudo_sintetico,enviada_por)
 values('20000000-0000-4000-8000-000000000011','80000000-0000-4000-8000-000000000011','40000000-0000-4000-8000-000000000011','70000000-0000-4000-8000-000000000011','saida','simulado','texto do OP ficticio','10000000-0000-4000-8000-000000000013');
\echo 'PASS: operador atribuido grava apenas mensagem simulada'
reset role;
update public.atribuicoes_humanas set encerrada_em=now()
 where caso_id='70000000-0000-4000-8000-000000000011' and encerrada_em is null;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id) values
('20000000-0000-4000-8000-000000000011','70000000-0000-4000-8000-000000000011','10000000-0000-4000-8000-000000000011');
set local role authenticated;
select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000013',true);
do $$ begin
 if (select count(*) from public.conversas)<>0 then raise exception 'FAIL ex-OP le'; end if;
 begin
 insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,origem,conteudo_sintetico,enviada_por)
 values('20000000-0000-4000-8000-000000000011','80000000-0000-4000-8000-000000000011','40000000-0000-4000-8000-000000000011','70000000-0000-4000-8000-000000000011','saida','simulado','ex OP','10000000-0000-4000-8000-000000000013');
 raise exception 'FAIL ex-OP escreveu';
 exception when insufficient_privilege then null; end;
end $$;
select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000011',true);
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,origem,conteudo_sintetico,enviada_por)
 values('20000000-0000-4000-8000-000000000011','80000000-0000-4000-8000-000000000011','40000000-0000-4000-8000-000000000011','70000000-0000-4000-8000-000000000011','saida','simulado','gestor autoatribuido','10000000-0000-4000-8000-000000000011');
\echo 'PASS AP41-05/06/09: remanejamento e autoatribuicao'
reset role;
-- Integridade: um caso da loja A nao pode associar outro lead de A ao mesmo ciclo.
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('30000000-0000-4000-8000-000000000019','20000000-0000-4000-8000-000000000011','+5500000000019');
do $ begin
 begin
  insert into public.casos_humanos(concessionaria_id,lead_id,ciclo_id) values
  ('20000000-0000-4000-8000-000000000011','30000000-0000-4000-8000-000000000019','50000000-0000-4000-8000-000000000011');
  raise exception 'FAIL ciclo/caso associados a leads diferentes';
 exception when foreign_key_violation then null; end;
end $;
-- Oito status comerciais, versao e evento sao trilhas independentes.
update public.ciclos_comerciais set status_comercial='em atendimento pela IA',versao_registro=2
 where id='50000000-0000-4000-8000-000000000011';
insert into public.eventos_status_comercial(concessionaria_id,ciclo_id,versao_ciclo_apos,status_anterior,status_posterior)
 values('20000000-0000-4000-8000-000000000011','50000000-0000-4000-8000-000000000011',2,
 'aguardando primeiro disparo','em atendimento pela IA');
do $ begin
 begin
  insert into public.eventos_status_comercial(concessionaria_id,ciclo_id,versao_ciclo_apos,status_anterior,status_posterior)
  values('20000000-0000-4000-8000-000000000011','50000000-0000-4000-8000-000000000011',2,
  'aguardando primeiro disparo','em atendimento pela IA');
  raise exception 'FAIL evento duplicado por versao';
 exception when unique_violation then null; end;
end $;
\echo 'PASS: escopo lead-ciclo-caso e historico de status por versao'
-- Desligar concessao ainda durante a transacao: leitura e escrita devem cessar nas consultas seguintes.
update public.vinculos_papel_escopo set valido_ate=clock_timestamp()
 where ator_id='10000000-0000-4000-8000-000000000011' and papel='gestor';
set local role authenticated;
select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000011',true);
do $ begin
 if (select count(*) from public.conversas)<>0 then
  raise exception 'FAIL gestor sem concessao ainda le conversa'; end if;
 begin
  insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,origem,conteudo_sintetico,enviada_por)
  values('20000000-0000-4000-8000-000000000011','80000000-0000-4000-8000-000000000011',
  '40000000-0000-4000-8000-000000000011','70000000-0000-4000-8000-000000000011',
  'saida','simulado','gestor revogado','10000000-0000-4000-8000-000000000011');
  raise exception 'FAIL vinculo revogado ainda escreve';
 exception when insufficient_privilege then null; end;
end $;
\echo 'PASS: concessao revogada invalida direitos em operacao seguinte'
reset role;
rollback;
