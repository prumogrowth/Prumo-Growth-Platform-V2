-- F03 S0: LAB ONLY, disposable PG17, never a hosted migration.
-- Apply only after the existing CFI01 human closure table local fixture.
-- Stores immutable message *membership metadata*; no customer content.
create table prumo_private.cfi01_f03_history_seals_local (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 evento_fechamento_id uuid not null references prumo_private.cfi01_human_closure_events_local(id) on delete restrict,
 caso_id uuid not null,
 lead_id uuid not null,
 versao_ciclo bigint not null check (versao_ciclo>0),
 snapshot_caso_sha256 text not null check (snapshot_caso_sha256 ~ '^[0-9a-f]{64}$'),
 ultima_mensagem_id uuid not null,
 corte_em timestamptz not null,
 quantidade_mensagens integer not null check (quantidade_mensagens between 1 and 10000),
 quantidade_casos integer not null check (quantidade_casos between 1 and 10000),
 metadados_sha256 text not null check (metadados_sha256 ~ '^[0-9a-f]{64}$'),
 metadados_json jsonb not null check (jsonb_typeof(metadados_json)='array'),
 selado_em timestamptz not null default statement_timestamp(),
 foreign key (concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id) on delete restrict,
 foreign key (concessionaria_id,lead_id)
  references public.leads_loja(concessionaria_id,id) on delete restrict,
 unique(concessionaria_id,evento_fechamento_id)
);
-- Enforce that closure, store, case, lead, watermark and cutoff belong
-- together in trusted S0 rows. No browser/model-supplied case identity.
create function prumo_private.cfi01_f03_seal_scope_guard_local()
returns trigger language plpgsql security invoker set search_path=''
as $ begin
 if not exists (
  select 1 from prumo_private.cfi01_human_closure_events_local e
  join public.casos_humanos h on h.id=e.caso_id
   and h.concessionaria_id=e.concessionaria_id
  where e.id=new.evento_fechamento_id
   and e.concessionaria_id=new.concessionaria_id
   and e.caso_id=new.caso_id and h.lead_id=new.lead_id
   and e.versao_ciclo=new.versao_ciclo
   and e.snapshot_sha256=new.snapshot_caso_sha256
   and e.ultima_mensagem_id=new.ultima_mensagem_id
   and e.registrado_em=new.corte_em
   and e.quantidade_mensagens<=new.quantidade_mensagens
 ) then
  raise exception 'F03_MANIFEST_SCOPE_MISMATCH_LOCAL' using errcode='42501';
 end if;
 return new;
end $;
create trigger cfi01_f03_history_seal_scope_guard
 before insert on prumo_private.cfi01_f03_history_seals_local
 for each row execute function prumo_private.cfi01_f03_seal_scope_guard_local();
-- Do not permit later mutation or deletion even through a casually granted role.
create function prumo_private.cfi01_f03_seal_immutable_local()
returns trigger language plpgsql security invoker set search_path=''
as $$ begin
 raise exception 'F03_MANIFEST_IMMUTABLE_LOCAL' using errcode='42501';
end $$;
create trigger cfi01_f03_history_seal_no_mutation
 before update or delete on prumo_private.cfi01_f03_history_seals_local
 for each row execute function prumo_private.cfi01_f03_seal_immutable_local();
revoke all on prumo_private.cfi01_f03_history_seals_local
 from public,anon,authenticated,service_role;
revoke execute on function prumo_private.cfi01_f03_seal_immutable_local()
 from public,anon,authenticated,service_role;
revoke execute on function prumo_private.cfi01_f03_seal_scope_guard_local()
 from public,anon,authenticated,service_role;
alter table prumo_private.cfi01_f03_history_seals_local enable row level security;
comment on table prumo_private.cfi01_f03_history_seals_local is
 'DISPOSABLE PG S0 F03 history membership only; NOT content, authority, or production';
