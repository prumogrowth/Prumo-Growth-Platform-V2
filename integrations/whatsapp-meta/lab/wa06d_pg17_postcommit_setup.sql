-- WA06D-B, phase one: a disposable database only, durable across psql sessions.
-- DO NOT run outside the isolated cluster created by run-wa06d-ephemeral.sh.
BEGIN;
CREATE SCHEMA wa06d_postcommit;
CREATE TABLE wa06d_postcommit.batch (
 batch_ref text PRIMARY KEY, principal_ref text NOT NULL, request_ref text NOT NULL,
 app_ref text NOT NULL, shop_ref text NOT NULL,
 fingerprint bytea NOT NULL, UNIQUE(principal_ref,request_ref)
);
CREATE TABLE wa06d_postcommit.payload (
 batch_ref text PRIMARY KEY REFERENCES wa06d_postcommit.batch(batch_ref),
 raw_bytes bytea NOT NULL CHECK(octet_length(raw_bytes)>0),
 sha bytea NOT NULL CHECK(sha=sha256(raw_bytes))
);
CREATE TABLE wa06d_postcommit.nonce (
 principal_ref text NOT NULL, key_epoch integer NOT NULL,
 nonce_ref text NOT NULL, batch_ref text NOT NULL REFERENCES wa06d_postcommit.batch(batch_ref),
 PRIMARY KEY(principal_ref,key_epoch,nonce_ref)
);
CREATE TABLE wa06d_postcommit.occurrence (
 occurrence_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 batch_ref text NOT NULL REFERENCES wa06d_postcommit.batch(batch_ref),
 entry_index integer NOT NULL, change_index integer NOT NULL,
 array_kind text NOT NULL, item_index integer NOT NULL,
 provider_id text NOT NULL, channel_ref text NOT NULL,
 UNIQUE(batch_ref,entry_index,change_index,array_kind,item_index)
);
CREATE TABLE wa06d_postcommit.task (
 occurrence_id bigint PRIMARY KEY REFERENCES wa06d_postcommit.occurrence(occurrence_id),
 state text NOT NULL CHECK(state='READY')
);
CREATE TABLE wa06d_postcommit.receipt (
 batch_ref text PRIMARY KEY REFERENCES wa06d_postcommit.batch(batch_ref),
 fingerprint bytea NOT NULL, occurrence_count integer NOT NULL,
 state text NOT NULL CHECK(state='IN_TX_ONLY')
);
INSERT INTO wa06d_postcommit.batch(batch_ref,principal_ref,request_ref,app_ref,shop_ref,fingerprint)
 VALUES('batch_proof','fake_principal','request_proof','app_a','shop_a',sha256(convert_to('synthetic_fingerprint','UTF8')));
INSERT INTO wa06d_postcommit.payload(batch_ref,raw_bytes,sha)
 VALUES('batch_proof',convert_to('SYNTHETIC_BODY','UTF8'),sha256(convert_to('SYNTHETIC_BODY','UTF8')));
INSERT INTO wa06d_postcommit.nonce(principal_ref,key_epoch,nonce_ref,batch_ref)
 VALUES('fake_principal',1,'nonce_proof','batch_proof');
INSERT INTO wa06d_postcommit.occurrence(batch_ref,entry_index,change_index,array_kind,item_index,provider_id,channel_ref)
 VALUES ('batch_proof',0,0,'statuses',0,'wamid.FAKE','chan_a'),
        ('batch_proof',1,0,'statuses',0,'wamid.FAKE','chan_a');
INSERT INTO wa06d_postcommit.task(occurrence_id,state)
 SELECT occurrence_id,'READY' FROM wa06d_postcommit.occurrence WHERE batch_ref='batch_proof';
INSERT INTO wa06d_postcommit.receipt(batch_ref,fingerprint,occurrence_count,state)
 SELECT batch_ref,fingerprint,2,'IN_TX_ONLY' FROM wa06d_postcommit.batch WHERE batch_ref='batch_proof';
COMMIT;
