/** Meta Cloud composition hardening — synthetic signed adversarial identities. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {inspectSignedMetaComposedWebhook as inspect}
 from './cloud-composed-observation-handoff.ts';
const SECRET='GENERIC_IDENTITY_AUDIT_OFFLINE_ONLY';
const ROUTE={waba_id:'123456789012',phone_number_id:'987654321098',revision:3};
const T='1761000000';
const generic=(extra:Record<string,unknown>={})=>({
 id:'wamid.GENERIC',from:'5581888800000',timestamp:T,type:'text',
 text:{body:'synthetic'},...extra,
});
const unknown=(extra:Record<string,unknown>={})=>({
 id:'wamid.FUTURE',from:'5581888800000',timestamp:T,
 type:'future_feature',...extra,
});
const reaction=()=>({
 id:'wamid.REACT',from:'5581888800000',timestamp:T,type:'reaction',
 reaction:{message_id:'wamid.OUT',emoji:'👍'},
});
const status=(extra:Record<string,unknown>={})=>({
 id:'wamid.OUT',recipient_id:'5581888800000',timestamp:T,status:'sent',...extra,
});
const body=(messages:unknown[]=[generic()],statuses:unknown[]=[])=>({
 object:'whatsapp_business_account',
 entry:[{id:ROUTE.waba_id,changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:ROUTE.phone_number_id},
  messages,statuses,
 }}]}],
});
const b=(v:unknown)=>Buffer.from(JSON.stringify(v),'utf8');
const sign=(x:Uint8Array)=>
 'sha256='+createHmac('sha256',SECRET).update(x).digest('hex');
const run=(v:unknown)=>{
 const raw=b(v);return inspect(raw,sign(raw),SECRET,ROUTE);
};
function accepted(x:Awaited<ReturnType<typeof inspect>>){
 assert.equal(x.decision,'SIGNED_COMPOSED_NOT_DURABLE');
 if(x.decision!=='SIGNED_COMPOSED_NOT_DURABLE')throw Error('Denied');
 assert.equal(x.ack_allowed,false);
 assert.equal(x.send_authorized,false);
 return x.occurrences;
}
function denied(x:Awaited<ReturnType<typeof inspect>>){
 assert.equal(x.decision,'DENIED');
 if(x.decision!=='DENIED')throw Error('Accepted unexpectedly');
 assert.equal(x.reason,'INVALID_TECHNICAL_IDENTIFIERS');
 assert.equal(x.raw_sha256,null);
 assert.deepEqual(x.occurrences,[]);
 for(const flag of ['ack_allowed','send_authorized','s0_write_authorized',
  'delivery_confirmed','commercial_effect_authorized','deduplicated',
  'case_transition_authorized'] as const)assert.equal(x[flag],false);
}

test('IDENTITY-01 valid generic message remains uninterpreted',async()=>{
 const o=accepted(await run(body()));
 assert.equal(o[0].kind,'uninterpreted_inbound');
});
test('IDENTITY-02 legitimate future type remains uninterpreted',async()=>{
 const o=accepted(await run(body([unknown()])));
 assert.equal(o[0].provider_kind,'future_feature');
 assert.equal(o[0].evidence,null);
});
test('IDENTITY-03 reject non-wamid generic ID rather than exposing it',async()=>{
 await denied(await run(body([generic({id:'NON_WAMID'})])));
});
test('IDENTITY-04 reject newlines in signed generic message ID',async()=>{
 await denied(await run(body([generic({id:'wamid.OK\nX-Header: bad'})])));
});
test('IDENTITY-05 reject invisible control in signed message ID',async()=>{
 await denied(await run(body([generic({id:'wamid.BAD\u0000ID'})])));
});
test('IDENTITY-06 reject whitespace and Unicode lookalikes in message ID',async()=>{
 for(const id of ['wamid.BAD ID','wamid.Á','wamid.BAD\tTAB']){
  await denied(await run(body([generic({id})])));
 }
});
test('IDENTITY-07 reject free-form participant identifier in generic message',async()=>{
 await denied(await run(body([generic({from:'anonymous'})])));
});
test('IDENTITY-08 reject multiline participant identifier',async()=>{
 await denied(await run(body([generic({from:'5581888800000\nadmin'})])));
});
test('IDENTITY-09 reject too-short numeric participant identifier',async()=>{
 await denied(await run(body([generic({from:'1234567'})])));
});
test('IDENTITY-10 reject overlong numeric participant identifier',async()=>{
 await denied(await run(body([generic({from:'1'.repeat(16)})])));
});
test('IDENTITY-11 reject invisible Unicode numeric lookalike',async()=>{
 await denied(await run(body([generic({from:'٥٥٨١٨٨٨٨٠٠٠٠٠'})])));
});
test('IDENTITY-12 reject uppercase message kind as uncontracted',async()=>{
 await denied(await run(body([generic({type:'TEXT'})])));
});
test('IDENTITY-13 reject kind containing control or newline',async()=>{
 await denied(await run(body([generic({type:'text\nprivileged'})])));
});
test('IDENTITY-14 reject empty or punctuation-leading message type',async()=>{
 for(const type of ['_text','.text','1text']){
  await denied(await run(body([generic({type})])));
 }
});
test('IDENTITY-15 reject malformed successful status message ID',async()=>{
 await denied(await run(body([],[status({id:'sent01'})])));
});
test('IDENTITY-16 reject malformed successful status recipient identifier',async()=>{
 await denied(await run(body([],[status({recipient_id:'evil\nLOG'})])));
});
test('IDENTITY-17 reject non-E164-length numeric recipient identifier',async()=>{
 await denied(await run(body([],[status({recipient_id:'1234567'})])));
});
test('IDENTITY-18 one invalid generic sibling denies all valid specialty evidence',async()=>{
 const o=await run(body([reaction(),generic({from:'INJECTED'})],[status()]));
 await denied(o);
});
test('IDENTITY-19 repeated valid identifiers remain distinct signed occurrences',async()=>{
 const m=generic();
 const o=accepted(await run(body([m,{...m}])));
 assert.deepEqual(o.map(x=>x.position.item_index),[0,1]);
 assert.equal(o[0].provider_message_id,o[1].provider_message_id);
 assert.equal(o[0].evidence,null);
});
test('IDENTITY-20 100 valid generic events remain supported',async()=>{
 const arr=Array.from({length:100},(_,i)=>generic({id:'wamid.GENERIC_'+i}));
 const o=accepted(await run(body(arr)));
 assert.equal(o.length,100);
 assert.equal(o[99].position.item_index,99);
});
