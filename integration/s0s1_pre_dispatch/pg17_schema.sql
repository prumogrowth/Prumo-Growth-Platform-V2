-- S0 #10 PRE_DISPATCH control reservation candidate; PG17 lab ONLY.
-- No message, Graph API, vault, HTTP ACK, outbound send or production authority.
BEGIN;
DO $$ BEGIN
 IF current_setting('server_version_num')::int / 10000 <> 17
    OR current_database() <> 's0_meta_ingress_lab'
    OR current_user <> 'postgres'
    OR current_setting('s0_meta.disposable',true) IS DISTINCT FROM 'YES'
    OR current_setting('s0_m09.install',true) IS DISTINCT FROM 'PRE_DISPATCH_CANDIDATE_ONLY'
    OR to_regclass('s0_m09_lab.point_of_use_checks') IS NULL
 THEN RAISE EXCEPTION 'PRE_DISPATCH disposable PG17 only'; END IF;
END $$;
CREATE SCHEMA s0_pre_dispatch_lab AUTHORIZATION s0_meta_owner;
SET ROLE s0_meta_owner;
CREATE TABLE s0_pre_dispatch_lab.cases (
 case_ref text PRIMARY KEY,
 concessionaria_id text NOT NULL,
 app_ref text NOT NULL,
 route_ref text NOT NULL,
 canal_id text NOT NULL,
 waba_id text NOT NULL,
 principal_ref text NOT NULL,
 case_revision bigint NOT NULL CHECK(case_revision>0),
 assignment_revision bigint NOT NULL CHECK(assignment_revision>0),
 policy_revision bigint NOT NULL CHECK(policy_revision>0),
 suppression_revision bigint NOT NULL CHECK(suppression_revision>0),
 active boolean NOT NULL,
 global_opt_out boolean NOT NULL
);
CREATE TABLE s0_pre_dispatch_lab.consents (
 case_ref text NOT NULL REFERENCES s0_pre_dispatch_lab.cases(case_ref),
 purpose_ref text NOT NULL,
 revision bigint NOT NULL CHECK(revision>0),
 state text NOT NULL CHECK(state IN ('GRANTED','DENIED','UNKNOWN','REVOKED')),
 valid_until timestamptz NOT NULL,
 PRIMARY KEY (case_ref,purpose_ref)
);
CREATE TABLE s0_pre_dispatch_lab.suppressions (
 case_ref text NOT NULL REFERENCES s0_pre_dispatch_lab.cases(case_ref),
 purpose_ref text NOT NULL,
 active boolean NOT NULL,
 PRIMARY KEY (case_ref,purpose_ref)
);
CREATE TABLE s0_pre_dispatch_lab.templates (
 template_ref text NOT NULL,
 template_version text NOT NULL,
 concessionaria_id text NOT NULL,
 waba_id text NOT NULL,
 template_purpose_ref text NOT NULL,
 consent_purpose_ref text NOT NULL,
 revision bigint NOT NULL CHECK(revision>0),
 active boolean NOT NULL,
 provider_approved boolean NOT NULL,
 media_verified boolean NOT NULL,
 valid_until timestamptz NOT NULL,
 PRIMARY KEY(template_ref,template_version)
);
CREATE TABLE s0_pre_dispatch_lab.campaigns (
 campaign_ref text PRIMARY KEY,
 case_ref text NOT NULL REFERENCES s0_pre_dispatch_lab.cases(case_ref),
 template_ref text NOT NULL,
 template_version text NOT NULL,
 revision bigint NOT NULL CHECK(revision>0),
 active boolean NOT NULL,
 eligible boolean NOT NULL,
 FOREIGN KEY (template_ref,template_version)
 REFERENCES s0_pre_dispatch_lab.templates(template_ref,template_version)
);
CREATE TABLE s0_pre_dispatch_lab.grants (
 case_ref text NOT NULL REFERENCES s0_pre_dispatch_lab.cases(case_ref),
 service_ref text NOT NULL,
 template_ref text NOT NULL,
 template_version text NOT NULL,
 campaign_ref text NOT NULL REFERENCES s0_pre_dispatch_lab.campaigns(campaign_ref),
 template_purpose_ref text NOT NULL,
 revision bigint NOT NULL CHECK(revision>0),
 active boolean NOT NULL,
 PRIMARY KEY(case_ref,service_ref,template_ref,template_version,campaign_ref)
);
CREATE TABLE s0_pre_dispatch_lab.reservations (
 attempt_ref text PRIMARY KEY,
 selection_ref text NOT NULL UNIQUE,
 case_ref text NOT NULL,
 concessionaria_id text NOT NULL,
 template_ref text NOT NULL,
 template_version text NOT NULL,
 template_purpose_ref text NOT NULL,
 observed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 state text NOT NULL DEFAULT 'LAB_HELD_NO_DISPATCH'
   CHECK(state='LAB_HELD_NO_DISPATCH'),
 CHECK (attempt_ref ~ '^[A-Za-z0-9_.:-]{1,128}$'),
 CHECK (selection_ref ~ '^[A-Za-z0-9_.:-]{1,128}$')
);
REVOKE ALL ON SCHEMA s0_pre_dispatch_lab FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA s0_pre_dispatch_lab FROM PUBLIC;
ALTER TABLE s0_pre_dispatch_lab.cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_pre_dispatch_lab.consents ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_pre_dispatch_lab.suppressions ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_pre_dispatch_lab.templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_pre_dispatch_lab.campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_pre_dispatch_lab.grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_pre_dispatch_lab.reservations ENABLE ROW LEVEL SECURITY;
-- Runtime has NO schema usage, SELECT, INSERT or UPDATE grants/policies.
RESET ROLE;
COMMIT;
