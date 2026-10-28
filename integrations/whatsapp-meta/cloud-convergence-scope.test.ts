/**
 * OFFLINE compatibility audit of PR #36 shared verifier with PR #37 selective
 * composition and PR #39 generic identity guard. Synthetic bodies only.
 * Tests do not send/ACK/persist anything; no real Meta credentials.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {inspectCloudWebhookForHandoff as base} from './cloud-webhook-handoff.ts';
import {inspectSignedMetaComposedWebhook as composed}
 from './cloud-composed-observation-handoff.ts';
import {inspectSignedMetaReactions as reactions}
 from './cloud-reaction-handoff.ts';
import {inspectSignedMetaSelections as selections}
 from './cloud-button-reply-handoff.ts';
import {inspectSignedMetaMediaMetadata as media}
 from './cloud-media-metadata-handoff.ts';
import {inspectSignedMetaUnsupportedMessages as unsupported}
 from './cloud-unsupported-inbound-handoff.ts';
import {inspectSignedMetaFailedStatusErrors as failedStatuses}
 from './cloud-failed-status-errors-handoff.ts';

const SECRET='CONVERGENCE_SYNTHETIC_NOT_META';
const A={waba_id:'123456789012',phone_number_id:'987654321098',revision:7};
const B={waba_id:'999999999999',phone_number_id:'987654321098',revision:8};
const TS='1761000000';
const msg=(type:string,id:string,rest:Record<string,unknown>={})=>({
 from:'5581888800000',id,timestamp:TS,type,...rest,
});
const kind={
 reaction:()=>msg('reaction','wamid.R',{
  reaction:{message_id:'wamid.OUT',emoji:'👍'},
 }),
 button:()=>msg('button','wamid.B',{
  button:{payload:'CHOOSE_ONE',text:'Escolher'},
 }),
 image:()=>msg('image','wamid.M',{image:{id:'99887766554433'}}),
 unsupported:()=>msg('unsupported','wamid.U',{
  errors:[{code:131051,title:'Unsupported'}],
 }),
 text:()=>msg('text','wamid.T',{text:{body:'Only synthetic'}}),
};
const state=(status:'sent'|'failed'='failed')=>({
 id:'wamid.OUT',recipient_id:'5581888800000',timestamp:TS,status,
 ...(status==='failed'?{errors:[{code:131026}]}:{}),
});
const envelope=(messages:unknown[],statuses:unknown[]=[],route=A)=>({
 object:'whatsapp_business_account',entry:[{id:route.waba_id,
  changes:[{field:'messages',value:{
   messaging_product:'whatsapp',
   metadata:{phone_number_id:route.phone_number_id},messages,statuses,
  }}]}],
});
const bytes=(x:unknown)=>Buffer.from(JSON.stringify(x),'utf8');
const signature=(b:Uint8Array)=>
 'sha256='+createHmac('sha256',SECRET).update(b).digest('hex');
const validate=(r:unknown)=>{
 const x=r as Record<string,unknown>;
 for(const f of ['ack_allowed','send_authorized','delivery_confirmed',
   's0_write_authorized','production_authorized'])
  assert.equal(x[f],false,f);
};
test('CONVERGE-01 raw base rejects originally wrong route even if caller retargets',async()=>{
 const b=bytes(envelope([kind.text()]));
 const route={...B};
 const task=base(b,signature(b),SECRET,route);
 Object.assign(route,A);
 const result=await task;
 validate(result);
 assert.equal(result.outcome,'DENIED');
 assert.equal(result.raw_sha256,null);
});
test('CONVERGE-02 raw base accepts originally correct route despite caller mutation',async()=>{
 const b=bytes(envelope([kind.text()]));
 const route={...A};
 const task=base(b,signature(b),SECRET,route);
 Object.assign(route,B);
 const result=await task;
 validate(result);
 assert.equal(result.outcome,'AUTHENTICATED_NOT_DURABLE');
 assert.equal(result.route_revision,7);
});
test('CONVERGE-03 base route revision is frozen before awaited HMAC',async()=>{
 const b=bytes(envelope([kind.text()]));
 const route={...A};
 const task=base(b,signature(b),SECRET,route);
 route.revision=88;
 const result=await task;
 validate(result);
 assert.equal(result.outcome,'AUTHENTICATED_NOT_DURABLE');
 assert.equal(result.route_revision,7);
});
test('CONVERGE-04 base invalid getter fails closed without thrown secrets',async()=>{
 const b=bytes(envelope([kind.text()]));
 const route=new Proxy({...A},{get(o,k){
  if(k==='phone_number_id')throw Error('synthetic getter trap');
  return Reflect.get(o,k);
 }});
 const result=await base(b,signature(b),SECRET,route);
 validate(result);
 assert.equal(result.outcome,'DENIED');
 assert.equal(result.raw_sha256,null);
});
test('CONVERGE-05 direct reaction reader cannot be retargeted after invocation',async()=>{
 const b=bytes(envelope([kind.reaction()]));
 const route={...B};
 const task=reactions(b,signature(b),SECRET,route);
 Object.assign(route,A);
 const result=await task;validate(result);
 assert.equal(result.decision,'DENIED');
});
test('CONVERGE-06 direct selection reader retains entry-time correct scope',async()=>{
 const b=bytes(envelope([kind.button()]));
 const route={...A};
 const task=selections(b,signature(b),SECRET,route);
 Object.assign(route,B);
 const result=await task;validate(result);
 assert.equal(result.decision,'SIGNED_CANDIDATES_NOT_DURABLE');
});
test('CONVERGE-07 direct media reader retains entry-time wrong scope',async()=>{
 const b=bytes(envelope([kind.image()]));
 const route={...B};
 const task=media(b,signature(b),SECRET,route);
 Object.assign(route,A);
 const result=await task;validate(result);
 assert.equal(result.decision,'DENIED');
});
test('CONVERGE-08 direct unsupported reader retains entry-time correct scope',async()=>{
 const b=bytes(envelope([kind.unsupported()]));
 const route={...A};
 const task=unsupported(b,signature(b),SECRET,route);
 Object.assign(route,B);
 const result=await task;validate(result);
 assert.equal(result.decision,'SIGNED_UNSUPPORTED_NOT_DURABLE');
});
test('CONVERGE-09 direct failed-status reader cannot legalize wrong initial scope',async()=>{
 const b=bytes(envelope([],[state()]));
 const route={...B};
 const task=failedStatuses(b,signature(b),SECRET,route);
 Object.assign(route,A);
 const result=await task;validate(result);
 assert.equal(result.decision,'DENIED');
});
test('CONVERGE-10 selective composition retains PR #37 behavior with shared fix',async()=>{
 const b=bytes(envelope([kind.text(),kind.reaction(),kind.button()],[state()]));
 const r=await composed(b,signature(b),SECRET,{...A});validate(r);
 assert.equal(r.decision,'SIGNED_COMPOSED_NOT_DURABLE');
 if(r.decision!=='SIGNED_COMPOSED_NOT_DURABLE')return;
 assert.deepEqual(r.occurrences.map(e=>e.kind),[
  'uninterpreted_inbound','incoming_reaction','template_quick_reply',
  'provider_reported_failed_status_errors',
 ]);
});
test('CONVERGE-11 PR #39 generic identifier deny survives shared verifier repair',async()=>{
 const b=bytes(envelope([kind.button(),msg('text','NOT_A_WAMID')]));
 const r=await composed(b,signature(b),SECRET,{...A});validate(r);
 assert.equal(r.decision,'DENIED');
 if(r.decision==='DENIED'){
  assert.equal(r.reason,'INVALID_TECHNICAL_IDENTIFIERS');
  assert.deepEqual(r.occurrences,[]);
 }
});
test('CONVERGE-12 byte changes after call cannot alter signed base and composition',async()=>{
 const b=bytes(envelope([kind.text(),kind.reaction()]));
 const s=signature(b);
 const p1=base(b,s,SECRET,{...A});
 const p2=composed(b,s,SECRET,{...A});
 b.fill(0);
 const [a,c]=await Promise.all([p1,p2]);
 validate(a);validate(c);
 assert.equal(a.outcome,'AUTHENTICATED_NOT_DURABLE');
 assert.equal(c.decision,'SIGNED_COMPOSED_NOT_DURABLE');
});
