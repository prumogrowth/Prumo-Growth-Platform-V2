/** Synthetic quoted-reply context compatibility and signed composition. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {inspectSignedMetaQuotedContexts as inspect}
 from './cloud-quoted-context-handoff.ts';
import {inspectSignedMetaComposedWebhook as compose}
 from './cloud-composed-observation-handoff.ts';

const SECRET='QUOTED_CONTEXT_FIXTURES_NOT_META_SECRET';
const ROUTE={waba_id:'123456789012',phone_number_id:'987654321098',revision:9};
const TIME='1761000000';
const context=(id='wamid.QUOTED')=>({id,from:'5581888812345'});
const msg=(type:string,id:string,rest:Record<string,unknown>={})=>({
 from:'5581888800000',id,timestamp:TIME,type,...rest,
});
const NO_CONTEXT=Symbol('synthetic-message-without-context');
const text=(ctx:unknown=context(),id='wamid.TEXT')=>msg('text',id,{
 text:{body:'Synthetic reply without original content'},
 ...(ctx===NO_CONTEXT?{}:{context:ctx}),
});
const button=(ctx:unknown=context())=>msg('button','wamid.BUTTON',{
 button:{payload:'TEST_1',text:'Escolher'},context:ctx,
});
const media=()=>msg('image','wamid.MEDIA',{
 image:{id:'99887766554433'},context:context(),
});
const reaction=()=>msg('reaction','wamid.REACT',{
 reaction:{message_id:'wamid.ORIGINAL',emoji:'👍'},context:context(),
});
const status=(value:'sent'|'failed'='sent')=>({
 id:'wamid.OUT',recipient_id:'5581888800000',status:value,timestamp:TIME,
 ...(value==='failed'?{errors:[{code:131026}]}:{}),
});
const body=(messages:unknown[]=[text()],statuses:unknown[]=[])=>({
 object:'whatsapp_business_account',entry:[{id:ROUTE.waba_id,
 changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:ROUTE.phone_number_id},
  messages,statuses,
 }}]}],
});
const bytes=(v:unknown)=>Buffer.from(JSON.stringify(v),'utf8');
const sign=(b:Uint8Array)=>
 'sha256='+createHmac('sha256',SECRET).update(b).digest('hex');
const run=(v:unknown=body(),route=ROUTE)=>{
 const b=bytes(v);return inspect(b,sign(b),SECRET,route);
};
const combined=(v:unknown=body())=>{
 const b=bytes(v);return compose(b,sign(b),SECRET,ROUTE);
};
function noAuthority(v:Record<string,unknown>){
 for(const key of ['ack_allowed','send_authorized','s0_write_authorized',
  'retry_external','production_authorized','delivery_confirmed',
  'case_transition_authorized','commercial_effect_authorized',
  'consent_verified','deduplicated','quoted_message_correlated',
  'quoted_content_recovered'] )
  assert.equal(v[key],false,key);
}
function observed(r:Awaited<ReturnType<typeof inspect>>){
 noAuthority(r);assert.equal(r.decision,'SIGNED_QUOTED_REFERENCES_NOT_DURABLE');
 if(r.decision!=='SIGNED_QUOTED_REFERENCES_NOT_DURABLE')throw Error('denied');
 return r.observations;
}
function denied(r:Awaited<ReturnType<typeof inspect>>,reason:string){
 noAuthority(r);assert.equal(r.decision,'DENIED');
 if(r.decision!=='DENIED')throw Error('accepted');
 assert.equal(r.reason,reason);
 assert.deepEqual(r.observations,[]);assert.equal(r.raw_sha256,null);
}
function composed(r:Awaited<ReturnType<typeof compose>>){
 assert.equal(r.decision,'SIGNED_COMPOSED_NOT_DURABLE');
 if(r.decision!=='SIGNED_COMPOSED_NOT_DURABLE')throw Error('denied');
 assert.equal(r.quoted_message_correlated,false);
 assert.equal(r.quoted_content_recovered,false);
 assert.equal(r.send_authorized,false);
 return r.occurrences;
}
function denyComposite(r:Awaited<ReturnType<typeof compose>>,reason:string){
 assert.equal(r.decision,'DENIED');
 if(r.decision!=='DENIED')throw Error('accepted');
 assert.equal(r.reason,reason);
 assert.equal(r.raw_sha256,null);
 assert.deepEqual(r.occurrences,[]);
}
async function countVerify(fn:()=>Promise<unknown>){
 const subtle=crypto.subtle,orig=subtle.verify;
 let count=0;
 (subtle as any).verify=function(...args:unknown[]){
  count++;return Reflect.apply(orig,subtle,args);
 };
 try{return {result:await fn(),count};}
 finally{(subtle as any).verify=orig;}
}

test('QUOTE-01 signed text reply exposes only referenced ID and optional sender',async()=>{
 const r=await run(),v=observed(r);
 assert.equal(v.length,1);
 assert.equal(v[0].kind,'incoming_quoted_reference');
 assert.equal(v[0].quoted_provider_message_id,'wamid.QUOTED');
 assert.equal(v[0].quoted_sender_identifier_untrusted,'5581888812345');
 assert.equal(v[0].provider_message_id,'wamid.TEXT');
 assert.equal(v[0].position.array_kind,'messages');
 assert.match(r.raw_sha256!,/^[a-f0-9]{64}$/);
 assert.ok(Object.isFrozen(r)&&Object.isFrozen(v)&&
  Object.isFrozen(v[0])&&Object.isFrozen(v[0].position));
 assert.equal(JSON.stringify(v).includes('Synthetic reply'),false);
});
test('QUOTE-02 optional sender omitted and unknown context fields ignored',async()=>{
 const v=observed(await run(body([text({
  id:'wamid.OTHER',referred_product:{catalog_id:'CATALOG_SECRET'},
  mentions:['UNTRUSTED'],forwarded:true,
 })])));
 assert.equal(v[0].quoted_sender_identifier_untrusted,null);
 assert.equal(JSON.stringify(v).includes('CATALOG_SECRET'),false);
 assert.equal(JSON.stringify(v).includes('UNTRUSTED'),false);
});
test('QUOTE-03 forwarding-only context is not falsely classified as a quote',async()=>{
 const v=observed(await run(body([text({
  forwarded:true,frequently_forwarded:false,
 })])));
 assert.deepEqual(v,[]);
});
test('QUOTE-04 generic messages without context preserve no observations',async()=>{
 const v=observed(await run(body([text(NO_CONTEXT)])));
 assert.deepEqual(v,[]);
});
test('QUOTE-05 mixed context and no-context preserve positions',async()=>{
 const v=observed(await run(body([
  text(NO_CONTEXT,'wamid.T0'),text(context(),'wamid.T1'),
  text({id:'wamid.EXTRA'},'wamid.T2'),
 ],[status()])));
 assert.deepEqual(v.map(x=>x.position.item_index),[1,2]);
});
test('QUOTE-06 duplicate refs remain separate occurrences without dedupe',async()=>{
 const x=text(),v=observed(await run(body([x,{...x}])));
 assert.equal(v.length,2);
 assert.deepEqual(v.map(x=>x.position.item_index),[0,1]);
});
test('QUOTE-07 malformed null or scalar context denies all',async()=>{
 for(const ctx of [null,1,'wamid.QUOTE',[],true]){
  denied(await run(body([text(),text(ctx,'wamid.BAD')])),
   'INVALID_CONTEXT_SHAPE');
 }
});
test('QUOTE-08 incorrect quoted ID denied atomically',async()=>{
 for(const id of ['', 'wamid.BAD ID','a-wamid','wamid.X\ninject']){
  denied(await run(body([text(),text({id},'wamid.BAD')])),
   'INVALID_CONTEXT_SHAPE');
 }
});
test('QUOTE-09 malformed context sender denied atomically',async()=>{
 for(const from of [null,23,'name','1234567','1'.repeat(16),
  '5581888800000\nfoo']){
  denied(await run(body([text({id:'wamid.Q',from},'wamid.BAD')])),
   'INVALID_CONTEXT_SHAPE');
 }
});
test('QUOTE-10 sender without quoted ID is incoherent',async()=>{
 denied(await run(body([text({from:'5581888800000'})])),
  'INVALID_CONTEXT_SHAPE');
});
test('QUOTE-11 body signature tampering is denied before extraction',async()=>{
 const raw=bytes(body());const modified=bytes(body([
  text({id:'wamid.OTHER'})]));
 denied(await inspect(modified,sign(raw),SECRET,ROUTE),
  'VERIFICATION_DENIED');
 denied(await inspect(raw,'sha256='+'0'.repeat(64),SECRET,ROUTE),
  'VERIFICATION_DENIED');
 denied(await inspect(raw,null,SECRET,ROUTE),'VERIFICATION_DENIED');
});
test('QUOTE-12 trusted route mismatch denies content',async()=>{
 const b=bytes(body());
 denied(await inspect(b,sign(b),SECRET,{
  ...ROUTE,waba_id:'999999999999',
 }),'VERIFICATION_DENIED');
 denied(await inspect(b,sign(b),SECRET,{
  ...ROUTE,phone_number_id:'999999999999',
 }),'VERIFICATION_DENIED');
});
test('QUOTE-13 authenticated but malformed sibling status denies all',async()=>{
 const x=status();x.timestamp='bad';
 denied(await run(body([text()],[x])),'VERIFICATION_DENIED');
});
test('QUOTE-14 body mutation after invocation cannot change the signed view',async()=>{
 const b=bytes(body());
 const task=inspect(b,sign(b),SECRET,{...ROUTE});
 b.fill(0);
 assert.equal(observed(await task)[0].quoted_provider_message_id,'wamid.QUOTED');
});
test('QUOTE-15 body/event limits respected before any candidate',async()=>{
 const b=bytes(body([text(),text(context(),'wamid.T2')]));
 denied(await inspect(b,sign(b),SECRET,ROUTE,{maxBodyBytes:b.byteLength-1}),
  'VERIFICATION_DENIED');
 denied(await inspect(b,sign(b),SECRET,ROUTE,{maxEvents:1}),
  'VERIFICATION_DENIED');
});
test('QUOTE-16 one composed slot carries selection AND quote without duplication',async()=>{
 const v=composed(await combined(body([button()],[status()])));
 assert.equal(v.length,2);
 assert.equal(v[0].kind,'template_quick_reply');
 assert.equal(v[0].evidence?.kind,'template_quick_reply');
 assert.equal(v[0].quoted_reference?.quoted_provider_message_id,'wamid.QUOTED');
 assert.equal(v[1].quoted_reference,null);
 assert.equal(v[1].kind,'uninterpreted_status');
});
test('QUOTE-17 media and reaction quote overlays do not duplicate slots',async()=>{
 const v=composed(await combined(body([media(),reaction()])));
 assert.equal(v.length,2);
 assert.equal(v[0].kind,'inbound_media_metadata');
 assert.equal(v[1].kind,'incoming_reaction');
 assert.ok(v.every(x=>x.quoted_reference?.quoted_provider_message_id==='wamid.QUOTED'));
 assert.deepEqual(v.map(x=>x.position.item_index),[0,1]);
});
test('QUOTE-18 standalone generic text gets quote without content reconstruction',async()=>{
 const v=composed(await combined(body([text()])));
 assert.equal(v.length,1);
 assert.equal(v[0].kind,'uninterpreted_inbound');
 assert.equal(v[0].evidence,null);
 assert.equal(v[0].quoted_reference?.quoted_provider_message_id,'wamid.QUOTED');
 assert.equal(JSON.stringify(v).includes('Synthetic reply'),false);
});
test('QUOTE-19 malformed context in generic sibling rejects entire composition',async()=>{
 const r=await combined(body([button(),text({id:'bad'},'wamid.BAD')]));
 denyComposite(r,'COMPONENT_DENIED');
});
test('QUOTE-20 no context adds zero extra HMAC, context adds one',async()=>{
 const no=await countVerify(()=>combined(body([text(NO_CONTEXT)])));
 const yes=await countVerify(()=>combined(body([text()])));
 assert.equal(no.count,1);
 assert.equal(yes.count,2);
 assert.equal(composed(no.result as Awaited<ReturnType<typeof compose>>)[0].quoted_reference,null);
 assert.ok(composed(yes.result as Awaited<ReturnType<typeof compose>>)[0].quoted_reference);
});
test('QUOTE-21 context with only forwarded flag keeps generic slot',async()=>{
 const c=composed(await combined(body([text({forwarded:true})])));
 assert.equal(c.length,1);
 assert.equal(c[0].quoted_reference,null);
});
test('QUOTE-22 invalid quoted context denies full mixed-status batch',async()=>{
 const x=body([text({id:'not-a-wamid'})],[status('failed')]);
 denyComposite(await combined(x),'COMPONENT_DENIED');
});
