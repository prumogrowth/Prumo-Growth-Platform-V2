-- Separate actor identity/authorization revision change; grants restored.
\set ON_ERROR_STOP on
BEGIN;
UPDATE wa27_lab.catalogs
 SET payload=jsonb_set(payload,'{0,grants}',
   '[{"purpose_ref":"recontato","actor_kind":"PLANNER","actor_ref":"planner_A","flow_ref":"flow_A","campaign_ref":null}]'::jsonb)
 WHERE reader_role='wa27_reader_shop_a';
UPDATE wa27_lab.scopes
 SET payload=jsonb_set(jsonb_set(payload,'{actor_ref}','"planner_revoked"'::jsonb),
   '{authorization_revision}','3'::jsonb)
 WHERE reader_role='wa27_reader_shop_a';
UPDATE wa27_lab.policies
 SET payload=jsonb_set(payload,'{authorization_revision}','3'::jsonb)
 WHERE reader_role='wa27_reader_shop_a';
COMMIT;
