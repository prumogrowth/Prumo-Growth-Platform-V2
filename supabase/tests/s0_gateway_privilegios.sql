\set ON_ERROR_STOP on
begin;
-- Only disposable pure PostgreSQL runner lacks auth.sessions; real local Supabase
-- already owns this table and MUST NOT use this test bootstrap.
create table if not exists auth.sessions(
 id uuid primary key,user_id uuid not null references auth.users(id));
insert into auth.users(id) values
 ('91000000-0000-4000-8000-000000000001'),
 ('91000000-0000-4000-8000-000000000002');
insert into public.atores(id) values
 ('91000000-0000-4000-8000-000000000001'),
 ('91000000-0000-4000-8000-000000000002');
insert into auth.sessions(id,user_id) values
 ('92000000-0000-4000-8000-000000000001','91000000-0000-4000-8000-000000000001'),
 ('92000000-0000-4000-8000-000000000002','91000000-0000-4000-8000-000000000002');
insert into public.concessionarias(id,nome_operacional) values
 ('93000000-0000-4000-8000-000000000001','Gateway A ficticia'),
 ('93000000-0000-4000-8000-000000000002','Gateway B ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('91000000-0000-4000-8000-000000000001','93000000-0000-4000-8000-000000000001','gestor'),
 ('91000000-0000-4000-8000-000000000002','93000000-0000-4000-8000-000000000002','gestor');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('94000000-0000-4000-8000-000000000001',
 '93000000-0000-4000-8000-000000000001','GW_S0_CANAL_A');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('95000000-0000-4000-8000-000000000001',
 '93000000-0000-4000-8000-000000000001','+5581877110991');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
 ('96000000-0000-4000-8000-000000000001',
 '93000000-0000-4000-8000-000000000001',
 '95000000-0000-4000-8000-000000000001');
insert into public.catalogo_templates_sinteticos(
 id,concessionaria_id,codigo,versao,aprovado_simulacao)
 values('97000000-0000-4000-8000-000000000001',
 '93000000-0000-4000-8000-000000000001','GW_FICTICIO',1,true);
insert into public.evidencias_elegibilidade_sinteticas(
 concessionaria_id,lead_id,canal_id,finalidade,referencia_ficticia)
 values('93000000-0000-4000-8000-000000000001',
 '95000000-0000-4000-8000-000000000001',
 '94000000-0000-4000-8000-000000000001','recontato_comercial_sintetico',
 'EVIDENCIA_GW_TESTE_001');
select prumo_private.agendar_recontatos_sinteticos(
 '91000000-0000-4000-8000-000000000001',
 '93000000-0000-4000-8000-000000000001',
 '96000000-0000-4000-8000-000000000001',
 '94000000-0000-4000-8000-000000000001',
 'GW-PLAN-1',
 jsonb_build_array(jsonb_build_object(
 'template_id','97000000-0000-4000-8000-000000000001',
 'agendado_em',(statement_timestamp()+interval '1 day')::text)));

-- Create callback needing human classification without real Meta contact.
select prumo_private.registrar_callback_c07_sintetico(
 '94000000-0000-4000-8000-000000000001',
 'gw-no-match','GW-CB-1','INCERTO_SIMULADO',
 statement_timestamp());

set local role prumo_s0_gateway;
do $test$
declare r jsonb; v_plan uuid;v_pend uuid;
begin
 -- Gateway cannot browse tables or invoke original internal functions.
 if has_table_privilege(current_user,'public.leads_loja','SELECT')
 or has_table_privilege(current_user,'prumo_private.auditoria_gateway_s0','SELECT')
 or has_function_privilege(current_user,
  'prumo_private.cancelar_plano_gestor_sintetico(uuid,uuid,uuid,bigint)','EXECUTE')
 then raise exception 'FAIL GW-01 gateway inherited powerful privilege';end if;
 begin
  perform count(*) from auth.sessions;
  raise exception 'FAIL GW-01 auth session read escaped';
 exception when insufficient_privilege then null;end;
 begin
  perform count(*) from public.leads_loja;
  raise exception 'FAIL GW-01 read escaped';
 exception when insufficient_privilege then null;end;
 begin
  perform prumo_private.cancelar_plano_gestor_sintetico(
   '91000000-0000-4000-8000-000000000001',
   '93000000-0000-4000-8000-000000000001',
   '96000000-0000-4000-8000-000000000001',1);
  raise exception 'FAIL GW-01 raw function callable';
 exception when insufficient_privilege then null;end;
end $test$;
\echo 'PASS GW-01: role gateway sem leitura direta e sem EXECUTE no dominio'

do $test$
declare r jsonb;
begin
 begin
  perform prumo_private.gateway_cancelar_plano_s0(
   '91000000-0000-4000-8000-000000000002', -- store B actor
   '92000000-0000-4000-8000-000000000002', -- valid B session
   '93000000-0000-4000-8000-000000000001', -- A plan
   '96000000-0000-4000-8000-000000000001',1);
  raise exception 'FAIL GW-02 cross-store manager used A plan';
 exception when insufficient_privilege then null;end;
 begin
  perform prumo_private.gateway_cancelar_plano_s0(
   '91000000-0000-4000-8000-000000000001',
   '92000000-0000-4000-8000-000000000002', -- B session != A actor
   '93000000-0000-4000-8000-000000000001',
   '96000000-0000-4000-8000-000000000001',1);
  raise exception 'FAIL GW-02 session impersonation';
 exception when insufficient_privilege then null;end;
end $test$;
\echo 'PASS GW-02: sessao divergente e gestor interloja bloqueados'

reset role;
-- Resolve the fixture identifiers as privileged owner, not via the gateway.
select set_config('prumo.test.gw_plano',(select id::text from public.planos_recontato_sinteticos where chave_idempotencia='GW-PLAN-1'),true);
select set_config('prumo.test.gw_pendencia',(select p.id::text from public.pendencias_reconciliacao_c07_sinteticas p
 join public.eventos_callback_sinteticos e
 on e.concessionaria_id=p.concessionaria_id and e.id=p.evento_id
 where e.evento_externo_ficticio='GW-CB-1'),true);
set local role prumo_s0_gateway;
do $test$
declare r jsonb;v_plano uuid;v_pendencia uuid;
begin
 v_plano:=current_setting('prumo.test.gw_plano')::uuid;
 v_pendencia:=current_setting('prumo.test.gw_pendencia')::uuid;
 r:=prumo_private.gateway_cancelar_plano_s0(
  '91000000-0000-4000-8000-000000000001',
  '92000000-0000-4000-8000-000000000001',
  '93000000-0000-4000-8000-000000000001',v_plano,1);
 if r->>'outcome'<>'APPLIED' then raise exception 'FAIL GW-03 cancel';end if;
 r:=prumo_private.gateway_cancelar_plano_s0(
  '91000000-0000-4000-8000-000000000001',
  '92000000-0000-4000-8000-000000000001',
  '93000000-0000-4000-8000-000000000001',v_plano,1);
 if r->>'outcome'<>'ALREADY_APPLIED' then raise exception 'FAIL GW-03 replay';end if;
 r:=prumo_private.gateway_conciliar_c07_s0(
  '91000000-0000-4000-8000-000000000001',
  '92000000-0000-4000-8000-000000000001',
  '93000000-0000-4000-8000-000000000001',v_pendencia,1,
  'ENCERRAR_SEM_PROVA','Anotacao ficticia de revisao de incerteza',null);
 if r->>'outcome'<>'APPLIED' then raise exception 'FAIL GW-03 reconcile';end if;
end $test$;
\echo 'PASS GW-03: cancelamento e conciliacao privados por gateway nao login'

reset role;
do $test$
begin
 if (select count(*) from prumo_private.auditoria_gateway_s0)<>3
 or (select count(*) from prumo_private.auditoria_gateway_s0
     where resultado='ALREADY_APPLIED')<>1
 or (select count(*) from prumo_private.auditoria_gateway_s0
     where operacao='conciliar_c07')<>1
 or (select count(*) from public.auditoria_reconciliacao_c07_sintetica)<>1
 then raise exception 'FAIL GW-04 audit log incomplete';end if;
end $test$;
\echo 'PASS GW-04: trilha transacional de comandos aplicados/replay'

delete from auth.sessions where id='92000000-0000-4000-8000-000000000001';
set local role prumo_s0_gateway;
do $test$
begin
 begin
  perform prumo_private.gateway_cancelar_plano_s0(
   '91000000-0000-4000-8000-000000000001',
   '92000000-0000-4000-8000-000000000001',
   '93000000-0000-4000-8000-000000000001',
   current_setting('prumo.test.gw_plano')::uuid,1);
  raise exception 'FAIL GW-05 revoked session accepted';
 exception when insufficient_privilege then null;end;
end $test$;
reset role;
do $test$
begin
 if (select count(*) from prumo_private.auditoria_gateway_s0)<>3
 then raise exception 'FAIL GW-05 denied operation added success audit';end if;
end $test$;
\echo 'PASS GW-05: sessao revogada rejeitada antes de escrita e auditoria'
do $acl$
declare f_name text;f_oid oid;v_proc record;
begin
 if not exists(select 1 from pg_roles where rolname='prumo_s0_gateway'
  and not rolcanlogin and not rolinherit)
 then raise exception 'FAIL GW-06 gateway role unexpectedly login/inherits';end if;
 for f_name in select unnest(array[
 'prumo_private.gateway_cancelar_plano_s0(uuid,uuid,uuid,uuid,bigint)',
 'prumo_private.gateway_conciliar_c07_s0(uuid,uuid,uuid,uuid,bigint,text,text,uuid)'
 ]) loop
  f_oid:=f_name::regprocedure::oid;
  select p.prosecdef,pg_get_userbyid(p.proowner) as owner_role into v_proc
  from pg_proc p where p.oid=f_oid;
  if not v_proc.prosecdef or v_proc.owner_role<>'postgres'
   or not has_function_privilege('prumo_s0_gateway',f_oid,'EXECUTE')
   or has_function_privilege('anon',f_oid,'EXECUTE')
   or has_function_privilege('authenticated',f_oid,'EXECUTE')
   or has_function_privilege('service_role',f_oid,'EXECUTE')
  then raise exception 'FAIL GW-06 function ACL/owner %',f_name;end if;
 end loop;
 if has_table_privilege('prumo_s0_gateway',
   'prumo_private.auditoria_gateway_s0','SELECT')
 or has_table_privilege('prumo_s0_gateway',
   'prumo_private.auditoria_gateway_s0','INSERT')
 or has_table_privilege('prumo_s0_gateway',
   'prumo_private.auditoria_gateway_s0','UPDATE')
 or has_table_privilege('prumo_s0_gateway',
   'prumo_private.auditoria_gateway_s0','DELETE')
 then raise exception 'FAIL GW-06 audit table not private';end if;
end $acl$;
\echo 'PASS GW-06: dono e ACL das wrappers conferidos, tabela de auditoria inacessivel'
rollback;
