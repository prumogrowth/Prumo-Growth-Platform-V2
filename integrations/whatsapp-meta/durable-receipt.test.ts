/** Legacy shape-only receipt must never authorize an HTTP action. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {decideBatchAck} from './durable-receipt.ts';

const forged=(overrides:Record<string,unknown>={})=>({
 outcome:'ACCEPTED_DURABLE',commit_state:'COMMITTED',
 total:4,accepted:4,duplicates:0,quarantined:0,...overrides,
});
const denied=(n:number,v:unknown)=>{
 const result=decideBatchAck(n,v);
 assert.equal(result.decision,'DENIED_NO_HTTP_AUTHORITY');
 assert.equal(result.reason,'UNTRUSTED_RECEIPT_PROVENANCE');
 for(const [k,val] of Object.entries(result)){
  if(k.endsWith('_allowed')||k.endsWith('_authorized')||k.endsWith('_verified'))
   assert.equal(val,false,k);
 }
 for(const key of ['status','statusCode','http_status','action','retry']) {
  assert.equal(key in result,false,key);
 }
 assert.equal(Object.isFrozen(result),true);
 assert.equal(JSON.stringify(result).includes('200'),false);
 return result;
};
test('WA-ACK-01: even perfectly forged COMMITTED cannot ACK',()=>{
 denied(4,forged());
});
test('WA-ACK-02: accepted and duplicates cannot ACK',()=>{
 denied(4,forged({accepted:2,duplicates:2}));
});
test('WA-ACK-03: ALREADY_ACCEPTED cannot suppress redelivery',()=>{
 denied(4,forged({outcome:'ALREADY_ACCEPTED',accepted:0,duplicates:4}));
});
test('WA-ACK-04: rollback, timeout and missing commit cannot act as transport policy',()=>{
 for(const input of [forged({commit_state:'ROLLED_BACK'}),
  {outcome:'RETRYABLE_STORAGE_FAILURE'},forged({commit_state:'TIMEOUT'})])
  denied(4,input);
});
test('WA-ACK-05: incomplete/overcounted batch cannot ACK',()=>{
 for(const input of [forged({accepted:3}),forged({total:3,accepted:3}),
  forged({accepted:5})])denied(4,input);
});
test('WA-ACK-06: quarantined items have no acknowledged policy',()=>{
 denied(4,forged({outcome:'QUARANTINED_DURABLE',accepted:3,quarantined:1}));
});
test('WA-ACK-07: inconsistent outcome labels cannot ACK',()=>{
 for(const input of [forged({outcome:'ALREADY_ACCEPTED'}),
  forged({accepted:0,duplicates:4}),forged({outcome:'UNKNOWN'})])
  denied(4,input);
});
test('WA-ACK-08: arbitrary objects and primitives cannot ACK',()=>{
 for(const v of [null,undefined,[],{},'COMMITTED',false])denied(4,v);
});
test('WA-ACK-09: invalid event counts have no authority',()=>{
 for(const n of [0,-1,NaN,Infinity,1.5,Number.MAX_SAFE_INTEGER+1])
  denied(n,forged());
});
test('WA-ACK-10: other S0-shaped claims cannot ACK',()=>{
 denied(4,{outcome:'ACCEPTED_DURABLE',accepted:4,duplicates:0,
  concessionaria_id:'fixture_uuid'});
});
test('WA-ACK-11: getter traps are not evaluated',()=>{
 const x=Object.defineProperty({},'commit_state',{
  enumerable:true,get(){throw Error('SHOULD_NEVER_READ');},
 });
 denied(4,x);
});
test('WA-ACK-12: hostile proxy traps are never evaluated',()=>{
 const p=new Proxy({},{
  get(){throw Error('GET');},ownKeys(){throw Error('KEYS');},
  getPrototypeOf(){throw Error('PROTOTYPE');},
 });
 denied(4,p);
});
test('WA-ACK-13: forged unsigned signature and HTTP claim are ignored',()=>{
 denied(1,{...forged({total:1,accepted:1}),
  signature:'SIGNED_BY_ATTACKER',status:200,action:'ACK',ack_allowed:true});
});
test('WA-ACK-14: receipts with arbitrary key and physical flags cannot ACK',()=>{
 denied(1,{...forged({total:1,accepted:1}),
  receipt_public_key:'UNPINNED',durable_receipt_verified:true,
  production_authorized:true,commit_verified:true});
});
test('WA-ACK-15: result is independent of all caller-controlled fields',()=>{
 assert.strictEqual(denied(4,forged()),denied(1,{status:200}));
 assert.strictEqual(denied(-1,null),denied(999999,{}));
});
test('WA-ACK-16: legacy API cannot authorize ACK through a repeated call',()=>{
 for(let i=0;i<16;i++)denied(4,forged());
});
