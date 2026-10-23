-- I50 [T] only: disposable GoTrue/PostgREST stack after I49.
-- This is a distinct S0-SHAPED CAS mock; never install as operational S1.
create schema prumo_s1_i50_test authorization postgres;
revoke all on schema prumo_s1_i50_test from public,anon,authenticated,service_role;
create function prumo_s1_i50_test.assumir_versao_mock(
 p_loja uuid,p_lead uuid,p_ciclo uuid,p_caso uuid,p_gestor uuid,p_versao bigint
) returns text language plpgsql security invoker set search_path='' as $fn$
declare v_fila record;
begin
 if current_user<>'postgres' then
  raise exception 'I50_INTERNAL_ONLY' using errcode='42501';
 end if;
 if p_loja is null or p_lead is null or p_ciclo is null
 or p_caso is null or p_gestor is null or p_versao is null or p_versao<1
 then raise exception 'I50_INVALID_ARGS' using errcode='22023';end if;

 -- Same S0 lead row is the single serialization point for this fixture.
 -- This may block while a separate transaction revokes an actor's grants.
 perform 1 from public.leads_loja l
 where l.concessionaria_id=p_loja and l.id=p_lead for update;
 if not found then return 'REJECTED_SCOPE';end if;

 -- AFTER lock acquisition, recheck live identity and store authorization.
 -- The test specifically revokes either attribute while claimant is blocked.
 if not exists(select 1 from public.equipe_prumo_s1 e
  where e.ator_id=p_gestor and e.estado='ativo')
 or not exists(select 1 from public.vinculos_papel_escopo v
  where v.ator_id=p_gestor and v.concessionaria_id=p_loja
  and v.papel='gestor' and v.valido_desde<=pg_catalog.statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp()))
 or not exists(select 1 from public.concessionarias loja
  where loja.id=p_loja and loja.ativo)
 then return 'REJECTED_SCOPE';end if;

 select q.estado,q.versao into v_fila
 from prumo_s1_i49_test.s0_fila_sem_titular_mock q
 where q.concessionaria_id=p_loja and q.lead_id=p_lead
 and q.ciclo_id=p_ciclo for update;
 if not found then return 'NOT_IN_QUEUE';end if;
 if v_fila.estado<>'pendente' then return 'ALREADY_CLAIMED';end if;
 if v_fila.versao<>p_versao then return 'CONFLICT_VERSION';end if;
 if exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.lead_id=p_lead)
 then return 'ALREADY_CLAIMED';end if;

 -- Exactly one new owner and a monotonic queue revision in this mock.
 insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 values(p_caso,p_loja,p_lead,p_ciclo);
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values(p_loja,p_caso,p_gestor);
 update prumo_s1_i49_test.s0_fila_sem_titular_mock
 set estado='resolvido',versao=versao+1
 where concessionaria_id=p_loja and lead_id=p_lead and ciclo_id=p_ciclo
 and versao=p_versao and estado='pendente';
 if not found then raise exception 'I50_LOST_CAS' using errcode='40001';end if;
 return 'APPLIED';
end $fn$;
revoke all on function
 prumo_s1_i50_test.assumir_versao_mock(uuid,uuid,uuid,uuid,uuid,bigint)
 from public,anon,authenticated,service_role;
notify pgrst, 'reload schema';
