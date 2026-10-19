-- S1-002/I8: trilha de auditoria append-only no sandbox PG17.
-- Nao protege contra SUPERUSER que explicitamente desabilita triggers,
-- nem substitui politica de retencao, assinatura externa ou LGPD.
-- Sem alteração S0, canais, status, dados reais ou Supabase hospedado.
create function prumo_private.s1_proibir_alteracao_historico()
returns trigger language plpgsql security invoker set search_path='' as $s1$
begin
 raise exception 'HISTORICO_S1_IMUTAVEL' using errcode='23514';
 return null;
end $s1$;

-- Eventos de estado de equipe registrados na 038.
create trigger s1_hist_equipes_no_mutation
 before update or delete on public.equipe_prumo_eventos_s1
 for each row execute function prumo_private.s1_proibir_alteracao_historico();
create trigger s1_hist_equipes_no_truncate
 before truncate on public.equipe_prumo_eventos_s1
 for each statement execute function prumo_private.s1_proibir_alteracao_historico();

-- Movimentação de responsável registrada na 039.
create trigger s1_hist_movimentos_no_mutation
 before update or delete on prumo_private.s1_remanejamento_historico
 for each row execute function prumo_private.s1_proibir_alteracao_historico();
create trigger s1_hist_movimentos_no_truncate
 before truncate on prumo_private.s1_remanejamento_historico
 for each statement execute function prumo_private.s1_proibir_alteracao_historico();

-- Recuperação de pendência registrada na 042.
create trigger s1_hist_recuperacoes_no_mutation
 before update or delete on prumo_private.s1_recuperacao_fila_historico
 for each row execute function prumo_private.s1_proibir_alteracao_historico();
create trigger s1_hist_recuperacoes_no_truncate
 before truncate on prumo_private.s1_recuperacao_fila_historico
 for each statement execute function prumo_private.s1_proibir_alteracao_historico();
revoke all on function prumo_private.s1_proibir_alteracao_historico()
 from public,anon,authenticated,service_role;
