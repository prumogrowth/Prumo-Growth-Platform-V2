-- S1-002/I7: varredura justa de pendencias e lotes finitos no PG17 descartavel.
-- Sem scheduler, GoTrue, elevacao de privilegios ou mudancas em status comerciais.
-- Rotaciona itens sem elegivel; a ordem de chegada e preservada na primeira passagem.
alter table prumo_private.s1_remanejamento_pendencias
 add column ultima_inspecao_em timestamptz;
create index s1_pendencias_varredura_prioridade
 on prumo_private.s1_remanejamento_pendencias(concessionaria_id,ultima_inspecao_em,registrado_em,caso_id);

create or replace function prumo_private.s1_recuperar_fila_protegida(
 p_loja uuid, p_max_casos integer default 25)
returns jsonb language plpgsql security invoker set search_path='' as $s1$
declare
 p record;
 v_status text;
 v_destino uuid;
 v_atribuido integer:=0;
 v_ja_atribuido integer:=0;
 v_terminal integer:=0;
 v_sem_elegivel integer:=0;
 v_inspecionado integer:=0;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';
 end if;
 if p_loja is null or p_max_casos is null or p_max_casos not between 1 and 50 then
  raise exception 'INVALID_RECOVERY_INPUT' using errcode='22023';
 end if;
 -- Registros pendentes travados para impedir dois consumidores do mesmo caso.
 for p in
  select q.concessionaria_id,q.caso_id,q.operador_anterior,q.registrado_em
  from prumo_private.s1_remanejamento_pendencias q
  where q.concessionaria_id=p_loja
  order by q.ultima_inspecao_em nulls first,q.registrado_em,q.caso_id
  limit p_max_casos
  for update of q skip locked
 loop
  v_inspecionado:=v_inspecionado+1;
  -- Bloqueio do caso torna concorrente a criacao de outra atribuicao:
  -- INSERT de atribuicoes referencia o caso via FK e aguarda este row lock.
  select c.status_comercial into v_status
  from public.casos_humanos h
  join public.ciclos_comerciais c
   on c.id=h.ciclo_id and c.concessionaria_id=h.concessionaria_id
  where h.id=p.caso_id and h.concessionaria_id=p.concessionaria_id
  for update of h;
  if exists(
   select 1 from public.atribuicoes_humanas a
   where a.caso_id=p.caso_id and a.concessionaria_id=p.concessionaria_id
    and a.encerrada_em is null
  ) then
   delete from prumo_private.s1_remanejamento_pendencias q
    where q.caso_id=p.caso_id and q.concessionaria_id=p.concessionaria_id;
   insert into prumo_private.s1_recuperacao_fila_historico(
    concessionaria_id,caso_id,operador_anterior,resultado,pendencia_criada_em)
   values(p.concessionaria_id,p.caso_id,p.operador_anterior,'JA_ATRIBUIDO',
    p.registrado_em);
   v_ja_atribuido:=v_ja_atribuido+1;
   continue;
  end if;
  if v_status in ('vendido','perdido') then
   delete from prumo_private.s1_remanejamento_pendencias q
    where q.caso_id=p.caso_id and q.concessionaria_id=p.concessionaria_id;
   insert into prumo_private.s1_recuperacao_fila_historico(
    concessionaria_id,caso_id,operador_anterior,resultado,pendencia_criada_em)
   values(p.concessionaria_id,p.caso_id,p.operador_anterior,'TERMINAL',
    p.registrado_em);
   v_terminal:=v_terminal+1;
   continue;
  end if;
  v_destino:=null;
  select v.ator_id into v_destino
  from public.vinculos_papel_escopo v
  join public.equipe_prumo_s1 e on e.ator_id=v.ator_id
  join public.concessionarias l on l.id=v.concessionaria_id
  where v.concessionaria_id=p.concessionaria_id
    and v.ator_id<>p.operador_anterior
    and v.papel='operador' and e.estado='ativo' and l.ativo
    and v.valido_desde<=pg_catalog.statement_timestamp()
    and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
  order by (
   select pg_catalog.count(*) from public.atribuicoes_humanas a
    where a.operador_id=v.ator_id and a.concessionaria_id=p.concessionaria_id
     and a.encerrada_em is null),v.ator_id
  limit 1 for share of e,v,l skip locked;
  if v_destino is null then
   -- Rotaciona pendencias sem substituto para nao bloquear os itens posteriores.
   update prumo_private.s1_remanejamento_pendencias q
     set ultima_inspecao_em=pg_catalog.clock_timestamp()
    where q.concessionaria_id=p.concessionaria_id and q.caso_id=p.caso_id;
   v_sem_elegivel:=v_sem_elegivel+1;
   continue;
  end if;
  -- Aplica o guard I2 (equipe e escopo) novamente no proprio INSERT.
  insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
  values(p.concessionaria_id,p.caso_id,v_destino);
  delete from prumo_private.s1_remanejamento_pendencias q
   where q.caso_id=p.caso_id and q.concessionaria_id=p.concessionaria_id;
  insert into prumo_private.s1_recuperacao_fila_historico(
   concessionaria_id,caso_id,operador_anterior,operador_novo,
   resultado,pendencia_criada_em)
  values(p.concessionaria_id,p.caso_id,p.operador_anterior,v_destino,
   'RECUPERADO',p.registrado_em);
  v_atribuido:=v_atribuido+1;
 end loop;
 return pg_catalog.jsonb_build_object(
  'outcome','PROCESSED','inspected',v_inspecionado,
  'reassigned',v_atribuido,'already_assigned',v_ja_atribuido,
  'terminal_closed',v_terminal,'still_protected',v_sem_elegivel);
end $s1$;

-- Entrada interna explicita para reconciliacao em parcelas finitas, com teto 250.
-- Os gatilhos de ativacao/concessao continuam limitados a 25 por evento.
create function prumo_private.s1_drenar_backlog_protegido(
 p_loja uuid, p_max_lotes integer default 4)
returns jsonb language plpgsql security invoker set search_path='' as $s1$
declare
 v_i integer;
 v_resultado jsonb;
 v_inspecionados integer:=0;
 v_recuperados integer:=0;
 v_existentes integer:=0;
 v_terminais integer:=0;
 v_sem_elegivel integer:=0;
 v_antes integer;
 v_depois integer;
 v_lotes integer:=0;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';
 end if;
 if p_loja is null or p_max_lotes is null or p_max_lotes not between 1 and 10 then
  raise exception 'INVALID_DRAIN_BOUNDS' using errcode='22023';
 end if;
 select count(*) into v_antes
  from prumo_private.s1_remanejamento_pendencias q
  where q.concessionaria_id=p_loja;
 for v_i in 1..p_max_lotes loop
  v_resultado:=prumo_private.s1_recuperar_fila_protegida(p_loja,25);
  exit when (v_resultado->>'inspected')::integer=0;
  v_lotes:=v_lotes+1;
  v_inspecionados:=v_inspecionados+(v_resultado->>'inspected')::integer;
  v_recuperados:=v_recuperados+(v_resultado->>'reassigned')::integer;
  v_existentes:=v_existentes+(v_resultado->>'already_assigned')::integer;
  v_terminais:=v_terminais+(v_resultado->>'terminal_closed')::integer;
  v_sem_elegivel:=v_sem_elegivel+(v_resultado->>'still_protected')::integer;
 end loop;
 select count(*) into v_depois
  from prumo_private.s1_remanejamento_pendencias q
  where q.concessionaria_id=p_loja;
 return pg_catalog.jsonb_build_object(
  'outcome',case when v_depois=0 then 'DRAINED' else 'STILL_PROTECTED' end,
  'pending_before',v_antes,'pending_after',v_depois,
  'batches_run',v_lotes,'inspected',v_inspecionados,
  'reassigned',v_recuperados,'already_assigned',v_existentes,
  'terminal_closed',v_terminais,'blocked_inspections',v_sem_elegivel);
end $s1$;
revoke all on function prumo_private.s1_drenar_backlog_protegido(uuid,integer)
 from public,anon,authenticated,service_role;
