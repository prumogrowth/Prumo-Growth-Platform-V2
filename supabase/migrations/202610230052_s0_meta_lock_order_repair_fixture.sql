-- WA53 S0/052: normalize WA50 lock order to event -> key, PG17 test only.
-- Do not deploy in hosted Supabase. No changes to WA48/49/51/52, S1, main.
do $wa53_preflight$
begin
 if current_user<>'postgres' or current_database()<>'prumo_s0_test_ci'
 then raise exception 'WA53_DISPOSABLE_ONLY' using errcode='42501';end if;
 if (select proowner::pg_catalog.regrole::text
 from pg_catalog.pg_proc where oid=
 'prumo_private.meta_wa50_restricted_forensic_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)'::pg_catalog.regprocedure)
 is distinct from 'prumo_s0_meta_wa50_writer_lab'
 then raise exception 'WA53_UNEXPECTED_OWNER' using errcode='42501';end if;
 if exists(select 1 from pg_catalog.pg_roles where rolname in
 ('prumo_s0_meta_wa50_writer_lab','prumo_s0_meta_wa48_executor_lab')
 and (rolcanlogin or rolsuper or rolbypassrls))
 then raise exception 'WA53_UNSAFE_OWNER' using errcode='42501';end if;
end $wa53_preflight$;
-- CREATE OR REPLACE preserves OID, ACL and SECURITY DEFINER owner.
grant create on schema prumo_private to prumo_s0_meta_wa50_writer_lab;
set role prumo_s0_meta_wa50_writer_lab;
create or replace function prumo_private.meta_wa50_restricted_forensic_fixture_s0(
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
 -- WA53 fixes former WA50 key->event inversion. Exact S0 source match
 -- happens first; then event lock; then cryptographic key/nonce lock.
 -- A scope mismatch cannot consume a nonce or write a shadow receipt.
 -- Same S0/043 lock for event race / kind conflict; no UPDATE on binding.
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended('wa39:'||v_binding::text||':'||p_event,39));
 -- WA48 fails closed on a different status kind for an existing exact
 -- event/body; forensic conflict insertion is NOT yet supported by this path.
 -- WA48 takes key lock only AFTER WA39 event and spends nonce in same transaction.
 -- Any error below rolls back nonce, shadow receipt AND original ledger.
 v_receipt:=prumo_private.meta_wa48_shadow_append_fixture_s0(
  p_key,p_app,p_waba,p_phone,p_channel,p_intent,p_attempt,p_corr,p_recipient,
  p_wamid,p_event,p_kind,p_hash,p_issued,p_nonce,p_mac);
 if v_receipt is null or v_receipt->>'lab_only'<>'true'
 then raise exception 'WA50_VERIFIER_FAILED' using errcode='42501';end if;



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
-- No new EXECUTE grants, no RLS changes, no commercial side effects.
