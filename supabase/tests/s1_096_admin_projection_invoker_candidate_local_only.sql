-- I68 local-only projection boundary. Requires I63+I64+I67.
-- No raw batch/channel headers, no new SECURITY DEFINER or public RPC.
-- Restrictive RLS is retained. Column ACL shrinks the otherwise SELECT * D2.
do $pre$ begin
 if current_user<>'postgres'
 or (select count(*) from pg_catalog.pg_policies
     where schemaname='public' and policyname like 's1_67_%')<>3
 or (select count(*) from pg_catalog.pg_policies
     where schemaname='public' and policyname like 's1_64_%')<>4
 or pg_catalog.to_regclass('public.s1_68_lotes_equipe') is not null
 or pg_catalog.to_regclass('public.s1_68_canais_equipe') is not null
 then raise exception 'I68_CANDIDATE_BASELINE_DRIFT' using errcode='42501';end if;
end $pre$;

-- Keep selected IDs only when required to join a granted case or group.
-- Do NOT grant id, criado_em, motivo_rejeicao, motivo, status_anterior,
-- tipo_origem or any text from shared lot/channel headers.
revoke select on table public.itens_lote from authenticated;
revoke select on table public.reencontros_lote from authenticated;
revoke select on table public.eventos_status_comercial from authenticated;
grant select (concessionaria_id,lote_id,ordinal_linha,lead_id,resultado)
 on public.itens_lote to authenticated;
grant select (concessionaria_id,lote_id,lead_id)
 on public.reencontros_lote to authenticated;
grant select (concessionaria_id,ciclo_id,versao_ciclo_apos,status_posterior)
 on public.eventos_status_comercial to authenticated;

-- PostgreSQL 15+ security_invoker applies the JWT caller's RLS and SELECT
-- privilege to underlying tables BEFORE aggregation. The opaque reference
-- and count are for authorized rows only, NEVER whole-lot totals.
create view public.s1_68_lotes_equipe
 with (security_invoker=true)
as
select concessionaria_id, lote_id as lote_ref,
 count(*)::bigint as itens_autorizados
from public.itens_lote
where resultado='aceito'
group by concessionaria_id,lote_id;

-- Channel metadata comes only from allowed conversations; never join to
-- public.canais_loja (I64 quarantine), never read identificador_emissor.
-- Active manager/shop grant required to make this an ADMIN summary.
create view public.s1_68_canais_equipe
 with (security_invoker=true)
as
select c.concessionaria_id,c.canal_id as canal_ref,
 count(*)::bigint as conversas_autorizadas
from public.conversas c
where exists(
 select 1 from public.vinculos_papel_escopo v
 where v.concessionaria_id=c.concessionaria_id
  and v.ator_id=(select auth.uid())
  and v.papel='gestor'
  and v.valido_desde<=pg_catalog.statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
)
group by c.concessionaria_id,c.canal_id;

revoke all on public.s1_68_lotes_equipe,public.s1_68_canais_equipe
 from public,anon,service_role;
grant select on public.s1_68_lotes_equipe,public.s1_68_canais_equipe
 to authenticated;

do $gate$ declare v_name text;begin
 if (select count(*) from pg_catalog.pg_class c
  join pg_catalog.pg_namespace ns on ns.oid=c.relnamespace
  where ns.nspname='public' and c.relname in
    ('s1_68_lotes_equipe','s1_68_canais_equipe')
  and c.relkind='v'
  and 'security_invoker=true'=any(coalesce(c.reloptions,array[]::text[])))<>2
 or (select count(*) from pg_catalog.pg_policies
   where schemaname='public' and policyname like 's1_67_%')<>3
 or pg_catalog.has_table_privilege('anon','public.s1_68_lotes_equipe','SELECT')
 or pg_catalog.has_table_privilege('anon','public.s1_68_canais_equipe','SELECT')
 or pg_catalog.has_column_privilege('authenticated','public.itens_lote','id','SELECT')
 or pg_catalog.has_column_privilege('authenticated','public.itens_lote','motivo_rejeicao','SELECT')
 or pg_catalog.has_column_privilege('authenticated','public.reencontros_lote','motivo','SELECT')
 or pg_catalog.has_column_privilege('authenticated','public.eventos_status_comercial','status_anterior','SELECT')
 or not pg_catalog.has_column_privilege('authenticated','public.itens_lote','lead_id','SELECT')
 or not pg_catalog.has_column_privilege('authenticated','public.eventos_status_comercial','status_posterior','SELECT')
 or pg_catalog.has_schema_privilege('authenticated','prumo_s1_interface','USAGE')
 then raise exception 'I68_COLUMN_OR_INVOKER_VIEW_BOUNDARY_INVALID' using errcode='42501';end if;
end $gate$;
