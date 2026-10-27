/** Unsupported-message callback fixtures: all synthetic and offline. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {inspectSignedMetaUnsupportedMessages as inspect}
 from './cloud-unsupported-inbound-handoff.ts';

const SECRET='UNSUPPORTED_OFFLINE_ONLY_NO_META_CREDENTIAL';
const ROUTE={waba_id:'123456789012',phone_number_id:'987654321098',revision:4};
const STAMP='1761000000';
const diagnostic=()=>({
 code:131051,title:'Unsupported message type',
 message:'Not supported',
 error_data:{details:'Cannot read the message'},
});
const unsupported=(id='wamid.IN_UNSUPPORTED')=>({
 from:'5581888800000',id,timestamp:STAMP,type:'unsupported',
 errors:[diagnostic()],unsupported:{type:'edit'},
});
const regular=()=>({
 from:'5581888800001',id:'wamid.TEXT',timestamp:STAMP,
 type:'text',text:{body:'Inert text'},
});
const reaction=()=>({
 from:'5581888800002',id:'wamid.REACT',timestamp:STAMP,
 type:'reaction',reaction:{message_id:'wamid.TARGET',emoji:'👍'},
});
const status=(ts=STAMP)=>({
 id:'wamid.SENT',recipient_id:'5581888800000',status:'failed',timestamp:ts,
});
const root=(messages:unknown[]=[unsupported()],statuses:unknown[]=[])=>({
 object:'whatsapp_business_account',entry:[{id:ROUTE.waba_id,
 changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:ROUTE.phone_number_id},
  messages,statuses,
 }}]}],
});
const bytes=(v:unknown)=>Buffer.from(JSON.stringify(v),'utf8');
const sign=(b:Uint8Array)=>
 'sha256='+createHmac('sha256',SECRET).update(b).digest('hex');
const run=(value:unknown=root(),route=ROUTE)=>{
 const b=bytes(value);return inspect(b,sign(b),SECRET,route);
};
function safe(r:Awaited<ReturnType<typeof inspect>>){
 assert.equal(Object.isFrozen(r),true);
 for(const key of [
  'ack_allowed','send_authorized','s0_write_authorized','retry_external',
  'production_authorized','delivery_confirmed',
  'case_transition_authorized','commercial_effect_authorized',
  'consent_verified','deduplicated','provider_error_action_authorized',
  'inbound_content_recovered','auto_reply_authorized',
  'definitive_failure_count_increment',
 ] as const)assert.equal(r[key],false,key);
}
function valid(r:Awaited<ReturnType<typeof inspect>>){
 safe(r);assert.equal(r.decision,'SIGNED_UNSUPPORTED_NOT_DURABLE');
 if(r.decision!=='SIGNED_UNSUPPORTED_NOT_DURABLE')throw Error('denied');
 return r.observations;
}
function denied(r:Awaited<ReturnType<typeof inspect>>){
 safe(r);assert.equal(r.decision,'DENIED');
 if(r.decision!=='DENIED')throw Error('expected denial');
 assert.equal(r.raw_sha256,null);assert.deepEqual(r.observations,[]);
 return r.reason;
}

test('UNSUPPORTED-01 signed 131051 exposes only numeric diagnostics',async()=>{
 const r=await run(), items=valid(r);
 assert.equal(items.length,1);
 assert.equal(items[0].kind,'incoming_unsupported_message');
 assert.equal(items[0].provider_message_id,'wamid.IN_UNSUPPORTED');
 assert.equal(items[0].participant_identifier,'5581888800000');
 assert.equal(items[0].provider_subtype_untrusted,'edit');
 assert.deepEqual(items[0].errors,[{code:131051,error_subcode:null}]);
 assert.equal(items[0].position.item_index,0);
 assert.ok(Object.isFrozen(items[0]));
 assert.ok(Object.isFrozen(items[0].errors));
 assert.ok(Object.isFrozen(items[0].errors[0]));
 assert.match(r.raw_sha256!,/^[a-f0-9]{64}$/);
 assert.equal(JSON.stringify(items).includes('Cannot read'),false);
 assert.equal(JSON.stringify(items).includes('Not supported'),false);
});
test('UNSUPPORTED-02 absent optional fields preserve null subtype/subcode',async()=>{
 const m=unsupported();
 delete (m as any).unsupported;
 m.errors=[{code:131051}] as any;
 const v=valid(await run(root([m])));
 assert.equal(v[0].provider_subtype_untrusted,null);
 assert.deepEqual(v[0].errors,[{code:131051,error_subcode:null}]);
});
test('UNSUPPORTED-03 optional positive subcode and multiple codes are inert',async()=>{
 const m=unsupported();
 m.errors=[{code:131051,error_subcode:17},{code:131000}] as any;
 const v=valid(await run(root([m])));
 assert.deepEqual(v[0].errors,[
  {code:131051,error_subcode:17},
  {code:131000,error_subcode:null},
 ]);
});
test('UNSUPPORTED-04 mixed statuses, messages and callbacks retain position',async()=>{
 const r=await run(root([
  regular(),unsupported(),reaction(),unsupported('wamid.SECOND'),
 ],[status()]));
 const v=valid(r);
 assert.deepEqual(v.map(x=>x.position.item_index),[1,3]);
 assert.deepEqual(v.map(x=>x.provider_message_id),
  ['wamid.IN_UNSUPPORTED','wamid.SECOND']);
 assert.equal(r.delivery_confirmed,false);
});
test('UNSUPPORTED-05 non-unsupported signed event has no diagnoses',async()=>{
 const r=await run(root([regular(),reaction()],[status()]));
 assert.deepEqual(valid(r),[]);
 assert.equal(r.ack_allowed,false);
});
test('UNSUPPORTED-06 missing, empty, oversized and nonarray errors deny all',async()=>{
 for(const value of [undefined,null,[],{},[diagnostic(),...Array(8).fill(diagnostic())]]){
  const m=unsupported();
  if(value===undefined)delete (m as any).errors;
  else (m as any).errors=value;
  assert.equal(denied(await run(root([regular(),unsupported(),m]))),
   'UNSUPPORTED_ERROR_SHAPE');
 }
});
test('UNSUPPORTED-07 invalid codes and subcodes fail without partial output',async()=>{
 for(const value of [0,-1,1.5,'131051',null,Number.MAX_SAFE_INTEGER+1]){
  const m=unsupported();m.errors=[{code:value}] as any;
  assert.equal(denied(await run(root([unsupported(),m]))),
   'UNSUPPORTED_ERROR_SHAPE');
 }
 for(const value of [0,-5,1.3,null,'10']){
  const m=unsupported();m.errors=[{code:131051,error_subcode:value}] as any;
  assert.equal(denied(await run(root([m]))),'UNSUPPORTED_ERROR_SHAPE');
 }
});
test('UNSUPPORTED-08 unexpected error fields or spoofed permissions denied',async()=>{
 for(const extra of [
  {commercial_effect_authorized:true},{send_authorized:true},
  {transport_status:200},{access_token:'SECRET'},
 ]){
  const m=unsupported();Object.assign(m.errors[0],extra);
  assert.equal(denied(await run(root([m]))),'UNSUPPORTED_ERROR_SHAPE');
 }
});
test('UNSUPPORTED-09 invalid freeform error diagnostics denied, never returned',async()=>{
 for(const bad of [null,11,'X'.repeat(513),'bad\ncontrol','\uD800']){
  const m=unsupported();(m.errors[0] as any).title=bad;
  assert.equal(denied(await run(root([m]))),'UNSUPPORTED_ERROR_SHAPE');
 }
});
test('UNSUPPORTED-10 nested error_data accepts Meta shape but blocks extras',async()=>{
 const m=unsupported();(m.errors[0] as any).error_data={
  details:'Not available',messaging_product:'whatsapp',
 };
 assert.equal(valid(await run(root([m])))[0].errors[0].code,131051);
 for(const data of [null,[],{details:'ok',authorization:true},
   {messaging_product:'instagram'},{details:2}]){
  const q=unsupported();(q.errors[0] as any).error_data=data;
  assert.equal(denied(await run(root([q]))),'UNSUPPORTED_ERROR_SHAPE');
 }
});
test('UNSUPPORTED-11 unsupported subtype must be structurally safe',async()=>{
 for(const bad of [null,{}, {type:'bad type'}, {type:''},
  {type:2},{type:'edit',approve:true},{type:'x'.repeat(65)}]){
  const m=unsupported();(m as any).unsupported=bad;
  assert.equal(denied(await run(root([m]))),'UNSUPPORTED_ERROR_SHAPE');
 }
});
test('UNSUPPORTED-12 incorrect HMAC, missing HMAC and bad secret reveal no error',async()=>{
 const b=bytes(root());
 for(const r of await Promise.all([
  inspect(b,'sha256='+'0'.repeat(64),SECRET,ROUTE),
  inspect(b,null,SECRET,ROUTE),
  inspect(b,sign(b),'BAD_SECRET',ROUTE),
  inspect(b,sign(b),'',ROUTE),
 ]))assert.equal(denied(r),'VERIFICATION_DENIED');
});
test('UNSUPPORTED-13 route mismatch denies whole signed callback batch',async()=>{
 const b=bytes(root());
 const [a,c]=await Promise.all([
  inspect(b,sign(b),SECRET,{...ROUTE,waba_id:'999999999999'}),
  inspect(b,sign(b),SECRET,{...ROUTE,phone_number_id:'999999999999'}),
 ]);
 assert.equal(denied(a),'VERIFICATION_DENIED');
 assert.equal(denied(c),'VERIFICATION_DENIED');
 const mixed=root();
 mixed.entry.push({id:'999999999999',changes:[{field:'messages',value:{
  messaging_product:'whatsapp',
  metadata:{phone_number_id:ROUTE.phone_number_id},
  messages:[unsupported('wamid.CROSS')],statuses:[],
 }}]});
 assert.equal(denied(await run(mixed)),'VERIFICATION_DENIED');
});
test('UNSUPPORTED-14 invalid sibling status blocks entire batch',async()=>{
 assert.equal(denied(await run(root([unsupported()],[status('bad')]))),
  'VERIFICATION_DENIED');
});
test('UNSUPPORTED-15 duplicate callback remains duplicated pending S0 dedupe',async()=>{
 const m=unsupported();
 const r=await run(root([m,{...m}]));
 assert.deepEqual(valid(r).map(x=>x.position.item_index),[0,1]);
 assert.equal(r.deduplicated,false);
});
test('UNSUPPORTED-16 byte mutation and limits fail or preserve signed snapshot',async()=>{
 const b=bytes(root([unsupported()]));
 const started=inspect(b,sign(b),SECRET,ROUTE);b.fill(0);
 assert.equal(valid(await started)[0].errors[0].code,131051);
 const original=bytes(root([unsupported(),unsupported('wamid.U2')]));
 assert.equal(denied(await inspect(original,sign(original),SECRET,ROUTE,
  {maxBodyBytes:original.length-1})),'VERIFICATION_DENIED');
 assert.equal(denied(await inspect(original,sign(original),SECRET,ROUTE,
  {maxEvents:1})),'VERIFICATION_DENIED');
 const invalid=Uint8Array.from([0xff,0xfe]);
 assert.equal(denied(await inspect(invalid,sign(invalid),SECRET,ROUTE)),
  'VERIFICATION_DENIED');
});
