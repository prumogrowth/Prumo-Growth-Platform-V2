-- Simulate an authorized server-side revoke between separate PG sessions.
\set ON_ERROR_STOP on
BEGIN;
UPDATE wa27_lab.policies
 SET payload=jsonb_set(payload,'{opted_out}','true'::jsonb)
 WHERE reader_role='wa27_reader_shop_a';
COMMIT;
