-- WA31: ISOLATED PG17 forensic event lab only; not Meta webhooks, S0 or migrations.
-- Records simulated late evidence AFTER revocation of an existing attempt,
-- without unlocking the claim, updating WA30 evidence or authorizing a POST.
\set ON_ERROR_STOP on
CREATE SCHEMA wa31_lab;
CREATE TABLE wa31_lab.observations (
 shop_ref text NOT NULL,case_ref text NOT NULL,attempt_ref text NOT NULL,
 event_ref text NOT NULL,event_kind text NOT NULL
  CHECK(event_kind IN ('UNKNOWN','ACCEPTED','SENT_REPORTED','FAILED_REPORTED')),
 observed_after_invalidation boolean NOT NULL,
 send_authorized boolean NOT NULL DEFAULT false CHECK(NOT send_authorized),
 production_authorized boolean NOT NULL DEFAULT false CHECK(NOT production_authorized),
 ack_allowed boolean NOT NULL DEFAULT false CHECK(NOT ack_allowed),
 definitive_failure_count_increment boolean NOT NULL DEFAULT false
   CHECK(NOT definitive_failure_count_increment),
 PRIMARY KEY(shop_ref,case_ref,attempt_ref,event_ref),
 FOREIGN KEY(shop_ref,case_ref,attempt_ref)
  REFERENCES wa29_lab.reservations(shop_ref,case_ref,attempt_ref)
);
CREATE TABLE wa31_lab.quarantines (
 shop_ref text NOT NULL,case_ref text NOT NULL,attempt_ref text NOT NULL,
 reason text NOT NULL CHECK(reason='LAB_KIND_CONFLICT'),
 PRIMARY KEY(shop_ref,case_ref,attempt_ref),
 FOREIGN KEY(shop_ref,case_ref,attempt_ref)
  REFERENCES wa29_lab.reservations(shop_ref,case_ref,attempt_ref)
);

WITH seed(shop_ref,case_ref,attempt_ref) AS (
 VALUES ('shop_A','case31_hist','attempt31_hist'),
 ('shop_A','case31_late','attempt31_late'),
 ('shop_A','case31_conflict','attempt31_conflict'),
 ('shop_A','case31_empty','attempt31_empty'),
 ('shop_A','case31_rollback','attempt31_rollback'),
 ('shop_A','case31_revoke_first','attempt31_revoke_first'),
 ('shop_A','case31_observe_first','attempt31_observe_first'),
 ('shop_A','case31_no_claim','attempt31_no_claim'),
 ('shop_B','case31_b','attempt31_b')
)
INSERT INTO wa29_lab.authority(
 shop_ref,case_ref,actor_ref,state_version,catalog_revision,
 consent_ok,opted_out,case_ok,grant_ok,template_ok,campaign_ok
)
SELECT shop_ref,case_ref,
 CASE WHEN shop_ref='shop_B' THEN 'planner_B' ELSE 'planner_A' END,
 1,10,true,false,true,true,true,true FROM seed;
INSERT INTO wa29_lab.reservations(
 shop_ref,case_ref,attempt_ref,actor_ref,state_version,catalog_revision
)
SELECT a.shop_ref,a.case_ref,'attempt31_'||substring(a.case_ref from 8),
 a.actor_ref,1,10
FROM wa29_lab.authority a WHERE a.case_ref LIKE 'case31_%';
DO $wa31_seed$
DECLARE r record;k text;
BEGIN
 FOR r IN SELECT * FROM wa29_lab.reservations
  WHERE case_ref LIKE 'case31_%' AND case_ref<>'case31_no_claim'
 LOOP
  SELECT wa29_lab.claim_fixture(r.shop_ref,r.case_ref,r.actor_ref,
    r.attempt_ref,1,10) INTO k;
  IF k<>'LAB_CLAIMED_NO_SEND_RIGHTS' THEN
    RAISE EXCEPTION 'WA31_SEED_CLAIM_FAILED % %',r.case_ref,k;
  END IF;
 END LOOP;
END $wa31_seed$;

-- Forensic ingestion is deliberately distinct from WA30 operational gates.
-- It may archive evidence for an INVALIDATED claim, but NEVER revive it.
-- Lock order authority -> claim -> observation mirrors WA29's local order.
CREATE FUNCTION wa31_lab.archive_fixture(
 p_shop text,p_case text,p_attempt text,p_event text,p_kind text
) RETURNS text LANGUAGE plpgsql AS $wa31_archive$
DECLARE a wa29_lab.authority%ROWTYPE;
        c wa29_lab.claims%ROWTYPE;
        old_kind text;
        late boolean;
BEGIN
 IF p_shop IS NULL OR p_case IS NULL OR p_attempt IS NULL OR
    p_event IS NULL OR p_kind IS NULL OR
    p_shop !~ '^[A-Za-z0-9_]{1,64}$' OR
    p_case !~ '^[A-Za-z0-9_]{1,64}$' OR
    p_attempt !~ '^[A-Za-z0-9_]{1,64}$' OR
    p_event !~ '^[A-Za-z0-9_]{1,64}$' OR
    p_kind NOT IN ('UNKNOWN','ACCEPTED','SENT_REPORTED','FAILED_REPORTED')
 THEN RETURN 'LAB_DENIED'; END IF;
 SELECT * INTO a FROM wa29_lab.authority WHERE shop_ref=p_shop
  AND case_ref=p_case FOR UPDATE;
 IF NOT FOUND THEN RETURN 'LAB_DENIED'; END IF;
 SELECT * INTO c FROM wa29_lab.claims WHERE shop_ref=p_shop AND
  case_ref=p_case AND attempt_ref=p_attempt FOR UPDATE;
 IF NOT FOUND THEN RETURN 'LAB_DENIED'; END IF;
 IF EXISTS(SELECT 1 FROM wa31_lab.quarantines WHERE shop_ref=p_shop AND
    case_ref=p_case AND attempt_ref=p_attempt) THEN RETURN 'LAB_QUARANTINED'; END IF;
 SELECT o.event_kind INTO old_kind FROM wa31_lab.observations o
 WHERE o.shop_ref=p_shop AND o.case_ref=p_case AND
  o.attempt_ref=p_attempt AND o.event_ref=p_event FOR UPDATE;
 IF FOUND THEN
  IF old_kind=p_kind THEN RETURN 'LAB_REPLAY_NO_RESEND'; END IF;
  INSERT INTO wa31_lab.quarantines(shop_ref,case_ref,attempt_ref,reason)
   VALUES(p_shop,p_case,p_attempt,'LAB_KIND_CONFLICT')
   ON CONFLICT DO NOTHING;
  RETURN 'LAB_QUARANTINED';
 END IF;
 late:=c.state='LAB_INVALIDATED' OR a.state_version<>c.authority_version OR
  NOT a.consent_ok OR a.opted_out OR NOT a.case_ok OR NOT a.grant_ok OR
  NOT a.template_ok OR NOT a.campaign_ok;
 INSERT INTO wa31_lab.observations(
  shop_ref,case_ref,attempt_ref,event_ref,event_kind,observed_after_invalidation
 ) VALUES(p_shop,p_case,p_attempt,p_event,p_kind,late);
 RETURN CASE WHEN late THEN 'LAB_ARCHIVED_AFTER_REVOCATION'
             ELSE 'LAB_ARCHIVED_UNVERIFIED' END;
END $wa31_archive$;

CREATE FUNCTION wa31_lab.read_fixture(
 p_shop text,p_case text,p_attempt text
) RETURNS jsonb LANGUAGE plpgsql STABLE AS $wa31_read$
DECLARE a wa29_lab.authority%ROWTYPE;
        c wa29_lab.claims%ROWTYPE;
        k text:='LAB_NO_CLAIM'; observed boolean;late boolean;invalid boolean;
BEGIN
 IF p_shop IS NOT NULL AND p_case IS NOT NULL AND p_attempt IS NOT NULL
  AND p_shop ~ '^[A-Za-z0-9_]{1,64}$'
  AND p_case ~ '^[A-Za-z0-9_]{1,64}$'
  AND p_attempt ~ '^[A-Za-z0-9_]{1,64}$' THEN
  SELECT * INTO a FROM wa29_lab.authority WHERE shop_ref=p_shop AND case_ref=p_case;
  IF FOUND THEN
   SELECT * INTO c FROM wa29_lab.claims WHERE shop_ref=p_shop AND
     case_ref=p_case AND attempt_ref=p_attempt;
   IF FOUND THEN
    invalid:=c.state='LAB_INVALIDATED' OR a.state_version<>c.authority_version OR
      NOT a.consent_ok OR a.opted_out OR NOT a.case_ok OR NOT a.grant_ok OR
      NOT a.template_ok OR NOT a.campaign_ok;
    SELECT coalesce(bool_or(true),false),
      coalesce(bool_or(o.observed_after_invalidation),false)
      INTO observed,late FROM wa31_lab.observations o
      WHERE o.shop_ref=p_shop AND o.case_ref=p_case AND o.attempt_ref=p_attempt;
    k:=CASE
      WHEN EXISTS(SELECT 1 FROM wa31_lab.quarantines q WHERE
       q.shop_ref=p_shop AND q.case_ref=p_case AND q.attempt_ref=p_attempt)
        THEN 'LAB_KIND_CONFLICT'
      WHEN late THEN 'LAB_LATE_OBSERVATION'
      WHEN invalid AND observed THEN 'LAB_INVALIDATED_HISTORICAL'
      WHEN invalid THEN 'LAB_INVALIDATED_EMPTY'
      WHEN observed THEN 'LAB_ACTIVE_OBSERVATION'
      ELSE 'LAB_EMPTY_CLAIM' END;
   END IF;
  END IF;
 END IF;
 RETURN jsonb_build_object('outcome',k,'retry_external',false,
  'send_authorized',false,'ack_allowed',false,'production_authorized',false,
  'delivery_confirmed',false,'definitive_failure_count_increment',false,
  'case_transition_authorized',false);
END $wa31_read$;
SELECT 'WA31-SETUP PASS' WHERE
 (SELECT count(*) FROM wa29_lab.authority WHERE case_ref LIKE 'case31_%')=9
 AND (SELECT count(*) FROM wa29_lab.claims WHERE case_ref LIKE 'case31_%')=8
 AND (SELECT count(*) FROM wa31_lab.observations)=0;
