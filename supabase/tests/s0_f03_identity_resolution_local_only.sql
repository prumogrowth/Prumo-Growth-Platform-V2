-- E04 synthetic local-only S0 disposition close: NOT a hosted migration.
-- The third human signer CANNOT be original reviewer or ratifier.
-- This immutable event is a HOLD_ONLY resolution proof, not permission for
-- F03, identity merging, removal of S0/028 pending row, or commercial writes.
create table prumo_private.cfi01_f03_identity_resolution_local (
  id uuid primary key default gen_random_uuid(),
  concessionaria_id uuid not null,
  pendencia_id uuid not null,
  caso_id uuid not null,
  revisao_id uuid not null,
  ratificacao_id uuid not null,
  lead_candidato_id uuid not null,
  gestor_resolvedor_id uuid not null references public.atores(id) on delete restrict,
  sessao_id uuid not null references auth.sessions(id) on delete restrict,
  versao_ciclo bigint not null check(versao_ciclo>0),
  versao_identidade bigint not null check(versao_identidade>0),
  chave_hmac_versao text not null check(chave_hmac_versao ~ '^[A-Za-z0-9_.:-]{8,80}$'),
  pendencia_mac_sha256 text not null check(pendencia_mac_sha256 ~ '^[0-9a-f]{64}$'),
  evidencia_sha256 text not null check(evidencia_sha256 ~ '^[0-9a-f]{64}$'),
  chave_idempotencia text not null check(chave_idempotencia ~ '^[A-Za-z0-9._:-]{8,128}$'),
  resultado text not null check(resultado='NOT_RELATED_HOLD_ONLY'),
  criado_em timestamptz not null default statement_timestamp(),
  foreign key(concessionaria_id,pendencia_id,caso_id)
    references prumo_private.cfi01_f03_identity_ratifications_local
    (concessionaria_id,pendencia_id,caso_id) on delete restrict,
  foreign key(revisao_id)
    references prumo_private.cfi01_f03_identity_human_reviews_local(id) on delete restrict,
  foreign key(ratificacao_id)
    references prumo_private.cfi01_f03_identity_ratifications_local(id) on delete restrict,
  foreign key(concessionaria_id,lead_candidato_id)
    references public.leads_loja(concessionaria_id,id) on delete restrict,
  unique(concessionaria_id,pendencia_id,caso_id)
);

create function prumo_private.cfi01_f03_resolution_guard_local()
returns trigger language plpgsql security invoker set search_path=''
as $resolution$
begin
 if not exists (
   select 1
   from prumo_private.cfi01_f03_identity_ratifications_local t
   join prumo_private.cfi01_f03_identity_human_reviews_local r
     on r.id=t.revisao_id and r.concessionaria_id=t.concessionaria_id
     and r.pendencia_id=t.pendencia_id and r.caso_id=t.caso_id
   join public.casos_humanos h
     on h.concessionaria_id=t.concessionaria_id
     and h.id=t.caso_id and h.lead_id=t.lead_candidato_id
   join public.ciclos_comerciais c
     on c.concessionaria_id=h.concessionaria_id and c.id=h.ciclo_id
     and c.lead_id=h.lead_id
   join prumo_private.cfi01_f03_lead_versions_local v
     on v.concessionaria_id=h.concessionaria_id and v.lead_id=h.lead_id
   join public.atribuicoes_humanas a
     on a.concessionaria_id=r.concessionaria_id and a.id=r.atribuicao_id
     and a.caso_id=h.id and a.operador_id=r.ator_id and a.encerrada_em is null
   join auth.sessions ses
     on ses.id=new.sessao_id and ses.user_id=new.gestor_resolvedor_id
   join public.equipe_prumo_s1 team
     on team.ator_id=new.gestor_resolvedor_id and team.estado='ativo'
   join public.vinculos_papel_escopo role
     on role.ator_id=new.gestor_resolvedor_id
     and role.concessionaria_id=t.concessionaria_id
     and role.papel='gestor'
     and role.valido_desde<=statement_timestamp()
     and (role.valido_ate is null or role.valido_ate>statement_timestamp())
   where t.id=new.ratificacao_id
     and t.concessionaria_id=new.concessionaria_id
     and t.pendencia_id=new.pendencia_id and t.caso_id=new.caso_id
     and t.revisao_id=new.revisao_id
     and t.lead_candidato_id=new.lead_candidato_id
     and r.lead_candidato_id=t.lead_candidato_id
     and r.ator_id<>new.gestor_resolvedor_id
     and t.ratificador_id<>new.gestor_resolvedor_id
     and r.ator_id<>t.ratificador_id
     and r.decisao='CANDIDATE_NOT_RELATED'
     and t.decisao='RATIFY_CANDIDATE_NOT_RELATED'
     and r.versao_identidade=new.versao_identidade
     and t.versao_identidade=new.versao_identidade
     and v.versao_identidade=new.versao_identidade
     and r.versao_ciclo=new.versao_ciclo
     and t.versao_ciclo=new.versao_ciclo
     and c.versao_registro=new.versao_ciclo
 ) then
   raise exception 'F03_RESOLUTION_SCOPE_DENIED_LOCAL' using errcode='42501';
 end if;
 return new;
end $resolution$;
create trigger cfi01_f03_resolution_guard
 before insert on prumo_private.cfi01_f03_identity_resolution_local
 for each row execute function prumo_private.cfi01_f03_resolution_guard_local();

create function prumo_private.cfi01_f03_resolution_immutable_local()
returns trigger language plpgsql security invoker set search_path=''
as $resolution$
begin
 raise exception 'F03_RESOLUTION_IMMUTABLE_LOCAL' using errcode='42501';
end $resolution$;
create trigger cfi01_f03_resolution_immutable
 before update or delete on prumo_private.cfi01_f03_identity_resolution_local
 for each row execute function prumo_private.cfi01_f03_resolution_immutable_local();

alter table prumo_private.cfi01_f03_identity_resolution_local enable row level security;
revoke all on prumo_private.cfi01_f03_identity_resolution_local
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
revoke execute on function prumo_private.cfi01_f03_resolution_guard_local(),
 prumo_private.cfi01_f03_resolution_immutable_local()
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
comment on table prumo_private.cfi01_f03_identity_resolution_local
 is 'S0-only E04 third independent manager close receipt HOLD_ONLY, never F03 grant or pending mutation';
