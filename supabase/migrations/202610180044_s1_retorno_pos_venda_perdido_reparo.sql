-- S1-002/AUD-01 — Corrige falsos encerramentos do atendimento humano
-- posterior a venda/perda. Motivos sao do S0 (migracao 009), SEM mudar
-- status historico ou acrescentar novo status comercial.
-- Somente PostgreSQL descartavel, nunca Supabase hospedado.
-- Trava ciclo e caso durante a decisao de remanejamento/recuperacao.
-- Caso terminal original sem marcador segue regra legada.
-- Casos de retorno apos venda (retorno_pos_venda) e revisao humana apos
-- perdido (revisao_humana) preservam elegibilidade humana para C11.

create or replace function prumo_private.s1_remanejar_ator(p_ator uuid,p_loja uuid,p_motivo text)
returns integer language plpgsql security invoker set search_path='' as $fn$
declare a record; v_destino uuid; n integer:=0;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_ator is null or p_motivo not in ('EQUIPE_INATIVA','ESCOPO_REVOGADO')
 then raise exception 'INVALID_REASSIGN_INPUT' using errcode='22023';end if;
 for a in
  select x.id,x.atribuida_em,x.caso_id,x.concessionaria_id,c.status_comercial,h.motivo_simulado
  from public.atribuicoes_humanas x
  join public.casos_humanos h on h.id=x.caso_id and h.concessionaria_id=x.concessionaria_id
  join public.ciclos_comerciais c on c.id=h.ciclo_id and c.concessionaria_id=h.concessionaria_id
  where x.operador_id=p_ator and x.encerrada_em is null
   and (p_loja is null or x.concessionaria_id=p_loja)
  order by x.concessionaria_id,x.caso_id for update of x,h,c
 loop
  update public.atribuicoes_humanas set
   encerrada_em=greatest(a.atribuida_em,statement_timestamp())
   where id=a.id and encerrada_em is null;
  if (a.status_comercial='vendido' and a.motivo_simulado is distinct from 'retorno_pos_venda')
    or (a.status_comercial='perdido' and a.motivo_simulado is distinct from 'revisao_humana') then
   insert into prumo_private.s1_remanejamento_historico(
    concessionaria_id,caso_id,atribuicao_anterior_id,operador_anterior,motivo,resultado)
   values(a.concessionaria_id,a.caso_id,a.id,p_ator,p_motivo,'ENCERRADO_HISTORICO');
   n:=n+1;continue;
  end if;
  v_destino:=null;
  select v.ator_id into v_destino
  from public.vinculos_papel_escopo v
  join public.equipe_prumo_s1 e on e.ator_id=v.ator_id
  join public.concessionarias l on l.id=v.concessionaria_id
  where v.concessionaria_id=a.concessionaria_id and v.ator_id<>p_ator
   and v.papel='operador' and e.estado='ativo' and l.ativo
   and v.valido_desde<=statement_timestamp()
   and (v.valido_ate is null or v.valido_ate>statement_timestamp())
  order by (select count(*) from public.atribuicoes_humanas z
   where z.operador_id=v.ator_id and z.concessionaria_id=a.concessionaria_id
   and z.encerrada_em is null),v.ator_id
  limit 1 for share of e,v,l skip locked;
  if v_destino is null then
   insert into prumo_private.s1_remanejamento_pendencias(
    concessionaria_id,caso_id,operador_anterior,motivo)
   values(a.concessionaria_id,a.caso_id,p_ator,p_motivo)
   on conflict(concessionaria_id,caso_id) do update
   set operador_anterior=excluded.operador_anterior,motivo=excluded.motivo,
       registrado_em=statement_timestamp();
  else
   insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
   values(a.concessionaria_id,a.caso_id,v_destino);
   delete from prumo_private.s1_remanejamento_pendencias
   where concessionaria_id=a.concessionaria_id and caso_id=a.caso_id;
  end if;
  insert into prumo_private.s1_remanejamento_historico(
   concessionaria_id,caso_id,atribuicao_anterior_id,operador_anterior,
   operador_novo,resultado,motivo)
  values(a.concessionaria_id,a.caso_id,a.id,p_ator,v_destino,
   case when v_destino is null then 'FILA_PROTEGIDA' else 'REDISTRIBUIDO' end,p_motivo);
  n:=n+1;
 end loop;
 return n;
end $fn$;


create or replace function prumo_private.s1_recuperar_fila_protegida(
 p_loja uuid, p_max_casos integer default 25)
returns jsonb language plpgsql security invoker set search_path='' as $s1$
declare
 p record;
 v_status text;
 v_motivo text;
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
  select c.status_comercial,h.motivo_simulado into v_status,v_motivo
  from public.casos_humanos h
  join public.ciclos_comerciais c
   on c.id=h.ciclo_id and c.concessionaria_id=h.concessionaria_id
  where h.id=p.caso_id and h.concessionaria_id=p.concessionaria_id
  for update of h,c;
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
  if (v_status='vendido' and v_motivo is distinct from 'retorno_pos_venda')
    or (v_status='perdido' and v_motivo is distinct from 'revisao_humana') then
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
