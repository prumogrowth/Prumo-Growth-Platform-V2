-- WA38: PG17 forensic callback variants lab: offline only, no real Meta.
-- WA35's synthetic event_ref is a digest of selected status fields, NOT an
-- independently certified unique Meta callback ID. Body hash is produced by
-- synthetic test caller; DB cannot verify the HMAC or authenticate the caller.
\set ON_ERROR_STOP on
CREATE SCHEMA wa38_lab;
CREATE TABLE wa38_lab.observations (
 shop_ref text NOT NULL,case_ref text NOT NULL,attempt_ref text NOT NULL,
 event_ref text NOT NULL,body_sha256 text NOT NULL
   CHECK(body_sha256 ~ '^[0-9a-f]{64}$'),
 kind text NOT NULL CHECK(kind IN
   ('SENT_REPORTED','DELIVERED_REPORTED','READ_REPORTED','FAILED_REPORTED')),
 after_invalidation boolean NOT NULL,
 send_authorized boolean NOT NULL DEFAULT false CHECK(NOT send_authorized),
 retry_external boolean NOT NULL DEFAULT false CHECK(NOT retry_external),
 ack_allowed boolean NOT NULL DEFAULT false CHECK(NOT ack_allowed),
 production_authorized boolean NOT NULL DEFAULT false CHECK(NOT production_authorized),
 delivery_confirmed boolean NOT NULL DEFAULT false CHECK(NOT delivery_confirmed),
 definitive_failure_count_increment boolean NOT NULL DEFAULT false
   CHECK(NOT definitive_failure_count_increment),
 case_transition_authorized boolean NOT NULL DEFAULT false
   CHECK(NOT case_transition_authorized),
 PRIMARY KEY(shop_ref,case_ref,attempt_ref,event_ref,body_sha256),
 FOREIGN KEY(shop_ref,case_ref,attempt_ref)
   REFERENCES wa33_lab.bindings(shop_ref,case_ref,attempt_ref)
);
CREATE TABLE wa38_lab.quarantine (
 shop_ref text NOT NULL,case_ref text NOT NULL,attempt_ref text NOT NULL,
 event_ref text NOT NULL,
 reason text NOT NULL CHECK(reason IN
   ('LAB_DIFFERENT_BODY_SAME_EVENT','LAB_SAME_BODY_KIND_CONFLICT')),
 PRIMARY KEY(shop_ref,case_ref,attempt_ref,event_ref),
 FOREIGN KEY(shop_ref,case_ref,attempt_ref)
   REFERENCES wa33_lab.bindings(shop_ref,case_ref,attempt_ref)
);
CREATE FUNCTION wa38_lab.archive_fixture(
 p_app text,p_waba text,p_phone text,p_wamid text,p_recipient text,
 p_event text,p_kind text,p_body_sha text,p_binding_revision integer
) RETURNS text LANGUAGE plpgsql AS $wa38$
DECLARE first_binding wa33_lab.bindings%ROWTYPE;
        current_binding wa33_lab.bindings%ROWTYPE;
        authority wa29_lab.authority%ROWTYPE;
        claim wa29_lab.claims%ROWTYPE;
        prev_kind text;
        has_prior boolean;
        late boolean;
BEGIN
 IF p_app IS NULL OR p_waba IS NULL OR p_phone IS NULL OR
    p_wamid IS NULL OR p_recipient IS NULL OR p_event IS NULL OR
    p_kind IS NULL OR p_body_sha IS NULL OR
    p_app !~ '^[A-Za-z0-9_.:-]{1,128}$' OR
    p_waba !~ '^[A-Za-z0-9_.:-]{1,128}$' OR
    p_phone !~ '^[0-9]{5,25}$' OR
    p_wamid !~ '^wamid[.][A-Za-z0-9_.:-]{1,128}$' OR
    p_recipient !~ '^[0-9]{8,15}$' OR
    p_event !~ '^[A-Za-z0-9_.:-]{1,128}$' OR
    p_body_sha !~ '^[0-9a-f]{64}$' OR
    p_kind NOT IN ('SENT_REPORTED','DELIVERED_REPORTED',
      'READ_REPORTED','FAILED_REPORTED') OR
    p_binding_revision IS NULL OR p_binding_revision<1
 THEN RETURN 'LAB_DENIED'; END IF;

 SELECT * INTO first_binding FROM wa33_lab.bindings
 WHERE app_ref=p_app AND waba_ref=p_waba AND phone_ref=p_phone
   AND wamid_ref=p_wamid;
 IF NOT FOUND THEN RETURN 'LAB_DENIED'; END IF;
 -- Same synthetic case lock order as WA33/WA34. This is NOT the
 -- ratified S0/S1 service lock hierarchy.
 SELECT * INTO authority FROM wa29_lab.authority
 WHERE shop_ref=first_binding.shop_ref AND case_ref=first_binding.case_ref
 FOR UPDATE;
 IF NOT FOUND THEN RETURN 'LAB_DENIED'; END IF;
 SELECT * INTO current_binding FROM wa33_lab.bindings
 WHERE shop_ref=first_binding.shop_ref AND case_ref=first_binding.case_ref
 AND attempt_ref=first_binding.attempt_ref FOR UPDATE;
 IF NOT FOUND OR current_binding IS DISTINCT FROM first_binding OR
    NOT current_binding.active OR
    current_binding.recipient_ref<>p_recipient OR
    current_binding.binding_revision<>p_binding_revision
 THEN RETURN 'LAB_DENIED'; END IF;
 SELECT * INTO claim FROM wa29_lab.claims
 WHERE shop_ref=current_binding.shop_ref AND
 case_ref=current_binding.case_ref AND
 attempt_ref=current_binding.attempt_ref FOR UPDATE;
 IF NOT FOUND THEN RETURN 'LAB_DENIED'; END IF;

 -- An exact same raw-body fingerprint with a different claimed kind
 -- is impossible under consistent trusted parsing. Do not overwrite.
 SELECT o.kind INTO prev_kind FROM wa38_lab.observations o
 WHERE o.shop_ref=claim.shop_ref AND o.case_ref=claim.case_ref
   AND o.attempt_ref=claim.attempt_ref
   AND o.event_ref=p_event AND o.body_sha256=p_body_sha FOR UPDATE;
 IF FOUND THEN
  IF prev_kind=p_kind THEN RETURN 'LAB_EXACT_BODY_REPLAY_NO_RETRY'; END IF;
  INSERT INTO wa38_lab.quarantine(shop_ref,case_ref,attempt_ref,event_ref,reason)
   VALUES(claim.shop_ref,claim.case_ref,claim.attempt_ref,p_event,
          'LAB_SAME_BODY_KIND_CONFLICT')
   ON CONFLICT(shop_ref,case_ref,attempt_ref,event_ref)
   DO UPDATE SET reason='LAB_SAME_BODY_KIND_CONFLICT';
  RETURN 'LAB_KIND_CONFLICT_QUARANTINED';
 END IF;

 SELECT EXISTS(SELECT 1 FROM wa38_lab.observations o
   WHERE o.shop_ref=claim.shop_ref AND o.case_ref=claim.case_ref
   AND o.attempt_ref=claim.attempt_ref AND o.event_ref=p_event)
 INTO has_prior;
 late:=claim.state='LAB_INVALIDATED' OR
   claim.authority_version<>authority.state_version OR
   NOT authority.consent_ok OR authority.opted_out OR
   NOT authority.case_ok OR NOT authority.grant_ok OR
   NOT authority.template_ok OR NOT authority.campaign_ok;
 INSERT INTO wa38_lab.observations(
  shop_ref,case_ref,attempt_ref,event_ref,body_sha256,kind,after_invalidation
 ) VALUES(claim.shop_ref,claim.case_ref,claim.attempt_ref,
   p_event,p_body_sha,p_kind,late);
 IF has_prior THEN
  INSERT INTO wa38_lab.quarantine(shop_ref,case_ref,attempt_ref,event_ref,reason)
   VALUES(claim.shop_ref,claim.case_ref,claim.attempt_ref,p_event,
          'LAB_DIFFERENT_BODY_SAME_EVENT')
   ON CONFLICT DO NOTHING;
  RETURN 'LAB_BODY_VARIANT_QUARANTINED';
 END IF;
 RETURN CASE WHEN late THEN 'LAB_LATE_OBSERVATION_UNVERIFIED'
             ELSE 'LAB_FIRST_OBSERVATION_UNVERIFIED' END;
END $wa38$;

-- Only aggregate / authority-free classification; never leak body SHA,
-- phone or case to a consumer. S0 must own the actual trusted reader.
CREATE FUNCTION wa38_lab.read_fixture(
 p_shop text,p_case text,p_attempt text,p_event text
) RETURNS jsonb LANGUAGE plpgsql STABLE AS $wa38_read$
DECLARE n integer;
        is_late boolean;
        quarantined boolean;
        status text;
BEGIN
 SELECT count(*),coalesce(bool_or(o.after_invalidation),false)
 INTO n,is_late FROM wa38_lab.observations o
 WHERE o.shop_ref=p_shop AND o.case_ref=p_case
   AND o.attempt_ref=p_attempt AND o.event_ref=p_event;
 SELECT EXISTS(SELECT 1 FROM wa38_lab.quarantine q
 WHERE q.shop_ref=p_shop AND q.case_ref=p_case
  AND q.attempt_ref=p_attempt AND q.event_ref=p_event) INTO quarantined;
 status:=CASE WHEN quarantined THEN 'LAB_MULTIPLE_OR_CONFLICT_QUARANTINED'
   WHEN n=0 THEN 'LAB_NONE'
   WHEN is_late THEN 'LAB_LATE_UNVERIFIED'
   ELSE 'LAB_SINGLE_UNVERIFIED' END;
 RETURN jsonb_build_object(
  'outcome',status,'retry_external',false,'send_authorized',false,
  'ack_allowed',false,'production_authorized',false,
  'delivery_confirmed',false,'definitive_failure_count_increment',false,
  'case_transition_authorized',false);
END $wa38_read$;

SELECT 'WA38-SETUP PASS'
WHERE (SELECT count(*) FROM wa38_lab.observations)=0
 AND (SELECT count(*) FROM wa38_lab.quarantine)=0;
