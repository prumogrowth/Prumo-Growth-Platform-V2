-- S1-002/I14: contrato de identidade derivada da sessao, em schema NAO EXPOSTO.
-- APENAS sandbox PostgreSQL. Antes de producao exige GoTrue/PostgREST
-- validando JWT, sessao e configuracao de schemas expostos.
-- NAO acrescenta identidade do solicitante nos argumentos do cliente.
-- A função definer transita para postgres APENAS apos autenticação fake
-- do caller 'authenticated', e chama as funções transacionais I11/I13.
-- Public e service_role continuam sem EXECUTE nas tres funções.
create function prumo_private.s1_exigir_identidade_sessao()
returns uuid language plpgsql security invoker set search_path='' as $auth$
declare v_ator uuid;
begin
 -- O papel aqui e claim verificados POR UM GATEWAY real em produção;
 -- em PG17 fake-auth estes parametros sao sinteticos, nao criptograficos.
 if pg_catalog.current_setting('request.jwt.claim.role',true)
    is distinct from 'authenticated' then
   raise exception 'SESSAO_AUTENTICADA_OBRIGATORIA' using errcode='42501';
 end if;
 v_ator:=auth.uid();
 if v_ator is null or not exists(
  select 1 from public.atores a where a.id=v_ator
 ) then
   raise exception 'IDENTIDADE_SESSAO_INVALIDA' using errcode='42501';
 end if;
 return v_ator;
end $auth$;

create function prumo_private.s1_mover_atendimento_sessao(
 p_loja uuid,p_caso uuid,p_atribuicao_esperada uuid,p_destino uuid)
returns jsonb language plpgsql security definer set search_path='' as $rpc$
declare v_ator uuid;
begin
 v_ator:=prumo_private.s1_exigir_identidade_sessao();
 return prumo_private.s1_mover_atendimento_da_equipe(
   v_ator,p_loja,p_caso,p_atribuicao_esperada,p_destino);
end $rpc$;

create function prumo_private.s1_pausar_operador_sessao(
 p_operador uuid,p_motivo_codigo text)
returns jsonb language plpgsql security definer set search_path='' as $rpc$
declare v_ator uuid;
begin
 v_ator:=prumo_private.s1_exigir_identidade_sessao();
 return prumo_private.s1_pausar_operador_da_equipe(
  v_ator,p_operador,p_motivo_codigo);
end $rpc$;

create function prumo_private.s1_reativar_operador_sessao(p_operador uuid)
returns jsonb language plpgsql security definer set search_path='' as $rpc$
declare v_ator uuid;
begin
 v_ator:=prumo_private.s1_exigir_identidade_sessao();
 return prumo_private.s1_reativar_operador_da_equipe(v_ator,p_operador);
end $rpc$;

-- PostgreSQL dá EXECUTE a PUBLIC como padrao, inclusive para DEFINER.
-- Retirar primeiro e conceder APENAS os tres endpoints prototipos
-- à role authenticated. prumo_private nao e Data API schema exposto.
revoke all on function prumo_private.s1_exigir_identidade_sessao()
 from public,anon,authenticated,service_role;
revoke all on function prumo_private.s1_mover_atendimento_sessao(
 uuid,uuid,uuid,uuid) from public,anon,authenticated,service_role;
revoke all on function prumo_private.s1_pausar_operador_sessao(
 uuid,text) from public,anon,authenticated,service_role;
revoke all on function prumo_private.s1_reativar_operador_sessao(
 uuid) from public,anon,authenticated,service_role;

-- IMPORTANTE: somente schema privado; nao criar RPC em public nem expor
-- 'prumo_private' em Supabase Data API. GRANT USAGE nao e EXPOSED SCHEMA.
grant usage on schema prumo_private to authenticated;
grant execute on function prumo_private.s1_mover_atendimento_sessao(
 uuid,uuid,uuid,uuid) to authenticated;
grant execute on function prumo_private.s1_pausar_operador_sessao(
 uuid,text) to authenticated;
grant execute on function prumo_private.s1_reativar_operador_sessao(
 uuid) to authenticated;
