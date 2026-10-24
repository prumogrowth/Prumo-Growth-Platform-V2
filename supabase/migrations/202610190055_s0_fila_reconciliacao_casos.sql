-- I56: integrate external S0 case creation with canonical I54 queue and audit.
begin;
do $fix$
declare c record;n int;
begin
 select count(*) into n from pg_catalog.pg_constraint x
 where x.conrelid='prumo_private.s0_fila_humana'::regclass and x.contype='c'
 and pg_catalog.pg_get_constraintdef(x.oid) like '%pendente%'
 and pg_catalog.pg_get_constraintdef(x.oid) like '%atribuido%';
 if n<>2 then raise exception 'I56_QUEUE_CONSTRAINTS_CHANGED: %',n;end if;
 for c in select x.conname from pg_catalog.pg_constraint x
 where x.conrelid='prumo_private.s0_fila_humana'::regclass and x.contype='c'
 and pg_catalog.pg_get_constraintdef(x.oid) like '%pendente%'
 and pg_catalog.pg_get_constraintdef(x.oid) like '%atribuido%'
 loop execute pg_catalog.format('alter table prumo_private.s0_fila_humana drop constraint %I',c.conname);end loop;
 select count(*) into n from pg_catalog.pg_constraint x
 where x.conrelid='prumo_private.s0_fila_humana_eventos'::regclass and x.contype='c'
 and pg_catalog.pg_get_constraintdef(x.oid) like '%PENDENTE%'
 and pg_catalog.pg_get_constraintdef(x.oid) like '%DISTRIBUIDO%';
 if n<>1 then raise exception 'I56_EVENT_CONSTRAINT_CHANGED: %',n;end if;
 for c in select x.conname from pg_catalog.pg_constraint x
 where x.conrelid='prumo_private.s0_fila_humana_eventos'::regclass and x.contype='c'
 and pg_catalog.pg_get_constraintdef(x.oid) like '%PENDENTE%'
 and pg_catalog.pg_get_constraintdef(x.oid) like '%DISTRIBUIDO%'
 loop execute pg_catalog.format('alter table prumo_private.s0_fila_humana_eventos drop constraint %I',c.conname);end loop;
end $fix$;
alter table prumo_private.s0_fila_humana
 add constraint s0_fila_estado_i56 check(estado in ('pendente','atribuido','reconciliado')),
 add constraint s0_fila_integridade_i56 check(
 (estado='pendente' and caso_id is null and atribuicao_id is null) or
 (estado='atribuido' and caso_id is not null and atribuicao_id is not null) or
 (estado='reconciliado' and caso_id is not null and atribuicao_id is null));
alter table prumo_private.s0_fila_humana_eventos
 add constraint s0_fila_evento_i56 check(resultado in
 ('PENDENTE','ASSUMIDO','DISTRIBUIDO','RECONCILIADO'));

-- Every S0 case producer uses the lead lock already used by I54 claim/dispatch.
-- Also refuse a second human case for the SAME commercial cycle.
create function prumo_private.s0_caso_lead_lock_i56()
returns trigger language plpgsql security definer set search_path='' as $f$
begin
 perform 1 from public.leads_loja l
 where l.id=new.lead_id and l.concessionaria_id=new.concessionaria_id for update of l;
 if not found then raise exception 'I56_LEAD_NOT_FOUND' using errcode='23503';end if;
 if exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=new.concessionaria_id and h.ciclo_id=new.ciclo_id)
 then raise exception 'I56_DUPLICATE_CYCLE_CASE' using errcode='23505';end if;
 return new;
end $f$;
create trigger s0_caso_lead_lock_i56 before insert on public.casos_humanos
 for each row execute function prumo_private.s0_caso_lead_lock_i56();

-- Deferring reconciliation until the end of the transaction is essential:
-- an I54-origin case is already 'atribuido' then, and is NOT made obsolete.
create function prumo_private.s0_fila_reconciliar_i56()
returns trigger language plpgsql security definer set search_path='' as $f$
declare q record;
begin
 for q in select f.concessionaria_id,f.lead_id,f.ciclo_id,f.versao
  from prumo_private.s0_fila_humana f
  where f.concessionaria_id=new.concessionaria_id and f.lead_id=new.lead_id
  and f.estado='pendente' order by f.ciclo_id for update of f
 loop
  update prumo_private.s0_fila_humana set estado='reconciliado',
   caso_id=new.id,atribuicao_id=null,versao=q.versao+1,
   atualizado_em=pg_catalog.clock_timestamp()
  where concessionaria_id=q.concessionaria_id and ciclo_id=q.ciclo_id
  and estado='pendente' and versao=q.versao;
  if not found then raise exception 'I56_RECONCILIATION_CONFLICT' using errcode='40001';end if;
  insert into prumo_private.s0_fila_humana_eventos(
   concessionaria_id,lead_id,ciclo_id,versao_anterior,versao_nova,resultado,caso_id)
  values(q.concessionaria_id,q.lead_id,q.ciclo_id,q.versao,q.versao+1,
   'RECONCILIADO',new.id);
 end loop;
 return null;
end $f$;
create constraint trigger s0_fila_reconciliar_i56 after insert on public.casos_humanos
 deferrable initially deferred for each row
 execute function prumo_private.s0_fila_reconciliar_i56();

-- Fix the complementary race: signal producer must lock lead before
-- checking whether a case exists, not after that check.
create or replace function prumo_private.s0_fila_registrar_sinal()
returns trigger language plpgsql security invoker set search_path='' as $f$
begin
 if current_user<>'postgres' then
  raise exception 'S0_FILA_EXECUTOR_INTERNO' using errcode='42501';end if;
 if new.status_comercial not in
  ('em atendimento pelo operador','cadastro enviado ao operador') then return new;end if;
 if tg_op='UPDATE' and new.status_comercial is not distinct from old.status_comercial
 then return new;end if;
 perform 1 from public.leads_loja l where l.concessionaria_id=new.concessionaria_id
  and l.id=new.lead_id for update of l;
 if not found then raise exception 'I56_LEAD_NOT_FOUND' using errcode='23503';end if;
 if exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=new.concessionaria_id and h.lead_id=new.lead_id)
 then return new;end if;
 insert into prumo_private.s0_fila_humana(concessionaria_id,lead_id,ciclo_id)
 values(new.concessionaria_id,new.lead_id,new.id)
 on conflict(concessionaria_id,ciclo_id) do nothing;
 if found then
  insert into prumo_private.s0_fila_humana_eventos(
   concessionaria_id,lead_id,ciclo_id,versao_nova,resultado)
  values(new.concessionaria_id,new.lead_id,new.id,1,'PENDENTE');
 end if;
 return new;
end $f$;

-- Deterministic migration backfill for any pre-existing orphaned pendencies.
do $backfill$
declare q record;v_case uuid;
begin
 for q in select * from prumo_private.s0_fila_humana f
  where f.estado='pendente' order by f.concessionaria_id,f.lead_id,f.ciclo_id
 loop
  select h.id into v_case from public.casos_humanos h
  where h.concessionaria_id=q.concessionaria_id and h.lead_id=q.lead_id
  order by h.criado_em,h.id limit 1;
  if v_case is not null then
   update prumo_private.s0_fila_humana set estado='reconciliado',
    caso_id=v_case,versao=q.versao+1,atualizado_em=pg_catalog.clock_timestamp()
   where concessionaria_id=q.concessionaria_id and ciclo_id=q.ciclo_id
    and estado='pendente' and versao=q.versao;
   insert into prumo_private.s0_fila_humana_eventos(
    concessionaria_id,lead_id,ciclo_id,versao_anterior,versao_nova,
    resultado,caso_id)
   values(q.concessionaria_id,q.lead_id,q.ciclo_id,q.versao,q.versao+1,
   'RECONCILIADO',v_case);
  end if;
 end loop;
end $backfill$;
revoke all on function prumo_private.s0_caso_lead_lock_i56(),
 prumo_private.s0_fila_reconciliar_i56()
 from public,anon,authenticated,service_role;
commit;
