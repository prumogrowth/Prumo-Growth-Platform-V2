-- Acesso autenticado de LEITURA, sempre condicionado a RLS; escrita negada ao cliente.
grant select on public.atores,public.vinculos_papel_escopo,public.concessionarias,public.leads_loja,public.ciclos_comerciais to authenticated;
create policy atores_select_self on public.atores for select to authenticated
 using(id=(select auth.uid()));
create policy vinculos_select_self on public.vinculos_papel_escopo for select to authenticated
 using(ator_id=(select auth.uid()));
create policy concessionarias_select_linked on public.concessionarias for select to authenticated
 using(exists(
 select 1 from public.vinculos_papel_escopo v where v.ator_id=(select auth.uid())
 and v.concessionaria_id=concessionarias.id
 and v.valido_desde <= now() and (v.valido_ate is null or v.valido_ate>now())
 ));
create policy leads_select_gestor_loja on public.leads_loja for select to authenticated
 using(exists(
 select 1 from public.vinculos_papel_escopo v where v.ator_id=(select auth.uid())
 and v.concessionaria_id=leads_loja.concessionaria_id and v.papel='gestor'
 and v.valido_desde <= now() and (v.valido_ate is null or v.valido_ate>now())
 ));
create policy ciclos_select_gestor_loja on public.ciclos_comerciais for select to authenticated
 using(exists(
 select 1 from public.vinculos_papel_escopo v where v.ator_id=(select auth.uid())
 and v.concessionaria_id=ciclos_comerciais.concessionaria_id and v.papel='gestor'
 and v.valido_desde <= now() and (v.valido_ate is null or v.valido_ate>now())
 ));
-- Nenhuma permissão INSERT/UPDATE/DELETE ou leitura universal para OP e responsável.
