import { test } from 'node:test';
import assert from 'node:assert/strict';
import { inspectMetaWebhook } from './inbound.ts';
import { decideBatchAck } from './durable-receipt.ts';
import { FakeMetaStatusReconciler } from './technical-reconciliation.ts';
import type { CorrelationReference } from './technical-reconciliation.ts';
import type { GraphSendOutcome } from './graph-outbound.ts';
const scope={concessionaria_id:'SHOP1',canal_id:'CH1',meta_app_ref:'APP1',meta_waba_id:'WABA1',phone_number_id:'123456789'};
const ref:CorrelationReference={app_ref:'APP1',scope,intent_id:'INTENT1',recipient_verified:'5581900000000'};
const outcome:GraphSendOutcome={attempt_id:'ATT1',correlation_id:'CORR1',send_state:'API_ACCEPTED',api_accepted:true,provider_message_id:'wamid.id1',http_status:200,meta_error_code:null,meta_error_subcode:null,retry_automatically:false};
const encoder=new TextEncoder();const secret='test-secret';
async function signed(input:Uint8Array){const key=await crypto.subtle.importKey('raw',encoder.encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign']);return 'sha256='+Array.from(new Uint8Array(await crypto.subtle.sign('HMAC',key,input)),x=>x.toString(16).padStart(2,'0')).join('');}
test('AUD-UN-01 distinct message and status positions cannot collide',async()=>{
 const body=encoder.encode(JSON.stringify({object:'whatsapp_business_account',entry:[{id:'WABA1',changes:[{field:'messages',value:{metadata:{phone_number_id:'123456789'},messages:[{id:'wamid.in',from:'5581900000000',type:'text',timestamp:'1792320000'}],statuses:[{id:'wamid.out',recipient_id:'5581900000000',status:'sent',timestamp:'1792320000'}]}}]}]}));
 const result=await inspectMetaWebhook(body,await signed(body),secret);
 assert.equal(result.ok,true);
 if(result.ok)assert.notDeepEqual(result.events[0].position,result.events[1].position);
});
test('AUD-UN-02 receipt outcome must be primitive string',()=>{
 const forged={outcome:{toString:()=> 'ACCEPTED_DURABLE'},commit_state:'COMMITTED',total:1,accepted:1,duplicates:0,quarantined:0};
 assert.equal(decideBatchAck(1,forged).ack_allowed,false);
});
test('AUD-UN-03 projection must match claimed intent even with same shop/channel',()=>{
 const x=new FakeMetaStatusReconciler();assert.equal(x.registerAcceptedSend(ref,outcome).decision,'LINKED');
 assert.equal(x.projectionFor({...ref,intent_id:'INTRUDER_INTENT'},'wamid.id1'),undefined);
});
test('AUD-UN-04 same attempt but different correlation cannot count as already linked',()=>{
 const x=new FakeMetaStatusReconciler();assert.equal(x.registerAcceptedSend(ref,outcome).decision,'LINKED');
 assert.equal(x.registerAcceptedSend(ref,{...outcome,correlation_id:'OTHER_CORR'}).decision,'CONFLICT');
});
test('AUD-UN-05 verify exactly same snapshot as parsed despite caller mutation',async()=>{
 const obj={object:'whatsapp_business_account',entry:[{id:'WABA1',changes:[{field:'messages',value:{metadata:{phone_number_id:'123456789'},messages:[{id:'wamid.in',from:'5581900000000',type:'text',timestamp:'1792320000'}]}}]}]};
 const raw=encoder.encode(JSON.stringify(obj)),sig=await signed(raw);
 const promise=inspectMetaWebhook(raw,sig,secret);
 const adversarial=encoder.encode(JSON.stringify({...obj,entry:[{...obj.entry[0],id:'WABA2'}]}));
 assert.equal(adversarial.length,raw.length);
 raw.set(adversarial);
 const result=await promise;
 assert.equal(result.ok,true);
 if(result.ok)assert.equal(result.events[0].waba_id,'WABA1');
});

test('AUD-UN-06 receipt counters cannot exceed batch total',()=>{
 const forged={outcome:'ACCEPTED_DURABLE',commit_state:'COMMITTED',total:1,accepted:Number.MAX_SAFE_INTEGER,duplicates:Number.MAX_SAFE_INTEGER,quarantined:2};
 assert.equal(decideBatchAck(1,forged).status,503);
});
test('AUD-UN-07 no callback content leaks through a malformed aggregate',async()=>{
 const raw=encoder.encode(JSON.stringify({object:'whatsapp_business_account',entry:[{id:'WABA1',changes:[{field:'messages',value:{metadata:{phone_number_id:'123456789'},messages:[{id:'wamid.in',from:'5581900000000',timestamp:'1792320000',type:'text'},{id:'damaged'}]}}]}]}));
 const r=await inspectMetaWebhook(raw,await signed(raw),secret);assert.equal(r.ok,false);
 assert.equal(JSON.stringify(r).includes('5581900000000'),false);
});
test('AUD-UN-08 scope mismatch on existing message link cannot be counted duplicate',()=>{
 const x=new FakeMetaStatusReconciler();assert.equal(x.registerAcceptedSend(ref,outcome).decision,'LINKED');
 const cross={...ref,scope:{...ref.scope,canal_id:'CH2'}};assert.equal(x.registerAcceptedSend(cross,outcome).decision,'CONFLICT');
});
