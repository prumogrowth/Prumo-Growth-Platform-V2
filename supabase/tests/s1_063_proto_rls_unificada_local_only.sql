-- I43/I44: composicao de RLS restritiva em laboratório; S0 precisa homologar.
drop policy s1_61_casos_r on public.casos_humanos;
create policy s1_63_casos_restrict on public.casos_humanos as restrictive
 for select to authenticated using (
  prumo_s1_i41_test.pode_ler_caso(concessionaria_id,id,lead_id)
  or prumo_s1_i42_test.historico_autorizado(concessionaria_id,lead_id));
drop policy s1_61_conversas_r on public.conversas;
create policy s1_63_conversas_restrict on public.conversas as restrictive
 for select to authenticated using (
  caso_id is not null and (
   prumo_s1_i41_test.pode_ler_caso_id(concessionaria_id,caso_id)
   or prumo_s1_i42_test.caso_historico_autorizado(concessionaria_id,caso_id)));
drop policy s1_61_atribuicoes_r on public.atribuicoes_humanas;
create policy s1_63_atribuicoes_restrict on public.atribuicoes_humanas as restrictive
 for select to authenticated using (
  prumo_s1_i41_test.pode_ler_atribuicao(
    concessionaria_id,caso_id,operador_id,encerrada_em)
  or (
   encerrada_em is null and
   prumo_private.s1_caso_excepcional_autorizado_55(concessionaria_id,caso_id)
  ));
-- Duas policies RESTRICTIVE distintas gerariam AND: retirar ambas.
-- I42 isolado tambem nega Gestor de equipe sem grant da concessionaria.
drop policy s1_61_mensagens_r on public.mensagens;
drop policy s1_62_mensagens_restrict on public.mensagens;
create policy s1_63_mensagens_restrict on public.mensagens as restrictive
 for select to authenticated using (
  prumo_s1_i41_test.pode_ler_mensagem(concessionaria_id,conversa_id,caso_id)
  or (caso_id is not null
   and prumo_s1_i42_test.msg_historico_autorizado(
    concessionaria_id,conversa_id,caso_id)));
