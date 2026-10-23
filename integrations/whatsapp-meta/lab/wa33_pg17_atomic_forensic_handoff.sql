-- WA33: isolated, disposable PG17 candidate for S0 forensic commit after WA32.
-- NEVER USE AS S0 MIGRATION. This has NO authenticated caller / actual Meta HMAC.
-- A fake internally seeded channel binding is NOT proof of signed provenance.
\set ON_ERROR_STOP on
CREATE SCHEMA wa33_lab;
CREATE TABLE wa33_lab.bindings (
  shop_ref text NOT NULL, case_ref text NOT NULL, attempt_ref text NOT NULL,
  app_ref text NOT NULL, channel_ref text NOT NULL, waba_ref text NOT NULL,
  phone_ref text NOT NULL, wamid_ref text NOT NULL, recipient_ref text NOT NULL,
  binding_revision integer NOT NULL CHECK(binding_revision>0),
  active boolean NOT NULL DEFAULT true,
  PRIMARY KEY(shop_ref,case_ref,attempt_ref),
  UNIQUE(app_ref,waba_ref,phone_ref,wamid_ref),
  FOREIGN KEY(shop_ref,case_ref,attempt_ref)
    REFERENCES wa29_lab.reservations(shop_ref,case_ref,attempt_ref)
);
CREATE TABLE wa33_lab.events (
  shop_ref text NOT NULL,case_ref text NOT NULL,attempt_ref text NOT NULL,
  event_ref text NOT NULL,kind text NOT NULL
     CHECK(kind IN ('SENT_REPORTED','DELIVERED_REPORTED','READ_REPORTED','FAILED_REPORTED')),
  after_invalidation boolean NOT NULL,
  send_authorized boolean NOT NULL DEFAULT false CHECK(NOT send_authorized),
  production_authorized boolean NOT NULL DEFAULT false CHECK(NOT production_authorized),
  ack_allowed boolean NOT NULL DEFAULT false CHECK(NOT ack_allowed),
  definitive_failure_count_increment boolean NOT NULL DEFAULT false
    CHECK(NOT definitive_failure_count_increment),
  PRIMARY KEY(shop_ref,case_ref,attempt_ref,event_ref),
  FOREIGN KEY(shop_ref,case_ref,attempt_ref)
    REFERENCES wa33_lab.bindings(shop_ref,case_ref,attempt_ref)
);
CREATE TABLE wa33_lab.quarantine (
  shop_ref text NOT NULL,case_ref text NOT NULL,attempt_ref text NOT NULL,
  reason text NOT NULL CHECK(reason='LAB_EVENT_KIND_CONFLICT'),
  PRIMARY KEY(shop_ref,case_ref,attempt_ref),
  FOREIGN KEY(shop_ref,case_ref,attempt_ref)
    REFERENCES wa33_lab.bindings(shop_ref,case_ref,attempt_ref)
);
INSERT INTO wa33_lab.bindings
 (shop_ref,case_ref,attempt_ref,app_ref,channel_ref,waba_ref,phone_ref,
  wamid_ref,recipient_ref,binding_revision)
VALUES
 ('shop_A','case31_hist','attempt31_hist','APP_A','CHANNEL_A','111111','1234567890','wamid.WA33_HIST','5581900000000',1),
 ('shop_A','case31_empty','attempt31_empty','APP_A','CHANNEL_A','111111','1234567890','wamid.WA33_REVOKE_FIRST','5581900000000',1),
 ('shop_A','case31_rollback','attempt31_rollback','APP_A','CHANNEL_A','111111','1234567890','wamid.WA33_APPEND_FIRST','5581900000000',1),
 ('shop_A','case31_conflict','attempt31_conflict','APP_A','CHANNEL_A','111111','1234567890','wamid.WA33_DUPLICATE','5581900000000',1),
 ('shop_A','case31_late','attempt31_late','APP_A','CHANNEL_A','111111','1234567890','wamid.WA33_LATE','5581900000000',1),
 ('shop_A','case31_no_claim','attempt31_no_claim','APP_A','CHANNEL_A','111111','1234567890','wamid.WA33_MISSING_CLAIM','5581900000000',1),
 ('shop_B','case31_b','attempt31_b','APP_B','CHANNEL_B','222222','9876543210','wamid.WA33_B','5581900000011',1);

-- This is a proposed ONE-TRANSACTION gate. Does not authenticate its arguments.
-- lock order: synthetic authority -> binding -> synthetic claim -> event.
CREATE FUNCTION wa33_lab.append_fixture(
  p_app text,p_waba text,p_phone text,p_wamid text,p_recipient text,
  p_event text,p_kind text,p_expected_revision int
) RETURNS text LANGUAGE plpgsql AS $body$
DECLARE observed wa33_lab.bindings%ROWTYPE;
        current_binding wa33_lab.bindings%ROWTYPE;
        a wa29_lab.authority%ROWTYPE;
        claim wa29_lab.claims%ROWTYPE;
        old_kind text;
        late boolean;
BEGIN
  IF p_app IS NULL OR p_waba IS NULL OR p_phone IS NULL OR
     p_wamid IS NULL OR p_recipient IS NULL OR p_event IS NULL OR p_kind IS NULL OR
     p_app !~ '^[A-Za-z0-9_.:-]{1,128}$' OR
     p_waba !~ '^[A-Za-z0-9_.:-]{1,128}$' OR
     p_phone !~ '^[0-9]{5,25}$' OR
     p_wamid !~ '^wamid\\.[A-Za-z0-9_.:-]{1,128}$' OR
     p_recipient !~ '^[0-9]{8,15}$' OR
     p_event !~ '^[A-Za-z0-9_.:-]{1,128}$' OR
     p_kind NOT IN ('SENT_REPORTED','DELIVERED_REPORTED','READ_REPORTED','FAILED_REPORTED') OR
     p_expected_revision IS NULL OR p_expected_revision<=0
  THEN RETURN 'LAB_DENIED'; END IF;
  SELECT * INTO observed FROM wa33_lab.bindings
   WHERE app_ref=p_app AND waba_ref=p_waba AND phone_ref=p_phone
     AND wamid_ref=p_wamid;
  IF NOT FOUND THEN RETURN 'LAB_DENIED'; END IF;
  SELECT * INTO a FROM wa29_lab.authority
   WHERE shop_ref=observed.shop_ref AND case_ref=observed.case_ref FOR UPDATE;
  IF NOT FOUND THEN RETURN 'LAB_DENIED'; END IF;
  SELECT * INTO current_binding FROM wa33_lab.bindings
   WHERE shop_ref=observed.shop_ref AND case_ref=observed.case_ref
     AND attempt_ref=observed.attempt_ref FOR UPDATE;
  IF NOT FOUND OR current_binding IS DISTINCT FROM observed OR
     NOT current_binding.active OR
     current_binding.recipient_ref<>p_recipient OR
     current_binding.binding_revision<>p_expected_revision
  THEN RETURN 'LAB_DENIED'; END IF;
  SELECT * INTO claim FROM wa29_lab.claims
   WHERE shop_ref=current_binding.shop_ref AND case_ref=current_binding.case_ref
     AND attempt_ref=current_binding.attempt_ref FOR UPDATE;
  IF NOT FOUND THEN RETURN 'LAB_DENIED'; END IF;
  IF EXISTS(SELECT 1 FROM wa33_lab.quarantine q
       WHERE q.shop_ref=claim.shop_ref AND q.case_ref=claim.case_ref
         AND q.attempt_ref=claim.attempt_ref)
  THEN RETURN 'LAB_QUARANTINED'; END IF;
  SELECT e.kind INTO old_kind FROM wa33_lab.events e
     WHERE e.shop_ref=claim.shop_ref AND e.case_ref=claim.case_ref
       AND e.attempt_ref=claim.attempt_ref AND e.event_ref=p_event FOR UPDATE;
  IF FOUND THEN
    IF old_kind=p_kind THEN RETURN 'LAB_REPLAY_NO_RETRY'; END IF;
    INSERT INTO wa33_lab.quarantine(shop_ref,case_ref,attempt_ref,reason)
      VALUES(claim.shop_ref,claim.case_ref,claim.attempt_ref,'LAB_EVENT_KIND_CONFLICT')
      ON CONFLICT DO NOTHING;
    RETURN 'LAB_QUARANTINED';
  END IF;
  late:=claim.state='LAB_INVALIDATED' OR claim.authority_version<>a.state_version OR
    NOT a.consent_ok OR a.opted_out OR NOT a.case_ok OR NOT a.grant_ok OR
    NOT a.template_ok OR NOT a.campaign_ok;
  INSERT INTO wa33_lab.events(shop_ref,case_ref,attempt_ref,event_ref,kind,after_invalidation)
    VALUES(claim.shop_ref,claim.case_ref,claim.attempt_ref,p_event,p_kind,late);
  RETURN CASE WHEN late THEN 'LAB_ARCHIVED_LATE_NO_SEND'
    ELSE 'LAB_ARCHIVED_UNVERIFIED_NO_SEND' END;
END;
$body$;

-- Fixture control, NOT authorization: same authority lock as append/revoke.
CREATE FUNCTION wa33_lab.change_binding_fixture(
  p_shop text,p_case text,p_new_recipient text
) RETURNS text LANGUAGE plpgsql AS $body$
DECLARE old_binding wa33_lab.bindings%ROWTYPE;
BEGIN
  IF p_shop IS NULL OR p_case IS NULL OR
     p_new_recipient IS NULL OR p_new_recipient !~ '^[0-9]{8,15}$'
  THEN RETURN 'LAB_DENIED'; END IF;
  PERFORM 1 FROM wa29_lab.authority WHERE shop_ref=p_shop
    AND case_ref=p_case FOR UPDATE;
  IF NOT FOUND THEN RETURN 'LAB_DENIED'; END IF;
  SELECT * INTO old_binding FROM wa33_lab.bindings
    WHERE shop_ref=p_shop AND case_ref=p_case FOR UPDATE;
  IF NOT FOUND OR old_binding.recipient_ref=p_new_recipient
  THEN RETURN 'LAB_DENIED'; END IF;
  UPDATE wa33_lab.bindings SET recipient_ref=p_new_recipient,
    binding_revision=binding_revision+1
    WHERE shop_ref=p_shop AND case_ref=p_case;
  RETURN 'LAB_BINDING_CHANGED';
END;
$body$;

SELECT 'WA33-SETUP PASS'
WHERE (SELECT count(*) FROM wa33_lab.bindings)=7
  AND (SELECT count(*) FROM wa33_lab.events)=0
  AND (SELECT count(*) FROM wa33_lab.quarantine)=0;
