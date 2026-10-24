-- E04/S0-F03 disposable PostgreSQL 17 fixture only. Not a hosted migration.
-- An authenticated S0/S1 human can record a disposition of a candidate
-- ambiguous identity. This is an immutable REVIEW ONLY fact, NEVER a grant
-- to F03, a lead merge or a business/form update.
-- S0/028 has a primary-key-only pending table: add explicit composite
-- uniqueness for the scope-safe FK; no user data or rows are modified.
create unique index cfi01_f03_identity_pending_scope_local
 on prumo_private.pendencias_identidade_s0(concessionaria_id,id);

create table prumo_private.cfi01_f03_identity_human_reviews_local (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 pendencia_id uuid not null,
 caso_id uuid not null,
 lead_candidato_id uuid not null,
 atribuicao_id uuid not null,
 ator_id uuid not null references public.atores(id) on delete restrict,
 sessao_id uuid not null references auth.sessions(id) on delete restrict,
 versao_ciclo bigint not null check(versao_ciclo>0),
 versao_identidade bigint not null check(versao_identidade>0),
 decisao text not null check(decisao in
  ('ESCALATE_REVIEW','CANDIDATE_POSSIBLY_RELATED','CANDIDATE_NOT_RELATED')),
 evidencia_sha256 text not null check(evidencia_sha256 ~ '^[0-9a-f]{64}$'),
 chave_idempotencia text not null check(chave_idempotencia ~ '^[A-Za-z0-9._:-]{8,128}$'),
 registrado_em timestamptz not null default statement_timestamp(),
 foreign key(concessionaria_id,caso_id)
   references public.casos_humanos(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,lead_candidato_id)
   references public.leads_loja(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,pendencia_id)
   references prumo_private.pendencias_identidade_s0(concessionaria_id,id)
   on delete restrict,
 unique(concessionaria_id,pendencia_id,caso_id)
);
create function prumo_private.cfi01_f03_identity_human_scope_local()
returns trigger language plpgsql security invoker set search_path=''
as $review$
begin
 if not exists(
  select 1 from public.casos_humanos h
  join public.ciclos_comerciais c
    on c.concessionaria_id=h.concessionaria_id and c.id=h.ciclo_id
   and c.lead_id=h.lead_id
  join public.atribuicoes_humanas a
    on a.concessionaria_id=h.concessionaria_id and a.caso_id=h.id
  join prumo_private.cfi01_f03_lead_versions_local v
    on v.concessionaria_id=h.concessionaria_id and v.lead_id=h.lead_id
  join prumo_private.pendencias_identidade_s0 p
    on p.concessionaria_id=h.concessionaria_id
   and p.id=new.pendencia_id
  join public.leads_loja l
    on l.concessionaria_id=h.concessionaria_id and l.id=h.lead_id
  where h.concessionaria_id=new.concessionaria_id
   and h.id=new.caso_id and h.lead_id=new.lead_candidato_id
   and a.id=new.atribuicao_id and a.operador_id=new.ator_id
   and a.encerrada_em is null
   and c.versao_registro=new.versao_ciclo
   and v.versao_identidade=new.versao_identidade
   and (
    p.telefone_sintetico=l.telefone_cliente_normalizado
    or (prumo_private.chave_variante_br_s0(p.telefone_sintetico) is not null
       and prumo_private.chave_variante_br_s0(p.telefone_sintetico)
        =prumo_private.chave_variante_br_s0(l.telefone_cliente_normalizado))
    or exists (
     select 1 from prumo_private.aliases_identidade_s0 al
     where al.concessionaria_id=l.concessionaria_id and al.lead_id=l.id
      and (al.numero_sintetico=p.telefone_sintetico
        or (prumo_private.chave_variante_br_s0(p.telefone_sintetico) is not null
         and prumo_private.chave_variante_br_s0(p.telefone_sintetico)
          =prumo_private.chave_variante_br_s0(al.numero_sintetico)))
    )
   )
 ) then
  raise exception 'F03_HUMAN_REVIEW_SCOPE_INVALID_LOCAL' using errcode='42501';
 end if;
 if not exists(select 1 from auth.sessions s
  where s.id=new.sessao_id and s.user_id=new.ator_id) then
  raise exception 'F03_HUMAN_REVIEW_SESSION_INVALID_LOCAL' using errcode='42501';
 end if;
 return new;
end $review$;
create trigger cfi01_f03_identity_human_scope
 before insert on prumo_private.cfi01_f03_identity_human_reviews_local
 for each row execute function prumo_private.cfi01_f03_identity_human_scope_local();

create function prumo_private.cfi01_f03_identity_human_immutable_local()
returns trigger language plpgsql security invoker set search_path=''
as $review$
begin
 raise exception 'F03_HUMAN_REVIEW_APPEND_ONLY_LOCAL' using errcode='42501';
end $review$;
create trigger cfi01_f03_identity_human_immutable
 before update or delete on prumo_private.cfi01_f03_identity_human_reviews_local
 for each row execute function prumo_private.cfi01_f03_identity_human_immutable_local();

alter table prumo_private.cfi01_f03_identity_human_reviews_local enable row level security;
revoke all on prumo_private.cfi01_f03_identity_human_reviews_local
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
revoke execute on function prumo_private.cfi01_f03_identity_human_scope_local(),
 prumo_private.cfi01_f03_identity_human_immutable_local()
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
comment on table prumo_private.cfi01_f03_identity_human_reviews_local
 is 'Disposable S0/S1 authenticated human REVIEW only; does NOT resolve pending or authorize F03';
