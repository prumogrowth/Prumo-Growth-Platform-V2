-- Issue #12 commercial-source metadata LAB ONLY, no prices/text/PII.
BEGIN;
DO $$ BEGIN
 IF current_setting('server_version_num')::int/10000<>17
 OR current_database()<>'s0_meta_ingress_lab'
 OR current_user<>'postgres'
 OR current_setting('s0_meta.disposable',true) IS DISTINCT FROM 'YES'
 OR current_setting('s0_f01.install',true) IS DISTINCT FROM 'COMMERCIAL_SOURCES_LAB_ONLY'
 OR to_regclass('s0_f01_lab.cases') IS NULL
 THEN RAISE EXCEPTION 'S0 F01 sources: PG17 disposable-only installer'; END IF;
END $$;
CREATE SCHEMA s0_f01_sources_lab AUTHORIZATION s0_meta_owner;
SET ROLE s0_meta_owner;
CREATE TABLE s0_f01_sources_lab.contexts (
 case_ref text PRIMARY KEY REFERENCES s0_f01_lab.cases(case_ref),
 store_ref text NOT NULL,
 person_ref text NOT NULL,
 purpose_ref text NOT NULL,
 catalog_revision bigint NOT NULL CHECK(catalog_revision>0),
 knowledge_revision bigint NOT NULL CHECK(knowledge_revision>0),
 policy_revision bigint NOT NULL CHECK(policy_revision>0),
 consent_revision bigint NOT NULL CHECK(consent_revision>0),
 grant_revision bigint NOT NULL CHECK(grant_revision>0),
 content_policy text NOT NULL CHECK(content_policy IN ('LAB_ALLOWED','LAB_DENIED','LAB_UNKNOWN')),
 consent_state text NOT NULL CHECK(consent_state IN ('LAB_ALLOWED','LAB_DENIED','LAB_UNKNOWN')),
 active boolean NOT NULL DEFAULT true
);
CREATE TABLE s0_f01_sources_lab.sources (
 source_ref text PRIMARY KEY CHECK(source_ref ~ '^[A-Za-z0-9_.:-]{1,120}$'),
 case_ref text NOT NULL REFERENCES s0_f01_sources_lab.contexts(case_ref),
 store_ref text NOT NULL,
 purpose_ref text NOT NULL,
 kind text NOT NULL CHECK(kind IN ('current','historical')),
 approval_state text NOT NULL CHECK(approval_state IN
  ('APPROVED_ACTIVE','PAUSED','REVOKED','EXPIRED','DRAFT')),
 source_version bigint NOT NULL CHECK(source_version>0),
 valid_until timestamptz,
 corrected_by_ref text,
 claim_codes jsonb NOT NULL,
 content_grant_active boolean NOT NULL DEFAULT false,
 provenance_lab_asserted boolean NOT NULL DEFAULT false,
 minimized_lab_asserted boolean NOT NULL DEFAULT false,
 CHECK (jsonb_typeof(claim_codes)='array'),
 CHECK (corrected_by_ref IS NULL OR corrected_by_ref ~ '^[A-Za-z0-9_.:-]{1,120}$')
);
CREATE INDEX f01_source_scope ON s0_f01_sources_lab.sources
 (case_ref,store_ref,purpose_ref,source_ref);
CREATE TABLE s0_f01_sources_lab.selections (
 request_ref text PRIMARY KEY REFERENCES s0_f01_lab.turns(turn_ref),
 case_ref text NOT NULL REFERENCES s0_f01_sources_lab.contexts(case_ref),
 request_fingerprint char(64) NOT NULL,
 snapshot_fingerprint char(64) NOT NULL,
 expected_versions jsonb NOT NULL,
 observed_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE s0_f01_sources_lab.aliases (
 request_ref text NOT NULL REFERENCES s0_f01_sources_lab.selections(request_ref),
 alias_ref text NOT NULL CHECK(alias_ref ~ '^src_[0-9]{3}$'),
 source_ref text NOT NULL REFERENCES s0_f01_sources_lab.sources(source_ref),
 source_version bigint NOT NULL,
 claim_code text NOT NULL,
 usage text NOT NULL CHECK(usage IN ('commercial','interpretive')),
 PRIMARY KEY(request_ref,alias_ref,claim_code,usage),
 UNIQUE(request_ref,source_ref,claim_code,usage)
);
CREATE TABLE s0_f01_sources_lab.reviews (
 request_ref text PRIMARY KEY REFERENCES s0_f01_sources_lab.selections(request_ref),
 proposal_fingerprint char(64) NOT NULL,
 state text NOT NULL DEFAULT 'LAB_REVIEW_ONLY_NO_PUBLISH'
 CHECK(state='LAB_REVIEW_ONLY_NO_PUBLISH'),
 reviewed_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
REVOKE ALL ON SCHEMA s0_f01_sources_lab FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA s0_f01_sources_lab FROM PUBLIC;
ALTER TABLE s0_f01_sources_lab.contexts ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_f01_sources_lab.sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_f01_sources_lab.selections ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_f01_sources_lab.aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_f01_sources_lab.reviews ENABLE ROW LEVEL SECURITY;
RESET ROLE;
COMMIT;
