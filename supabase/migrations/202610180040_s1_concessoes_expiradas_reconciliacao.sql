-- S1-002/I3: reparacao de concessoes que expiraram PELO RELOGIO
-- Sem cron/worker e sem acesso REST; execucao interna controlada em PG descartavel.
-- Nao altera estados comerciais nem mensagens e nao aplica no Supabase hospedado.
create function prumo_private.s1_reconciliar_elegibilidade_vencida(p_max_grupos integer default 50)
returns jsonb language plpgsql security invoker set search_path='' as $s1$
declare r record; v_motivo text; v_casos integer:=0; v_grupos integer:=0;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';
 end if;
 if p_max_grupos is null or p_max_grupos not between 1 and 100 then
  raise exception 'INVALID_RECONCILE_BATCH' using errcode='22023';
 end if;
 -- Agrupamento deterministico; casos individuais sao travados dentro do I2.
 -- Nenhuma filtragem por status no reparo de atribuicoes stale:
 -- I2 encerra vinculo residual de ciclos terminais, sem novo titular.
 for r in
  select distinct a.concessionaria_id,a.operador_id
  from public.atribuicoes_humanas a
  where a.encerrada_em is null
   and (
    not exists(select 1 from public.equipe_prumo_s1 e
     where e.ator_id=a.operador_id and e.estado='ativo')
    or not exists(
     select 1 from public.vinculos_papel_escopo v
     join public.concessionarias l on l.id=v.concessionaria_id
     where v.ator_id=a.operador_id and v.concessionaria_id=a.concessionaria_id
       and v.papel in ('gestor','operador') and l.ativo
       and v.valido_desde<=pg_catalog.statement_timestamp()
       and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
    )
   )
  order by a.concessionaria_id,a.operador_id
  limit p_max_grupos
 loop
  -- A transacao pode ter esperado por outro remanejamento: o segundo
  -- executor continua idempotente porque I2 so move atribuicoes ativas.
  if exists(select 1 from public.equipe_prumo_s1 e
    where e.ator_id=r.operador_id and e.estado='ativo') then
   v_motivo:='ESCOPO_REVOGADO';
  else
   v_motivo:='EQUIPE_INATIVA';
  end if;
  v_casos:=v_casos+prumo_private.s1_remanejar_ator(
   r.operador_id,r.concessionaria_id,v_motivo);
  v_grupos:=v_grupos+1;
 end loop;
 return pg_catalog.jsonb_build_object(
  'outcome','RECONCILED','groups_checked',v_grupos,
  'cases_reassigned_or_closed',v_casos);
end $s1$;
revoke all on function prumo_private.s1_reconciliar_elegibilidade_vencida(integer)
 from public,anon,authenticated,service_role;
