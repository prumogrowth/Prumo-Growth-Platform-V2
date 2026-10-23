-- S0/043 WA39: forensics for Meta STATUS tied to actual S0/041-042 fixture bindings.
-- ADDITIVE / OFFLINE ONLY. Neither webhook authentication nor service login.
-- DB fixture writer postgres is NOT an operational M2M identity.
-- Run only in disposable PostgreSQL 17, never in hosted Supabase.
create table prumo_private.meta_status_forense_fixture_s0 (
 id uuid primary key default gen_random_uuid(),
 vinculo_id uuid not null,
 event_ref text not null check(event_ref ~ '^[A-Za-z0-9_.:-]{1,128}$'),
 body_sha256 text not null check(body_sha256 ~ '^[0-9a-f]{64}$'),
 provider_status text not null
   check(provider_status in ('sent','delivered','read','failed')),
 recebido_em timestamptz not null default clock_timestamp(),
 ack_allowed boolean not null default false check(not ack_allowed),
 send_authorized boolean not null default false check(not send_authorized),
 retry_external boolean not null default false check(not retry_external),
 production_authorized boolean not null default false check(not production_authorized),
 delivery_confirmed boolean not null default false check(not delivery_confirmed),
 case_transition_authorized boolean not null default false
   check(not case_transition_authorized),
 definitive_failure_count_increment boolean not null default false
   check(not definitive_failure_count_increment),
 unique(vinculo_id,event_ref,body_sha256)
);
create table prumo_private.meta_status_conflitos_fixture_s0 (
 id uuid primary key default gen_random_uuid(),
 vinculo_id uuid not null,
 event_ref text not null check(event_ref ~ '^[A-Za-z0-9_.:-]{1,128}$'),
 body_sha256 text not null check(body_sha256 ~ '^[0-9a-f]{64}$'),
 reported_kind text not null
   check(reported_kind in ('sent','delivered','read','failed')),
 reason text not null check(reason='LAB_SAME_BODY_DIFFERENT_KIND'),
 observado_em timestamptz not null default clock_timestamp(),
 unique(vinculo_id,event_ref,body_sha256,reported_kind)
);
-- Existing S0/041 regression intentionally exercises TRUNCATE's own
-- immutable-ledger trigger and expects SQLSTATE 42501. A referencing FK
-- would cause PostgreSQL to preempt this existing guard with 0A000. Use
-- an INSERT constraint trigger instead: validate+lock the immutable
-- source binding, preserving old regression and denying orphan records.
create function prumo_private.validar_meta_status_vinculo_fixture_s0()
returns trigger language plpgsql security invoker set search_path='' as $wa39_fk$
begin
 perform 1 from prumo_private.meta_vinculos_tentativa_fixture_s0
  where id=new.vinculo_id for key share;
 if not found then
  raise exception 'UNKNOWN_META_STATUS_BINDING' using errcode='23503';
 end if;
 return new;
end $wa39_fk$;
create trigger meta_status_forense_validate_binding_s0
 before insert on prumo_private.meta_status_forense_fixture_s0
 for each row execute function prumo_private.validar_meta_status_vinculo_fixture_s0();
create trigger meta_status_conflitos_validate_binding_s0
 before insert on prumo_private.meta_status_conflitos_fixture_s0
 for each row execute function prumo_private.validar_meta_status_vinculo_fixture_s0();
revoke all on function prumo_private.validar_meta_status_vinculo_fixture_s0()
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;

-- Preserve all evidence, including after opt-out, without mutating original rows.
create trigger meta_status_forense_block_update_delete_s0
 before update or delete on prumo_private.meta_status_forense_fixture_s0
 for each row execute function prumo_private.bloquear_mutacao_meta_vinculo_fixture_s0();
create trigger meta_status_conflitos_block_update_delete_s0
 before update or delete on prumo_private.meta_status_conflitos_fixture_s0
 for each row execute function prumo_private.bloquear_mutacao_meta_vinculo_fixture_s0();

alter table prumo_private.meta_status_forense_fixture_s0 enable row level security;
alter table prumo_private.meta_status_conflitos_fixture_s0 enable row level security;
revoke all on prumo_private.meta_status_forense_fixture_s0,
 prumo_private.meta_status_conflitos_fixture_s0
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;

-- Resolve the caller-provided *candidate* against exact S0-owned bindings.
-- No untrusted tenant, channel ownership, recipient or wamid is authoritative.
-- Explicitly not a complete Meta HMAC-to-S0 authentication chain.
create function prumo_private.archivar_status_meta_tecnico_fixture_s0(
 p_app_tech text,p_waba_tech text,p_phone_tech text,
 p_canal uuid,p_intencao uuid,p_attempt text,p_correlation text,
 p_recipient text,p_wamid text,p_event_ref text,p_kind text,p_body_sha256 text
) returns jsonb language plpgsql security invoker set search_path='' as $wa39$
declare v_binding uuid;v_status text;v_prior_kind text;
 v_seen boolean;v_existing uuid;v_cancelled boolean;v_outcome text;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';
 end if;
 if p_app_tech is null or p_app_tech !~ '^[0-9]{5,25}$'
  or p_waba_tech is null or p_waba_tech !~ '^[0-9]{5,25}$'
  or p_phone_tech is null or p_phone_tech !~ '^[0-9]{5,25}$'
  or p_canal is null or p_intencao is null
  or p_attempt is null or p_attempt !~ '^[A-Za-z0-9_.:-]{1,128}$'
  or p_correlation is null or p_correlation !~ '^[A-Za-z0-9_.:-]{1,128}$'
  or p_recipient is null or p_recipient !~ '^[0-9]{8,15}$'
  or p_wamid is null or p_wamid !~ '^wamid\.[A-Za-z0-9+/_=:.-]+$'
  or length(p_wamid) not between 7 and 1030
  or p_event_ref is null or p_event_ref !~ '^[A-Za-z0-9_.:-]{1,128}$'
  or p_kind is null or p_kind not in ('sent','delivered','read','failed')
  or p_body_sha256 is null or p_body_sha256 !~ '^[0-9a-f]{64}$'
 then raise exception 'INVALID_STATUS_FIXTURE' using errcode='22023';end if;

 select b.id,o.estado into v_binding,v_status
 from prumo_private.meta_vinculos_tentativa_fixture_s0 b
 join prumo_private.meta_apps_fixture_s0 a
   on a.app_ref=b.app_ref and a.concessionaria_id=b.concessionaria_id
 join prumo_private.meta_canais_fixture_s0 m
   on m.app_ref=b.app_ref and m.concessionaria_id=b.concessionaria_id
   and m.canal_id=b.canal_id and m.waba_ref=b.waba_ref
   and m.phone_number_ref=b.phone_number_ref
 join prumo_private.outbox_intencoes_s0 o
   on o.concessionaria_id=b.concessionaria_id
   and o.canal_id=b.canal_id and o.id=b.intencao_id
 where a.app_technical_ref=p_app_tech
   and m.waba_technical_ref=p_waba_tech
   and m.phone_technical_ref=p_phone_tech
   and b.canal_id=p_canal and b.intencao_id=p_intencao
   and b.attempt_ref=p_attempt and b.correlation_ref=p_correlation
   and b.recipient_verified=p_recipient and b.provider_message_id=p_wamid
 for share of a,m,b,o;
 if not found then
  return pg_catalog.jsonb_build_object('outcome','LAB_SCOPE_DENIED',
   'ack_allowed',false,'send_authorized',false,'retry_external',false,
   'production_authorized',false,'delivery_confirmed',false,
   'case_transition_authorized',false,'definitive_failure_count_increment',false);
 end if;

 -- Serializes both hash variants and kind conflicts for same binding/event
 -- before checking prior observations. No cross-shop or sender-wide locking.
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended('wa39:'||v_binding::text||':'||p_event_ref,39));
 select id,provider_status into v_existing,v_prior_kind
 from prumo_private.meta_status_forense_fixture_s0
 where vinculo_id=v_binding and event_ref=p_event_ref and body_sha256=p_body_sha256;
 if found then
  if v_prior_kind=p_kind then
   v_outcome:='LAB_EXACT_BODY_REPLAY';
  else
   insert into prumo_private.meta_status_conflitos_fixture_s0(
    vinculo_id,event_ref,body_sha256,reported_kind,reason)
   values(v_binding,p_event_ref,p_body_sha256,p_kind,'LAB_SAME_BODY_DIFFERENT_KIND')
   on conflict do nothing;
   v_outcome:='LAB_KIND_CONFLICT_QUARANTINED';
  end if;
 else
  select exists(select 1 from prumo_private.meta_status_forense_fixture_s0
   where vinculo_id=v_binding and event_ref=p_event_ref) into v_seen;
  insert into prumo_private.meta_status_forense_fixture_s0(
   vinculo_id,event_ref,body_sha256,provider_status)
  values(v_binding,p_event_ref,p_body_sha256,p_kind);
  if v_seen then
   v_outcome:='LAB_BODY_VARIANT_QUARANTINED';
  elsif v_status='CANCELADA' then
   v_outcome:='LAB_LATE_UNVERIFIED';
  else
   v_outcome:='LAB_OBSERVED_UNVERIFIED';
  end if;
 end if;
 return pg_catalog.jsonb_build_object('outcome',v_outcome,
  'ack_allowed',false,'send_authorized',false,'retry_external',false,
  'production_authorized',false,'delivery_confirmed',false,
  'case_transition_authorized',false,'definitive_failure_count_increment',false);
end $wa39$;

-- Do not expose even a synthetic SQL function to HTTP REST or service_role.
revoke all on function prumo_private.archivar_status_meta_tecnico_fixture_s0(
 text,text,text,uuid,uuid,text,text,text,text,text,text,text)
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
