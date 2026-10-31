/** Cross-runtime S0 PG17 -> Meta receipt consumer. No ACK, Graph or writes. */
import assert from 'node:assert/strict';
import {readFileSync,statSync} from 'node:fs';
import {inspectPinnedS0LabReceipt} from '../cloud-s0-ed25519-receipt-interop.ts';

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
 'trusted_s0_public_key_base64',
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
process.stdout.write('PASS '+checks+' physical PG17-to-Meta checks; no HTTP ACK authorized\n');
