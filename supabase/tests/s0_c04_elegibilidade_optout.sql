\set ON_ERROR_STOP on
begin;
insert into auth.users(id) values
 ('aa000000-0000-4000-8000-000000000031'),
 ('aa000000-0000-4000-8000-000000000032');
insert into public.atores(id) values
 ('aa000000-0000-4000-8000-000000000031'),
 ('aa000000-0000-4000-8000-000000000032');
insert into public.concessionarias(id,nome_operacional) values
 ('ab000000-0000-4000-8000-000000000031','C04 A ficticia'),
 ('ab000000-0000-4000-8000-000000000032','C04 B ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('aa000000-0000-4000-8000-000000000031','ab000000-0000-4000-8000-000000000031','gestor'),
 ('aa000000-0000-4000-8000-000000000032','ab000000-0000-4000-8000-000000000032','gestor');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('ac000000-0000-4000-8000-000000000031','ab000000-0000-4000-8000-000000000031','C04_CANAL_A'),
 ('ac000000-0000-4000-8000-000000000032','ab000000-0000-4000-8000-000000000032','C04_CANAL_B');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('ad000000-0000-4000-8000-000000000031','ab000000-0000-4000-8000-000000000031','+5581888880101'),
 ('ad000000-0000-4000-8000-000000000032','ab000000-0000-4000-8000-000000000032','+5581888880101'),
 ('ad000000-0000-4000-8000-000000000033','ab000000-0000-4000-8000-000000000031','+5581888880102');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
 ('ae000000-0000-4000-8000-000000000031','ab000000-0000-4000-8000-000000000031','ad000000-0000-4000-8000-000000000031'),
 ('ae000000-0000-4000-8000-000000000032','ab000000-0000-4000-8000-000000000032','ad000000-0000-4000-8000-000000000032');
insert into public.catalogo_templates_sinteticos(id,concessionaria_id,codigo,versao,aprovado_simulacao) values
 ('af000000-0000-4000-8000-000000000031','ab000000-0000-4000-8000-000000000031','T',1,true),
 ('af000000-0000-4000-8000-000000000032','ab000000-0000-4000-8000-000000000032','T',1,true);
do $test$
declare r jsonb;begin
 r:=prumo_private.verificar_contato_sintetico(
 'ab000000-0000-4000-8000-000000000031','ad000000-0000-4000-8000-000000000031',
 'ac000000-0000-4000-8000-000000000031','recontato_comercial_sintetico');
 if r->>'decisao'<>'INDETERMINADO' or r->>'real'<>'DEPENDENCY_UNVERIFIED'
 then raise exception 'FAIL C04 importacao sem prova ganhou elegibilidade'; end if;
 begin
 perform prumo_private.agendar_recontatos_sinteticos(
 'aa000000-0000-4000-8000-000000000031','ab000000-0000-4000-8000-000000000031',
 'ae000000-0000-4000-8000-000000000031','ac000000-0000-4000-8000-000000000031',
 'NO-EVIDENCE',jsonb_build_array(jsonb_build_object(
 'template_id','af000000-0000-4000-8000-000000000031',
 'agendado_em',(statement_timestamp()+interval '1 day')::text)));
 raise exception 'FAIL C04 agendamento sem evidencia';
 exception when invalid_parameter_value then null; end;
end $test$;
\echo 'PASS C04-01: sem prova explicita, indeciso e agendamento proibido'

insert into public.evidencias_elegibilidade_sinteticas(
 concessionaria_id,lead_id,canal_id,finalidade,referencia_ficticia)
values ('ab000000-0000-4000-8000-000000000031','ad000000-0000-4000-8000-000000000031',
 'ac000000-0000-4000-8000-000000000031','recontato_comercial_sintetico','FAKE_EVIDENCE_A_01');
do $test$
declare r jsonb;begin
 r:=prumo_private.verificar_contato_sintetico(
 'ab000000-0000-4000-8000-000000000031','ad000000-0000-4000-8000-000000000031',
 'ac000000-0000-4000-8000-000000000031','recontato_comercial_sintetico');
 if r->>'decisao'<>'ELEGIVEL_SOMENTE_SIMULACAO'
 or r->>'real'<>'DEPENDENCY_UNVERIFIED'
 then raise exception 'FAIL C04 evidência fake confundida com real'; end if;
 r:=prumo_private.verificar_contato_sintetico(
 'ab000000-0000-4000-8000-000000000032','ad000000-0000-4000-8000-000000000032',
 'ac000000-0000-4000-8000-000000000032','recontato_comercial_sintetico');
 if r->>'decisao'<>'INDETERMINADO' then
 raise exception 'FAIL C04 prova A virou autorizacao B'; end if;
end $test$;
\echo 'PASS C04-02: apenas prova ficticia do canal A, sem autorização presumida B'

select prumo_private.agendar_recontatos_sinteticos(
 'aa000000-0000-4000-8000-000000000031','ab000000-0000-4000-8000-000000000031',
 'ae000000-0000-4000-8000-000000000031','ac000000-0000-4000-8000-000000000031',
 'PLAN-C04-A',jsonb_build_array(jsonb_build_object(
 'template_id','af000000-0000-4000-8000-000000000031',
 'agendado_em',(statement_timestamp()+interval '2 days')::text)));

do $test$
declare r jsonb; duplicate jsonb; e uuid;begin
 r:=prumo_private.registrar_optout_sintetico(
 'ab000000-0000-4000-8000-000000000031','ad000000-0000-4000-8000-000000000031',
 'ac000000-0000-4000-8000-000000000031','recontato_comercial_sintetico','OPTOUT-A-01');
 duplicate:=prumo_private.registrar_optout_sintetico(
 'ab000000-0000-4000-8000-000000000031','ad000000-0000-4000-8000-000000000031',
 'ac000000-0000-4000-8000-000000000031','recontato_comercial_sintetico','OPTOUT-A-01');
 if r->>'outcome'<>'APPLIED' or duplicate->>'outcome'<>'ALREADY_APPLIED'
 or (r->>'envios_cancelados')::integer<>1
 or (select count(*) from public.supressoes_contato_sinteticas)<>1
 or (select count(*) from public.eventos_envio_template_sinteticos
      where motivo='opt_out_simulado')<>1
 then raise exception 'FAIL C04 optout nao idempotente/cancelamento'; end if;
 r:=prumo_private.verificar_contato_sintetico(
 'ab000000-0000-4000-8000-000000000031','ad000000-0000-4000-8000-000000000031',
 'ac000000-0000-4000-8000-000000000031','recontato_comercial_sintetico');
 if r->>'decisao'<>'INELEGIVEL' or r->>'motivo'<>'OPT_OUT'
 then raise exception 'FAIL C04 optout sem precedencia'; end if;
 select id into e from public.envios_template_sinteticos
 where concessionaria_id='ab000000-0000-4000-8000-000000000031';
 r:=prumo_private.reservar_envio_sintetico(
 'ab000000-0000-4000-8000-000000000031',e,
 statement_timestamp()+interval '4 days');
 if r->>'outcome'<>'NOT_ELIGIBLE' then
 raise exception 'FAIL C04 reserva apos optout'; end if;
 begin
  perform prumo_private.registrar_optout_sintetico(
 'ab000000-0000-4000-8000-000000000031','ad000000-0000-4000-8000-000000000033',
 'ac000000-0000-4000-8000-000000000031','recontato_comercial_sintetico','OPTOUT-A-01');
  raise exception 'FAIL C04 id evento de outra pessoa';
 exception when unique_violation then null; end;
end $test$;
\echo 'PASS C04-03: optout preservado, cancela C08, reserva negada e replay seguro'

-- Inbound does not reinstate opt-in, even if same sender replies spontaneously.
select prumo_private.receber_mensagem_sintetica(
 'ac000000-0000-4000-8000-000000000031',
 '+5581888880101','C04-IN-1','Cliente iniciou conversa ficticia');
do $test$
declare r jsonb;begin
 r:=prumo_private.verificar_contato_sintetico(
 'ab000000-0000-4000-8000-000000000031','ad000000-0000-4000-8000-000000000031',
 'ac000000-0000-4000-8000-000000000031','recontato_comercial_sintetico');
 if r->>'decisao'<>'INELEGIVEL'
 or (select count(*) from public.supressoes_contato_sinteticas)<>1
 then raise exception 'FAIL C04 inbound virou opt-in'; end if;
end $test$;
\echo 'PASS C04-04: inbound espontaneo nao revoga optout nem cria consentimento'

insert into public.evidencias_elegibilidade_sinteticas(
 concessionaria_id,lead_id,canal_id,finalidade,referencia_ficticia)
values ('ab000000-0000-4000-8000-000000000032','ad000000-0000-4000-8000-000000000032',
 'ac000000-0000-4000-8000-000000000032','recontato_comercial_sintetico','FAKE_EVIDENCE_B_01');
do $test$
declare r jsonb;begin
 r:=prumo_private.verificar_contato_sintetico(
 'ab000000-0000-4000-8000-000000000032','ad000000-0000-4000-8000-000000000032',
 'ac000000-0000-4000-8000-000000000032','recontato_comercial_sintetico');
 if r->>'decisao'<>'ELEGIVEL_SOMENTE_SIMULACAO'
 then raise exception 'FAIL C04 B sem independencia'; end if;
 if (select count(*) from public.leads_loja
     where telefone_cliente_normalizado='+5581888880101')<>2
 then raise exception 'FAIL C04 cliente nao pode existir A/B'; end if;
end $test$;
\echo 'PASS C04-05: mesmo telefone A/B sem compartilhar optout ou autorizacao'

set local role authenticated;
select set_config('request.jwt.claim.sub','aa000000-0000-4000-8000-000000000031',true);
do $test$ begin
 if (select count(*) from public.supressoes_contato_sinteticas)<>1
 or (select count(*) from public.evidencias_elegibilidade_sinteticas)<>1
 then raise exception 'FAIL C04 RLS gestor A'; end if;
 begin
 insert into public.supressoes_contato_sinteticas(
 concessionaria_id,lead_id,canal_id,finalidade,evento_origem)
 values('ab000000-0000-4000-8000-000000000031','ad000000-0000-4000-8000-000000000031',
 'ac000000-0000-4000-8000-000000000031','recontato_comercial_sintetico','INJECTION');
 raise exception 'FAIL cliente autenticado escreve supressao';
 exception when insufficient_privilege then null; end;
end $test$;
select set_config('request.jwt.claim.sub','aa000000-0000-4000-8000-000000000032',true);
do $test$ begin
 if (select count(*) from public.supressoes_contato_sinteticas)<>0
 or (select count(*) from public.evidencias_elegibilidade_sinteticas)<>1
 then raise exception 'FAIL C04 RLS gestor B'; end if;
end $test$;
reset role;
\echo 'PASS C04-06: RLS por loja e escrita por cliente negada'
rollback;
