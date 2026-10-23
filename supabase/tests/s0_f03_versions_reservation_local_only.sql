-- E04 F03 S0-only LOCAL fixture. NOT migration, never hosted Supabase.
-- Independent S0 version sources and append-only pre-commit reservation.
-- This is deliberately NOT a real form/table update or grant to AI.
create table prumo_private.cfi01_f03_catalog_versions_local (
 concessionaria_id uuid primary key references public.concessionarias(id) on delete restrict,
 versao_catalogo bigint not null default 1 check (versao_catalogo>0)
);
create table prumo_private.cfi01_f03_lead_versions_local (
 concessionaria_id uuid not null,
 lead_id uuid not null,
 versao_ficha bigint not null default 1 check (versao_ficha>0),
 versao_identidade bigint not null default 1 check (versao_identidade>0),
 primary key(concessionaria_id,lead_id),
 foreign key(concessionaria_id,lead_id)
  references public.leads_loja(concessionaria_id,id) on delete restrict
);
create table prumo_private.cfi01_f03_case_versions_local (
 concessionaria_id uuid not null,
 caso_id uuid not null,
 lead_id uuid not null,
 versao_caso bigint not null default 1 check (versao_caso>0),
 versao_atribuicao bigint not null default 1 check (versao_atribuicao>0),
 primary key(concessionaria_id,caso_id),
 foreign key(concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,lead_id)
  references public.leads_loja(concessionaria_id,id) on delete restrict
);
create function prumo_private.cfi01_f03_case_versions_scope_local()
returns trigger language plpgsql security invoker set search_path=''
as $scope$ begin
 if not exists (
  select 1 from public.casos_humanos c
  where c.concessionaria_id=new.concessionaria_id
    and c.id=new.caso_id and c.lead_id=new.lead_id
 ) then
  raise exception 'F03_CASE_LEAD_MISMATCH_LOCAL' using errcode='42501';
 end if;
 return new;
end $scope$;
create trigger cfi01_f03_case_versions_scope
 before insert or update on prumo_private.cfi01_f03_case_versions_local
 for each row execute function prumo_private.cfi01_f03_case_versions_scope_local();

create table prumo_private.cfi01_f03_reservations_local (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 evento_fechamento_id uuid not null,
 caso_id uuid not null,
 lead_id uuid not null,
 referencia_requisicao text not null
  check (length(referencia_requisicao) between 8 and 128),
 proposta_sha256 text not null check (proposta_sha256 ~ '^[0-9a-f]{64}$'),
 chave_versao text not null check (chave_versao ~ '^[A-Za-z0-9_.:-]{8,80}$'),
 versao_ficha bigint not null check (versao_ficha>0),
 versao_catalogo bigint not null check (versao_catalogo>0),
 versao_caso bigint not null check (versao_caso>0),
 versao_atribuicao bigint not null check (versao_atribuicao>0),
 versao_identidade bigint not null check (versao_identidade>0),
 criado_em timestamptz not null default statement_timestamp(),
 foreign key (concessionaria_id,evento_fechamento_id)
  references prumo_private.cfi01_f03_content_proofs_local
   (concessionaria_id,evento_fechamento_id) on delete restrict,
 foreign key(concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,lead_id)
  references public.leads_loja(concessionaria_id,id) on delete restrict,
 unique(concessionaria_id,evento_fechamento_id)
);
create function prumo_private.cfi01_f03_reservation_scope_local()
returns trigger language plpgsql security invoker set search_path=''
as $scope$ begin
 if not exists (
  select 1 from prumo_private.cfi01_f03_content_proofs_local p
  join prumo_private.cfi01_f03_history_seals_local s
    on s.concessionaria_id=p.concessionaria_id
    and s.evento_fechamento_id=p.evento_fechamento_id
  where p.concessionaria_id=new.concessionaria_id
    and p.evento_fechamento_id=new.evento_fechamento_id
    and p.caso_id=new.caso_id and s.caso_id=new.caso_id
    and s.lead_id=new.lead_id and p.chave_versao=new.chave_versao
 ) then
  raise exception 'F03_RESERVATION_SCOPE_MISMATCH_LOCAL' using errcode='42501';
 end if;
 return new;
end $scope$;
create trigger cfi01_f03_reservation_scope
 before insert on prumo_private.cfi01_f03_reservations_local
 for each row execute function prumo_private.cfi01_f03_reservation_scope_local();
create function prumo_private.cfi01_f03_reservation_immutable_local()
returns trigger language plpgsql security invoker set search_path=''
as $scope$ begin
 raise exception 'F03_RESERVATION_IMMUTABLE_LOCAL' using errcode='42501';
end $scope$;
create trigger cfi01_f03_reservation_immutable
 before update or delete on prumo_private.cfi01_f03_reservations_local
 for each row execute function prumo_private.cfi01_f03_reservation_immutable_local();

revoke all on prumo_private.cfi01_f03_catalog_versions_local,
 prumo_private.cfi01_f03_lead_versions_local,
 prumo_private.cfi01_f03_case_versions_local,
 prumo_private.cfi01_f03_reservations_local
 from public,anon,authenticated,service_role;
revoke execute on function prumo_private.cfi01_f03_case_versions_scope_local(),
 prumo_private.cfi01_f03_reservation_scope_local(),
 prumo_private.cfi01_f03_reservation_immutable_local()
 from public,anon,authenticated,service_role;
alter table prumo_private.cfi01_f03_catalog_versions_local enable row level security;
alter table prumo_private.cfi01_f03_lead_versions_local enable row level security;
alter table prumo_private.cfi01_f03_case_versions_local enable row level security;
alter table prumo_private.cfi01_f03_reservations_local enable row level security;
comment on table prumo_private.cfi01_f03_reservations_local is
 'Synthetic pre-commit CAS reservation ONLY; never a form write, sale or model grant';
