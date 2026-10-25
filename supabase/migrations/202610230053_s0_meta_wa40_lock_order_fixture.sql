-- WA54/S0-053: change the offline privileged WA40 handoff to
-- binding/outbox FOR SHARE -> WA39 event -> WA42 key/nonce.
-- PG17 prumo_s0_test_ci ONLY. No S1/production/Meta hosted deployments.
do $wa54_guard$
declare v_proc oid;
begin
 if current_user<>'postgres' or current_database()<>'prumo_s0_test_ci'
 then raise exception 'WA54_OFFLINE_ONLY' using errcode='42501';end if;
 v_proc:='prumo_private.meta_arquivar_handoff_assinado_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)'::regprocedure;
 if (select proowner::regrole::text from pg_catalog.pg_proc where oid=v_proc)<>'postgres'
 or (select not prosecdef from pg_catalog.pg_proc where oid=v_proc)
 or (select position('meta_verificar_handoff_fixture_s0' in prosrc)=0
     from pg_catalog.pg_proc where oid=v_proc)
 then raise exception 'WA54_UNKNOWN_WA40_OWNER_OR_BODY' using errcode='42501';end if;
end $wa54_guard$;
-- CREATE OR REPLACE by the existing postgres owner preserves OID, grants,
-- and SECURITY DEFINER. The synthetic SET ROLE ingress requirement remains.
create or replace function prumo_private.meta_arquivar_handoff_assinado_fixture_s0(
 p_chave uuid,p_app text,p_waba text,p_phone text,p_canal uuid,
 p_intencao uuid,p_attempt text,p_correlation text,p_recipient text,
 p_wamid text,p_event text,p_kind text,p_body_hash text,
 p_emitido bigint,p_nonce uuid,p_mac text
) returns jsonb language plpgsql security definer set search_path='' as $wa41_outer$
declare v_out jsonb;v_binding uuid;
begin
 if session_user <> 'postgres' or
    current_setting('role') <> 'prumo_s0_meta_ingress_lab'
 then raise exception 'META_SERVICE_ROLE_DENIED' using errcode='42501';end if;
 if p_chave is null or p_canal is null or p_intencao is null
  or p_nonce is null or p_emitido is null
  or p_app is null or p_app !~ '^[0-9]{5,25}$'
  or p_waba is null or p_waba !~ '^[0-9]{5,25}$'
  or p_phone is null or p_phone !~ '^[0-9]{5,25}$'
  or p_attempt is null or p_attempt !~ '^[A-Za-z0-9_.:-]{1,128}$'
  or p_correlation is null or p_correlation !~ '^[A-Za-z0-9_.:-]{1,128}$'
  or p_recipient is null or p_recipient !~ '^[0-9]{8,15}$'
  or p_wamid is null or p_wamid !~ '^wamid\.[A-Za-z0-9+/_=:.-]+$'
  or length(p_wamid) not between 7 and 1030
  or p_event is null or p_event !~ '^[A-Za-z0-9_.:-]{1,128}$'
  or p_kind is null or p_kind not in ('sent','delivered','read','failed')
  or p_body_hash is null or p_body_hash !~ '^[a-f0-9]{64}$'
  or p_mac is null or p_mac !~ '^[a-f0-9]{64}$'
 then raise exception 'META_HANDOFF_INVALID' using errcode='42501';end if;
 -- WA54 PG17: resolve the SAME S0/043 authoritative technical binding
 -- and lock all corresponding source rows before any cryptographic key lock.
 -- This preserves the historical WA39 row-lock -> event-lock ordering.
 select b.id into v_binding
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
   and m.waba_technical_ref=p_waba
   and m.phone_technical_ref=p_phone
   and b.canal_id=p_canal and b.intencao_id=p_intencao
   and b.attempt_ref=p_attempt and b.correlation_ref=p_correlation
   and b.recipient_verified=p_recipient and b.provider_message_id=p_wamid
 for share of a,m,b,o;
 if not found then
  raise exception 'META_HANDOFF_SCOPE_DENIED' using errcode='42501';end if;
 -- Once locked, the canonical WA39 event namespace serializes all kind/body
 -- variants for this S0 binding. WA42 key verification locks only afterwards.
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended('wa39:'||v_binding::text||':'||p_event,39));

 perform prumo_private.meta_verificar_handoff_fixture_s0(
  p_chave,p_app,p_waba,p_phone,p_canal,p_intencao,p_attempt,
  p_correlation,p_recipient,p_wamid,p_event,p_kind,p_body_hash,
  p_emitido,p_nonce,p_mac);
 v_out:=prumo_private.archivar_status_meta_tecnico_fixture_s0(
  p_app,p_waba,p_phone,p_canal,p_intencao,p_attempt,p_correlation,
  p_recipient,p_wamid,p_event,p_kind,p_body_hash);
 if v_out->>'outcome'='LAB_SCOPE_DENIED' then
  raise exception 'META_HANDOFF_SCOPE_DENIED' using errcode='42501';end if;
 if v_out->>'outcome' not in (
  'LAB_OBSERVED_UNVERIFIED','LAB_LATE_UNVERIFIED','LAB_EXACT_BODY_REPLAY',
  'LAB_BODY_VARIANT_QUARANTINED','LAB_KIND_CONFLICT_QUARANTINED') then
  raise exception 'META_HANDOFF_UNEXPECTED_RESULT' using errcode='42501';end if;
 return v_out || pg_catalog.jsonb_build_object(
  'service_authenticated',false,'s0_production_authorized',false,
  'handoff_contract','WA40_PG17_LAB_ONLY');
end $wa41_outer$;

-- No grants, new service identities, webhook, or commercial operations.
