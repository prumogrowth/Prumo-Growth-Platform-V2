\set ON_ERROR_STOP on
begin;
insert into auth.users(id) values
('f1000000-0000-4000-8000-000000000001'),
('f1000000-0000-4000-8000-000000000002');
insert into public.atores(id) values
('f1000000-0000-4000-8000-000000000001'),
('f1000000-0000-4000-8000-000000000002');
insert into public.concessionarias(id,nome_operacional) values
('f2000000-0000-4000-8000-000000000001','Gestor A fictício'),
('f2000000-0000-4000-8000-000000000002','Gestor B fictício');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
('f1000000-0000-4000-8000-000000000001','f2000000-0000-4000-8000-000000000001','gestor'),
('f1000000-0000-4000-8000-000000000002','f2000000-0000-4000-8000-000000000002','gestor');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
('f3000000-0000-4000-8000-000000000001','f2000000-0000-4000-8000-000000000001','+5581998000001'),
('f3000000-0000-4000-8000-000000000002','f2000000-0000-4000-8000-000000000002','+5581998000001');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
('f4000000-0000-4000-8000-000000000001','f2000000-0000-4000-8000-000000000001','f3000000-0000-4000-8000-000000000001'),
('f4000000-0000-4000-8000-000000000002','f2000000-0000-4000-8000-000000000002','f3000000-0000-4000-8000-000000000002');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
('f5000000-0000-4000-8000-000000000001','f2000000-0000-4000-8000-000000000001','GESTOR_CANAL_A'),
('f5000000-0000-4000-8000-000000000002','f2000000-0000-4000-8000-000000000002','GESTOR_CANAL_B');
insert into public.catalogo_templates_sinteticos(id,concessionaria_id,codigo,versao,aprovado_simulacao) values
('f6000000-0000-4000-8000-000000000001','f2000000-0000-4000-8000-000000000001','APROVADO',1,true),
('f6000000-0000-4000-8000-000000000002','f2000000-0000-4000-8000-000000000001','PENDENTE',1,false),
('f6000000-0000-4000-8000-000000000003','f2000000-0000-4000-8000-000000000002','APROVADO',1,true);

insert into public.evidencias_elegibilidade_sinteticas(concessionaria_id,lead_id,canal_id,finalidade,referencia_ficticia) values
('f2000000-0000-4000-8000-000000000001','f3000000-0000-4000-8000-000000000001','f5000000-0000-4000-8000-000000000001','recontato_comercial_sintetico','PROVA_FICTICIA_CI_1');
do $test$
begin
 begin
 perform prumo_private.agendar_recontatos_sinteticos(
 'f1000000-0000-4000-8000-000000000001',
 'f2000000-0000-4000-8000-000000000001',
 'f4000000-0000-4000-8000-000000000001',
 'f5000000-0000-4000-8000-000000000001','nao-aprovado',
 jsonb_build_array(jsonb_build_object(
 'template_id','f6000000-0000-4000-8000-000000000002',
 'agendado_em',(statement_timestamp()+interval '1 day')::text)));
 raise exception 'FAIL agendar template não aprovado';
 exception when invalid_parameter_value then null; end;
 if exists(select 1 from public.planos_recontato_sinteticos)
 then raise exception 'FAIL plano parcial após rejeição';end if;
end $test$;
\echo 'PASS C05-APPROVAL: template nao aprovado negado antes do plano, sem escrita parcial'

do $test$
declare p uuid; r jsonb; dup jsonb;before_count integer;
begin
 r:=prumo_private.agendar_recontatos_sinteticos(
 'f1000000-0000-4000-8000-000000000001',
 'f2000000-0000-4000-8000-000000000001',
 'f4000000-0000-4000-8000-000000000001',
 'f5000000-0000-4000-8000-000000000001','gestor-A-1',
 jsonb_build_array(jsonb_build_object(
 'template_id','f6000000-0000-4000-8000-000000000001',
 'agendado_em',(statement_timestamp()+interval '1 day')::text)));
 p:=(r->>'plano_id')::uuid;
 begin
  perform prumo_private.cancelar_plano_gestor_sintetico(
  'f1000000-0000-4000-8000-000000000002',
  'f2000000-0000-4000-8000-000000000001',p,1);
  raise exception 'FAIL gestor B cancelou A';
 exception when insufficient_privilege then null; end;
 begin
  perform prumo_private.cancelar_plano_gestor_sintetico(
  'f1000000-0000-4000-8000-000000000001',
  'f2000000-0000-4000-8000-000000000001',p,99);
  raise exception 'FAIL versao invalida cancelou plano';
 exception when serialization_failure then null; end;
 if (select estado from public.planos_recontato_sinteticos where id=p)<>'ativo'
 then raise exception 'FAIL tentativa inválida alterou plano'; end if;
 r:=prumo_private.cancelar_plano_gestor_sintetico(
 'f1000000-0000-4000-8000-000000000001',
 'f2000000-0000-4000-8000-000000000001',p,1);
 before_count:=(select count(*) from public.eventos_envio_template_sinteticos);
 dup:=prumo_private.cancelar_plano_gestor_sintetico(
 'f1000000-0000-4000-8000-000000000001',
 'f2000000-0000-4000-8000-000000000001',p,1);
 if r->>'outcome'<>'APPLIED'
   or dup->>'outcome'<>'ALREADY_APPLIED'
   or (r->>'envios_cancelados')::int<>1
   or (select count(*) from public.eventos_envio_template_sinteticos)<>before_count
   or (select versao from public.planos_recontato_sinteticos where id=p)<>2
 then raise exception 'FAIL cancelamento versionado/idempotente'; end if;
end $test$;
\echo 'PASS C08-GESTOR: escopo, expected_version, repeticao e auditoria tecnica'

-- No UPDATE/INSERT access to the scheduled outgoing state by ordinary JWT role.
do $test$ begin
 if has_function_privilege('authenticated',
 'prumo_private.cancelar_plano_gestor_sintetico(uuid,uuid,uuid,bigint)','EXECUTE')
 or has_schema_privilege('authenticated','prumo_private','USAGE')
 then raise exception 'FAIL C08 privilegiado exposto'; end if;
end $test$;
\echo 'PASS C08-PRIVATE: gestor usa adaptador confiavel, sem funcao acessivel pelo navegador'
rollback;
