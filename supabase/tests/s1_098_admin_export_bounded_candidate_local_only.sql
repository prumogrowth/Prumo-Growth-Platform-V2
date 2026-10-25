-- I69 local-only. Bounded per-request export of minimally-scoped I68 summaries.
-- NO changes to shared headers; no signing / production rollout / bulk export.
-- Invoker function reads S0 tables with RLS I63/I67 and column grants I68.
-- Raw I68 views must not remain directly queryable to bypass LIMIT.
do $pre$ begin
 if current_user<>'postgres'
 or pg_catalog.to_regclass('public.s1_68_lotes_equipe') is null
 or pg_catalog.to_regclass('public.s1_68_canais_equipe') is null
 or not pg_catalog.has_table_privilege('authenticated','public.s1_68_lotes_equipe','SELECT')
 or not pg_catalog.has_table_privilege('authenticated','public.s1_68_canais_equipe','SELECT')
 or (select count(*) from pg_catalog.pg_policies
    where schemaname='public' and policyname like 's1_67_%')<>3
 then raise exception 'I69_UNEXPECTED_I68_BASELINE' using errcode='42501';end if;
end $pre$;

-- Prevent an unbounded direct scan of aggregated I68 views via REST.
revoke select on public.s1_68_lotes_equipe,public.s1_68_canais_equipe
 from public,anon,authenticated,service_role;

-- Keyset pages of up to 20 group summaries per authenticated manager+store.
-- The function is SECURITY INVOKER: underlying RLS and SELECT grants
-- apply as the JWT role, not the function owner. No dynamic SQL.
create function public.s1_69_exportar_lotes(
 p_loja uuid,p_apos uuid,p_limite integer)
returns table(concessionaria_id uuid,lote_ref uuid,itens_autorizados bigint)
language plpgsql stable security invoker set search_path='' as $body$
begin
 if p_loja is null or p_limite is null or p_limite<1 or p_limite>20 then
  raise exception 'I69_PAGINACAO_INVALIDA' using errcode='22023';end if;
 return query
 select i.concessionaria_id,i.lote_id,count(*)::bigint
 from public.itens_lote i
 where i.concessionaria_id=p_loja and i.resultado='aceito'
  and (p_apos is null or i.lote_id>p_apos)
 group by i.concessionaria_id,i.lote_id
 order by i.concessionaria_id,i.lote_id
 limit p_limite;
end $body$;

create function public.s1_69_exportar_canais(
 p_loja uuid,p_apos uuid,p_limite integer)
returns table(concessionaria_id uuid,canal_ref uuid,conversas_autorizadas bigint)
language plpgsql stable security invoker set search_path='' as $body$
begin
 if p_loja is null or p_limite is null or p_limite<1 or p_limite>20 then
  raise exception 'I69_PAGINACAO_INVALIDA' using errcode='22023';end if;
 return query
 select c.concessionaria_id,c.canal_id,count(*)::bigint
 from public.conversas c
 where c.concessionaria_id=p_loja
  and (p_apos is null or c.canal_id>p_apos)
  and exists(select 1 from public.vinculos_papel_escopo v
    where v.ator_id=(select auth.uid())
      and v.concessionaria_id=c.concessionaria_id
      and v.papel='gestor'
      and v.valido_desde<=pg_catalog.statement_timestamp()
      and (v.valido_ate is null
           or v.valido_ate>pg_catalog.statement_timestamp()))
 group by c.concessionaria_id,c.canal_id
 order by c.concessionaria_id,c.canal_id
 limit p_limite;
end $body$;

revoke all on function
 public.s1_69_exportar_lotes(uuid,uuid,integer),
 public.s1_69_exportar_canais(uuid,uuid,integer)
 from public,anon,authenticated,service_role;
grant execute on function
 public.s1_69_exportar_lotes(uuid,uuid,integer),
 public.s1_69_exportar_canais(uuid,uuid,integer)
 to authenticated;

do $gate$ declare p oid; begin
 if pg_catalog.has_table_privilege('authenticated','public.s1_68_lotes_equipe','SELECT')
 or pg_catalog.has_table_privilege('authenticated','public.s1_68_canais_equipe','SELECT')
 or pg_catalog.has_table_privilege('anon','public.s1_68_lotes_equipe','SELECT')
 or pg_catalog.has_function_privilege('anon','public.s1_69_exportar_lotes(uuid,uuid,integer)','EXECUTE')
 or pg_catalog.has_function_privilege('anon','public.s1_69_exportar_canais(uuid,uuid,integer)','EXECUTE')
 or not pg_catalog.has_function_privilege('authenticated','public.s1_69_exportar_lotes(uuid,uuid,integer)','EXECUTE')
 or not pg_catalog.has_function_privilege('authenticated','public.s1_69_exportar_canais(uuid,uuid,integer)','EXECUTE')
 or (select count(*) from pg_catalog.pg_proc
    where oid in (
       'public.s1_69_exportar_lotes(uuid,uuid,integer)'::regprocedure,
       'public.s1_69_exportar_canais(uuid,uuid,integer)'::regprocedure)
     and not prosecdef and provolatile='s')<>2
 or pg_catalog.has_schema_privilege('authenticated','prumo_s1_interface','USAGE')
 then raise exception 'I69_DIRECT_EXPORT_OR_PRIVILEGE_BYPASS' using errcode='42501';end if;
end $gate$;
