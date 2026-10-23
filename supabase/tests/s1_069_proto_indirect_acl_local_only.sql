-- I47 [P/T] only: candidate to isolate new S0 object read paths.
-- Strict fail-closed for unmatched callbacks and pending inbox; does not
-- implement an S0-proven shared queue or approve S0 operational migrations.
create schema prumo_s1_i47_test authorization postgres;
create function prumo_s1_i47_test.pode_ler_envio(p_loja uuid,p_envio uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_envio is not null and (select auth.uid()) is not null
 and exists(select 1 from public.envios_template_sinteticos e
  join public.planos_recontato_sinteticos p on
   p.concessionaria_id=e.concessionaria_id and p.id=e.plano_id
  where e.concessionaria_id=p_loja and e.id=p_envio
  and prumo_s1_i45_test.pode_ler_ciclo(p_loja,p.ciclo_id));
$fn$;
create function prumo_s1_i47_test.pode_ler_callback(p_loja uuid,p_evento uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_evento is not null and (select auth.uid()) is not null
 and exists(select 1 from public.eventos_callback_sinteticos cb
  where cb.concessionaria_id=p_loja and cb.id=p_evento
   and cb.envio_id is not null
   and prumo_s1_i47_test.pode_ler_envio(p_loja,cb.envio_id));
$fn$;
revoke all on schema prumo_s1_i47_test from public,anon,service_role;
grant usage on schema prumo_s1_i47_test to authenticated;
revoke all on function prumo_s1_i47_test.pode_ler_envio(uuid,uuid),
 prumo_s1_i47_test.pode_ler_callback(uuid,uuid) from public,anon,service_role;
grant execute on function prumo_s1_i47_test.pode_ler_envio(uuid,uuid),
 prumo_s1_i47_test.pode_ler_callback(uuid,uuid) to authenticated;

-- Unlike S1/038, this gate must cover objects added AFTER the original gate.
-- These exact nine objects are installed in S1's ephemeral test only.
do $s1$
declare v_rel text;
begin
 foreach v_rel in array array[
 'pendencias_inbound_simulado',
 'catalogo_templates_sinteticos','planos_recontato_sinteticos',
 'envios_template_sinteticos','eventos_envio_template_sinteticos',
 'eventos_callback_sinteticos','pendencias_reconciliacao_c07_sinteticas',
 'associacoes_callback_c07_sinteticas','auditoria_reconciliacao_c07_sintetica']
 loop
  execute format(
    'create policy s1_47_ativo_gate on public.%I as restrictive for select to authenticated
     using (exists(select 1 from public.equipe_prumo_s1 e where e.ator_id=(select auth.uid()) and e.estado=''ativo''))',
    v_rel);
 end loop;
end $s1$;

-- Inbox multiple cycles: it cannot be inferred to be a case or shared queue.
create policy s1_47_inbound_unlinked_deny on public.pendencias_inbound_simulado
 as restrictive for select to authenticated using (false);
-- Template catalog is store-level technical metadata, no case/write permission.
-- For all case-related rows we need both OR-permissive and AND-restrictive.
create policy s1_47_plano_p on public.planos_recontato_sinteticos
 for select to authenticated using(prumo_s1_i45_test.pode_ler_ciclo(concessionaria_id,ciclo_id));
create policy s1_47_plano_r on public.planos_recontato_sinteticos as restrictive
 for select to authenticated using(prumo_s1_i45_test.pode_ler_ciclo(concessionaria_id,ciclo_id));
create policy s1_47_envio_p on public.envios_template_sinteticos
 for select to authenticated using(prumo_s1_i47_test.pode_ler_envio(concessionaria_id,id));
create policy s1_47_envio_r on public.envios_template_sinteticos as restrictive
 for select to authenticated using(prumo_s1_i47_test.pode_ler_envio(concessionaria_id,id));
create policy s1_47_evento_envio_p on public.eventos_envio_template_sinteticos
 for select to authenticated using(prumo_s1_i47_test.pode_ler_envio(concessionaria_id,envio_id));
create policy s1_47_evento_envio_r on public.eventos_envio_template_sinteticos as restrictive
 for select to authenticated using(prumo_s1_i47_test.pode_ler_envio(concessionaria_id,envio_id));
create policy s1_47_callback_p on public.eventos_callback_sinteticos
 for select to authenticated using(prumo_s1_i47_test.pode_ler_envio(concessionaria_id,envio_id));
create policy s1_47_callback_r on public.eventos_callback_sinteticos as restrictive
 for select to authenticated using(prumo_s1_i47_test.pode_ler_envio(concessionaria_id,envio_id));
create policy s1_47_pendencia_p on public.pendencias_reconciliacao_c07_sinteticas
 for select to authenticated using(
 envio_id is not null and prumo_s1_i47_test.pode_ler_envio(concessionaria_id,envio_id)
 and prumo_s1_i47_test.pode_ler_callback(concessionaria_id,evento_id));
create policy s1_47_pendencia_r on public.pendencias_reconciliacao_c07_sinteticas as restrictive
 for select to authenticated using(
 envio_id is not null and prumo_s1_i47_test.pode_ler_envio(concessionaria_id,envio_id)
 and prumo_s1_i47_test.pode_ler_callback(concessionaria_id,evento_id));
create policy s1_47_associacao_p on public.associacoes_callback_c07_sinteticas
 for select to authenticated using(
 prumo_s1_i47_test.pode_ler_envio(concessionaria_id,envio_id)
 and prumo_s1_i47_test.pode_ler_callback(concessionaria_id,evento_id));
create policy s1_47_associacao_r on public.associacoes_callback_c07_sinteticas as restrictive
 for select to authenticated using(
 prumo_s1_i47_test.pode_ler_envio(concessionaria_id,envio_id)
 and prumo_s1_i47_test.pode_ler_callback(concessionaria_id,evento_id));
create policy s1_47_auditoria_p on public.auditoria_reconciliacao_c07_sintetica
 for select to authenticated using(
 envio_associado_id is not null
 and prumo_s1_i47_test.pode_ler_envio(concessionaria_id,envio_associado_id));
create policy s1_47_auditoria_r on public.auditoria_reconciliacao_c07_sintetica as restrictive
 for select to authenticated using(
 envio_associado_id is not null
 and prumo_s1_i47_test.pode_ler_envio(concessionaria_id,envio_associado_id));
notify pgrst, 'reload schema';
