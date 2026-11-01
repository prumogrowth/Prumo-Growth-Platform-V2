-- M09-08 LAB control ledger. No credential use, dispatch, or operational authority.
-- Installer requires the pinned PG17 s0_meta_ingress_lab and M09-03 extension.
BEGIN;
DO $$
BEGIN
 IF current_setting('server_version_num')::int / 10000 <> 17
 OR current_database() <> 's0_meta_ingress_lab'
 OR current_user <> 'postgres'
 OR current_setting('s0_meta.disposable',true) IS DISTINCT FROM 'YES'
 OR current_setting('s0_m09.install',true) IS DISTINCT FROM 'POINT_OF_USE_CANDIDATE_ONLY'
 OR to_regclass('s0_m09_lab.apps') IS NULL
 OR to_regclass('s0_m09_lab.grants') IS NULL
 THEN RAISE EXCEPTION 'M09 point of use installation only in disposable PG17'; END IF;
END $$;
SET ROLE s0_meta_owner;
CREATE TABLE s0_m09_lab.point_of_use_checks (
  attempt_ref text PRIMARY KEY CHECK (attempt_ref ~ '^[A-Za-z0-9_.:-]{1,128}$'),
  route_ref text NOT NULL,
  app_ref text NOT NULL,
  canal_id text NOT NULL,
  principal_ref text NOT NULL,
  expected_route_revision bigint NOT NULL CHECK(expected_route_revision>0),
  expected_app_revision bigint NOT NULL CHECK(expected_app_revision>0),
  expected_binding_revision bigint NOT NULL CHECK(expected_binding_revision>0),
  expected_grant_revision bigint NOT NULL CHECK(expected_grant_revision>0),
  expected_principal_revision bigint NOT NULL CHECK(expected_principal_revision>0),
  observed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  laboratory_status text NOT NULL DEFAULT 'CHECK_RECORDED_ONLY'
     CHECK(laboratory_status='CHECK_RECORDED_ONLY')
);
REVOKE ALL ON s0_m09_lab.point_of_use_checks FROM PUBLIC;
ALTER TABLE s0_m09_lab.point_of_use_checks ENABLE ROW LEVEL SECURITY;
-- No runtime policy or privileges. Installer-only simulation of a control event.
RESET ROLE;
COMMIT;
