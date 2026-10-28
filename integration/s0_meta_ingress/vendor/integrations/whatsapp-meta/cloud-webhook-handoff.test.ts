/** Offline contract tests: no Graph calls, HTTP server, DB, S0 or token. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac,createHash} from 'node:crypto';
import {inspectCloudWebhookForHandoff as inspect} from './cloud-webhook-handoff.ts';

const SECRET='offline-test-app-secret-only';
const ROUTE=Object.freeze({waba_id:'22346000002',phone_number_id:'32346000002',revision:7});
const STAMP='1761000000';
const original=()=>({object:'whatsapp_business_account',
 entry:[{id:ROUTE.waba_id,changes:[{field:'messages',value:{
  messaging_product:'whatsapp',
  metadata:{display_phone_number:'558199998888',phone_number_id:ROUTE.phone_number_id},
  statuses:[
   {id:'wamid.DEMO',recipient_id:'5581999990000',status:'sent',timestamp:STAMP,
    conversation:{id:'synthetic-conversation',origin:{type:'service'}},
    pricing:{billable:false,category:'service'}},
   {id:'wamid.DEMO',recipient_id:'5581999990000',status:'delivered',timestamp:STAMP,
    errors:[]}
  ],
  messages:[{id:'wamid.INBOUND',from:'558188880000',timestamp:STAMP,
    type:'text',text:{body:'private-not-exposed'}}],
 }}]}]});
const bytes=(v:unknown)=>Buffer.from(JSON.stringify(v),'utf8');
const sign=(b:Uint8Array)=>'sha256='+createHmac('sha256',SECRET).update(b).digest('hex');
const call=(obj:unknown,route=ROUTE,limits?:{maxBodyBytes?:number;maxEvents?:number})=>{
 const b=bytes(obj);
 return inspect(b,sign(b),SECRET,route,limits);
};
function noAuthority(x:Awaited<ReturnType<typeof inspect>>){
 for(const name of ['ack_allowed','send_authorized','retry_external',
  's0_write_authorized','production_authorized','delivery_confirmed',
  'case_transition_authorized'] as const)assert.equal(x[name],false,name);
}
test('valid signed batch preserves statuses and inbound separately without ACK',async()=>{
 const r=await call(original());
 assert.equal(r.outcome,'AUTHENTICATED_NOT_DURABLE');
 if(r.outcome!=='AUTHENTICATED_NOT_DURABLE')throw Error('denied');
 assert.equal(r.route_revision,7);
 assert.equal(r.observations.length,3);
 assert.deepEqual(r.observations.map(x=>x.kind),
  ['inbound_message','status_callback','status_callback']);
 assert.deepEqual(r.observations.map(x=>x.provider_kind),['text','sent','delivered']);
 assert.deepEqual(r.observations.map(x=>x.position.array_kind),
  ['messages','statuses','statuses']);
 assert.equal(r.observations[0].provider_timestamp,new Date(Number(STAMP)*1000).toISOString());
 noAuthority(r);
 assert.ok(Object.isFrozen(r));
 assert.ok(Object.isFrozen(r.observations));
 assert.ok(Object.isFrozen(r.observations[0].position));
});
test('forensic hash uses exact bytes, even if key order differs',async()=>{
 const root=original(),a=bytes(root);
 const signed=await inspect(a,sign(a),SECRET,ROUTE);
 assert.equal(signed.outcome,'AUTHENTICATED_NOT_DURABLE');
 if(signed.outcome!=='AUTHENTICATED_NOT_DURABLE')throw Error();
 assert.equal(signed.raw_sha256,createHash('sha256').update(a).digest('hex'));
 const reordered=JSON.parse(JSON.stringify(root));
 const status=reordered.entry[0].changes[0].value.statuses[0];
 reordered.entry[0].changes[0].value.statuses[0]={
  timestamp:status.timestamp,id:status.id,status:status.status,
  recipient_id:status.recipient_id,conversation:status.conversation,pricing:status.pricing};
 const other=await call(reordered);
 assert.equal(other.outcome,'AUTHENTICATED_NOT_DURABLE');
 if(other.outcome!=='AUTHENTICATED_NOT_DURABLE')throw Error();
 assert.notEqual(other.raw_sha256,signed.raw_sha256);
 assert.deepEqual(other.observations.map(x=>x.candidate_key),
  signed.observations.map(x=>x.candidate_key));
});
test('one malformed scope rejects ALL events, no partial handoff',async()=>{
 const v=original();
 const statusOnly={field:'messages',value:{
  metadata:{phone_number_id:'99999000002'},statuses:[
  {id:'wamid.CROSS',status:'read',recipient_id:'55818880000',timestamp:STAMP}]
 }};
 v.entry[0].changes.push(statusOnly as never);
 const r=await call(v);
 assert.equal(r.outcome,'DENIED');
 if(r.outcome!=='DENIED')throw Error();
 assert.equal(r.reason,'SCOPE_MISMATCH');
 assert.equal(r.observations.length,0);
 noAuthority(r);
});
test('unknown provider status is quarantined, not treated as business state',async()=>{
 const v=original();v.entry[0].changes[0].value.statuses[1].status='extremely_custom';
 const r=await call(v);
 assert.equal(r.outcome,'DENIED');
 if(r.outcome!=='DENIED')throw Error();
 assert.equal(r.reason,'UNSUPPORTED_STATUS');
 noAuthority(r);
});
test('bad signature refuses before any candidate plan',async()=>{
 const b=bytes(original());
 const r=await inspect(b,'sha256='+'0'.repeat(64),SECRET,ROUTE);
 assert.equal(r.outcome,'DENIED');
 if(r.outcome!=='DENIED')throw Error();
 assert.equal(r.reason,'INVALID_SIGNATURE');
 assert.equal(r.raw_sha256,null);
 noAuthority(r);
});
test('validly signed invalid JSON refuses',async()=>{
 const b=Buffer.from('{"object":');
 const r=await inspect(b,sign(b),SECRET,ROUTE);
 assert.equal(r.outcome,'DENIED');
 if(r.outcome!=='DENIED')throw Error();
 assert.equal(r.reason,'INVALID_JSON');
 noAuthority(r);
});
test('validly signed invalid UTF8 refuses',async()=>{
 const b=Buffer.from([0x7b,0x22,0x61,0x22,0x3a,0xff,0x7d]);
 const r=await inspect(b,sign(b),SECRET,ROUTE);
 assert.equal(r.outcome,'DENIED');
 if(r.outcome!=='DENIED')throw Error();
 assert.equal(r.reason,'INVALID_UTF8');
});
test('deny invalid trusted route, not trusting body-scoped routing',async()=>{
 const r=await call(original(),{...ROUTE,revision:0});
 assert.equal(r.outcome,'DENIED');
 if(r.outcome!=='DENIED')throw Error();
 assert.equal(r.reason,'INVALID_TRUSTED_SCOPE');
 const v=original();v.entry[0].id='99999999999';
 const denied=await call(v);
 assert.equal(denied.outcome,'DENIED');
 if(denied.outcome!=='DENIED')throw Error();
 assert.equal(denied.reason,'SCOPE_MISMATCH');
});
test('duplicate callbacks remain separate observations for durable dedupe',async()=>{
 const v=original();v.entry[0].changes[0].value.statuses.push(
  {...v.entry[0].changes[0].value.statuses[0]});
 const r=await call(v);
 assert.equal(r.outcome,'AUTHENTICATED_NOT_DURABLE');
 if(r.outcome!=='AUTHENTICATED_NOT_DURABLE')throw Error();
 assert.equal(r.observations.length,4);
 assert.equal(r.observations[1].candidate_key,r.observations[3].candidate_key);
 assert.notDeepEqual(r.observations[1].position,r.observations[3].position);
});
test('max events caps input before downstream binding decisions',async()=>{
 const r=await call(original(),ROUTE,{maxEvents:2});
 assert.equal(r.outcome,'DENIED');
 if(r.outcome!=='DENIED')throw Error();
 assert.equal(r.reason,'TOO_MANY_EVENTS');
 noAuthority(r);
});
test('size cap refuses HMAC-valid oversized payload',async()=>{
 const b=bytes(original());
 const r=await inspect(b,sign(b),SECRET,ROUTE,{maxBodyBytes:b.length-1});
 assert.equal(r.outcome,'DENIED');
 if(r.outcome!=='DENIED')throw Error();
 assert.equal(r.reason,'BODY_TOO_LARGE');
});
test('statuses and inbound are distinct; no Graph response interpretation',async()=>{
 const v=original();
 v.entry[0].changes[0].value.messages=[{
  id:'wamid.NEW',from:'558177770000',timestamp:STAMP,type:'image',
  image:{id:'offline-id',mime_type:'image/jpeg'}}];
 const r=await call(v);
 assert.equal(r.outcome,'AUTHENTICATED_NOT_DURABLE');
 if(r.outcome!=='AUTHENTICATED_NOT_DURABLE')throw Error();
 assert.equal(r.observations[0].kind,'inbound_message');
 assert.equal(r.observations[0].provider_kind,'image');
 assert.equal(r.observations[1].kind,'status_callback');
 noAuthority(r);
});
