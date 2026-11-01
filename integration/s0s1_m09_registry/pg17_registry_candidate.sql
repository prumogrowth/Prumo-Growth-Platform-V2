-- M09-03 additive isolated laboratory candidate. NEVER run on hosted S0/S1.
-- Install ONLY after pinned S0 Meta Ingress schema in an exclusive PG17 disposal DB.
BEGIN;
DO $$
BEGIN
  IF current_setting('server_version_num')::int / 10000 <> 17
     OR current_database() <> 's0_meta_ingress_lab'
     OR current_user <> 'postgres'
     OR current_setting('s0_meta.disposable', true) IS DISTINCT FROM 'YES'
     OR current_setting('s0_m09.install', true) IS DISTINCT FROM 'CANDIDATE_ONLY'
  THEN RAISE EXCEPTION 'M09 isolated PG17 disposable installer only'; END IF;
END $$;
CREATE SCHEMA s0_m09_lab AUTHORIZATION s0_meta_owner;
SET ROLE s0_meta_owner;
SET search_path = s0_m09_lab,pg_catalog;

CREATE TABLE apps (
  app_ref text PRIMARY KEY,
  route_ref text NOT NULL UNIQUE REFERENCES s0_meta_lab.routes(id),
  concessionaria_id text NOT NULL UNIQUE,
  tenant text NOT NULL UNIQUE,
  revision bigint NOT NULL CHECK (revision > 0),
  active boolean NOT NULL,
  valid_from timestamptz NOT NULL,
  valid_until timestamptz NOT NULL,
  ownership_state text NOT NULL DEFAULT 'UNVERIFIED'
    CHECK (ownership_state='UNVERIFIED'),
  delegation_state text NOT NULL DEFAULT 'UNVERIFIED'
    CHECK (delegation_state='UNVERIFIED'),
  CHECK (valid_from < valid_until),
  UNIQUE (app_ref,route_ref)
);
-- WABA may contain multiple phones; WABA identity cannot cross App by uniqueness.
CREATE TABLE wabas (
  waba_id text PRIMARY KEY,
  app_ref text NOT NULL REFERENCES apps(app_ref),
  UNIQUE (waba_id,app_ref)
);
CREATE TABLE grants (
  canal_id text PRIMARY KEY,
  app_ref text NOT NULL,
  route_ref text NOT NULL,
  waba_id text NOT NULL,
  phone_number_id text NOT NULL UNIQUE,
  revision bigint NOT NULL CHECK (revision > 0),
  active boolean NOT NULL,
  FOREIGN KEY (app_ref,route_ref) REFERENCES apps(app_ref,route_ref),
  FOREIGN KEY (waba_id,app_ref) REFERENCES wabas(waba_id,app_ref),
  UNIQUE (route_ref,canal_id)
);
-- Only control-plane installer can access slot NAMES; runtime never selects here.
CREATE TABLE slots (
  slot_ref text PRIMARY KEY,
  app_ref text NOT NULL REFERENCES apps(app_ref),
  purpose text NOT NULL CHECK
    (purpose IN ('GET_VERIFY_TOKEN','POST_APP_SECRET','GRAPH_ACCESS_TOKEN')),
  UNIQUE (app_ref,purpose),
  CHECK (slot_ref ~ '^[A-Z][A-Z0-9_]{2,127}$'),
  CHECK (slot_ref !~ '^SUPABASE_')
);

REVOKE ALL ON ALL TABLES IN SCHEMA s0_m09_lab FROM PUBLIC;
REVOKE ALL ON SCHEMA s0_m09_lab FROM PUBLIC;
GRANT USAGE ON SCHEMA s0_m09_lab TO s0_meta_runtime;
GRANT SELECT ON apps,wabas,grants TO s0_meta_runtime;
-- PG17 row locks need UPDATE privilege; RLS forbids any actual UPDATE.
GRANT UPDATE(app_ref) ON apps TO s0_meta_runtime;
GRANT UPDATE(canal_id) ON grants TO s0_meta_runtime;
ALTER TABLE apps ENABLE ROW LEVEL SECURITY;
ALTER TABLE wabas ENABLE ROW LEVEL SECURITY;
ALTER TABLE grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE slots ENABLE ROW LEVEL SECURITY;
CREATE POLICY apps_read ON apps FOR SELECT TO s0_meta_runtime USING (true);
CREATE POLICY wabas_read ON wabas FOR SELECT TO s0_meta_runtime USING (true);
CREATE POLICY grants_read ON grants FOR SELECT TO s0_meta_runtime USING (true);
CREATE POLICY apps_lock ON apps FOR UPDATE TO s0_meta_runtime USING (true) WITH CHECK (false);
CREATE POLICY grants_lock ON grants FOR UPDATE TO s0_meta_runtime USING (true) WITH CHECK (false);
-- No runtime slot policy, no INSERT/UPDATE/DELETE for runtime, ever.
RESET ROLE;
COMMIT;
