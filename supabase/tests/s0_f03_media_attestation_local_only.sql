-- E04 disposable PG17 S0-only MEDIA ATTESTATION CONTRACT. Never hosted.
-- This attests digests/lineage for a fixture, NOT the truth of speech, consent
-- to process media or permission to provide media/transcript to an LLM.
create table prumo_private.cfi01_f03_media_attestations_local (
 concessionaria_id uuid not null,
 evento_fechamento_id uuid not null,
 caso_id uuid not null,
 mensagem_id uuid not null,
 proposito text not null
   check (proposito='F03_POST_HUMAN_REVIEW_SYNTHETIC'),
 chave_versao text not null check (chave_versao ~ '^[A-Za-z0-9_.:-]{8,80}$'),
 anexo_sha256 text not null check (anexo_sha256 ~ '^[0-9a-f]{64}$'),
 transcricao_sha256 text not null check (transcricao_sha256 ~ '^[0-9a-f]{64}$'),
 prova_hmac_sha256 text not null check (prova_hmac_sha256 ~ '^[0-9a-f]{64}$'),
 valido_ate timestamptz not null,
 atestado_em timestamptz not null default statement_timestamp(),
 primary key (concessionaria_id,evento_fechamento_id,mensagem_id),
 foreign key(concessionaria_id,evento_fechamento_id)
  references prumo_private.cfi01_f03_history_seals_local(
   concessionaria_id,evento_fechamento_id) on delete restrict,
 foreign key(concessionaria_id,mensagem_id)
  references prumo_private.cfi01_f03_message_modalities_local(
   concessionaria_id,mensagem_id) on delete restrict,
 check (valido_ate>atestado_em)
);
create function prumo_private.cfi01_f03_media_attestation_guard_local()
returns trigger language plpgsql security invoker set search_path=''
as $$
begin
 if tg_op<>'INSERT' then
  raise exception 'S0_F03_MEDIA_PROOF_IMMUTABLE_LOCAL' using errcode='42501';
 end if;
 if current_user<>'postgres' or
  not exists (
   select 1 from prumo_private.cfi01_f03_message_modalities_local t
   join public.mensagens m on m.id=t.mensagem_id
    and m.concessionaria_id=t.concessionaria_id
   join public.conversas v on v.id=m.conversa_id
    and v.concessionaria_id=m.concessionaria_id
   join prumo_private.cfi01_human_closure_events_local e
    on e.id=new.evento_fechamento_id
    and e.concessionaria_id=new.concessionaria_id
    and e.caso_id=new.caso_id
   join public.casos_humanos h on h.id=e.caso_id
    and h.concessionaria_id=e.concessionaria_id
   where t.concessionaria_id=new.concessionaria_id
    and t.mensagem_id=new.mensagem_id
    and t.tipo in ('AUDIO','DOCUMENT')
    and t.estado='MEDIA_UNVERIFIED'
    and t.anexo_sha256=new.anexo_sha256
    and v.lead_id=h.lead_id
    and m.criada_em<=e.registrado_em
  ) then
  raise exception 'S0_F03_MEDIA_PROOF_SCOPE_DENIED_LOCAL' using errcode='42501';
 end if;
 return new;
end $$;
create trigger cfi01_f03_media_attestation_insert_guard
before insert on prumo_private.cfi01_f03_media_attestations_local
for each row execute function prumo_private.cfi01_f03_media_attestation_guard_local();
create trigger cfi01_f03_media_attestation_immutable_guard
before update or delete on prumo_private.cfi01_f03_media_attestations_local
for each row execute function prumo_private.cfi01_f03_media_attestation_guard_local();
alter table prumo_private.cfi01_f03_media_attestations_local enable row level security;
revoke all on prumo_private.cfi01_f03_media_attestations_local
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
revoke execute on function prumo_private.cfi01_f03_media_attestation_guard_local()
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
comment on table prumo_private.cfi01_f03_media_attestations_local is
 'E04 PG17 disposable-only immutable synthetic media digest/lineage HMAC; no raw media, transcription or live access';
