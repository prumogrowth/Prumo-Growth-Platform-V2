-- WA28 — FICTITIOUS atomic Meta template reservation model, PG17 disposable only.
-- Never migrate this schema to S0/S1, never send or allow Graph.
\set ON_ERROR_STOP on
CREATE SCHEMA wa28_lab;
CREATE TABLE wa28_lab.authority (
  shop_ref text NOT NULL,
  case_ref text NOT NULL,
  actor_ref text NOT NULL,
  version int NOT NULL CHECK(version>0),
  catalog_revision int NOT NULL CHECK(catalog_revision>0),
  consent_valid boolean NOT NULL,
  opted_out boolean NOT NULL,
  case_authorized boolean NOT NULL,
  grant_active boolean NOT NULL,
  template_active boolean NOT NULL,
  PRIMARY KEY(shop_ref,case_ref)
);
CREATE TABLE wa28_lab.reservations (
  shop_ref text NOT NULL,
  case_ref text NOT NULL,
  attempt_ref text NOT NULL,
  actor_ref text NOT NULL,
  status text NOT NULL CHECK(status IN ('LAB_RESERVED','LAB_CANCELLED')),
  authority_version int NOT NULL,
  send_authorized boolean NOT NULL DEFAULT false CHECK(NOT send_authorized),
  production_authorized boolean NOT NULL DEFAULT false CHECK(NOT production_authorized),
  PRIMARY KEY(shop_ref,case_ref,attempt_ref),
  FOREIGN KEY(shop_ref,case_ref) REFERENCES wa28_lab.authority(shop_ref,case_ref)
);
INSERT INTO wa28_lab.authority(
  shop_ref,case_ref,actor_ref,version,catalog_revision,consent_valid,
  opted_out,case_authorized,grant_active,template_active
) VALUES
('shop_A','case_reserve_first','planner_A',1,1,true,false,true,true,true),
('shop_A','case_revoke_first','planner_A',1,1,true,false,true,true,true),
('shop_A','case_duplicate','planner_A',1,1,true,false,true,true,true),
('shop_A','case_rollback','planner_A',1,1,true,false,true,true,true),
('shop_A','case_suspended','planner_A',1,1,true,false,true,true,false),
('shop_B','case_control','planner_B',1,1,true,false,true,true,true);

-- One-row lock precedes all reservation operations; same order on revocation.
-- This is a proposal fixture, NOT operational authentication or dispatch.
CREATE FUNCTION wa28_lab.attempt_reserve(
  p_shop text,p_case text,p_actor text,p_attempt text,
  p_expected_version int,p_expected_catalog int
) RETURNS text LANGUAGE plpgsql AS $$
DECLARE a wa28_lab.authority%ROWTYPE;
        current_status text;
BEGIN
  IF p_shop IS NULL OR p_case IS NULL OR p_actor IS NULL OR
     p_attempt IS NULL OR p_shop !~ '^[A-Za-z0-9_]{1,64}$' OR
     p_case !~ '^[A-Za-z0-9_]{1,64}$' OR
     p_actor !~ '^[A-Za-z0-9_]{1,64}$' OR
     p_attempt !~ '^[A-Za-z0-9_]{1,64}$' OR
     p_expected_version IS NULL OR p_expected_version<1 OR
     p_expected_catalog IS NULL OR p_expected_catalog<1 THEN
    RETURN 'LAB_DENIED';
  END IF;
  SELECT * INTO a FROM wa28_lab.authority
   WHERE shop_ref=p_shop AND case_ref=p_case FOR UPDATE;
  IF NOT FOUND OR a.actor_ref<>p_actor OR
     a.version<>p_expected_version OR
     a.catalog_revision<>p_expected_catalog OR
     NOT a.consent_valid OR a.opted_out OR
     NOT a.case_authorized OR NOT a.grant_active OR
     NOT a.template_active THEN
    RETURN 'LAB_DENIED';
  END IF;
  SELECT r.status INTO current_status FROM wa28_lab.reservations r
   WHERE r.shop_ref=p_shop AND r.case_ref=p_case AND r.attempt_ref=p_attempt;
  IF current_status='LAB_RESERVED' THEN
    RETURN 'LAB_ALREADY_RESERVED';
  END IF;
  IF current_status='LAB_CANCELLED' THEN
    RETURN 'LAB_DENIED';
  END IF;
  INSERT INTO wa28_lab.reservations (
   shop_ref,case_ref,attempt_ref,actor_ref,status,authority_version
  ) VALUES (p_shop,p_case,p_attempt,p_actor,'LAB_RESERVED',a.version);
  RETURN 'LAB_RESERVED';
END;
$$;

-- Authorized mutation is simulated by test owner (not authenticated S0).
-- Serialization point is the identical authority row as attempt_reserve.
CREATE FUNCTION wa28_lab.revoke_fixture(
 p_shop text,p_case text,p_kind text
) RETURNS text LANGUAGE plpgsql AS $$
DECLARE a wa28_lab.authority%ROWTYPE;
BEGIN
  IF p_kind NOT IN ('OPT_OUT','GRANT','PAUSE') OR
     p_shop IS NULL OR p_case IS NULL THEN
    RETURN 'LAB_DENIED';
  END IF;
  SELECT * INTO a FROM wa28_lab.authority
   WHERE shop_ref=p_shop AND case_ref=p_case FOR UPDATE;
  IF NOT FOUND THEN RETURN 'LAB_DENIED'; END IF;
  UPDATE wa28_lab.authority SET
    opted_out=CASE WHEN p_kind='OPT_OUT' THEN true ELSE opted_out END,
    grant_active=CASE WHEN p_kind='GRANT' THEN false ELSE grant_active END,
    template_active=CASE WHEN p_kind='PAUSE' THEN false ELSE template_active END,
    version=version+1
  WHERE shop_ref=p_shop AND case_ref=p_case;
  UPDATE wa28_lab.reservations SET status='LAB_CANCELLED'
   WHERE shop_ref=p_shop AND case_ref=p_case AND status='LAB_RESERVED';
  RETURN 'LAB_REVOKED';
END;
$$;
SELECT 'WA28-SETUP PASS' WHERE
 (SELECT COUNT(*) FROM wa28_lab.authority)=6 AND
 (SELECT COUNT(*) FROM wa28_lab.reservations)=0;
