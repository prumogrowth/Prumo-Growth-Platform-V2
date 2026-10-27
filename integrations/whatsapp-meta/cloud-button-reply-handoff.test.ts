/** Signed Meta button reply observations — ALL synthetic, no HTTP, S0 or Graph. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {inspectSignedMetaButtonReplies as inspect} from './cloud-button-reply-handoff.ts';

const SECRET='DEMO_META_APP_SECRET_NOT_PRODUCTION';
const route={waba_id:'123456789012',phone_number_id:'987654321098',revision:4};
const stamp='1761000000';
const quick=(id='wamid.IN_BTN')=>({
 from:'5581900000000',id,timestamp:stamp,type:'button',
 button:{text:'Tenho interesse',payload:'OPT_INQUIRY'},
 context:{id:'wamid.SENT_TEMPLATE'},
});
const interactive=()=>({
 from:'5581999999999',id:'wamid.IN_INTERACTIVE',timestamp:stamp,
 type:'interactive',
 interactive:{type:'button_reply',button_reply:{id:'BTN_MORE',title:'Saiba mais'}},
 context:{id:'wamid.SENT_INTERACTIVE'},
});
const text=()=>({
 from:'5581777700000',id:'wamid.TEXT',timestamp:stamp,
 type:'text',text:{body:'Mensagem normal sem botão'},
});
const root=(messages:unknown[]=[quick(),interactive(),text()],statuses:unknown[]=[])=>({
 object:'whatsapp_business_account',entry:[{id:route.waba_id,changes:[{
 field:'messages',value:{messaging_product:'whatsapp',
 metadata:{phone_number_id:route.phone_number_id},
 messages,statuses},
 }]}],
});
const bytes=(v:unknown)=>Buffer.from(JSON.stringify(v),'utf8');
const sign=(v:Uint8Array)=>'sha256='+createHmac('sha256',SECRET).update(v).digest('hex');
const run=(v:unknown=root(),override=route)=>{
 const b=bytes(v);return inspect(b,sign(b),SECRET,override);
};
function safety(r:Awaited<ReturnType<typeof inspect>>){
 for(const key of ['ack_allowed','send_authorized','s0_write_authorized',
  'retry_external','production_authorized','delivery_confirmed',
  'case_transition_authorized','commercial_effect_authorized',
  'catalog_choice_verified','consent_verified','deduplicated'] as const)
  assert.equal(r[key],false,key);
 assert.ok(Object.isFrozen(r));
}
test('REPLY-01 template and interactive replies are separate types',async()=>{
 const r=await run();safety(r);
 assert.equal(r.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(r.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error();
 assert.deepEqual(r.observations.map(x=>x.kind),
  ['template_quick_reply','interactive_button_reply']);
 assert.deepEqual(r.observations.map(x=>x.button_value),['OPT_INQUIRY','BTN_MORE']);
 assert.deepEqual(r.observations.map(x=>x.display_text),
  ['Tenho interesse','Saiba mais']);
 assert.deepEqual(r.observations.map(x=>x.reply_to_provider_message_id),
  ['wamid.SENT_TEMPLATE','wamid.SENT_INTERACTIVE']);
 assert.deepEqual(r.observations.map(x=>x.position.item_index),[0,1]);
 assert.ok(Object.isFrozen(r.observations[0].position));
});
test('REPLY-02 ordinary inbound text is ignored, not turned into intent',async()=>{
 const r=await run(root([text()]));safety(r);
 assert.equal(r.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(r.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error();
 assert.equal(r.observations.length,0);
});
test('REPLY-03 a status callback is not a clicked button',async()=>{
 const status={id:'wamid.SENT_TEMPLATE',recipient_id:'5581900000000',
  status:'delivered',timestamp:stamp};
 const r=await run(root([quick()], [status]));safety(r);
 assert.equal(r.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(r.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error();
 assert.equal(r.observations.length,1);
 assert.equal(r.delivery_confirmed,false);
});
test('REPLY-04 missing context can still be observed but not correlated',async()=>{
 const b=quick();delete (b as any).context;
 const r=await run(root([b]));safety(r);
 assert.equal(r.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(r.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error();
 assert.equal(r.observations[0].reply_to_provider_message_id,null);
 assert.equal(r.catalog_choice_verified,false);
});
test('REPLY-05 signed payload with unknown button value is not approved choice',async()=>{
 const b=quick();b.button.payload='UNKNOWN_FUTURE_CHOICE';
 const r=await run(root([b]));safety(r);
 assert.equal(r.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(r.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error();
 assert.equal(r.observations[0].button_value,'UNKNOWN_FUTURE_CHOICE');
 assert.equal(r.catalog_choice_verified,false);
});
test('REPLY-06 invalid HMAC denies, revealing no callback payload',async()=>{
 const b=bytes(root());
 const r=await inspect(b,'sha256='+'0'.repeat(64),SECRET,route);safety(r);
 assert.equal(r.decision,'DENIED');
 if(r.decision!=='DENIED')throw Error();
 assert.equal(r.reason,'VERIFICATION_DENIED');
 assert.equal(r.observations.length,0);
 assert.equal(r.raw_sha256,null);
 assert.equal(JSON.stringify(r).includes('OPT_INQUIRY'),false);
});
test('REPLY-07 wrong app secret and wrong trusted route both deny',async()=>{
 const b=bytes(root());
 const [a,c]=await Promise.all([
  inspect(b,sign(b),'WRONG_SECRET',route),
  inspect(b,sign(b),SECRET,{...route,phone_number_id:'100000000000'}),
 ]);
 for(const r of [a,c]){safety(r);assert.equal(r.decision,'DENIED');}
});
test('REPLY-08 cross-WABA entry in signed batch invalidates whole handoff',async()=>{
 const a=root([quick()]);a.entry.push({id:'999999999999',changes:[{
  field:'messages',value:{messaging_product:'whatsapp',
   metadata:{phone_number_id:route.phone_number_id},
   messages:[quick('wamid.CROSS')],statuses:[]}}]});
 const r=await run(a);safety(r);
 assert.equal(r.decision,'DENIED');
});
test('REPLY-09 missing button payload denies entire batch, not partial',async()=>{
 const broken=quick();delete (broken.button as any).payload;
 const r=await run(root([quick(),broken]));safety(r);
 assert.equal(r.decision,'DENIED');
 if(r.decision!=='DENIED')throw Error();
 assert.equal(r.reason,'UNSUPPORTED_REPLY_SHAPE');
 assert.equal(r.observations.length,0);
});
test('REPLY-10 URL-shaped, control, overlength or unicode payloads denied',async()=>{
 for(const payload of ['https://attacker.invalid','bad value','\n','é','X'.repeat(129),'']){
  const b=quick();b.button.payload=payload;
  const r=await run(root([b]));safety(r);
  assert.equal(r.decision,'DENIED',payload);
 }
});
test('REPLY-11 forged extra button fields refused, no inferred authority',async()=>{
 const b=quick();(b.button as any).send_authorized=true;
 const r=await run(root([b]));safety(r);
 assert.equal(r.decision,'DENIED');
});
test('REPLY-12 unknown interactive variants fail closed',async()=>{
 for(const payload of [
  {type:'list_reply',list_reply:{id:'CHOICE',title:'N'}},
  {type:'button_reply',button_reply:{id:'YES',title:'Sim'},extra_flag:true},
  {type:'product',product:{id:'ABC'}},
 ]){
  const item={...interactive(),interactive:payload};
  const r=await run(root([item]));safety(r);
  assert.equal(r.decision,'DENIED');
 }
});
test('REPLY-13 missing button_reply or invalid id/title deny',async()=>{
 for(const payload of [
  {type:'button_reply'}, {type:'button_reply',button_reply:{id:'',title:'Sim'}},
  {type:'button_reply',button_reply:{id:'CHOICE',title:'\uD800'}},
  {type:'button_reply',button_reply:{id:'CHOICE',title:'Sim',send_authorized:true}},
 ]){
  const r=await run(root([{...interactive(),interactive:payload}]));safety(r);
  assert.equal(r.decision,'DENIED');
 }
});
test('REPLY-14 invalid context ID denies; no correlated sent message invented',async()=>{
 const b=quick();b.context.id='not-a-wamid';
 const r=await run(root([b]));safety(r);
 assert.equal(r.decision,'DENIED');
});
test('REPLY-15 duplicate message remains duplicated, pending S0 dedupe',async()=>{
 const b=quick();
 const r=await run(root([b,{...b}]));safety(r);
 assert.equal(r.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(r.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error();
 assert.equal(r.observations.length,2);
 assert.deepEqual(r.observations.map(x=>x.position.item_index),[0,1]);
 assert.equal(r.deduplicated,false);
});
test('REPLY-16 oversized or invalid UTF8 requests deny',async()=>{
 const b=bytes(root());
 const over=await inspect(b,sign(b),SECRET,route,{maxBodyBytes:b.length-1});
 const bad=Buffer.from([0xff,0xfe,0xfd]);
 const malformed=await inspect(bad,sign(bad),SECRET,route);
 for(const r of [over,malformed]){safety(r);assert.equal(r.decision,'DENIED');}
});
test('REPLY-17 legitimate emoji and accents in button title remain as data',async()=>{
 const b=quick();b.button.text='Quero saber mais 🚀';
 const r=await run(root([b]));safety(r);
 assert.equal(r.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
 if(r.decision!=='SIGNED_CANDIDATES_NOT_DURABLE')throw Error();
 assert.equal(r.observations[0].display_text,'Quero saber mais 🚀');
});
test('REPLY-18 malformed sibling entry or status blocks all output',async()=>{
 const b=root([quick()]);b.entry[0].changes[0].value.statuses=[{
  id:'wamid.SENT',recipient_id:'12345',status:'failed',timestamp:'BAD',
 }];
 const r=await run(b);safety(r);
 assert.equal(r.decision,'DENIED');
});
