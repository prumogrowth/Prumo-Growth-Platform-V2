-- I58: shared after-lock manager/store authority for signed LIST and S0 CLAIM.
-- Disposable PG17 only; no exposed RPC, session spoofing or historic rewrite.
begin;
create function prumo_private.s0_fila_exigir_gestor_i58(p_gestor uuid,p_loja uuid)
returns void language plpgsql security invoker set search_path='' as $verify$
begin
 if current_user<>'postgres' then
  raise exception 'S0_FILA_EXECUTOR_INTERNO' using errcode='42501';end if;
 if p_gestor is null or p_loja is null then
  raise exception 'S0_FILA_GESTOR_SEM_LOJA' using errcode='42501';end if;
 -- Lock without predicates that may turn false during a lock wait.
 perform 1 from public.equipe_prumo_s1 e
 where e.ator_id=p_gestor for share of e;
 if not found then raise exception 'S0_FILA_GESTOR_SEM_LOJA'
  using errcode='42501';end if;
 perform 1 from public.concessionarias l
 where l.id=p_loja for share of l;
 if not found then raise exception 'S0_FILA_GESTOR_SEM_LOJA'
  using errcode='42501';end if;
 perform 1 from public.vinculos_papel_escopo v
 where v.ator_id=p_gestor and v.concessionaria_id=p_loja
 and v.papel='gestor' order by v.valido_desde for share of v;
 if not found then raise exception 'S0_FILA_GESTOR_SEM_LOJA'
  using errcode='42501';end if;
 -- Separate SQL statement AFTER all locks, so both expired grants and
 -- suspensions that committed during a wait are re-read at the current time.
 if not exists(
  select 1 from public.equipe_prumo_s1 e
  join public.vinculos_papel_escopo v on v.ator_id=e.ator_id
  join public.concessionarias l on l.id=v.concessionaria_id
  where e.ator_id=p_gestor and e.estado='ativo'
   and v.concessionaria_id=p_loja and v.papel='gestor' and l.ativo
   and v.valido_desde<=pg_catalog.clock_timestamp()
   and (v.valido_ate is null or v.valido_ate>pg_catalog.clock_timestamp())
 ) then raise exception 'S0_FILA_GESTOR_SEM_LOJA' using errcode='42501';end if;
end $verify$;
revoke all on function prumo_private.s0_fila_exigir_gestor_i58(uuid,uuid)
 from public,anon,authenticated,service_role;

-- I54 transaction preserved; manager authority is now before stale CAS.
create or replace function prumo_private.s0_fila_assumir(
 p_gestor uuid,p_loja uuid,p_ciclo uuid,p_versao bigint)
returns jsonb language plpgsql security invoker set search_path='' as $f$
declare q record;v_caso uuid;v_atr uuid;
begin
 if current_user<>'postgres' then
  raise exception 'S0_FILA_EXECUTOR_INTERNO' using errcode='42501';end if;
 if p_gestor is null or p_loja is null or p_ciclo is null
  or p_versao is null or p_versao<1 then
  raise exception 'S0_FILA_PARAMETROS_INVALIDOS' using errcode='22023';end if;
 -- Versioned queue is an explicit S0 event, not a naked missing-case inference.
 select q0.lead_id into q from prumo_private.s0_fila_humana q0
  where q0.concessionaria_id=p_loja and q0.ciclo_id=p_ciclo;
 if not found then raise exception 'S0_FILA_NAO_EXISTE' using errcode='22023';end if;
 perform 1 from public.leads_loja l where l.concessionaria_id=p_loja
  and l.id=q.lead_id for update of l;
 if not found then raise exception 'S0_LEAD_NAO_EXISTE' using errcode='22023';end if;
 select f.* into q from prumo_private.s0_fila_humana f
  where f.concessionaria_id=p_loja and f.ciclo_id=p_ciclo for update of f;
 -- Canonical lead -> queue -> team/store/grant order; authorize before CAS.
 perform prumo_private.s0_fila_exigir_gestor_i58(p_gestor,p_loja);
 if q.estado<>'pendente' or q.versao<>p_versao then
  return pg_catalog.jsonb_build_object('outcome','CONFLICT');end if;
 -- I58 authorization already locked+refreshed BEFORE CAS response.
 -- A Gestor cannot claim to themselves if intake explicitly paused.
 -- The canonical I52 guard is also enforced on the assignment INSERT.
 if exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.lead_id=q.lead_id) then
  return pg_catalog.jsonb_build_object('outcome','ALREADY_HAS_CASE');
 end if;
 if not exists(select 1 from public.ciclos_comerciais c
  where c.concessionaria_id=p_loja and c.id=p_ciclo and c.lead_id=q.lead_id
  and c.status_comercial in
   ('em atendimento pelo operador','cadastro enviado ao operador'))
 then raise exception 'S0_FILA_SINAL_EXPIRADO' using errcode='23514';end if;
 insert into public.casos_humanos(concessionaria_id,lead_id,ciclo_id)
  values(p_loja,q.lead_id,p_ciclo) returning id into v_caso;
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
  values(p_loja,v_caso,p_gestor) returning id into v_atr;
 update prumo_private.s0_fila_humana set estado='atribuido',versao=versao+1,
  caso_id=v_caso,atribuicao_id=v_atr,atualizado_em=pg_catalog.statement_timestamp()
 where concessionaria_id=p_loja and ciclo_id=p_ciclo;
 insert into prumo_private.s0_fila_humana_eventos(
 concessionaria_id,lead_id,ciclo_id,versao_anterior,versao_nova,
 resultado,solicitante_id,operador_id,caso_id,atribuicao_id)
 values(p_loja,q.lead_id,p_ciclo,p_versao,p_versao+1,
 'ASSUMIDO',p_gestor,p_gestor,v_caso,v_atr);
 return pg_catalog.jsonb_build_object('outcome','CLAIMED_BY_MANAGER',
  'case_id',v_caso,'assignment_id',v_atr,'version',p_versao+1);
end $f$;
revoke all on function prumo_private.s0_fila_assumir(uuid,uuid,uuid,bigint)
 from public,anon,authenticated,service_role;
commit;
