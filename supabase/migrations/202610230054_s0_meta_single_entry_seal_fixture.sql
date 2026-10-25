-- WA55 / S0-054 FINAL PHASE: seal old user-facing fixture entrypoints and
-- expose ONE signed PG17-only candidate delegating to WA52's locked path.
-- Applied ONLY after WA39-54 historical regressions and race scripts finish.
-- NOT a hosted Supabase migration, real Meta principal or commercial grant.
do $wa55_preflight$
begin
 if current_user<>'postgres' or current_database()<>'prumo_s0_test_ci'
 then raise exception 'WA55_DISPOSABLE_ONLY' using errcode='42501';end if;
 if exists(select 1 from pg_catalog.pg_roles where rolname in (
  'prumo_s0_meta_wa50_writer_lab','prumo_s0_meta_wa48_executor_lab',
  'prumo_s0_meta_wa52_outbox_guard_lab','prumo_s0_meta_ingress_lab'
 ) and (rolcanlogin or rolsuper or rolbypassrls))
 then raise exception 'WA55_ROLE_NOT_ISOLATED' using errcode='42501';end if;
 if (select proowner::regrole::text from pg_catalog.pg_proc
 where oid='prumo_private.meta_wa52_locked_forensic_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)'::regprocedure)
 is distinct from 'prumo_s0_meta_wa50_writer_lab'
 then raise exception 'WA55_UNEXPECTED_WA52_OWNER' using errcode='42501';end if;
end $wa55_preflight$;

-- The wrapper owns no table privileges beyond the WA52 writer's existing
-- scope; no update on source outbox or binding is delegated to the client.
grant create on schema prumo_private to prumo_s0_meta_wa50_writer_lab;
set role prumo_s0_meta_wa50_writer_lab;
create function prumo_private.meta_wa55_single_entry_fixture_s0(
 p_key uuid,p_app text,p_waba text,p_phone text,p_channel uuid,
 p_intent uuid,p_attempt text,p_corr text,p_recipient text,p_wamid text,
 p_event text,p_kind text,p_hash text,p_issued bigint,p_nonce uuid,p_mac text)
returns jsonb language plpgsql security definer set search_path='' as $wa55$
declare v_receipt jsonb;
begin
 if session_user<>'prumo_s0_meta_wa48_client_lab'
 or current_database()<>'prumo_s0_test_ci'
 then raise exception 'WA55_CLIENT_DENIED' using errcode='42501';end if;
 -- The WA52 definer checks full S0 scoped binding, locks the real outbox
 -- before event/key/HMAC and appends the original immutable forensic ledger.
 -- Any error propagates, atomically reverting nonce and append.
 v_receipt:=prumo_private.meta_wa52_locked_forensic_fixture_s0(
  p_key,p_app,p_waba,p_phone,p_channel,p_intent,p_attempt,p_corr,
  p_recipient,p_wamid,p_event,p_kind,p_hash,p_issued,p_nonce,p_mac);
 if v_receipt is null or v_receipt->>'lab_only' is distinct from 'true'
 or v_receipt->>'service_authenticated' is distinct from 'false'
 or v_receipt->>'ack_allowed' is distinct from 'false'
 or v_receipt->>'send_authorized' is distinct from 'false'
 or v_receipt->>'production_authorized' is distinct from 'false'
 or v_receipt->>'case_transition_authorized' is distinct from 'false'
 then raise exception 'WA55_UNTRUSTED_WA52_RESULT' using errcode='42501';end if;
 return v_receipt||pg_catalog.jsonb_build_object(
  'entrypoint','WA55_PG17_SINGLE_LAB_ONLY',
  'legacy_paths_directly_executable',false,
  'runtime_principal_authenticated',false);
end $wa55$;
reset role;
revoke create on schema prumo_private from prumo_s0_meta_wa50_writer_lab;

-- Function execute list is explicit and fail-closed. Older privileged
-- postgres-only S0/043 internal SQL routines are outside the API surface:
-- their continued presence in the fixture does NOT mean prod readiness.
revoke all on function prumo_private.meta_wa55_single_entry_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s0_meta_ingress_lab,
 prumo_s0_meta_signer_lab,prumo_s0_meta_wa48_executor_lab,
 prumo_s0_meta_wa50_writer_lab,prumo_s0_meta_wa52_outbox_guard_lab;
grant execute on function prumo_private.meta_wa55_single_entry_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 to prumo_s0_meta_wa48_client_lab;

-- This final migration is deliberately placed AFTER all WA39–54 tests.
-- No historic test is weakened or deleted. Its public/test-client doors
-- close, while internal helper privileges needed by WA55 remain intact.
revoke execute on function prumo_private.meta_wa48_shadow_append_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 from prumo_s0_meta_wa48_client_lab;
revoke execute on function prumo_private.meta_wa49_scoped_shadow_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 from prumo_s0_meta_wa48_client_lab;
revoke execute on function prumo_private.meta_wa50_restricted_forensic_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 from prumo_s0_meta_wa48_client_lab;
revoke execute on function prumo_private.meta_wa51_parity_forensic_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 from prumo_s0_meta_wa48_client_lab;
revoke execute on function prumo_private.meta_wa52_locked_forensic_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 from prumo_s0_meta_wa48_client_lab;
-- WA52 originally revoked EXECUTE even from its own NOLOGIN writer role.
-- Restore ONLY the private definer-to-definer call needed by WA55;
-- do not grant the old route back to the synthetic client.
grant execute on function prumo_private.meta_wa52_locked_forensic_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 to prumo_s0_meta_wa50_writer_lab;
revoke execute on function prumo_private.meta_arquivar_handoff_assinado_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)
 from prumo_s0_meta_ingress_lab;
