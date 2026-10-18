-- WA-06D / PG17 executable lab candidate: transaction, replay, scope, rollback.
-- Run ONLY in a disposable local PostgreSQL 17 database:
-- psql -X -v ON_ERROR_STOP=1 -f integrations/whatsapp-meta/lab/wa06d_pg17_atomicity.sql
-- Not a production migration. No identities, HMAC, real channel or HTTP ACK.
-- Every table/function is pg_temp. ROLLBACK intentionally removes all objects.
BEGIN;

CREATE TEMP TABLE wa06d_registry (
 app text NOT NULL, shop text NOT NULL, channel text NOT NULL UNIQUE,
 waba text NOT NULL, sender text NOT NULL, active boolean NOT NULL DEFAULT true,
 PRIMARY KEY(app,channel), UNIQUE(waba,sender)
) ON COMMIT DROP;
CREATE TEMP TABLE wa06d_batch (
 batch text PRIMARY KEY, principal text NOT NULL, request text NOT NULL,
 app text NOT NULL, shop text NOT NULL, fingerprint bytea NOT NULL,
 UNIQUE(principal,request)
) ON COMMIT DROP;
CREATE TEMP TABLE wa06d_payload (
 batch text PRIMARY KEY REFERENCES pg_temp.wa06d_batch(batch),
 raw_bytes bytea NOT NULL, digest bytea NOT NULL,
 CHECK(octet_length(raw_bytes)>0), CHECK(digest=sha256(raw_bytes))
) ON COMMIT DROP;
CREATE TEMP TABLE wa06d_nonce (
 principal text NOT NULL, epoch integer NOT NULL CHECK(epoch>0),
 nonce text NOT NULL, batch text NOT NULL REFERENCES pg_temp.wa06d_batch(batch),
 fingerprint bytea NOT NULL, PRIMARY KEY(principal,epoch,nonce)
) ON COMMIT DROP;
CREATE TEMP TABLE wa06d_occurrence (
 occurrence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 batch text NOT NULL REFERENCES pg_temp.wa06d_batch(batch),
 entry_index integer NOT NULL CHECK(entry_index BETWEEN 0 AND 1000),
 change_index integer NOT NULL CHECK(change_index BETWEEN 0 AND 1000),
 kind text NOT NULL CHECK(kind IN ('messages','statuses')),
 item_index integer NOT NULL CHECK(item_index BETWEEN 0 AND 1000),
 channel text NOT NULL, provider_id text NOT NULL,
 UNIQUE(batch,entry_index,change_index,kind,item_index)
) ON COMMIT DROP;
CREATE TEMP TABLE wa06d_task (
 occurrence bigint PRIMARY KEY REFERENCES pg_temp.wa06d_occurrence(occurrence),
 state text NOT NULL CHECK(state='READY')
) ON COMMIT DROP;
CREATE TEMP TABLE wa06d_receipt (
 batch text PRIMARY KEY REFERENCES pg_temp.wa06d_batch(batch),
 fingerprint bytea NOT NULL, item_count integer NOT NULL CHECK(item_count>0),
 state text NOT NULL CHECK(state='IN_TX_ONLY')
) ON COMMIT DROP;

INSERT INTO pg_temp.wa06d_registry(app,shop,channel,waba,sender) VALUES
 ('app_a','shop_a','chan_a','waba_a','sender_a'),
 ('app_a','shop_a','chan_b','waba_a','sender_b'),
 ('app_b','shop_b','chan_c','waba_b','sender_c');

-- Pure fixture: principal is a *supplied string*, not authenticated identity.
-- PostgreSQL atomicity is real when executed, but these tables are TEMP.
CREATE FUNCTION pg_temp.wa06d_accept(
 p_principal text,p_request text,p_nonce text,p_epoch integer,p_batch text,
 p_app text,p_shop text,p_raw bytea,p_events jsonb,p_fault text DEFAULT 'NONE'
) RETURNS text LANGUAGE plpgsql SECURITY INVOKER
 SET search_path=pg_catalog,pg_temp AS $fn$
DECLARE
 v_fingerprint bytea; v_old record; v_event jsonb; v_ref bigint; v_n integer:=0;
BEGIN
 IF p_principal IS NULL OR p_principal='' OR p_request IS NULL OR p_request=''
    OR p_nonce IS NULL OR p_nonce='' OR p_epoch IS NULL OR p_epoch<1
    OR p_batch IS NULL OR p_batch='' OR p_app IS NULL OR p_app=''
    OR p_shop IS NULL OR p_shop='' OR p_raw IS NULL
    OR octet_length(p_raw) NOT BETWEEN 1 AND 262144
    OR jsonb_typeof(p_events) IS DISTINCT FROM 'array'
    OR jsonb_array_length(p_events) NOT BETWEEN 1 AND 100
    OR p_fault IS NULL OR p_fault NOT IN ('NONE','AFTER_PAYLOAD','AFTER_ITEM')
 THEN RAISE EXCEPTION 'LAB_INVALID_INPUT' USING ERRCODE='22023'; END IF;
 -- Must check declared scope before allowing even a previously stored replay.
 FOR v_event IN SELECT value FROM jsonb_array_elements(p_events) LOOP
   IF jsonb_typeof(v_event) IS DISTINCT FROM 'object'
      OR jsonb_typeof(v_event->'entry_index') IS DISTINCT FROM 'number'
      OR (v_event->>'entry_index') !~ '^[0-9]{1,4}$'
      OR (v_event->>'entry_index')::integer > 1000
      OR jsonb_typeof(v_event->'change_index') IS DISTINCT FROM 'number'
      OR (v_event->>'change_index') !~ '^[0-9]{1,4}$'
      OR (v_event->>'change_index')::integer > 1000
      OR jsonb_typeof(v_event->'item_index') IS DISTINCT FROM 'number'
      OR (v_event->>'item_index') !~ '^[0-9]{1,4}$'
      OR (v_event->>'item_index')::integer > 1000
      OR v_event->>'kind' NOT IN ('messages','statuses')
      OR v_event->>'kind' IS NULL
      OR v_event->>'provider_id' IS NULL
      OR v_event->>'app' IS DISTINCT FROM p_app
      OR v_event->>'shop' IS DISTINCT FROM p_shop
      OR NOT EXISTS (
        SELECT 1 FROM pg_temp.wa06d_registry r
        WHERE r.app=p_app AND r.shop=p_shop AND r.channel=v_event->>'channel'
        AND r.waba=v_event->>'waba' AND r.sender=v_event->>'sender'
        AND r.active FOR SHARE
      )
   THEN RAISE EXCEPTION 'LAB_SCOPE_DENIED' USING ERRCODE='42501'; END IF;
   v_n:=v_n+1;
 END LOOP;
 -- A consistency hash, NOT signature or proof of authenticated Meta bytes.
 v_fingerprint:=sha256(p_raw || convert_to(p_events::text || '|' ||
                  p_app || '|' || p_shop || '|' || p_batch,'UTF8'));
 SELECT n.batch,n.fingerprint INTO v_old FROM pg_temp.wa06d_nonce n
 WHERE n.principal=p_principal AND n.epoch=p_epoch AND n.nonce=p_nonce FOR UPDATE;
 IF FOUND AND (v_old.batch<>p_batch OR v_old.fingerprint<>v_fingerprint)
 THEN RAISE EXCEPTION 'LAB_NONCE_CONFLICT' USING ERRCODE='23505'; END IF;
 SELECT b.batch,b.fingerprint INTO v_old FROM pg_temp.wa06d_batch b
 WHERE b.principal=p_principal AND b.request=p_request FOR UPDATE;
 IF FOUND AND (v_old.batch<>p_batch OR v_old.fingerprint<>v_fingerprint)
 THEN RAISE EXCEPTION 'LAB_REQUEST_CONFLICT' USING ERRCODE='23505'; END IF;
 SELECT b.batch,b.principal,b.request,b.fingerprint INTO v_old
 FROM pg_temp.wa06d_batch b WHERE b.batch=p_batch FOR UPDATE;
 IF FOUND THEN
   IF v_old.principal<>p_principal OR v_old.request<>p_request
      OR v_old.fingerprint<>v_fingerprint
   THEN RAISE EXCEPTION 'LAB_REQUEST_CONFLICT' USING ERRCODE='23505'; END IF;
   INSERT INTO pg_temp.wa06d_nonce(principal,epoch,nonce,batch,fingerprint)
   VALUES(p_principal,p_epoch,p_nonce,p_batch,v_fingerprint)
   ON CONFLICT(principal,epoch,nonce) DO NOTHING;
   RETURN 'LAB_REPLAY_IN_TX';
 END IF;
 INSERT INTO pg_temp.wa06d_batch(batch,principal,request,app,shop,fingerprint)
 VALUES(p_batch,p_principal,p_request,p_app,p_shop,v_fingerprint);
 INSERT INTO pg_temp.wa06d_payload(batch,raw_bytes,digest)
 VALUES(p_batch,p_raw,sha256(p_raw));
 IF p_fault='AFTER_PAYLOAD'
 THEN RAISE EXCEPTION 'LAB_INJECT_AFTER_PAYLOAD'; END IF;
 INSERT INTO pg_temp.wa06d_nonce(principal,epoch,nonce,batch,fingerprint)
 VALUES(p_principal,p_epoch,p_nonce,p_batch,v_fingerprint);
 FOR v_event IN SELECT value FROM jsonb_array_elements(p_events) LOOP
   INSERT INTO pg_temp.wa06d_occurrence(
     batch,entry_index,change_index,kind,item_index,channel,provider_id)
   VALUES(p_batch,(v_event->>'entry_index')::integer,
          (v_event->>'change_index')::integer,v_event->>'kind',
          (v_event->>'item_index')::integer,
          v_event->>'channel',v_event->>'provider_id')
   RETURNING occurrence INTO v_ref;
   IF p_fault='AFTER_ITEM'
   THEN RAISE EXCEPTION 'LAB_INJECT_AFTER_ITEM'; END IF;
   INSERT INTO pg_temp.wa06d_task(occurrence,state) VALUES(v_ref,'READY');
 END LOOP;
 INSERT INTO pg_temp.wa06d_receipt(batch,fingerprint,item_count,state)
 VALUES(p_batch,v_fingerprint,v_n,'IN_TX_ONLY');
 RETURN 'LAB_INSERTED_IN_TX'; -- NOT COMMITTED and never Meta ACK.
END $fn$;

DO $test$
DECLARE
 raw bytea := convert_to('SYNTHETIC_ONLY','UTF8');
 items jsonb := '[{"kind":"statuses","entry_index":0,"change_index":0,"item_index":0,"app":"app_a","shop":"shop_a","channel":"chan_a","waba":"waba_a","sender":"sender_a","provider_id":"wamid.FAKE"}]';
 dup jsonb;
 result text;
BEGIN
 result:=pg_temp.wa06d_accept('fake','req1','nonce1',1,'batch1','app_a','shop_a',raw,items);
 IF result<>'LAB_INSERTED_IN_TX' OR
    (SELECT count(*) FROM pg_temp.wa06d_payload)<>1 OR
    (SELECT count(*) FROM pg_temp.wa06d_nonce)<>1 OR
    (SELECT count(*) FROM pg_temp.wa06d_occurrence)<>1 OR
    (SELECT count(*) FROM pg_temp.wa06d_task)<>1 OR
    (SELECT count(*) FROM pg_temp.wa06d_receipt)<>1
 THEN RAISE EXCEPTION 'WA06D_01_FAIL'; END IF;
 RAISE NOTICE 'WA06D-01 PASS';

 IF pg_temp.wa06d_accept('fake','req1','nonce1',1,'batch1','app_a','shop_a',raw,items)<>'LAB_REPLAY_IN_TX'
    OR pg_temp.wa06d_accept('fake','req1','nonce2',1,'batch1','app_a','shop_a',raw,items)<>'LAB_REPLAY_IN_TX'
    OR (SELECT count(*) FROM pg_temp.wa06d_task)<>1
    OR (SELECT count(*) FROM pg_temp.wa06d_nonce)<>2
 THEN RAISE EXCEPTION 'WA06D_02_FAIL'; END IF;
 RAISE NOTICE 'WA06D-02 PASS';

 BEGIN
   PERFORM pg_temp.wa06d_accept('fake','req_other','nonce1',1,'other','app_a','shop_a',raw,items);
   RAISE EXCEPTION 'EXPECTED_DENIAL';
 EXCEPTION WHEN OTHERS THEN
   IF SQLERRM<>'LAB_NONCE_CONFLICT' THEN RAISE;END IF;
 END;
 IF EXISTS(SELECT 1 FROM pg_temp.wa06d_batch WHERE batch='other')
 THEN RAISE EXCEPTION 'WA06D_03_FAIL';END IF;
 RAISE NOTICE 'WA06D-03 PASS';

 BEGIN
   PERFORM pg_temp.wa06d_accept('fake','req1','nonce3',1,'batch1','app_a','shop_a',
            convert_to('CHANGED','UTF8'),items);
   RAISE EXCEPTION 'EXPECTED_DENIAL';
 EXCEPTION WHEN OTHERS THEN
   IF SQLERRM<>'LAB_REQUEST_CONFLICT' THEN RAISE;END IF;
 END;
 RAISE NOTICE 'WA06D-04 PASS';

 BEGIN
   PERFORM pg_temp.wa06d_accept('fake','req_fail','nonce_fail',1,'batch_fail',
            'app_a','shop_a',raw,items,'AFTER_PAYLOAD');
   RAISE EXCEPTION 'EXPECTED_DENIAL';
 EXCEPTION WHEN OTHERS THEN
   IF SQLERRM<>'LAB_INJECT_AFTER_PAYLOAD' THEN RAISE;END IF;
 END;
 IF EXISTS(SELECT 1 FROM pg_temp.wa06d_batch WHERE batch='batch_fail')
 OR EXISTS(SELECT 1 FROM pg_temp.wa06d_payload WHERE batch='batch_fail')
 OR EXISTS(SELECT 1 FROM pg_temp.wa06d_nonce WHERE nonce='nonce_fail')
 THEN RAISE EXCEPTION 'WA06D_05_FAIL';END IF;
 RAISE NOTICE 'WA06D-05 PASS';

 BEGIN
   PERFORM pg_temp.wa06d_accept('fake','req_fail2','nonce_fail2',1,'batch_fail2',
            'app_a','shop_a',raw,items,'AFTER_ITEM');
   RAISE EXCEPTION 'EXPECTED_DENIAL';
 EXCEPTION WHEN OTHERS THEN
   IF SQLERRM<>'LAB_INJECT_AFTER_ITEM' THEN RAISE;END IF;
 END;
 IF EXISTS(SELECT 1 FROM pg_temp.wa06d_batch WHERE batch='batch_fail2')
 OR EXISTS(SELECT 1 FROM pg_temp.wa06d_occurrence WHERE batch='batch_fail2')
 OR EXISTS(SELECT 1 FROM pg_temp.wa06d_nonce WHERE nonce='nonce_fail2')
 THEN RAISE EXCEPTION 'WA06D_06_FAIL';END IF;
 RAISE NOTICE 'WA06D-06 PASS';

 IF pg_temp.wa06d_accept('fake','req_fail2','nonce_fail2',1,'batch_fail2',
      'app_a','shop_a',raw,items)<>'LAB_INSERTED_IN_TX'
 OR (SELECT count(*) FROM pg_temp.wa06d_task)<>2
 THEN RAISE EXCEPTION 'WA06D_07_FAIL';END IF;
 RAISE NOTICE 'WA06D-07 PASS';

 -- statuses[].id is message reference, not a unique callback occurrence.
 dup:=items || jsonb_build_array(jsonb_set(items->0,'{item_index}','1'::jsonb));
 IF pg_temp.wa06d_accept('fake','req_double','nonce_double',1,'batch_double',
       'app_a','shop_a',raw,dup)<>'LAB_INSERTED_IN_TX'
 OR (SELECT count(*) FROM pg_temp.wa06d_occurrence WHERE batch='batch_double')<>2
 THEN RAISE EXCEPTION 'WA06D_08_FAIL';END IF;
 RAISE NOTICE 'WA06D-08 PASS';

 dup:=items || jsonb_build_array(
       jsonb_set(jsonb_set(items->0,'{item_index}','1'::jsonb),'{shop}','"shop_b"'::jsonb));
 BEGIN
   PERFORM pg_temp.wa06d_accept('fake','req_cross','nonce_cross',1,'batch_cross',
            'app_a','shop_a',raw,dup);
   RAISE EXCEPTION 'EXPECTED_DENIAL';
 EXCEPTION WHEN OTHERS THEN
   IF SQLERRM<>'LAB_SCOPE_DENIED' THEN RAISE;END IF;
 END;
 IF EXISTS(SELECT 1 FROM pg_temp.wa06d_batch WHERE batch='batch_cross')
 THEN RAISE EXCEPTION 'WA06D_09_FAIL';END IF;
 RAISE NOTICE 'WA06D-09 PASS';

 UPDATE pg_temp.wa06d_registry SET active=false WHERE channel='chan_a';
 BEGIN
   PERFORM pg_temp.wa06d_accept('fake','req_revoked','nonce_revoked',1,'batch_revoked',
            'app_a','shop_a',raw,items);
   RAISE EXCEPTION 'EXPECTED_DENIAL';
 EXCEPTION WHEN OTHERS THEN
   IF SQLERRM<>'LAB_SCOPE_DENIED' THEN RAISE;END IF;
 END;
 RAISE NOTICE 'WA06D-10 PASS';

 -- This record is visible only INSIDE the uncommitted laboratory transaction.
 IF (SELECT r.state FROM pg_temp.wa06d_receipt r JOIN pg_temp.wa06d_batch b USING(batch)
     WHERE b.principal='fake' AND b.request='req_double')<>'IN_TX_ONLY'
 THEN RAISE EXCEPTION 'WA06D_11_FAIL';END IF;
 RAISE NOTICE 'WA06D-11 PASS';

 -- WA06D-12: same item index under separate entry[] indices is valid.
 dup:=items || jsonb_build_array(jsonb_set(items->0,'{entry_index}','1'::jsonb));
 IF pg_temp.wa06d_accept('fake','req_multientry','nonce_multientry',1,
       'batch_multientry','app_a','shop_a',raw,dup)<>'LAB_INSERTED_IN_TX'
 OR (SELECT count(*) FROM pg_temp.wa06d_occurrence WHERE batch='batch_multientry')<>2
 OR (SELECT count(*) FROM pg_temp.wa06d_task t
     JOIN pg_temp.wa06d_occurrence o ON o.occurrence=t.occurrence
     WHERE o.batch='batch_multientry')<>2
 THEN RAISE EXCEPTION 'WA06D_12_FAIL';END IF;
 RAISE NOTICE 'WA06D-12 PASS';

 -- WA06D-13: repeating the exact same full position rolls back the batch.
 dup:=items || jsonb_build_array(items->0);
 BEGIN
   PERFORM pg_temp.wa06d_accept('fake','req_samepos','nonce_samepos',1,
            'batch_samepos','app_a','shop_a',raw,dup);
   RAISE EXCEPTION 'EXPECTED_DENIAL';
 EXCEPTION WHEN unique_violation THEN NULL;
 END;
 IF EXISTS(SELECT 1 FROM pg_temp.wa06d_batch WHERE batch='batch_samepos')
 OR EXISTS(SELECT 1 FROM pg_temp.wa06d_payload WHERE batch='batch_samepos')
 OR EXISTS(SELECT 1 FROM pg_temp.wa06d_nonce WHERE nonce='nonce_samepos')
 OR EXISTS(SELECT 1 FROM pg_temp.wa06d_occurrence WHERE batch='batch_samepos')
 OR EXISTS(SELECT 1 FROM pg_temp.wa06d_receipt WHERE batch='batch_samepos')
 THEN RAISE EXCEPTION 'WA06D_13_FAIL';END IF;
 RAISE NOTICE 'WA06D-13 PASS';

 -- WA06D-14: two distinct channels of the same App and dealership accepted.
 dup:=items || jsonb_build_array(
       jsonb_set(jsonb_set(jsonb_set(items->0,'{item_index}','1'::jsonb),
                '{channel}','"chan_b"'::jsonb),'{sender}','"sender_b"'::jsonb));
 IF pg_temp.wa06d_accept('fake','req_twochan','nonce_twochan',1,
        'batch_twochan','app_a','shop_a',raw,dup)<>'LAB_INSERTED_IN_TX'
 OR (SELECT count(*) FROM pg_temp.wa06d_occurrence WHERE batch='batch_twochan')<>2
 THEN RAISE EXCEPTION 'WA06D_14_FAIL';END IF;
 RAISE NOTICE 'WA06D-14 PASS';
END $test$;

ROLLBACK;
