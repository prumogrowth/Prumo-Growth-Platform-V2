-- S0/030: audit remediation for 028/029. PostgreSQL synthetic fixtures ONLY.
-- No Meta credentials, active Meta channel, service principal or production ACK.
-- DEC-WA-05: app owned by each concessionaria; this is a fake registry, not onboarding.
alter table prumo_private.aliases_identidade_s0
 add constraint aliases_s0_loja_lead_id_uniq unique(concessionaria_id,lead_id,id),
 add constraint aliases_s0_evidencia_consistente check(
   (mobile_confirmado_sintetico
      and chave_variante_sintetica is not null
      and chave_variante_sintetica = prumo_private.chave_variante_br_s0(numero_sintetico))
   or (not mobile_confirmado_sintetico and chave_variante_sintetica is null));
alter table prumo_private.eventos_identidade_s0
 add constraint evento_alias_mesmo_lead_loja_s0
 foreign key(concessionaria_id,lead_id,alias_id)
 references prumo_private.aliases_identidade_s0(concessionaria_id,lead_id,id);

-- Preserve the first conflict as an immutable pending fact. Same key with
-- changed message/number must fail rather than ON CONFLICT DO NOTHING.
create or replace function prumo_private.receber_mensagem_identidade_s0(
 p_canal uuid,p_numero text,p_id_externo text,p_texto text,
 p_mobile_confirmado boolean
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_loja uuid;v_res jsonb;v_motivo text;v_pend record;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 select c.concessionaria_id into v_loja
 from public.canais_loja c join public.concessionarias l
 on l.id=c.concessionaria_id and l.ativo
 where c.id=p_canal and c.modo='simulado';
 if v_loja is null then raise exception 'UNKNOWN_CHANNEL' using errcode='22023';end if;
 if p_id_externo is null or p_id_externo !~ '^[A-Za-z0-9_.:-]{1,120}$'
 or p_texto is null or length(btrim(p_texto)) not between 1 and 1024
 then raise exception 'INVALID_INBOUND_SYNTHETIC' using errcode='22023';end if;
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  's0-identity-pending:'||p_canal::text||':'||p_id_externo,30));
 select telefone_sintetico,texto_sintetico,motivo into v_pend
 from prumo_private.pendencias_identidade_s0
 where concessionaria_id=v_loja and canal_id=p_canal and id_externo=p_id_externo
 for update;
 if found then
  if v_pend.telefone_sintetico is distinct from p_numero
     or v_pend.texto_sintetico is distinct from p_texto
  then raise exception 'CONFLICT_IDEMPOTENCY_KEY' using errcode='23505';end if;
  return pg_catalog.jsonb_build_object('outcome',v_pend.motivo,
    'roteamento','HUMANO_PENDENTE','replay','ALREADY_PENDING');
 end if;
 v_res:=prumo_private.resolver_contato_s0(
   v_loja,p_numero,'CANAL_SINTETICO',p_mobile_confirmado);
 if v_res->>'outcome' in ('IDENTITY_CONFLICT','NEEDS_REVIEW') then
  v_motivo:=v_res->>'outcome';
  insert into prumo_private.pendencias_identidade_s0(
    concessionaria_id,canal_id,id_externo,telefone_sintetico,texto_sintetico,motivo)
  values(v_loja,p_canal,p_id_externo,p_numero,p_texto,v_motivo);
  return pg_catalog.jsonb_build_object('outcome',v_motivo,'roteamento','HUMANO_PENDENTE');
 end if;
 return prumo_private.receber_mensagem_sintetica(
   p_canal,v_res->>'numero_principal_sintetico',p_id_externo,p_texto);
end $fn$;
revoke all on function prumo_private.receber_mensagem_identidade_s0(
 uuid,text,text,text,boolean)
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;

-- Identity and sender mapping for FAKE app references only, scoped to a shop.
-- One app fixture belongs to one shop, but may have multiple sender channels.
create table prumo_private.meta_apps_fixture_s0(
 app_ref text primary key check(app_ref ~ '^FIXTURE_[A-Za-z0-9_]{1,64}$'),
 concessionaria_id uuid not null references public.concessionarias(id),
 unique(app_ref,concessionaria_id)
);
create table prumo_private.meta_canais_fixture_s0(
 app_ref text not null,
 concessionaria_id uuid not null,
 canal_id uuid not null,
 waba_ref text not null check(waba_ref ~ '^FIXTURE_[A-Za-z0-9_]{1,64}$'),
 phone_number_ref text not null unique check(phone_number_ref ~ '^FIXTURE_[A-Za-z0-9_]{1,64}$'),
 unique(app_ref,waba_ref,phone_number_ref),
 foreign key(app_ref,concessionaria_id)
  references prumo_private.meta_apps_fixture_s0(app_ref,concessionaria_id),
 foreign key(concessionaria_id,canal_id)
  references public.canais_loja(concessionaria_id,id)
);
alter table prumo_private.meta_apps_fixture_s0 enable row level security;
alter table prumo_private.meta_canais_fixture_s0 enable row level security;
revoke all on prumo_private.meta_apps_fixture_s0,prumo_private.meta_canais_fixture_s0
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;

-- Distinguish a durable fixture payload from the metadata-only records of 029.
-- Old 029 remains a synthetic test and is never an HTTP ACK authority.
alter table prumo_private.inbox_eventos_s0
 add column app_fixture_ref text,
 add column waba_fixture_ref text,
 add column phone_fixture_ref text,
 add column provider_message_id_s0 text,
 add column provider_kind_s0 text,
 add column provider_timestamp_s0 timestamptz,
 add column payload_fixture_s0 jsonb,
 add constraint inbox_payload_fixture_shape_s0 check (
   payload_fixture_s0 is null or (
    pg_catalog.jsonb_typeof(payload_fixture_s0)='object'
    and payload_fixture_s0->>'fixture_ref' ~ '^FIXTURE_[A-Za-z0-9_]{1,80}$'
   ));

-- A SINGLE database transaction can commit multiple synthetic sender channels
-- without deriving any shop from a user claim. The app/channel mapping is
-- populated only by a privileged local fixture. NO public function or auth.
create function prumo_private.aceitar_lote_multicanal_fixture_s0(p_itens jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_item jsonb;v_payload jsonb;v_loja uuid;v_canal uuid;
 v_app text;v_waba text;v_phone text;v_kind text;v_msg text;v_type text;
 v_when text;v_timestamp timestamptz;v_key text;v_hash text;
 v_id uuid;v_prev record;v_new integer:=0;v_dup integer:=0;v_total integer;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if pg_catalog.jsonb_typeof(p_itens) is distinct from 'array'
 then raise exception 'INVALID_INGRESS_BATCH' using errcode='22023';end if;
 v_total:=pg_catalog.jsonb_array_length(p_itens);
 if v_total not between 1 and 20
 then raise exception 'INVALID_INGRESS_BATCH' using errcode='22023';end if;
 for v_item in select value from pg_catalog.jsonb_array_elements(p_itens) loop
  if pg_catalog.jsonb_typeof(v_item) is distinct from 'object'
    or v_item ? 'concessionaria_id' or v_item ? 'canal_id'
    or v_item ? 'transport_signature_validated'
  then raise exception 'UNTRUSTED_INGRESS_SCOPE' using errcode='22023';end if;
  v_app:=v_item->>'app_ref'; v_waba:=v_item->>'waba_id';
  v_phone:=v_item->>'phone_number_id'; v_type:=v_item->>'event_kind';
  v_msg:=v_item->>'provider_message_id';v_kind:=v_item->>'provider_kind';
  v_when:=v_item->>'provider_timestamp';v_payload:=v_item->'payload_fixture';
  if v_app is null or v_waba is null or v_phone is null
    or v_type not in ('inbound_message','status_callback') or v_type is null
    or v_msg is null or v_msg !~ '^[A-Za-z0-9_.:-]{1,100}$'
    or v_kind is null or v_kind !~ '^[A-Za-z_]{1,32}$'
    or v_when is null or v_when !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T'
    or pg_catalog.jsonb_typeof(v_payload) is distinct from 'object'
    or v_payload->>'fixture_ref' is null
    or v_payload->>'fixture_ref' !~ '^FIXTURE_[A-Za-z0-9_]{1,80}$'
    or (select count(*) from pg_catalog.jsonb_object_keys(v_payload))<>1
  then raise exception 'INVALID_INGRESS_ITEM' using errcode='22023';end if;
  begin
   v_timestamp:=v_when::timestamptz;
  exception when datetime_field_overflow or invalid_datetime_format then
   raise exception 'INVALID_INGRESS_TIMESTAMP' using errcode='22023';
  end;
  select c.concessionaria_id,c.canal_id into v_loja,v_canal
  from prumo_private.meta_canais_fixture_s0 c
  join prumo_private.meta_apps_fixture_s0 a
   on a.app_ref=c.app_ref and a.concessionaria_id=c.concessionaria_id
  join public.canais_loja cl
   on cl.id=c.canal_id and cl.concessionaria_id=c.concessionaria_id
  join public.concessionarias lo
   on lo.id=c.concessionaria_id
  where c.app_ref=v_app and c.waba_ref=v_waba
    and c.phone_number_ref=v_phone and cl.modo='simulado' and lo.ativo;
  if v_loja is null then raise exception 'UNMAPPED_FIXTURE_CHANNEL' using errcode='42501';end if;
  if v_type='inbound_message' then
   v_key:='in:'||v_msg;
  else
   -- Callback ID is message ID, not unique status event ID. This fixture
   -- differentiates status + provider time, pending Meta semantic validation.
   v_key:='st:'||v_msg||':'||v_kind||':'||
    pg_catalog.to_char(v_timestamp at time zone 'UTC','YYYYMMDDHH24MISSUS');
  end if;
  if length(v_key)>160 then raise exception 'INGRESS_KEY_TOO_LONG' using errcode='22023';end if;
  v_hash:=pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
   v_type||':'||v_msg||':'||v_kind||':'||v_when||':'||v_payload::text,
   'UTF8')),'hex');
  insert into prumo_private.inbox_eventos_s0(
    concessionaria_id,canal_id,tipo,chave_evento,fingerprint_sintetico,
    app_fixture_ref,waba_fixture_ref,phone_fixture_ref,
    provider_message_id_s0,provider_kind_s0,provider_timestamp_s0,payload_fixture_s0)
  values(v_loja,v_canal,v_type,v_key,v_hash,v_app,v_waba,v_phone,
    v_msg,v_kind,v_timestamp,v_payload)
  on conflict(concessionaria_id,canal_id,tipo,chave_evento) do nothing
  returning id into v_id;
  if v_id is not null then
   insert into prumo_private.tarefas_ingresso_s0(inbox_id,concessionaria_id)
     values(v_id,v_loja);
   v_new:=v_new+1;
  else
   select fingerprint_sintetico,payload_fixture_s0 into v_prev
   from prumo_private.inbox_eventos_s0
   where concessionaria_id=v_loja and canal_id=v_canal
     and tipo=v_type and chave_evento=v_key;
   if v_prev.fingerprint_sintetico is distinct from v_hash
     or v_prev.payload_fixture_s0 is distinct from v_payload
   then raise exception 'CONFLICT_IDEMPOTENCY_KEY' using errcode='23505';end if;
   v_dup:=v_dup+1;
  end if;
  v_id:=null;
 end loop;
 -- NOT a production ACK receipt, and deliberately no COMMITTED claim.
 return pg_catalog.jsonb_build_object('outcome','FIXTURE_BATCH_STORED',
  'items',v_total,'accepted',v_new,'duplicates',v_dup);
end $fn$;
revoke all on function prumo_private.aceitar_lote_multicanal_fixture_s0(jsonb)
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
