-- E04 synthetic-only message modality evidence; never a hosted migration.
-- A media attachment cannot be upgraded to textual proof by a model assertion.
create table prumo_private.cfi01_f03_message_modalities_local (
 mensagem_id uuid primary key references public.mensagens(id) on delete restrict,
 concessionaria_id uuid not null,
 tipo text not null check (tipo in ('TEXT','AUDIO','IMAGE','VIDEO','DOCUMENT','UNKNOWN')),
 estado text not null check (
   (tipo='TEXT' and estado='NATIVE_TEXT_FIXTURE') or
   (tipo<>'TEXT' and estado='MEDIA_UNVERIFIED')),
 anexo_sha256 text check (
   anexo_sha256 is null or anexo_sha256 ~ '^[0-9a-f]{64}$'),
 classificado_em timestamptz not null default statement_timestamp(),
 unique (concessionaria_id,mensagem_id)
);
create function prumo_private.cfi01_f03_modality_scope_local()
returns trigger language plpgsql security invoker set search_path=''
as $$
begin
 if tg_op <> 'INSERT' then
   raise exception 'S0_F03_MODALITY_IMMUTABLE_LOCAL' using errcode='42501';
 end if;
 if current_user <> 'postgres' or not exists (
   select 1 from public.mensagens m
   where m.id=new.mensagem_id
    and m.concessionaria_id=new.concessionaria_id
 ) then
   raise exception 'S0_F03_MODALITY_SCOPE_DENIED_LOCAL' using errcode='42501';
 end if;
 return new;
end $$;
create trigger cfi01_f03_modality_insert_guard
before insert on prumo_private.cfi01_f03_message_modalities_local
for each row execute function prumo_private.cfi01_f03_modality_scope_local();
create trigger cfi01_f03_modality_immutable_guard
before update or delete on prumo_private.cfi01_f03_message_modalities_local
for each row execute function prumo_private.cfi01_f03_modality_scope_local();
alter table prumo_private.cfi01_f03_message_modalities_local enable row level security;
revoke all on prumo_private.cfi01_f03_message_modalities_local
from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
revoke execute on function prumo_private.cfi01_f03_modality_scope_local()
from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
comment on table prumo_private.cfi01_f03_message_modalities_local is
 'E04 PG17-only immutable S0 source modality fixture; never a media processing claim';
