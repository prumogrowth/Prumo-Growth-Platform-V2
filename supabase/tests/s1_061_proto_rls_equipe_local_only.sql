-- I43 shared fixture, PG17 disposable ONLY. Caller owns BEGIN/ROLLBACK.
-- Candidato unificado para S0/S1: atende caso exato da equipe OU
-- historia desse contato/loja se Consultor TITULAR ATUAL desse contato.
-- Definer bypassa RLS de atribuicoes/casos para evitar recursao de policies.
-- Fixture NÃO propoe bypass arbitrario em banco hospedado.
create schema prumo_s1_i41_test authorization postgres;
create function prumo_s1_i41_test.pode_ler_caso(p_loja uuid,p_caso uuid,p_lead uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_caso is not null and p_lead is not null
 and (select auth.uid()) is not null
 and exists(select 1 from public.equipe_prumo_s1 e
    where e.ator_id=(select auth.uid()) and e.estado='ativo')
 and (
  -- Consultor titular atual de algum caso do MESMO contato E loja.
  exists(
   select 1 from public.casos_humanos h
   join public.atribuicoes_humanas a on a.concessionaria_id=h.concessionaria_id
    and a.caso_id=h.id and a.encerrada_em is null
   join public.vinculos_papel_escopo v on v.ator_id=a.operador_id
    and v.concessionaria_id=p_loja and v.papel='operador'
    and v.valido_desde<=pg_catalog.statement_timestamp()
    and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
   where h.concessionaria_id=p_loja and h.lead_id=p_lead
    and a.operador_id=(select auth.uid())
  )
  or
  -- Gestor atual de Consultor que PARTICIPOU deste caso (inclusive passado).
  exists(
   select 1 from public.atribuicoes_humanas a
   join prumo_private.s1_gestor_operadores g
    on g.operador_id=a.operador_id and g.gestor_id=(select auth.uid())
    and g.encerrado_em is null
   where a.concessionaria_id=p_loja and a.caso_id=p_caso
  )
 );
$fn$;
create function prumo_s1_i41_test.pode_ler_caso_id(p_loja uuid,p_caso uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select exists(
  select 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.id=p_caso
    and prumo_s1_i41_test.pode_ler_caso(p_loja,p_caso,h.lead_id)
 );
$fn$;
create function prumo_s1_i41_test.pode_ler_atribuicao(
 p_loja uuid,p_caso uuid,p_operador uuid,p_fim timestamptz)
returns boolean language sql stable security definer set search_path='' as $fn$
 select (select auth.uid()) is not null
 and exists(select 1 from public.equipe_prumo_s1 e
    where e.ator_id=(select auth.uid()) and e.estado='ativo')
 and (
  (p_operador=(select auth.uid()) and p_fim is null
    and exists(select 1 from public.vinculos_papel_escopo v
     where v.ator_id=p_operador and v.concessionaria_id=p_loja
      and v.papel='operador' and v.valido_desde<=pg_catalog.statement_timestamp()
      and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())))
  or exists(select 1 from prumo_private.s1_gestor_operadores g
      where g.gestor_id=(select auth.uid())
        and g.operador_id=p_operador and g.encerrado_em is null)
 );
$fn$;
-- Mensagens obrigatoriamente relacionadas ao MESMO caso da conversa.
create function prumo_s1_i41_test.pode_ler_mensagem(
 p_loja uuid,p_conversa uuid,p_caso uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_conversa is not null and p_caso is not null
 and exists(
  select 1 from public.conversas c where c.id=p_conversa
    and c.concessionaria_id=p_loja and c.caso_id=p_caso
    and prumo_s1_i41_test.pode_ler_caso_id(p_loja,p_caso)
 );
$fn$;
revoke all on schema prumo_s1_i41_test from public,anon,service_role;
grant usage on schema prumo_s1_i41_test to authenticated;
revoke all on function prumo_s1_i41_test.pode_ler_caso(uuid,uuid,uuid),
 prumo_s1_i41_test.pode_ler_caso_id(uuid,uuid),
 prumo_s1_i41_test.pode_ler_atribuicao(uuid,uuid,uuid,timestamptz),
 prumo_s1_i41_test.pode_ler_mensagem(uuid,uuid,uuid)
 from public,anon,service_role;
grant execute on function prumo_s1_i41_test.pode_ler_caso(uuid,uuid,uuid),
 prumo_s1_i41_test.pode_ler_caso_id(uuid,uuid),
 prumo_s1_i41_test.pode_ler_atribuicao(uuid,uuid,uuid,timestamptz),
 prumo_s1_i41_test.pode_ler_mensagem(uuid,uuid,uuid) to authenticated;

-- Policies permissivas adicionais (gestor sem grant; historia do contato).
create policy s1_61_casos_p on public.casos_humanos
 for select to authenticated using(
 prumo_s1_i41_test.pode_ler_caso(concessionaria_id,id,lead_id));
create policy s1_61_conversas_p on public.conversas
 for select to authenticated using(
 caso_id is not null and prumo_s1_i41_test.pode_ler_caso_id(concessionaria_id,caso_id));
create policy s1_61_atribuicoes_p on public.atribuicoes_humanas
 for select to authenticated using(
 prumo_s1_i41_test.pode_ler_atribuicao(concessionaria_id,caso_id,operador_id,encerrada_em));

-- Restritivas neutralizam concessão demasiadamente ampla por loja da S0.
create policy s1_61_casos_r on public.casos_humanos as restrictive
 for select to authenticated using(
 prumo_s1_i41_test.pode_ler_caso(concessionaria_id,id,lead_id));
create policy s1_61_conversas_r on public.conversas as restrictive
 for select to authenticated using(
 caso_id is not null and prumo_s1_i41_test.pode_ler_caso_id(concessionaria_id,caso_id));
create policy s1_61_atribuicoes_r on public.atribuicoes_humanas as restrictive
 for select to authenticated using(
 prumo_s1_i41_test.pode_ler_atribuicao(concessionaria_id,caso_id,operador_id,encerrada_em));
create policy s1_61_mensagens_r on public.mensagens as restrictive
 for select to authenticated using(
 prumo_s1_i41_test.pode_ler_mensagem(concessionaria_id,conversa_id,caso_id));
