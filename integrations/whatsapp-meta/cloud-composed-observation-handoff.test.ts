/** Composition tests: fictional Meta payloads, no API, S0, HTTP or ACK. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {inspectSignedMetaComposedWebhook as inspect}
 from './cloud-composed-observation-handoff.ts';

const SECRET='SYNTHETIC_COMPOSITION_SECRET_NOT_META';
const ROUTE={waba_id:'123456789012',phone_number_id:'987654321098',revision:4};
const STAMP='1761000000';
const msg=(type:string,id:string,props:Record<string,unknown>={})=>({
 from:'5581888800000',id,timestamp:STAMP,type,...props,
});
const template=()=>msg('button','wamid.BUTTON',{
 button:{payload:'CHOOSE_ONE',text:'Escolher'},
});
const interactive=()=>msg('interactive','wamid.INTERACTIVE',{
 interactive:{type:'button_reply',button_reply:{id:'CHOICE_B',title:'B'}},
 context:{id:'wamid.ORIGIN'},
});
const list=()=>msg('interactive','wamid.LIST',{
 interactive:{type:'list_reply',list_reply:{id:'LIST_1',title:'Produto'}},
});
const reaction=(id='wamid.REACTION')=>msg('reaction',id,{
 reaction:{message_id:'wamid.TARGET',emoji:'❤️'},
});
const media=(kind='image',id='wamid.MEDIA')=>msg(kind,id,{
 [kind]:{id:'99887766554433',mime_type:'image/jpeg',
  sha256:Buffer.alloc(32,17).toString('base64')},
});
const unsupported=(id='wamid.UNSUPPORTED')=>msg('unsupported',id,{
 errors:[{code:131051,title:'Unsupported message type'}],
});
const plain=(id='wamid.PLAIN')=>msg('text',id,{text:{body:'Fictício'}});
const unknown=(id='wamid.UNKNOWN')=>msg('contacts',id,{
 contacts:[{name:{formatted_name:'Inerte'}}],
});
const status=(value='sent',id='wamid.SENT')=>({
 id,recipient_id:'5581888800000',status:value,timestamp:STAMP,
});
const failed=(id='wamid.FAILED')=>({
 ...status('failed',id),
 errors:[{code:131026,title:'Message undeliverable',
  error_data:{details:'PII_HIDDEN'}}],
});
const webhook=(messages:unknown[]=[template()],statuses:unknown[]=[])=>({
 object:'whatsapp_business_account',entry:[{id:ROUTE.waba_id,
 changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:ROUTE.phone_number_id},
  messages,statuses,
 }}]}],
});
const bytes=(v:unknown)=>Buffer.from(JSON.stringify(v),'utf8');
const sign=(b:Uint8Array)=>
 'sha256='+createHmac('sha256',SECRET).update(b).digest('hex');
const run=(v:unknown=webhook(),route=ROUTE)=>{
 const b=bytes(v);return inspect(b,sign(b),SECRET,route);
};
function safe(r:Awaited<ReturnType<typeof inspect>>){
 assert.ok(Object.isFrozen(r));
 for(const key of [
  'ack_allowed','send_authorized','s0_write_authorized','retry_external',
  'production_authorized','delivery_confirmed','case_transition_authorized',
  'commercial_effect_authorized','consent_verified','deduplicated',
  'exactly_once_guaranteed','provider_failure_effect_confirmed',
  'definitive_failure_count_increment','automatic_retry_authorized',
 ] as const)assert.equal(r[key],false,key);
}
function accepted(r:Awaited<ReturnType<typeof inspect>>){
 safe(r);assert.equal(r.decision,'SIGNED_COMPOSED_NOT_DURABLE');
 if(r.decision!=='SIGNED_COMPOSED_NOT_DURABLE')throw Error('expected signed');
 return r.occurrences;
}
function denied(r:Awaited<ReturnType<typeof inspect>>){
 safe(r);assert.equal(r.decision,'DENIED');
 if(r.decision!=='DENIED')throw Error('expected denied');
 assert.deepEqual(r.occurrences,[]);
 assert.equal(r.raw_sha256,null);
 return r.reason;
}

test('COMPOSE-01 one slot for every heterogeneous callback in original order',async()=>{
 const messages=[plain(),template(),interactive(),list(),reaction(),media(),
  unsupported(),unknown()];
 const statuses=[status('sent'),failed(),status('delivered','wamid.DELIVERED')];
 const r=await run(webhook(messages,statuses));
 const events=accepted(r);
 assert.deepEqual(events.map(x=>x.kind),[
  'uninterpreted_inbound','template_quick_reply',
  'interactive_button_reply','interactive_list_reply','incoming_reaction',
  'inbound_media_metadata','incoming_unsupported_message',
  'uninterpreted_inbound','uninterpreted_status',
  'provider_reported_failed_status_errors','uninterpreted_status',
 ]);
 assert.equal(events.length,11);
 assert.deepEqual(events.map(x=>x.position.item_index),[0,1,2,3,4,5,6,7,0,1,2]);
 assert.equal(events.filter(x=>x.position.array_kind==='statuses').length,3);
 assert.equal(events[3].evidence?.kind,'interactive_list_reply');
 assert.equal(events[9].evidence?.kind,'provider_reported_failed_status_errors');
 assert.equal(r.route_revision,ROUTE.revision);
 assert.match(r.raw_sha256!,/^[a-f0-9]{64}$/);
 assert.ok(Object.isFrozen(events));
 assert.ok(Object.isFrozen(events[0]));
 assert.ok(Object.isFrozen(events[0].position));
});
test('COMPOSE-02 generic text and unknown type are preserved, not discarded',async()=>{
 const v=accepted(await run(webhook([plain(),unknown()])));
 assert.deepEqual(v.map(x=>x.kind),['uninterpreted_inbound','uninterpreted_inbound']);
 assert.ok(v.every(x=>x.evidence===null));
});
test('COMPOSE-03 nonfailure statuses remain observations without delivery claims',async()=>{
 const r=await run(webhook([],[status('sent'),status('delivered'),status('read')]));
 const v=accepted(r);
 assert.deepEqual(v.map(x=>x.kind),Array(3).fill('uninterpreted_status'));
 assert.ok(v.every(x=>x.evidence===null));
 assert.equal(r.delivery_confirmed,false);
});
test('COMPOSE-04 distinct evidence classes retain specialized technical data',async()=>{
 const v=accepted(await run(webhook([list(),reaction(),media('audio'),
  unsupported()],[failed()])));
 assert.equal((v[0].evidence as any).button_value,'LIST_1');
 assert.equal((v[1].evidence as any).target_provider_message_id,'wamid.TARGET');
 assert.equal((v[2].evidence as any).media_id,'99887766554433');
 assert.deepEqual((v[3].evidence as any).errors,
  [{code:131051,error_subcode:null}]);
 assert.deepEqual((v[4].evidence as any).codes,
  [{code:131026,error_subcode:null}]);
 assert.equal(JSON.stringify(v).includes('PII_HIDDEN'),false);
});
test('COMPOSE-05 duplicate provider ID in same batch remains separate occurrence',async()=>{
 const one=reaction();
 const v=accepted(await run(webhook([one,{...one}])));
 assert.equal(v.length,2);
 assert.deepEqual(v.map(x=>x.position.item_index),[0,1]);
 assert.equal(v[0].provider_message_id,v[1].provider_message_id);
});
test('COMPOSE-06 identical sent-message ID across callbacks is not deduped',async()=>{
 const s=failed();
 const v=accepted(await run(webhook([],[s,{...s}])));
 assert.equal(v.length,2);
 assert.deepEqual(v.map(x=>x.position.item_index),[0,1]);
});
test('COMPOSE-07 two changes preserve change indices and independently scoped slots',async()=>{
 const root=webhook([plain()]);
 root.entry[0].changes.push({field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:ROUTE.phone_number_id},
  messages:[reaction()],statuses:[failed()],
 }});
 const v=accepted(await run(root));
 assert.deepEqual(v.map(x=>[x.position.change_index,x.position.array_kind]),
  [[0,'messages'],[1,'messages'],[1,'statuses']]);
});
test('COMPOSE-08 mixed-batch invalid reaction denies all including prior candidates',async()=>{
 const bad=reaction();(bad.reaction as any).emoji=null;
 assert.equal(denied(await run(webhook([template(),bad,media()]))),
  'COMPONENT_DENIED');
});
test('COMPOSE-09 malformed media id rejects entire mixed batch',async()=>{
 const m=media();(m.image as any).id='file:///never-open';
 assert.equal(denied(await run(webhook([list(),m,unsupported()]))),
  'COMPONENT_DENIED');
});
test('COMPOSE-10 malformed selections deny all, including unrelated text',async()=>{
 const b=template();(b.button as any).payload='bad payload';
 assert.equal(denied(await run(webhook([plain(),b]))),'COMPONENT_DENIED');
});
test('COMPOSE-11 unknown interactive variant fails closed rather than silently ignored',async()=>{
 const weird=msg('interactive','wamid.UNEXPECTED',{
  interactive:{type:'catalog_reply',catalog_reply:{id:'x'}},
 });
 assert.equal(denied(await run(webhook([plain(),weird]))),'COMPONENT_DENIED');
});
test('COMPOSE-12 unsupported inbound without valid diagnostic codes denies all',async()=>{
 const m=unsupported();delete (m as any).errors;
 assert.equal(denied(await run(webhook([media(),m]))),'COMPONENT_DENIED');
});
test('COMPOSE-13 failed status without errors or progress status with errors denied',async()=>{
 const f=status('failed');
 assert.equal(denied(await run(webhook([template()],[f]))),'COMPONENT_DENIED');
 const s={...status('delivered'),errors:[{code:131026}]};
 assert.equal(denied(await run(webhook([plain()],[s]))),'COMPONENT_DENIED');
});
test('COMPOSE-14 invalid HMAC or wrong App secret leaks no technical items',async()=>{
 const b=bytes(webhook([template(),reaction()],[failed()]));
 for(const r of await Promise.all([
  inspect(b,null,SECRET,ROUTE),
  inspect(b,'bogus',SECRET,ROUTE),
  inspect(b,'sha256='+'0'.repeat(64),SECRET,ROUTE),
  inspect(b,sign(b),'WRONG_SECRET',ROUTE),
  inspect(b,sign(b),'',ROUTE),
 ]))assert.equal(denied(r),'VERIFICATION_DENIED');
});
test('COMPOSE-15 WABA and phone scope mismatch deny entire batch',async()=>{
 const b=bytes(webhook([reaction()]));
 assert.equal(denied(await inspect(b,sign(b),SECRET,
  {...ROUTE,waba_id:'999999999999'})),'VERIFICATION_DENIED');
 assert.equal(denied(await inspect(b,sign(b),SECRET,
  {...ROUTE,phone_number_id:'999999999999'})),'VERIFICATION_DENIED');
 const w=webhook([plain()]);
 w.entry.push({id:'999999999999',changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:ROUTE.phone_number_id},
  messages:[reaction()],statuses:[],
 }}]});
 assert.equal(denied(await run(w)),'VERIFICATION_DENIED');
});
test('COMPOSE-16 malformed sibling and unknown subscription deny all',async()=>{
 const w=webhook([template()],[failed()]);
 (w.entry[0].changes[0] as any).field='business_capability_update';
 assert.equal(denied(await run(w)),'VERIFICATION_DENIED');
 const a=webhook([plain()],[failed()]);
 a.entry[0].changes[0].value.statuses.push({
  id:'wamid.BAD',recipient_id:'5581888800000',status:'failed',timestamp:'bad',
 });
 assert.equal(denied(await run(a)),'VERIFICATION_DENIED');
});
test('COMPOSE-17 mutation after invocation cannot change the signed snapshot',async()=>{
 const b=bytes(webhook([template(),reaction()],[failed()]));
 const task=inspect(b,sign(b),SECRET,ROUTE);
 b.fill(0);
 const v=accepted(await task);
 assert.equal(v.length,3);
 assert.equal(v[1].kind,'incoming_reaction');
});
test('COMPOSE-18 body size, event limits and invalid UTF-8 reject before candidates',async()=>{
 const b=bytes(webhook([template(),reaction()],[failed()]));
 assert.equal(denied(await inspect(b,sign(b),SECRET,ROUTE,
  {maxBodyBytes:b.byteLength-1})),'VERIFICATION_DENIED');
 assert.equal(denied(await inspect(b,sign(b),SECRET,ROUTE,
  {maxEvents:2})),'VERIFICATION_DENIED');
 const bad=Uint8Array.from([0xff,0xfe]);
 assert.equal(denied(await inspect(bad,sign(bad),SECRET,ROUTE)),
  'VERIFICATION_DENIED');
});
test('COMPOSE-19 no duplicate specialist execution at occurrence level',async()=>{
 const v=accepted(await run(webhook([template(),list(),reaction(),media(),
  unsupported()],[status('sent'),failed()])));
 const keys=v.map(x=>JSON.stringify(x.position));
 assert.equal(new Set(keys).size,v.length);
 assert.equal(v.filter(x=>x.evidence!==null).length,6);
 assert.equal(v.filter(x=>x.evidence===null).length,1);
});
test('COMPOSE-20 malformed expected kind must not be downgraded to generic',async()=>{
 const m=media('document');(m.document as any).filename=45;
 assert.equal(denied(await run(webhook([plain(),m]))),'COMPONENT_DENIED');
});
