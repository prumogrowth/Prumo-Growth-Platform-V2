-- S1-002 / ISSUE10 / I37 - signed, versioned intake-only command.
-- TEST-ONLY POSTGRES / disposable Supabase GoTrue, after fixtures I20-I22 and S1_053.
-- The I22 custodian alone verifies HMAC; executor alone consumes nonce.
-- SQL login gets no private table grants or ability to mint a session.
begin;
do $gate$
begin
 if current_user<>'postgres'
   or not exists(select 1 from pg_roles where rolname='prumo_s1_i22_custodio')
   or not exists(select 1 from pg_roles where rolname='prumo_s1_i21_executor')
 then raise exception 'I37_CUSTODY_AND_LOCAL_POSTGRES_REQUIRED' using errcode='42501';end if;
end $gate$;

-- A small postgres-owned bridge verifies a LIVE GoTrue session after HMAC,
-- then uses the existing S1_053 business function as postgres. No public RPC.
create function prumo_private.s1_apply_intake_signed_v37(
 p_ator uuid,p_sessao uuid,p_operador uuid,p_pausar boolean,p_versao bigint
) returns jsonb language plpgsql security definer set search_path='' as $bridge$
begin
 if session_user<>'prumo_s1_signed_login_ci'
  or p_ator is null or p_sessao is null
  or p_operador is null or p_pausar is null
  or p_versao is null or p_versao<1 then
  raise exception 'I37_NO_TRUSTED_CONTEXT' using errcode='42501';end if;
 perform 1 from auth.sessions s
 where s.id=p_sessao and s.user_id=p_ator for key share of s;
 if not found then
  raise exception 'I37_SESSION_REVOKED' using errcode='42501';end if;
 if not exists(select 1 from public.atores where id=p_ator) then
  raise exception 'I37_ACTOR_UNKNOWN' using errcode='42501';end if;
 return prumo_private.s1_definir_disponibilidade_leads_10(
  p_ator,p_operador,p_pausar,p_versao);
end $bridge$;
revoke all on function prumo_private.s1_apply_intake_signed_v37(
 uuid,uuid,uuid,boolean,bigint) from public,anon,authenticated,service_role,
 prumo_s1_signed_login_ci;
grant usage on schema prumo_private to prumo_s1_i21_executor;
grant execute on function prumo_private.s1_apply_intake_signed_v37(
 uuid,uuid,uuid,boolean,bigint) to prumo_s1_i21_executor;

-- Narrow entrypoint: there is no route back to PAUSAR / REATIVAR legacy
-- and no caller-supplied reason. A nonce replay cannot reuse the proof.
grant create on schema prumo_s1_signed_i20 to prumo_s1_i21_executor;
set local role prumo_s1_i21_executor;
create function prumo_s1_signed_i20.invocar_intake_v37(
 p_ator uuid,p_sessao uuid,p_operador uuid,p_pausar boolean,p_versao bigint,
 p_chave uuid,p_emitido bigint,p_nonce uuid,p_hmac text
) returns jsonb language plpgsql security definer set search_path='' as $signed$
declare
 v_acao text;
 v_agora bigint;
 v_consumido uuid;
 v_resultado jsonb;
begin
 if p_ator is null or p_sessao is null or p_operador is null
  or p_pausar is null or p_versao is null
  or p_versao<1 or p_versao>9223372036854775807
  or p_chave is null or p_emitido is null or p_nonce is null
  or p_hmac is null or p_hmac !~ '^[0-9a-f]{64}$'
 then raise exception 'I37_FIELDS_INVALID' using errcode='42501';end if;
 v_agora:=extract(epoch from pg_catalog.clock_timestamp())::bigint;
 if p_emitido<v_agora-30 or p_emitido>v_agora+5 then
  raise exception 'I37_EXPIRED' using errcode='42501';end if;
 v_acao:=(case when p_pausar then 'P:' else 'R:' end)||p_versao::text;
 perform prumo_s1_signed_i20.verificar_hmac(
  'INTAKE',p_ator,p_sessao,
  null,null,null,null,p_operador,v_acao,
  p_chave,p_emitido,p_nonce,p_hmac);
 insert into prumo_s1_signed_i20.nonces(id,chave_id)
 values(p_nonce,p_chave)
 on conflict do nothing returning id into v_consumido;
 if v_consumido is null then
  raise exception 'I37_NONCE_REPLAY' using errcode='42501';end if;
 v_resultado:=prumo_private.s1_apply_intake_signed_v37(
  p_ator,p_sessao,p_operador,p_pausar,p_versao);
 if v_resultado->>'outcome' not in ('INTAKE_PAUSED','INTAKE_RESUMED','ALREADY_APPLIED')
   or v_resultado->>'redistribution' is distinct from 'DEFERRED_S0_PROOF'
 then raise exception 'I37_INVALID_RESULT' using errcode='42501';end if;
 return v_resultado;
end $signed$;
reset role;
revoke create on schema prumo_s1_signed_i20 from prumo_s1_i21_executor;
revoke all on function prumo_s1_signed_i20.invocar_intake_v37(
 uuid,uuid,uuid,boolean,bigint,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s1_signed_login_ci;
grant execute on function prumo_s1_signed_i20.invocar_intake_v37(
 uuid,uuid,uuid,boolean,bigint,uuid,bigint,uuid,text)
 to prumo_s1_signed_login_ci;

do $assert$
declare exec_owner text;bridge_owner text;
begin
 select pg_catalog.pg_get_userbyid(proowner) into exec_owner from pg_catalog.pg_proc
 where oid='prumo_s1_signed_i20.invocar_intake_v37(
 uuid,uuid,uuid,boolean,bigint,uuid,bigint,uuid,text)'::regprocedure;
 select pg_catalog.pg_get_userbyid(proowner) into bridge_owner from pg_catalog.pg_proc
 where oid='prumo_private.s1_apply_intake_signed_v37(
 uuid,uuid,uuid,boolean,bigint)'::regprocedure;
 if exec_owner<>'prumo_s1_i21_executor' or bridge_owner<>'postgres'
  or has_schema_privilege('prumo_s1_signed_login_ci','prumo_private','USAGE')
  or has_table_privilege('prumo_s1_signed_login_ci',
    'prumo_s1_signed_i20.chaves','SELECT')
  or has_table_privilege('prumo_s1_i21_executor',
    'prumo_s1_signed_i20.chaves','SELECT')
  or has_schema_privilege('prumo_s1_i21_executor','prumo_s1_signed_i20','CREATE')
  or has_function_privilege('authenticated',
    'prumo_s1_signed_i20.invocar_intake_v37(
 uuid,uuid,uuid,boolean,bigint,uuid,bigint,uuid,text)','EXECUTE')
 then raise exception 'I37_OWNER_OR_ACL_INVALID' using errcode='42501';end if;
end $assert$;
commit;
