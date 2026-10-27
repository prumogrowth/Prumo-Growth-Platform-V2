/** All reaction samples are fictional. No HTTP ACK, token, Graph or S0. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {inspectSignedMetaReactions as inspect} from './cloud-reaction-handoff.ts';

const SECRET='REACTION_FIXTURE_SECRET_NOT_FOR_PRODUCTION';
const ROUTE={waba_id:'123456789012',phone_number_id:'987654321098',revision:4};
const STAMP='1761000000';
const reaction=(emoji='👍',id='wamid.REACTION_EVENT')=>({
 from:'5581888800000',id,timestamp:STAMP,type:'reaction',
 reaction:{message_id:'wamid.TARGET_SENT',emoji},
});
const text=()=>({
 from:'5581888800001',id:'wamid.TEXT',timestamp:STAMP,type:'text',
 text:{body:'Mensagem fictícia'},
});
const list=()=>({
 from:'5581888800002',id:'wamid.LIST',timestamp:STAMP,type:'interactive',
 interactive:{type:'list_reply',list_reply:{id:'MODEL_1',title:'Modelo'}},
});
const status=(timestamp=STAMP)=>({
 id:'wamid.TARGET_SENT',recipient_id:'5581888800000',status:'delivered',timestamp,
});
const envelope=(messages:unknown[]=[reaction()],statuses:unknown[]=[])=>({
 object:'whatsapp_business_account',
 entry:[{id:ROUTE.waba_id,changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:ROUTE.phone_number_id},
  messages,statuses,
 }}]}],
});
const bytes=(value:unknown)=>Buffer.from(JSON.stringify(value),'utf8');
const sign=(body:Uint8Array)=>
 'sha256='+createHmac('sha256',SECRET).update(body).digest('hex');
const run=(value:unknown=envelope(),route=ROUTE)=>{
 const b=bytes(value);return inspect(b,sign(b),SECRET,route);
};
function safe(r:Awaited<ReturnType<typeof inspect>>){
 assert.ok(Object.isFrozen(r));
 for(const key of ['ack_allowed','send_authorized','s0_write_authorized',
  'retry_external','production_authorized','delivery_confirmed',
  'case_transition_authorized','commercial_effect_authorized',
  'consent_verified','deduplicated','target_message_correlated',
  'reaction_effect_confirmed'] as const)
  assert.equal(r[key],false,key);
}
function accepted(r:Awaited<ReturnType<typeof inspect>>){
 safe(r);assert.equal(r.decision,'SIGNED_REACTIONS_NOT_DURABLE');
 if(r.decision!=='SIGNED_REACTIONS_NOT_DURABLE')throw Error('unexpected denial');
 return r.observations;
}

test('REACTION-01 signed addition preserves distinct event and target identifiers',async()=>{
 const r=await run();const o=accepted(r);
 assert.equal(o.length,1);
 assert.equal(o[0].provider_message_id,'wamid.REACTION_EVENT');
 assert.equal(o[0].target_provider_message_id,'wamid.TARGET_SENT');
 assert.equal(o[0].kind,'incoming_reaction');
 assert.equal(o[0].emoji,'👍');
 assert.equal(o[0].operation,'add_candidate');
 assert.equal(o[0].participant_identifier,'5581888800000');
 assert.equal(o[0].position.item_index,0);
 assert.equal(o[0].position.array_kind,'messages');
 assert.ok(Object.isFrozen(o[0]));assert.ok(Object.isFrozen(o[0].position));
 assert.match(r.raw_sha256!,/^[0-9a-f]{64}$/);
});
test('REACTION-02 empty emoji is removal marker, not a confirmed removal',async()=>{
 const r=await run(envelope([reaction('')]));const o=accepted(r);
 assert.equal(o[0].emoji,'');
 assert.equal(o[0].operation,'remove_candidate');
 assert.equal(r.reaction_effect_confirmed,false);
 assert.equal(r.target_message_correlated,false);
});
test('REACTION-03 mixed ordinary messages, lists and statuses retain exact positions',async()=>{
 const r=await run(envelope([text(),reaction(),list(),reaction('','wamid.R2')],[status()]));
 const o=accepted(r);
 assert.equal(o.length,2);
 assert.deepEqual(o.map(x=>x.position.item_index),[1,3]);
 assert.deepEqual(o.map(x=>x.provider_message_id),['wamid.REACTION_EVENT','wamid.R2']);
 assert.equal(r.delivery_confirmed,false);
});
test('REACTION-04 signed non-reaction webhook gives no inferred reactions or ACK',async()=>{
 const r=await run(envelope([text(),list()],[status()]));
 assert.deepEqual(accepted(r),[]);
 assert.equal(r.ack_allowed,false);
});
test('REACTION-05 missing, null and wrong-type emoji deny whole mixed batch',async()=>{
 for(const bad of [undefined,null,1,{},[]]){
  const v=reaction();
  if(bad===undefined)delete (v.reaction as any).emoji;
  else (v.reaction as any).emoji=bad;
  const r=await run(envelope([reaction(),v]));
  safe(r);assert.equal(r.decision,'DENIED');
  if(r.decision!=='DENIED')throw Error();
  assert.equal(r.reason,'UNSUPPORTED_REACTION_SHAPE');
  assert.equal(r.observations.length,0);
 }
});
test('REACTION-06 extra commercial field or forged action is denied',async()=>{
 for(const extra of [{commercial_effect_authorized:true},{action:'approve'}]){
  const v=reaction();Object.assign(v.reaction,extra);
  const r=await run(envelope([v]));safe(r);
  assert.equal(r.decision,'DENIED');
 }
});
test('REACTION-07 missing and malformed target identifiers denied',async()=>{
 for(const id of [undefined,null,'','1234','not.wamid', 'wamid.'+'x'.repeat(1025),'wamid.BAD ID']){
  const v=reaction();
  if(id===undefined)delete (v.reaction as any).message_id;
  else (v.reaction as any).message_id=id;
  const r=await run(envelope([v]));safe(r);
  assert.equal(r.decision,'DENIED',String(id));
 }
});
test('REACTION-08 control characters, broken surrogates and overly long emoji denied',async()=>{
 for(const emoji of ['A\nB','\u0000','\uD800','\uDC00','😀'.repeat(33)]){
  const r=await run(envelope([reaction(emoji)]));safe(r);
  assert.equal(r.decision,'DENIED');
 }
});
test('REACTION-09 Unicode joined emoji is preserved as opaque untrusted content',async()=>{
 const glyph='👩🏽‍💻';
 const r=await run(envelope([reaction(glyph)]));const o=accepted(r);
 assert.equal(o[0].emoji,glyph);
 assert.equal(r.consent_verified,false);
});
test('REACTION-10 HMAC mismatch and malformed signature reveal no data',async()=>{
 const b=bytes(envelope());
 for(const sig of ['sha256='+'0'.repeat(64),'not-a-signature',null]){
  const r=await inspect(b,sig,SECRET,ROUTE);safe(r);
  assert.equal(r.decision,'DENIED');
  if(r.decision!=='DENIED')throw Error();
  assert.equal(r.raw_sha256,null);assert.equal(r.observations.length,0);
 }
});
test('REACTION-11 wrong app secret or trusted route never produce candidates',async()=>{
 const b=bytes(envelope());
 for(const r of await Promise.all([
  inspect(b,sign(b),'WRONG_SECRET',ROUTE),
  inspect(b,sign(b),SECRET,{...ROUTE,waba_id:'900000000000'}),
  inspect(b,sign(b),SECRET,{...ROUTE,phone_number_id:'900000000000'}),
 ])){
  safe(r);assert.equal(r.decision,'DENIED');
 }
});
test('REACTION-12 whole-batch WABA and phone scope are enforced',async()=>{
 const b=envelope();
 b.entry.push({id:'999999999999',changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:ROUTE.phone_number_id},
  messages:[reaction()],statuses:[],
 }}]});
 const r=await run(b);safe(r);assert.equal(r.decision,'DENIED');
 const c=envelope();
 c.entry[0].changes.push({field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:'999999999999'},
  messages:[reaction()],statuses:[],
 }});
 const other=await run(c);safe(other);assert.equal(other.decision,'DENIED');
});
test('REACTION-13 duplicate callback remains two candidates pending S0 dedupe',async()=>{
 const v=reaction();
 const r=await run(envelope([v,{...v}]));const o=accepted(r);
 assert.equal(o.length,2);
 assert.deepEqual(o.map(x=>x.position.item_index),[0,1]);
 assert.equal(r.deduplicated,false);
});
test('REACTION-14 malformed sibling status and unsupported subscribed field block all',async()=>{
 const r=await run(envelope([reaction()],[status('bad')]));
 safe(r);assert.equal(r.decision,'DENIED');
 const v=envelope([reaction()]);
 (v.entry[0].changes[0] as any).field='unknown_field';
 const q=await run(v);safe(q);assert.equal(q.decision,'DENIED');
});
test('REACTION-15 body size, invalid UTF-8 and max event limit fail closed',async()=>{
 const b=bytes(envelope([reaction(),reaction('','wamid.SECOND')]));
 const cases=[
  inspect(b,sign(b),SECRET,ROUTE,{maxBodyBytes:b.byteLength-1}),
  inspect(b,sign(b),SECRET,ROUTE,{maxEvents:1}),
 ];
 const invalid=Uint8Array.from([0xff,0xfe,0xfd]);
 cases.push(inspect(invalid,sign(invalid),SECRET,ROUTE));
 for(const r of await Promise.all(cases)){safe(r);assert.equal(r.decision,'DENIED');}
});
test('REACTION-16 caller mutation after invocation cannot change signed snapshot',async()=>{
 const b=bytes(envelope([reaction('🔥')]));
 const task=inspect(b,sign(b),SECRET,ROUTE);
 b.fill(0);
 const r=await task;const o=accepted(r);
 assert.equal(o[0].emoji,'🔥');
});
