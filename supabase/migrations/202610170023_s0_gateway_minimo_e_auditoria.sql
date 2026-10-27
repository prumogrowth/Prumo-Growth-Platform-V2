-- S0 LOCAL ONLY candidate: non-login gateway role with two private entrypoints.
-- Provision any real LOGIN and credentials OUTSIDE migrations, after security approval.
-- NO API endpoint, no Meta transmission, no privilege to browse business tables.
do $role$
begin
 if not exists(select 1 from pg_roles where rolname='prumo_s0_gateway') then
   create role prumo_s0_gateway nologin noinherit;
 end if;
end $role$;
revoke all on schema prumo_private from prumo_s0_gateway;
grant usage on schema prumo_private to prumo_s0_gateway;

-- Append-only from the gateway's perspective; privileged database owner can
-- still administrate this table. This is NOT a cryptographic audit ledger.
create table prumo_private.auditoria_gateway_s0 (
 id uuid primary key default gen_random_uuid(),
 ator_id uuid not null references public.atores(id) on delete restrict,
 sessao_id uuid not null,
 concessionaria_id uuid not null references public.concessionarias(id) on delete restrict,
 operacao text not null check(operacao in ('cancelar_plano','conciliar_c07')),
 alvo_id uuid not null,
 versao_esperada bigint not null check(versao_esperada>0),
 resultado text not null check(resultado in ('APPLIED','ALREADY_APPLIED')),
 ocorrido_em timestamptz not null default statement_timestamp()
);
create index auditoria_gateway_s0_scope
 on prumo_private.auditoria_gateway_s0(concessionaria_id,ocorrido_em);
revoke all on prumo_private.auditoria_gateway_s0
 from public,anon,authenticated,service_role,prumo_s0_gateway;

-- SECURITY DEFINER is used ONLY inside unexposed prumo_private.
-- Creator/owner must be postgres: existing domain code checks current_user
-- exactly 'postgres'.  The limited gateway is NOT granted the domain functions.
-- The trusted app server MUST bind actor/session from GoTrue, never client body.
create function prumo_private.gateway_cancelar_plano_s0(
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
  ator_id,sessao_id,concessionaria_id,operacao,alvo_id,versao_esperada,resultado)
 values(p_ator,p_sessao,p_loja,'cancelar_plano',p_plano,p_versao,
        v_result->>'outcome');
 return v_result;
end $gateway$;

create function prumo_private.gateway_conciliar_c07_s0(
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
  ator_id,sessao_id,concessionaria_id,operacao,alvo_id,versao_esperada,resultado)
 values(p_ator,p_sessao,p_loja,'conciliar_c07',p_pendencia,p_versao,
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
