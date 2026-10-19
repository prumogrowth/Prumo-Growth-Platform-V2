-- S1-002/I12: comando privado de remanejamento MANUAL por gestor de EQUIPE.
-- Apenas PostgreSQL 17 sintético. NÃO é endpoint nem ação autenticada real.
-- Não cria/apaga funcionário, não modifica grants de concessionária, não
-- altera status comercial, Meta, OpenAI ou frontend.
create table prumo_private.s1_movimentos_manuais_historico(
 id bigint generated always as identity primary key,
 solicitante_id uuid not null references public.atores(id),
 concessionaria_id uuid not null,
 caso_id uuid not null,
 atribuicao_anterior_id uuid not null unique references public.atribuicoes_humanas(id),
 atribuicao_nova_id uuid not null unique references public.atribuicoes_humanas(id),
 operador_anterior uuid not null references public.atores(id),
 operador_novo uuid not null references public.atores(id),
 realizado_em timestamptz not null default pg_catalog.statement_timestamp(),
 foreign key(concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id),
 check(operador_anterior<>operador_novo)
);
create index s1_movimentos_manuais_por_equipe
 on prumo_private.s1_movimentos_manuais_historico(solicitante_id,realizado_em);
alter table prumo_private.s1_movimentos_manuais_historico enable row level security;
revoke all on prumo_private.s1_movimentos_manuais_historico
 from public,anon,authenticated,service_role;
revoke all on sequence prumo_private.s1_movimentos_manuais_historico_id_seq
 from public,anon,authenticated,service_role;
create trigger s1_hist_manual_no_mutation
 before update or delete on prumo_private.s1_movimentos_manuais_historico
 for each row execute function prumo_private.s1_proibir_alteracao_historico();
create trigger s1_hist_manual_no_truncate
 before truncate on prumo_private.s1_movimentos_manuais_historico
 for each statement execute function prumo_private.s1_proibir_alteracao_historico();

-- O id exato da atribuicao anterior é obrigatório: reenvio/duplo clique
-- nunca pode reverter uma transferência feita com sucesso ("ABA").
-- Dois atores precisam estar aptos na MESMA concessionária do caso,
-- gestor deve ser chefe de AMBOS; responsável da plataforma é alternativo.
-- Fluxo trava equipe antes de caso/atribuição, reduzindo inversão de locks
-- com o gatilho de suspensão global (equipe primeiro, depois carteira).
create function prumo_private.s1_mover_atendimento_da_equipe(
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
  where e.ator_id in (v_origem,p_destino)
  order by e.ator_id
  for share of e
 ) x;
 if v_atores<>2 then
  raise exception 'OPERADORES_NAO_CADASTRADOS' using errcode='42501';end if;

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
 set encerrada_em=pg_catalog.greatest(v_data,pg_catalog.statement_timestamp())
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
