-- WA29: FICTITIOUS PG17-only serializable pre-dispatch CLAIM laboratory.
-- NO Graph call, no S0/S1 deployment, no authenticated actors, no send rights.
-- A claim is bookkeeping, NOT permission to send, and NOT delivery proof.
\set ON_ERROR_STOP on
CREATE SCHEMA wa29_lab;
CREATE TABLE wa29_lab.authority (
  shop_ref text NOT NULL, case_ref text NOT NULL, actor_ref text NOT NULL,
  state_version int NOT NULL CHECK (state_version > 0),
  catalog_revision int NOT NULL CHECK (catalog_revision > 0),
  consent_ok boolean NOT NULL, opted_out boolean NOT NULL,
  case_ok boolean NOT NULL, grant_ok boolean NOT NULL,
  template_ok boolean NOT NULL, campaign_ok boolean NOT NULL,
  PRIMARY KEY (shop_ref,case_ref)
);
CREATE TABLE wa29_lab.reservations (
  shop_ref text NOT NULL, case_ref text NOT NULL, attempt_ref text NOT NULL,
  actor_ref text NOT NULL, state_version int NOT NULL,
  catalog_revision int NOT NULL,
  state text NOT NULL DEFAULT 'LAB_RESERVED'
    CHECK (state IN ('LAB_RESERVED','LAB_CLAIMED','LAB_CANCELLED')),
  send_authorized boolean NOT NULL DEFAULT false CHECK (NOT send_authorized),
  production_authorized boolean NOT NULL DEFAULT false CHECK (NOT production_authorized),
  PRIMARY KEY (shop_ref,case_ref,attempt_ref),
  FOREIGN KEY (shop_ref,case_ref) REFERENCES wa29_lab.authority(shop_ref,case_ref)
);
CREATE TABLE wa29_lab.claims (
  shop_ref text NOT NULL, case_ref text NOT NULL, attempt_ref text NOT NULL,
  state text NOT NULL CHECK (state IN ('LAB_CLAIMED','LAB_INVALIDATED')),
  authority_version int NOT NULL CHECK (authority_version>0),
  send_authorized boolean NOT NULL DEFAULT false CHECK (NOT send_authorized),
  production_authorized boolean NOT NULL DEFAULT false CHECK (NOT production_authorized),
  PRIMARY KEY (shop_ref,case_ref), -- at most one unresolved claim per case in this fixture
  FOREIGN KEY (shop_ref,case_ref,attempt_ref)
    REFERENCES wa29_lab.reservations(shop_ref,case_ref,attempt_ref)
);
INSERT INTO wa29_lab.authority
  (shop_ref,case_ref,actor_ref,state_version,catalog_revision,
   consent_ok,opted_out,case_ok,grant_ok,template_ok,campaign_ok)
VALUES
  ('shop_A','case_claim_first','planner_A',1,10,true,false,true,true,true,true),
  ('shop_A','case_revoke_first','planner_A',1,10,true,false,true,true,true,true),
  ('shop_A','case_two_claims','planner_A',1,10,true,false,true,true,true,true),
  ('shop_A','case_rollback','planner_A',1,10,true,false,true,true,true,true),
  ('shop_A','case_missing_grant','planner_A',1,10,true,false,true,false,true,true),
  ('shop_A','case_campaign_expired','planner_A',1,10,true,false,true,true,true,false),
  ('shop_B','case_control','planner_B',1,10,true,false,true,true,true,true);
INSERT INTO wa29_lab.reservations
  (shop_ref,case_ref,attempt_ref,actor_ref,state_version,catalog_revision)
VALUES
  ('shop_A','case_claim_first','attempt_a1','planner_A',1,10),
  ('shop_A','case_revoke_first','attempt_a2','planner_A',1,10),
  ('shop_A','case_two_claims','attempt_a3','planner_A',1,10),
  ('shop_A','case_two_claims','attempt_a4','planner_A',1,10),
  ('shop_A','case_rollback','attempt_a5','planner_A',1,10),
  ('shop_A','case_missing_grant','attempt_a6','planner_A',1,10),
  ('shop_A','case_campaign_expired','attempt_a7','planner_A',1,10),
  ('shop_B','case_control','attempt_b1','planner_B',1,10);

-- Both claim and revocation take authority row FIRST. The same order avoids
-- the fixture's own inversion; DOES NOT model or prove S1->S0 lock ordering.
CREATE FUNCTION wa29_lab.claim_fixture(
 p_shop text,p_case text,p_actor text,p_attempt text,
 p_version int,p_catalog int
) RETURNS text LANGUAGE plpgsql AS $$
DECLARE a wa29_lab.authority%ROWTYPE;
        reservation wa29_lab.reservations%ROWTYPE;
        prior wa29_lab.claims%ROWTYPE;
BEGIN
 IF p_shop IS NULL OR p_case IS NULL OR p_actor IS NULL OR p_attempt IS NULL OR
    p_shop !~ '^[A-Za-z0-9_]{1,64}$' OR
    p_case !~ '^[A-Za-z0-9_]{1,64}$' OR
    p_actor !~ '^[A-Za-z0-9_]{1,64}$' OR
    p_attempt !~ '^[A-Za-z0-9_]{1,64}$' OR
    p_version IS NULL OR p_version<1 OR
    p_catalog IS NULL OR p_catalog<1 THEN RETURN 'LAB_DENIED'; END IF;
 SELECT * INTO a FROM wa29_lab.authority
  WHERE shop_ref=p_shop AND case_ref=p_case FOR UPDATE;
 IF NOT FOUND OR a.actor_ref<>p_actor OR a.state_version<>p_version OR
    a.catalog_revision<>p_catalog OR NOT a.consent_ok OR a.opted_out OR
    NOT a.case_ok OR NOT a.grant_ok OR NOT a.template_ok OR
    NOT a.campaign_ok THEN RETURN 'LAB_DENIED'; END IF;
 SELECT * INTO reservation FROM wa29_lab.reservations
  WHERE shop_ref=p_shop AND case_ref=p_case AND attempt_ref=p_attempt FOR UPDATE;
 IF NOT FOUND OR reservation.actor_ref<>p_actor OR
    reservation.state_version<>a.state_version OR
    reservation.catalog_revision<>a.catalog_revision THEN RETURN 'LAB_DENIED'; END IF;
 SELECT * INTO prior FROM wa29_lab.claims
  WHERE shop_ref=p_shop AND case_ref=p_case;
 IF FOUND THEN
   IF prior.attempt_ref=p_attempt AND prior.state='LAB_CLAIMED' THEN
     RETURN 'LAB_ALREADY_CLAIMED_NO_RETRY';
   END IF;
   RETURN 'LAB_DENIED';
 END IF;
 IF reservation.state<>'LAB_RESERVED' THEN RETURN 'LAB_DENIED'; END IF;
 INSERT INTO wa29_lab.claims(shop_ref,case_ref,attempt_ref,state,authority_version)
  VALUES (p_shop,p_case,p_attempt,'LAB_CLAIMED',a.state_version);
 UPDATE wa29_lab.reservations SET state='LAB_CLAIMED'
  WHERE shop_ref=p_shop AND case_ref=p_case AND attempt_ref=p_attempt;
 RETURN 'LAB_CLAIMED_NO_SEND_RIGHTS';
END;
$$;

CREATE FUNCTION wa29_lab.revoke_fixture(
 p_shop text,p_case text,p_kind text
) RETURNS text LANGUAGE plpgsql AS $$
DECLARE a wa29_lab.authority%ROWTYPE;
BEGIN
 IF p_kind IS NULL OR p_kind NOT IN ('OPT_OUT','GRANT','TEMPLATE','CAMPAIGN','CASE') OR
    p_shop IS NULL OR p_case IS NULL OR
    p_shop !~ '^[A-Za-z0-9_]{1,64}$' OR
    p_case !~ '^[A-Za-z0-9_]{1,64}$' THEN RETURN 'LAB_DENIED'; END IF;
 SELECT * INTO a FROM wa29_lab.authority
  WHERE shop_ref=p_shop AND case_ref=p_case FOR UPDATE;
 IF NOT FOUND THEN RETURN 'LAB_DENIED'; END IF;
 UPDATE wa29_lab.authority SET
  state_version=state_version+1,
  opted_out=CASE WHEN p_kind='OPT_OUT' THEN true ELSE opted_out END,
  grant_ok=CASE WHEN p_kind='GRANT' THEN false ELSE grant_ok END,
  template_ok=CASE WHEN p_kind='TEMPLATE' THEN false ELSE template_ok END,
  campaign_ok=CASE WHEN p_kind='CAMPAIGN' THEN false ELSE campaign_ok END,
  case_ok=CASE WHEN p_kind='CASE' THEN false ELSE case_ok END
 WHERE shop_ref=p_shop AND case_ref=p_case;
 UPDATE wa29_lab.reservations SET state='LAB_CANCELLED'
 WHERE shop_ref=p_shop AND case_ref=p_case AND state IN ('LAB_RESERVED','LAB_CLAIMED');
 UPDATE wa29_lab.claims SET state='LAB_INVALIDATED'
 WHERE shop_ref=p_shop AND case_ref=p_case AND state='LAB_CLAIMED';
 RETURN 'LAB_REVOKED';
END;
$$;
SELECT 'WA29-SETUP PASS'
 WHERE (SELECT count(*) FROM wa29_lab.authority)=7
 AND (SELECT count(*) FROM wa29_lab.reservations)=8
 AND (SELECT count(*) FROM wa29_lab.claims)=0;
