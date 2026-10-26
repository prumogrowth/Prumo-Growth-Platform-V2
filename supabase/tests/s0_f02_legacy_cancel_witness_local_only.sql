-- Disposable PG17 E04 S0-only forensic witness of local C08 cancellation.
-- Not Meta cancellation, outbound authorization, or hosted migration.
create table prumo_private.cfi01_f02_legacy_cancel_witness_local (
 concessionaria_id uuid not null,
 evento_fechamento_id uuid not null,
 gestor_id uuid not null references public.atores(id) on delete restrict,
 sessao_id uuid not null references auth.sessions(id) on delete restrict,
 chave_versao text not null check(chave_versao ~ '^[A-Za-z0-9_.:-]{8,80}$'),
 cadeia_sha256 text not null check(cadeia_sha256 ~ '^[0-9a-f]{64}$'),
 prova_hmac_sha256 text not null check(prova_hmac_sha256 ~ '^[0-9a-f]{64}$'),
 planos_cancelados integer not null check(planos_cancelados between 1 and 100),
 tentativas_canceladas integer not null check(tentativas_canceladas between 1 and 500),
 comprovado_em timestamptz not null default statement_timestamp(),
 tipo text not null default 'C08_LOCAL_CANCELED_AUDIT_ONLY'
   check(tipo='C08_LOCAL_CANCELED_AUDIT_ONLY'),
 primary key(concessionaria_id,evento_fechamento_id),
 foreign key(concessionaria_id,evento_fechamento_id)
  references prumo_private.cfi01_f02_posthuman_intents_local(
    concessionaria_id,evento_fechamento_id) on delete restrict
);
create function prumo_private.cfi01_f02_legacy_witness_guard_local()
returns trigger language plpgsql security invoker set search_path=''
as $$
begin
 if tg_op<>'INSERT' then
  raise exception 'F02_LEGACY_WITNESS_IMMUTABLE_LOCAL' using errcode='42501';
 end if;
 if current_user<>'postgres' or not exists(
  select 1 from prumo_private.cfi01_f02_posthuman_intents_local i
   join auth.sessions s on s.id=new.sessao_id and s.user_id=new.gestor_id
   join public.equipe_prumo_s1 team on team.ator_id=new.gestor_id
    and team.estado='ativo'
   join public.vinculos_papel_escopo v on v.ator_id=new.gestor_id
    and v.concessionaria_id=i.concessionaria_id and v.papel='gestor'
    and v.valido_desde<=statement_timestamp()
    and (v.valido_ate is null or v.valido_ate>statement_timestamp())
   where i.concessionaria_id=new.concessionaria_id
    and i.evento_fechamento_id=new.evento_fechamento_id
    and i.gestor_id=new.gestor_id and i.sessao_id=new.sessao_id
 ) then
  raise exception 'F02_LEGACY_WITNESS_SCOPE_DENIED_LOCAL' using errcode='42501';
 end if;
 return new;
end $$;
create trigger cfi01_f02_legacy_witness_insert
before insert on prumo_private.cfi01_f02_legacy_cancel_witness_local
for each row execute function prumo_private.cfi01_f02_legacy_witness_guard_local();
create trigger cfi01_f02_legacy_witness_immutable
before update or delete on prumo_private.cfi01_f02_legacy_cancel_witness_local
for each row execute function prumo_private.cfi01_f02_legacy_witness_guard_local();
alter table prumo_private.cfi01_f02_legacy_cancel_witness_local enable row level security;
revoke all on prumo_private.cfi01_f02_legacy_cancel_witness_local
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
revoke execute on function prumo_private.cfi01_f02_legacy_witness_guard_local()
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
comment on table prumo_private.cfi01_f02_legacy_cancel_witness_local is
 'E04 offline HMAC seal of physical C08 local cancellation snapshot, never external dispatch cancellation';
