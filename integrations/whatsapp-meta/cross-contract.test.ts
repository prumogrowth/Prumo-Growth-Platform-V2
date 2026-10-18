/** WA-03A laboratory audit of integration seams, with NO production ports. */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { inspectMetaWebhook, type MetaIngressEvent } from './inbound.ts';
import { decideBatchAck } from './durable-receipt.ts';
import { FakeS0Outbox, ScriptedFakeGraph, simulateOfflineDispatch,
  type OfflineCommand, type ScriptedObservation } from './offline-dispatch.ts';
import { FakeMetaStatusReconciler, type CorrelationReference } from './technical-reconciliation.ts';
import type { GraphTextIntent, GraphSendOutcome } from './graph-outbound.ts';
import type { TrustedTemplateScope } from './graph-template.ts';

const secret='LOCAL_FIXTURE_APP_SECRET_NOT_REAL';
const enc=new TextEncoder();
const scope:TrustedTemplateScope={concessionaria_id:'SYN_SHOP_A',canal_id:'SYN_CHANNEL_A',meta_app_ref:'SYN_APP_A',meta_waba_id:'SYN_WABA_A',phone_number_id:'123456789012'};
const intent:GraphTextIntent={contract_version:'meta-s0.v0.1-proposed',intent_id:'IN_A',attempt_id:'ATT_A',correlation_id:'CORR_A',authorized_business_action:'C12',authorized_state_version:5,phone_number_id:scope.phone_number_id,recipient_verified:'5581900000000',text_body:'SOMENTE FICTICIO'};
const command:OfflineCommand={kind:'text',intent,asserted_scope:scope};
const ref:CorrelationReference={app_ref:scope.meta_app_ref,intent_id:intent.intent_id,recipient_verified:intent.recipient_verified,scope};
const GraphAccepted={kind:'http_response' as const,http_status:200,response_json:{messages:[{id:'wamid.SYNTHETIC+PAD='}]}};
const msg=(id:string)=>({id,from:'5581900000000',timestamp:'1792320000',type:'text',text:{body:'DO_NOT_LOG'}});
const status=(kind:string,t='1792320000',dest='5581900000000')=>({id:'wamid.SYNTHETIC+PAD=',recipient_id:dest,timestamp:t,status:kind});
const pack=(m:unknown[]=[],s:unknown[]=[])=>({object:'whatsapp_business_account',entry:[{id:scope.meta_waba_id,changes:[{field:'messages',value:{metadata:{phone_number_id:scope.phone_number_id},messages:m,statuses:s}}]}]});
async function signature(bytes:Uint8Array,key=secret){const cryptoKey=await crypto.subtle.importKey('raw',enc.encode(key),{name:'HMAC',hash:'SHA-256'},false,['sign']);const mac=new Uint8Array(await crypto.subtle.sign('HMAC',cryptoKey,bytes));return 'sha256='+Array.from(mac,n=>n.toString(16).padStart(2,'0')).join('');}
async function parse(payload:unknown,key=secret){const raw=enc.encode(JSON.stringify(payload));return inspectMetaWebhook(raw,await signature(raw,key),secret);}
function dispatch(result: ScriptedObservation = GraphAccepted){const s0=new FakeS0Outbox();s0.upsertCurrent({intent_id:intent.intent_id,attempt_id:intent.attempt_id,correlation_id:intent.correlation_id,authorized_business_action:'C12',current_state_version:5,allowed_now:true,scope,recipient_verified:intent.recipient_verified});const graph=new ScriptedFakeGraph([result]);return {s0,graph,result:simulateOfflineDispatch(command,s0,graph,'v24.0')};}
const successReceipt=(n:number)=>({outcome:'ACCEPTED_DURABLE',commit_state:'COMMITTED',total:n,accepted:n,duplicates:0,quarantined:0});

test('CROSS-01 valid HMAC aggregate: two messages+two statuses; hypothetical 4-item receipt',async()=>{
 const inspected=await parse(pack([msg('wamid.IN1'),msg('wamid.IN2')],[status('delivered'),status('read')]));
 assert.equal(inspected.ok,true);
 if(!inspected.ok)return;
 assert.deepEqual(inspected.events.map(e=>e.event_kind),['inbound_message','inbound_message','status_callback','status_callback']);
 assert.equal(decideBatchAck(inspected.events.length,successReceipt(4)).status,200);
 // The receipt is an artificial fixture: this does NOT attest an S0 commit.
});
test('CROSS-02 body tampering fails before event processing',async()=>{
 const raw=enc.encode(JSON.stringify(pack([msg('wamid.IN1')])));
 const altered=enc.encode(new TextDecoder().decode(raw)+' ');
 const inspected=await inspectMetaWebhook(altered,await signature(raw),secret);
 assert.deepEqual(inspected,{ok:false,failure:{code:'INVALID_SIGNATURE'}});
});
test('CROSS-03 wrong app key prevents a valid-looking body from entering fake state',async()=>{
 const inspected=await parse(pack([msg('wamid.IN1')]),'WRONG_APP_SECRET');
 assert.equal(inspected.ok,false);
 if(!inspected.ok)assert.equal(inspected.failure.code,'INVALID_SIGNATURE');
});
test('CROSS-04 missing and partial transaction receipts never permit ACK',async()=>{
 assert.equal(decideBatchAck(4,{...successReceipt(4),commit_state:'ROLLBACK'}).status,503);
 assert.equal(decideBatchAck(4,{...successReceipt(4),accepted:3}).status,503);
});
test('CROSS-05 signed status before Graph registration remains pending then correlates',async()=>{
 const parsed=await parse(pack([],[status('read')]));assert.equal(parsed.ok,true);if(!parsed.ok)return;
 const reconciliation=new FakeMetaStatusReconciler();
 assert.equal(reconciliation.observeAuthenticatedFixture(parsed.events[0],scope.meta_app_ref).decision,'PENDING_RECONCILIATION');
 const send=dispatch();assert.equal(send.result.observation?.send_state,'API_ACCEPTED');
 assert.equal(reconciliation.registerAcceptedSend(ref,send.result.observation!).pending_correlated,1);
 assert.equal(reconciliation.projectionFor(ref,'wamid.SYNTHETIC+PAD=')?.progress,'READ');
 assert.equal(send.graph.calls,1);
});
test('CROSS-06 two callbacks same wamid+status+second preserved independently',async()=>{
 const parsed=await parse(pack([],[status('delivered'),status('delivered')]));assert.equal(parsed.ok,true);if(!parsed.ok)return;
 const reconciler=new FakeMetaStatusReconciler();
 const send=dispatch().result.observation!;reconciler.registerAcceptedSend(ref,send);
 const a=reconciler.observeAuthenticatedFixture(parsed.events[0],scope.meta_app_ref);
 const b=reconciler.observeAuthenticatedFixture(parsed.events[1],scope.meta_app_ref);
 assert.equal(a.observation_count,1);assert.equal(b.observation_count,2);
 assert.equal(b.possible_repeat,true);
 // Same event characteristics cannot supply a reliable universal event ID.
 assert.equal(parsed.events[0].provider_message_id,parsed.events[1].provider_message_id);
});
test('CROSS-07 late status does not downgrade read or cause commercial effect',async()=>{
 const parsed=await parse(pack([],[status('read','1792320003'),status('sent','1792320001')]));assert.equal(parsed.ok,true);if(!parsed.ok)return;
 const rec=new FakeMetaStatusReconciler();rec.registerAcceptedSend(ref,dispatch().result.observation!);
 for(const e of parsed.events)rec.observeAuthenticatedFixture(e,scope.meta_app_ref);
 assert.equal(rec.projectionFor(ref,'wamid.SYNTHETIC+PAD=')?.progress,'READ');
 assert.equal('commercial_status' in (rec.projectionFor(ref,'wamid.SYNTHETIC+PAD=')||{}),false);
});
test('CROSS-08 signed status for other phone is never attached even if wamid matches',async()=>{
 const parsed=await parse(pack([],[status('read','1792320000','558100000000')]));assert.equal(parsed.ok,true);if(!parsed.ok)return;
 const rec=new FakeMetaStatusReconciler();rec.registerAcceptedSend(ref,dispatch().result.observation!);
 assert.equal(rec.observeAuthenticatedFixture(parsed.events[0],scope.meta_app_ref).decision,'PENDING_RECONCILIATION');
 assert.equal(rec.projectionFor(ref,'wamid.SYNTHETIC+PAD=')?.observation_count,0);
});
test('CROSS-09 timeout without provider ID cannot be linked or automatically resent',()=>{
 const dispatched=dispatch({kind:'transport_error'});
 assert.equal(dispatched.result.observation?.send_state,'UNCERTAIN_EXTERNAL');
 assert.equal(dispatched.result.observation?.provider_message_id,null);
 assert.equal(dispatched.result.retry_automatically,false);
 const r=new FakeMetaStatusReconciler();
 assert.equal(r.registerAcceptedSend(ref,dispatched.result.observation!).decision,'INVALID_REFERENCE');
 assert.equal(simulateOfflineDispatch(command,dispatched.s0,dispatched.graph,'v24.0').reason,'ATTEMPT_ALREADY_RESERVED');
 assert.equal(dispatched.graph.calls,1);
});
test('CROSS-10 forged shop/canal scope cannot query linked projection',()=>{
 const rec=new FakeMetaStatusReconciler();rec.registerAcceptedSend(ref,dispatch().result.observation!);
 for(const k of ['concessionaria_id','canal_id'] as const){
   const crossed:CorrelationReference={...ref,scope:{...ref.scope,[k]:'SYN_FORGED_OTHER'}};
   assert.equal(rec.projectionFor(crossed,'wamid.SYNTHETIC+PAD='),undefined);
 }
});
test('CROSS-11 forged shop cannot claim an already linked message as its own',()=>{
 const rec=new FakeMetaStatusReconciler();const sent=dispatch().result.observation!;
 assert.equal(rec.registerAcceptedSend(ref,sent).decision,'LINKED');
 assert.equal(rec.registerAcceptedSend({...ref,scope:{...ref.scope,concessionaria_id:'SYN_SHOP_B'}},sent).decision,'CONFLICT');
});
test('CROSS-12 parsed inbound messages are not interpreted as delivery callbacks',async()=>{
 const parsed=await parse(pack([msg('wamid.IN1')]));assert.equal(parsed.ok,true);if(!parsed.ok)return;
 const rec=new FakeMetaStatusReconciler();
 assert.equal(rec.observeAuthenticatedFixture(parsed.events[0],scope.meta_app_ref).decision,'REJECTED_EVENT');
 assert.equal(rec.pendingCount,0);
});
test('CROSS-13 internal occurrence ref is distinct from Meta message ID (synthetic only)',async()=>{
 const parsed=await parse(pack([],[status('delivered'),status('delivered')]));assert.equal(parsed.ok,true);if(!parsed.ok)return;
 const occurrences=parsed.events.map(event=>({
   occurrence_ref:crypto.randomUUID(),provider_message_id:event.provider_message_id,
   event_kind:event.event_kind,status:event.provider_kind,
 }));
 assert.equal(occurrences.length,2);
 assert.notEqual(occurrences[0].occurrence_ref,occurrences[1].occurrence_ref);
 assert.equal(occurrences[0].provider_message_id,occurrences[1].provider_message_id);
 assert.equal(occurrences[0].status,occurrences[1].status);
 // The production occurrence must be assigned/retained by a trusted durable ingress service.
});
test('CROSS-14 status+timestamp key collision cannot justify discarding distinct observations',async()=>{
 const parsed=await parse(pack([],[status('delivered'),status('delivered')]));assert.equal(parsed.ok,true);if(!parsed.ok)return;
 const oldFixtureKey=(event:MetaIngressEvent)=>
   JSON.stringify([event.provider_message_id,event.provider_kind,event.provider_timestamp]);
 assert.equal(oldFixtureKey(parsed.events[0]),oldFixtureKey(parsed.events[1]));
 assert.notDeepEqual(parsed.events[0].position,parsed.events[1].position);
 // This is a negative assertion about a lab key; it is NOT a proven Meta dedupe algorithm.
});
