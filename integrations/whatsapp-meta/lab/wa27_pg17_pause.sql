-- Restore opt-out while Meta provider template becomes paused.
\set ON_ERROR_STOP on
BEGIN;
UPDATE wa27_lab.policies
 SET payload=jsonb_set(jsonb_set(payload,'{opted_out}','false'::jsonb),
     '{policy_revision}','4'::jsonb)
 WHERE reader_role='wa27_reader_shop_a';
UPDATE wa27_lab.catalogs
 SET payload=jsonb_set(payload,'{0,meta_status}','"PAUSED"'::jsonb)
 WHERE reader_role='wa27_reader_shop_a';
COMMIT;
