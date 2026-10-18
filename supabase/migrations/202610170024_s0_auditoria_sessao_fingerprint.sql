-- Audit 024: session identifiers should not be retained verbatim in
-- operation logs; store deterministic SHA256 fingerprint for correlation only.
-- Session UUID remains an authorization input under GoTrue, but NOT audit data.
alter table prumo_private.auditoria_gateway_s0
 add column sessao_fingerprint_sha256 text;
update prumo_private.auditoria_gateway_s0
 set sessao_fingerprint_sha256=pg_catalog.encode(
   pg_catalog.sha256(pg_catalog.convert_to(sessao_id::text,'UTF8')),'hex');
alter table prumo_private.auditoria_gateway_s0
 alter column sessao_fingerprint_sha256 set not null;
alter table prumo_private.auditoria_gateway_s0
 add constraint auditoria_gateway_session_hash_len
 check(sessao_fingerprint_sha256 ~ '^[0-9a-f]{64}$');
alter table prumo_private.auditoria_gateway_s0 drop column sessao_id;

create or replace function prumo_private.gateway_cancelar_plano_s0(
 p_ator uuid,p_sessao uuid,p_loja uuid,p_plano uuid,p_versao bigint
) returns jsonb language plpgsql security definer set search_path='' as $gateway$
declare v_result jsonb;
begin
 if p_ator is null or p_sessao is null or p_loja is null
    or p_plano is null or p_versao is null then
  raise exception 'INVALID_GATEWAY_ARGUMENTS' using errcode='22023';
 end if;
 perform 1 from auth.sessions s where s.id=p_sessao and s.user_id=p_ator
  for key share;
 if not found then
   raise exception 'SESSAO_INATIVA' using errcode='42501';
 end if;
 v_result:=prumo_private.cancelar_plano_gestor_sintetico(
  p_ator,p_loja,p_plano,p_versao);
 if v_result->>'outcome' not in ('APPLIED','ALREADY_APPLIED')
   then raise exception 'UNSUPPORTED_DOMAIN_OUTCOME' using errcode='22023';end if;
 insert into prumo_private.auditoria_gateway_s0(
  ator_id,sessao_fingerprint_sha256,concessionaria_id,operacao,alvo_id,versao_esperada,resultado)
 values(p_ator,pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(p_sessao::text,'UTF8')),'hex'),p_loja,'cancelar_plano',p_plano,p_versao,
        v_result->>'outcome');
 return v_result;
end $gateway$;

create or replace function prumo_private.gateway_conciliar_c07_s0(
 p_ator uuid,p_sessao uuid,p_loja uuid,p_pendencia uuid,p_versao bigint,
 p_decisao text,p_justificativa text,p_envio uuid default null
) returns jsonb language plpgsql security definer set search_path='' as $gateway$
declare v_result jsonb;
begin
 if p_ator is null or p_sessao is null or p_loja is null or
    p_pendencia is null or p_versao is null then
  raise exception 'INVALID_GATEWAY_ARGUMENTS' using errcode='22023';
 end if;
 perform 1 from auth.sessions s where s.id=p_sessao and s.user_id=p_ator
  for key share;
 if not found then
   raise exception 'SESSAO_INATIVA' using errcode='42501';
 end if;
 v_result:=prumo_private.conciliar_pendencia_c07_sintetica(
  p_ator,p_loja,p_pendencia,p_versao,p_decisao,p_justificativa,p_envio);
 if v_result->>'outcome' not in ('APPLIED','ALREADY_APPLIED')
   then raise exception 'UNSUPPORTED_DOMAIN_OUTCOME' using errcode='22023';end if;
 insert into prumo_private.auditoria_gateway_s0(
  ator_id,sessao_fingerprint_sha256,concessionaria_id,operacao,alvo_id,versao_esperada,resultado)
 values(p_ator,pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(p_sessao::text,'UTF8')),'hex'),p_loja,'conciliar_c07',p_pendencia,p_versao,
        v_result->>'outcome');
 return v_result;
end $gateway$;

revoke all on function prumo_private.gateway_cancelar_plano_s0(
 uuid,uuid,uuid,uuid,bigint) from public,anon,authenticated,service_role;
revoke all on function prumo_private.gateway_conciliar_c07_s0(
 uuid,uuid,uuid,uuid,bigint,text,text,uuid) from public,anon,authenticated,service_role;
grant execute on function prumo_private.gateway_cancelar_plano_s0(
 uuid,uuid,uuid,uuid,bigint) to prumo_s0_gateway;
grant execute on function prumo_private.gateway_conciliar_c07_s0(
 uuid,uuid,uuid,uuid,bigint,text,text,uuid) to prumo_s0_gateway;
