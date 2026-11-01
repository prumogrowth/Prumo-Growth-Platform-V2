-- M09-04: Ed25519 replay journal, disposable PG17 only. Not a hosted migration.
BEGIN;
DO $$ BEGIN
  IF current_setting('server_version_num')::int / 10000 <> 17
     OR current_database() <> 's0_meta_ingress_lab'
     OR current_user <> 'postgres'
     OR current_setting('s0_meta.disposable', true) IS DISTINCT FROM 'YES'
     OR current_setting('s0_m09.install', true) IS DISTINCT FROM 'M2M_CANDIDATE_ONLY'
     OR to_regclass('s0_m09_lab.grants') IS NULL
     OR to_regclass('s0_meta_lab.principals') IS NULL
  THEN RAISE EXCEPTION 'disposable M09 registry prerequisite required'; END IF;
END $$;
SET ROLE s0_meta_owner;
CREATE TABLE s0_m09_lab.read_nonces (
  key_id text NOT NULL REFERENCES s0_meta_lab.principals(key_id),
  nonce text NOT NULL CHECK (nonce ~ '^[A-Za-z0-9_-]{16,128}$'),
  envelope_sha256 char(64) NOT NULL CHECK (envelope_sha256 ~ '^[0-9a-f]{64}$'),
  seen_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (key_id, nonce)
);
REVOKE ALL ON s0_m09_lab.read_nonces FROM PUBLIC;
ALTER TABLE s0_m09_lab.read_nonces ENABLE ROW LEVEL SECURITY;
GRANT INSERT ON s0_m09_lab.read_nonces TO s0_meta_runtime;
CREATE POLICY nonce_append_only ON s0_m09_lab.read_nonces
 FOR INSERT TO s0_meta_runtime WITH CHECK (true);
-- Runtime has no SELECT/UPDATE/DELETE on journal, no access to secret slots.
RESET ROLE;
COMMIT;
