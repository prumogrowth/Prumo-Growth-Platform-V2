-- I62 local signed bridge for I61 canonical case-only exception.
-- Ephemeral GoTrue stack ONLY, never operational migration.
begin;
do $pre$ begin
 if current_user<>'postgres'
 or to_regclass('prumo_private.s1_excecoes_caso_i61') is null
 or not exists(select 1 from pg_roles where rolname='prumo_s1_i21_executor')
 or not exists(select 1 from pg_roles where rolname='prumo_s1_i22_custodio')
 then raise exception 'I62_LOCAL_SIGNED_PREREQUISITE' using errcode='42501';end if;
end $pre$;

-- This bridge is postgres-owned, checks the REAL live GoTrue session,
-- and derives p_gestor solely from the verified signed principal.
create function prumo_private.s1_excecao_signed_i62(
 p_ator uuid,p_sessao uuid,p_operacao text,p_id1 uuid,
 p_caso uuid,p_atr uuid,p_destino uuid
) returns jsonb language plpgsql security definer set search_path='' as $fn$
begin
 if session_user<>'prumo_s1_signed_login_ci'
 or p_ator is null or p_sessao is null or p_id1 is null
 or p_operacao not in ('MOVE','REVOKE') then
 raise exception 'I62_CALLER_DENIED' using errcode='42501';end if;
 perform 1 from auth.sessions s where s.id=p_sessao and s.user_id=p_ator
 for key share of s;
 if not found then raise exception 'I62_SESSION_REVOKED' using errcode='42501';end if;
 if not exists(select 1 from public.atores a where a.id=p_ator)
 then raise exception 'I62_ACTOR_UNKNOWN' using errcode='42501';end if;
 if p_operacao='MOVE' then
  if p_caso is null or p_atr is null or p_destino is null then
   raise exception 'I62_FIELDS_DENIED' using errcode='42501';end if;
  return prumo_private.s1_mover_excecao_caso_i61(
   p_ator,p_id1,p_caso,p_atr,p_destino);
 end if;
 if p_caso is not null or p_atr is not null or p_destino is not null
 then raise exception 'I62_FIELDS_DENIED' using errcode='42501';end if;
 return prumo_private.s1_revogar_excecao_i61(p_ator,p_id1);
end $fn$;
revoke all on function prumo_private.s1_excecao_signed_i62(
 uuid,uuid,text,uuid,uuid,uuid,uuid)
 from public,anon,authenticated,service_role,prumo_s1_signed_login_ci;
grant usage on schema prumo_private to prumo_s1_i21_executor;
grant execute on function prumo_private.s1_excecao_signed_i62(
 uuid,uuid,text,uuid,uuid,uuid,uuid) to prumo_s1_i21_executor;

grant create on schema prumo_s1_signed_i20 to prumo_s1_i21_executor;
set local role prumo_s1_i21_executor;
create function prumo_s1_signed_i20.invocar_excecao_i62(
 p_ator uuid,p_sessao uuid,p_acao text,p_id1 uuid,
 p_caso uuid,p_atr uuid,p_destino uuid,
 p_chave uuid,p_emitido bigint,p_nonce uuid,p_hmac text
) returns jsonb language plpgsql security definer set search_path='' as $signed$
declare v_op text;v_motivo text;v_now bigint;v_nonce uuid;v_result jsonb;
begin
 if p_ator is null or p_sessao is null or p_id1 is null
 or p_chave is null or p_emitido is null or p_nonce is null
 or p_hmac is null or p_hmac !~ '^[0-9a-f]{64}$'
 then raise exception 'I62_INVALID_FIELDS' using errcode='42501';end if;
 if p_acao='MOVE' and p_caso is not null and p_atr is not null
 and p_destino is not null then
  v_op:='EXC62M';v_motivo:=null;
 elsif p_acao='REVOKE' and p_caso is null and p_atr is null
 and p_destino is null then
  v_op:='EXC62R';v_motivo:='R';
 else raise exception 'I62_INVALID_OPERATION' using errcode='42501';end if;
 v_now:=extract(epoch from pg_catalog.clock_timestamp())::bigint;
 if p_emitido<v_now-30 or p_emitido>v_now+5
 then raise exception 'I62_PROOF_EXPIRED' using errcode='42501';end if;
 perform prumo_s1_signed_i20.verificar_hmac(
  v_op,p_ator,p_sessao,p_id1,p_caso,p_atr,p_destino,
  null,v_motivo,p_chave,p_emitido,p_nonce,p_hmac);
 insert into prumo_s1_signed_i20.nonces(id,chave_id)
 values(p_nonce,p_chave) on conflict do nothing returning id into v_nonce;
 if v_nonce is null then raise exception 'I62_PROOF_REPLAY'
 using errcode='42501';end if;
 v_result:=prumo_private.s1_excecao_signed_i62(
  p_ator,p_sessao,p_acao,p_id1,p_caso,p_atr,p_destino);
 if v_result->>'outcome' not in
 ('MOVED_CASE_EXCEPTION','REVOKED_CASE_ACCESS','ALREADY_REVOKED')
 then raise exception 'I62_BAD_RESULT' using errcode='42501';end if;
 return v_result;
end $signed$;
revoke all on function prumo_s1_signed_i20.invocar_excecao_i62(
 uuid,uuid,text,uuid,uuid,uuid,uuid,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s1_signed_login_ci;
grant execute on function prumo_s1_signed_i20.invocar_excecao_i62(
 uuid,uuid,text,uuid,uuid,uuid,uuid,uuid,bigint,uuid,text)
 to prumo_s1_signed_login_ci;
reset role;
revoke create on schema prumo_s1_signed_i20 from prumo_s1_i21_executor;
do $audit$ begin
 if (select pg_catalog.pg_get_userbyid(proowner) from pg_catalog.pg_proc
 where oid='prumo_s1_signed_i20.invocar_excecao_i62(uuid,uuid,text,uuid,uuid,uuid,uuid,uuid,bigint,uuid,text)'::regprocedure)
 <>'prumo_s1_i21_executor'
 or (select pg_catalog.pg_get_userbyid(proowner) from pg_catalog.pg_proc
 where oid='prumo_private.s1_excecao_signed_i62(uuid,uuid,text,uuid,uuid,uuid,uuid)'::regprocedure)
 <>'postgres'
 or has_function_privilege('authenticated',
 'prumo_s1_signed_i20.invocar_excecao_i62(uuid,uuid,text,uuid,uuid,uuid,uuid,uuid,bigint,uuid,text)','EXECUTE')
 or has_function_privilege('prumo_s1_signed_login_ci',
 'prumo_private.s1_excecao_signed_i62(uuid,uuid,text,uuid,uuid,uuid,uuid)','EXECUTE')
 or has_table_privilege('prumo_s1_signed_login_ci',
 'prumo_private.s1_excecoes_caso_i61','SELECT')
 then raise exception 'I62_OWNER_ACL_INVALID' using errcode='42501';end if;
end $audit$;
commit;
