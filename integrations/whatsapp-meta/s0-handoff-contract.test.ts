import {test} from 'node:test';
import assert from 'node:assert/strict';
import {prepareS0HandoffFixture,reviewS0ReceiptFixture,type S0HandoffCandidate} from './s0-handoff-contract.ts';
import type {TrustedRoutingPorts} from './routed-webhook.ts';
import type {TrustedMetaRegistry} from './credential-routing.ts';
import {createHash} from 'node:crypto';
const when=1792320000000;
const keyA='FAKE_SECRET_PER_APP_A_ONLY';
const keyB='FAKE_SECRET_PER_APP_B_ONLY';
const a={app_ref:'APP_A',route_ref:'ROUTE_A',concessionaria_id:'SHOP_A',active:true,
  revision:1,valid_from_ms:when-1000,valid_until_ms:when+1000,
  secret_slots:{get_verify_token:'A_GET',post_app_secret:'A_POST',graph_access_token:'A_GRAPH'},
  channels:[{canal_id:'CH_A1',waba_id:'WABA_A',phone_number_id:'12345678901',active:true},
    {canal_id:'CH_A2',waba_id:'WABA_A2',phone_number_id:'12345678902',active:true}]};
const b={...a,app_ref:'APP_B',route_ref:'ROUTE_B',concessionaria_id:'SHOP_B',
  secret_slots:{get_verify_token:'B_GET',post_app_secret:'B_POST',graph_access_token:'B_GRAPH'},
  channels:[{canal_id:'CH_B',waba_id:'WABA_B',phone_number_id:'99999999999',active:true}]};
const registry:TrustedMetaRegistry={contract_version:'wa-meta-credential-routing.v0.1-proposed',apps:[a,b]};
const ports=(reg:TrustedMetaRegistry=registry):TrustedRoutingPorts=>({
  currentRegistry:()=>reg,resolveSecret:s=>s==='A_POST'?keyA:s==='B_POST'?keyB:undefined,nowMs:()=>when});
const entry=(waba='WABA_A',phone='12345678901',messages=true,statuses=false)=>({id:waba,changes:[{
  field:'messages',value:{metadata:{phone_number_id:phone},
  ...(messages?{messages:[{id:'wamid.IN_A=',from:'5581900000000',type:'text',timestamp:'1792320000'}]}:{}),
  ...(statuses?{statuses:[{id:'wamid.OUT_A=',recipient_id:'5581900000000',status:'delivered',timestamp:'1792320001'}]}:{})
  }}]});
const raw = (items:unknown[]=[entry()])=>new TextEncoder().encode(JSON.stringify({object:'whatsapp_business_account',entry:items}));
const sign=async(raw:Uint8Array,secret=keyA)=>{
  const k=await crypto.subtle.importKey('raw',new TextEncoder().encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign']);
  const out=new Uint8Array(await crypto.subtle.sign('HMAC',k,raw));
  return 'sha256='+Array.from(out,b=>b.toString(16).padStart(2,'0')).join('');
};
const setup=async(opts?:{raw?:Uint8Array,appSecret?:string,route?:string,batch?:string,payload?:string})=>{
  const body=opts?.raw??raw();
  return {request:{route:{route_ref:opts?.route??'ROUTE_A',expected_revision:1},
    raw_body:body,signature_header:await sign(body,opts?.appSecret)},
    batch_ref:opts?.batch??'BATCH_001',protected_payload_ref:opts?.payload??'PAYLOAD_001'};
};
const receive=async(opts?:Parameters<typeof setup>[0], reg=registry)=>prepareS0HandoffFixture(await setup(opts),ports(reg));
const receipt=(candidate:S0HandoffCandidate,parts:Record<string,unknown>={})=>({
  contract_version:'meta-s0-receipt.v0.1-proposed',batch_ref:candidate.batch_ref,
  app_ref:candidate.app_ref,protected_payload_ref:candidate.protected_payload_ref,
  payload_sha256:candidate.payload_sha256,total:candidate.event_count,
  accepted:candidate.event_count,duplicates:0,quarantined:0,
  outcome:'ACCEPTED_DURABLE',commit_state:'COMMITTED',...parts
});
const candidate=async()=>{const r=await receive();assert.equal(r.ok,true);if(!r.ok)throw Error('bad fixture');return r.candidate};
test('S0C-01 HMAC-checked fake App route produces minimal S0 handoff and never ACK',async()=>{
  const r=await receive();assert.equal(r.ok,true);
  if(!r.ok)return;assert.equal(r.ack_allowed,false);assert.equal(r.candidate.ack_allowed,false);
  assert.equal(r.candidate.production_authorized,false);assert.equal(r.candidate.event_count,1);
  assert.equal(r.candidate.contract_version,'meta-s0-handoff.v0.1-proposed');
});
test('S0C-02 digest bound to original raw POST bytes, but payload remains out of band',async()=>{
  const r=await receive();if(!r.ok)throw Error('fixture');
  assert.equal(r.candidate.payload_sha256,createHash('sha256').update(raw()).digest('hex'));
  assert.equal('raw_body' in r.candidate,false);
  assert.equal('payload' in r.candidate,false);
});
test('S0C-03 no customer participant, raw message, HMAC, token in handoff metadata',async()=>{
  const r=await receive();if(!r.ok)throw Error('fixture');const json=JSON.stringify(r.candidate);
  for(const x of ['5581900000000','FAKE_SECRET','signature_header','participant_identifier','access_token','raw_body'])
    assert.equal(json.includes(x),false);
});
test('S0C-04 one batch with messages[0] and statuses[0] yields two distinct positions',async()=>{
  const r=await receive({raw:raw([entry('WABA_A','12345678901',true,true)])});
  assert.equal(r.ok,true);if(!r.ok)return;
  assert.equal(r.candidate.event_count,2);
  assert.deepEqual(r.candidate.occurrences.map(x=>x.position.array_kind),['messages','statuses']);
  assert.equal(r.candidate.occurrences[1].event_kind,'status_callback');
});
test('S0C-05 multiple WABAs within one App retain their individual channel IDs',async()=>{
  const r=await receive({raw:raw([entry(),entry('WABA_A2','12345678902')])});
  assert.equal(r.ok,true);if(r.ok)assert.deepEqual(r.candidate.occurrences.map(x=>x.canal_id),['CH_A1','CH_A2']);
});
test('S0C-06 cross App entry invalidates full POST, never partial handoff',async()=>{
  const r=await receive({raw:raw([entry(),entry('WABA_B','99999999999')])});
  assert.equal(r.ok,false);if(!r.ok)assert.equal(r.reason,'HMAC_OR_ROUTE_DENIED');
});
test('S0C-07 forged App B signature cannot pass App A route',async()=>{
  const r=await receive({appSecret:keyB});assert.equal(r.ok,false);
});
test('S0C-08 unknown route and revoked App cannot produce handoff',async()=>{
  assert.equal((await receive({route:'UNKNOWN'})).ok,false);
  assert.equal((await receive(undefined,{...registry,apps:[{...a,active:false},b]})).ok,false);
});
test('S0C-09 missing fake internal batch ref or protected payload ref is denied',async()=>{
  assert.equal((await receive({batch:'../bad'})).ok,false);
  assert.equal((await receive({payload:''})).ok,false);
});
test('S0C-10 tampered body after signature creation is denied',async()=>{
  const inp=await setup(),old=inp.request.raw_body;
  inp.request.raw_body=Uint8Array.from(old);inp.request.raw_body[3]^=1;
  assert.equal((await prepareS0HandoffFixture(inp,ports())).ok,false);
});
test('S0C-11 input body mutation following invocation does not alter digest or metadata',async()=>{
  const inp=await setup(),expected=createHash('sha256').update(inp.request.raw_body).digest('hex');
  const pending=prepareS0HandoffFixture(inp,ports());inp.request.raw_body.fill(0);
  const out=await pending;assert.equal(out.ok,true);if(out.ok)assert.equal(out.candidate.payload_sha256,expected);
});
test('S0C-12 candidate has no S0 occurrence_ref or durable receipt',async()=>{
  const c=await candidate();assert.equal('occurrence_ref' in c.occurrences[0],false);
  assert.equal('commit_state' in c,false);assert.equal('http_status' in c,false);
});
test('S0C-13 padded technical wamid preserves provider correlation',async()=>{
  const c=await candidate();assert.equal(c.occurrences[0].provider_message_id,'wamid.IN_A=');
});
test('S0C-14 forged COMMITTED receipt matching all fields STILL cannot authorize ACK',async()=>{
  const c=await candidate();const r=reviewS0ReceiptFixture(c,receipt(c));
  assert.deepEqual(r,{verdict:'STRUCTURE_MATCHES_BUT_UNVERIFIED',
    reason:'NEEDS_AUTHENTICATED_S0_COMMIT_EVIDENCE',ack_allowed:false,production_authorized:false});
});
test('S0C-15 ALREADY_ACCEPTED structurally matches but never means HTTP 200',async()=>{
  const c=await candidate();const r=reviewS0ReceiptFixture(c,receipt(c,{outcome:'ALREADY_ACCEPTED',accepted:0,duplicates:1}));
  assert.equal(r.verdict,'STRUCTURE_MATCHES_BUT_UNVERIFIED');assert.equal(r.ack_allowed,false);
});
test('S0C-16 fake matching receipt with quarantined item remains pending policy',async()=>{
  const c=await candidate();const r=reviewS0ReceiptFixture(c,receipt(c,{outcome:'QUARANTINED_DURABLE',accepted:0,quarantined:1}));
  assert.equal(r.reason,'QUARANTINE_POLICY_PENDING');
});
test('S0C-17 partial and contradictory counters fail even with string COMMITTED',async()=>{
  const c=await candidate();
  for (const patch of [{total:0},{accepted:0},{accepted:2},{accepted:Number.MAX_SAFE_INTEGER},{duplicates:1},{total:1.5}])
    assert.equal(reviewS0ReceiptFixture(c,receipt(c,patch)).verdict,'DENIED');
});
test('S0C-18 wrong batch, App, payload ref or digest fail receipt binding',async()=>{
  const c=await candidate();for(const patch of [{batch_ref:'FORGED'},{app_ref:'APP_B'},
    {protected_payload_ref:'OTHER'},{payload_sha256:'b'.repeat(64)}])
    assert.equal(reviewS0ReceiptFixture(c,receipt(c,patch)).reason,'ENVELOPE_MISMATCH');
});
test('S0C-19 malformed getter/receipt object fails closed without throwing',async()=>{
  const c=await candidate();const hostile:any=receipt(c);
  Object.defineProperty(hostile,'outcome',{get(){throw Error('SECRET_HIDDEN');},enumerable:true});
  assert.doesNotThrow(()=>reviewS0ReceiptFixture(c,hostile));
  assert.equal(reviewS0ReceiptFixture(c,hostile).verdict,'DENIED');
});
test('S0C-20 extra fields and unsupported schema version fail closed',async()=>{
  const c=await candidate();
  assert.equal(reviewS0ReceiptFixture(c,receipt(c,{raw_token:'DONOTSTORE'})).reason,'INVALID_RECEIPT');
  assert.equal(reviewS0ReceiptFixture(c,receipt(c,{contract_version:'v2'})).reason,'INVALID_RECEIPT');
});
test('S0C-21 receipt cannot be an array, object with custom prototype or a string',async()=>{
  const c=await candidate();for(const r of [[], 'COMMITTED', new Date(), null])
    assert.equal(reviewS0ReceiptFixture(c,r).verdict,'DENIED');
});
test('S0C-22 all candidate failures omit customer IDs and do not leak raw content',async()=>{
  const r=await receive({appSecret:keyB});const json=JSON.stringify(r);
  for(const value of ['5581900000000','FAKE_SECRET','wamid.IN_A=','PAYLOAD_001'])
    assert.equal(json.includes(value),false);
});
