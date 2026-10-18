-- WA06D-B, phase two: MUST execute in a fresh psql/server connection.
-- The DB/cluster will be deleted afterwards by the local ephemeral runner.
DO $verify$
DECLARE actual bytea;
BEGIN
 IF (SELECT count(*) FROM wa06d_postcommit.batch)<>1
   OR (SELECT count(*) FROM wa06d_postcommit.payload)<>1
   OR (SELECT count(*) FROM wa06d_postcommit.nonce)<>1
   OR (SELECT count(*) FROM wa06d_postcommit.occurrence)<>2
   OR (SELECT count(*) FROM wa06d_postcommit.task)<>2
   OR (SELECT count(*) FROM wa06d_postcommit.receipt)<>1
 THEN RAISE EXCEPTION 'WA06D_B01_POSTCOMMIT_INCOMPLETE'; END IF;
 RAISE NOTICE 'WA06D-B01 PASS: all records visible after COMMIT from fresh backend';

 IF (SELECT count(DISTINCT (entry_index,change_index,array_kind,item_index))
       FROM wa06d_postcommit.occurrence)<>2
 OR (SELECT count(DISTINCT provider_id) FROM wa06d_postcommit.occurrence)<>1
 THEN RAISE EXCEPTION 'WA06D_B02_POSITION_LOSS'; END IF;
 RAISE NOTICE 'WA06D-B02 PASS: duplicate provider ID preserved at separate positions';

 SELECT fingerprint INTO actual FROM wa06d_postcommit.batch
 WHERE principal_ref='fake_principal' AND request_ref='request_proof';
 IF actual IS DISTINCT FROM sha256(convert_to('synthetic_fingerprint','UTF8'))
 OR (SELECT digest.sha FROM wa06d_postcommit.payload digest WHERE batch_ref='batch_proof')
    IS DISTINCT FROM sha256(convert_to('SYNTHETIC_BODY','UTF8'))
 THEN RAISE EXCEPTION 'WA06D_B03_RECOVERY_MISMATCH'; END IF;
 RAISE NOTICE 'WA06D-B03 PASS: request_ref can resolve stored fingerprint after COMMIT';

 BEGIN
   INSERT INTO wa06d_postcommit.batch(batch_ref,principal_ref,request_ref,app_ref,shop_ref,fingerprint)
   VALUES ('different_batch','fake_principal','request_proof','app_a','shop_a',decode(repeat('00',32),'hex'));
   RAISE EXCEPTION 'WA06D_B04_COLLISION_NOT_REJECTED';
 EXCEPTION WHEN unique_violation THEN NULL; END;
 IF EXISTS(SELECT 1 FROM wa06d_postcommit.batch WHERE batch_ref='different_batch')
 THEN RAISE EXCEPTION 'WA06D_B04_PARTIAL_WRITE'; END IF;
 RAISE NOTICE 'WA06D-B04 PASS: request-ref collision rejected';

 BEGIN
   INSERT INTO wa06d_postcommit.batch(batch_ref,principal_ref,request_ref,app_ref,shop_ref,fingerprint)
   VALUES ('failed_batch','fake_principal','request_failed','app_a','shop_a',sha256(convert_to('fake','UTF8')));
   INSERT INTO wa06d_postcommit.payload(batch_ref,raw_bytes,sha)
   VALUES ('failed_batch',convert_to('RAW','UTF8'),sha256(convert_to('RAW','UTF8')));
   RAISE EXCEPTION 'INJECTED_ROLLBACK';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM<>'INJECTED_ROLLBACK' THEN RAISE; END IF;
 END;
 IF EXISTS(SELECT 1 FROM wa06d_postcommit.batch WHERE batch_ref='failed_batch')
 OR EXISTS(SELECT 1 FROM wa06d_postcommit.payload WHERE batch_ref='failed_batch')
 THEN RAISE EXCEPTION 'WA06D_B05_PARTIAL_ROLLBACK'; END IF;
 RAISE NOTICE 'WA06D-B05 PASS: injected failure rolled back its subtransaction';

 IF (SELECT r.occurrence_count FROM wa06d_postcommit.receipt r WHERE r.batch_ref='batch_proof')<>2
 THEN RAISE EXCEPTION 'WA06D_B06_RECEIPT_MISMATCH'; END IF;
 RAISE NOTICE 'WA06D-B06 PASS: receipt survives but is NOT HTTP ACK authority';
END $verify$;

-- Leave only temporary cluster artifacts, never user tables: cluster destroyed by runner.
