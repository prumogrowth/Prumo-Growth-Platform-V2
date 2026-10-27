/**
 * AUDIT — count actual WebCrypto HMAC verifications, not guessed timings.
 * Demonstrate snapshot isolation of caller-owned trusted configuration.
 * Synthetic callbacks only. No Graph, token, S0, HTTP endpoint or ACK.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {inspectSignedMetaComposedWebhook as inspect}
 from './cloud-composed-observation-handoff.ts';

const SECRET='AUDIT_TEST_SECRET_NO_PRODUCTION_KEY';
const ROUTE={waba_id:'123456789012',phone_number_id:'987654321098',revision:4};
const T='1761000000';
const msg=(type:string,id:string,extra:Record<string,unknown>={})=>({
 type,id,from:'5581888800000',timestamp:T,...extra,
});
const text=()=>msg('text','wamid.T',{text:{body:'offline'}});
const button=()=>msg('button','wamid.B',{button:{text:'Ok',payload:'OK'}});
const list=()=>msg('interactive','wamid.L',{interactive:{
 type:'list_reply',list_reply:{id:'LIST_1',title:'Teste'}}});
const reaction=()=>msg('reaction','wamid.R',{reaction:{
 message_id:'wamid.OUT',emoji:'👍'}});
const media=()=>msg('image','wamid.M',{image:{
 id:'99998888777766',mime_type:'image/jpeg',
 sha256:Buffer.alloc(32,1).toString('base64')}});
const unsupported=()=>msg('unsupported','wamid.U',{
 errors:[{code:131051,title:'Unsupported message type'}]});
const status=(kind:string,id='wamid.OUT')=>({
 id,recipient_id:'5581888800000',timestamp:T,status:kind,
});
const failed=()=>({...status('failed'),
 errors:[{code:131026,title:'Message undeliverable'}]});
const bodyFor=(messages:unknown[]=[text()],statuses:unknown[]=[])=>({
 object:'whatsapp_business_account',entry:[{id:ROUTE.waba_id,
 changes:[{field:'messages',value:{
  messaging_product:'whatsapp',
  metadata:{phone_number_id:ROUTE.phone_number_id},
  messages,statuses}}]}],
});
const bytes=(v:unknown)=>Buffer.from(JSON.stringify(v),'utf8');
const signature=(b:Uint8Array)=>
 'sha256='+createHmac('sha256',SECRET).update(b).digest('hex');
const run=(v:unknown,route={...ROUTE},limits?:{maxEvents?:number;maxBodyBytes?:number})=>{
 const b=bytes(v);return inspect(b,signature(b),SECRET,route,limits);
};
/** Count WebCrypto verify calls; restore method even when a test fails. */
async function countHmac(task:()=>Promise<unknown>){
 const subtle=crypto.subtle;
 const original=subtle.verify;
 let count=0;
 (subtle as any).verify=function(...args:unknown[]){
  count++;
  return Reflect.apply(original,subtle,args);
 };
 try{return {result:await task() as Awaited<ReturnType<typeof inspect>>,count};}
 finally{(subtle as any).verify=original;}
}
const valid=(result:Awaited<ReturnType<typeof inspect>>)=>{
 assert.equal(result.decision,'SIGNED_COMPOSED_NOT_DURABLE');
 if(result.decision!=='SIGNED_COMPOSED_NOT_DURABLE')throw Error('unexpected deny');
 assert.equal(result.ack_allowed,false);
 assert.equal(result.send_authorized,false);
 assert.equal(result.s0_write_authorized,false);
 assert.equal(result.exactly_once_guaranteed,false);
 return result;
};
const denied=(result:Awaited<ReturnType<typeof inspect>>)=>{
 assert.equal(result.decision,'DENIED');
 assert.deepEqual(result.occurrences,[]);
 assert.equal(result.raw_sha256,null);
 assert.equal(result.ack_allowed,false);
};

test('AUDIT-01 generic text runs only the mandatory base HMAC',async()=>{
 const x=await countHmac(()=>run(bodyFor([text()])));
 assert.equal(x.count,1);
 assert.equal(valid(x.result).occurrences[0].kind,'uninterpreted_inbound');
});
test('AUDIT-02 sent/read statuses call status guard plus base (two HMAC)',async()=>{
 const x=await countHmac(()=>run(bodyFor([],[
  status('sent'),status('delivered'),status('read')])));
 assert.equal(x.count,2);
 assert.equal(valid(x.result).occurrences.length,3);
});
test('AUDIT-03 button only invokes selection inspector and base',async()=>{
 const x=await countHmac(()=>run(bodyFor([button()])));
 assert.equal(x.count,2);
 assert.equal(valid(x.result).occurrences[0].kind,'template_quick_reply');
});
test('AUDIT-04 interactive list invokes selection inspector and base',async()=>{
 const x=await countHmac(()=>run(bodyFor([list()])));
 assert.equal(x.count,2);
 assert.equal(valid(x.result).occurrences[0].kind,'interactive_list_reply');
});
test('AUDIT-05 reaction only invokes reaction inspector and base',async()=>{
 const x=await countHmac(()=>run(bodyFor([reaction()])));
 assert.equal(x.count,2);
 assert.equal(valid(x.result).occurrences[0].kind,'incoming_reaction');
});
test('AUDIT-06 media only invokes media inspector and base',async()=>{
 const x=await countHmac(()=>run(bodyFor([media()])));
 assert.equal(x.count,2);
 assert.equal(valid(x.result).occurrences[0].kind,'inbound_media_metadata');
});
test('AUDIT-07 unsupported only invokes unsupported inspector and base',async()=>{
 const x=await countHmac(()=>run(bodyFor([unsupported()])));
 assert.equal(x.count,2);
 assert.equal(valid(x.result).occurrences[0].kind,'incoming_unsupported_message');
});
test('AUDIT-08 failed status only invokes failed inspector and base',async()=>{
 const x=await countHmac(()=>run(bodyFor([],[failed()])));
 assert.equal(x.count,2);
 assert.equal(valid(x.result).occurrences[0].kind,'provider_reported_failed_status_errors');
});
test('AUDIT-09 fully heterogeneous batch still executes all six authenticated passes',async()=>{
 const x=await countHmac(()=>run(bodyFor([
  button(),reaction(),media(),unsupported()],[failed()])));
 assert.equal(x.count,6);
 assert.equal(valid(x.result).occurrences.length,5);
});
test('AUDIT-10 partial mixed batch runs only relevant guards',async()=>{
 const x=await countHmac(()=>run(bodyFor([text(),reaction()],
  [status('delivered')])));
 assert.equal(x.count,3);
 assert.equal(valid(x.result).occurrences.length,3);
});
test('AUDIT-11 invalid progress-status errors must still be rejected by status guard',async()=>{
 const x=await countHmac(()=>run(bodyFor([],[{
  ...status('read'),errors:[{code:131026}],
 }])));
 assert.equal(x.count,2);
 denied(x.result);
});
test('AUDIT-12 unknown interactive variant is never downgraded to generic',async()=>{
 const x=await countHmac(()=>run(bodyFor([msg('interactive','wamid.BAD',{
  interactive:{type:'catalog_reply',catalog_reply:{id:'bad'}},
 })])));
 assert.equal(x.count,2);
 denied(x.result);
});
test('AUDIT-13 caller mutation of WABA/phone after invocation cannot change scope',async()=>{
 const scope={...ROUTE},v=bodyFor([reaction()]),b=bytes(v);
 const task=inspect(b,signature(b),SECRET,scope);
 scope.waba_id='999999999999';
 scope.phone_number_id='999999999999';
 const o=valid(await task);
 assert.equal(o.occurrences[0].waba_id,ROUTE.waba_id);
 assert.equal(o.occurrences[0].phone_number_id,ROUTE.phone_number_id);
});
test('AUDIT-14 caller mutation of route revision does not rewrite provenance',async()=>{
 const scope={...ROUTE},v=bodyFor([text()]),b=bytes(v);
 const task=inspect(b,signature(b),SECRET,scope);
 scope.revision=99;
 assert.equal(valid(await task).route_revision,ROUTE.revision);
});
test('AUDIT-15 caller mutation of maxEvents mid-HMAC does not change guards',async()=>{
 const limits={maxEvents:1,maxBodyBytes:256*1024};
 const v=bodyFor([reaction()]),b=bytes(v);
 const task=inspect(b,signature(b),SECRET,{...ROUTE},limits);
 limits.maxEvents=0;
 limits.maxBodyBytes=1;
 const o=valid(await task);
 assert.equal(o.occurrences.length,1);
});
test('AUDIT-16 caller byte mutation remains isolated under selective dispatch',async()=>{
 const b=bytes(bodyFor([text(),reaction()]));
 const x=await countHmac(async()=>{
  const task=inspect(b,signature(b),SECRET,{...ROUTE});
  b.fill(0);
  return task;
 });
 assert.equal(x.count,2);
 const r=valid(x.result);
 assert.deepEqual(r.occurrences.map(e=>e.kind),
  ['uninterpreted_inbound','incoming_reaction']);
});

test('AUDIT-17 a full 100-generic-event batch needs one HMAC',async()=>{
 const events=Array.from({length:100},(_,i)=>msg('text','wamid.T_'+i,{
  text:{body:'offline'}}));
 const x=await countHmac(()=>run(bodyFor(events)));
 assert.equal(x.count,1);
 const o=valid(x.result);
 assert.equal(o.occurrences.length,100);
 assert.ok(o.occurrences.every(e=>e.kind==='uninterpreted_inbound'));
 assert.equal(new Set(o.occurrences.map(e=>JSON.stringify(e.position))).size,100);
});
test('AUDIT-18 a full 100-reaction-event batch verifies twice, not 101 times',async()=>{
 const events=Array.from({length:100},(_,i)=>msg('reaction','wamid.R_'+i,{
  reaction:{message_id:'wamid.ORIGINAL',emoji:'👍'}}));
 const x=await countHmac(()=>run(bodyFor(events)));
 assert.equal(x.count,2);
 assert.equal(valid(x.result).occurrences.length,100);
 assert.equal(x.result.deduplicated,false);
});
test('AUDIT-19 full 100-event mixed-kind envelope retains all six guards',async()=>{
 const ordinary=Array.from({length:95},(_,i)=>msg('text','wamid.T_'+i,{
  text:{body:'inert'}}));
 const x=await countHmac(()=>run(bodyFor([
  ...ordinary,button(),reaction(),media(),unsupported()],[failed()])));
 assert.equal(x.count,6);
 const o=valid(x.result);
 assert.equal(o.occurrences.length,100);
 assert.equal(o.occurrences[95].kind,'template_quick_reply');
 assert.equal(o.occurrences[99].kind,'provider_reported_failed_status_errors');
});
test('AUDIT-20 event-cap overflow blocks signed batch before specialist work',async()=>{
 const events=Array.from({length:101},(_,i)=>msg('text','wamid.T_'+i,{
  text:{body:'inert'}}));
 const x=await countHmac(()=>run(bodyFor(events)));
 assert.equal(x.count,1);
 denied(x.result);
});
