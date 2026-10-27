\set ON_ERROR_STOP on
begin;
insert into auth.users(id) values('b1000000-0000-4000-8000-000000000010');
insert into public.atores(id) values('b1000000-0000-4000-8000-000000000010');
insert into public.concessionarias(id,nome_operacional)
 values('b2000000-0000-4000-8000-000000000010','Auditoria C05 fictícia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('b1000000-0000-4000-8000-000000000010','b2000000-0000-4000-8000-000000000010','gestor');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
('b3000000-0000-4000-8000-000000000010','b2000000-0000-4000-8000-000000000010','+5581990000010'),
('b3000000-0000-4000-8000-000000000011','b2000000-0000-4000-8000-000000000010','+5581990000011');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
('b4000000-0000-4000-8000-000000000010','b2000000-0000-4000-8000-000000000010','b3000000-0000-4000-8000-000000000010'),
('b4000000-0000-4000-8000-000000000011','b2000000-0000-4000-8000-000000000010','b3000000-0000-4000-8000-000000000011');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
('b5000000-0000-4000-8000-000000000010','b2000000-0000-4000-8000-000000000010','C05_AUDIT_SENDER_1'),
('b5000000-0000-4000-8000-000000000011','b2000000-0000-4000-8000-000000000010','C05_AUDIT_SENDER_2');
insert into public.catalogo_templates_sinteticos(id,concessionaria_id,codigo,versao,aprovado_simulacao)
 values('b6000000-0000-4000-8000-000000000010','b2000000-0000-4000-8000-000000000010','T1',1,true);

insert into public.evidencias_elegibilidade_sinteticas(concessionaria_id,lead_id,canal_id,finalidade,referencia_ficticia) values
('b2000000-0000-4000-8000-000000000010','b3000000-0000-4000-8000-000000000010','b5000000-0000-4000-8000-000000000010','recontato_comercial_sintetico','PROVA_FICTICIA_CI_1');
do $test$
declare v jsonb; t jsonb; p uuid; e uuid;
begin
 t:=jsonb_build_array(jsonb_build_object(
 'template_id','b6000000-0000-4000-8000-000000000010',
 'agendado_em',(statement_timestamp()+interval '3 days')::text));
 v:=prumo_private.agendar_recontatos_sinteticos(
 'b1000000-0000-4000-8000-000000000010','b2000000-0000-4000-8000-000000000010',
 'b4000000-0000-4000-8000-000000000010','b5000000-0000-4000-8000-000000000010','KEY-AUDIT',t);
 p:=(v->>'plano_id')::uuid;
 if v->>'outcome'<>'APPLIED' then raise exception 'FAIL plano inicial'; end if;
 begin
  perform prumo_private.agendar_recontatos_sinteticos(
 'b1000000-0000-4000-8000-000000000010','b2000000-0000-4000-8000-000000000010',
 'b4000000-0000-4000-8000-000000000011','b5000000-0000-4000-8000-000000000010','KEY-AUDIT',t);
  raise exception 'FAIL mesma chave outro ciclo retornou plano alheio';
 exception when unique_violation then null; end;
 begin
  perform prumo_private.agendar_recontatos_sinteticos(
 'b1000000-0000-4000-8000-000000000010','b2000000-0000-4000-8000-000000000010',
 'b4000000-0000-4000-8000-000000000010','b5000000-0000-4000-8000-000000000011','KEY-AUDIT',t);
  raise exception 'FAIL mesma chave outro canal foi aceito';
 exception when unique_violation then null; end;
 if (select count(*) from public.planos_recontato_sinteticos)<>1
 then raise exception 'FAIL duplicacao de plano por idempotencia'; end if;
 -- Array na ordem errada nao constitui sequencia de envios.
 begin
  perform prumo_private.agendar_recontatos_sinteticos(
 'b1000000-0000-4000-8000-000000000010','b2000000-0000-4000-8000-000000000010',
 'b4000000-0000-4000-8000-000000000011','b5000000-0000-4000-8000-000000000010',
 'KEY-REVERSE',jsonb_build_array(
 jsonb_build_object('template_id','b6000000-0000-4000-8000-000000000010',
 'agendado_em',(statement_timestamp()+interval '5 days')::text),
 jsonb_build_object('template_id','b6000000-0000-4000-8000-000000000010',
 'agendado_em',(statement_timestamp()+interval '4 days')::text)));
  raise exception 'FAIL agendamento fora de ordem';
 exception when invalid_parameter_value then null; end;
 if exists(select 1 from public.planos_recontato_sinteticos where chave_idempotencia='KEY-REVERSE')
 then raise exception 'FAIL transacao parcial em ordem temporal invalida'; end if;
 select id into e from public.envios_template_sinteticos where plano_id=p;
 -- Template que estava aprovado no agendamento pode ser revogado antes da reserva.
 update public.catalogo_templates_sinteticos set aprovado_simulacao=false
 where id='b6000000-0000-4000-8000-000000000010';
 v:=prumo_private.reservar_envio_sintetico(
 'b2000000-0000-4000-8000-000000000010',e,statement_timestamp()+interval '10 days');
 if v->>'outcome'<>'NOT_ELIGIBLE'
  or (select estado from public.envios_template_sinteticos where id=e)<>'programado'
  or (select count(*) from public.eventos_envio_template_sinteticos)<>0
 then raise exception 'FAIL reserva com template desautorizado'; end if;
end $test$;
\echo 'PASS AUD-REC-01: idempotencia inclui ciclo/canal, ordem cronologica, revalida template'
rollback;
