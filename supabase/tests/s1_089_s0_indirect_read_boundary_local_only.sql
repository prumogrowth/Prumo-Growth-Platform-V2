-- I64: indirect S0 read boundary candidate; CI/PG17/GoTrue local ONLY.
-- Requires I63 canonical history functions and S0 manager-grant permissives.
-- Lead/cycle do not gain any new permissive access to consultants without grant.
-- Bulk imports, channels and status events have no defensible case-level
-- entitlement contract yet: intentionally quarantine ALL authenticated SELECTs.
create policy s1_64_leads_scope_r on public.leads_loja as restrictive
 for select to authenticated using (
 prumo_s1_i63_test.contato_com_caso(concessionaria_id,id));
create policy s1_64_ciclos_scope_r on public.ciclos_comerciais as restrictive
 for select to authenticated using (
 prumo_s1_i63_test.contato_com_caso(concessionaria_id,lead_id));

create policy s1_64_canais_quarantine_r on public.canais_loja as restrictive
 for select to authenticated using (false);
create policy s1_64_lotes_quarantine_r on public.lotes_importacao as restrictive
 for select to authenticated using (false);
create policy s1_64_itens_quarantine_r on public.itens_lote as restrictive
 for select to authenticated using (false);
create policy s1_64_reencontros_quarantine_r on public.reencontros_lote as restrictive
 for select to authenticated using (false);
create policy s1_64_eventos_quarantine_r on public.eventos_status_comercial as restrictive
 for select to authenticated using (false);

do $audit$ begin
 if (select count(*) from pg_catalog.pg_policies
   where schemaname='public' and policyname like 's1_64_%')<>7
 or exists (select 1 from pg_catalog.pg_policies
   where schemaname='public' and policyname like 's1_64_%'
    and (permissive<>'RESTRICTIVE' or cmd<>'SELECT'))
 or has_table_privilege('anon','public.leads_loja','SELECT')
 or has_table_privilege('anon','public.lotes_importacao','SELECT')
 or has_table_privilege('authenticated','prumo_private.s1_excecoes_caso_i61','SELECT')
 then raise exception 'I64_CANDIDATE_POLICY_MATRIX_INVALID' using errcode='42501';end if;
end $audit$;
