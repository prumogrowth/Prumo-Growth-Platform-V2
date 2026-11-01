-- Additive S0 PRE_DISPATCH v0.2 reservation receipt only, no Meta authority.
BEGIN;
DO $$ BEGIN
 IF current_setting('server_version_num')::int/10000<>17
 OR current_database()<>'s0_meta_ingress_lab'
 OR current_user<>'postgres'
 OR current_setting('s0_meta.disposable',true) IS DISTINCT FROM 'YES'
 OR current_setting('s0_pd.install',true) IS DISTINCT FROM 'READBACK_V02_LAB_ONLY'
 OR to_regclass('s0_pre_dispatch_lab.reservations') IS NULL
 THEN RAISE EXCEPTION 'S0 PRE_DISPATCH readback PG17 disposable only'; END IF;
END $$;
CREATE SCHEMA s0_pd_v02_lab AUTHORIZATION s0_meta_owner;
SET ROLE s0_meta_owner;
CREATE TABLE s0_pd_v02_lab.quotas(
 store_ref text NOT NULL,
 app_ref text NOT NULL,
 phone_ref text NOT NULL,
 window_ref text NOT NULL,
 observed_at timestamptz NOT NULL,
 valid_until timestamptz NOT NULL,
 revision bigint NOT NULL CHECK(revision>0),
 capacity integer NOT NULL CHECK(capacity>0),
 consumed integer NOT NULL DEFAULT 0 CHECK(consumed>=0 AND consumed<=capacity),
 enabled boolean NOT NULL DEFAULT true,
 PRIMARY KEY(store_ref,app_ref,phone_ref,window_ref),
 CHECK(valid_until>observed_at)
);
CREATE TABLE s0_pd_v02_lab.receipts(
 attempt_ref text PRIMARY KEY REFERENCES s0_pre_dispatch_lab.reservations(attempt_ref),
 selection_ref text NOT NULL UNIQUE,
 intent_ref text NOT NULL UNIQUE,
 nonce text NOT NULL UNIQUE CHECK(nonce ~ '^[A-Za-z0-9_.:-]{8,120}$'),
 request_digest char(64) NOT NULL CHECK(request_digest ~ '^[0-9a-f]{64}$'),
 scope_digest char(64) NOT NULL CHECK(scope_digest ~ '^[0-9a-f]{64}$'),
 store_ref text NOT NULL,
 app_ref text NOT NULL,
 route_ref text NOT NULL,
 channel_ref text NOT NULL,
 phone_ref text NOT NULL,
 waba_ref text NOT NULL,
 case_ref text NOT NULL,
 service_ref text NOT NULL,
 consent_purpose_ref text NOT NULL,
 template_ref text NOT NULL,
 template_version text NOT NULL,
 campaign_ref text NOT NULL,
 destination_sha256 char(64) NOT NULL CHECK(destination_sha256 ~ '^[0-9a-f]{64}$'),
 body_sha256 char(64) NOT NULL CHECK(body_sha256 ~ '^[0-9a-f]{64}$'),
 expected_versions jsonb NOT NULL,
 m09_versions jsonb NOT NULL,
 window_ref text NOT NULL,
 quota_revision bigint NOT NULL,
 quota_observed_at timestamptz NOT NULL,
 quota_valid_until timestamptz NOT NULL,
 quota_slot integer NOT NULL CHECK(quota_slot>0),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 expires_at timestamptz NOT NULL,
 state text NOT NULL DEFAULT 'LAB_HELD_NO_DISPATCH'
   CHECK(state IN ('LAB_HELD_NO_DISPATCH','LAB_CANCELLED_NO_DISPATCH')),
 cancel_reason text,
 CHECK(expires_at>created_at),
 CHECK((state='LAB_HELD_NO_DISPATCH' AND cancel_reason IS NULL)
   OR (state='LAB_CANCELLED_NO_DISPATCH' AND cancel_reason IS NOT NULL))
);
-- Slots are never reusable within a quota epoch, even if a test-admin
-- incorrectly resets consumed. Only a new window identity may issue new slots.
CREATE UNIQUE INDEX pd_v02_unique_slot ON s0_pd_v02_lab.receipts
  (store_ref,app_ref,phone_ref,window_ref,quota_slot);
CREATE INDEX pd_v02_case_receipt ON s0_pd_v02_lab.receipts(case_ref,created_at);
-- Enforce monotonic consumed at the physical storage boundary. A held or
-- cancelled receipt does not refund a slot; admin fixture has no bypass.
CREATE FUNCTION s0_pd_v02_lab.prevent_quota_reset()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $quota_guard$
BEGIN
 IF NEW.consumed < OLD.consumed THEN
  RAISE EXCEPTION 'PD_V02_QUOTA_NONMONOTONIC';
 END IF;
 IF NEW.revision < OLD.revision THEN
  RAISE EXCEPTION 'PD_V02_QUOTA_REVISION_ROLLBACK';
 END IF;
 RETURN NEW;
END $quota_guard$;
CREATE TRIGGER prevent_quota_reset BEFORE UPDATE
ON s0_pd_v02_lab.quotas FOR EACH ROW
EXECUTE FUNCTION s0_pd_v02_lab.prevent_quota_reset();
REVOKE ALL ON SCHEMA s0_pd_v02_lab FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA s0_pd_v02_lab FROM PUBLIC;
ALTER TABLE s0_pd_v02_lab.quotas ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_pd_v02_lab.receipts ENABLE ROW LEVEL SECURITY;
RESET ROLE;
COMMIT;
