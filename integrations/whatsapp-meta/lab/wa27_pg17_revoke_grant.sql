-- Template status restored but independent purpose grant revoked.
\set ON_ERROR_STOP on
BEGIN;
UPDATE wa27_lab.catalogs
 SET payload=jsonb_set(jsonb_set(payload,'{0,meta_status}','"APPROVED"'::jsonb),
   '{0,grants}','[]'::jsonb)
 WHERE reader_role='wa27_reader_shop_a';
COMMIT;
