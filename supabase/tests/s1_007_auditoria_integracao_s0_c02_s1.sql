\set ON_ERROR_STOP on
-- AUD2: integrar a funcao S0 C02 de inbound simulado com S1 C11 real
-- em PG17 descartavel. Provas artificiais, sem Meta/Banco/cliente real.
begin;
insert into auth.users(id) values
 ('f1020000-0000-4000-8000-000000000001'),
 ('f1020000-0000-4000-8000-000000000002');
insert into public.atores(id)
 select id from auth.users where id::text like 'f1020000-%';
insert into public.concessionarias(id,nome_operacional) values
 ('f2020000-0000-4000-8000-000000000001','AUD2 loja ficticia');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('f2020000-0000-4000-8000-000000000010',
  'f2020000-0000-4000-8000-000000000001','AUD2 CANAL FICTICIO');
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like 'f1020000-%';
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 select id,'f2020000-0000-4000-8000-000000000001','operador'
 from public.atores where id::text like 'f1020000-%';
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('f3020000-0000-4000-8000-000000000001','f2020000-0000-4000-8000-000000000001','+5581982000001'),
 ('f3020000-0000-4000-8000-000000000002','f2020000-0000-4000-8000-000000000001','+5581982000002');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial) values
 ('f4020000-0000-4000-8000-000000000001','f2020000-0000-4000-8000-000000000001','f3020000-0000-4000-8000-000000000001','vendido'),
 ('f4020000-0000-4000-8000-000000000002','f2020000-0000-4000-8000-000000000001','f3020000-0000-4000-8000-000000000002','cadastro enviado ao banco');
do $t$ declare v jsonb;begin
 v:=prumo_private.receber_mensagem_sintetica(
 'f2020000-0000-4000-8000-000000000010','+5581982000001',
 'aud2-venda-001','Ola, preciso de atendimento humano apos venda');
 if v->>'roteamento'<>'HUMANO_PENDENTE' or v->>'caso_id' is null
 then raise exception 'AUD2-01 venda nao gerou caso humano %',v;end if;
 v:=prumo_private.receber_mensagem_sintetica(
 'f2020000-0000-4000-8000-000000000010','+5581982000002',
 'aud2-banco-001','Ola, tenho uma duvida da proposta enviada');
 if v->>'roteamento'<>'HUMANO_PENDENTE' or v->>'caso_id' is null
 then raise exception 'AUD2-01 banco nao gerou caso humano %',v;end if;
end $t$;
\echo 'PASS AUD2-01: inbound S0 abriu casos humanos para vendido e banco sem IA'
do $t$ begin
 if (select count(*) from public.casos_humanos
  where concessionaria_id='f2020000-0000-4000-8000-000000000001'
    and motivo_simulado='retorno_pos_venda')<>1
 or (select count(*) from public.casos_humanos
  where concessionaria_id='f2020000-0000-4000-8000-000000000001'
    and motivo_simulado='retorno_pos_remessa')<>1
 then raise exception 'AUD2-02 motivo real do S0 diverge da regra S1';end if;
end $t$;
\echo 'PASS AUD2-02: S0 C02 gera os mesmos marcadores usados pela S1'
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select concessionaria_id,id,'f1020000-0000-4000-8000-000000000001'
 from public.casos_humanos where concessionaria_id='f2020000-0000-4000-8000-000000000001';
update public.equipe_prumo_s1 set estado='suspenso'
 where ator_id='f1020000-0000-4000-8000-000000000001';
do $t$ begin
 if (select count(*) from public.atribuicoes_humanas
  where operador_id='f1020000-0000-4000-8000-000000000002'
   and encerrada_em is null
   and concessionaria_id='f2020000-0000-4000-8000-000000000001')<>2
 or (select count(*) from prumo_private.s1_remanejamento_historico
  where caso_id in(select id from public.casos_humanos
   where concessionaria_id='f2020000-0000-4000-8000-000000000001')
   and resultado='REDISTRIBUIDO')<>2
 then raise exception 'AUD2-03 reatribuicao de casos reais S0 falhou';end if;
end $t$;
\echo 'PASS AUD2-03: suspensao S1 remaneja os dois casos gerados por C02'
do $t$ declare j jsonb; begin
 j:=prumo_private.receber_mensagem_sintetica(
 'f2020000-0000-4000-8000-000000000010','+5581982000001',
 'aud2-venda-001','Ola, preciso de atendimento humano apos venda');
 if j->>'outcome'<>'ALREADY_APPLIED'
 or (select count(*) from public.casos_humanos
  where concessionaria_id='f2020000-0000-4000-8000-000000000001')<>2
 or (select count(*) from public.mensagens
  where concessionaria_id='f2020000-0000-4000-8000-000000000001'
   and direcao='entrada' and id_externo='aud2-venda-001')<>1
 then raise exception 'AUD2-04 replay inbound duplicou caso %',j;end if;
end $t$;
\echo 'PASS AUD2-04: replay de inbound nao duplica caso/atribuição'
do $t$ begin
 if (select count(*) from public.ciclos_comerciais
  where id='f4020000-0000-4000-8000-000000000001'
  and status_comercial='vendido')<>1
 or (select count(*) from public.ciclos_comerciais
  where id='f4020000-0000-4000-8000-000000000002'
  and status_comercial='cadastro enviado ao banco')<>1
 then raise exception 'AUD2-05 reescreveu status original do ciclo';end if;
end $t$;
\echo 'PASS AUD2-05: venda/remessa historica preservada no ciclo'
rollback;
