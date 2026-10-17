-- D41: gestor vê D2 completo da sua(s) lojas; OP só caso designado.
-- D3/D4 não estão armazenados nesta fatia, e nenhuma permissão de leitura bruta é criada.
-- Apenas SELECT permitido aos clientes; mensagem simulada escrita pelo OP designado.
grant select on public.canais_loja,public.lotes_importacao,public.itens_lote,
 public.reencontros_lote,public.eventos_status_comercial,public.casos_humanos,
 public.atribuicoes_humanas,public.conversas,public.mensagens to authenticated;
-- Atribuições são legíveis por gestor da loja ou pelo próprio operador designado.
create policy atribuicoes_select_escopo on public.atribuicoes_humanas
 for select to authenticated using (
 operador_id=(select auth.uid()) or exists(
  select 1 from public.vinculos_papel_escopo v where
   v.ator_id=(select auth.uid()) and v.concessionaria_id=atribuicoes_humanas.concessionaria_id
   and v.papel='gestor' and v.valido_desde<=now() and (v.valido_ate is null or v.valido_ate>now())
 ));
create policy casos_select_escopo on public.casos_humanos
 for select to authenticated using (
 exists(select 1 from public.vinculos_papel_escopo v
  where v.ator_id=(select auth.uid()) and v.concessionaria_id=casos_humanos.concessionaria_id
  and v.papel='gestor' and v.valido_desde<=now() and (v.valido_ate is null or v.valido_ate>now()))
 or exists(select 1 from public.atribuicoes_humanas a
  where a.concessionaria_id=casos_humanos.concessionaria_id and a.caso_id=casos_humanos.id
  and a.operador_id=(select auth.uid()) and a.encerrada_em is null
  and exists(select 1 from public.vinculos_papel_escopo vx
   where vx.ator_id=(select auth.uid()) and vx.concessionaria_id=a.concessionaria_id
   and vx.papel in ('gestor','operador') and vx.valido_desde<=now()
   and (vx.valido_ate is null or vx.valido_ate>now())))
);
create policy conversas_select_escopo on public.conversas
 for select to authenticated using (
 exists(select 1 from public.vinculos_papel_escopo v
  where v.ator_id=(select auth.uid()) and v.concessionaria_id=conversas.concessionaria_id
  and v.papel='gestor' and v.valido_desde<=now() and (v.valido_ate is null or v.valido_ate>now()))
 or exists(select 1 from public.atribuicoes_humanas a
  where a.concessionaria_id=conversas.concessionaria_id and a.caso_id=conversas.caso_id
  and a.operador_id=(select auth.uid()) and a.encerrada_em is null
  and exists(select 1 from public.vinculos_papel_escopo vx
   where vx.ator_id=(select auth.uid()) and vx.concessionaria_id=a.concessionaria_id
   and vx.papel in ('gestor','operador') and vx.valido_desde<=now()
   and (vx.valido_ate is null or vx.valido_ate>now())))
);
create policy mensagens_select_escopo on public.mensagens
 for select to authenticated using (
 exists(select 1 from public.conversas c
  where c.concessionaria_id=mensagens.concessionaria_id and c.id=mensagens.conversa_id)
);
create policy canais_select_gestor on public.canais_loja
 for select to authenticated using (exists(
 select 1 from public.vinculos_papel_escopo v where v.ator_id=(select auth.uid())
 and v.concessionaria_id=canais_loja.concessionaria_id and v.papel='gestor'
 and v.valido_desde<=now() and (v.valido_ate is null or v.valido_ate>now())
));
create policy lotes_select_gestor on public.lotes_importacao
 for select to authenticated using (exists(
 select 1 from public.vinculos_papel_escopo v where v.ator_id=(select auth.uid())
 and v.concessionaria_id=lotes_importacao.concessionaria_id and v.papel='gestor'
 and v.valido_desde<=now() and (v.valido_ate is null or v.valido_ate>now())
));
create policy itens_select_gestor on public.itens_lote
 for select to authenticated using (exists(
 select 1 from public.vinculos_papel_escopo v where v.ator_id=(select auth.uid())
 and v.concessionaria_id=itens_lote.concessionaria_id and v.papel='gestor'
 and v.valido_desde<=now() and (v.valido_ate is null or v.valido_ate>now())
));
create policy reencontros_select_gestor on public.reencontros_lote
 for select to authenticated using (exists(
 select 1 from public.vinculos_papel_escopo v where v.ator_id=(select auth.uid())
 and v.concessionaria_id=reencontros_lote.concessionaria_id and v.papel='gestor'
 and v.valido_desde<=now() and (v.valido_ate is null or v.valido_ate>now())
));
create policy eventos_status_select_gestor on public.eventos_status_comercial
 for select to authenticated using (exists(
 select 1 from public.vinculos_papel_escopo v where v.ator_id=(select auth.uid())
 and v.concessionaria_id=eventos_status_comercial.concessionaria_id and v.papel='gestor'
 and v.valido_desde<=now() and (v.valido_ate is null or v.valido_ate>now())
));
-- Somente inserções SIMULADAS, atribuições vigentes e autoria vinculada ao JWT.
grant insert (concessionaria_id,conversa_id,canal_id,caso_id,direcao,origem,
 conteudo_sintetico,enviada_por) on public.mensagens to authenticated;
create policy mensagens_insert_operador_simulado on public.mensagens
 for insert to authenticated with check (
 direcao='saida' and origem='simulado' and id_externo is null
 and enviada_por=(select auth.uid()) and caso_id is not null
 and exists(select 1 from public.atribuicoes_humanas a
  where a.concessionaria_id=mensagens.concessionaria_id and a.caso_id=mensagens.caso_id
  and a.operador_id=(select auth.uid()) and a.encerrada_em is null
  and exists(select 1 from public.vinculos_papel_escopo vx
   where vx.ator_id=(select auth.uid()) and vx.concessionaria_id=a.concessionaria_id
   and vx.papel in ('gestor','operador') and vx.valido_desde<=now()
   and (vx.valido_ate is null or vx.valido_ate>now())))
 and exists(select 1 from public.vinculos_papel_escopo v
  where v.concessionaria_id=mensagens.concessionaria_id and v.ator_id=(select auth.uid())
  and v.papel in ('operador','gestor') and v.valido_desde<=now()
  and (v.valido_ate is null or v.valido_ate>now()))
);
-- Nada de DML via cliente em casos, atribuições, lotes, ciclos, eventos ou dados sensíveis.
