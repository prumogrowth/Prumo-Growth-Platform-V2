-- I71 experimental ONLY (PG17 + ephemeral GoTrue); must run AFTER I70 tests.
-- Sliding 60-minute quota, durable aggregate of DENIALS without customer data,
-- and private explicit retention. New caller-visible RPCs return status JSON,
-- and both old I69 export RPCs are revoked to prevent parallel unmetered paths.
do $pre$ begin
 if current_user<>'postgres'
 or to_regclass('public.s1_70_export_reservas') is null
 or to_regclass('prumo_private.s1_70_export_contadores') is null
 or not has_function_privilege('authenticated',
      'public.s1_69_exportar_lotes(uuid,uuid,integer)','EXECUTE')
 then raise exception 'I71_EXPECTS_I70_EPHEMERAL_BASELINE' using errcode='42501';end if;
end $pre$;
create table prumo_private.s1_71_export_recusas(
 ator_id uuid not null, concessionaria_id uuid not null,
 tipo text not null check(tipo in('lotes','canais')),
 minuto_inicio timestamptz not null, motivo text not null
  check(motivo='QUOTA_60_MINUTOS'),
 total integer not null default 1 check(total between 1 and 999999),
 ultima_em timestamptz not null,
 primary key(ator_id,concessionaria_id,tipo,minuto_inicio,motivo)
);
revoke all on prumo_private.s1_71_export_recusas
 from public,anon,authenticated,service_role;
-- Legacy fixed-hour counter would become stale: remove it rather than
-- falsely presenting it as an authoritative rolling quota.
drop table prumo_private.s1_70_export_contadores;

create or replace function prumo_private.s1_70_reserva_gatilho()
returns trigger language plpgsql volatile security definer
set search_path='' as $trigger$
declare t timestamptz;used_count integer;used_units integer;
begin
 if (select auth.uid()) is null
 or new.ator_id is distinct from (select auth.uid())
 or new.tipo not in ('lotes','canais')
 or new.unidades_reservadas not between 1 and 20
 or not exists(select 1 from public.equipe_prumo_s1 e
   where e.ator_id=new.ator_id and e.estado='ativo')
 or not exists(select 1 from public.vinculos_papel_escopo v
   where v.ator_id=new.ator_id and v.concessionaria_id=new.concessionaria_id
   and v.papel='gestor'
   and v.valido_desde<=pg_catalog.statement_timestamp()
   and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp()))
 then raise exception 'I71_RESERVA_NAO_AUTORIZADA' using errcode='42501';end if;

 -- Database-transaction-scoped lock: collisions only reduce throughput.
 -- Critical section rechecks ALL accepted reservations in trailing 60min.
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended(
    new.ator_id::text||':'||new.concessionaria_id::text||':'||new.tipo,0));
 t:=pg_catalog.clock_timestamp();
 select count(*)::integer,
  coalesce(sum(x.unidades_reservadas),0)::integer
 into used_count,used_units
 from public.s1_70_export_reservas x
 where x.ator_id=new.ator_id
 and x.concessionaria_id=new.concessionaria_id and x.tipo=new.tipo
 and x.registrada_em>t-interval '60 minutes'
 and x.registrada_em<=t;
 if used_count>=4 or used_units+new.unidades_reservadas>30 then
  insert into prumo_private.s1_71_export_recusas as q(
    ator_id,concessionaria_id,tipo,minuto_inicio,motivo,total,ultima_em)
  values(new.ator_id,new.concessionaria_id,new.tipo,
    pg_catalog.date_trunc('minute',t),'QUOTA_60_MINUTOS',1,t)
  on conflict (ator_id,concessionaria_id,tipo,minuto_inicio,motivo)
  do update set
   total=least(q.total+1,999999),ultima_em=excluded.ultima_em;
  -- No exception: persist private refusal as part of successful
  -- function call; SKIP writing a row into the accepted-only ledger.
  return null;
 end if;
 return new;
end $trigger$;
revoke all on function prumo_private.s1_70_reserva_gatilho()
 from public,anon,authenticated,service_role;

revoke all on function
 public.s1_69_exportar_lotes(uuid,uuid,integer),
 public.s1_69_exportar_canais(uuid,uuid,integer)
 from public,anon,authenticated,service_role;

-- All users call this single explicit response contract, never I69 directly.
-- No SECURITY DEFINER in public. Both reads use I63/I67 RLS and I68 ACL.
create function public.s1_71_exportar_resumo(
 p_tipo text,p_loja uuid,p_apos uuid,p_limite integer)
returns jsonb language plpgsql volatile security invoker
set search_path='' as $body$
declare n integer;payload jsonb;
begin
 if p_tipo is null or p_tipo not in('lotes','canais')
 or p_loja is null or p_limite is null or p_limite<1 or p_limite>20
 then raise exception 'I71_PAGINACAO_INVALIDA' using errcode='22023';end if;
 if (select auth.uid()) is null or not exists(
  select 1 from public.equipe_prumo_s1 e
  join public.vinculos_papel_escopo v on v.ator_id=e.ator_id
  where e.ator_id=(select auth.uid()) and e.estado='ativo'
  and v.concessionaria_id=p_loja and v.papel='gestor'
  and v.valido_desde<=pg_catalog.statement_timestamp()
  and (v.valido_ate is null
   or v.valido_ate>pg_catalog.statement_timestamp())
 ) then
  return pg_catalog.jsonb_build_object('estado','VAZIO','linhas', '[]'::jsonb);
 end if;
 insert into public.s1_70_export_reservas(
  ator_id,concessionaria_id,tipo,unidades_reservadas)
 values((select auth.uid()),p_loja,p_tipo,p_limite);
 get diagnostics n = row_count;
 if n<>1 then
  return pg_catalog.jsonb_build_object('estado','LIMITE_ATINGIDO',
    'linhas','[]'::jsonb);
 end if;
 if p_tipo='lotes' then
  select coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(page)
    order by page.lote_ref),'[]'::jsonb)
  into payload from (
    select i.concessionaria_id,i.lote_id as lote_ref,
      count(*)::bigint as itens_autorizados
    from public.itens_lote i
    where i.concessionaria_id=p_loja and i.resultado='aceito'
     and (p_apos is null or i.lote_id>p_apos)
    group by i.concessionaria_id,i.lote_id
    order by i.concessionaria_id,i.lote_id
    limit p_limite
  ) page;
 else
  select coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(page)
    order by page.canal_ref),'[]'::jsonb)
  into payload from (
    select c.concessionaria_id,c.canal_id as canal_ref,
      count(*)::bigint as conversas_autorizadas
    from public.conversas c
    where c.concessionaria_id=p_loja
     and (p_apos is null or c.canal_id>p_apos)
     and exists(select 1 from public.vinculos_papel_escopo v
       where v.ator_id=(select auth.uid())
        and v.concessionaria_id=c.concessionaria_id and v.papel='gestor'
        and v.valido_desde<=pg_catalog.statement_timestamp()
        and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp()))
    group by c.concessionaria_id,c.canal_id
    order by c.concessionaria_id,c.canal_id
    limit p_limite
  ) page;
 end if;
 return pg_catalog.jsonb_build_object('estado','OK','linhas',payload);
end $body$;

revoke all on function public.s1_71_exportar_resumo(text,uuid,uuid,integer)
 from public,anon,authenticated,service_role;
grant execute on function public.s1_71_exportar_resumo(text,uuid,uuid,integer)
 to authenticated;

-- Explicit-only administrator cleanup (no scheduled deletion; no cron
-- changes). 30 days for accepted reservations and aggregate denials,
-- enough to exceed any rolling quota window.
create function prumo_private.s1_71_purgar_registros(p_referencia timestamptz)
returns table(aceitos_excluidos bigint,recusas_excluidas bigint)
language plpgsql volatile security invoker set search_path='' as $purge$
declare a bigint;b bigint;
begin
 if current_user<>'postgres' or p_referencia is null
 then raise exception 'I71_LIMPEZA_ADMIN_APENAS' using errcode='42501';end if;
 delete from public.s1_70_export_reservas x
  where x.registrada_em<p_referencia-interval '30 days';
 get diagnostics a=row_count;
 delete from prumo_private.s1_71_export_recusas x
  where x.ultima_em<p_referencia-interval '30 days';
 get diagnostics b=row_count;
 return query select a,b;
end $purge$;
revoke all on function prumo_private.s1_71_purgar_registros(timestamptz)
 from public,anon,authenticated,service_role;

do $audit$ begin
 if has_function_privilege('authenticated',
    'public.s1_69_exportar_lotes(uuid,uuid,integer)','EXECUTE')
 or has_function_privilege('authenticated',
    'public.s1_69_exportar_canais(uuid,uuid,integer)','EXECUTE')
 or not has_function_privilege('authenticated',
    'public.s1_71_exportar_resumo(text,uuid,uuid,integer)','EXECUTE')
 or has_function_privilege('anon',
    'public.s1_71_exportar_resumo(text,uuid,uuid,integer)','EXECUTE')
 or (select count(*) from pg_catalog.pg_proc
   where oid='public.s1_71_exportar_resumo(text,uuid,uuid,integer)'::regprocedure
    and not prosecdef and provolatile='v')<>1
 or to_regclass('prumo_private.s1_70_export_contadores') is not null
 or has_table_privilege('authenticated','prumo_private.s1_71_export_recusas','SELECT')
 or has_table_privilege('authenticated','public.s1_70_export_reservas','SELECT')
 or has_schema_privilege('authenticated','prumo_private','USAGE')
 then raise exception 'I71_LEAK_OR_OLD_RPC_REMAINS' using errcode='42501';end if;
end $audit$;
