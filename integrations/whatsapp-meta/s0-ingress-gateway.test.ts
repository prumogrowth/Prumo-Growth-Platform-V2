import {test} from 'node:test';
import assert from 'node:assert/strict';
import {prepareS0HandoffFixture,type S0HandoffCandidate} from './s0-handoff-contract.ts';
import {FakePrivilegedS0Ingress,type FakeS0IngressPorts} from './s0-ingress-gateway.ts';
import {FakeProtectedPayloads} from './transactional-ingress.ts';
import type {TrustedMetaRegistry} from './credential-routing.ts';
const at=1792320000000;
const secret='FAKE_APP_HMAC_KEY';
const app={app_ref:'APP_A',route_ref:'ROUTE_A',concessionaria_id:'SHOP_A',revision:4,active:true,
 valid_from_ms:at-10000,valid_until_ms:at+10000,
 secret_slots:{get_verify_token:'A_VERIFY',post_app_secret:'A_HMAC',graph_access_token:'A_GRAPH'},
 channels:[{canal_id:'CHAN_A',waba_id:'100001',phone_number_id:'12345678901',active:true},
 {canal_id:'CHAN_A2',waba_id:'100002',phone_number_id:'12345678902',active:true}]};
const appB={...app,app_ref:'APP_B',route_ref:'ROUTE_B',concessionaria_id:'SHOP_B',
 secret_slots:{get_verify_token:'B_VERIFY',post_app_secret:'B_HMAC',graph_access_token:'B_GRAPH'},
 channels:[{canal_id:'CHAN_B',waba_id:'200001',phone_number_id:'98765432101',active:true}]};
const registry:TrustedMetaRegistry={contract_version:'wa-meta-credential-routing.v0.1-proposed',apps:[app,appB]};
const entry=(waba='100001',phone='12345678901',status=false)=>({id:waba,changes:[{field:'messages',value:{
 metadata:{phone_number_id:phone},
 ...(status?{statuses:[{id:'wamid.OUT=',status:'delivered',recipient_id:'5581900000000',timestamp:'1792320001'}]}:
 {messages:[{id:'wamid.IN=',from:'5581900000000',timestamp:'1792320000',type:'text'}]})}}]});
const payload=(items:unknown[]=[entry()])=>new TextEncoder().encode(JSON.stringify({object:'whatsapp_business_account',entry:items}));
async function sign(raw:Uint8Array){const key=await crypto.subtle.importKey('raw',new TextEncoder().encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign']);const b=new Uint8Array(await crypto.subtle.sign('HMAC',key,raw));return 'sha256='+Array.from(b,x=>x.toString(16).padStart(2,'0')).join('');}
const caller={service_ref:'TRUSTED_FAKE_GATEWAY',active:true,allowed_route_refs:['ROUTE_A']};
async function fixture(raw=payload(),batch='BATCH_1') {
 let current=registry;
 let auth={...caller};
 const store=new FakeProtectedPayloads();
 assert.equal(store.putFixture('PRIVATE_PAYLOAD',raw),true);
 const request={raw_body:raw,route:{route_ref:'ROUTE_A',expected_revision:4},signature_header:await sign(raw)};
 const inspected=await prepareS0HandoffFixture({request,batch_ref:batch,protected_payload_ref:'PRIVATE_PAYLOAD'},{
   currentRegistry:()=>registry,resolveSecret:(n:string)=>n==='A_HMAC'?secret:undefined,nowMs:()=>at});
 assert.equal(inspected.ok,true);
 if(!inspected.ok)throw Error('invalid setup');
 const ports:FakeS0IngressPorts={trustedCaller:()=>auth,trustedRegistry:()=>current,nowMs:()=>at,payloads:store};
 const gateway=new FakePrivilegedS0Ingress();
 return {candidate:inspected.candidate,raw,ports,gateway,store,setRegistry:(r:TrustedMetaRegistry)=>{current=r;},setCaller:(x:typeof caller)=>{auth=x;}};
}
const tryIt=(f:Awaited<ReturnType<typeof fixture>>,candidate=f.candidate,raw=f.raw,opts:Parameters<FakePrivilegedS0Ingress['admit']>[2]={})=>f.gateway.admit({candidate,raw_body:raw},f.ports,opts);
test('GATE-01 privileged fake source + stored exact bytes + valid scopes produces LAB only',async()=>{const f=await fixture();const r=await tryIt(f);assert.equal(r.decision,'LAB_ACCEPTED');assert.equal(r.simulated_occurrences,1);assert.equal(r.ack_allowed,false);assert.equal(r.production_authorized,false);});
test('GATE-02 identical internal batch replays without duplicate occurrence',async()=>{const f=await fixture();await tryIt(f);const r=await tryIt(f);assert.equal(r.decision,'LAB_REPLAY');assert.equal(f.gateway.occurrenceCount,1);});
test('GATE-03 batch ref conflict rejects divergent identity',async()=>{const f=await fixture();await tryIt(f);const altered={...f.candidate,scope_sha256:'b'.repeat(64)};const r=await tryIt(f,altered);assert.equal(r.decision,'DENIED');assert.equal(f.gateway.batchCount,1);});
test('GATE-04 nonprivileged fake caller cannot cause commit',async()=>{const f=await fixture();f.setCaller({...caller,active:false});assert.equal((await tryIt(f)).reason,'UNTRUSTED_CALLER');assert.equal(f.gateway.batchCount,0);});
test('GATE-05 wrong route permission cannot claim App A scope',async()=>{const f=await fixture();f.setCaller({...caller,allowed_route_refs:['ROUTE_B']});assert.equal((await tryIt(f)).decision,'DENIED');});
test('GATE-06 caller identity from candidate is ignored and extra fields rejected',async()=>{const f=await fixture();const candidate={...f.candidate,service_ref:'TRUSTED_FAKE_GATEWAY'} as S0HandoffCandidate;assert.equal((await tryIt(f,candidate)).reason,'MALFORMED');});
test('GATE-07 revised App is denied before accepting',async()=>{const f=await fixture();f.setRegistry({...registry,apps:[{...app,revision:5},appB]});assert.equal((await tryIt(f)).decision,'DENIED');});
test('GATE-08 App revocation during await is denied at final gate',async()=>{const f=await fixture();const r=await tryIt(f,f.candidate,f.raw,{beforeCommit:()=>f.setRegistry({...registry,apps:[{...app,active:false},appB]})});assert.equal(r.reason,'SCOPE_OR_REVISION_INVALID');assert.equal(f.gateway.batchCount,0);});
test('GATE-09 channel revocation during commit also blocks entire batch',async()=>{const f=await fixture(payload([entry(),entry('100002','12345678902',true)]));const r=await tryIt(f,f.candidate,f.raw,{beforeCommit:()=>f.setRegistry({...registry,apps:[{...app,channels:[app.channels[0],{...app.channels[1],active:false}]},appB]})});assert.equal(r.decision,'DENIED');assert.equal(f.gateway.occurrenceCount,0);});
test('GATE-10 tenant change with same route revision is detected by independent S0 map',async()=>{const f=await fixture();f.setRegistry({...registry,apps:[{...app,concessionaria_id:'SHOP_OTHER'},appB]});assert.equal((await tryIt(f)).decision,'DENIED');});
test('GATE-11 channel reassignment with same raw body and same revision is detected',async()=>{const f=await fixture();f.setRegistry({...registry,apps:[{...app,channels:[{...app.channels[0],canal_id:'CHAN_CHANGED'},app.channels[1]]},appB]});assert.equal((await tryIt(f)).decision,'DENIED');});
test('GATE-12 raw bytes differ from protected fixture before any lab commit',async()=>{const f=await fixture();const other=Uint8Array.from(f.raw);other[5]^=1;assert.equal((await tryIt(f,f.candidate,other)).reason,'BODY_NOT_PRESERVED');});
test('GATE-13 body present but candidate digest forged is rejected',async()=>{const f=await fixture();const c={...f.candidate,payload_sha256:'a'.repeat(64)};assert.equal((await tryIt(f,c)).reason,'BODY_NOT_PRESERVED');});
test('GATE-14 digest over scope is independently recalculated and mismatch is rejected',async()=>{const f=await fixture();const c={...f.candidate,scope_sha256:'a'.repeat(64)};assert.equal((await tryIt(f,c)).reason,'SCOPE_DIGEST_MISMATCH');});
test('GATE-15 forged metadata with accessor is rejected without triggering getter',async()=>{const f=await fixture();let called=0;const c=Object.assign({},f.candidate);Object.defineProperty(c,'batch_ref',{enumerable:true,get(){called++;return 'BATCH_1';}});assert.equal((await tryIt(f,c)).reason,'MALFORMED');assert.equal(called,0);});
test('GATE-16 extra customer data or secret fields are not copied to journal',async()=>{const f=await fixture();const bad={...f.candidate,raw_customer_phone:'5581900000000'} as S0HandoffCandidate;assert.equal((await tryIt(f,bad)).decision,'DENIED');assert.equal(f.gateway.occurrenceCount,0);});
test('GATE-17 fake write failure produces zero records; retry may succeed',async()=>{const f=await fixture();const r=await tryIt(f,f.candidate,f.raw,{failWrite:true});assert.equal(r.reason,'FAKE_WRITE_FAILED');assert.equal(f.gateway.batchCount,0);assert.equal((await tryIt(f)).decision,'LAB_ACCEPTED');});
test('GATE-18 callback/status same wamid in separate batches can each be admitted',async()=>{const f=await fixture(payload([entry('100001','12345678901',true)]));const first=await tryIt(f);assert.equal(first.decision,'LAB_ACCEPTED');const next={...f.candidate,batch_ref:'BATCH_NEW'}; // scope checksum needs rebuild from new authenticated handoff
 const body=f.raw;const second=await prepareS0HandoffFixture({request:{raw_body:body,route:{route_ref:'ROUTE_A',expected_revision:4},signature_header:await sign(body)},batch_ref:'BATCH_NEW',protected_payload_ref:'PRIVATE_PAYLOAD'},{currentRegistry:()=>registry,resolveSecret:(n:string)=>n==='A_HMAC'?secret:undefined,nowMs:()=>at});assert.equal(second.ok,true);if(second.ok)assert.equal((await tryIt(f,second.candidate)).decision,'LAB_ACCEPTED');assert.equal(f.gateway.occurrenceCount,2);void next;});
test('GATE-19 result carries no HTTP code, COMMITTED receipt, secret or PII',async()=>{const f=await fixture();const r=await tryIt(f);const json=JSON.stringify(r);for(const marker of ['http_status','commit_state','5581900000000','FAKE_APP_HMAC_KEY','ack_allowed":true'])assert.equal(json.includes(marker),false);});
test('GATE-20 batch replay is still denied after service revocation',async()=>{const f=await fixture();await tryIt(f);f.setCaller({...caller,active:false});assert.equal((await tryIt(f)).decision,'DENIED');assert.equal(f.gateway.occurrenceCount,1);});
