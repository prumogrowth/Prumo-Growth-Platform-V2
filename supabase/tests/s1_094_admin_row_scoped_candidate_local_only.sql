-- I67 disposable candidate: read only row-addressable administrative D2,
-- never whole shared channel/batch headers. Requires I63 + I64.
-- No new permissive policy, grant, view, SECURITY DEFINER or RPC.
-- Legacy I64 restrictive quarantine is replaced IN-PLACE on 3 tables.
do $pre$
begin
 if current_user<>'postgres'
 or (select count(*) from pg_catalog.pg_policies
     where schemaname='public' and policyname like 's1_64_%')<>7
 or (select count(*) from pg_catalog.pg_policies
     where schemaname='public' and policyname like 's1_63_canon_%')<>8
 then raise exception 'I67_WRONG_CANDIDATE_BASELINE' using errcode='42501';end if;
end $pre$;

drop policy s1_64_itens_quarantine_r on public.itens_lote;
drop policy s1_64_reencontros_quarantine_r on public.reencontros_lote;
drop policy s1_64_eventos_quarantine_r on public.eventos_status_comercial;

-- The existing S0 permissive policy still demands an active MANAGER grant
-- for the exact store. I63 validates team-specific case participation.
-- Rejected lines have no lead id and are never readable by customer case.
create policy s1_67_itens_caso_r on public.itens_lote as restrictive
 for select to authenticated using (
 resultado='aceito' and lead_id is not null
 and prumo_s1_i63_test.contato_com_caso(concessionaria_id,lead_id));
create policy s1_67_reencontros_caso_r on public.reencontros_lote as restrictive
 for select to authenticated using (
 prumo_s1_i63_test.contato_com_caso(concessionaria_id,lead_id));
create policy s1_67_eventos_ciclo_r on public.eventos_status_comercial as restrictive
 for select to authenticated using (
 exists(select 1 from public.ciclos_comerciais c
  where c.concessionaria_id=eventos_status_comercial.concessionaria_id
   and c.id=eventos_status_comercial.ciclo_id
   and prumo_s1_i63_test.contato_com_caso(c.concessionaria_id,c.lead_id)));

do $gate$
begin
 if (select count(*) from pg_catalog.pg_policies
     where schemaname='public' and policyname like 's1_64_%')<>4
 or (select count(*) from pg_catalog.pg_policies
     where schemaname='public' and policyname like 's1_67_%')<>3
 or exists(select 1 from pg_catalog.pg_policies
     where schemaname='public' and policyname like 's1_67_%'
      and (permissive<>'RESTRICTIVE' or cmd<>'SELECT'))
 or not exists(select 1 from pg_catalog.pg_policies
     where schemaname='public' and policyname='s1_64_lotes_quarantine_r'
       and pg_catalog.pg_get_expr(
         (select polqual from pg_catalog.pg_policy
          where polname='s1_64_lotes_quarantine_r'
            and polrelid='public.lotes_importacao'::regclass),
         'public.lotes_importacao'::regclass)='false')
 or not exists(select 1 from pg_catalog.pg_policies
     where schemaname='public' and policyname='s1_64_canais_quarantine_r')
 or pg_catalog.has_table_privilege('anon','public.itens_lote','SELECT')
 or pg_catalog.has_table_privilege('authenticated',
    'prumo_private.s1_excecoes_caso_i61','SELECT')
 then raise exception 'I67_POLICY_BOUNDARY_BROKEN' using errcode='42501';end if;
end $gate$;
