-- S1-002/I18. SOMENTE TESTE TEMPORARIO NO SUPABASE LOCAL EFEMERO.
-- JAMAIS promover como migration: estas tres fachadas publicas sao pontes
-- descartaveis de ensaio E2E para a interface NAO EXPOSTA (I14/051).
-- Nenhuma ponte aceita p_solicitante; author é SEMPRE auth.uid() no helper.
create function public.s1_i18_mover(
 p_loja uuid,p_caso uuid,p_atribuicao_esperada uuid,p_destino uuid)
returns jsonb language plpgsql security definer set search_path='' as $fn$
begin
 return prumo_s1_interface.s1_mover_atendimento_sessao(
  p_loja,p_caso,p_atribuicao_esperada,p_destino);
end $fn$;
create function public.s1_i18_pausar(p_operador uuid,p_motivo_codigo text)
returns jsonb language plpgsql security definer set search_path='' as $fn$
begin
 return prumo_s1_interface.s1_pausar_operador_sessao(p_operador,p_motivo_codigo);
end $fn$;
create function public.s1_i18_reativar(p_operador uuid)
returns jsonb language plpgsql security definer set search_path='' as $fn$
begin
 return prumo_s1_interface.s1_reativar_operador_sessao(p_operador);
end $fn$;
revoke all on function
 public.s1_i18_mover(uuid,uuid,uuid,uuid),
 public.s1_i18_pausar(uuid,text),
 public.s1_i18_reativar(uuid)
 from public,anon,authenticated,service_role;
grant execute on function
 public.s1_i18_mover(uuid,uuid,uuid,uuid),
 public.s1_i18_pausar(uuid,text),
 public.s1_i18_reativar(uuid) to authenticated;
select pg_catalog.pg_notify('pgrst','reload schema');
