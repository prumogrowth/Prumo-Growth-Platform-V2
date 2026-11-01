-- S0 #11 F01 owner and irreversible handoff — disposable PG17 ONLY.
BEGIN;
DO $$ BEGIN
 IF current_setting('server_version_num')::int/10000<>17
 OR current_database()<>'s0_meta_ingress_lab'
 OR current_user<>'postgres'
 OR current_setting('s0_meta.disposable',true) IS DISTINCT FROM 'YES'
 OR current_setting('s0_f01.install',true) IS DISTINCT FROM 'OWNER_HANDOFF_LAB_ONLY'
 OR to_regclass('s0_frontend_lab.cases') IS NULL
 THEN RAISE EXCEPTION 'F01 ownership test schema restricted to disposable PG17'; END IF;
END $$;
CREATE SCHEMA s0_f01_lab AUTHORIZATION s0_meta_owner;
SET ROLE s0_meta_owner;
CREATE TABLE s0_f01_lab.cases(
 case_ref text PRIMARY KEY,
 store_ref text NOT NULL,
 person_ref text NOT NULL,
 service_ref text NOT NULL,
 owner_route text NOT NULL CHECK(owner_route IN ('AI','HUMAN')),
 handoff_definitive boolean NOT NULL DEFAULT false,
 humanized boolean NOT NULL DEFAULT false,
 opt_out boolean NOT NULL DEFAULT false,
 channel_eligible boolean NOT NULL DEFAULT true,
 post_remittance boolean NOT NULL DEFAULT false,
 post_sale boolean NOT NULL DEFAULT false,
 case_revision bigint NOT NULL CHECK(case_revision>0),
 cycle_revision bigint NOT NULL CHECK(cycle_revision>0),
 assignment_revision bigint NOT NULL CHECK(assignment_revision>0),
 catalog_revision bigint NOT NULL CHECK(catalog_revision>0),
 knowledge_revision bigint NOT NULL CHECK(knowledge_revision>0),
 policy_revision bigint NOT NULL CHECK(policy_revision>0),
 route_revision bigint NOT NULL CHECK(route_revision>0),
 consent_revision bigint NOT NULL CHECK(consent_revision>0),
 handoff_sequence bigint NOT NULL DEFAULT 0,
 CHECK ((NOT handoff_definitive AND NOT humanized AND owner_route='AI')
   OR (handoff_definitive AND humanized AND owner_route='HUMAN'))
);
CREATE TABLE s0_f01_lab.turns(
 turn_ref text PRIMARY KEY CHECK(turn_ref ~ '^[A-Za-z0-9_.:-]{1,120}$'),
 case_ref text NOT NULL REFERENCES s0_f01_lab.cases(case_ref),
 service_ref text NOT NULL,
 scope_digest char(64) NOT NULL,
 expected_versions jsonb NOT NULL,
 started_at timestamptz NOT NULL,
 deadline_at timestamptz NOT NULL,
 state text NOT NULL DEFAULT 'LAB_REQUEST_ONLY'
   CHECK(state='LAB_REQUEST_ONLY')
);
CREATE TABLE s0_f01_lab.handoff_events(
 event_ref text PRIMARY KEY CHECK(event_ref ~ '^[A-Za-z0-9_.:-]{1,120}$'),
 case_ref text NOT NULL UNIQUE REFERENCES s0_f01_lab.cases(case_ref),
 service_ref text NOT NULL,
 event_sequence bigint NOT NULL,
 handoff_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 state text NOT NULL DEFAULT 'LAB_HUMAN_DEFINITIVE'
   CHECK(state='LAB_HUMAN_DEFINITIVE')
);
CREATE TABLE s0_f01_lab.publication_checks(
 turn_ref text PRIMARY KEY REFERENCES s0_f01_lab.turns(turn_ref),
 case_ref text NOT NULL REFERENCES s0_f01_lab.cases(case_ref),
 candidate_digest char(64) NOT NULL,
 checked_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 state text NOT NULL DEFAULT 'LAB_RECHECK_ONLY_NO_PUBLISH'
   CHECK(state='LAB_RECHECK_ONLY_NO_PUBLISH')
);
CREATE FUNCTION s0_f01_lab.block_reopen() RETURNS trigger
 LANGUAGE plpgsql AS $fn$
 BEGIN
  IF OLD.handoff_definitive AND
   (NOT NEW.handoff_definitive OR NOT NEW.humanized OR NEW.owner_route<>'HUMAN'
    OR NEW.handoff_sequence<OLD.handoff_sequence) THEN
     RAISE EXCEPTION 'S0 F01 irreversible human ownership';
  END IF;
  RETURN NEW;
 END
 $fn$;
CREATE TRIGGER f01_irreversible BEFORE UPDATE ON s0_f01_lab.cases
 FOR EACH ROW EXECUTE FUNCTION s0_f01_lab.block_reopen();
REVOKE ALL ON SCHEMA s0_f01_lab FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA s0_f01_lab FROM PUBLIC;
ALTER TABLE s0_f01_lab.cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_f01_lab.turns ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_f01_lab.handoff_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE s0_f01_lab.publication_checks ENABLE ROW LEVEL SECURITY;
RESET ROLE;
COMMIT;
