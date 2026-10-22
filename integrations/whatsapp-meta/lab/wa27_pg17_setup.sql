-- WA27: EPHEMERAL isolated PostgreSQL 17 fixture. NOT an S0 migration.
-- Role-scoped rows prove a narrow RLS property; no Supabase Auth / Meta / bank.
\set ON_ERROR_STOP on
CREATE SCHEMA wa27_lab;
CREATE ROLE wa27_reader_shop_a NOLOGIN NOINHERIT;
CREATE ROLE wa27_reader_shop_b NOLOGIN NOINHERIT;
CREATE ROLE wa27_reader_shop_none NOLOGIN NOINHERIT;
GRANT USAGE ON SCHEMA wa27_lab TO wa27_reader_shop_a,wa27_reader_shop_b,wa27_reader_shop_none;
CREATE TABLE wa27_lab.scopes (reader_role name NOT NULL, selection_ref text NOT NULL, payload jsonb NOT NULL, PRIMARY KEY(reader_role,selection_ref));
ALTER TABLE wa27_lab.scopes ENABLE ROW LEVEL SECURITY;
ALTER TABLE wa27_lab.scopes FORCE ROW LEVEL SECURITY;
CREATE POLICY wa27_only_current_role ON wa27_lab.scopes FOR SELECT USING (reader_role=current_user::name);
GRANT SELECT ON wa27_lab.scopes TO wa27_reader_shop_a,wa27_reader_shop_b,wa27_reader_shop_none;
CREATE TABLE wa27_lab.policies (reader_role name NOT NULL, selection_ref text NOT NULL, payload jsonb NOT NULL, PRIMARY KEY(reader_role,selection_ref));
ALTER TABLE wa27_lab.policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE wa27_lab.policies FORCE ROW LEVEL SECURITY;
CREATE POLICY wa27_only_current_role ON wa27_lab.policies FOR SELECT USING (reader_role=current_user::name);
GRANT SELECT ON wa27_lab.policies TO wa27_reader_shop_a,wa27_reader_shop_b,wa27_reader_shop_none;
CREATE TABLE wa27_lab.catalogs (reader_role name NOT NULL, selection_ref text NOT NULL, payload jsonb NOT NULL, PRIMARY KEY(reader_role,selection_ref));
ALTER TABLE wa27_lab.catalogs ENABLE ROW LEVEL SECURITY;
ALTER TABLE wa27_lab.catalogs FORCE ROW LEVEL SECURITY;
CREATE POLICY wa27_only_current_role ON wa27_lab.catalogs FOR SELECT USING (reader_role=current_user::name);
GRANT SELECT ON wa27_lab.catalogs TO wa27_reader_shop_a,wa27_reader_shop_b,wa27_reader_shop_none;
INSERT INTO wa27_lab.scopes (reader_role,selection_ref,payload) VALUES ('wa27_reader_shop_a','fixture_selection_100','{"selection_ref":"fixture_selection_100","concessionaria_id":"shop_A","waba_ref":"waba_A","catalog_revision":8,"language":"pt_BR","purpose_ref":"recontato","actor_kind":"PLANNER","actor_ref":"planner_A","flow_ref":"flow_A","campaign_ref":null,"case_ref":"case_A","lead_ref":"lead_A","case_version":4,"authorization_revision":2}'::jsonb);
INSERT INTO wa27_lab.policies (reader_role,selection_ref,payload) VALUES ('wa27_reader_shop_a','fixture_selection_100','{"selection_ref":"fixture_selection_100","concessionaria_id":"shop_A","waba_ref":"waba_A","case_ref":"case_A","lead_ref":"lead_A","case_version":4,"authorization_revision":2,"policy_revision":3,"consent_state":"VALID","opted_out":false,"case_authorized":true,"audience_eligible":true,"campaign_eligibility":"NOT_APPLICABLE"}'::jsonb);
INSERT INTO wa27_lab.catalogs (reader_role,selection_ref,payload) VALUES ('wa27_reader_shop_a','fixture_selection_100','[{"template_ref":"template_A","version_ref":"v5","catalog_revision":8,"concessionaria_id":"shop_A","waba_ref":"waba_A","language":"pt_BR","meta_category":"UTILITY","meta_status":"APPROVED","locally_active":true,"current_version":true,"purpose_refs":["recontato"],"grants":[{"purpose_ref":"recontato","actor_kind":"PLANNER","actor_ref":"planner_A","flow_ref":"flow_A","campaign_ref":null}]}]'::jsonb);
INSERT INTO wa27_lab.scopes (reader_role,selection_ref,payload) VALUES ('wa27_reader_shop_b','fixture_selection_100','{"selection_ref":"fixture_selection_100","concessionaria_id":"shop_B","waba_ref":"waba_B","catalog_revision":8,"language":"pt_BR","purpose_ref":"recontato","actor_kind":"PLANNER","actor_ref":"planner_B","flow_ref":"flow_B","campaign_ref":null,"case_ref":"case_B","lead_ref":"lead_B","case_version":4,"authorization_revision":2}'::jsonb);
INSERT INTO wa27_lab.policies (reader_role,selection_ref,payload) VALUES ('wa27_reader_shop_b','fixture_selection_100','{"selection_ref":"fixture_selection_100","concessionaria_id":"shop_B","waba_ref":"waba_B","case_ref":"case_B","lead_ref":"lead_B","case_version":4,"authorization_revision":2,"policy_revision":3,"consent_state":"VALID","opted_out":false,"case_authorized":true,"audience_eligible":true,"campaign_eligibility":"NOT_APPLICABLE"}'::jsonb);
INSERT INTO wa27_lab.catalogs (reader_role,selection_ref,payload) VALUES ('wa27_reader_shop_b','fixture_selection_100','[{"template_ref":"template_B","version_ref":"v5","catalog_revision":8,"concessionaria_id":"shop_B","waba_ref":"waba_B","language":"pt_BR","meta_category":"UTILITY","meta_status":"APPROVED","locally_active":true,"current_version":true,"purpose_refs":["recontato"],"grants":[{"purpose_ref":"recontato","actor_kind":"PLANNER","actor_ref":"planner_B","flow_ref":"flow_B","campaign_ref":null}]}]'::jsonb);
-- Owner deliberately retains write privileges; reader roles do not.
SELECT 'WA27-SETUP PASS' WHERE (SELECT COUNT(*) FROM wa27_lab.scopes)=2 AND (SELECT COUNT(*) FROM wa27_lab.policies)=2 AND (SELECT COUNT(*) FROM wa27_lab.catalogs)=2;
