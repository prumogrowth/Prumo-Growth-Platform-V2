-- S1-002 I48: only disposable I44 GoTrue lab; NOT a migration.
-- S0/016 store-grant SELECT must be narrowed by existing I45 case/lead context.
create policy s1_70_elegibilidade_p on public.evidencias_elegibilidade_sinteticas
 for select to authenticated using(prumo_s1_i45_test.pode_ler_lead(concessionaria_id,lead_id));
create policy s1_70_elegibilidade_r on public.evidencias_elegibilidade_sinteticas
 as restrictive for select to authenticated using(prumo_s1_i45_test.pode_ler_lead(concessionaria_id,lead_id));
create policy s1_70_supressao_p on public.supressoes_contato_sinteticas
 for select to authenticated using(prumo_s1_i45_test.pode_ler_lead(concessionaria_id,lead_id));
create policy s1_70_supressao_r on public.supressoes_contato_sinteticas
 as restrictive for select to authenticated using(prumo_s1_i45_test.pode_ler_lead(concessionaria_id,lead_id));
create policy s1_70_elegibilidade_gate on public.evidencias_elegibilidade_sinteticas
 as restrictive for select to authenticated using(exists(
 select 1 from public.equipe_prumo_s1 e where e.ator_id=(select auth.uid()) and e.estado='ativo'));
create policy s1_70_supressao_gate on public.supressoes_contato_sinteticas
 as restrictive for select to authenticated using(exists(
 select 1 from public.equipe_prumo_s1 e where e.ator_id=(select auth.uid()) and e.estado='ativo'));
notify pgrst, 'reload schema';
