-- S1-002 I45 [P/T] exclusivamente em Supabase CLI descartavel, NAO MIGRATION.
-- Base S0 001..005 + I43/I44. A S0 deve homologar owners e predicates.
create schema prumo_s1_i45_test authorization postgres;
create function prumo_s1_i45_test.pode_ler_lead(p_loja uuid,p_lead uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_lead is not null and (select auth.uid()) is not null
 and exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.lead_id=p_lead
  and (prumo_s1_i41_test.pode_ler_caso(h.concessionaria_id,h.id,h.lead_id)
    or prumo_s1_i42_test.historico_autorizado(h.concessionaria_id,h.lead_id)));
$fn$;
create function prumo_s1_i45_test.pode_ler_ciclo(p_loja uuid,p_ciclo uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_ciclo is not null and (select auth.uid()) is not null
 and exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.ciclo_id=p_ciclo
  and (prumo_s1_i41_test.pode_ler_caso(h.concessionaria_id,h.id,h.lead_id)
    or prumo_s1_i42_test.historico_autorizado(h.concessionaria_id,h.lead_id)));
$fn$;
revoke all on schema prumo_s1_i45_test from public,anon,service_role;
grant usage on schema prumo_s1_i45_test to authenticated;
revoke all on function prumo_s1_i45_test.pode_ler_lead(uuid,uuid),
 prumo_s1_i45_test.pode_ler_ciclo(uuid,uuid) from public,anon,service_role;
grant execute on function prumo_s1_i45_test.pode_ler_lead(uuid,uuid),
 prumo_s1_i45_test.pode_ler_ciclo(uuid,uuid) to authenticated;
-- AND restritivo corrige OR historico por loja; policy permissiva
-- permite supervisor da propria equipe SEM concessionaria concedida.
-- Lead sem caso fica fechado: fila sem titular demanda projecao S0 separada.
create policy s1_65_leads_contexto_p on public.leads_loja for select to authenticated
 using(prumo_s1_i45_test.pode_ler_lead(concessionaria_id,id));
create policy s1_65_leads_contexto_r on public.leads_loja as restrictive
 for select to authenticated using(prumo_s1_i45_test.pode_ler_lead(concessionaria_id,id));
create policy s1_65_ciclos_contexto_p on public.ciclos_comerciais for select to authenticated
 using(prumo_s1_i45_test.pode_ler_ciclo(concessionaria_id,id));
create policy s1_65_ciclos_contexto_r on public.ciclos_comerciais as restrictive
 for select to authenticated using(prumo_s1_i45_test.pode_ler_ciclo(concessionaria_id,id));
notify pgrst, 'reload schema';
