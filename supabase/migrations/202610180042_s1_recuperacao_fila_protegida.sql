-- S1-002/I6: recuperar fila protegida quando aparece operador Prumo elegivel.
-- APENAS PostgreSQL descartavel: nao executar no Supabase hospedado.
-- Nenhuma atribuicao a gerente apenas supervisor; sem status comercial, Meta ou OpenAI.
create table prumo_private.s1_recuperacao_fila_historico (
 id bigint generated always as identity primary key,
 concessionaria_id uuid not null,
 caso_id uuid not null,
 operador_anterior uuid not null references public.atores(id),
 operador_novo uuid references public.atores(id),
 resultado text not null check (resultado in ('RECUPERADO','JA_ATRIBUIDO','TERMINAL')),
 pendencia_criada_em timestamptz not null,
 registrado_em timestamptz not null default pg_catalog.statement_timestamp(),
 foreign key(concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id),
 check ((resultado='RECUPERADO' and operador_novo is not null)
  or (resultado in ('JA_ATRIBUIDO','TERMINAL') and operador_novo is null))
);
create index s1_recuperacao_fila_historico_loja
 on prumo_private.s1_recuperacao_fila_historico(concessionaria_id,registrado_em);
alter table prumo_private.s1_recuperacao_fila_historico enable row level security;
revoke all on prumo_private.s1_recuperacao_fila_historico
 from public,anon,authenticated,service_role;
revoke all on sequence prumo_private.s1_recuperacao_fila_historico_id_seq
 from public,anon,authenticated,service_role;

-- p_loja obrigatorio: esta funcao NUNCA varre lojas arbitrarias automaticamente.
-- Um caso ja reatribuido por outro fluxo apenas fecha pendencia stale (sem novo dono).
-- Evita restaurar carteira ao antigo operador excluindo operador_anterior.
-- SKIP LOCKED preserva concorrencia com outras suspensoes ou recuperacoes.
create function prumo_private.s1_recuperar_fila_protegida(
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
  order by q.registrado_em,q.caso_id
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

-- Recuperar, com limite, quando operador Prumo fica ativo (seus grants ja existem).
create function prumo_private.s1_recuperar_apos_ativacao()
returns trigger language plpgsql security invoker set search_path='' as $s1$
declare r record;
begin
 if new.estado='ativo' and (tg_op='INSERT' or old.estado is distinct from new.estado) then
  for r in
   select distinct v.concessionaria_id
   from public.vinculos_papel_escopo v
   where v.ator_id=new.ator_id and v.papel='operador'
    and v.valido_desde<=pg_catalog.statement_timestamp()
    and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
   order by v.concessionaria_id
  loop
   perform prumo_private.s1_recuperar_fila_protegida(r.concessionaria_id,25);
  end loop;
 end if;
 return new;
end $s1$;
create trigger s1_recuperar_ativacao after insert or update of estado
 on public.equipe_prumo_s1 for each row
 execute function prumo_private.s1_recuperar_apos_ativacao();

-- Recuperar quando um escopo de operador e concedido/renovado.
create function prumo_private.s1_recuperar_apos_concessao()
returns trigger language plpgsql security invoker set search_path='' as $s1$
begin
 if new.papel='operador'
  and new.valido_desde<=pg_catalog.statement_timestamp()
  and (new.valido_ate is null or new.valido_ate>pg_catalog.statement_timestamp())
  and exists(select 1 from public.equipe_prumo_s1 e
   where e.ator_id=new.ator_id and e.estado='ativo')
  and exists(select 1 from prumo_private.s1_remanejamento_pendencias q
   where q.concessionaria_id=new.concessionaria_id)
 then
  perform prumo_private.s1_recuperar_fila_protegida(new.concessionaria_id,25);
 end if;
 return new;
end $s1$;
create trigger s1_recuperar_concessao after insert or update of
 ator_id,concessionaria_id,papel,valido_desde,valido_ate
 on public.vinculos_papel_escopo for each row
 execute function prumo_private.s1_recuperar_apos_concessao();
revoke all on function
 prumo_private.s1_recuperar_fila_protegida(uuid,integer),
 prumo_private.s1_recuperar_apos_ativacao(),
 prumo_private.s1_recuperar_apos_concessao()
 from public,anon,authenticated,service_role;
