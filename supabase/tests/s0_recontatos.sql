\set ON_ERROR_STOP on
begin;
insert into auth.users(id) values
 ('d1000000-0000-4000-8000-000000000001'),
 ('d1000000-0000-4000-8000-000000000002');
insert into public.atores(id) select id from auth.users
 where id in ('d1000000-0000-4000-8000-000000000001',
              'd1000000-0000-4000-8000-000000000002');
insert into public.concessionarias(id,nome_operacional) values
 ('d2000000-0000-4000-8000-000000000001','Recontato A sintético'),
 ('d2000000-0000-4000-8000-000000000002','Recontato B sintético');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('d1000000-0000-4000-8000-000000000001','d2000000-0000-4000-8000-000000000001','gestor'),
 ('d1000000-0000-4000-8000-000000000002','d2000000-0000-4000-8000-000000000002','gestor');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('d3000000-0000-4000-8000-000000000001','d2000000-0000-4000-8000-000000000001','EMISSOR_RECONTATO_A'),
 ('d3000000-0000-4000-8000-000000000002','d2000000-0000-4000-8000-000000000002','EMISSOR_RECONTATO_B');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('d4000000-0000-4000-8000-000000000001','d2000000-0000-4000-8000-000000000001','+5581998800100'),
 ('d4000000-0000-4000-8000-000000000002','d2000000-0000-4000-8000-000000000002','+5581998800100');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
 ('d5000000-0000-4000-8000-000000000001','d2000000-0000-4000-8000-000000000001','d4000000-0000-4000-8000-000000000001'),
 ('d5000000-0000-4000-8000-000000000002','d2000000-0000-4000-8000-000000000002','d4000000-0000-4000-8000-000000000002');
insert into public.catalogo_templates_sinteticos(id,concessionaria_id,codigo,versao,aprovado_simulacao) values
 ('d6000000-0000-4000-8000-000000000001','d2000000-0000-4000-8000-000000000001','T1',1,true),
 ('d6000000-0000-4000-8000-000000000002','d2000000-0000-4000-8000-000000000002','T1',1,true),
 ('d6000000-0000-4000-8000-000000000003','d2000000-0000-4000-8000-000000000001','UNAPPROVED',1,false);

do $test$
declare r jsonb; again jsonb; ra jsonb; rb jsonb; input jsonb; pa uuid; pb uuid;
begin
 input:=jsonb_build_array(
   jsonb_build_object('template_id','d6000000-0000-4000-8000-000000000001',
     'agendado_em',(statement_timestamp()+interval '1 day')::text),
   jsonb_build_object('template_id','d6000000-0000-4000-8000-000000000001',
     'agendado_em',(statement_timestamp()+interval '2 days')::text));
 r:=prumo_private.agendar_recontatos_sinteticos(
 'd1000000-0000-4000-8000-000000000001','d2000000-0000-4000-8000-000000000001',
 'd5000000-0000-4000-8000-000000000001','d3000000-0000-4000-8000-000000000001',
 'batch-plan-A',input);
 again:=prumo_private.agendar_recontatos_sinteticos(
 'd1000000-0000-4000-8000-000000000001','d2000000-0000-4000-8000-000000000001',
 'd5000000-0000-4000-8000-000000000001','d3000000-0000-4000-8000-000000000001',
 'batch-plan-A',input);
 pa:=(r->>'plano_id')::uuid;
 if r->>'outcome'<>'APPLIED' or (r->>'envios')::int<>2
 or again->>'outcome'<>'ALREADY_APPLIED' or again->>'plano_id'<>r->>'plano_id'
 then raise exception 'FAIL C05 idempotencia de plano'; end if;
 begin
  perform prumo_private.agendar_recontatos_sinteticos(
   'd1000000-0000-4000-8000-000000000001','d2000000-0000-4000-8000-000000000001',
   'd5000000-0000-4000-8000-000000000001','d3000000-0000-4000-8000-000000000001',
   'batch-plan-A','[{"template_id":"d6000000-0000-4000-8000-000000000001",
   "agendado_em":"2031-01-01T00:00:00Z"}]'::jsonb);
  raise exception 'FAIL C05 chave reutilizada com payload distinto';
 exception when unique_violation then null; end;
 begin
  perform prumo_private.agendar_recontatos_sinteticos(
   'd1000000-0000-4000-8000-000000000001','d2000000-0000-4000-8000-000000000001',
   'd5000000-0000-4000-8000-000000000001','d3000000-0000-4000-8000-000000000001',
   'plano-nao-aprovado',jsonb_build_array(jsonb_build_object(
   'template_id','d6000000-0000-4000-8000-000000000003',
   'agendado_em',(statement_timestamp()+interval '1 day')::text)));
  raise exception 'FAIL C05 aceitou template sem aprovacao';
 exception when invalid_parameter_value then null; end;
 begin
  perform prumo_private.agendar_recontatos_sinteticos(
   'd1000000-0000-4000-8000-000000000002','d2000000-0000-4000-8000-000000000001',
   'd5000000-0000-4000-8000-000000000001','d3000000-0000-4000-8000-000000000001',
   'plano-invasao',input);
  raise exception 'FAIL C05 gestor B criou em A';
 exception when insufficient_privilege then null; end;
 rb:=prumo_private.agendar_recontatos_sinteticos(
 'd1000000-0000-4000-8000-000000000002','d2000000-0000-4000-8000-000000000002',
 'd5000000-0000-4000-8000-000000000002','d3000000-0000-4000-8000-000000000002',
 'batch-plan-B',jsonb_build_array(jsonb_build_object(
    'template_id','d6000000-0000-4000-8000-000000000002',
    'agendado_em',(statement_timestamp()+interval '3 days')::text)));
 if rb->>'outcome'<>'APPLIED' or
 (select count(*) from public.planos_recontato_sinteticos)<>2
 or (select count(*) from public.envios_template_sinteticos)<>3
 then raise exception 'FAIL C05 plano B independe de A'; end if;
end $test$;
\echo 'PASS REC-01: plano idempotente, so templates aprovados, segregacao A/B e 3 envios programados'

-- Simula reserva FUTURA, sem despachar externamente nem marcar enviado.
do $test$
declare envio uuid; r jsonb;begin
 select id into envio from public.envios_template_sinteticos
 where concessionaria_id='d2000000-0000-4000-8000-000000000001'
 and ordem=1;
 r:=prumo_private.reservar_envio_sintetico(
 'd2000000-0000-4000-8000-000000000001',envio,
 statement_timestamp()+interval '4 days');
 if r->>'outcome'<>'RESERVED_SIMULATED' then raise exception 'FAIL reserva C06'; end if;
end $test$;
\echo 'PASS REC-02: apenas reserva sintética, estado técnico separado, sem entrega'

do $test$
declare r jsonb; dup jsonb;begin
 r:=prumo_private.receber_mensagem_sintetica(
  'd3000000-0000-4000-8000-000000000001','+5581998800100',
  'REC_REPLY_1','Resposta ficticia A');
 dup:=prumo_private.receber_mensagem_sintetica(
  'd3000000-0000-4000-8000-000000000001','+5581998800100',
  'REC_REPLY_1','Resposta ficticia A');
 if r->>'outcome'<>'APPLIED'
 or (r->'recontatos'->>'envios_cancelados')::int<>2
 or (r->'recontatos'->>'planos_cancelados')::int<>1
 or dup->>'outcome'<>'ALREADY_APPLIED'
 or (select count(*) from public.envios_template_sinteticos
     where concessionaria_id='d2000000-0000-4000-8000-000000000001'
       and estado='cancelado')<>2
 or (select count(*) from public.envios_template_sinteticos
     where concessionaria_id='d2000000-0000-4000-8000-000000000002'
       and estado='programado')<>1
 or (select count(*) from public.eventos_envio_template_sinteticos
     where concessionaria_id='d2000000-0000-4000-8000-000000000001'
     and estado_posterior='cancelado')<>2
 then raise exception 'FAIL REC-03 cancelamento atomico C02'; end if;
end $test$;
\echo 'PASS REC-03: inbound cancela reservado/programado na mesma transacao sem afetar B'

do $test$
declare envio uuid; r jsonb;begin
 select id into envio from public.envios_template_sinteticos
 where concessionaria_id='d2000000-0000-4000-8000-000000000001'
 and ordem=2;
 r:=prumo_private.reservar_envio_sintetico(
 'd2000000-0000-4000-8000-000000000001',envio,
 statement_timestamp()+interval '8 days');
 if r->>'outcome'<>'NOT_ELIGIBLE' then
 raise exception 'FAIL REC-04 reserva cancelada elegivel';end if;
 if (select count(*) from public.eventos_envio_template_sinteticos
 where concessionaria_id='d2000000-0000-4000-8000-000000000001')<>3 then
 raise exception 'FAIL REC-04 historico eventos apagado'; end if;
end $test$;
\echo 'PASS REC-04: envio obsoleto nao reserva de novo; trilha tecnica preservada'

-- Explicit manager cancellation, no commercial status change.
do $test$
declare x jsonb; y jsonb;begin
 x:=prumo_private.cancelar_recontatos_sinteticos(
 'd2000000-0000-4000-8000-000000000002','d4000000-0000-4000-8000-000000000002',
 'cancelamento_gestor');
 y:=prumo_private.cancelar_recontatos_sinteticos(
 'd2000000-0000-4000-8000-000000000002','d4000000-0000-4000-8000-000000000002',
 'cancelamento_gestor');
 if (x->>'envios_cancelados')::int<>1 or (y->>'envios_cancelados')::int<>0
 or (select status_comercial from public.ciclos_comerciais
     where id='d5000000-0000-4000-8000-000000000002')<>'aguardando primeiro disparo'
 then raise exception 'FAIL REC-05 cancelamento idempotente'; end if;
end $test$;
\echo 'PASS REC-05: cancelamento explicito idempotente nao altera 8 estados comerciais'

-- A manager may inspect only technical schedule for their shop; anon and OP cannot.
set local role authenticated;
select set_config('request.jwt.claim.sub','d1000000-0000-4000-8000-000000000001',true);
do $test$ begin
 if (select count(*) from public.planos_recontato_sinteticos)<>1
 or (select count(*) from public.envios_template_sinteticos)<>2
 or (select count(*) from public.eventos_envio_template_sinteticos)<>3
 then raise exception 'FAIL REC-06 gestor A leitura escopo'; end if;
 begin
  update public.envios_template_sinteticos set estado='programado';
  raise exception 'FAIL REC-06 gestor gravou evento';
 exception when insufficient_privilege then null; end;
end $test$;
select set_config('request.jwt.claim.sub','d1000000-0000-4000-8000-000000000002',true);
do $test$ begin
 if (select count(*) from public.planos_recontato_sinteticos)<>1
 or (select count(*) from public.envios_template_sinteticos)<>1
 or (select count(*) from public.eventos_envio_template_sinteticos)<>1
 then raise exception 'FAIL REC-06 gestor B leitura escopo'; end if;
end $test$;
reset role;
\echo 'PASS REC-06: RLS A/B eventos/envios, sem escrita por usuarios autenticados'
rollback;
