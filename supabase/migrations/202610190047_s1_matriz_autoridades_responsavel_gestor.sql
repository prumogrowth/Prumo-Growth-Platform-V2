-- S1-002/I10: matriz de alçada aprovada (responsavel x gestor x operador).
-- Predicado interno de CONTRATO para sandbox: NAO autoriza operação por si.
-- Não é RPC pública nem substitui checagem de sessão validada no gateway.
-- Autoridade restrita ao escopo explícito da concessionária.
create function prumo_private.s1_pode_administrar_operador(
 p_solicitante uuid, p_loja uuid, p_acao text, p_alvo uuid)
returns boolean language sql stable security invoker set search_path='' as $scope$
 select
  p_solicitante is not null and p_loja is not null
  and p_acao in (
   'adicionar_operador','adicionar_gestor',
   'desligar_definitivo_operador','desligar_definitivo_gestor',
   'suspender_temporariamente','reativar_temporariamente',
   'mover_atendimento','redistribuir_carteira','ajustar_distribuicao'
  )
  and p_alvo is not null and p_alvo<>p_solicitante
  and exists(
   select 1 from public.equipe_prumo_s1 e
   where e.ator_id=p_solicitante and e.estado='ativo'
  )
  and exists(select 1 from public.concessionarias l
   where l.id=p_loja and l.ativo)
  and (
   -- "responsavel" é a autoridade para inclusão e desligamento definitivo.
   exists(select 1 from public.vinculos_papel_escopo v
    where v.ator_id=p_solicitante and v.concessionaria_id=p_loja
      and v.papel='responsavel'
      and v.valido_desde<=pg_catalog.statement_timestamp()
      and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp()))
   or (
    -- Gestor apenas administra OPERADORES preexistentes na loja.
    p_acao in (
     'suspender_temporariamente','reativar_temporariamente',
     'mover_atendimento','redistribuir_carteira','ajustar_distribuicao'
    )
    and exists(select 1 from public.vinculos_papel_escopo v
     where v.ator_id=p_solicitante and v.concessionaria_id=p_loja
       and v.papel='gestor'
       and v.valido_desde<=pg_catalog.statement_timestamp()
       and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp()))
    and exists(select 1 from public.equipe_prumo_s1 ea
     where ea.ator_id=p_alvo and ea.estado in ('ativo','suspenso'))
    -- O vínculo pode estar temporariamente expirado/suspenso e ainda assim
    -- demonstra que é colaborador operacional PREEXISTENTE daquela loja.
    and exists(select 1 from public.vinculos_papel_escopo vo
     where vo.ator_id=p_alvo and vo.concessionaria_id=p_loja
       and vo.papel='operador'
       and vo.valido_desde<=pg_catalog.statement_timestamp())
    -- Se a mesma pessoa é gestor/responsável na loja, nunca rebaixar
    -- implicitamente seu nível administrativo.
    and not exists(select 1 from public.vinculos_papel_escopo va
     where va.ator_id=p_alvo and va.concessionaria_id=p_loja
       and va.papel in ('gestor','responsavel')
       and va.valido_desde<=pg_catalog.statement_timestamp()
       and (va.valido_ate is null or va.valido_ate>pg_catalog.statement_timestamp()))
   )
  );
$scope$;

-- Isolamento por padrão: este predicado com IDs explícitos só serve
-- para provar a matriz internamente, sob executor confiável.
revoke all on function
 prumo_private.s1_pode_administrar_operador(uuid,uuid,text,uuid)
 from public,anon,authenticated,service_role;
