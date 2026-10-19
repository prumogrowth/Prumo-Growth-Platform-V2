-- S1-002/I13. Revogacao de chefia e suspensao do gestor durante
-- movimento manual DEVEM bloquear ate o commit e revalidar alçada.
-- SECURITY INVOKER, executor de teste postgres. Nenhum endpoint/JWT real.
-- Preserva assinatura e trilha I12, ajusta exclusivamente locks no caminho.
create or replace function prumo_private.s1_mover_atendimento_da_equipe(
 p_solicitante uuid,p_loja uuid,p_caso uuid,
 p_atribuicao_esperada uuid,p_destino uuid)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare
 v_origem uuid;
 v_achado uuid;
 v_data timestamptz;
 v_nova uuid;
 v_motivo text;
 v_status text;
 v_atores integer;
 v_chefias integer;
 v_responsavel boolean;
 v_caso uuid;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_solicitante is null or p_loja is null or p_caso is null
 or p_atribuicao_esperada is null or p_destino is null then
  raise exception 'MOVIMENTO_PARAMETROS_INVALIDOS' using errcode='22023';end if;

 -- Pré-leitura não bloqueante. O identificador imutável de atribuição
 -- será conferido NOVAMENTE após todos os locks.
 select a.operador_id into v_origem
 from public.atribuicoes_humanas a
 where a.id=p_atribuicao_esperada and a.caso_id=p_caso
   and a.concessionaria_id=p_loja and a.encerrada_em is null;
 if v_origem is null then
  raise exception 'ATRIBUICAO_ESPERADA_NAO_ATIVA' using errcode='22023';end if;
 if v_origem=p_destino then
  raise exception 'DESTINO_IGUAL_ORIGEM' using errcode='22023';end if;

 -- Ordenação de locks evita gerente A tomar destino B enquanto gerente B
 -- segura origem A. Se uma pausa global detiver uma das linhas, aguardamos
 -- e verificamos novamente a elegibilidade após o commit.
 select count(*) into v_atores from (
  select e.ator_id from public.equipe_prumo_s1 e
  where e.ator_id in (p_solicitante,v_origem,p_destino)
  order by e.ator_id
  for share of e
 ) x;
 if v_atores<>3 then
  raise exception 'OPERADORES_NAO_CADASTRADOS' using errcode='42501';end if;

 -- Protege a identidade ativa do solicitante, e os vinculos de chefia
 -- de origem e destino contra UPDATE/DELETE concorrente. Sem essa trava,
 -- o gestor removido da equipe poderia concluir uma operacao com alçada
 -- lida antes da revogacao. Responsavel ativo usa linha propria.
 select exists(
  select 1 from prumo_private.s1_responsaveis_plataforma r
  where r.ator_id=p_solicitante and r.ativo
 ) into v_responsavel;
 if v_responsavel then
  perform 1 from prumo_private.s1_responsaveis_plataforma r
  where r.ator_id=p_solicitante and r.ativo
  for share of r;
  if not found then
   raise exception 'RESPONSAVEL_REVOGADO' using errcode='42501';end if;
 else
  select count(*) into v_chefias from (
   select g.operador_id from prumo_private.s1_gestor_operadores g
   where g.gestor_id=p_solicitante and g.encerrado_em is null
    and g.operador_id in (v_origem,p_destino)
   order by g.operador_id for share of g
  ) x;
  if v_chefias<>2 then
   raise exception 'GESTAO_EQUIPE_NAO_AUTORIZADA' using errcode='42501';end if;
 end if;

 if not prumo_private.s1_pode_administrar_operador(
   p_solicitante,p_loja,'mover_atendimento',v_origem)
 or not prumo_private.s1_pode_administrar_operador(
   p_solicitante,p_loja,'mover_atendimento',p_destino) then
  raise exception 'GESTAO_EQUIPE_NAO_AUTORIZADA' using errcode='42501';end if;

 -- Somente operador ATIVO com grant explícito da loja pode RECEBER.
 -- Só o RESPONSÁVEL altera esse grant; gerente não altera A/B/C.
 perform 1 from public.vinculos_papel_escopo v
 join public.concessionarias l on l.id=v.concessionaria_id
 join public.equipe_prumo_s1 e on e.ator_id=v.ator_id
 where v.ator_id=p_destino and v.concessionaria_id=p_loja
  and v.papel='operador' and e.estado='ativo' and l.ativo
  and v.valido_desde<=pg_catalog.statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
 limit 1 for share of v,l,e;
 if not found then
  raise exception 'DESTINO_SEM_ACESSO_OU_INATIVO' using errcode='23514';end if;

 -- Serializa alterações comerciais S0, atualizações humanas e a concorrência
 -- de outro gestor sobre o MESMO caso antes de mexer no titular.
 select h.id,h.motivo_simulado,c.status_comercial
 into v_caso,v_motivo,v_status
 from public.casos_humanos h
 join public.ciclos_comerciais c
  on c.id=h.ciclo_id and c.concessionaria_id=h.concessionaria_id
 where h.id=p_caso and h.concessionaria_id=p_loja
 for update of h,c;
 if v_caso is null then
  raise exception 'CASO_FORA_DA_LOJA' using errcode='22023';end if;
 if (v_status='vendido' and v_motivo is distinct from 'retorno_pos_venda')
  or (v_status='perdido' and v_motivo is distinct from 'revisao_humana') then
  raise exception 'CICLO_TERMINAL_SEM_NOVO_CASO' using errcode='23514';end if;

 select a.id,a.operador_id,a.atribuida_em into v_achado,v_origem,v_data
 from public.atribuicoes_humanas a
 where a.caso_id=p_caso and a.concessionaria_id=p_loja
   and a.encerrada_em is null
 for update of a;
 if v_achado is distinct from p_atribuicao_esperada then
  raise exception 'ATRIBUICAO_ESPERADA_DESATUALIZADA' using errcode='22023';end if;
 if not prumo_private.s1_pode_administrar_operador(
  p_solicitante,p_loja,'mover_atendimento',v_origem) then
  raise exception 'ORIGEM_SAIU_DA_EQUIPE' using errcode='42501';end if;
 update public.atribuicoes_humanas
 set encerrada_em=greatest(v_data,pg_catalog.statement_timestamp())
 where id=v_achado and encerrada_em is null;
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values(p_loja,p_caso,p_destino) returning id into v_nova;
 insert into prumo_private.s1_movimentos_manuais_historico(
  solicitante_id,concessionaria_id,caso_id,atribuicao_anterior_id,
  atribuicao_nova_id,operador_anterior,operador_novo)
 values(p_solicitante,p_loja,p_caso,v_achado,v_nova,v_origem,p_destino);
 -- Pendência anterior eventualmente obsoleta é corrigida pelo reconciliador I6:
 -- não travar fila antes do caso, evitando deadlock com consumidor de fila.
 return pg_catalog.jsonb_build_object(
  'outcome','MOVED','case_id',p_caso,'assignment_id',v_nova,
  'from_assignment_id',v_achado);
end $fn$;

revoke all on function
 prumo_private.s1_mover_atendimento_da_equipe(uuid,uuid,uuid,uuid,uuid)
 from public,anon,authenticated,service_role;
