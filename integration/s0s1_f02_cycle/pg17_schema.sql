-- S0 F02 cycle provenance and monotonic transition journal: PG17 disposable only.
-- No hosted service principal, commercial permission, Graph or authorization.
BEGIN;
DO $$ BEGIN
 IF current_setting('server_version_num')::int/10000<>17
 OR current_database()<>'s0_meta_ingress_lab'
 OR current_user<>'postgres'
 OR current_setting('s0_meta.disposable',true) IS DISTINCT FROM 'YES'
 OR current_setting('s0_f02.install',true) IS DISTINCT FROM 'CYCLE_AUTHORITY_LAB_ONLY'
 OR to_regclass('s0_f02_lab.case_cycles') IS NULL
 OR to_regclass('s0_pre_dispatch_lab.cases') IS NULL
 OR to_regclass('s0_pre_dispatch_lab.consents') IS NULL
 THEN RAISE EXCEPTION 'F02 cycle authority: PG17 disposable only'; END IF;
END $$;
CREATE SCHEMA s0_f02_cycle_lab AUTHORIZATION s0_meta_owner;
SET ROLE s0_meta_owner;
CREATE TABLE s0_f02_cycle_lab.authorities(
 case_ref text PRIMARY KEY REFERENCES s0_pre_dispatch_lab.cases(case_ref),
 flow_ref text NOT NULL,
 store_ref text NOT NULL,
 service_ref text NOT NULL,
 purpose_ref text NOT NULL,
 actor_ref text NOT NULL CHECK(actor_ref ~ '^[A-Za-z0-9_.:-]{1,120}$'),
 actor_key_revision bigint NOT NULL CHECK(actor_key_revision>0),
 ed25519_public_key bytea NOT NULL CHECK(octet_length(ed25519_public_key)=32),
 actor_enabled boolean NOT NULL DEFAULT true,
 cycle_revision bigint NOT NULL CHECK(cycle_revision>0),
 state text NOT NULL CHECK(state IN ('ACTIVE','PAUSED','REVOKED')),
 generation bigint NOT NULL DEFAULT 1 CHECK(generation>0),
 last_command_ref text,
 CHECK (last_command_ref IS NULL OR last_command_ref ~ '^[A-Za-z0-9_.:-]{1,120}$')
);
CREATE TABLE s0_f02_cycle_lab.commands(
 command_ref text PRIMARY KEY CHECK(command_ref ~ '^[A-Za-z0-9_.:-]{1,120}$'),
 case_ref text NOT NULL REFERENCES s0_f02_cycle_lab.authorities(case_ref),
 nonce text NOT NULL CHECK(nonce ~ '^[A-Za-z0-9_.:-]{8,120}$'),
 request_digest char(64) NOT NULL CHECK(request_digest ~ '^[0-9a-f]{64}$'),
 action text NOT NULL CHECK(action IN ('ADVANCE','PAUSE','RESUME','REVOKE')),
 before_revision bigint NOT NULL CHECK(before_revision>0),
 after_revision bigint NOT NULL CHECK(after_revision>0),
 after_state text NOT NULL CHECK(after_state IN ('ACTIVE','PAUSED','REVOKED')),
 actor_ref text NOT NULL,
 actor_key_revision bigint NOT NULL,
 consent_revision bigint NOT NULL,
 assignment_revision bigint NOT NULL,
 policy_revision bigint NOT NULL,
 suppression_revision bigint NOT NULL,
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 UNIQUE(case_ref,nonce),
 CHECK(after_revision=before_revision+1)
);
REVOKE ALL ON SCHEMA s0_f02_cycle_lab FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA s0_f02_cycle_lab FROM PUBLIC;
ALTER TABLE s0_f02_cycle_lab.authorities ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_f02_cycle_lab.commands ENABLE ROW LEVEL SECURITY;
RESET ROLE;
COMMIT;
