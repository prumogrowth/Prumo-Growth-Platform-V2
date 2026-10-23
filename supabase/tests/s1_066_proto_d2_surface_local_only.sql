-- I46: only disposable I44/I45 GoTrue/PostgREST fixture, not a migration.
-- Mixed import-batch header has no reliable case-level identity: fail closed
-- until S0 provides a minimal authorized projection for workflow/queue.
create policy s1_66_lotes_restrict on public.lotes_importacao as restrictive
 for select to authenticated using (false);
-- Content bearing an explicit lead/cycle FK may use the I45 team/context guard.
create policy s1_66_itens_contexto_p on public.itens_lote for select to authenticated
 using(prumo_s1_i45_test.pode_ler_lead(concessionaria_id,lead_id));
create policy s1_66_itens_contexto_r on public.itens_lote as restrictive
 for select to authenticated
 using(prumo_s1_i45_test.pode_ler_lead(concessionaria_id,lead_id));
create policy s1_66_reencontros_contexto_p on public.reencontros_lote
 for select to authenticated using(
 prumo_s1_i45_test.pode_ler_lead(concessionaria_id,lead_id));
create policy s1_66_reencontros_contexto_r on public.reencontros_lote as restrictive
 for select to authenticated using(
 prumo_s1_i45_test.pode_ler_lead(concessionaria_id,lead_id));
create policy s1_66_eventos_contexto_p on public.eventos_status_comercial
 for select to authenticated using(
 prumo_s1_i45_test.pode_ler_ciclo(concessionaria_id,ciclo_id));
create policy s1_66_eventos_contexto_r on public.eventos_status_comercial as restrictive
 for select to authenticated using(
 prumo_s1_i45_test.pode_ler_ciclo(concessionaria_id,ciclo_id));
notify pgrst, 'reload schema';
