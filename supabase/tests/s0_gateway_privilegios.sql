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


-- Test-only symmetric key, NEVER from a production migration.
insert into prumo_private.gateway_chaves_assinatura_s0(
 chave_id,segredo,valido_desde,valido_ate,ativo)
 values('f1000000-0000-4000-8000-000000000001',
 decode(repeat('a5',32),'hex'),statement_timestamp()-interval '1 hour',
 statement_timestamp()+interval '1 hour',false);
select prumo_private.alterar_estado_chave_gateway_s0(
 'f1000000-0000-4000-8000-000000000001',1,true,
 'Ativacao de chave exclusivamente ficticia');

create function prumo_private.assinar_prova_gateway_teste(
 p_operacao text,p_ator uuid,p_sessao uuid,p_loja uuid,p_alvo uuid,
 p_versao bigint,p_decisao text,p_justificativa text,p_envio uuid,
 p_emitido bigint,p_nonce uuid
) returns text language plpgsql security invoker set search_path='' as $fn$
declare v_schema text;v_bytes bytea;v_payload text;
begin
 select n.nspname into v_schema from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace where e.extname='pgcrypto';
 v_payload:=prumo_private.gateway_material_assinatura_s0(
  p_operacao,p_ator,p_sessao,p_loja,p_alvo,p_versao,p_decisao,
  p_justificativa,p_envio,p_emitido,p_nonce);
 execute pg_catalog.format('select %I.hmac($1,$2,''sha256'')',v_schema)
 into v_bytes using pg_catalog.convert_to(v_payload,'UTF8'),decode(repeat('a5',32),'hex');
 return pg_catalog.encode(v_bytes,'hex');
end $fn$;
revoke all on function prumo_private.assinar_prova_gateway_teste(
 text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,bigint,uuid)
 from public,anon,authenticated,service_role,prumo_s0_gateway;

select set_config('prumo.test.gw_plano',
 (select id::text from public.planos_recontato_sinteticos
 where chave_idempotencia='GW-PLAN-1'),true);
select set_config('prumo.test.gw_pendencia',
 (select p.id::text from public.pendencias_reconciliacao_c07_sinteticas p
 join public.eventos_callback_sinteticos e
 on e.concessionaria_id=p.concessionaria_id and e.id=p.evento_id
 where e.evento_externo_ficticio='GW-CB-1'),true);
select set_config('prumo.test.issued',
 (extract(epoch from clock_timestamp())::bigint)::text,true);
-- Proofs computed by privileged fixture role and passed to a restricted session.
-- All nonce values distinct across commands, including idempotent replay.
select set_config('prumo.test.sig_a1',prumo_private.assinar_prova_gateway_teste(
 'cancelar_plano','91000000-0000-4000-8000-000000000001',
 '92000000-0000-4000-8000-000000000001',
 '93000000-0000-4000-8000-000000000001',current_setting('prumo.test.gw_plano')::uuid,
 1,null,null,null,current_setting('prumo.test.issued')::bigint,
 'f2000000-0000-4000-8000-000000000001'),true);
select set_config('prumo.test.sig_a2',prumo_private.assinar_prova_gateway_teste(
 'cancelar_plano','91000000-0000-4000-8000-000000000001',
 '92000000-0000-4000-8000-000000000001',
 '93000000-0000-4000-8000-000000000001',current_setting('prumo.test.gw_plano')::uuid,
 1,null,null,null,current_setting('prumo.test.issued')::bigint,
 'f2000000-0000-4000-8000-000000000002'),true);
select set_config('prumo.test.sig_c1',prumo_private.assinar_prova_gateway_teste(
 'conciliar_c07','91000000-0000-4000-8000-000000000001',
 '92000000-0000-4000-8000-000000000001',
 '93000000-0000-4000-8000-000000000001',current_setting('prumo.test.gw_pendencia')::uuid,
 1,'ENCERRAR_SEM_PROVA','Anotacao ficticia de revisao de incerteza',null,
 current_setting('prumo.test.issued')::bigint,
 'f2000000-0000-4000-8000-000000000003'),true);
select set_config('prumo.test.sig_revoked',prumo_private.assinar_prova_gateway_teste(
 'cancelar_plano','91000000-0000-4000-8000-000000000001',
 '92000000-0000-4000-8000-000000000001',
 '93000000-0000-4000-8000-000000000001',current_setting('prumo.test.gw_plano')::uuid,
 1,null,null,null,current_setting('prumo.test.issued')::bigint,
 'f2000000-0000-4000-8000-000000000004'),true);

set local role prumo_s0_gateway;
do $gw$
declare r jsonb;v_plan uuid:=current_setting('prumo.test.gw_plano')::uuid;
begin
 if has_table_privilege(current_user,'public.leads_loja','SELECT')
 or has_table_privilege(current_user,'prumo_private.auditoria_gateway_s0','SELECT')
 or has_function_privilege(current_user,
 'prumo_private.gateway_cancelar_plano_s0(uuid,uuid,uuid,uuid,bigint)','EXECUTE')
 or not has_function_privilege(current_user,
 'prumo_private.gateway_cancelar_plano_assinado_s0(uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)','EXECUTE')
 then raise exception 'FAIL GW-01 privileges';end if;
 begin perform count(*) from auth.sessions;
  raise exception 'FAIL GW-01 session read';exception when insufficient_privilege then null;end;
 begin perform count(*) from public.leads_loja;
  raise exception 'FAIL GW-01 leads read';exception when insufficient_privilege then null;end;
 begin perform prumo_private.gateway_cancelar_plano_s0(
 '91000000-0000-4000-8000-000000000001',
 '92000000-0000-4000-8000-000000000001',
 '93000000-0000-4000-8000-000000000001',v_plan,1);
 raise exception 'FAIL GW-01 unsigned legacy call';exception when insufficient_privilege then null;end;
end $gw$;
\echo 'PASS GW-01: gateway sem leitura direta e sem acesso ao legado nao assinado'

do $gw$
declare v_plan uuid:=current_setting('prumo.test.gw_plano')::uuid;
begin
 begin
  perform prumo_private.gateway_cancelar_plano_assinado_s0(
  '91000000-0000-4000-8000-000000000001',
  '92000000-0000-4000-8000-000000000001',
  '93000000-0000-4000-8000-000000000001',v_plan,1,
  'f1000000-0000-4000-8000-000000000001',
  current_setting('prumo.test.issued')::bigint,
  'f2000000-0000-4000-8000-000000000008',repeat('0',64));
  raise exception 'FAIL GW-02 bad proof accepted';
 exception when insufficient_privilege then null;end;
 begin
  perform prumo_private.gateway_cancelar_plano_assinado_s0(
  '91000000-0000-4000-8000-000000000001',
  '92000000-0000-4000-8000-000000000001',
  '93000000-0000-4000-8000-000000000001',v_plan,2,
  'f1000000-0000-4000-8000-000000000001',
  current_setting('prumo.test.issued')::bigint,
  'f2000000-0000-4000-8000-000000000001',current_setting('prumo.test.sig_a1'));
  raise exception 'FAIL GW-02 modified version accepted';
 exception when insufficient_privilege then null;end;
 begin
  perform prumo_private.gateway_cancelar_plano_assinado_s0(
  '91000000-0000-4000-8000-000000000001',
  '92000000-0000-4000-8000-000000000001',
  '93000000-0000-4000-8000-000000000001',v_plan,1,
  'f1000000-0000-4000-8000-000000000001',
  current_setting('prumo.test.issued')::bigint-300,
  'f2000000-0000-4000-8000-000000000001',current_setting('prumo.test.sig_a1'));
  raise exception 'FAIL GW-02 expired proof accepted';
 exception when insufficient_privilege then null;end;
end $gw$;
\echo 'PASS GW-02: senha SQL isolada, prova adulterada ou expirada negadas'

do $gw$
declare r jsonb;v_plan uuid:=current_setting('prumo.test.gw_plano')::uuid;
 v_pend uuid:=current_setting('prumo.test.gw_pendencia')::uuid;
begin
 r:=prumo_private.gateway_cancelar_plano_assinado_s0(
  '91000000-0000-4000-8000-000000000001',
  '92000000-0000-4000-8000-000000000001',
  '93000000-0000-4000-8000-000000000001',v_plan,1,
  'f1000000-0000-4000-8000-000000000001',
  current_setting('prumo.test.issued')::bigint,
  'f2000000-0000-4000-8000-000000000001',current_setting('prumo.test.sig_a1'));
 if r->>'outcome'<>'APPLIED' then raise exception 'FAIL GW-03 signed cancel';end if;
 begin
  perform prumo_private.gateway_cancelar_plano_assinado_s0(
  '91000000-0000-4000-8000-000000000001',
  '92000000-0000-4000-8000-000000000001',
  '93000000-0000-4000-8000-000000000001',v_plan,1,
  'f1000000-0000-4000-8000-000000000001',
  current_setting('prumo.test.issued')::bigint,
  'f2000000-0000-4000-8000-000000000001',current_setting('prumo.test.sig_a1'));
  raise exception 'FAIL GW-03 nonce replay accepted';
 exception when insufficient_privilege then null;end;
 r:=prumo_private.gateway_cancelar_plano_assinado_s0(
  '91000000-0000-4000-8000-000000000001',
  '92000000-0000-4000-8000-000000000001',
  '93000000-0000-4000-8000-000000000001',v_plan,1,
  'f1000000-0000-4000-8000-000000000001',
  current_setting('prumo.test.issued')::bigint,
  'f2000000-0000-4000-8000-000000000002',current_setting('prumo.test.sig_a2'));
 if r->>'outcome'<>'ALREADY_APPLIED' then raise exception 'FAIL GW-03 new proof idempotency';end if;
 r:=prumo_private.gateway_conciliar_c07_assinado_s0(
  '91000000-0000-4000-8000-000000000001',
  '92000000-0000-4000-8000-000000000001',
  '93000000-0000-4000-8000-000000000001',v_pend,1,
  'ENCERRAR_SEM_PROVA','Anotacao ficticia de revisao de incerteza',null,
  'f1000000-0000-4000-8000-000000000001',
  current_setting('prumo.test.issued')::bigint,
  'f2000000-0000-4000-8000-000000000003',current_setting('prumo.test.sig_c1'));
 if r->>'outcome'<>'APPLIED' then raise exception 'FAIL GW-03 signed reconcile';end if;
end $gw$;
\echo 'PASS GW-03: assinaturas validas aplicam, repeticao de nonce negada e novo nonce idempotente'

reset role;
do $verify$
begin
 if (select count(*) from prumo_private.auditoria_gateway_s0)<>3
  or (select count(*) from prumo_private.gateway_provas_usadas_s0)<>3
  or (select count(*) from prumo_private.auditoria_gateway_s0 where resultado='ALREADY_APPLIED')<>1
 then raise exception 'FAIL GW-04 audit or nonce ledger';end if;
end $verify$;
\echo 'PASS GW-04: auditoria de tres comandos e tres provas consumidas, sem extras'

delete from auth.sessions where id='92000000-0000-4000-8000-000000000001';
set local role prumo_s0_gateway;
do $revoked$
begin
 begin
  perform prumo_private.gateway_cancelar_plano_assinado_s0(
  '91000000-0000-4000-8000-000000000001',
  '92000000-0000-4000-8000-000000000001',
  '93000000-0000-4000-8000-000000000001',
  current_setting('prumo.test.gw_plano')::uuid,1,
  'f1000000-0000-4000-8000-000000000001',
  current_setting('prumo.test.issued')::bigint,
  'f2000000-0000-4000-8000-000000000004',current_setting('prumo.test.sig_revoked'));
  raise exception 'FAIL GW-05 revoked session accepted';
 exception when insufficient_privilege then null;end;
end $revoked$;
reset role;
do $verify$
begin
 if (select count(*) from prumo_private.auditoria_gateway_s0)<>3
 or (select count(*) from prumo_private.gateway_provas_usadas_s0)<>3
 then raise exception 'FAIL GW-05 revoked session wrote data';end if;
end $verify$;
\echo 'PASS GW-05: sessao revogada bloqueia mesmo prova valida, sem efeito adicional'

do $acl$
declare f_name text;f_oid oid;v_proc record;
begin
 if not exists(select 1 from pg_roles where rolname='prumo_s0_gateway'
  and not rolcanlogin and not rolinherit) then raise exception 'FAIL GW-06 role';end if;
 for f_name in select unnest(array[
 'prumo_private.gateway_cancelar_plano_assinado_s0(uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)',
 'prumo_private.gateway_conciliar_c07_assinado_s0(uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)'
 ]) loop
  f_oid:=f_name::regprocedure::oid;
  select p.prosecdef,pg_get_userbyid(p.proowner) as owner_role into v_proc
  from pg_proc p where p.oid=f_oid;
  if not v_proc.prosecdef or v_proc.owner_role<>'postgres'
   or not has_function_privilege('prumo_s0_gateway',f_oid,'EXECUTE')
   or has_function_privilege('anon',f_oid,'EXECUTE')
   or has_function_privilege('authenticated',f_oid,'EXECUTE')
   or has_function_privilege('service_role',f_oid,'EXECUTE')
  then raise exception 'FAIL GW-06 function owner/ACL %',f_name;end if;
 end loop;
 if has_function_privilege('prumo_s0_gateway',
   'prumo_private.gateway_cancelar_plano_s0(uuid,uuid,uuid,uuid,bigint)','EXECUTE')
 or has_function_privilege('prumo_s0_gateway',
   'prumo_private.gateway_conciliar_c07_s0(uuid,uuid,uuid,uuid,bigint,text,text,uuid)','EXECUTE')
 or has_table_privilege('prumo_s0_gateway','prumo_private.gateway_chaves_assinatura_s0','SELECT')
 or has_table_privilege('prumo_s0_gateway','prumo_private.gateway_provas_usadas_s0','INSERT')
 or has_table_privilege('prumo_s0_gateway','prumo_private.auditoria_gateway_s0','SELECT')
 then raise exception 'FAIL GW-06 privileged material available to login';end if;
end $acl$;
\echo 'PASS GW-06: somente wrappers assinadas, tabelas de segredos e provas inacessiveis'

do $privacy$
declare expected text;
begin
 expected:=pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
 '92000000-0000-4000-8000-000000000001','UTF8')),'hex');
 if exists(select 1 from information_schema.columns
 where table_schema='prumo_private' and table_name='auditoria_gateway_s0'
 and column_name='sessao_id')
 or (select count(*) from prumo_private.auditoria_gateway_s0)<>3
 or exists(select 1 from prumo_private.auditoria_gateway_s0
  where sessao_fingerprint_sha256<>expected)
 then raise exception 'FAIL GW-07 audit data';end if;
end $privacy$;
\echo 'PASS GW-07: auditoria preserva fingerprint sem guardar UUID da sessao'
rollback;
