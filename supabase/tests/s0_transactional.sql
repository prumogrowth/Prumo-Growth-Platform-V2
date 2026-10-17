\set ON_ERROR_STOP on
begin;
insert into auth.users(id) values
('91000000-0000-4000-8000-000000000001'),('91000000-0000-4000-8000-000000000002');
insert into public.atores(id) select id from auth.users where id::text like '91000000%';
insert into public.concessionarias(id,nome_operacional) values
('92000000-0000-4000-8000-000000000001','Loja A sintética'),
('92000000-0000-4000-8000-000000000002','Loja B sintética');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
('91000000-0000-4000-8000-000000000001','92000000-0000-4000-8000-000000000001','gestor'),
('91000000-0000-4000-8000-000000000002','92000000-0000-4000-8000-000000000002','gestor');
do $test$
declare r jsonb; rr jsonb; old_lead uuid; begin
 r:=prumo_private.importar_lote_sintetico(
 '91000000-0000-4000-8000-000000000001','92000000-0000-4000-8000-000000000001',
 'L01','[{"telefone":"+5512345678901"},{"telefone":"INVALIDO"}]'::jsonb);
 if r->>'outcome'<>'APPLIED' or (r->>'aceitos')::int<>1 or (r->>'rejeitados')::int<>1
 then raise exception 'FAIL primeiro lote'; end if;
 rr:=prumo_private.importar_lote_sintetico(
 '91000000-0000-4000-8000-000000000001','92000000-0000-4000-8000-000000000001',
 'L01','[{"telefone":"+5512345678901"},{"telefone":"INVALIDO"}]'::jsonb);
 if rr->>'outcome'<>'ALREADY_APPLIED' or rr->>'lote_id'<>r->>'lote_id'
 then raise exception 'FAIL reentrega'; end if;
 begin
  perform prumo_private.importar_lote_sintetico(
  '91000000-0000-4000-8000-000000000001','92000000-0000-4000-8000-000000000001',
  'L01','[{"telefone":"+5512345678902"}]'::jsonb);
  raise exception 'FAIL alteracao payload mesma chave';
 exception when unique_violation then null; end;
 select id into old_lead from public.leads_loja
 where concessionaria_id='92000000-0000-4000-8000-000000000001';
 perform prumo_private.importar_lote_sintetico(
 '91000000-0000-4000-8000-000000000001','92000000-0000-4000-8000-000000000001',
 'L02','[{"telefone":"+5512345678901"}]'::jsonb);
 perform prumo_private.importar_lote_sintetico(
 '91000000-0000-4000-8000-000000000002','92000000-0000-4000-8000-000000000002',
 'L01','[{"telefone":"+5512345678901"}]'::jsonb);
 if (select count(*) from public.leads_loja where telefone_cliente_normalizado='+5512345678901')<>2
  or (select count(*) from public.reencontros_lote where lead_id=old_lead)<>1
  or (select count(*) from public.ciclos_comerciais where lead_id=old_lead)<>1
  or (select count(*) from public.itens_lote where resultado='rejeitado')<>1
 then raise exception 'FAIL duplicacao interlotes/historico'; end if;
 begin
  perform prumo_private.importar_lote_sintetico(
  '91000000-0000-4000-8000-000000000002','92000000-0000-4000-8000-000000000001',
  'INVASAO','[{"telefone":"+5512345678901"}]'::jsonb);
  raise exception 'FAIL ator B importou A';
 exception when insufficient_privilege then null; end;
end $test$;
\echo 'PASS TX-C01: reimportacao, itens rejeitados, idempotencia, duas lojas'
do $test$ begin
 if has_schema_privilege('authenticated','prumo_private','USAGE')
 or has_schema_privilege('anon','prumo_private','USAGE')
 or has_function_privilege('authenticated','prumo_private.importar_lote_sintetico(uuid,uuid,text,jsonb)','EXECUTE')
 then raise exception 'FAIL funcao exposta para API'; end if;
end $test$;
\echo 'PASS TX-AUTH: operacoes privadas sem grant a cliente'
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
('94000000-0000-4000-8000-000000000001','92000000-0000-4000-8000-000000000001','TEST-LOJA-TX-A'),
('94000000-0000-4000-8000-000000000002','92000000-0000-4000-8000-000000000002','TEST-LOJA-TX-B');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id)
 select '95000000-0000-4000-8000-000000000001',
   '92000000-0000-4000-8000-000000000001',id,'94000000-0000-4000-8000-000000000001'
 from public.leads_loja where concessionaria_id='92000000-0000-4000-8000-000000000001';
insert into public.conversas(id,concessionaria_id,lead_id,canal_id)
 select '95000000-0000-4000-8000-000000000002',
   '92000000-0000-4000-8000-000000000002',id,'94000000-0000-4000-8000-000000000002'
 from public.leads_loja where concessionaria_id='92000000-0000-4000-8000-000000000002';
insert into public.mensagens(id,concessionaria_id,conversa_id,canal_id,direcao,conteudo_sintetico,id_externo) values
('96000000-0000-4000-8000-000000000001','92000000-0000-4000-8000-000000000001',
 '95000000-0000-4000-8000-000000000001','94000000-0000-4000-8000-000000000001',
 'entrada','Texto de teste A','FICTICIO-1'),
('96000000-0000-4000-8000-000000000002','92000000-0000-4000-8000-000000000002',
 '95000000-0000-4000-8000-000000000002','94000000-0000-4000-8000-000000000002',
 'entrada','Texto de teste B','FICTICIO-1');
do $test$
declare v_ciclo uuid; r jsonb; rr jsonb; begin
 select id into v_ciclo from public.ciclos_comerciais
 where concessionaria_id='92000000-0000-4000-8000-000000000001';
 begin
  perform prumo_private.transicao_inbound_sintetico(
 '92000000-0000-4000-8000-000000000001',v_ciclo,
 '96000000-0000-4000-8000-000000000002',1);
  raise exception 'FAIL aceitou evento cruzado';
 exception when invalid_parameter_value then null; end;
 begin
  perform prumo_private.transicao_inbound_sintetico(
 '92000000-0000-4000-8000-000000000001',v_ciclo,
 '96000000-0000-4000-8000-000000000001',999);
  raise exception 'FAIL versao obsoleta';
 exception when serialization_failure then null; end;
 r:=prumo_private.transicao_inbound_sintetico(
 '92000000-0000-4000-8000-000000000001',v_ciclo,
 '96000000-0000-4000-8000-000000000001',1);
 rr:=prumo_private.transicao_inbound_sintetico(
 '92000000-0000-4000-8000-000000000001',v_ciclo,
 '96000000-0000-4000-8000-000000000001',1);
 if r->>'outcome'<>'APPLIED' or rr->>'outcome'<>'ALREADY_APPLIED'
   or rr->>'evento_id'<>r->>'evento_id'
   or (select count(*) from public.eventos_status_comercial where ciclo_id=v_ciclo)<>1
   or (select versao_registro from public.ciclos_comerciais where id=v_ciclo)<>2
   or (select status_comercial from public.ciclos_comerciais where id=v_ciclo)<>'em atendimento pela IA'
 then raise exception 'FAIL transicao evento atomico'; end if;
end $test$;
\echo 'PASS TX-STATUS: versao, evento correlacionado, reentrega, prova escopada'
-- Handoff humano definitivo: mesmo uma conversa antiga sem caso não reativa IA.
select prumo_private.importar_lote_sintetico(
 '91000000-0000-4000-8000-000000000001','92000000-0000-4000-8000-000000000001',
 'L03','[{"telefone":"+5512345678903"}]'::jsonb);
do $test$
declare v_lead uuid; v_ciclo uuid; v_conv uuid; v_msg uuid;
begin
 select id into v_lead from public.leads_loja
 where concessionaria_id='92000000-0000-4000-8000-000000000001'
 and telefone_cliente_normalizado='+5512345678903';
 select id into v_ciclo from public.ciclos_comerciais where lead_id=v_lead;
 insert into public.conversas(concessionaria_id,lead_id,canal_id)
 values('92000000-0000-4000-8000-000000000001',v_lead,
 '94000000-0000-4000-8000-000000000001') returning id into v_conv;
 insert into public.mensagens(concessionaria_id,conversa_id,canal_id,direcao,conteudo_sintetico,id_externo)
 values('92000000-0000-4000-8000-000000000001',v_conv,
 '94000000-0000-4000-8000-000000000001','entrada','Mensagem antiga fictícia','HUMAN-TEST-1')
 returning id into v_msg;
 insert into public.casos_humanos(concessionaria_id,lead_id,ciclo_id)
 values('92000000-0000-4000-8000-000000000001',v_lead,v_ciclo);
 begin
  perform prumo_private.transicao_inbound_sintetico(
   '92000000-0000-4000-8000-000000000001',v_ciclo,v_msg,1);
  raise exception 'FAIL handoff humano retornou a IA';
 exception when invalid_parameter_value then null; end;
 if (select status_comercial from public.ciclos_comerciais where id=v_ciclo)<>'aguardando primeiro disparo'
 or exists(select 1 from public.eventos_status_comercial where ciclo_id=v_ciclo)
 then raise exception 'FAIL tentativa humana mudou status/evento'; end if;
end $test$;
\echo 'PASS TX-HANDOFF: humano definitivo, sem retorno IA e sem evento comercial'
rollback;
