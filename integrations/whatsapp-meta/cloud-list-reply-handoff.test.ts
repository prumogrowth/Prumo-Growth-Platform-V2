/** Synthetic Meta inbound interactive.list_reply: no HTTP, Graph, S0 or ACK. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {
 inspectSignedMetaSelections as inspect,
 inspectSignedMetaButtonReplies as legacy,
} from './cloud-button-reply-handoff.ts';

const SECRET='OFFLINE_SIGNATURE_FIXTURE_ONLY';
const ROUTE={waba_id:'123456789012',phone_number_id:'987654321098',revision:4};
const STAMP='1761000000';
const list=(id='wamid.LIST_IN')=>({
 from:'5581888800000',id,timestamp:STAMP,type:'interactive',
 interactive:{type:'list_reply',list_reply:{
  id:'CATEGORY_GENERICA',title:'Modelos Marca A',description:'Opção fictícia',
 }},
 context:{id:'wamid.SENT_LIST'},
});
const button=()=>({
 from:'5581888800001',id:'wamid.BUTTON_IN',timestamp:STAMP,type:'button',
 button:{text:'Tenho interesse',payload:'MORE_INFO'},
});
const interactiveButton=()=>({
 from:'5581888800002',id:'wamid.INTERACTIVE_IN',timestamp:STAMP,type:'interactive',
 interactive:{type:'button_reply',button_reply:{id:'CHOOSE',title:'Escolher'}},
 context:{id:'wamid.SENT_BUTTON'},
});
const text=()=>({
 from:'5581888800003',id:'wamid.TEXT_IN',timestamp:STAMP,type:'text',
 text:{body:'Texto sem escolha'},
});
const envelope=(messages:unknown[]=[list()],statuses:unknown[]=[])=>({
 object:'whatsapp_business_account',
 entry:[{id:ROUTE.waba_id,changes:[{field:'messages',value:{
  messaging_product:'whatsapp',
  metadata:{phone_number_id:ROUTE.phone_number_id},
  messages,statuses,
 }}]}],
});
const encode=(value:unknown)=>Buffer.from(JSON.stringify(value),'utf8');
const signature=(body:Uint8Array)=>'sha256='+createHmac('sha256',SECRET).update(body).digest('hex');
const run=(value:unknown=envelope(),route=ROUTE)=>{
 const body=encode(value);return inspect(body,signature(body),SECRET,route);
};
function assertSafe(r:Awaited<ReturnType<typeof inspect>>){
 assert.equal(Object.isFrozen(r),true);
 for(const name of ['ack_allowed','send_authorized','s0_write_authorized',
  'retry_external','production_authorized','delivery_confirmed',
  'case_transition_authorized','commercial_effect_authorized',
  'catalog_choice_verified','consent_verified','deduplicated'] as const)
  assert.equal(r[name],false,name);
}
test('LISTREPLY-01 correct signed list selection yields inert technical fields',async()=>{
 const r=await run();assertSafe(r);
 assert.equal(r.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(r.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error('denied');
 assert.equal(r.observations.length,1);
 const selected=r.observations[0];
 assert.equal(selected.kind,'interactive_list_reply');
 assert.equal(selected.button_value,'CATEGORY_GENERICA');
 assert.equal(selected.display_text,'Modelos Marca A');
 assert.equal(selected.reply_to_provider_message_id,'wamid.SENT_LIST');
 assert.equal(selected.provider_message_id,'wamid.LIST_IN');
 assert.equal(selected.position.array_kind,'messages');
 assert.equal(selected.position.item_index,0);
 if(selected.kind!=='interactive_list_reply')throw Error('not list');
 assert.equal(selected.list_description,'Opção fictícia');
 assert.ok(Object.isFrozen(selected));
 assert.ok(Object.isFrozen(selected.position));
});
test('LISTREPLY-02 optional description absent gives null without fabrication',async()=>{
 const v=list();delete (v.interactive.list_reply as any).description;
 const r=await run(envelope([v]));assertSafe(r);
 assert.equal(r.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(r.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error();
 const item=r.observations[0];
 assert.equal(item.kind,'interactive_list_reply');
 if(item.kind!=='interactive_list_reply')throw Error();
 assert.equal(item.list_description,null);
});
test('LISTREPLY-03 mixed list, template button and interactive button retain order',async()=>{
 const r=await run(envelope([button(),text(),list(),interactiveButton()]));assertSafe(r);
 assert.equal(r.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(r.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error();
 assert.deepEqual(r.observations.map(x=>x.kind),[
  'template_quick_reply','interactive_list_reply','interactive_button_reply',
 ]);
 assert.deepEqual(r.observations.map(x=>x.position.item_index),[0,2,3]);
});
test('LISTREPLY-04 old PR24 function still denies list_reply while accepting buttons',async()=>{
 const v=encode(envelope([list()]));
 const old=await legacy(v,signature(v),SECRET,ROUTE);
 assertSafe(old);
 assert.equal(old.decision,'DENIED');
 if(old.decision!=='DENIED')throw Error();
 assert.equal(old.reason,'UNSUPPORTED_INTERACTIVE_VARIANT');
 const vb=encode(envelope([button(),interactiveButton()]));
 const b=await legacy(vb,signature(vb),SECRET,ROUTE);
 assertSafe(b);
 assert.equal(b.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(b.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error();
 assert.deepEqual(b.observations.map(x=>x.kind),[
  'template_quick_reply','interactive_button_reply']);
});
test('LISTREPLY-05 signed but unknown choice remains unverified, no consent',async()=>{
 const v=list();v.interactive.list_reply.id='UNREGISTERED_ID';
 const r=await run(envelope([v]));assertSafe(r);
 assert.equal(r.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(r.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error();
 assert.equal(r.observations[0].button_value,'UNREGISTERED_ID');
 assert.equal(r.catalog_choice_verified,false);
 assert.equal(r.consent_verified,false);
});
test('LISTREPLY-06 malformed list ID, title and description fail entire batch',async()=>{
 for(const item of [
  {id:'',title:'Escolher'},
  {id:'https://malicious.invalid',title:'Escolher'},
  {id:'INVALID ID',title:'Escolher'},
  {id:'CHOICE_1',title:''},
  {id:'CHOICE_1',title:'X'.repeat(25)},
  {id:'CHOICE_1',title:'Nome',description:'X'.repeat(73)},
  {id:'CHOICE_1',title:'Nome',description:'\uD800'},
  {id:'CHOICE_1',title:'Nome',description:13},
 ]){
  const v=list();
  (v.interactive as any).list_reply=item;
  const r=await run(envelope([button(),v]));assertSafe(r);
  assert.equal(r.decision,'DENIED',JSON.stringify(item));
  if(r.decision!=='DENIED')throw Error();
  assert.equal(r.reason,'UNSUPPORTED_REPLY_SHAPE');
  assert.equal(r.observations.length,0);
 }
});
test('LISTREPLY-07 extra action permission or unsupported sibling field denied',async()=>{
 for(const detail of [
  {id:'TEST',title:'Escolher',send_authorized:true},
  {id:'TEST',title:'Escolher',context_id:'wamid.FORGE'},
 ]){
  const v=list();(v.interactive as any).list_reply=detail;
  const r=await run(envelope([v]));assertSafe(r);
  assert.equal(r.decision,'DENIED');
 }
});
test('LISTREPLY-08 interactive envelope with extra field cannot grant authority',async()=>{
 const v=list();(v.interactive as any).commercial_action='APPROVE';
 const r=await run(envelope([v]));assertSafe(r);
 assert.equal(r.decision,'DENIED');
 if(r.decision!=='DENIED')throw Error();
 assert.equal(r.reason,'UNSUPPORTED_INTERACTIVE_VARIANT');
});
test('LISTREPLY-09 unsupported interactive list-like variants denied atomically',async()=>{
 for(const interactive of [
  {type:'nfm_reply',nfm_reply:{response_json:'{}'}},
  {type:'list_reply'},
  {type:'list_reply',button_reply:{id:'FAKE',title:'Sim'}},
 ]){
  const v=list();(v as any).interactive=interactive;
  const r=await run(envelope([button(),v]));assertSafe(r);
  assert.equal(r.decision,'DENIED');
  if(r.decision!=='DENIED')throw Error();
  assert.equal(r.observations.length,0);
 }
});
test('LISTREPLY-10 bad HMAC, wrong secret and wrong WABA scope denied',async()=>{
 const b=encode(envelope([list()]));
 const [a,c,d]=await Promise.all([
  inspect(b,'sha256='+'0'.repeat(64),SECRET,ROUTE),
  inspect(b,signature(b),'INCORRECT_SECRET',ROUTE),
  inspect(b,signature(b),SECRET,{...ROUTE,waba_id:'999999999999'}),
 ]);
 for(const r of [a,c,d]){
  assertSafe(r);assert.equal(r.decision,'DENIED');
  assert.equal(r.raw_sha256,null);assert.equal(r.observations.length,0);
 }
});
test('LISTREPLY-11 multiple changes mixed scopes deny entire result',async()=>{
 const v=envelope([list()]);
 v.entry[0].changes.push({field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:'999999999999'},
  messages:[list('wamid.CROSS')],statuses:[],
 }});
 const r=await run(v);assertSafe(r);
 assert.equal(r.decision,'DENIED');
});
test('LISTREPLY-12 duplicate list callbacks remain separate until durable dedupe',async()=>{
 const l=list();
 const r=await run(envelope([l,{...l}]));assertSafe(r);
 assert.equal(r.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(r.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error();
 assert.equal(r.observations.length,2);
 assert.deepEqual(r.observations.map(x=>x.position.item_index),[0,1]);
 assert.equal(r.deduplicated,false);
});
test('LISTREPLY-13 missing context remains technical candidate not sent correlation',async()=>{
 const l=list();delete (l as any).context;
 const r=await run(envelope([l]));assertSafe(r);
 assert.equal(r.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(r.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error();
 assert.equal(r.observations[0].reply_to_provider_message_id,null);
});
test('LISTREPLY-14 invalid context and malformed sibling status block all',async()=>{
 const l=list();l.context.id='not_a_wamid';
 const bad=await run(envelope([l]));assertSafe(bad);
 assert.equal(bad.decision,'DENIED');
 const s={id:'wamid.SENT',recipient_id:'5581888800000',status:'failed',timestamp:'BAD'};
 const other=await run(envelope([list()],[s]));assertSafe(other);
 assert.equal(other.decision,'DENIED');
});
test('LISTREPLY-15 unicode title and description preserved only as untrusted display',async()=>{
 const v=list();v.interactive.list_reply.title='Motos 🏍️';
 v.interactive.list_reply.description='Escolha rápida: São Paulo 🚀';
 const r=await run(envelope([v]));assertSafe(r);
 assert.equal(r.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(r.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error();
 assert.equal(r.observations[0].display_text,'Motos 🏍️');
 if(r.observations[0].kind!=='interactive_list_reply')throw Error();
 assert.equal(r.observations[0].list_description,'Escolha rápida: São Paulo 🚀');
});
