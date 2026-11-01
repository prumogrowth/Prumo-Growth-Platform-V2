-- F02 S0 durable request/alias/review journal, disposable PG17 only.
-- This is not an authorization to call an OpenAI API or send a message.
BEGIN;
DO $$ BEGIN
 IF current_setting('server_version_num')::int/10000 <> 17
 OR current_database() <> 's0_meta_ingress_lab'
 OR current_user <> 'postgres'
 OR current_setting('s0_meta.disposable',true) IS DISTINCT FROM 'YES'
 OR current_setting('s0_f02.install',true) IS DISTINCT FROM 'F02_CANDIDATE_ONLY'
 OR to_regclass('s0_pre_dispatch_lab.cases') IS NULL
 OR to_regclass('s0_m09_lab.point_of_use_checks') IS NULL
 THEN RAISE EXCEPTION 'F02 only in isolated S0 PG17 lab'; END IF;
END $$;
CREATE SCHEMA s0_f02_lab AUTHORIZATION s0_meta_owner;
SET ROLE s0_meta_owner;
-- Independently owned F02 flow/cycle revision, NOT an assignment alias.
-- The disposable fixture seeds this source only; hosted authority remains pending.
CREATE TABLE s0_f02_lab.case_cycles (
 case_ref text PRIMARY KEY REFERENCES s0_pre_dispatch_lab.cases(case_ref),
 cycle_revision bigint NOT NULL CHECK(cycle_revision>0),
 flow_ref text NOT NULL CHECK(flow_ref ~ '^[A-Za-z0-9_.:-]{1,120}$')
);
CREATE TABLE s0_f02_lab.requests (
 request_ref text PRIMARY KEY CHECK(request_ref ~ '^[A-Za-z0-9_.:-]{1,128}$'),
 provider_tag text NOT NULL UNIQUE,
 fingerprint char(64) NOT NULL CHECK (fingerprint ~ '^[a-f0-9]{64}$'),
 case_ref text NOT NULL,
 concessionaria_id text NOT NULL,
 app_ref text NOT NULL,
 principal_ref text NOT NULL,
 purpose_ref text NOT NULL,
 consent_purpose_ref text NOT NULL,
 owner_route text NOT NULL CHECK (owner_route IN ('human','seller_ai')),
 plan_revision bigint NOT NULL CHECK(plan_revision>0),
 case_revision bigint NOT NULL CHECK(case_revision>0),
 cycle_revision bigint NOT NULL CHECK(cycle_revision>0),
 assignment_revision bigint NOT NULL CHECK(assignment_revision>0),
 policy_revision bigint NOT NULL CHECK(policy_revision>0),
 consent_revision bigint NOT NULL CHECK(consent_revision>0),
 template_revision bigint NOT NULL CHECK(template_revision>0),
 grant_revision bigint NOT NULL CHECK(grant_revision>0),
 source_sha256 char(64) NOT NULL CHECK (source_sha256 ~ '^[a-f0-9]{64}$'),
 window_start timestamptz NOT NULL,
 window_end timestamptz NOT NULL,
 deadline_at timestamptz NOT NULL,
 max_attempts integer NOT NULL CHECK(max_attempts BETWEEN 0 AND 16),
 state text NOT NULL DEFAULT 'LAB_PLAN_REQUESTED'
   CHECK (state='LAB_PLAN_REQUESTED')
);
CREATE TABLE s0_f02_lab.aliases (
 request_ref text NOT NULL REFERENCES s0_f02_lab.requests(request_ref),
 alias text NOT NULL CHECK(alias ~ '^tpl_[0-9]{3}$'),
 template_ref text NOT NULL,
 version_ref text NOT NULL,
 template_revision bigint NOT NULL CHECK(template_revision>0),
 PRIMARY KEY(request_ref,alias),
 UNIQUE(request_ref,template_ref,version_ref)
);
CREATE TABLE s0_f02_lab.reviews (
 request_ref text PRIMARY KEY REFERENCES s0_f02_lab.requests(request_ref),
 plan_fingerprint char(64) NOT NULL CHECK(plan_fingerprint ~ '^[a-f0-9]{64}$'),
 state text NOT NULL DEFAULT 'LAB_REVIEW_ONLY'
  CHECK(state='LAB_REVIEW_ONLY'),
 observed_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
REVOKE ALL ON SCHEMA s0_f02_lab FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA s0_f02_lab FROM PUBLIC;
ALTER TABLE s0_f02_lab.case_cycles ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_f02_lab.requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_f02_lab.aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_f02_lab.reviews ENABLE ROW LEVEL SECURITY;
-- All writes/reads are controlled by disposable test installer only.
RESET ROLE;
COMMIT;
