/** Cross-runtime S0 PG17 -> Meta receipt consumer. No ACK, Graph or writes. */
import assert from 'node:assert/strict';
import {readFileSync,statSync} from 'node:fs';
import {inspectPinnedS0LabReceipt} from '../cloud-s0-ed25519-receipt-interop.ts';
import {inspectSignedMetaBatchChannelScope} from '../cloud-batch-scope-preflight.ts';

const s0Sha='01ffdb093013664b73b18d23f92aac2202578210';
if(process.argv.length!==3)throw Error('EXPECTED_PRIVATE_LAB_PROOF_PATH');
const path=process.argv[2];
const stat=statSync(path);
assert.equal((stat.mode & 0o077),0,'physical proof must be private');
const data=JSON.parse(readFileSync(path,'utf8'));
assert.equal(data.kind,'S0_PG17_DISPOSABLE_RECEIPT_TO_META_UNRATIFIED');
assert.equal(data.source_sha,s0Sha);
assert.deepEqual(Object.keys(data).sort(),[
 'kind','raw_base64','receipt','source_sha','trusted_expected',
 'trusted_s0_public_key_base64','trusted_meta_app_secret',
 'trusted_meta_signature_header','m08_lab_evidence',
].sort());
const raw=Buffer.from(data.raw_base64,'base64');
const pinned=Buffer.from(data.trusted_s0_public_key_base64,'base64');
assert.equal(pinned.length,32);
const expected=data.trusted_expected;
const receipt=data.receipt;
const clone=x=>structuredClone(x);
const inspect=(body=raw,proof=receipt,context=expected,key=pinned)=>
 inspectPinnedS0LabReceipt(body,proof,context,key);
const denied=result=>assert.equal(result.decision,'DENIED');
const allNoAuthority=result=>{
 for(const field of [
  'ack_allowed','http_ack_allowed','partial_ack_allowed','http_response_authorized',
  'production_authorized','send_authorized','s0_write_authorized',
  'durable_receipt_verified','commit_verified','service_identity_verified',
  'm2m_verified','commercial_effect_authorized','channel_policy_ratified',
  'retry_external','automatic_retry_authorized','replay_suppression_authorized',
 ])assert.equal(result[field],false,field);
 assert.equal('status' in result,false);
 assert.equal('action' in result,false);
};
let checks=0;
const test=(name,action)=>{
 action();
 checks+=1;
 process.stdout.write('PASS '+name+'\n');
};
test('PG17 signed receipt verified by unchanged Meta consumer',()=>{
 const result=inspect();
 assert.equal(result.decision,'S0_LAB_SIGNATURE_AND_CONTEXT_MATCH_UNRATIFIED');
 assert.equal(result.receipt_signature_matched,true);
 assert.equal(result.physical_bytes_matched,true);
 assert.equal(result.trusted_context_matched,true);
 allNoAuthority(result);
});
test('physical raw bytes tampered',()=>{
 const changed=Buffer.from(raw);changed[changed.length-1]^=1;
 const result=inspect(changed);denied(result);allNoAuthority(result);
});
test('whitespace changes original physical payload',()=>{
 denied(inspect(Buffer.concat([raw,Buffer.from(' ')])));
});
test('wrong independently pinned key cannot be self-selected',()=>{
 const key=Buffer.from(pinned);key[0]^=1;
 denied(inspect(raw,receipt,expected,key));
});
test('mutated receipt signature rejected',()=>{
 const altered=clone(receipt);
 altered.signature=Buffer.alloc(64,44).toString('base64');
 denied(inspect(raw,altered));
});
test('receipt embedded key is not a trust source',()=>{
 const altered=clone(receipt);
 altered.body.receipt_public_key=Buffer.alloc(32,4).toString('base64');
 denied(inspect(raw,altered));
});
test('stale routing revision rejected',()=>{
 const e=clone(expected);e.route_revision='2';denied(inspect(raw,receipt,e));
});
test('cross-tenant channel expectation rejected',()=>{
 const e=clone(expected);e.bindings[1].tenant='tenant_OTHER';denied(inspect(raw,receipt,e));
});
test('binding without an expected grant rejected',()=>{
 const e=clone(expected);e.bindings=e.bindings.slice(0,1);denied(inspect(raw,receipt,e));
});
test('M2M issuer mismatch rejected',()=>{
 const e=clone(expected);e.m2m_issuer='LAB_FOREIGN';denied(inspect(raw,receipt,e));
});
test('item count mismatch rejected',()=>{
 const e=clone(expected);e.expected_item_count=3;denied(inspect(raw,receipt,e));
});
test('repeated cryptographic check is not deduplication or HTTP ACK',()=>{
 const first=inspect(),second=inspect();
 assert.deepEqual(first,second);
 allNoAuthority(first);allNoAuthority(second);
});
const syntheticSecret=data.trusted_meta_app_secret;
const physicalMetaSignature=data.trusted_meta_signature_header;
const facts=data.m08_lab_evidence;
assert.equal(facts.rejected_sibling_batches_without_partial_storage,5);
assert.equal(facts.fresh_nonce_recovery_same_signed_receipt,true);
assert.equal(facts.nonce_replay_rejected,true);
assert.equal(facts.mutated_same_batch_conflict_without_second_batch,true);
assert.equal(typeof syntheticSecret,'string');
assert.match(physicalMetaSignature,/^sha256=[a-f0-9]{64}$/);
const now=Date.now();
const trustedChannels=expected.bindings.map(b=>({
 canal_id:b.channel,waba_id:b.waba,phone_number_id:b.phone,active:true,
}));
const metadataRegistry={
 contract_version:'wa-meta-credential-routing.v0.1-proposed',
 apps:[{
  app_ref:expected.app,route_ref:expected.route,
  concessionaria_id:'tenant_A',
  active:true,revision:Number(expected.route_revision),
  valid_from_ms:now-60000,valid_until_ms:now+60000,
  secret_slots:{get_verify_token:'M08_LAB_GET',
   post_app_secret:'M08_LAB_POST',graph_access_token:'M08_LAB_GRAPH'},
  channels:trustedChannels,
 }],
};
const ports=(registry=metadataRegistry)=>({
 currentRegistry:()=>registry,
 resolveSecret:slot=>slot==='M08_LAB_POST'?syntheticSecret:undefined,
 nowMs:()=>now,
});
const metaRequest={
 route:{route_ref:expected.route,expected_revision:Number(expected.route_revision)},
 raw_body:raw,signature_header:physicalMetaSignature,
};
const inspectMeta=(request=metaRequest,registry=metadataRegistry)=>
 inspectSignedMetaBatchChannelScope(request,ports(registry));
const asyncTest=async(name,run)=>{
 await run();checks++;process.stdout.write('PASS '+name+'\n');
};
await asyncTest('M08 whole S0-signed physical POST is HMAC-verified by Meta',async()=>{
 const result=await inspectMeta();
 assert.equal(result.decision,'SIGNED_MULTI_CHANNEL_UNRATIFIED');
 assert.equal(result.event_count,4);
 assert.equal(result.scope_count,2);
 assert.deepEqual(result.channels.map(c=>[c.waba_id,c.phone_number_id,
  c.canal_id,c.concessionaria_id,c.inbound_message_count,c.status_callback_count]),[
  ['100001','200001','channel_A','tenant_A',1,1],
  ['100002','200002','channel_A2','tenant_A',1,1],
 ]);
 assert.equal(result.raw_sha256,receipt.body.raw_sha256);
 assert.equal(result.ack_allowed,false);
 assert.equal(result.partial_ack_allowed,false);
 assert.equal(result.batch_partition_authorized,false);
 assert.equal(result.channel_policy_ratified,false);
 assert.equal(result.persisted,false);
 assert.equal('status' in result,false);
});
await asyncTest('M08 entire multi-WABA POST denied for changed Meta HMAC',async()=>{
 const result=await inspectMeta({...metaRequest,
  signature_header:'sha256='+('0'.repeat(64))});
 assert.equal(result.decision,'DENIED');
 assert.equal(result.event_count,0);
 assert.equal(result.ack_allowed,false);
});
await asyncTest('M08 entire physical POST denied for revoked second channel',async()=>{
 const altered=structuredClone(metadataRegistry);
 altered.apps[0].channels[1].active=false;
 const result=await inspectMeta(metaRequest,altered);
 assert.equal(result.decision,'DENIED');
 assert.equal(result.event_count,0);
 assert.equal(result.partial_ack_allowed,false);
});
await asyncTest('M08 entire physical POST denied for a foreign App owning sibling',async()=>{
 const altered=structuredClone(metadataRegistry);
 const foreign=altered.apps[0].channels.pop();
 altered.apps.push({
  ...altered.apps[0],app_ref:'LAB_APP_B',route_ref:'route_B',
  concessionaria_id:'tenant_B',
  secret_slots:{get_verify_token:'M08_FOREIGN_GET',
   post_app_secret:'M08_FOREIGN_POST',graph_access_token:'M08_FOREIGN_GRAPH'},
  channels:[foreign],
 });
 const result=await inspectMeta(metaRequest,altered);
 assert.equal(result.decision,'DENIED');
 assert.equal(result.event_count,0);
 assert.equal(result.partial_ack_allowed,false);
});
await asyncTest('M08 input byte modification invalidates entire Meta verification',async()=>{
 const damaged=Buffer.from(raw);
 damaged[damaged.length-1]^=1;
 const result=await inspectMeta({...metaRequest,raw_body:damaged});
 assert.equal(result.decision,'DENIED');
 assert.equal(result.event_count,0);
});
process.stdout.write('PASS '+checks+' physical PG17-to-Meta checks; no HTTP ACK authorized\n');
