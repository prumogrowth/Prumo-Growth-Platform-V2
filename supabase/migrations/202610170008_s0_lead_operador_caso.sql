-- AP41: operador atribuído precisa consultar o lead do caso, nunca o cadastro geral da loja.
create policy leads_select_operador_designado on public.leads_loja
for select to authenticated using (
 exists(
  select 1 from public.casos_humanos h
  join public.atribuicoes_humanas a
    on a.concessionaria_id=h.concessionaria_id and a.caso_id=h.id
  where h.concessionaria_id=leads_loja.concessionaria_id
  and h.lead_id=leads_loja.id
  and a.operador_id=(select auth.uid())
  and a.encerrada_em is null
  and exists(select 1 from public.vinculos_papel_escopo v
   where v.ator_id=(select auth.uid())
     and v.concessionaria_id=leads_loja.concessionaria_id
     and v.papel in ('operador','gestor')
     and v.valido_desde<=statement_timestamp()
     and (v.valido_ate is null or v.valido_ate>statement_timestamp()))
 )
);
