-- S0 only: second credential boundary to mitigate SQL-only gateway compromise.
-- NO SIGNING KEYS IN MIGRATIONS, no remote deploy. Test fixtures inject dummy keys.
-- Signature must be produced by a trusted backend AFTER GoTrue user verification.
-- DB verifies HMAC, short TTL and a single-use nonce before any domain mutation.
create schema if not exists prumo_crypto;
revoke all on schema prumo_crypto from public,anon,authenticated,service_role,prumo_s0_gateway;
create extension if not exists pgcrypto with schema prumo_crypto;

create table prumo_private.gateway_chaves_assinatura_s0 (
 chave_id uuid primary key,
 segredo bytea not null check(octet_length(segredo)>=32),
 valido_desde timestamptz not null default statement_timestamp(),
 valido_ate timestamptz not null,
 ativo boolean not null default false,
 check(valido_ate>valido_desde)
);
create table prumo_private.gateway_provas_usadas_s0 (
 nonce uuid primary key,
 chave_id uuid not null references prumo_private.gateway_chaves_assinatura_s0(chave_id),
 consumido_em timestamptz not null default clock_timestamp()
);
revoke all on prumo_private.gateway_chaves_assinatura_s0,
 prumo_private.gateway_provas_usadas_s0 from public,anon,authenticated,service_role,prumo_s0_gateway;

-- Fixed fields separated by |. Free text is SHA256 hashed; UUID/integers have
-- unambiguous canonical representations. Python must use this exact encoding.
create function prumo_private.gateway_material_assinatura_s0(
 p_operacao text,p_ator uuid,p_sessao uuid,p_loja uuid,p_alvo uuid,
 p_versao bigint,p_decisao text,p_justificativa text,p_envio uuid,
 p_emitido bigint,p_nonce uuid
) returns text language sql immutable set search_path='' as $sql$
 select pg_catalog.concat_ws('|',
 'prumo-gw-v1',p_operacao,p_ator::text,p_sessao::text,p_loja::text,
 p_alvo::text,p_versao::text,coalesce(p_decisao,'-'),
 pg_catalog.encode(pg_catalog.sha256(
  pg_catalog.convert_to(coalesce(p_justificativa,''),'UTF8')),'hex'),
 coalesce(p_envio::text,'-'),p_emitido::text,p_nonce::text)
$sql$;
revoke all on function prumo_private.gateway_material_assinatura_s0(
 text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,bigint,uuid)
 from public,anon,authenticated,service_role,prumo_s0_gateway;

create function prumo_private.gateway_validar_prova_s0(
 p_operacao text,p_ator uuid,p_sessao uuid,p_loja uuid,p_alvo uuid,
 p_versao bigint,p_decisao text,p_justificativa text,p_envio uuid,
 p_chave uuid,p_emitido bigint,p_nonce uuid,p_assinatura text
) returns void language plpgsql security definer set search_path='' as $fn$
declare v_segredo bytea;v_agora timestamptz;v_emitido timestamptz;
 v_schema text;v_esperada bytea;v_material text;v_consumida uuid;
begin
 if p_operacao not in ('cancelar_plano','conciliar_c07') or
 p_ator is null or p_sessao is null or p_loja is null or p_alvo is null
 or p_versao is null or p_versao<1 or p_chave is null
 or p_emitido is null or p_nonce is null or p_assinatura is null
 or p_assinatura !~ '^[0-9a-f]{64}$'
 then raise exception 'PROVA_INVALIDA' using errcode='42501';end if;
 v_agora:=pg_catalog.clock_timestamp();
 -- Permit 5 seconds of clock skew but no token older than 30 seconds.
 if p_emitido>pg_catalog.extract(epoch from v_agora)::bigint+5
 or p_emitido<pg_catalog.extract(epoch from v_agora)::bigint-30
 then raise exception 'PROVA_EXPIRADA' using errcode='42501';end if;
 v_emitido:=pg_catalog.to_timestamp(p_emitido::double precision);
 select segredo into v_segredo
 from prumo_private.gateway_chaves_assinatura_s0
 where chave_id=p_chave and ativo
  and valido_desde<=v_emitido and valido_ate>v_agora
 for share;
 if not found then raise exception 'PROVA_INVALIDA' using errcode='42501';end if;
 select n.nspname into v_schema
 from pg_catalog.pg_extension e join pg_catalog.pg_namespace n
 on n.oid=e.extnamespace where e.extname='pgcrypto';
 if v_schema is null then raise exception 'HMAC_INDISPONIVEL' using errcode='42501';end if;
 v_material:=prumo_private.gateway_material_assinatura_s0(
 p_operacao,p_ator,p_sessao,p_loja,p_alvo,p_versao,p_decisao,p_justificativa,
 p_envio,p_emitido,p_nonce);
 execute pg_catalog.format('select %I.hmac($1,$2,''sha256'')',v_schema)
 into v_esperada using pg_catalog.convert_to(v_material,'UTF8'),v_segredo;
 if v_esperada is distinct from pg_catalog.decode(p_assinatura,'hex')
 then raise exception 'PROVA_INVALIDA' using errcode='42501';end if;
 insert into prumo_private.gateway_provas_usadas_s0(nonce,chave_id)
 values(p_nonce,p_chave) on conflict do nothing returning nonce into v_consumida;
 if v_consumida is null
 then raise exception 'PROVA_REUTILIZADA' using errcode='42501';end if;
end $fn$;
revoke all on function prumo_private.gateway_validar_prova_s0(
 text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s0_gateway;

-- Old gateway entrypoints retained for internal postgres compatibility but
-- MUST NOT remain executable by the gateway role.
revoke execute on function prumo_private.gateway_cancelar_plano_s0(
 uuid,uuid,uuid,uuid,bigint) from prumo_s0_gateway;
revoke execute on function prumo_private.gateway_conciliar_c07_s0(
 uuid,uuid,uuid,uuid,bigint,text,text,uuid) from prumo_s0_gateway;

create function prumo_private.gateway_cancelar_plano_assinado_s0(
 p_ator uuid,p_sessao uuid,p_loja uuid,p_plano uuid,p_versao bigint,
 p_chave uuid,p_emitido bigint,p_nonce uuid,p_assinatura text
) returns jsonb language plpgsql security definer set search_path='' as $fn$
begin
 perform prumo_private.gateway_validar_prova_s0(
 'cancelar_plano',p_ator,p_sessao,p_loja,p_plano,p_versao,null,null,null,
 p_chave,p_emitido,p_nonce,p_assinatura);
 return prumo_private.gateway_cancelar_plano_s0(
 p_ator,p_sessao,p_loja,p_plano,p_versao);
end $fn$;
create function prumo_private.gateway_conciliar_c07_assinado_s0(
 p_ator uuid,p_sessao uuid,p_loja uuid,p_pendencia uuid,p_versao bigint,
 p_decisao text,p_justificativa text,p_envio uuid,
 p_chave uuid,p_emitido bigint,p_nonce uuid,p_assinatura text
) returns jsonb language plpgsql security definer set search_path='' as $fn$
begin
 perform prumo_private.gateway_validar_prova_s0(
 'conciliar_c07',p_ator,p_sessao,p_loja,p_pendencia,p_versao,
 p_decisao,p_justificativa,p_envio,p_chave,p_emitido,p_nonce,p_assinatura);
 return prumo_private.gateway_conciliar_c07_s0(
 p_ator,p_sessao,p_loja,p_pendencia,p_versao,p_decisao,p_justificativa,p_envio);
end $fn$;
revoke all on function prumo_private.gateway_cancelar_plano_assinado_s0(
 uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role;
revoke all on function prumo_private.gateway_conciliar_c07_assinado_s0(
 uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role;
grant execute on function prumo_private.gateway_cancelar_plano_assinado_s0(
 uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text) to prumo_s0_gateway;
grant execute on function prumo_private.gateway_conciliar_c07_assinado_s0(
 uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text) to prumo_s0_gateway;
