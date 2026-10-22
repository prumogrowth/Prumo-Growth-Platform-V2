-- WA30: synthetic readback/evidence audit AFTER WA29 physical claim tests.
-- Depends on disposable wa29_lab (CI only); NOT a S0 migration / Graph API.
\set ON_ERROR_STOP on
CREATE SCHEMA wa30_lab;
CREATE TABLE wa30_lab.evidence (
 shop_ref text NOT NULL,case_ref text NOT NULL,attempt_ref text NOT NULL,
 event_ref text NOT NULL,event_kind text NOT NULL
 CHECK(event_kind IN ('UNKNOWN','ACCEPTED','SENT_REPORTED','FAILED_REPORTED')),
 send_authorized boolean NOT NULL DEFAULT false CHECK(NOT send_authorized),
 production_authorized boolean NOT NULL DEFAULT false CHECK(NOT production_authorized),
 definitive_failure_count_increment boolean NOT NULL DEFAULT false
 CHECK(NOT definitive_failure_count_increment),
 PRIMARY KEY(shop_ref,case_ref,attempt_ref,event_ref),
 FOREIGN KEY(shop_ref,case_ref,attempt_ref)
   REFERENCES wa29_lab.reservations(shop_ref,case_ref,attempt_ref)
);
CREATE TABLE wa30_lab.quarantine (
 shop_ref text NOT NULL,case_ref text NOT NULL,attempt_ref text NOT NULL,
 reason text NOT NULL CHECK(reason='LAB_CONFLICTING_RECEIPT'),
 PRIMARY KEY(shop_ref,case_ref,attempt_ref),
 FOREIGN KEY(shop_ref,case_ref,attempt_ref)
  REFERENCES wa29_lab.reservations(shop_ref,case_ref,attempt_ref)
);

-- Additional cases are created on the same synthetic WA29 authority/claim
-- fixture, whose real row locks remain the sole serialization point.
WITH seeds(shop_ref,case_ref,attempt_ref) AS (
 VALUES ('shop_A','case_unknown','attempt_unknown'),
 ('shop_A','case_accepted','attempt_accepted'),
 ('shop_A','case_sent','attempt_sent'),
 ('shop_A','case_failed','attempt_failed'),
 ('shop_A','case_conflict','attempt_conflict'),
 ('shop_A','case_invalidated','attempt_invalidated'),
 ('shop_A','case_revoke_first','attempt_revoke_first'),
 ('shop_A','case_absent','attempt_absent'),
 ('shop_A','case_rollback30','attempt_rollback30'),
 ('shop_A','case_receipt_collision','attempt_receipt_collision'),
 ('shop_A','case_race','attempt_race'),
 ('shop_B','case_b30','attempt_b30')
)
INSERT INTO wa29_lab.authority
 (shop_ref,case_ref,actor_ref,state_version,catalog_revision,
  consent_ok,opted_out,case_ok,grant_ok,template_ok,campaign_ok)
SELECT s.shop_ref,s.case_ref,
 CASE WHEN s.shop_ref='shop_B' THEN 'planner_B' ELSE 'planner_A' END,
 1,10,true,false,true,true,true,true FROM seeds s;
INSERT INTO wa29_lab.reservations
 (shop_ref,case_ref,attempt_ref,actor_ref,state_version,catalog_revision)
SELECT shop_ref,case_ref,
 'attempt_'||substring(case_ref from 6),
 CASE WHEN shop_ref='shop_B' THEN 'planner_B' ELSE 'planner_A' END,
 1,10
 FROM wa29_lab.authority WHERE case_ref IN (
 'case_unknown','case_accepted','case_sent','case_failed','case_conflict',
 'case_invalidated','case_revoke_first','case_absent','case_rollback30',
 'case_receipt_collision','case_race','case_b30');

DO $wa30_seed$
DECLARE r record; outcome text;
BEGIN
 FOR r IN SELECT shop_ref,case_ref,attempt_ref,actor_ref
  FROM wa29_lab.reservations WHERE case_ref IN (
   'case_unknown','case_accepted','case_sent','case_failed','case_conflict',
   'case_invalidated','case_revoke_first','case_rollback30',
   'case_receipt_collision','case_race','case_b30')
 LOOP
  SELECT wa29_lab.claim_fixture(r.shop_ref,r.case_ref,r.actor_ref,
   r.attempt_ref,1,10) INTO outcome;
  IF outcome<>'LAB_CLAIMED_NO_SEND_RIGHTS' THEN
   RAISE EXCEPTION 'WA30_SETUP_CLAIM_NOT_CREATED_%: %',r.case_ref,outcome;
  END IF;
 END LOOP;
END $wa30_seed$;

-- Same lock order as WA29.revoke_fixture; none of the fields imply actual
-- Graph submission, ACK, WhatsApp delivery or definitive cadence failure.
CREATE FUNCTION wa30_lab.record_fixture(
 p_shop text,p_case text,p_attempt text,p_event text,p_kind text
) RETURNS text LANGUAGE plpgsql AS $wa30_record$
DECLARE a wa29_lab.authority%ROWTYPE;
        claim wa29_lab.claims%ROWTYPE;
        existing text;
BEGIN
 IF p_shop IS NULL OR p_case IS NULL OR p_attempt IS NULL OR
    p_event IS NULL OR p_kind IS NULL OR
    p_shop !~ '^[A-Za-z0-9_]{1,64}$' OR
    p_case !~ '^[A-Za-z0-9_]{1,64}$' OR
    p_attempt !~ '^[A-Za-z0-9_]{1,64}$' OR
    p_event !~ '^[A-Za-z0-9_]{1,64}$' OR
    p_kind NOT IN ('UNKNOWN','ACCEPTED','SENT_REPORTED','FAILED_REPORTED')
 THEN RETURN 'LAB_DENIED'; END IF;
 SELECT * INTO a FROM wa29_lab.authority WHERE shop_ref=p_shop AND
  case_ref=p_case FOR UPDATE;
 IF NOT FOUND OR NOT a.consent_ok OR a.opted_out OR NOT a.case_ok OR
    NOT a.grant_ok OR NOT a.template_ok OR NOT a.campaign_ok THEN
  RETURN 'LAB_DENIED';
 END IF;
 SELECT * INTO claim FROM wa29_lab.claims WHERE shop_ref=p_shop AND
  case_ref=p_case FOR UPDATE;
 IF NOT FOUND OR claim.attempt_ref<>p_attempt OR
    claim.state<>'LAB_CLAIMED' OR claim.authority_version<>a.state_version THEN
  RETURN 'LAB_DENIED';
 END IF;
 IF EXISTS(SELECT 1 FROM wa30_lab.quarantine q WHERE q.shop_ref=p_shop AND
    q.case_ref=p_case AND q.attempt_ref=p_attempt) THEN RETURN 'LAB_QUARANTINED'; END IF;
 SELECT event_kind INTO existing FROM wa30_lab.evidence WHERE
  shop_ref=p_shop AND case_ref=p_case AND attempt_ref=p_attempt AND event_ref=p_event;
 IF FOUND THEN
  IF existing=p_kind THEN RETURN 'LAB_REPLAY_NO_RESEND'; END IF;
  INSERT INTO wa30_lab.quarantine(shop_ref,case_ref,attempt_ref,reason)
   VALUES (p_shop,p_case,p_attempt,'LAB_CONFLICTING_RECEIPT')
   ON CONFLICT DO NOTHING;
  RETURN 'LAB_QUARANTINED';
 END IF;
 INSERT INTO wa30_lab.evidence(shop_ref,case_ref,attempt_ref,event_ref,event_kind)
  VALUES (p_shop,p_case,p_attempt,p_event,p_kind);
 RETURN 'LAB_RECORDED_UNVERIFIED';
END $wa30_record$;

-- A read cannot convert fixture evidence into a trusted Meta outcome. A
-- missing row is uncertainty, never proof that Graph did not accept a POST.
CREATE FUNCTION wa30_lab.read_fixture(p_shop text,p_case text,p_attempt text)
RETURNS jsonb LANGUAGE plpgsql STABLE AS $wa30_read$
DECLARE a wa29_lab.authority%ROWTYPE;
        claim wa29_lab.claims%ROWTYPE;
        k text:='LAB_ABSENT_UNKNOWN';
        received boolean;
        sent boolean;
        failed boolean;
BEGIN
 IF p_shop IS NOT NULL AND p_case IS NOT NULL AND p_attempt IS NOT NULL AND
    p_shop ~ '^[A-Za-z0-9_]{1,64}$' AND
    p_case ~ '^[A-Za-z0-9_]{1,64}$' AND
    p_attempt ~ '^[A-Za-z0-9_]{1,64}$' THEN
  SELECT * INTO a FROM wa29_lab.authority
   WHERE shop_ref=p_shop AND case_ref=p_case;
  IF FOUND THEN
   SELECT * INTO claim FROM wa29_lab.claims
    WHERE shop_ref=p_shop AND case_ref=p_case AND attempt_ref=p_attempt;
   IF FOUND THEN
    IF claim.state='LAB_INVALIDATED' OR
       a.state_version<>claim.authority_version OR
       NOT a.consent_ok OR a.opted_out OR NOT a.case_ok OR
       NOT a.grant_ok OR NOT a.template_ok OR NOT a.campaign_ok THEN
      k:='LAB_INVALIDATED';
    ELSIF EXISTS(SELECT 1 FROM wa30_lab.quarantine q
      WHERE q.shop_ref=p_shop AND q.case_ref=p_case
      AND q.attempt_ref=p_attempt) THEN
      k:='LAB_CONFLICT';
    ELSE
      SELECT
       coalesce(bool_or(e.event_kind='ACCEPTED'),false),
       coalesce(bool_or(e.event_kind='SENT_REPORTED'),false),
       coalesce(bool_or(e.event_kind='FAILED_REPORTED'),false)
      INTO received,sent,failed
      FROM wa30_lab.evidence e WHERE e.shop_ref=p_shop AND
       e.case_ref=p_case AND e.attempt_ref=p_attempt;
      k:=CASE
       WHEN sent AND failed THEN 'LAB_CONFLICT'
       WHEN sent THEN 'LAB_SENT_UNVERIFIED'
       WHEN failed THEN 'LAB_FAILURE_UNVERIFIED'
       WHEN received THEN 'LAB_PROVIDER_ACCEPTED_UNVERIFIED'
       ELSE 'LAB_CLAIM_UNRESOLVED' END;
    END IF;
   END IF;
  END IF;
 END IF;
 RETURN jsonb_build_object(
  'outcome',k,'retry_external',false,'send_authorized',false,
  'ack_allowed',false,'production_authorized',false,'delivery_confirmed',false,
  'definitive_failure_count_increment',false,'case_transition_authorized',false);
END $wa30_read$;
SELECT 'WA30-SETUP PASS' WHERE
 (SELECT count(*) FROM wa29_lab.authority WHERE case_ref LIKE 'case_%')>=12 AND
 (SELECT count(*) FROM wa29_lab.claims WHERE case_ref IN
 ('case_unknown','case_accepted','case_sent','case_failed','case_conflict',
  'case_invalidated','case_revoke_first','case_rollback30',
  'case_receipt_collision','case_race','case_b30'))=11;
