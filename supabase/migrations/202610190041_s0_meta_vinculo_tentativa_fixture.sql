-- S0/041 (WA-14): OFFLINE PostgreSQL-only attempt <-> scoped wamid binding.
-- NOT a live Graph sender, Meta ACK, trusted service authentication, or
-- proof of Graph transport. Existing S0/029 outbox remains BLOCKED.
-- Add only to ephemeral/local S0 schema, after S0/030 and S0/040.
alter table prumo_private.meta_canais_fixture_s0
  add constraint meta_canais_fixture_full_scope_uniq_s0
  unique(app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref);

alter table prumo_private.outbox_intencoes_s0
  add constraint outbox_intencoes_scope_id_uniq_s0
  unique(concessionaria_id,canal_id,id);

create table prumo_private.meta_vinculos_tentativa_fixture_s0 (
  id uuid primary key default gen_random_uuid(),
  app_ref text not null,
  concessionaria_id uuid not null,
  canal_id uuid not null,
  waba_ref text not null,
  phone_number_ref text not null,
  intencao_id uuid not null,
  attempt_ref text not null check(attempt_ref ~ '^[A-Za-z0-9_.:-]{1,128}$'),
  correlation_ref text not null check(correlation_ref ~ '^[A-Za-z0-9_.:-]{1,128}$'),
  recipient_verified text not null check(recipient_verified ~ '^[0-9]{8,15}$'),
  provider_message_id text not null
    check(provider_message_id ~ '^wamid\.[A-Za-z0-9+/_=:.-]{1,1024}$'),
  graph_http_status integer not null check(graph_http_status between 200 and 299),
  registrado_em timestamptz not null default clock_timestamp(),
  constraint meta_vinculo_scope_fk_s0 foreign key
    (app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref)
    references prumo_private.meta_canais_fixture_s0
    (app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref)
    on update restrict on delete restrict,
  constraint meta_vinculo_intencao_fk_s0 foreign key
    (concessionaria_id,canal_id,intencao_id)
    references prumo_private.outbox_intencoes_s0
    (concessionaria_id,canal_id,id)
    on update restrict on delete restrict,
  constraint meta_vinculo_attempt_uniq_s0
    unique(app_ref,concessionaria_id,attempt_ref),
  constraint meta_vinculo_wamid_uniq_s0
    unique(app_ref,waba_ref,phone_number_ref,provider_message_id)
);
alter table prumo_private.meta_vinculos_tentativa_fixture_s0 enable row level security;
revoke all on prumo_private.meta_vinculos_tentativa_fixture_s0
  from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;

-- One invocation is one local PostgreSQL transaction; the caller must
-- separately decide whether an API response was authentic/accepted.
-- Never infer Meta delivery, commercial progress or permission to transmit.
create function prumo_private.registrar_vinculo_meta_fixture_s0(
  p_app text,p_canal uuid,p_intencao uuid,p_attempt text,p_correlation text,
  p_recipient text,p_wamid text,p_http_status integer
) returns jsonb language plpgsql security invoker set search_path='' as $wa14$
declare v_scope record; v_new uuid; v_attempt record; v_message record;
begin
  if current_user <> 'postgres' then
    raise exception 'INTERNAL_ONLY' using errcode='42501';
  end if;
  if p_app is null or p_canal is null or p_intencao is null
    or p_attempt is null or p_attempt !~ '^[A-Za-z0-9_.:-]{1,128}$'
    or p_correlation is null or p_correlation !~ '^[A-Za-z0-9_.:-]{1,128}$'
    or p_recipient is null or p_recipient !~ '^[0-9]{8,15}$'
    or p_wamid is null or p_wamid !~ '^wamid\.[A-Za-z0-9+/_=:.-]{1,1024}$'
    or p_http_status is null or p_http_status not between 200 and 299
  then raise exception 'INVALID_TECHNICAL_EVIDENCE' using errcode='22023';end if;

  -- Resolve the sender from the existing S0 fixture, not request-provided
  -- dealership/WABA/phone. Lock registry+outbox against rebinding/cancel.
  select m.app_ref,m.concessionaria_id,m.canal_id,m.waba_ref,m.phone_number_ref
    into v_scope
  from prumo_private.meta_canais_fixture_s0 m
  join public.canais_loja c on c.id=m.canal_id
    and c.concessionaria_id=m.concessionaria_id
  join public.concessionarias l on l.id=m.concessionaria_id
  join prumo_private.outbox_intencoes_s0 o on o.concessionaria_id=m.concessionaria_id
    and o.canal_id=m.canal_id and o.id=p_intencao
  where m.app_ref=p_app and m.canal_id=p_canal and l.ativo
    and c.modo='simulado' and o.estado='BLOQUEADA_GATES'
  for share of m,o;
  if not found then
    raise exception 'UNTRUSTED_OR_INACTIVE_FIXTURE_SCOPE' using errcode='42501';
  end if;

  insert into prumo_private.meta_vinculos_tentativa_fixture_s0(
    app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref,
    intencao_id,attempt_ref,correlation_ref,recipient_verified,
    provider_message_id,graph_http_status)
  values(v_scope.app_ref,v_scope.concessionaria_id,v_scope.canal_id,
    v_scope.waba_ref,v_scope.phone_number_ref,p_intencao,p_attempt,
    p_correlation,p_recipient,p_wamid,p_http_status)
  on conflict do nothing returning id into v_new;

  if v_new is not null then
    return pg_catalog.jsonb_build_object('outcome','LAB_BOUND',
      'ack_allowed',false,'retry_external',false,'production_authorized',false);
  end if;
  -- Read BOTH uniqueness directions. Neither a different attempt on this
  -- wamid nor a second wamid for this attempt may become a silent replay.
  select * into v_attempt from prumo_private.meta_vinculos_tentativa_fixture_s0
    where app_ref=v_scope.app_ref and concessionaria_id=v_scope.concessionaria_id
      and attempt_ref=p_attempt for share;
  select * into v_message from prumo_private.meta_vinculos_tentativa_fixture_s0
    where app_ref=v_scope.app_ref and waba_ref=v_scope.waba_ref
      and phone_number_ref=v_scope.phone_number_ref and provider_message_id=p_wamid for share;
  if v_attempt.id is null or v_message.id is null
    or v_attempt.id is distinct from v_message.id
    or v_attempt.canal_id is distinct from v_scope.canal_id
    or v_attempt.waba_ref is distinct from v_scope.waba_ref
    or v_attempt.phone_number_ref is distinct from v_scope.phone_number_ref
    or v_attempt.intencao_id is distinct from p_intencao
    or v_attempt.correlation_ref is distinct from p_correlation
    or v_attempt.recipient_verified is distinct from p_recipient
    or v_attempt.graph_http_status is distinct from p_http_status
  then raise exception 'CONFLICT_TECHNICAL_BINDING' using errcode='23505';end if;
  return pg_catalog.jsonb_build_object('outcome','LAB_REPLAY',
    'ack_allowed',false,'retry_external',false,'production_authorized',false);
end $wa14$;

-- Exact scoped recovery is a READ, not a Graph retry command. An ABSENT
-- result after a lost response is NOT evidence the provider never sent.
create function prumo_private.consultar_vinculo_meta_fixture_s0(
  p_app text,p_canal uuid,p_intencao uuid,p_attempt text,p_correlation text,
  p_recipient text,p_wamid text
) returns jsonb language plpgsql security invoker set search_path='' as $wa14$
declare v_scope record; v_attempt record; v_message record; v_outcome text;
begin
  if current_user <> 'postgres' then
    raise exception 'INTERNAL_ONLY' using errcode='42501';
  end if;
  if p_app is null or p_canal is null or p_intencao is null
    or p_attempt is null or p_attempt !~ '^[A-Za-z0-9_.:-]{1,128}$'
    or p_correlation is null or p_correlation !~ '^[A-Za-z0-9_.:-]{1,128}$'
    or p_recipient is null or p_recipient !~ '^[0-9]{8,15}$'
    or p_wamid is null or p_wamid !~ '^wamid\.[A-Za-z0-9+/_=:.-]{1,1024}$'
  then raise exception 'INVALID_TECHNICAL_QUERY' using errcode='22023';end if;

  select m.app_ref,m.concessionaria_id,m.canal_id,m.waba_ref,m.phone_number_ref
    into v_scope
  from prumo_private.meta_canais_fixture_s0 m
  join public.canais_loja c on c.id=m.canal_id
    and c.concessionaria_id=m.concessionaria_id
  where m.app_ref=p_app and m.canal_id=p_canal and c.modo='simulado'
  for share of m;
  if not found then
    raise exception 'UNTRUSTED_FIXTURE_SCOPE' using errcode='42501';
  end if;
  select * into v_attempt from prumo_private.meta_vinculos_tentativa_fixture_s0
    where app_ref=v_scope.app_ref and concessionaria_id=v_scope.concessionaria_id
      and attempt_ref=p_attempt;
  select * into v_message from prumo_private.meta_vinculos_tentativa_fixture_s0
    where app_ref=v_scope.app_ref and waba_ref=v_scope.waba_ref
      and phone_number_ref=v_scope.phone_number_ref and provider_message_id=p_wamid;
  if v_attempt.id is null and v_message.id is null then
    v_outcome:='LAB_ABSENT';
  elsif v_attempt.id is not null and v_attempt.id=v_message.id
    and v_attempt.canal_id=v_scope.canal_id
    and v_attempt.intencao_id=p_intencao
    and v_attempt.correlation_ref=p_correlation
    and v_attempt.recipient_verified=p_recipient
  then v_outcome:='LAB_FOUND_EXACT';
  else v_outcome:='LAB_CONFLICT';
  end if;
  return pg_catalog.jsonb_build_object('outcome',v_outcome,
    'ack_allowed',false,'retry_external',false,'production_authorized',false);
end $wa14$;

revoke all on function prumo_private.registrar_vinculo_meta_fixture_s0(
  text,uuid,uuid,text,text,text,text,integer),
  prumo_private.consultar_vinculo_meta_fixture_s0(
  text,uuid,uuid,text,text,text,text)
from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
