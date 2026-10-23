-- I55 ONLY ephemeral GoTrue/PostgREST CI; after S0/S1 migrations 053+054
-- HMAC custody I22; executor owner NOLOGIN I21; bridge owner postgres.
begin;
do $guard$
begin
 if current_user<>'postgres' or to_regclass('prumo_private.s0_fila_humana') is null
 or not exists(select 1 from pg_roles where rolname='prumo_s1_i21_executor')
 or not exists(select 1 from pg_roles where rolname='prumo_s1_i22_custodio')
 then raise exception 'I55_DISPOSABLE_SIGNED_STACK_REQUIRED' using errcode='42501';end if;
end $guard$;

-- Bound projection: NO telephone, conversation, case history, or other-team cases.
-- The signed actor is re-authenticated via live auth.sessions for every invocation.
create function prumo_private.s0_fila_signed_v55(
 p_ator uuid,p_sessao uuid,p_loja uuid,p_ciclo uuid,p_versao bigint,
 p_operation text) returns jsonb language plpgsql security definer
 set search_path='' as $bridge$
declare v_rows jsonb;
begin
 if session_user<>'prumo_s1_signed_login_ci'
  or p_ator is null or p_sessao is null or p_loja is null
  or p_operation not in ('LIST','CLAIM') then
  raise exception 'I55_UNTRUSTED_CALLER' using errcode='42501';end if;
 perform 1 from auth.sessions s where s.id=p_sessao and s.user_id=p_ator
 for key share of s;
 if not found then raise exception 'I55_SESSION_REVOKED' using errcode='42501';end if;
 if not exists(select 1 from public.atores a where a.id=p_ator) then
  raise exception 'I55_UNKNOWN_ACTOR' using errcode='42501';end if;
 if p_operation='LIST' then
  if p_ciclo is not null or p_versao is not null then
   raise exception 'I55_LIST_PARAMETERS' using errcode='42501';end if;
  -- This predicate is evaluated at the current clock on every request.
  if not exists(select 1 from public.equipe_prumo_s1 e
   join public.vinculos_papel_escopo v on v.ator_id=e.ator_id
    and v.concessionaria_id=p_loja and v.papel='gestor'
    and v.valido_desde<=pg_catalog.clock_timestamp()
    and (v.valido_ate is null or v.valido_ate>pg_catalog.clock_timestamp())
   join public.concessionarias l on l.id=v.concessionaria_id and l.ativo
   where e.ator_id=p_ator and e.estado='ativo')
  then raise exception 'I55_MANAGER_SCOPE_DENIED' using errcode='42501';end if;
  select coalesce(pg_catalog.jsonb_agg(
       pg_catalog.jsonb_build_object('concessionaria_id',z.concessionaria_id,
       'lead_id',z.lead_id,'ciclo_id',z.ciclo_id,'versao',z.versao)
       order by z.criado_em,z.ciclo_id),'[]'::jsonb)
   into v_rows
  from (select f.concessionaria_id,f.lead_id,f.ciclo_id,f.versao,f.criado_em
        from prumo_private.s0_fila_humana f
        where f.concessionaria_id=p_loja and f.estado='pendente'
        and not exists(select 1 from public.casos_humanos h
         where h.concessionaria_id=p_loja and h.lead_id=f.lead_id)
        order by f.criado_em,f.ciclo_id limit 25) z;
  return pg_catalog.jsonb_build_object('outcome','QUEUE_LIST','items',v_rows);
 end if;
 if p_ciclo is null or p_versao is null or p_versao<1 then
  raise exception 'I55_CLAIM_PARAMETERS' using errcode='42501';end if;
 -- S0 authoritative CAS/lead/grant recheck AFTER lock; no duplicate queue.
 return prumo_private.s0_fila_assumir(p_ator,p_loja,p_ciclo,p_versao);
end $bridge$;
revoke all on function prumo_private.s0_fila_signed_v55(
 uuid,uuid,uuid,uuid,bigint,text)
 from public,anon,authenticated,service_role,prumo_s1_signed_login_ci;
grant usage on schema prumo_private to prumo_s1_i21_executor;
grant execute on function prumo_private.s0_fila_signed_v55(
 uuid,uuid,uuid,uuid,bigint,text) to prumo_s1_i21_executor;

grant create on schema prumo_s1_signed_i20 to prumo_s1_i21_executor;
set local role prumo_s1_i21_executor;
create function prumo_s1_signed_i20.invocar_fila_v55(
 p_ator uuid,p_sessao uuid,p_loja uuid,p_ciclo uuid,p_versao bigint,
 p_chave uuid,p_emitido bigint,p_nonce uuid,p_hmac text
) returns jsonb language plpgsql security definer set search_path='' as $signed$
declare v_op text;v_action text;v_now bigint;v_nonce uuid;v_result jsonb;
begin
 if p_ator is null or p_sessao is null or p_loja is null or p_chave is null
  or p_emitido is null or p_nonce is null or p_hmac !~ '^[0-9a-f]{64}$'
 then raise exception 'I55_INVALID_FIELDS' using errcode='42501';end if;
 if p_ciclo is null and p_versao is null then
  v_op:='FILA55L';v_action:='L';
 elsif p_ciclo is not null and p_versao between 1 and 9223372036854775807 then
  v_op:='FILA55C';v_action:='C:'||p_versao::text;
 else raise exception 'I55_INVALID_OPERATION' using errcode='42501';end if;
 v_now:=extract(epoch from pg_catalog.clock_timestamp())::bigint;
 if p_emitido<v_now-30 or p_emitido>v_now+5 then
  raise exception 'I55_EXPIRED' using errcode='42501';end if;
 perform prumo_s1_signed_i20.verificar_hmac(
  v_op,p_ator,p_sessao,p_loja,p_ciclo,null,null,null,v_action,
  p_chave,p_emitido,p_nonce,p_hmac);
 insert into prumo_s1_signed_i20.nonces(id,chave_id)
 values(p_nonce,p_chave) on conflict do nothing returning id into v_nonce;
 if v_nonce is null then
  raise exception 'I55_NONCE_REPLAY' using errcode='42501';end if;
 v_result:=prumo_private.s0_fila_signed_v55(
  p_ator,p_sessao,p_loja,p_ciclo,p_versao,
  case when p_ciclo is null then 'LIST' else 'CLAIM' end);
 if v_result->>'outcome' not in
    ('QUEUE_LIST','CLAIMED_BY_MANAGER','CONFLICT','ALREADY_HAS_CASE') then
  raise exception 'I55_BAD_RESULT' using errcode='42501';end if;
 return v_result;
end $signed$;
revoke all on function prumo_s1_signed_i20.invocar_fila_v55(
 uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s1_signed_login_ci;
grant execute on function prumo_s1_signed_i20.invocar_fila_v55(
 uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)
 to prumo_s1_signed_login_ci;
reset role;
revoke create on schema prumo_s1_signed_i20 from prumo_s1_i21_executor;
do $audit$
begin
 if (select pg_catalog.pg_get_userbyid(proowner) from pg_catalog.pg_proc
  where oid='prumo_s1_signed_i20.invocar_fila_v55(uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)'::regprocedure)
   <>'prumo_s1_i21_executor'
  or (select pg_catalog.pg_get_userbyid(proowner) from pg_catalog.pg_proc
  where oid='prumo_private.s0_fila_signed_v55(uuid,uuid,uuid,uuid,bigint,text)'::regprocedure)
   <>'postgres'
  or has_function_privilege('authenticated',
   'prumo_s1_signed_i20.invocar_fila_v55(uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)','EXECUTE')
  or has_function_privilege('prumo_s1_signed_login_ci',
   'prumo_private.s0_fila_signed_v55(uuid,uuid,uuid,uuid,bigint,text)','EXECUTE')
  or has_table_privilege('prumo_s1_signed_login_ci','prumo_private.s0_fila_humana','SELECT')
 then raise exception 'I55_PRIVILEGE_BOUNDARY_BROKEN' using errcode='42501';end if;
end $audit$;
commit;
