-- I63 RLS CANDIDATE ONLY: consume canonical S0/S1/I61 exceptions.
-- Loaded in disposable PG17 or ephemeral GoTrue, NEVER as hosted migration.
-- No SELECT grant on private ledger, no DML expansion, no public PII view.
begin;
create schema prumo_s1_i63_test authorization postgres;
revoke all on schema prumo_s1_i63_test from public,anon,service_role;
grant usage on schema prumo_s1_i63_test to authenticated;

-- The owner (postgres) bypasses recursive table RLS. The caller is always
-- auth.uid() from real JWT, not an operator id supplied in function arguments.
create function prumo_s1_i63_test.contato_atual(p_loja uuid,p_lead uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
select p_loja is not null and p_lead is not null
 and (select auth.uid()) is not null
 and exists(select 1 from public.equipe_prumo_s1 actor
  where actor.ator_id=(select auth.uid()) and actor.estado='ativo')
 and exists(select 1 from public.concessionarias loja
  where loja.id=p_loja and loja.ativo)
 and exists(
  select 1 from public.casos_humanos h
  join public.atribuicoes_humanas a
   on a.concessionaria_id=h.concessionaria_id
   and a.caso_id=h.id and a.encerrada_em is null
  where h.concessionaria_id=p_loja and h.lead_id=p_lead
    and a.operador_id=(select auth.uid())
    and (
     exists(select 1 from public.vinculos_papel_escopo v
       where v.ator_id=a.operador_id and v.concessionaria_id=p_loja
       and v.papel='operador'
       and v.valido_desde<=pg_catalog.clock_timestamp()
       and (v.valido_ate is null or v.valido_ate>pg_catalog.clock_timestamp()))
     or exists(select 1 from prumo_private.s1_excecoes_caso_i61 x
       join public.equipe_prumo_s1 mgr
        on mgr.ator_id=x.gestor_id and mgr.estado='ativo'
       join prumo_private.s1_gestor_operadores rel
        on rel.gestor_id=x.gestor_id and rel.operador_id=x.operador_id
        and rel.encerrado_em is null
       where x.atribuicao_id=a.id and x.caso_id=h.id
        and x.concessionaria_id=p_loja and x.operador_id=a.operador_id
        and x.revogada_em is null)
    )
 );
$fn$;

create function prumo_s1_i63_test.gestor_participante(
 p_loja uuid,p_caso uuid,p_operador uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
select p_loja is not null and p_caso is not null and p_operador is not null
 and (select auth.uid()) is not null
 and exists(select 1 from public.equipe_prumo_s1 mgr
  where mgr.ator_id=(select auth.uid()) and mgr.estado='ativo')
 and exists(select 1 from public.concessionarias loja
  where loja.id=p_loja and loja.ativo)
 and exists(select 1 from prumo_private.s1_gestor_operadores rel
  join public.equipe_prumo_s1 op
   on op.ator_id=rel.operador_id and op.estado='ativo'
  where rel.gestor_id=(select auth.uid()) and rel.operador_id=p_operador
   and rel.encerrado_em is null)
 and exists(select 1 from public.atribuicoes_humanas a
  where a.concessionaria_id=p_loja and a.caso_id=p_caso
  and a.operador_id=p_operador);
$fn$;

create function prumo_s1_i63_test.caso(
 p_loja uuid,p_caso uuid,p_lead uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_caso is not null and p_lead is not null
 and exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.id=p_caso and h.lead_id=p_lead)
 and (prumo_s1_i63_test.contato_atual(p_loja,p_lead)
  or exists(select 1 from public.atribuicoes_humanas a
    where a.concessionaria_id=p_loja and a.caso_id=p_caso
      and prumo_s1_i63_test.gestor_participante(p_loja,p_caso,a.operador_id)));
$fn$;

create function prumo_s1_i63_test.contato_com_caso(
 p_loja uuid,p_lead uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_lead is not null and
 exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.lead_id=p_lead
  and prumo_s1_i63_test.caso(p_loja,h.id,h.lead_id));
$fn$;

create function prumo_s1_i63_test.atribuicao(
 p_loja uuid,p_caso uuid,p_operador uuid,p_fim timestamptz)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_caso is not null and p_operador is not null
 and (
  prumo_s1_i63_test.gestor_participante(p_loja,p_caso,p_operador)
  or (
   p_operador=(select auth.uid()) and p_fim is null
   and exists(select 1 from public.atribuicoes_humanas a
    join public.casos_humanos h
     on h.concessionaria_id=a.concessionaria_id and h.id=a.caso_id
    where a.concessionaria_id=p_loja and a.caso_id=p_caso
     and a.operador_id=p_operador and a.encerrada_em is null
     and prumo_s1_i63_test.contato_atual(p_loja,h.lead_id))
  )
 );
$fn$;

create function prumo_s1_i63_test.conversa(
 p_loja uuid,p_conversa uuid,p_lead uuid,p_caso uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_conversa is not null and p_lead is not null
 and exists(select 1 from public.conversas co
  where co.concessionaria_id=p_loja and co.id=p_conversa
    and co.lead_id=p_lead and co.caso_id is not distinct from p_caso
    and (
      (p_caso is not null and
       prumo_s1_i63_test.caso(p_loja,p_caso,p_lead))
      or (p_caso is null and
       prumo_s1_i63_test.contato_com_caso(p_loja,p_lead))
    ));
$fn$;

create function prumo_s1_i63_test.mensagem(
 p_loja uuid,p_conversa uuid,p_canal uuid,p_caso uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_conversa is not null and p_canal is not null
 and exists(select 1 from public.conversas co
  where co.concessionaria_id=p_loja and co.id=p_conversa
   and co.canal_id=p_canal and co.caso_id is not distinct from p_caso
   and prumo_s1_i63_test.conversa(p_loja,co.id,co.lead_id,co.caso_id));
$fn$;

revoke all on function
 prumo_s1_i63_test.contato_atual(uuid,uuid),
 prumo_s1_i63_test.gestor_participante(uuid,uuid,uuid),
 prumo_s1_i63_test.caso(uuid,uuid,uuid),
 prumo_s1_i63_test.contato_com_caso(uuid,uuid),
 prumo_s1_i63_test.atribuicao(uuid,uuid,uuid,timestamptz),
 prumo_s1_i63_test.conversa(uuid,uuid,uuid,uuid),
 prumo_s1_i63_test.mensagem(uuid,uuid,uuid,uuid)
 from public,anon,service_role;
grant execute on function
 prumo_s1_i63_test.contato_atual(uuid,uuid),
 prumo_s1_i63_test.gestor_participante(uuid,uuid,uuid),
 prumo_s1_i63_test.caso(uuid,uuid,uuid),
 prumo_s1_i63_test.contato_com_caso(uuid,uuid),
 prumo_s1_i63_test.atribuicao(uuid,uuid,uuid,timestamptz),
 prumo_s1_i63_test.conversa(uuid,uuid,uuid,uuid),
 prumo_s1_i63_test.mensagem(uuid,uuid,uuid,uuid) to authenticated;

-- Each table gets exactly ONE permissive union with existing S0 policies and
-- ONE restrictive boundary that cannot be neutralized by S0's broad grants.
create policy s1_63_canon_casos_p on public.casos_humanos
 for select to authenticated using(
 prumo_s1_i63_test.caso(concessionaria_id,id,lead_id));
create policy s1_63_canon_casos_r on public.casos_humanos as restrictive
 for select to authenticated using(
 prumo_s1_i63_test.caso(concessionaria_id,id,lead_id));

create policy s1_63_canon_atr_p on public.atribuicoes_humanas
 for select to authenticated using(
 prumo_s1_i63_test.atribuicao(concessionaria_id,caso_id,operador_id,encerrada_em));
create policy s1_63_canon_atr_r on public.atribuicoes_humanas as restrictive
 for select to authenticated using(
 prumo_s1_i63_test.atribuicao(concessionaria_id,caso_id,operador_id,encerrada_em));

create policy s1_63_canon_conv_p on public.conversas
 for select to authenticated using(
 prumo_s1_i63_test.conversa(concessionaria_id,id,lead_id,caso_id));
create policy s1_63_canon_conv_r on public.conversas as restrictive
 for select to authenticated using(
 prumo_s1_i63_test.conversa(concessionaria_id,id,lead_id,caso_id));

create policy s1_63_canon_msg_p on public.mensagens
 for select to authenticated using(
 prumo_s1_i63_test.mensagem(concessionaria_id,conversa_id,canal_id,caso_id));
create policy s1_63_canon_msg_r on public.mensagens as restrictive
 for select to authenticated using(
 prumo_s1_i63_test.mensagem(concessionaria_id,conversa_id,canal_id,caso_id));

do $gate$ begin
 if (select count(*) from pg_catalog.pg_policies
  where schemaname='public' and policyname like 's1_63_canon_%')<>8
 or has_table_privilege('authenticated','prumo_private.s1_excecoes_caso_i61','SELECT')
 or has_table_privilege('authenticated','prumo_private.s1_excecoes_caso_eventos_i61','SELECT')
 or has_function_privilege('anon','prumo_s1_i63_test.caso(uuid,uuid,uuid)','EXECUTE')
 then raise exception 'I63_CANDIDATE_ACL_INVALID' using errcode='42501';end if;
end $gate$;
commit;
