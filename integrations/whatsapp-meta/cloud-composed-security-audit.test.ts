/**
 * AUDIT: adversarial concurrency and boundedness of the offline composition.
 * All payloads, app secrets, WABA numbers and recipients are synthetic.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {inspectSignedMetaComposedWebhook as inspect}
 from './cloud-composed-observation-handoff.ts';
const SECRET='SYNTHETIC_AUDIT_SECRET_NEVER_PRODUCTION';
const A={waba_id:'123456789012',phone_number_id:'987654321098',revision:9};
const B={waba_id:'999999999999',phone_number_id:'987654321098',revision:10};
const stamp='1761000000';
const text=(i=0)=>({
 from:'5581888800000',id:'wamid.TEXT_'+i,timestamp:stamp,type:'text',
 text:{body:'Synthetic '+i},
});
const button=(i=0)=>({
 from:'5581888800000',id:'wamid.BUTTON_'+i,timestamp:stamp,type:'button',
 button:{payload:'BTN_'+i,text:'Choice'},
});
const status=(i=0,kind='delivered')=>({
 recipient_id:'5581888800000',id:'wamid.STATUS_'+i,status:kind,timestamp:stamp,
});
function payload(messages:unknown[]= [button()],statuses:unknown[]=[],scope=A){
 return {object:'whatsapp_business_account',entry:[{
  id:scope.waba_id,changes:[{field:'messages',value:{
   messaging_product:'whatsapp',
   metadata:{phone_number_id:scope.phone_number_id},
   messages,statuses,
  }}],
 }]};
}
const raw=(v:unknown)=>Buffer.from(JSON.stringify(v),'utf8');
const sig=(v:Uint8Array)=>
 'sha256='+createHmac('sha256',SECRET).update(v).digest('hex');
const run=(v:unknown,route=A,limits?:{maxBodyBytes?:number;maxEvents?:number})=>{
 const b=raw(v);return inspect(b,sig(b),SECRET,route,limits);
};
function accepted(v:Awaited<ReturnType<typeof inspect>>){
 assert.equal(v.decision,'SIGNED_COMPOSED_NOT_DURABLE',JSON.stringify(v));
 if(v.decision!=='SIGNED_COMPOSED_NOT_DURABLE')throw Error('denied');
 assert.equal(v.ack_allowed,false);
 assert.equal(v.s0_write_authorized,false);
 assert.equal(v.exactly_once_guaranteed,false);
 return v.occurrences;
}
function denied(v:Awaited<ReturnType<typeof inspect>>){
 assert.equal(v.decision,'DENIED');
 if(v.decision!=='DENIED')throw Error('accepted');
 assert.deepEqual(v.occurrences,[]);
 assert.equal(v.raw_sha256,null);
 assert.equal(v.send_authorized,false);
 return v.reason;
}
test('AUDIT-01 mismatched entry-time trusted route cannot be legalized by midflight mutation',async()=>{
 const bytes=raw(payload([button()],[],A));
 const scope={...B};
 const task=inspect(bytes,sig(bytes),SECRET,scope);
 Object.assign(scope,A);
 assert.equal(denied(await task),'VERIFICATION_DENIED');
});
test('AUDIT-02 entry-time correct trusted route does not become denied by mutable caller',async()=>{
 const bytes=raw(payload([button()],[],A));
 const scope={...A};
 const task=inspect(bytes,sig(bytes),SECRET,scope);
 Object.assign(scope,B);
 assert.equal(accepted(await task).length,1);
});
test('AUDIT-03 entry-time approved event limit resists post-call downgrade',async()=>{
 const v=payload([button(),text()]);
 const b=raw(v),limits={maxBodyBytes:256*1024,maxEvents:2};
 const promise=inspect(b,sig(b),SECRET,A,limits);
 limits.maxEvents=1;
 assert.equal(accepted(await promise).length,2);
});
test('AUDIT-04 entry-time body ceiling resists post-call downgrade',async()=>{
 const b=raw(payload([button()]));
 const limits={maxBodyBytes:b.byteLength,maxEvents:10};
 const promise=inspect(b,sig(b),SECRET,A,limits);
 limits.maxBodyBytes=1;
 assert.equal(accepted(await promise).length,1);
});
test('AUDIT-05 entry-time narrow event limit is never relaxed by later mutation',async()=>{
 const b=raw(payload([button(),text()]));
 const limits={maxEvents:1};
 const promise=inspect(b,sig(b),SECRET,A,limits);
 limits.maxEvents=100;
 assert.equal(denied(await promise),'VERIFICATION_DENIED');
});
test('AUDIT-06 copy of caller-owned raw view remains authenticated after mutation',async()=>{
 const original=raw(payload([button(),text()]));
 const view=original.subarray(0);
 const task=inspect(view,sig(view),SECRET,A);
 original.fill(0);
 assert.equal(accepted(await task).length,2);
});
test('AUDIT-07 parallel correct and mismatched scope remain isolated',async()=>{
 const [a,b,c]=await Promise.all([
  run(payload([button()],[],A),A),
  run(payload([button()],[],B),A),
  run(payload([button()],[],B),B),
 ]);
 assert.equal(accepted(a).length,1);
 assert.equal(denied(b),'VERIFICATION_DENIED');
 assert.equal(accepted(c).length,1);
});
test('AUDIT-08 maximum 100 events preserve every position without dedupe',async()=>{
 const messages=Array.from({length:50},(_,i)=>i%2?text(i):button(i));
 const statuses=Array.from({length:50},(_,i)=>status(i));
 const v=accepted(await run(payload(messages,statuses)));
 assert.equal(v.length,100);
 assert.equal(new Set(v.map(x=>JSON.stringify(x.position))).size,100);
 assert.equal(v.filter(x=>x.position.array_kind==='messages').length,50);
 assert.equal(v.filter(x=>x.position.array_kind==='statuses').length,50);
});
test('AUDIT-09 event count 101 is denied without any partial observations',async()=>{
 const messages=Array.from({length:101},(_,i)=>text(i));
 assert.equal(denied(await run(payload(messages))),'VERIFICATION_DENIED');
});
test('AUDIT-10 independent changes with duplicate wamid retain individual slots',async()=>{
 const v=payload([button(0)]);
 v.entry[0].changes.push({field:'messages',value:{
  messaging_product:'whatsapp',
  metadata:{phone_number_id:A.phone_number_id},
  messages:[button(0)],statuses:[status(0)],
 }});
 const a=accepted(await run(v));
 assert.equal(a.length,3);
 assert.deepEqual(a.map(x=>[x.position.change_index,x.position.array_kind]),
  [[0,'messages'],[1,'messages'],[1,'statuses']]);
 assert.equal(a[0].provider_message_id,a[1].provider_message_id);
});
test('AUDIT-11 unsafe getter on trusted route never triggers an uncaught exception',async()=>{
 const b=raw(payload());
 const hostile=new Proxy({...A},{get(target,key){
  if(key==='phone_number_id')throw Error('auditor hostile getter');
  return Reflect.get(target,key);
 }});
 assert.equal(denied(await inspect(b,sig(b),SECRET,hostile)),
  'VERIFICATION_DENIED');
});
test('AUDIT-12 exact bounded bytes allowed but one extra byte is rejected',async()=>{
 const b=raw(payload([button()]));
 const one=await inspect(b,sig(b),SECRET,A,{maxBodyBytes:b.byteLength});
 assert.equal(accepted(one).length,1);
 assert.equal(denied(await inspect(b,sig(b),SECRET,A,
  {maxBodyBytes:b.byteLength-1})),'VERIFICATION_DENIED');
});
test('AUDIT-13 invalid trusted policy fails closed, not a successful empty batch',async()=>{
 const b=raw(payload());
 for(const limits of [{maxEvents:0},{maxEvents:-1},
  {maxBodyBytes:0},{maxEvents:1.5}]){
  assert.equal(denied(await inspect(b,sig(b),SECRET,A,limits)),
   'VERIFICATION_DENIED');
 }
});
test('AUDIT-14 different signed body under original signature is rejected',async()=>{
 const a=raw(payload([button(1)])),b=raw(payload([button(2)]));
 assert.equal(denied(await inspect(b,sig(a),SECRET,A)),
  'VERIFICATION_DENIED');
});
