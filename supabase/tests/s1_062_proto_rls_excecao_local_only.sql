-- I43 shared fixture, PG17 disposable ONLY. Caller owns BEGIN/ROLLBACK.
-- Candidato puramente local: o entitlement de caso atual abre somente
-- a leitura contextual do lead em MESMA loja, nunca outro lead ou loja.
create schema prumo_s1_i42_test authorization postgres;
create function prumo_s1_i42_test.historico_autorizado(
 p_loja uuid,p_lead uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_lead is not null and (select auth.uid()) is not null
 and exists (
  select 1 from public.casos_humanos h_cur
  join public.atribuicoes_humanas a
   on a.concessionaria_id=h_cur.concessionaria_id
    and a.caso_id=h_cur.id and a.encerrada_em is null
  join prumo_private.s1_excecoes_55 x on x.atribuicao_id=a.id
   and x.concessionaria_id=h_cur.concessionaria_id
   and x.caso_id=h_cur.id and x.operador_id=a.operador_id
   and x.revogada_em is null
  join public.equipe_prumo_s1 op on op.ator_id=a.operador_id
   and op.estado='ativo'
  join public.equipe_prumo_s1 mg on mg.ator_id=x.gestor_id
   and mg.estado='ativo'
  join prumo_private.s1_gestor_operadores go
   on go.gestor_id=x.gestor_id and go.operador_id=a.operador_id
    and go.encerrado_em is null
  join public.concessionarias l
   on l.id=h_cur.concessionaria_id and l.ativo
  where h_cur.concessionaria_id=p_loja and h_cur.lead_id=p_lead
   and a.operador_id=(select auth.uid())
 );
$fn$;
create function prumo_s1_i42_test.caso_historico_autorizado(
 p_loja uuid,p_caso uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.id=p_caso
   and prumo_s1_i42_test.historico_autorizado(p_loja,h.lead_id));
$fn$;
-- O gate de mensagens deve validar a pertença do corpo a conversa exata,
-- tanto para historico sem grant quanto para a excecao corrente.
create function prumo_s1_i42_test.msg_historico_autorizado(
 p_loja uuid,p_conversa uuid,p_caso uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_conversa is not null and p_caso is not null
 and exists (select 1 from public.conversas co
  where co.concessionaria_id=p_loja and co.id=p_conversa
   and co.caso_id=p_caso
   and prumo_s1_i42_test.historico_autorizado(p_loja,co.lead_id));
$fn$;
revoke all on schema prumo_s1_i42_test from public,anon,service_role;
grant usage on schema prumo_s1_i42_test to authenticated;
revoke all on function
 prumo_s1_i42_test.historico_autorizado(uuid,uuid),
 prumo_s1_i42_test.caso_historico_autorizado(uuid,uuid),
 prumo_s1_i42_test.msg_historico_autorizado(uuid,uuid,uuid)
 from public,anon,service_role;
grant execute on function
 prumo_s1_i42_test.historico_autorizado(uuid,uuid),
 prumo_s1_i42_test.caso_historico_autorizado(uuid,uuid),
 prumo_s1_i42_test.msg_historico_autorizado(uuid,uuid,uuid)
 to authenticated;

create policy s1_62_caso_historico on public.casos_humanos
 for select to authenticated using (
 prumo_s1_i42_test.historico_autorizado(concessionaria_id,lead_id));
create policy s1_62_conversa_historico on public.conversas
 for select to authenticated using (
 caso_id is not null
 and prumo_s1_i42_test.historico_autorizado(concessionaria_id,lead_id));
-- Revisor S0 precisa consolidar policies finais: I55 restritiva original
-- nao admitia historico. Aqui se substitui somente DENTRO do rollback.
drop policy s1_55_mensagens_restrict on public.mensagens;
create policy s1_62_mensagens_restrict on public.mensagens as restrictive
 for select to authenticated using (
 (
  exists(select 1 from public.vinculos_papel_escopo v
   where v.ator_id=(select auth.uid())
    and v.concessionaria_id=mensagens.concessionaria_id
    and v.papel in ('gestor','operador','responsavel')
    and v.valido_desde<=pg_catalog.statement_timestamp()
    and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp()))
 ) or (
  caso_id is not null
  and prumo_s1_i42_test.msg_historico_autorizado(
      concessionaria_id,conversa_id,caso_id)
 )
);
-- Visao de escopo minimo: contextualiza ciclo sem SELECT bruto dos demais.
-- Usa owner no LAB sob predicado JWT+excecao valido de cada contato.
create view public.s1_62_historico_contato_resumo with (security_barrier=true) as
 select h.concessionaria_id,h.id as caso_id,h.lead_id,h.ciclo_id,
        c.status_comercial,l.telefone_cliente_normalizado
 from public.casos_humanos h
 join public.ciclos_comerciais c
  on c.concessionaria_id=h.concessionaria_id and c.id=h.ciclo_id
 join public.leads_loja l
  on l.concessionaria_id=h.concessionaria_id and l.id=h.lead_id
 where prumo_s1_i42_test.historico_autorizado(h.concessionaria_id,h.lead_id);
revoke all on public.s1_62_historico_contato_resumo from public,anon,service_role;
grant select on public.s1_62_historico_contato_resumo to authenticated;
