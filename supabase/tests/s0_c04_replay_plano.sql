\set ON_ERROR_STOP on
begin;
insert into auth.users(id) values('f1000000-0000-4000-8000-000000000081');
insert into public.atores(id) values('f1000000-0000-4000-8000-000000000081');
insert into public.concessionarias(id,nome_operacional) values
('f2000000-0000-4000-8000-000000000081','Replay C04 sintético');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
('f1000000-0000-4000-8000-000000000081','f2000000-0000-4000-8000-000000000081','gestor');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
values('f3000000-0000-4000-8000-000000000081','f2000000-0000-4000-8000-000000000081','C04_REPLAY_CANAL');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
values('f4000000-0000-4000-8000-000000000081','f2000000-0000-4000-8000-000000000081','+5581880000081');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id)
values('f5000000-0000-4000-8000-000000000081','f2000000-0000-4000-8000-000000000081','f4000000-0000-4000-8000-000000000081');
insert into public.catalogo_templates_sinteticos(id,concessionaria_id,codigo,versao,aprovado_simulacao)
values('f6000000-0000-4000-8000-000000000081','f2000000-0000-4000-8000-000000000081','T',1,true);
insert into public.evidencias_elegibilidade_sinteticas(
 concessionaria_id,lead_id,canal_id,finalidade,referencia_ficticia)
values('f2000000-0000-4000-8000-000000000081','f4000000-0000-4000-8000-000000000081',
 'f3000000-0000-4000-8000-000000000081','recontato_comercial_sintetico','FICTICIO_REPLAY_81');

do $replay$
declare v_arr jsonb; v_new jsonb; v_again jsonb; v_cancel jsonb; v_old uuid;
begin
 v_arr:=jsonb_build_array(jsonb_build_object(
  'template_id','f6000000-0000-4000-8000-000000000081',
  'agendado_em','2030-01-01T13:00:00+00:00'));
 v_new:=prumo_private.agendar_recontatos_sinteticos(
 'f1000000-0000-4000-8000-000000000081','f2000000-0000-4000-8000-000000000081',
 'f5000000-0000-4000-8000-000000000081','f3000000-0000-4000-8000-000000000081','REPLAY-C04-81',v_arr);
 if v_new->>'outcome'<>'APPLIED' or v_new->>'estado_plano'<>'ativo'
  or (v_new->>'executavel_simulacao')::boolean is distinct from true
 then raise exception 'FAIL C04 replay plano novo';end if;
 v_old:=(v_new->>'plano_id')::uuid;
 v_cancel:=prumo_private.registrar_optout_sintetico(
 'f2000000-0000-4000-8000-000000000081','f4000000-0000-4000-8000-000000000081',
 'f3000000-0000-4000-8000-000000000081','recontato_comercial_sintetico','OPT-REPLAY-81');
 if v_cancel->>'outcome'<>'APPLIED' then raise exception 'FAIL C04 optout replay';end if;
 v_again:=prumo_private.agendar_recontatos_sinteticos(
 'f1000000-0000-4000-8000-000000000081','f2000000-0000-4000-8000-000000000081',
 'f5000000-0000-4000-8000-000000000081','f3000000-0000-4000-8000-000000000081','REPLAY-C04-81',v_arr);
 if v_again->>'outcome'<>'ALREADY_APPLIED'
 or v_again->>'plano_id'<>v_old::text or v_again->>'estado_plano'<>'cancelado'
 or (v_again->>'executavel_simulacao')::boolean is distinct from false
 or (select count(*) from public.planos_recontato_sinteticos)<>1
 or (select count(*) from public.envios_template_sinteticos
  where estado='cancelado')<>1
 then raise exception 'FAIL C04 replay usou plano cancelado';end if;
end $replay$;
\echo 'PASS C04-REPLAY: chave idempotente não simula plano ativo após opt-out'
rollback;
