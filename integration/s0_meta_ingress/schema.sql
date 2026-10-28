-- Standalone fixture only: installer must connect to its freshly created exclusive database.
BEGIN;
DO $$ BEGIN
 IF current_setting('server_version_num')::int / 10000 <> 17
 OR current_database() <> 's0_meta_ingress_lab'
 OR current_user <> 'postgres'
 OR current_setting('s0_meta.disposable', true) IS DISTINCT FROM 'YES' THEN
   RAISE EXCEPTION 'exclusive PG17 laboratory required';
 END IF;
END $$;
CREATE ROLE s0_meta_owner NOLOGIN NOSUPERUSER NOBYPASSRLS;
CREATE ROLE s0_meta_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
REVOKE ALL ON DATABASE s0_meta_ingress_lab FROM PUBLIC;
GRANT CONNECT ON DATABASE s0_meta_ingress_lab TO s0_meta_runtime;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA s0_meta_lab AUTHORIZATION s0_meta_owner;
SET ROLE s0_meta_owner;
SET search_path = s0_meta_lab, pg_catalog;
CREATE TABLE routes (
 id text PRIMARY KEY, app text NOT NULL, revision bigint NOT NULL CHECK(revision>0), active boolean NOT NULL
);
CREATE TABLE principals (
 key_id text PRIMARY KEY, issuer text NOT NULL, revision bigint NOT NULL CHECK(revision>0),
 public_key bytea NOT NULL CHECK(octet_length(public_key)=32), route text NOT NULL REFERENCES routes,
 app text NOT NULL, tenant text NOT NULL, scopes text[] NOT NULL, channels text[] NOT NULL,
 active boolean NOT NULL, not_before timestamptz NOT NULL, not_after timestamptz NOT NULL
);
CREATE TABLE bindings (
 route text NOT NULL REFERENCES routes, waba text NOT NULL, phone text NOT NULL,
 app text NOT NULL, tenant text NOT NULL, channel text NOT NULL,
 revision bigint NOT NULL CHECK(revision>0), active boolean NOT NULL,
 PRIMARY KEY(route,waba,phone), UNIQUE(route,channel)
);
CREATE TABLE batches (
 id uuid PRIMARY KEY, route text NOT NULL REFERENCES routes, app text NOT NULL,
 route_revision bigint NOT NULL, raw bytea NOT NULL, raw_sha text NOT NULL,
 item_count integer NOT NULL CHECK(item_count BETWEEN 1 AND 100), items_sha text NOT NULL,
 binding_snapshot jsonb NOT NULL, binding_sha text NOT NULL,
 issuer text NOT NULL, m2m_key text NOT NULL, m2m_revision bigint NOT NULL,
 receipt_key text NOT NULL, receipt_revision bigint NOT NULL, receipt_public bytea NOT NULL CHECK(octet_length(receipt_public)=32), instance text NOT NULL,
 audit_id uuid NOT NULL UNIQUE, committed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 UNIQUE(route,raw_sha)
);
CREATE TABLE occurrences (
 id uuid PRIMARY KEY, batch_id uuid NOT NULL REFERENCES batches,
 ordinal integer NOT NULL CHECK(ordinal>=0), normalized jsonb NOT NULL,
 UNIQUE(batch_id,ordinal)
);
CREATE TABLE aliases (
 route text NOT NULL REFERENCES routes, ref text NOT NULL, batch_id uuid NOT NULL REFERENCES batches,
 PRIMARY KEY(route,ref)
);
CREATE TABLE nonces (
 key_id text NOT NULL REFERENCES principals, nonce text NOT NULL,
 envelope_sha text NOT NULL, seen_at timestamptz NOT NULL DEFAULT clock_timestamp(), PRIMARY KEY(key_id,nonce)
);
CREATE TABLE audit (
 id uuid PRIMARY KEY, key_id text NOT NULL REFERENCES principals, nonce text NOT NULL,
 decision text NOT NULL, batch_id uuid REFERENCES batches,
 incoming_sha text NOT NULL, original_sha text, at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY(key_id,nonce) REFERENCES nonces(key_id,nonce)
);
REVOKE ALL ON ALL TABLES IN SCHEMA s0_meta_lab FROM PUBLIC;
GRANT USAGE ON SCHEMA s0_meta_lab TO s0_meta_runtime;
GRANT SELECT ON ALL TABLES IN SCHEMA s0_meta_lab TO s0_meta_runtime;
-- PostgreSQL requires UPDATE privilege for row locks; predicates block every actual UPDATE.
ALTER TABLE routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE principals ENABLE ROW LEVEL SECURITY;
ALTER TABLE bindings ENABLE ROW LEVEL SECURITY;
CREATE POLICY route_read ON routes FOR SELECT TO s0_meta_runtime USING(true);
CREATE POLICY route_lock ON routes FOR UPDATE TO s0_meta_runtime USING(true) WITH CHECK(false);
CREATE POLICY principal_read ON principals FOR SELECT TO s0_meta_runtime USING(true);
CREATE POLICY principal_lock ON principals FOR UPDATE TO s0_meta_runtime USING(true) WITH CHECK(false);
CREATE POLICY binding_read ON bindings FOR SELECT TO s0_meta_runtime USING(true);
CREATE POLICY binding_lock ON bindings FOR UPDATE TO s0_meta_runtime USING(true) WITH CHECK(false);
GRANT UPDATE(id) ON routes TO s0_meta_runtime;
GRANT UPDATE(key_id) ON principals TO s0_meta_runtime;
GRANT UPDATE(route) ON bindings TO s0_meta_runtime;
GRANT INSERT ON batches,occurrences,aliases,nonces,audit TO s0_meta_runtime;
RESET ROLE;
COMMIT;
