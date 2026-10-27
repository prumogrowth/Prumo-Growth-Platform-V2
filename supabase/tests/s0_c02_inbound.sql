\set ON_ERROR_STOP on
begin;
insert into auth.users(id) values
 ('a1000000-0000-4000-8000-000000000001'),
 ('a1000000-0000-4000-8000-000000000002');
insert into public.atores(id)
 select id from auth.users where id in
 ('a1000000-0000-4000-8000-000000000001','a1000000-0000-4000-8000-000000000002');
insert into public.concessionarias(id,nome_operacional) values
 ('a2000000-0000-4000-8000-000000000001','C02 loja A ficticia'),
 ('a2000000-0000-4000-8000-000000000002','C02 loja B ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('a1000000-0000-4000-8000-000000000001','a2000000-0000-4000-8000-000000000001','gestor'),
 ('a1000000-0000-4000-8000-000000000002','a2000000-0000-4000-8000-000000000002','gestor');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('a3000000-0000-4000-8000-000000000001','a2000000-0000-4000-8000-000000000001','C02_EMISSOR_A'),
 ('a3000000-0000-4000-8000-000000000002','a2000000-0000-4000-8000-000000000002','C02_EMISSOR_B');

do $test$
declare a jsonb; dup jsonb; b jsonb;
begin
 a:=prumo_private.receber_mensagem_sintetica(
 'a3000000-0000-4000-8000-000000000001','+5581000000001','same-event','Mensagem ficticia');
 dup:=prumo_private.receber_mensagem_sintetica(
 'a3000000-0000-4000-8000-000000000001','+5581000000001','same-event','Mensagem ficticia');
 b:=prumo_private.receber_mensagem_sintetica(
 'a3000000-0000-4000-8000-000000000002','+5581000000001','same-event','Mensagem ficticia');
 if a->>'outcome'<>'APPLIED' or dup->>'outcome'<>'ALREADY_APPLIED'
    or a->>'mensagem_id'<>dup->>'mensagem_id'
    or b->>'outcome'<>'APPLIED'
    or a->>'mensagem_id'=b->>'mensagem_id'
    or a->>'roteamento'<>'IA_PENDENTE'
 then raise exception 'FAIL C02 multiloja/idempotencia'; end if;
 if (select count(*) from public.leads_loja
      where telefone_cliente_normalizado='+5581000000001')<>2
    or (select count(*) from public.ciclos_comerciais
      where concessionaria_id in
      ('a2000000-0000-4000-8000-000000000001','a2000000-0000-4000-8000-000000000002'))<>2
    or (select count(*) from public.mensagens
      where id_externo='same-event' and canal_id in
      ('a3000000-0000-4000-8000-000000000001','a3000000-0000-4000-8000-000000000002'))<>2
    or (select count(*) from public.eventos_status_comercial
      where concessionaria_id in
      ('a2000000-0000-4000-8000-000000000001','a2000000-0000-4000-8000-000000000002'))<>2
 then raise exception 'FAIL C02 leads/ciclos/mensagens/status'; end if;
 begin
  perform prumo_private.receber_mensagem_sintetica(
   'a3000000-0000-4000-8000-000000000001','+5581000000001','same-event','texto alterado');
  raise exception 'FAIL mesmo ID aceitou payload distinto';
 exception when unique_violation then null; end;
 begin
  perform prumo_private.receber_mensagem_sintetica(
   'a3000000-0000-4000-8000-000000000001','+5581000000002','same-event','Mensagem ficticia');
  raise exception 'FAIL mesmo ID aceitou telefone distinto';
 exception when unique_violation then null; end;
end $test$;
\echo 'PASS C02-01: cliente A/B, canal exclusivo, mensagem deduplicada e evento correlato'

do $test$
begin
 begin
  perform prumo_private.receber_mensagem_sintetica(
   'a3000000-0000-4000-8000-000000000099','+5581000000001','unknown','ficticio');
  raise exception 'FAIL canal inexistente';
 exception when invalid_parameter_value then null; end;
 begin
  perform prumo_private.receber_mensagem_sintetica(
   'a3000000-0000-4000-8000-000000000001','000','invalid-phone','ficticio');
  raise exception 'FAIL telefone malformado';
 exception when invalid_parameter_value then null; end;
 begin
  insert into public.canais_loja(concessionaria_id,identificador_emissor)
  values('a2000000-0000-4000-8000-000000000002','C02_EMISSOR_A');
  raise exception 'FAIL emissor compartilhado';
 exception when unique_violation then null; end;
 begin
  insert into public.canais_loja(concessionaria_id,identificador_emissor)
  values('a2000000-0000-4000-8000-000000000002','   ');
  raise exception 'FAIL canal emissor vazio';
 exception when check_violation then null; end;
 begin
  insert into public.canais_loja(concessionaria_id,identificador_emissor)
  values('a2000000-0000-4000-8000-000000000002',' C02_EMISSOR_A ');
  raise exception 'FAIL canal emissor com espacos';
 exception when check_violation then null; end;
 if has_schema_privilege('authenticated','prumo_private','USAGE')
   or has_function_privilege('authenticated',
      'prumo_private.receber_mensagem_sintetica(uuid,text,text,text)','EXECUTE')
 then raise exception 'FAIL API pode executar funcao C02'; end if;
end $test$;
\echo 'PASS C02-02: emissor unico, canal e identificadores validados, API sem EXECUTE'

-- Mesmo lead, proxima mensagem, mesma conversa; nenhum novo evento comercial.
do $test$
declare x jsonb; y jsonb; begin
 x:=prumo_private.receber_mensagem_sintetica(
   'a3000000-0000-4000-8000-000000000001','+5581000000001','second','Continuacao sintética');
 select pg_catalog.jsonb_build_object('conversa_id',m.conversa_id) into y
 from public.mensagens m
 where m.concessionaria_id='a2000000-0000-4000-8000-000000000001'
   and m.id_externo='same-event';
 if x->>'conversa_id'<>y->>'conversa_id'
    or (select count(*) from public.eventos_status_comercial
      where concessionaria_id='a2000000-0000-4000-8000-000000000001')<>1
 then raise exception 'FAIL C02 continuacao'; end if;
end $test$;
\echo 'PASS C02-03: continuacao de conversa IA nao duplica ciclo nem evento'

-- C02 antes de IA: primeira resposta apos template efetivamente enviado.
select prumo_private.importar_lote_sintetico(
 'a1000000-0000-4000-8000-000000000001','a2000000-0000-4000-8000-000000000001',
 'lote-c02-fixture','[{"telefone":"+5581000000002"}]'::jsonb);
update public.ciclos_comerciais set
 status_comercial='primeiro disparo enviado',versao_registro=2
 where lead_id=(select id from public.leads_loja
 where telefone_cliente_normalizado='+5581000000002'
 and concessionaria_id='a2000000-0000-4000-8000-000000000001');
do $test$
declare x jsonb;begin
 x:=prumo_private.receber_mensagem_sintetica(
 'a3000000-0000-4000-8000-000000000001','+5581000000002','after-first','Respondeu ao primeiro ficticio');
 if x->>'roteamento'<>'IA_PENDENTE' or
    (select status_comercial from public.ciclos_comerciais
      where lead_id=(select id from public.leads_loja
      where concessionaria_id='a2000000-0000-4000-8000-000000000001'
      and telefone_cliente_normalizado='+5581000000002'))<>'em atendimento pela IA'
 then raise exception 'FAIL C02 apos primeiro disparo'; end if;
end $test$;
\echo 'PASS C02-04: resposta apos primeiro envio simulado promove IA com evento'

-- Retorno apos remessa: humano sem retroceder o ciclo nem inventar venda.
update public.ciclos_comerciais set status_comercial='cadastro enviado ao banco',
 versao_registro=3
 where concessionaria_id='a2000000-0000-4000-8000-000000000002';
do $test$
declare x jsonb; y jsonb; caso uuid; begin
 x:=prumo_private.receber_mensagem_sintetica(
 'a3000000-0000-4000-8000-000000000002','+5581000000001','after-bank-1','Dúvida ficticia após remessa');
 y:=prumo_private.receber_mensagem_sintetica(
 'a3000000-0000-4000-8000-000000000002','+5581000000001','after-bank-2','Continuação ficticia');
 caso:=(x->>'caso_id')::uuid;
 if caso is null or y->>'caso_id'<>caso::text
    or x->>'roteamento'<>'HUMANO_PENDENTE'
    or (select status_comercial from public.ciclos_comerciais
     where concessionaria_id='a2000000-0000-4000-8000-000000000002')<>'cadastro enviado ao banco'
    or (select count(*) from public.casos_humanos
     where concessionaria_id='a2000000-0000-4000-8000-000000000002'
      and motivo_simulado='retorno_pos_remessa')<>1
 then raise exception 'FAIL C02 pos-remessa'; end if;
end $test$;
\echo 'PASS C02-05: retorno pos-remessa abre caso humano sem mudar status comercial'

-- Retorno após venda, novo caso humano distinto do pós-remessa, IA desativada.
update public.ciclos_comerciais set status_comercial='vendido',versao_registro=4
 where concessionaria_id='a2000000-0000-4000-8000-000000000002';
do $test$
declare x jsonb; begin
 x:=prumo_private.receber_mensagem_sintetica(
 'a3000000-0000-4000-8000-000000000002','+5581000000001','after-sale','Retorno pós-venda ficticio');
 if x->>'roteamento'<>'HUMANO_PENDENTE'
    or x->>'caso_id' is null
    or (select count(*) from public.casos_humanos
        where concessionaria_id='a2000000-0000-4000-8000-000000000002')<>2
    or (select status_comercial from public.ciclos_comerciais
        where concessionaria_id='a2000000-0000-4000-8000-000000000002')<>'vendido'
    or (select count(*) from public.eventos_status_comercial
        where concessionaria_id='a2000000-0000-4000-8000-000000000002')<>1
 then raise exception 'FAIL C02 pos-venda'; end if;
end $test$;
\echo 'PASS C02-06: retorno pos-venda cria nova ocorrencia humana sem IA nem reversao'

-- Desambiguacao: proibir escolha arbitraria se varios ciclos de um lead.
insert into public.ciclos_comerciais(concessionaria_id,lead_id)
 select concessionaria_id,id from public.leads_loja
 where concessionaria_id='a2000000-0000-4000-8000-000000000001'
 and telefone_cliente_normalizado='+5581000000001';
do $test$
declare r jsonb; r2 jsonb; begin
 r:=prumo_private.receber_mensagem_sintetica(
    'a3000000-0000-4000-8000-000000000001',
    '+5581000000001','ambiguous','Novo pedido ficticio');
 r2:=prumo_private.receber_mensagem_sintetica(
    'a3000000-0000-4000-8000-000000000001',
    '+5581000000001','ambiguous','Novo pedido ficticio');
 if r->>'outcome'<>'APPLIED' or r->>'roteamento'<>'HUMANO_PENDENTE'
    or r->>'revisao'<>'MULTIPLOS_CICLOS'
    or r->>'ciclo_id' is not null or r->>'caso_id' is not null
    or r2->>'outcome'<>'ALREADY_APPLIED'
    or (select count(*) from public.mensagens
         where concessionaria_id='a2000000-0000-4000-8000-000000000001'
           and id_externo='ambiguous')<>1
    or (select count(*) from public.pendencias_inbound_simulado
         where concessionaria_id='a2000000-0000-4000-8000-000000000001')<>1
    or (select count(*) from public.eventos_status_comercial
         where concessionaria_id='a2000000-0000-4000-8000-000000000001')<>2
 then raise exception 'FAIL C02 inbox ambiguo perdeu mensagem ou inventou ciclo'; end if;
end $test$;
\echo 'PASS C02-07: multiplos ciclos preservam mensagem para revisao sem acionar IA'

-- RLS A/B: mesmos numeros de cliente nao compartilham linhas.
set local role authenticated;
select set_config('request.jwt.claim.sub','a1000000-0000-4000-8000-000000000001',true);
do $test$
begin
 if (select count(*) from public.leads_loja where telefone_cliente_normalizado='+5581000000001')<>1
 or (select count(*) from public.mensagens where id_externo='same-event')<>1
 or (select count(*) from public.pendencias_inbound_simulado)<>1
 then raise exception 'FAIL gestor A acessa B ou perdeu pendencia'; end if;
end $test$;
select set_config('request.jwt.claim.sub','a1000000-0000-4000-8000-000000000002',true);
do $test$
begin
 if (select count(*) from public.leads_loja where telefone_cliente_normalizado='+5581000000001')<>1
 or (select count(*) from public.mensagens where id_externo='same-event')<>1
 or (select count(*) from public.pendencias_inbound_simulado)<>0
 then raise exception 'FAIL gestor B acessa pendencia A'; end if;
end $test$;
reset role;
\echo 'PASS C02-08: gestor A/B isolados para o mesmo telefone cliente'
rollback;
