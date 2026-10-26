-- CFI-01 LOCAL-ONLY! Explicit manual fixture in disposable PostgreSQL 17.
-- NOT a migration, not connected to production/hosted Supabase and no API.
-- Requires baseline S0 tables and private schema from existing migrations.
create table prumo_private.cfi01_human_closure_events_local (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 caso_id uuid not null,
 ator_id uuid not null,
 sessao_id uuid not null,
 atribuicao_id uuid not null,
 versao_ciclo bigint not null check (versao_ciclo > 0),
 chave_idempotencia text not null check(length(chave_idempotencia) between 8 and 128),
 snapshot_sha256 text not null check(snapshot_sha256 ~ '^[0-9a-f]{64}$'),
 ultima_mensagem_id uuid not null,
 quantidade_mensagens integer not null check(quantidade_mensagens between 1 and 2500),
 registrado_em timestamptz not null default statement_timestamp(),
 foreign key (concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id) on delete restrict,
 foreign key (ator_id) references public.atores(id) on delete restrict,
 foreign key (atribuicao_id)
  references public.atribuicoes_humanas(id) on delete restrict,
 unique(concessionaria_id,caso_id,chave_idempotencia),
 unique(concessionaria_id,caso_id,atribuicao_id,snapshot_sha256)
);
revoke all on prumo_private.cfi01_human_closure_events_local
 from public,anon,authenticated,service_role;
-- Full S0 gateway migration is not part of this minimal PG17 fixture;
-- revoke the optional gateway role if it happens to have been installed.
do $cf$
begin
 if exists(select 1 from pg_catalog.pg_roles where rolname='prumo_s0_gateway') then
  execute 'revoke all on prumo_private.cfi01_human_closure_events_local from prumo_s0_gateway';
 end if;
end $cf$;
comment on table prumo_private.cfi01_human_closure_events_local is
 'DISPOSABLE S0 LOCAL CFI-01; NOT live closure/business status, cannot be used for production';
