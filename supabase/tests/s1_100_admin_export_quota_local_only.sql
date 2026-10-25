-- I70 PRIVATE, TEST-ONLY: atomic hourly quota reservations for BOTH I69 exports.
-- Keeps I69 RLS / column ACLs; direct RPCs now consume reservations first.
-- Only verified-identity authenticated sessions may reserve their own
-- actor/store/type. Own-account direct INSERT can only EXHAUST own budget,
-- never reduce it or read/export another actor's data.
do $pre$ begin
 if current_user<>'postgres'
 or pg_catalog.to_regprocedure('public.s1_69_exportar_lotes(uuid,uuid,integer)') is null
 or pg_catalog.to_regprocedure('public.s1_69_exportar_canais(uuid,uuid,integer)') is null
 or pg_catalog.to_regclass('public.s1_70_export_reservas') is not null
 then raise exception 'I70_BAD_I69_BASELINE' using errcode='42501';end if;
end $pre$;

create table prumo_private.s1_70_export_contadores(
 ator_id uuid not null,concessionaria_id uuid not null,tipo text not null,
 janela_inicio timestamptz not null,requisicoes integer not null,
 unidades_reservadas integer not null,
 primary key(ator_id,concessionaria_id,tipo,janela_inicio),
 constraint s1_70_private_tipo check(tipo in('lotes','canais')),
 constraint s1_70_private_counts check(requisicoes between 1 and 4
  and unidades_reservadas between 1 and 30)
);
revoke all on prumo_private.s1_70_export_contadores
 from public,anon,authenticated,service_role;

create table public.s1_70_export_reservas(
 id bigint generated always as identity primary key,
 ator_id uuid not null,concessionaria_id uuid not null,
 tipo text not null check(tipo in('lotes','canais')),
 unidades_reservadas integer not null check(unidades_reservadas between 1 and 20),
 registrada_em timestamptz not null default pg_catalog.clock_timestamp()
);
alter table public.s1_70_export_reservas enable row level security;
revoke all on public.s1_70_export_reservas from public,anon,authenticated,service_role;
-- No SELECT, UPDATE or DELETE; insert without RETURNING.
grant insert(ator_id,concessionaria_id,tipo,unidades_reservadas)
 on public.s1_70_export_reservas to authenticated;
create policy s1_70_reserva_propria on public.s1_70_export_reservas
 for insert to authenticated with check(
  ator_id=(select auth.uid())
  and exists(select 1 from public.equipe_prumo_s1 e
    where e.ator_id=(select auth.uid()) and e.estado='ativo')
  and exists(select 1 from public.vinculos_papel_escopo v
    where v.ator_id=(select auth.uid())
      and v.concessionaria_id=s1_70_export_reservas.concessionaria_id
      and v.papel='gestor'
      and v.valido_desde<=pg_catalog.statement_timestamp()
      and (v.valido_ate is null
         or v.valido_ate>pg_catalog.statement_timestamp()))
 );

create function prumo_private.s1_70_reserva_gatilho()
returns trigger language plpgsql volatile security definer
set search_path='' as $trigger$
declare w timestamptz;ok int;
begin
 -- RLS validates caller; trigger revalidates to avoid future policy drift.
 if (select auth.uid()) is null
    or new.ator_id is distinct from (select auth.uid())
    or new.tipo not in ('lotes','canais')
    or new.unidades_reservadas not between 1 and 20
    or not exists(select 1 from public.equipe_prumo_s1 e
      where e.ator_id=new.ator_id and e.estado='ativo')
    or not exists(select 1 from public.vinculos_papel_escopo v
      where v.ator_id=new.ator_id and v.concessionaria_id=new.concessionaria_id
       and v.papel='gestor' and v.valido_desde<=pg_catalog.statement_timestamp()
       and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp()))
 then raise exception 'I70_RESERVA_NAO_AUTORIZADA' using errcode='42501';end if;
 w:=pg_catalog.date_trunc('hour',pg_catalog.statement_timestamp());
 insert into prumo_private.s1_70_export_contadores as q(
    ator_id,concessionaria_id,tipo,janela_inicio,requisicoes,unidades_reservadas)
 values(new.ator_id,new.concessionaria_id,new.tipo,w,1,new.unidades_reservadas)
 on conflict(ator_id,concessionaria_id,tipo,janela_inicio)
 do update set requisicoes=q.requisicoes+1,
   unidades_reservadas=q.unidades_reservadas+excluded.unidades_reservadas
 where q.requisicoes<4
  and q.unidades_reservadas+excluded.unidades_reservadas<=30
 returning 1 into ok;
 if ok is distinct from 1 then
  raise exception 'I70_QUOTA_EXCEDIDA' using errcode='22023';end if;
 return new;
end $trigger$;
revoke all on function prumo_private.s1_70_reserva_gatilho()
 from public,anon,authenticated,service_role;
create trigger s1_70_gate_reserva before insert on public.s1_70_export_reservas
 for each row execute function prumo_private.s1_70_reserva_gatilho();

-- Upgrade the two I69 invoker RPCs in-place. Concurrency is guaranteed by
-- the private counter's INSERT ON CONFLICT row lock, not app state.
create or replace function public.s1_69_exportar_lotes(
 p_loja uuid,p_apos uuid,p_limite integer)
returns table(concessionaria_id uuid,lote_ref uuid,itens_autorizados bigint)
language plpgsql volatile security invoker set search_path='' as $body$
begin
 if p_loja is null or p_limite is null or p_limite<1 or p_limite>20 then
  raise exception 'I69_PAGINACAO_INVALIDA' using errcode='22023';end if;
 if not exists(select 1 from public.equipe_prumo_s1 e
   join public.vinculos_papel_escopo v
    on v.ator_id=e.ator_id
   where e.ator_id=(select auth.uid()) and e.estado='ativo'
    and v.concessionaria_id=p_loja and v.papel='gestor'
    and v.valido_desde<=pg_catalog.statement_timestamp()
    and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
 ) then return;end if;
 insert into public.s1_70_export_reservas(
   ator_id,concessionaria_id,tipo,unidades_reservadas)
 values((select auth.uid()),p_loja,'lotes',p_limite);
 return query
 select i.concessionaria_id,i.lote_id,count(*)::bigint
 from public.itens_lote i
 where i.concessionaria_id=p_loja and i.resultado='aceito'
  and (p_apos is null or i.lote_id>p_apos)
 group by i.concessionaria_id,i.lote_id
 order by i.concessionaria_id,i.lote_id
 limit p_limite;
end $body$;

create or replace function public.s1_69_exportar_canais(
 p_loja uuid,p_apos uuid,p_limite integer)
returns table(concessionaria_id uuid,canal_ref uuid,conversas_autorizadas bigint)
language plpgsql volatile security invoker set search_path='' as $body$
begin
 if p_loja is null or p_limite is null or p_limite<1 or p_limite>20 then
  raise exception 'I69_PAGINACAO_INVALIDA' using errcode='22023';end if;
 if not exists(select 1 from public.equipe_prumo_s1 e
   join public.vinculos_papel_escopo v on v.ator_id=e.ator_id
    where e.ator_id=(select auth.uid()) and e.estado='ativo'
     and v.concessionaria_id=p_loja and v.papel='gestor'
     and v.valido_desde<=pg_catalog.statement_timestamp()
     and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
 ) then return;end if;
 insert into public.s1_70_export_reservas(
   ator_id,concessionaria_id,tipo,unidades_reservadas)
 values((select auth.uid()),p_loja,'canais',p_limite);
 return query
 select c.concessionaria_id,c.canal_id,count(*)::bigint
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
 limit p_limite;
end $body$;

do $post$ begin
 if (select count(*) from pg_catalog.pg_proc
   where oid in (
    'public.s1_69_exportar_lotes(uuid,uuid,integer)'::regprocedure,
    'public.s1_69_exportar_canais(uuid,uuid,integer)'::regprocedure)
    and not prosecdef and provolatile='v')<>2
 or pg_catalog.has_table_privilege('authenticated','public.s1_70_export_reservas','SELECT')
 or pg_catalog.has_table_privilege('authenticated','prumo_private.s1_70_export_contadores','SELECT')
 or pg_catalog.has_table_privilege('anon','public.s1_70_export_reservas','INSERT')
 or pg_catalog.has_schema_privilege('authenticated','prumo_private','USAGE')
 or pg_catalog.has_schema_privilege('authenticated','prumo_s1_interface','USAGE')
 or (select count(*) from pg_catalog.pg_policies
    where schemaname='public' and policyname like 's1_67_%')<>3
 or (select count(*) from pg_catalog.pg_policies
    where schemaname='public' and policyname='s1_70_reserva_propria')<>1
 then raise exception 'I70_QUOTA_ACL_OR_RLS_INVALID' using errcode='42501';end if;
end $post$;
