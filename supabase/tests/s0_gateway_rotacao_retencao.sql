\set ON_ERROR_STOP on
begin;
insert into prumo_private.gateway_chaves_assinatura_s0(
 chave_id,segredo,valido_desde,valido_ate,ativo)
 values
 ('f3000000-0000-4000-8000-000000000001',decode(repeat('a7',32),'hex'),
  statement_timestamp()-interval '10 minutes',statement_timestamp()+interval '1 hour',false),
 ('f3000000-0000-4000-8000-000000000002',decode(repeat('b8',32),'hex'),
  statement_timestamp()-interval '10 minutes',statement_timestamp()+interval '1 hour',false),
 ('f3000000-0000-4000-8000-000000000003',decode(repeat('c9',32),'hex'),
  statement_timestamp()+interval '1 hour',statement_timestamp()+interval '2 hours',false);
do $keys$
declare r jsonb;
begin
 if (select count(*) from prumo_private.gateway_eventos_chave_s0
  where tipo='REGISTRADA')<>3
 then raise exception 'FAIL KEY-01 registration audit';end if;
 r:=prumo_private.alterar_estado_chave_gateway_s0(
  'f3000000-0000-4000-8000-000000000001',1,true,'Ativacao ficticia chave anterior');
 if r->>'outcome'<>'APPLIED' or (r->>'nova_versao')::int<>2
 then raise exception 'FAIL KEY-01 first activate';end if;
 r:=prumo_private.alterar_estado_chave_gateway_s0(
  'f3000000-0000-4000-8000-000000000002',1,true,'Ativacao ficticia chave substituta');
 if r->>'outcome'<>'APPLIED' then raise exception 'FAIL KEY-01 second activate';end if;
 if (select count(*) from prumo_private.gateway_chaves_assinatura_s0
  where ativo)<>2 then raise exception 'FAIL KEY-01 overlap';end if;
 begin
  perform prumo_private.alterar_estado_chave_gateway_s0(
  'f3000000-0000-4000-8000-000000000003',1,true,'Chave ainda nao valida para ativacao');
  raise exception 'FAIL KEY-01 future activation accepted';
 exception when invalid_parameter_value then null;end;
end $keys$;
\echo 'PASS KEY-01: registro inativo, ativacao versionada, sobreposicao, chave futura negada'

do $keys$
declare r jsonb;
begin
 begin
  perform prumo_private.alterar_estado_chave_gateway_s0(
  'f3000000-0000-4000-8000-000000000001',1,false,'Versao antiga deveria falhar');
  raise exception 'FAIL KEY-02 stale version';
 exception when serialization_failure then null;end;
 r:=prumo_private.alterar_estado_chave_gateway_s0(
  'f3000000-0000-4000-8000-000000000001',2,false,
  'Revogacao ficticia apos ativar chave substituta');
 if r->>'outcome'<>'APPLIED' or (r->>'revogacao_definitiva')::boolean is distinct from true
 then raise exception 'FAIL KEY-02 revoke';end if;
 begin
  perform prumo_private.alterar_estado_chave_gateway_s0(
  'f3000000-0000-4000-8000-000000000001',3,true,'Proibido reativar chave revogada');
  raise exception 'FAIL KEY-02 revoked key reactivated';
 exception when invalid_parameter_value then null;end;
 begin
  update prumo_private.gateway_chaves_assinatura_s0
  set segredo=decode(repeat('00',32),'hex'),versao=3
  where chave_id='f3000000-0000-4000-8000-000000000002';
  raise exception 'FAIL KEY-02 secret mutated without new key';
 exception when insufficient_privilege then null;end;
 if (select count(*) from prumo_private.gateway_eventos_chave_s0
     where tipo='ATIVADA')<>2
 or (select count(*) from prumo_private.gateway_eventos_chave_s0
     where tipo='REVOGADA')<>1
 or (select count(*) from prumo_private.gateway_eventos_chave_s0)<>6
 then raise exception 'FAIL KEY-02 key lifecycle history';end if;
end $keys$;
\echo 'PASS KEY-02: versao antiga negada, revogacao irreversivel e material imutavel'

create function prumo_private.assinar_rotacao_teste(
 p_chave_byte text,p_emitido bigint,p_nonce uuid
) returns text language plpgsql security invoker set search_path='' as $fn$
declare v_ext text;v_bytes bytea;v_material text;
begin
 select n.nspname into v_ext from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace
 where e.extname='pgcrypto';
 v_material:=prumo_private.gateway_material_assinatura_s0(
  'cancelar_plano',
  'f4000000-0000-4000-8000-000000000001',
  'f4000000-0000-4000-8000-000000000002',
  'f4000000-0000-4000-8000-000000000003',
  'f4000000-0000-4000-8000-000000000004',
  1,null,null,null,p_emitido,p_nonce);
 execute pg_catalog.format('select %I.hmac($1,$2,''sha256'')',v_ext)
 into v_bytes using pg_catalog.convert_to(v_material,'UTF8'),
 pg_catalog.decode(repeat(p_chave_byte,32),'hex');
 return pg_catalog.encode(v_bytes,'hex');
end $fn$;
revoke all on function prumo_private.assinar_rotacao_teste(text,bigint,uuid)
 from public,anon,authenticated,service_role,prumo_s0_gateway;

do $verify$
declare v_t bigint:=extract(epoch from clock_timestamp())::bigint;
 v_nonce uuid:='f5000000-0000-4000-8000-000000000001';
 v_sig text;
begin
 v_sig:=prumo_private.assinar_rotacao_teste('a7',v_t,
  'f5000000-0000-4000-8000-000000000002');
 begin
  perform prumo_private.gateway_validar_prova_s0(
   'cancelar_plano','f4000000-0000-4000-8000-000000000001',
   'f4000000-0000-4000-8000-000000000002',
   'f4000000-0000-4000-8000-000000000003',
   'f4000000-0000-4000-8000-000000000004',
   1,null,null,null,'f3000000-0000-4000-8000-000000000001',
   v_t,'f5000000-0000-4000-8000-000000000002',v_sig);
  raise exception 'FAIL KEY-03 revoked HMAC accepted';
 exception when insufficient_privilege then null;end;
 v_sig:=prumo_private.assinar_rotacao_teste('b8',v_t,v_nonce);
 perform prumo_private.gateway_validar_prova_s0(
   'cancelar_plano','f4000000-0000-4000-8000-000000000001',
   'f4000000-0000-4000-8000-000000000002',
   'f4000000-0000-4000-8000-000000000003',
   'f4000000-0000-4000-8000-000000000004',
   1,null,null,null,'f3000000-0000-4000-8000-000000000002',
   v_t,v_nonce,v_sig);
 begin
  perform prumo_private.gateway_validar_prova_s0(
   'cancelar_plano','f4000000-0000-4000-8000-000000000001',
   'f4000000-0000-4000-8000-000000000002',
   'f4000000-0000-4000-8000-000000000003',
   'f4000000-0000-4000-8000-000000000004',
   1,null,null,null,'f3000000-0000-4000-8000-000000000002',
   v_t,v_nonce,v_sig);
  raise exception 'FAIL KEY-03 nonce replay';
 exception when insufficient_privilege then null;end;
 if (select count(*) from prumo_private.gateway_provas_usadas_s0)<>1
 then raise exception 'FAIL KEY-03 valid proof count';end if;
end $verify$;
\echo 'PASS KEY-03: assinatura chave revogada negada, substituta aceita e nonce unico'

insert into prumo_private.gateway_provas_usadas_s0(nonce,chave_id,consumido_em)
 values('f5000000-0000-4000-8000-000000000099',
 'f3000000-0000-4000-8000-000000000002',
 clock_timestamp()-interval '20 minutes');
do $retention$
declare r jsonb;
begin
 begin
  perform prumo_private.expurgar_nonces_gateway_s0(
   clock_timestamp()-interval '1 minute');
  raise exception 'FAIL KEY-04 premature deletion';
 exception when invalid_parameter_value then null;end;
 r:=prumo_private.expurgar_nonces_gateway_s0(
   clock_timestamp()-interval '11 minutes');
 if (r->>'apagados')::int<>1 then raise exception 'FAIL KEY-04 expected one cleanup';end if;
 if (select count(*) from prumo_private.gateway_provas_usadas_s0)<>1
 or (select quantidade from prumo_private.gateway_limpezas_nonce_s0
    order by id desc limit 1)<>1
 then raise exception 'FAIL KEY-04 fresh nonce deleted';end if;
end $retention$;
\echo 'PASS KEY-04: expurgo minimo 10 minutos, nonce recente preservado e contagem auditada'

set local role prumo_s0_gateway;
do $scope$
begin
 if has_function_privilege(current_user,
  'prumo_private.alterar_estado_chave_gateway_s0(uuid,bigint,boolean,text)','EXECUTE')
 or has_function_privilege(current_user,
  'prumo_private.expurgar_nonces_gateway_s0(timestamptz)','EXECUTE')
 or has_table_privilege(current_user,'prumo_private.gateway_eventos_chave_s0','SELECT')
 then raise exception 'FAIL KEY-05 gateway gained rotation/retention privileges';end if;
 begin
  perform prumo_private.alterar_estado_chave_gateway_s0(
  'f3000000-0000-4000-8000-000000000002',2,false,
  'Ator tecnico nao autorizado');
  raise exception 'FAIL KEY-05 role rotated key';
 exception when insufficient_privilege then null;end;
end $scope$;
reset role;
\echo 'PASS KEY-05: gateway sem permissao de rotacao, expurgo ou historico'
rollback;
