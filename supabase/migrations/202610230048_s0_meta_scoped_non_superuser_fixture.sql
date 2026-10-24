-- WA49 S0/048: use ACTUAL S0/041-042 bindings for a scoped PG17
-- non-superuser SHADOW receipt. Read-only on authoritative S0 objects.
-- Never install this fixture in hosted Supabase; no production M2M or S1.
do $wa49_preflight$
begin
 if current_user<>'postgres' or current_database()<>'prumo_s0_test_ci'
 then raise exception 'WA49_OFFLINE_ONLY' using errcode='42501';end if;
 if (select rolcanlogin or rolsuper or rolbypassrls
     from pg_catalog.pg_roles where rolname='prumo_s0_meta_wa48_executor_lab')
 then raise exception 'WA49_UNSAFE_EXECUTOR' using errcode='42501';end if;
end $wa49_preflight$;
-- Read-only column grants for exact S0 mapping; UPDATE/DELETE are NOT granted.
grant select(id,app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref,
 intencao_id,attempt_ref,correlation_ref,recipient_verified,provider_message_id)
 on prumo_private.meta_vinculos_tentativa_fixture_s0
 to prumo_s0_meta_wa48_executor_lab;
grant select(app_ref,concessionaria_id,app_technical_ref)
 on prumo_private.meta_apps_fixture_s0 to prumo_s0_meta_wa48_executor_lab;
grant select(app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref,
 waba_technical_ref,phone_technical_ref)
 on prumo_private.meta_canais_fixture_s0 to prumo_s0_meta_wa48_executor_lab;
grant select(id,concessionaria_id,canal_id,estado)
 on prumo_private.outbox_intencoes_s0 to prumo_s0_meta_wa48_executor_lab;
create policy wa49_lab_binding_read on prumo_private.meta_vinculos_tentativa_fixture_s0
 for select to prumo_s0_meta_wa48_executor_lab using(true);
create policy wa49_lab_app_read on prumo_private.meta_apps_fixture_s0
 for select to prumo_s0_meta_wa48_executor_lab using(true);
create policy wa49_lab_channel_read on prumo_private.meta_canais_fixture_s0
 for select to prumo_s0_meta_wa48_executor_lab using(true);
create policy wa49_lab_intent_read on prumo_private.outbox_intencoes_s0
 for select to prumo_s0_meta_wa48_executor_lab using(true);

grant create on schema prumo_private to prumo_s0_meta_wa48_executor_lab;
set role prumo_s0_meta_wa48_executor_lab;
create function prumo_private.meta_wa49_scoped_shadow_fixture_s0(
 p_key uuid,p_app text,p_waba text,p_phone text,p_channel uuid,
 p_intent uuid,p_attempt text,p_corr text,p_recipient text,p_wamid text,
 p_event text,p_kind text,p_hash text,p_issued bigint,p_nonce uuid,p_mac text)
returns jsonb language plpgsql security definer set search_path='' as $wa49_fn$
declare v_binding uuid;v_status text;v_receipt jsonb;
begin
 if session_user<>'prumo_s0_meta_wa48_client_lab' or
  current_database()<>'prumo_s0_test_ci'
 then raise exception 'WA49_LOGIN_DENIED' using errcode='42501';end if;
 if p_app is null or p_app !~ '^[0-9]{5,25}$'
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
 then raise exception 'WA49_INVALID' using errcode='42501';end if;
 -- Matches S0/043's canonical join: app, shop/channel, WABA/phone aliases,
 -- outbox ownership and exact binding intent/attempt/recipient/wamid.
 -- No FOR SHARE: row locks would require UPDATE on source S0 tables.
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
 where a.app_technical_ref=p_app
   and m.waba_technical_ref=p_waba and m.phone_technical_ref=p_phone
   and b.canal_id=p_channel and b.intencao_id=p_intent
   and b.attempt_ref=p_attempt and b.correlation_ref=p_corr
   and b.recipient_verified=p_recipient and b.provider_message_id=p_wamid;
 if not found then
  raise exception 'WA49_SCOPE_DENIED' using errcode='42501';end if;
 -- Shared WA39 event namespace. This serializes with S0/043 on exact binding
 -- but does NOT turn our unlocked read into a commercial/lifecycle snapshot.
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended('wa39:'||v_binding::text||':'||p_event,39));
 -- WA48's independent verifier handles HMAC, time, key-revoke lock and nonce,
 -- and writes only the shadow ledger in THIS transaction. Any failure rolls
 -- back both portions; the original forensic ledger stays owned by postgres.
 v_receipt:=prumo_private.meta_wa48_shadow_append_fixture_s0(
  p_key,p_app,p_waba,p_phone,p_channel,p_intent,p_attempt,p_corr,p_recipient,
  p_wamid,p_event,p_kind,p_hash,p_issued,p_nonce,p_mac);
 if v_receipt is null or v_receipt->>'lab_only'<>'true'
 then raise exception 'WA49_SHADOW_FAILURE' using errcode='42501';end if;
 return v_receipt||pg_catalog.jsonb_build_object(
  's0_scope_matched',true,'authoritative_s0_written',false,
  'authoritative_scope_snapshot_locked',false,
  'lab_only',true,'service_authenticated',false,
  'ack_allowed',false,'send_authorized',false,
  'production_authorized',false,'case_transition_authorized',false);
end $wa49_fn$;
reset role;
revoke create on schema prumo_private from prumo_s0_meta_wa48_executor_lab;
revoke all on function prumo_private.meta_wa49_scoped_shadow_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer,
 prumo_s0_meta_signer_lab,prumo_s0_meta_ingress_lab,prumo_s0_meta_wa48_executor_lab;
grant execute on function prumo_private.meta_wa49_scoped_shadow_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 to prumo_s0_meta_wa48_client_lab;
