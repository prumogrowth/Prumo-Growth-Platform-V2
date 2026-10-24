-- WA50 / S0-049: PG17-only restricted ACTUAL S0 forensic ledger proof.
-- Experimental alternate path; unchanged WA39-49 public/privileged functions.
-- NO hosted migration, no real Meta principal, no ACK/Graph/S1.
do $wa50_guard$
begin
 if current_user<>'postgres' or current_database()<>'prumo_s0_test_ci'
 then raise exception 'WA50_LOCAL_ONLY' using errcode='42501';end if;
 create role prumo_s0_meta_wa50_writer_lab nologin noinherit
  nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
 create role prumo_s0_meta_wa50_binding_guard_lab nologin noinherit
  nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
 grant prumo_s0_meta_wa50_writer_lab to postgres with inherit false,set true;
 grant prumo_s0_meta_wa50_binding_guard_lab to postgres with inherit false,set true;
end $wa50_guard$;
grant usage on schema prumo_private to prumo_s0_meta_wa50_writer_lab,
 prumo_s0_meta_wa50_binding_guard_lab;

-- Dedicated NOLOGIN trigger owner holds exactly the row-lock privilege
-- needed by the EXISTING S0/043 immutable-binding verification trigger.
-- UPDATE(id) is granted ONLY to that guard, NEVER to the writer or client.
-- The source binding has an immutable UPDATE/DELETE trigger. This exception
-- must be reevaluated before any hosted migration.
grant select(id),update(id)
 on prumo_private.meta_vinculos_tentativa_fixture_s0
 to prumo_s0_meta_wa50_binding_guard_lab;
create policy wa50_fk_guard_read on prumo_private.meta_vinculos_tentativa_fixture_s0
 for select to prumo_s0_meta_wa50_binding_guard_lab using(true);
create policy wa50_fk_guard_lock on prumo_private.meta_vinculos_tentativa_fixture_s0
 for update to prumo_s0_meta_wa50_binding_guard_lab using(true) with check(true);
grant create on schema prumo_private to prumo_s0_meta_wa50_binding_guard_lab;
alter function prumo_private.validar_meta_status_vinculo_fixture_s0()
 security definer;
alter function prumo_private.validar_meta_status_vinculo_fixture_s0()
 owner to prumo_s0_meta_wa50_binding_guard_lab;
revoke create on schema prumo_private from prumo_s0_meta_wa50_binding_guard_lab;

-- Independent restricted writer can READ exact S0 join but cannot mutate
-- mapping, outbox, or technical attempt bindings.
grant select(id,app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref,
 intencao_id,attempt_ref,correlation_ref,recipient_verified,provider_message_id)
 on prumo_private.meta_vinculos_tentativa_fixture_s0
 to prumo_s0_meta_wa50_writer_lab;
grant select(app_ref,concessionaria_id,app_technical_ref)
 on prumo_private.meta_apps_fixture_s0 to prumo_s0_meta_wa50_writer_lab;
grant select(app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref,
 waba_technical_ref,phone_technical_ref)
 on prumo_private.meta_canais_fixture_s0 to prumo_s0_meta_wa50_writer_lab;
grant select(id,concessionaria_id,canal_id,estado)
 on prumo_private.outbox_intencoes_s0 to prumo_s0_meta_wa50_writer_lab;
create policy wa50_writer_binding_read on prumo_private.meta_vinculos_tentativa_fixture_s0
 for select to prumo_s0_meta_wa50_writer_lab using(true);
create policy wa50_writer_app_read on prumo_private.meta_apps_fixture_s0
 for select to prumo_s0_meta_wa50_writer_lab using(true);
create policy wa50_writer_channel_read on prumo_private.meta_canais_fixture_s0
 for select to prumo_s0_meta_wa50_writer_lab using(true);
create policy wa50_writer_intent_read on prumo_private.outbox_intencoes_s0
 for select to prumo_s0_meta_wa50_writer_lab using(true);

grant select(id,vinculo_id,event_ref,body_sha256,provider_status),
 insert(vinculo_id,event_ref,body_sha256,provider_status)
 on prumo_private.meta_status_forense_fixture_s0
 to prumo_s0_meta_wa50_writer_lab;
grant select(id,vinculo_id,event_ref,body_sha256,reported_kind),
 insert(vinculo_id,event_ref,body_sha256,reported_kind,reason)
 on prumo_private.meta_status_conflitos_fixture_s0
 to prumo_s0_meta_wa50_writer_lab;
create policy wa50_writer_forense_read on prumo_private.meta_status_forense_fixture_s0
 for select to prumo_s0_meta_wa50_writer_lab using(true);
create policy wa50_writer_forense_insert on prumo_private.meta_status_forense_fixture_s0
 for insert to prumo_s0_meta_wa50_writer_lab with check(true);
create policy wa50_writer_conflict_read on prumo_private.meta_status_conflitos_fixture_s0
 for select to prumo_s0_meta_wa50_writer_lab using(true);
create policy wa50_writer_conflict_insert on prumo_private.meta_status_conflitos_fixture_s0
 for insert to prumo_s0_meta_wa50_writer_lab with check(true);

-- Reuse only WA48 HMAC/nonce/shadow verifier as an internal library.
grant execute on function prumo_private.meta_wa48_shadow_append_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 to prumo_s0_meta_wa50_writer_lab;
grant create on schema prumo_private to prumo_s0_meta_wa50_writer_lab;
set role prumo_s0_meta_wa50_writer_lab;
create function prumo_private.meta_wa50_restricted_forensic_fixture_s0(
 p_key uuid,p_app text,p_waba text,p_phone text,p_channel uuid,
 p_intent uuid,p_attempt text,p_corr text,p_recipient text,p_wamid text,
 p_event text,p_kind text,p_hash text,p_issued bigint,p_nonce uuid,p_mac text)
returns jsonb language plpgsql security definer set search_path='' as $wa50_function$
declare v_binding uuid;v_state text;v_receipt jsonb;v_old_kind text;
 v_duplicate uuid;v_exists boolean;v_outcome text;
begin
 if session_user<>'prumo_s0_meta_wa48_client_lab' or
  current_database()<>'prumo_s0_test_ci'
 then raise exception 'WA50_CLIENT_DENIED' using errcode='42501';end if;
 if p_key is null or p_nonce is null or p_issued is null
 or p_mac is null or p_mac !~ '^[0-9a-f]{64}$'
 or p_app is null or p_app !~ '^[0-9]{5,25}$'
 or p_waba is null or p_waba !~ '^[0-9]{5,25}$'
 or p_phone is null or p_phone !~ '^[0-9]{5,25}$'
 or p_channel is null or p_intent is null
 or p_attempt is null or p_attempt !~ '^[A-Za-z0-9_.:-]{1,128}$'
 or p_corr is null or p_corr !~ '^[A-Za-z0-9_.:-]{1,128}$'
 or p_recipient is null or p_recipient !~ '^[0-9]{8,15}$'
 or p_wamid is null or p_wamid !~ '^wamid\.[A-Za-z0-9+/_=:.-]+$'
 or pg_catalog.length(p_wamid) not between 7 and 1030
 or p_event is null or p_event !~ '^[A-Za-z0-9_.:-]{1,128}$'
 or p_kind is null or p_kind not in ('sent','delivered','read','failed')
 or p_hash is null or p_hash !~ '^[0-9a-f]{64}$'
 then raise exception 'WA50_BAD_ENVELOPE' using errcode='42501';end if;
 -- WA48 takes key lock and spends nonce on our SAME transaction.
 -- Any error below rolls back nonce, shadow receipt AND original ledger.
 v_receipt:=prumo_private.meta_wa48_shadow_append_fixture_s0(
  p_key,p_app,p_waba,p_phone,p_channel,p_intent,p_attempt,p_corr,p_recipient,
  p_wamid,p_event,p_kind,p_hash,p_issued,p_nonce,p_mac);
 if v_receipt is null or v_receipt->>'lab_only'<>'true'
 then raise exception 'WA50_VERIFIER_FAILED' using errcode='42501';end if;
 -- Exact S0 authoritative joins and claim equality (not client tenant).
 select b.id,o.estado into v_binding,v_state
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
 where a.app_technical_ref=p_app and m.waba_technical_ref=p_waba
 and m.phone_technical_ref=p_phone and b.canal_id=p_channel
 and b.intencao_id=p_intent and b.attempt_ref=p_attempt
 and b.correlation_ref=p_corr and b.recipient_verified=p_recipient
 and b.provider_message_id=p_wamid;
 if not found then raise exception 'WA50_SCOPE_DENIED' using errcode='42501';end if;
 -- Same S0/043 lock for event race / kind conflict; no UPDATE on binding.
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended('wa39:'||v_binding::text||':'||p_event,39));
 select provider_status into v_old_kind
 from prumo_private.meta_status_forense_fixture_s0
 where vinculo_id=v_binding and event_ref=p_event and body_sha256=p_hash;
 if found then
  if v_old_kind=p_kind then v_outcome:='LAB_EXACT_BODY_REPLAY';
  else
   insert into prumo_private.meta_status_conflitos_fixture_s0(
    vinculo_id,event_ref,body_sha256,reported_kind,reason)
   values(v_binding,p_event,p_hash,p_kind,'LAB_SAME_BODY_DIFFERENT_KIND')
   on conflict do nothing;
   v_outcome:='LAB_KIND_CONFLICT_QUARANTINED';
  end if;
 else
  select exists(select 1 from prumo_private.meta_status_forense_fixture_s0
   where vinculo_id=v_binding and event_ref=p_event) into v_exists;
  insert into prumo_private.meta_status_forense_fixture_s0(
   vinculo_id,event_ref,body_sha256,provider_status)
  values(v_binding,p_event,p_hash,p_kind) returning id into v_duplicate;
  if v_exists then v_outcome:='LAB_BODY_VARIANT_QUARANTINED';
  elsif v_state='CANCELADA' then v_outcome:='LAB_LATE_UNVERIFIED';
  else v_outcome:='LAB_OBSERVED_UNVERIFIED';end if;
 end if;
 return pg_catalog.jsonb_build_object(
  'outcome',v_outcome,'lab_only',true,'authoritative_lab_forensic_appended',true,
  'original_wa39_owner_preserved',true,
  'service_authenticated',false,'production_authorized',false,
  'ack_allowed',false,'send_authorized',false,'retry_external',false,
  'delivery_confirmed',false,'case_transition_authorized',false,
  'definitive_failure_count_increment',false);
end $wa50_function$;
reset role;
revoke create on schema prumo_private from prumo_s0_meta_wa50_writer_lab;
revoke all on function prumo_private.meta_wa50_restricted_forensic_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer,
 prumo_s0_meta_signer_lab,prumo_s0_meta_ingress_lab,
 prumo_s0_meta_wa50_writer_lab,prumo_s0_meta_wa50_binding_guard_lab;
grant execute on function prumo_private.meta_wa50_restricted_forensic_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 to prumo_s0_meta_wa48_client_lab;
