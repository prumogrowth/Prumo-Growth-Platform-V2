-- WA34: atomic nonce consume experiment on top of WA33; fictitious S0 only.
-- NO real verifier in SQL: callers can forge every argument including time.
-- Trusted service identity + atomic signed-body linkage remain blocking gaps.
\set ON_ERROR_STOP on
CREATE SCHEMA wa34_lab;
CREATE TABLE wa34_lab.consumed_nonces(
 nonce_ref text PRIMARY KEY CHECK(nonce_ref ~ '^[A-Za-z0-9_.:-]{1,128}$'),
 shop_ref text NOT NULL,case_ref text NOT NULL,attempt_ref text NOT NULL,
 event_ref text NOT NULL,
 consumption text NOT NULL CHECK(consumption IN ('LAB_ARCHIVED','LAB_REPLAY')),
 send_authorized boolean NOT NULL DEFAULT false CHECK(NOT send_authorized),
 production_authorized boolean NOT NULL DEFAULT false CHECK(NOT production_authorized),
 ack_allowed boolean NOT NULL DEFAULT false CHECK(NOT ack_allowed),
 retry_external boolean NOT NULL DEFAULT false CHECK(NOT retry_external),
 case_transition_authorized boolean NOT NULL DEFAULT false
   CHECK(NOT case_transition_authorized),
 definitive_failure_count_increment boolean NOT NULL DEFAULT false
   CHECK(NOT definitive_failure_count_increment),
 FOREIGN KEY(shop_ref,case_ref,attempt_ref)
   REFERENCES wa33_lab.bindings(shop_ref,case_ref,attempt_ref)
);
-- No production authority: this function is only a physical nonce and lock test.
CREATE FUNCTION wa34_lab.consume_fixture(
 p_nonce text,p_app text,p_waba text,p_phone text,p_wamid text,
 p_recipient text,p_event text,p_kind text,p_binding_revision int,
 p_issued_at bigint,p_expires_at bigint,p_now bigint
) RETURNS text LANGUAGE plpgsql AS $wa34_consume$
DECLARE prior wa33_lab.bindings%ROWTYPE;
        current_binding wa33_lab.bindings%ROWTYPE;
        result text;
        inserted integer;
BEGIN
 IF p_nonce IS NULL OR p_nonce !~ '^[A-Za-z0-9_.:-]{1,128}$' OR
    p_issued_at IS NULL OR p_expires_at IS NULL OR p_now IS NULL OR
    p_issued_at<0 OR p_expires_at<=p_issued_at OR
    p_expires_at-p_issued_at>120000 OR
    p_now<p_issued_at OR p_now>=p_expires_at OR
    p_binding_revision IS NULL OR p_binding_revision<1 OR
    p_app IS NULL OR p_waba IS NULL OR p_phone IS NULL OR
    p_wamid IS NULL OR p_recipient IS NULL OR p_event IS NULL OR p_kind IS NULL
 THEN RETURN 'LAB_DENIED'; END IF;
 -- A preliminary selection is not authority. Revalidate under the SAME lock.
 SELECT * INTO prior FROM wa33_lab.bindings
 WHERE app_ref=p_app AND waba_ref=p_waba AND phone_ref=p_phone
   AND wamid_ref=p_wamid;
 IF NOT FOUND THEN RETURN 'LAB_DENIED'; END IF;
 PERFORM 1 FROM wa29_lab.authority
 WHERE shop_ref=prior.shop_ref AND case_ref=prior.case_ref FOR UPDATE;
 IF NOT FOUND THEN RETURN 'LAB_DENIED'; END IF;
 SELECT * INTO current_binding FROM wa33_lab.bindings
 WHERE shop_ref=prior.shop_ref AND case_ref=prior.case_ref
   AND attempt_ref=prior.attempt_ref FOR UPDATE;
 IF NOT FOUND OR current_binding IS DISTINCT FROM prior OR
    NOT current_binding.active OR
    current_binding.recipient_ref<>p_recipient OR
    current_binding.binding_revision<>p_binding_revision
 THEN RETURN 'LAB_DENIED'; END IF;
 -- Reserve the nonce before appending. A second transaction will wait for
 -- the unique index and must not persist any additional event.
 INSERT INTO wa34_lab.consumed_nonces(
   nonce_ref,shop_ref,case_ref,attempt_ref,event_ref,consumption
 ) VALUES(p_nonce,prior.shop_ref,prior.case_ref,prior.attempt_ref,p_event,'LAB_ARCHIVED')
 ON CONFLICT DO NOTHING;
 GET DIAGNOSTICS inserted=ROW_COUNT;
 IF inserted<>1 THEN RETURN 'LAB_NONCE_CONSUMED_NO_RETRY'; END IF;
 SELECT wa33_lab.append_fixture(
   p_app,p_waba,p_phone,p_wamid,p_recipient,p_event,p_kind,p_binding_revision
 ) INTO result;
 IF result IN ('LAB_ARCHIVED_UNVERIFIED_NO_SEND','LAB_ARCHIVED_LATE_NO_SEND')
 THEN RETURN 'LAB_NONCE_CONSUMED_ARCHIVED_NO_SEND'; END IF;
 IF result='LAB_REPLAY_NO_RETRY' THEN
   UPDATE wa34_lab.consumed_nonces SET consumption='LAB_REPLAY'
   WHERE nonce_ref=p_nonce;
   RETURN 'LAB_NONCE_CONSUMED_REPLAY_NO_SEND';
 END IF;
 DELETE FROM wa34_lab.consumed_nonces WHERE nonce_ref=p_nonce;
 RETURN CASE WHEN result='LAB_QUARANTINED' THEN 'LAB_QUARANTINED'
             ELSE 'LAB_DENIED' END;
END;
$wa34_consume$;
SELECT 'WA34-SETUP PASS'
WHERE (SELECT count(*) FROM wa34_lab.consumed_nonces)=0;
