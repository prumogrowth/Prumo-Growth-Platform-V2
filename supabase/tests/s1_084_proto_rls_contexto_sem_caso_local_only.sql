-- I60 RLS CANDIDATE ONLY: PG17 rollback / disposable GoTrue.
-- Case-less history may be read ONLY with current entitlement to a REAL case
-- of the SAME lead and store. Never promote this fixture to hosted Supabase.
create schema prumo_s1_i60_test authorization postgres;
create function prumo_s1_i60_test.contato(p_loja uuid,p_lead uuid)
returns boolean language sql stable security definer set search_path='' as $f$
 select p_loja is not null and p_lead is not null
 and (select auth.uid()) is not null
 and exists(select 1 from public.concessionarias l
  where l.id=p_loja and l.ativo)
 and exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.lead_id=p_lead
   and (prumo_s1_i41_test.pode_ler_caso(p_loja,h.id,h.lead_id)
    or prumo_s1_i42_test.historico_autorizado(p_loja,p_lead)));
$f$;
create function prumo_s1_i60_test.conversa(p_loja uuid,p_conversa uuid,p_lead uuid)
returns boolean language sql stable security definer set search_path='' as $f$
 select p_loja is not null and p_conversa is not null and p_lead is not null
 and exists(select 1 from public.conversas co
  where co.concessionaria_id=p_loja and co.id=p_conversa
  and co.lead_id=p_lead and co.caso_id is null
  and prumo_s1_i60_test.contato(p_loja,co.lead_id));
$f$;
create function prumo_s1_i60_test.mensagem(p_loja uuid,p_conversa uuid,p_caso uuid)
returns boolean language sql stable security definer set search_path='' as $f$
 select p_loja is not null and p_conversa is not null and p_caso is null
 and exists(select 1 from public.conversas co
  where co.concessionaria_id=p_loja and co.id=p_conversa
  and co.caso_id is null and prumo_s1_i60_test.contato(p_loja,co.lead_id));
$f$;
revoke all on schema prumo_s1_i60_test from public,anon,service_role;
grant usage on schema prumo_s1_i60_test to authenticated;
revoke all on function
 prumo_s1_i60_test.contato(uuid,uuid),
 prumo_s1_i60_test.conversa(uuid,uuid,uuid),
 prumo_s1_i60_test.mensagem(uuid,uuid,uuid)
 from public,anon,service_role;
grant execute on function
 prumo_s1_i60_test.contato(uuid,uuid),
 prumo_s1_i60_test.conversa(uuid,uuid,uuid),
 prumo_s1_i60_test.mensagem(uuid,uuid,uuid) to authenticated;

-- A single restrictive OR union: two separate restrictive policies would AND.
create policy s1_60_conversas_sem_caso_p on public.conversas
 for select to authenticated using (
 caso_id is null and prumo_s1_i60_test.conversa(concessionaria_id,id,lead_id));
drop policy s1_63_conversas_restrict on public.conversas;
create policy s1_60_conversas_restrict on public.conversas as restrictive
 for select to authenticated using (
  (caso_id is not null and
   (prumo_s1_i41_test.pode_ler_caso_id(concessionaria_id,caso_id)
    or prumo_s1_i42_test.caso_historico_autorizado(concessionaria_id,caso_id)))
  or (caso_id is null and
   prumo_s1_i60_test.conversa(concessionaria_id,id,lead_id)));
drop policy s1_63_mensagens_restrict on public.mensagens;
create policy s1_60_mensagens_restrict on public.mensagens as restrictive
 for select to authenticated using (
  (caso_id is not null and
   (prumo_s1_i41_test.pode_ler_mensagem(concessionaria_id,conversa_id,caso_id)
    or prumo_s1_i42_test.msg_historico_autorizado(concessionaria_id,conversa_id,caso_id)))
  or (caso_id is null and
   prumo_s1_i60_test.mensagem(concessionaria_id,conversa_id,caso_id)));
