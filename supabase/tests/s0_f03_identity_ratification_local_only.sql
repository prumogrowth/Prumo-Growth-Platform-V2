-- E04 F03 / S0 identity: second independent HUMAN ratification, local PG17 only.
-- The event is AUDIT_ONLY. It is NOT identity resolution, merging, F03 grant,
-- form write, withdrawal of a pending conflict, or permission to send messages.
create table prumo_private.cfi01_f03_identity_ratifications_local (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 pendencia_id uuid not null,
 caso_id uuid not null,
 revisao_id uuid not null,
 lead_candidato_id uuid not null,
 ratificador_id uuid not null references public.atores(id) on delete restrict,
 sessao_id uuid not null references auth.sessions(id) on delete restrict,
 versao_ciclo bigint not null check(versao_ciclo>0),
 versao_identidade bigint not null check(versao_identidade>0),
 decisao text not null check(decisao='RATIFY_CANDIDATE_NOT_RELATED'),
 evidencia_sha256 text not null check(evidencia_sha256 ~ '^[0-9a-f]{64}$'),
 chave_idempotencia text not null check(chave_idempotencia ~ '^[A-Za-z0-9._:-]{8,128}$'),
 registrado_em timestamptz not null default statement_timestamp(),
 foreign key(concessionaria_id,pendencia_id,caso_id)
  references prumo_private.cfi01_f03_identity_human_reviews_local
  (concessionaria_id,pendencia_id,caso_id) on delete restrict,
 foreign key (revisao_id)
  references prumo_private.cfi01_f03_identity_human_reviews_local(id) on delete restrict,
 foreign key(concessionaria_id,lead_candidato_id)
  references public.leads_loja(concessionaria_id,id) on delete restrict,
 unique(concessionaria_id,pendencia_id,caso_id)
);

create function prumo_private.cfi01_f03_ratification_scope_local()
returns trigger language plpgsql security invoker set search_path=''
as $ratify$
begin
 if not exists (
  select 1
  from prumo_private.cfi01_f03_identity_human_reviews_local r
  join public.casos_humanos h on
   h.concessionaria_id=r.concessionaria_id and h.id=r.caso_id
   and h.lead_id=r.lead_candidato_id
  join public.ciclos_comerciais c on
   c.concessionaria_id=h.concessionaria_id and c.id=h.ciclo_id
   and c.lead_id=h.lead_id
  join public.atribuicoes_humanas a on
   a.concessionaria_id=r.concessionaria_id and a.id=r.atribuicao_id
   and a.caso_id=r.caso_id and a.operador_id=r.ator_id
   and a.encerrada_em is null
  join prumo_private.cfi01_f03_lead_versions_local v on
   v.concessionaria_id=r.concessionaria_id and v.lead_id=r.lead_candidato_id
  join auth.sessions s on s.id=new.sessao_id and s.user_id=new.ratificador_id
  join public.equipe_prumo_s1 e on
   e.ator_id=new.ratificador_id and e.estado='ativo'
  join public.vinculos_papel_escopo role on
   role.ator_id=new.ratificador_id
   and role.concessionaria_id=r.concessionaria_id
   and role.papel='gestor'
   and role.valido_desde<=statement_timestamp()
   and (role.valido_ate is null or role.valido_ate>statement_timestamp())
  where r.id=new.revisao_id
   and r.concessionaria_id=new.concessionaria_id
   and r.pendencia_id=new.pendencia_id
   and r.caso_id=new.caso_id
   and r.lead_candidato_id=new.lead_candidato_id
   and r.ator_id<>new.ratificador_id
   and r.decisao='CANDIDATE_NOT_RELATED'
   and r.versao_ciclo=new.versao_ciclo
   and c.versao_registro=new.versao_ciclo
   and r.versao_identidade=new.versao_identidade
   and v.versao_identidade=new.versao_identidade
 ) then
  raise exception 'F03_RATIFICATION_SCOPE_DENIED_LOCAL' using errcode='42501';
 end if;
 return new;
end $ratify$;
create trigger cfi01_f03_ratification_scope
 before insert on prumo_private.cfi01_f03_identity_ratifications_local
 for each row execute function prumo_private.cfi01_f03_ratification_scope_local();

create function prumo_private.cfi01_f03_ratification_immutable_local()
returns trigger language plpgsql security invoker set search_path=''
as $ratify$
begin
 raise exception 'F03_RATIFICATION_IMMUTABLE_LOCAL' using errcode='42501';
end $ratify$;
create trigger cfi01_f03_ratification_immutable
 before update or delete on prumo_private.cfi01_f03_identity_ratifications_local
 for each row execute function prumo_private.cfi01_f03_ratification_immutable_local();

alter table prumo_private.cfi01_f03_identity_ratifications_local enable row level security;
revoke all on prumo_private.cfi01_f03_identity_ratifications_local
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
revoke execute on function prumo_private.cfi01_f03_ratification_scope_local(),
 prumo_private.cfi01_f03_ratification_immutable_local()
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
comment on table prumo_private.cfi01_f03_identity_ratifications_local
 is 'LOCAL E04 second distinct S1 manager attestation for CANDIDATE_NOT_RELATED; AUDIT_ONLY, never F03 grant';
