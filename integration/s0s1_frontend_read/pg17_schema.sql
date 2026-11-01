-- S0/S1 #14: operational READ only in disposable PG17 lab.
-- Installer alone owns data; role signatures and events are fixtures, not real S0 proof.
BEGIN;
DO $$ BEGIN
 IF current_setting('server_version_num')::int/10000<>17
 OR current_database()<>'s0_meta_ingress_lab'
 OR current_user<>'postgres'
 OR current_setting('s0_meta.disposable',true) IS DISTINCT FROM 'YES'
 OR current_setting('s0_frontend.install',true) IS DISTINCT FROM 'READ_LAB_ONLY'
 OR to_regclass('s0_pre_dispatch_lab.cases') IS NULL
 THEN RAISE EXCEPTION 'Frontend S0 read schema: only disposable PG17'; END IF;
END $$;
CREATE SCHEMA s0_frontend_lab AUTHORIZATION s0_meta_owner;
SET ROLE s0_meta_owner;
CREATE TABLE s0_frontend_lab.cases (
 case_ref text PRIMARY KEY CHECK(case_ref ~ '^[A-Za-z0-9_.:-]{1,120}$'),
 store_ref text NOT NULL,
 owner_ref text NOT NULL,
 assignment_revision bigint NOT NULL CHECK(assignment_revision>0),
 case_revision bigint NOT NULL CHECK(case_revision>0),
 inbox_revision bigint NOT NULL CHECK(inbox_revision>0),
 actionable boolean NOT NULL,
 active boolean NOT NULL
);
CREATE TABLE s0_frontend_lab.events (
 case_ref text NOT NULL REFERENCES s0_frontend_lab.cases(case_ref),
 event_seq bigint NOT NULL CHECK(event_seq>0),
 event_ref text NOT NULL UNIQUE,
 event_kind text NOT NULL
   CHECK(event_kind IN ('INBOUND','HUMAN_REPLY_PUBLISHED','API_ACCEPTED','LOCAL_DRAFT')),
 inbound_visible boolean NOT NULL DEFAULT false,
 occurred_at timestamptz,
 source_verified boolean NOT NULL DEFAULT false,
 PRIMARY KEY(case_ref,event_seq),
 CHECK (event_kind='INBOUND' OR inbound_visible=false)
);
CREATE TABLE s0_frontend_lab.read_cursors (
 case_ref text NOT NULL REFERENCES s0_frontend_lab.cases(case_ref),
 owner_ref text NOT NULL,
 read_through_seq bigint NOT NULL CHECK(read_through_seq>=0),
 PRIMARY KEY(case_ref,owner_ref)
);
CREATE TABLE s0_frontend_lab.open_attempts (
 open_ref text PRIMARY KEY CHECK(open_ref ~ '^[A-Za-z0-9_.:-]{1,120}$'),
 case_ref text NOT NULL REFERENCES s0_frontend_lab.cases(case_ref),
 owner_ref text NOT NULL,
 store_ref text NOT NULL,
 assignment_revision bigint NOT NULL,
 case_revision bigint NOT NULL,
 inbox_revision bigint NOT NULL,
 read_through_seq bigint NOT NULL,
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
REVOKE ALL ON SCHEMA s0_frontend_lab FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA s0_frontend_lab FROM PUBLIC;
ALTER TABLE s0_frontend_lab.cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_frontend_lab.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_frontend_lab.read_cursors ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_frontend_lab.open_attempts ENABLE ROW LEVEL SECURITY;
-- Deliberately no runtime RLS policy, schema USAGE, SELECT or INSERT.
RESET ROLE;
COMMIT;
