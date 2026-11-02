-- S0 G2-B additive cooperative PG17 transaction gate, no dispatch.
BEGIN;
DO $lab$ BEGIN
 IF current_setting('server_version_num')::int/10000<>17
 OR current_database()<>'s0_meta_ingress_lab'
 OR current_user<>'postgres'
 OR current_setting('s0_meta.disposable',true) IS DISTINCT FROM 'YES'
 OR current_setting('s0_g2b.install',true) IS DISTINCT FROM 'COOPERATIVE_CASE_GATE_LAB'
 OR to_regclass('s0_pd_v02_lab.receipts') IS NULL
 OR to_regclass('s0_pre_dispatch_lab.cases') IS NULL
 THEN RAISE EXCEPTION 'G2B disposable-only installer refused';END IF;
END $lab$;
CREATE SCHEMA s0_pd_g2b_lab AUTHORIZATION s0_meta_owner;
SET ROLE s0_meta_owner;
CREATE TABLE s0_pd_g2b_lab.case_gates(
 case_ref text PRIMARY KEY REFERENCES s0_pre_dispatch_lab.cases(case_ref),
 store_ref text NOT NULL,
 generation bigint NOT NULL CHECK(generation>0),
 changed_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
REVOKE ALL ON SCHEMA s0_pd_g2b_lab FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA s0_pd_g2b_lab FROM PUBLIC;
ALTER TABLE s0_pd_g2b_lab.case_gates ENABLE ROW LEVEL SECURITY;
RESET ROLE;
COMMIT;
