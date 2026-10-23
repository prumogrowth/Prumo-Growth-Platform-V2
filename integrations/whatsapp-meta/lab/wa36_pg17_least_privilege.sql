-- WA36: LOCAL PG17 privilege NEGATIVE test. NOT S0 migration or M2M auth.
-- Roles are synthetic, NOLOGIN, WITHOUT RLS/GoTrue/S1 delegation.
\set ON_ERROR_STOP on
CREATE ROLE wa36_untrusted NOLOGIN;
CREATE ROLE wa36_meta_ingress NOLOGIN;
CREATE ROLE wa36_s0_candidate NOLOGIN;
CREATE ROLE wa36_human_operator NOLOGIN;
CREATE SCHEMA wa36_lab;
CREATE TABLE wa36_lab.reviews (
 shop_ref text NOT NULL,attempt_ref text NOT NULL,nonce_ref text NOT NULL,
 status text NOT NULL CHECK(status='LAB_PENDING_RATIFICATION'),
 ack_allowed boolean NOT NULL DEFAULT false CHECK(NOT ack_allowed),
 send_authorized boolean NOT NULL DEFAULT false CHECK(NOT send_authorized),
 retry_external boolean NOT NULL DEFAULT false CHECK(NOT retry_external),
 production_authorized boolean NOT NULL DEFAULT false CHECK(NOT production_authorized),
 s0_write_authorized boolean NOT NULL DEFAULT false CHECK(NOT s0_write_authorized),
 PRIMARY KEY(shop_ref,attempt_ref,nonce_ref)
);
INSERT INTO wa36_lab.reviews
 (shop_ref,attempt_ref,nonce_ref,status)
VALUES('shop_A','attempt_lab','nonce_setup','LAB_PENDING_RATIFICATION');

-- Demonstrates that EXECUTE alone on a SECURITY INVOKER function cannot
-- bypass missing INSERT privilege. Deliberately no SECURITY DEFINER wrapper.
CREATE FUNCTION wa36_lab.append_proposal(p_shop text,p_attempt text,p_nonce text)
RETURNS text LANGUAGE plpgsql SECURITY INVOKER
SET search_path = pg_catalog AS $wa36$
BEGIN
 IF p_shop IS NULL OR p_attempt IS NULL OR p_nonce IS NULL OR
    p_shop !~ '^[A-Za-z0-9_.:-]{1,128}$' OR
    p_attempt !~ '^[A-Za-z0-9_.:-]{1,128}$' OR
    p_nonce !~ '^[A-Za-z0-9_.:-]{1,128}$'
 THEN RETURN 'LAB_DENIED'; END IF;
 INSERT INTO wa36_lab.reviews(shop_ref,attempt_ref,nonce_ref,status)
 VALUES(p_shop,p_attempt,p_nonce,'LAB_PENDING_RATIFICATION');
 RETURN 'LAB_FIXTURE_ONLY_NOT_SERVICE_AUTH';
END $wa36$;

REVOKE ALL ON SCHEMA wa36_lab FROM PUBLIC;
REVOKE ALL ON TABLE wa36_lab.reviews FROM PUBLIC;
REVOKE ALL ON FUNCTION wa36_lab.append_proposal(text,text,text) FROM PUBLIC;
GRANT USAGE ON SCHEMA wa36_lab TO wa36_meta_ingress,wa36_s0_candidate;
GRANT EXECUTE ON FUNCTION wa36_lab.append_proposal(text,text,text)
 TO wa36_meta_ingress,wa36_s0_candidate;

-- Intentionally NO table INSERT/SELECT/UPDATE/DELETE grants, no LOGIN grants,
-- no usage on wa34_lab, wa29_lab, public S0, auth or S1 objects.
SELECT 'WA36-SETUP PASS'
WHERE (SELECT count(*) FROM wa36_lab.reviews)=1 AND
 (SELECT count(*) FROM pg_roles WHERE rolname LIKE 'wa36_%')=4;
