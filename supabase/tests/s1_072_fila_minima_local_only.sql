-- I49 [T/P] ONLY in disposable I44 GoTrue CI, never a production migration.
-- Explicit mock S0 queue event: absence of a case alone is NOT sufficient proof.
create schema prumo_s1_i49_test authorization postgres;
create table prumo_s1_i49_test.s0_fila_sem_titular_mock (
 concessionaria_id uuid not null,
 lead_id uuid not null,
 ciclo_id uuid not null,
 estado text not null default 'pendente' check(estado in ('pendente','resolvido')),
 versao bigint not null default 1 check(versao>0),
 primary key(concessionaria_id,lead_id,ciclo_id),
 foreign key(concessionaria_id,ciclo_id,lead_id)
 references public.ciclos_comerciais(concessionaria_id,id,lead_id)
);
revoke all on schema prumo_s1_i49_test from public,anon,authenticated,service_role;
revoke all on prumo_s1_i49_test.s0_fila_sem_titular_mock
 from public,anon,authenticated,service_role;

-- Minimal projection: store and opaque lead/cycle IDs only. No telephone,
-- message, case, D3/D4 material or permission to claim/send. Laboratory-only
-- SECURITY DEFINER intentionally bypasses underlying I45 leads SELECT RLS
-- but applies its OWN explicit shop-manager+active-staff scope and S0 marker.
create function public.s1_i49_fila_resumo_mock(p_loja uuid)
returns table(concessionaria_id uuid,lead_id uuid,ciclo_id uuid)
language sql stable security definer set search_path='' as $fn$
 select q.concessionaria_id,q.lead_id,q.ciclo_id
 from prumo_s1_i49_test.s0_fila_sem_titular_mock q
 join public.concessionarias loja on loja.id=q.concessionaria_id and loja.ativo
 where q.concessionaria_id=p_loja and p_loja is not null and q.estado='pendente'
 and (select auth.uid()) is not null
 and exists(select 1 from public.equipe_prumo_s1 e
  where e.ator_id=(select auth.uid()) and e.estado='ativo')
 and exists(select 1 from public.vinculos_papel_escopo v
  where v.ator_id=(select auth.uid()) and v.concessionaria_id=p_loja
  and v.papel='gestor' and v.valido_desde<=pg_catalog.statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp()))
 and not exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=q.concessionaria_id and h.lead_id=q.lead_id);
$fn$;
revoke all on function public.s1_i49_fila_resumo_mock(uuid)
 from public,anon,authenticated,service_role;
grant execute on function public.s1_i49_fila_resumo_mock(uuid) to authenticated;

-- A privileged S0-shaped CLAIM MOCK, *not* an exposed RPC or an S1 product
-- operation. A trusted postgres executor alone supplies actor parameters.
-- Serializes on S0 lead row; the second contender rechecks after first commit.
create function prumo_s1_i49_test.assumir_mock(
 p_loja uuid,p_lead uuid,p_ciclo uuid,p_caso uuid,p_gestor uuid
) returns text language plpgsql security invoker set search_path='' as $fn$
begin
 if current_user<>'postgres' then
  raise exception 'I49_INTERNAL_ONLY' using errcode='42501';
 end if;
 if p_loja is null or p_lead is null or p_ciclo is null
    or p_caso is null or p_gestor is null then
  raise exception 'I49_INVALID_ARGS' using errcode='22023';
 end if;
 perform 1 from public.leads_loja l
 where l.concessionaria_id=p_loja and l.id=p_lead for update;
 if not found then return 'REJECTED_SCOPE'; end if;
 if exists(select 1 from public.casos_humanos h
    where h.concessionaria_id=p_loja and h.lead_id=p_lead)
 then return 'ALREADY_CLAIMED'; end if;
 if not exists(select 1 from prumo_s1_i49_test.s0_fila_sem_titular_mock q
   where q.concessionaria_id=p_loja and q.lead_id=p_lead
   and q.ciclo_id=p_ciclo and q.estado='pendente')
 or not exists(select 1 from public.concessionarias c
   where c.id=p_loja and c.ativo)
 or not exists(select 1 from public.equipe_prumo_s1 e
   where e.ator_id=p_gestor and e.estado='ativo')
 or not exists(select 1 from public.vinculos_papel_escopo v
   where v.ator_id=p_gestor and v.concessionaria_id=p_loja
   and v.papel='gestor' and v.valido_desde<=pg_catalog.statement_timestamp()
   and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
 then return 'REJECTED_SCOPE'; end if;
 -- Time window makes two independent psql sessions overlap in CI.
 perform pg_catalog.pg_sleep(0.4);
 insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 values(p_caso,p_loja,p_lead,p_ciclo);
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values(p_loja,p_caso,p_gestor);
 update prumo_s1_i49_test.s0_fila_sem_titular_mock
 set estado='resolvido',versao=versao+1
 where concessionaria_id=p_loja and lead_id=p_lead and ciclo_id=p_ciclo;
 return 'APPLIED';
end $fn$;
revoke all on function prumo_s1_i49_test.assumir_mock(uuid,uuid,uuid,uuid,uuid)
 from public,anon,authenticated,service_role;
notify pgrst, 'reload schema';
