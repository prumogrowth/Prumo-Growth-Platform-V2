-- E04 only. Dedicated disposable PG17. Do not deploy to hosted Supabase.
-- S0 OBSERVED source ledger: statement_timestamp is minted inside PG17 triggers,
-- distinct from caller-writable legacy criado_em. Cannot prove past history.
create extension if not exists pgcrypto;
create table prumo_private.cfi01_f02_c04_origin_ledger_local (
 id bigint generated always as identity primary key,
 concessionaria_id uuid not null,
 lead_id uuid not null,
 tipo text not null check (tipo in ('HUMAN_CASE','PLAN','ATTEMPT','C08_EVENT')),
 entidade_id uuid not null,
 etapa text not null check (etapa in ('CREATE','RESERVE','CANCEL','RECORD')),
 observado_em timestamptz not null default statement_timestamp(),
 estado_novo text,
 payload_sha256 text not null check(payload_sha256 ~ '^[0-9a-f]{64}$'),
 unique(concessionaria_id,tipo,entidade_id,etapa),
 check ((tipo='HUMAN_CASE' and etapa='CREATE')
  or (tipo='PLAN' and etapa in ('CREATE','CANCEL'))
  or (tipo='ATTEMPT' and etapa in ('CREATE','RESERVE','CANCEL'))
  or (tipo='C08_EVENT' and etapa='RECORD'))
);
create index cfi01_f02_c04_origin_lead_local
 on prumo_private.cfi01_f02_c04_origin_ledger_local
 (concessionaria_id,lead_id,tipo,etapa);

create function prumo_private.cfi01_f02_c04_origin_append_guard_local()
returns trigger language plpgsql security invoker set search_path='' as $$
begin
 if tg_op<>'INSERT' or current_user<>'postgres' then
  raise exception 'E04_ORIGIN_APPEND_ONLY' using errcode='42501';
 end if;
 return new;
end $$;
create trigger cfi01_f02_c04_origin_append
 before insert or update or delete on prumo_private.cfi01_f02_c04_origin_ledger_local
 for each row execute function prumo_private.cfi01_f02_c04_origin_append_guard_local();

create function prumo_private.cfi01_f02_c04_origin_observe_local()
returns trigger language plpgsql security invoker set search_path='' as $$
declare v_tipo text;v_etapa text;v_lead uuid;v_row jsonb;
begin
 if current_user<>'postgres' then
  raise exception 'E04_ORIGIN_WRITER_DENIED' using errcode='42501';
 end if;
 v_row=to_jsonb(new);
 if tg_table_name='casos_humanos' then
  if tg_op<>'INSERT' then return new;end if;
  v_tipo='HUMAN_CASE';v_etapa='CREATE';v_lead=new.lead_id;
 elsif tg_table_name='planos_recontato_sinteticos' then
  v_tipo='PLAN';v_lead=new.lead_id;
  if tg_op='INSERT' then v_etapa='CREATE';
  elsif tg_op='UPDATE' and old.estado<>'cancelado'
        and new.estado='cancelado' then v_etapa='CANCEL';
  else return new;end if;
 elsif tg_table_name='envios_template_sinteticos' then
  v_tipo='ATTEMPT';
  select p.lead_id into v_lead from public.planos_recontato_sinteticos p
   where p.concessionaria_id=new.concessionaria_id and p.id=new.plano_id;
  if v_lead is null then
   raise exception 'E04_ORIGIN_NO_PARENT' using errcode='42501';
  end if;
  if tg_op='INSERT' then v_etapa='CREATE';
  elsif tg_op='UPDATE' and old.estado<>'reservado'
       and new.estado='reservado' then v_etapa='RESERVE';
  elsif tg_op='UPDATE' and old.estado<>'cancelado'
       and new.estado='cancelado' then v_etapa='CANCEL';
  else return new;end if;
 elsif tg_table_name='eventos_envio_template_sinteticos' then
  if tg_op<>'INSERT' then return new;end if;
  v_tipo='C08_EVENT';v_etapa='RECORD';
  select p.lead_id into v_lead
   from public.envios_template_sinteticos e
   join public.planos_recontato_sinteticos p
    on p.concessionaria_id=e.concessionaria_id and p.id=e.plano_id
   where e.id=new.envio_id and e.concessionaria_id=new.concessionaria_id;
  if v_lead is null then
   raise exception 'E04_ORIGIN_NO_ATTEMPT' using errcode='42501';
  end if;
 else
  raise exception 'E04_ORIGIN_UNSUPPORTED_TABLE' using errcode='42501';
 end if;
 insert into prumo_private.cfi01_f02_c04_origin_ledger_local
  (concessionaria_id,lead_id,tipo,entidade_id,etapa,estado_novo,payload_sha256)
 values(new.concessionaria_id,v_lead,v_tipo,new.id,v_etapa,
  v_row->>'estado',encode(public.digest(v_row::text,'sha256'),'hex'));
 return new;
end $$;

create trigger cfi01_f02_origin_case_insert
 after insert on public.casos_humanos for each row
 execute function prumo_private.cfi01_f02_c04_origin_observe_local();
create trigger cfi01_f02_origin_plan_insert_update
 after insert or update on public.planos_recontato_sinteticos for each row
 execute function prumo_private.cfi01_f02_c04_origin_observe_local();
create trigger cfi01_f02_origin_attempt_insert_update
 after insert or update on public.envios_template_sinteticos for each row
 execute function prumo_private.cfi01_f02_c04_origin_observe_local();
create trigger cfi01_f02_origin_event_insert
 after insert on public.eventos_envio_template_sinteticos for each row
 execute function prumo_private.cfi01_f02_c04_origin_observe_local();

-- S0 read-only local origin judgement; deliberately independent of C04 scheduler.
-- It does not certify a case created before this lab ledger was installed.
create function prumo_private.cfi01_f02_check_origin_local(
 p_shop uuid,p_lead uuid,p_case uuid)
returns text language plpgsql security invoker set search_path='' as $$
declare v_case record;v_n integer;
begin
 if current_user<>'postgres' then
  raise exception 'E04_ORIGIN_READ_DENIED' using errcode='42501';
 end if;
 select c.id,c.ciclo_id,c.criado_em,o.observado_em,
    o.payload_sha256,encode(public.digest(to_jsonb(c)::text,'sha256'),'hex') as current_hash
 into v_case from public.casos_humanos c
 left join prumo_private.cfi01_f02_c04_origin_ledger_local o
  on o.concessionaria_id=c.concessionaria_id and o.entidade_id=c.id
  and o.lead_id=c.lead_id and o.tipo='HUMAN_CASE' and o.etapa='CREATE'
 where c.concessionaria_id=p_shop and c.lead_id=p_lead and c.id=p_case;
 if not found then return 'S0_SCOPE_DENIED';end if;
 if v_case.observado_em is null then return 'MISSING_ORIGIN';end if;
 if v_case.payload_sha256<>v_case.current_hash then return 'MUTATED_ORIGIN';end if;
 select count(*) into v_n from public.planos_recontato_sinteticos p
  where p.concessionaria_id=p_shop and p.lead_id=p_lead
    and p.ciclo_id=v_case.ciclo_id;
 if v_n=0 then return 'NO_LEGACY_CHAIN';end if;
 if v_n>100 then return 'INCOMPLETE_ORIGIN';end if;
 if exists (select 1 from public.planos_recontato_sinteticos p
  where p.concessionaria_id=p_shop and p.lead_id=p_lead
    and p.ciclo_id=v_case.ciclo_id and p.estado<>'cancelado'
 ) then return 'ACTIVE_LEGACY_CHAIN';end if;
 -- Every plan requires exactly one real insert observation and one C08 cancel.
 if exists(
 select 1 from public.planos_recontato_sinteticos p
 left join prumo_private.cfi01_f02_c04_origin_ledger_local created
  on created.concessionaria_id=p.concessionaria_id
  and created.entidade_id=p.id and created.tipo='PLAN'
  and created.etapa='CREATE'
 left join prumo_private.cfi01_f02_c04_origin_ledger_local canceled
  on canceled.concessionaria_id=p.concessionaria_id
  and canceled.entidade_id=p.id and canceled.tipo='PLAN'
  and canceled.etapa='CANCEL'
 where p.concessionaria_id=p_shop and p.lead_id=p_lead
   and p.ciclo_id=v_case.ciclo_id
   and (created.id is null or canceled.id is null
     or created.lead_id<>p_lead or canceled.lead_id<>p_lead)
 ) then return 'MISSING_ORIGIN';end if;
 if exists(
 select 1 from public.planos_recontato_sinteticos p
 join prumo_private.cfi01_f02_c04_origin_ledger_local canceled
  on canceled.concessionaria_id=p.concessionaria_id
  and canceled.entidade_id=p.id and canceled.tipo='PLAN'
  and canceled.etapa='CANCEL'
 where p.concessionaria_id=p_shop and p.lead_id=p_lead
  and p.ciclo_id=v_case.ciclo_id
  and canceled.payload_sha256<>encode(public.digest(to_jsonb(p)::text,'sha256'),'hex')
 ) then return 'MUTATED_ORIGIN';end if;
 -- A late observed creation cannot be passed off as a historic plan by
 -- backdating the mutable public.criado_em column.
 if exists(
 select 1 from public.planos_recontato_sinteticos p
 join prumo_private.cfi01_f02_c04_origin_ledger_local created
  on created.concessionaria_id=p.concessionaria_id
   and created.entidade_id=p.id and created.tipo='PLAN'
   and created.etapa='CREATE'
 join prumo_private.cfi01_f02_c04_origin_ledger_local canceled
  on canceled.concessionaria_id=p.concessionaria_id
   and canceled.entidade_id=p.id and canceled.tipo='PLAN'
   and canceled.etapa='CANCEL'
 where p.concessionaria_id=p_shop and p.lead_id=p_lead and p.ciclo_id=v_case.ciclo_id
 and (created.observado_em>=v_case.observado_em or
      canceled.observado_em<v_case.observado_em or
      created.observado_em>canceled.observado_em or
      p.criado_em>=v_case.criado_em)
 ) then return 'LATE_OBSERVED_SOURCE';end if;
 -- Each attempt requires C04 insert, C08 cancel, native cancellation event,
 -- correct ownership/scope, integrity of final rows and no reserved state.
 select count(*) into v_n
 from public.envios_template_sinteticos e join public.planos_recontato_sinteticos p
  on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 where p.concessionaria_id=p_shop and p.lead_id=p_lead
  and p.ciclo_id=v_case.ciclo_id;
 if v_n=0 or v_n>500 then return 'INCOMPLETE_ORIGIN';end if;
 if exists(
 select 1 from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p
  on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 left join prumo_private.cfi01_f02_c04_origin_ledger_local created
  on created.concessionaria_id=e.concessionaria_id
   and created.entidade_id=e.id and created.tipo='ATTEMPT'
   and created.etapa='CREATE'
 left join prumo_private.cfi01_f02_c04_origin_ledger_local canceled
  on canceled.concessionaria_id=e.concessionaria_id
   and canceled.entidade_id=e.id and canceled.tipo='ATTEMPT'
   and canceled.etapa='CANCEL'
 where p.concessionaria_id=p_shop and p.lead_id=p_lead
  and p.ciclo_id=v_case.ciclo_id
  and (e.estado<>'cancelado' or created.id is null or canceled.id is null
  or created.lead_id<>p_lead or canceled.lead_id<>p_lead)
 ) then return 'INCOMPLETE_ORIGIN';end if;
 if exists(
 select 1 from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p
  on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 join prumo_private.cfi01_f02_c04_origin_ledger_local canceled
  on canceled.concessionaria_id=e.concessionaria_id
  and canceled.entidade_id=e.id and canceled.tipo='ATTEMPT'
  and canceled.etapa='CANCEL'
 where p.concessionaria_id=p_shop and p.lead_id=p_lead
  and p.ciclo_id=v_case.ciclo_id
  and canceled.payload_sha256<>encode(public.digest(to_jsonb(e)::text,'sha256'),'hex')
 ) then return 'MUTATED_ORIGIN';end if;
 if exists(
 select 1 from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p
  on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 join prumo_private.cfi01_f02_c04_origin_ledger_local created
  on created.concessionaria_id=e.concessionaria_id
  and created.entidade_id=e.id and created.tipo='ATTEMPT' and created.etapa='CREATE'
 join prumo_private.cfi01_f02_c04_origin_ledger_local canceled
  on canceled.concessionaria_id=e.concessionaria_id
  and canceled.entidade_id=e.id and canceled.tipo='ATTEMPT' and canceled.etapa='CANCEL'
 where p.concessionaria_id=p_shop and p.lead_id=p_lead
  and p.ciclo_id=v_case.ciclo_id
  and (created.observado_em>=v_case.observado_em or
       canceled.observado_em<v_case.observado_em or
       created.observado_em>canceled.observado_em or
       e.criado_em>=v_case.criado_em)
 ) then return 'LATE_OBSERVED_SOURCE';end if;
 if exists(
 select 1 from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p
  on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 join prumo_private.cfi01_f02_c04_origin_ledger_local created
  on created.concessionaria_id=e.concessionaria_id
  and created.entidade_id=e.id and created.tipo='ATTEMPT' and created.etapa='CREATE'
 where p.concessionaria_id=p_shop and p.lead_id=p_lead
  and p.ciclo_id=v_case.ciclo_id
  and (e.reservado_em is not null or created.estado_novo='reservado'
    or exists(select 1 from prumo_private.cfi01_f02_c04_origin_ledger_local r
      where r.concessionaria_id=e.concessionaria_id
       and r.entidade_id=e.id and r.tipo='ATTEMPT' and r.etapa='RESERVE'))
 ) then return 'RESERVED_EXTERNAL_UNKNOWN';end if;
 if exists(
 select 1 from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p
  on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 left join public.eventos_envio_template_sinteticos ev
  on ev.concessionaria_id=e.concessionaria_id and ev.envio_id=e.id
  and ev.estado_posterior='cancelado'
 left join prumo_private.cfi01_f02_c04_origin_ledger_local o
  on o.concessionaria_id=ev.concessionaria_id
  and o.entidade_id=ev.id and o.tipo='C08_EVENT' and o.etapa='RECORD'
 where p.concessionaria_id=p_shop and p.lead_id=p_lead
  and p.ciclo_id=v_case.ciclo_id
  and (ev.id is null or o.id is null or o.lead_id<>p_lead)
 ) then return 'MISSING_ORIGIN';end if;
 if exists(
 select 1 from public.eventos_envio_template_sinteticos ev
 join public.envios_template_sinteticos e
  on e.id=ev.envio_id and e.concessionaria_id=ev.concessionaria_id
 join public.planos_recontato_sinteticos p
  on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 join prumo_private.cfi01_f02_c04_origin_ledger_local o
  on o.concessionaria_id=ev.concessionaria_id
  and o.entidade_id=ev.id and o.tipo='C08_EVENT' and o.etapa='RECORD'
 where p.concessionaria_id=p_shop and p.lead_id=p_lead
  and p.ciclo_id=v_case.ciclo_id
  and (o.payload_sha256<>encode(public.digest(to_jsonb(ev)::text,'sha256'),'hex')
   or o.observado_em<v_case.observado_em)
 ) then return 'MUTATED_ORIGIN';end if;
 return 'LOCAL_ORIGIN_VERIFIED_AUDIT_ONLY';
end $$;
alter table prumo_private.cfi01_f02_c04_origin_ledger_local enable row level security;
revoke all on prumo_private.cfi01_f02_c04_origin_ledger_local
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
revoke execute on function prumo_private.cfi01_f02_c04_origin_observe_local()
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
revoke execute on function prumo_private.cfi01_f02_c04_origin_append_guard_local()
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
revoke execute on function prumo_private.cfi01_f02_check_origin_local(uuid,uuid,uuid)
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
comment on table prumo_private.cfi01_f02_c04_origin_ledger_local is
 'E04 PG17 local AFTER triggers, observed timestamps and SHA256; NOT provider proof, not immune to postgres superuser and no historical backfill';
