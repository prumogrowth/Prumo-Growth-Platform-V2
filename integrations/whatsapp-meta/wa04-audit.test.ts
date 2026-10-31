import { test } from 'node:test';
import assert from 'node:assert/strict';
import { planMetaLifecycleTransition, type LifecycleProposalRequest } from './credential-lifecycle.ts';
import { selectMetaCredential, resolveSignedMetaChannel, type TrustedMetaRegistry } from './credential-routing.ts';
import { inspectRoutedMetaPost, inspectRoutedMetaGet, type TrustedRoutingPorts } from './routed-webhook.ts';
import { inspectMetaVerifyGet } from './verify-get.ts';
import { decideBatchAck } from './durable-receipt.ts';
import { technicalKeyHint } from './technical-keys.ts';
import type { MetaIngressEvent } from './inbound.ts';
const now = 1792320000000;
const appA={app_ref:'AUDIT_A',route_ref:'ROUTE_A',concessionaria_id:'SHOP_A',active:true,
  revision:1,valid_from_ms:now-100,valid_until_ms:now+100,
  secret_slots:{get_verify_token:'AUDIT_A_VERIFY',post_app_secret:'AUDIT_A_HMAC',graph_access_token:'AUDIT_A_GRAPH'},
  channels:[{canal_id:'CH_A',waba_id:'WABA_A',phone_number_id:'1234567890',active:true}]};
const appB={...appA,app_ref:'AUDIT_B',route_ref:'ROUTE_B',concessionaria_id:'SHOP_B',
 secret_slots:{get_verify_token:'AUDIT_B_VERIFY',post_app_secret:'AUDIT_B_HMAC',graph_access_token:'AUDIT_B_GRAPH'},
 channels:[{canal_id:'CH_B',waba_id:'WABA_B',phone_number_id:'9999999990',active:true}]};
const reg:TrustedMetaRegistry={contract_version:'wa-meta-credential-routing.v0.1-proposed',apps:[appA,appB]};
const req={app_ref:'AUDIT_A',concessionaria_id:'SHOP_A',expected_revision:1,at_ms:now,operation_ref:'AUDIT_OP_1'};
const slotA='FAKE_POST_SECRET_A';
const mkPorts=(registry:TrustedMetaRegistry, requested:string[]=[]):TrustedRoutingPorts=>({
 currentRegistry:()=>registry,
 resolveSecret:(name)=>{requested.push(name);return name==='AUDIT_A_HMAC'?slotA:'FAKE_OTHER';},
 nowMs:()=>now,
});
const payload=new TextEncoder().encode(JSON.stringify({object:'whatsapp_business_account',entry:[{
 id:'WABA_A',changes:[{field:'messages',value:{metadata:{phone_number_id:'1234567890'},
 messages:[{id:'wamid.FAKE',from:'5581900000000',type:'text',timestamp:'1792320000'}]}}]}]}));
const sign=async()=>{const key=await crypto.subtle.importKey('raw',new TextEncoder().encode(slotA),{name:'HMAC',hash:'SHA-256'},false,['sign']);const mac=new Uint8Array(await crypto.subtle.sign('HMAC',key,payload));return 'sha256='+Array.from(mac,b=>b.toString(16).padStart(2,'0')).join('')};
const post=(registry:TrustedMetaRegistry,slots:string[]=[])=>(async()=>inspectRoutedMetaPost({raw_body:payload,
 signature_header:await sign(),route:{route_ref:'ROUTE_A',expected_revision:registry.apps[0]?.revision ?? 1}},mkPorts(registry,slots)))();
const tryProposal=(registry:TrustedMetaRegistry, action:LifecycleProposalRequest)=>(planMetaLifecycleTransition(registry,action));

test('WA-AUD-01 malformed registry apps object returns denial, never throws',()=>{
 const bad={...reg,apps:{} as unknown as TrustedMetaRegistry['apps']};
 assert.doesNotThrow(()=>tryProposal(bad,{...req,action:'REVOKE_APP'}));
 assert.deepEqual(tryProposal(bad,{...req,action:'REVOKE_APP'}),{ok:false,production_authorized:false,reason:'REGISTRY_OR_APP_DENIED'});
});
test('WA-AUD-02 noncloneable additional property fails closed without throwing',()=>{
 const bad={...reg,apps:[{...appA,uncloneable:()=>42},appB]};
 assert.doesNotThrow(()=>tryProposal(bad,{...req,action:'REVOKE_APP'}));
 assert.equal(tryProposal(bad,{...req,action:'REVOKE_APP'}).ok,false);
});
test('WA-AUD-03 revocation proposal blocks GET and POST routing in candidate only',async()=>{
 const plan=tryProposal(reg,{...req,action:'REVOKE_APP'});assert.equal(plan.ok,true);if(!plan.ok)return;
 const attempted:string[]=[];
 const result=await post(plan.candidate_registry,attempted);
 assert.equal(result.ok,false);assert.deepEqual(attempted,[]);
 const get=await inspectRoutedMetaGet({raw_query:'hub.mode=subscribe&hub.verify_token=fake&hub.challenge=42',
 route:{route_ref:'ROUTE_A',expected_revision:2}},mkPorts(plan.candidate_registry));
 assert.equal(get.ok,false);
 assert.equal(selectMetaCredential(reg,{purpose:'POST_APP_SECRET',trusted_route_ref:'ROUTE_A',expected_revision:1,at_ms:now}).ok,true);
});
test('WA-AUD-04 staged rotation proposal never silently reactivates an App',async()=>{
 const rotated={get_verify_token:'NEXT_A_VERIFY',post_app_secret:'NEXT_A_HMAC',graph_access_token:'NEXT_A_GRAPH'};
 const plan=tryProposal(reg,{...req,action:'STAGE_ROTATION',next_secret_slots:rotated});
 assert.equal(plan.ok,true);if(!plan.ok)return;
 assert.equal(plan.external_token_verification_pending,true);
 assert.equal(plan.candidate_registry.apps[0].active,false);
 assert.equal((await post(plan.candidate_registry)).ok,false);
});
test('WA-AUD-05 revoked channel fails scoped binding and signed POST, unchanged other store',async()=>{
 const plan=tryProposal(reg,{...req,action:'REVOKE_CHANNEL',canal_id:'CH_A'});assert.equal(plan.ok,true);if(!plan.ok)return;
 assert.equal(resolveSignedMetaChannel(plan.candidate_registry,{trusted_route_ref:'ROUTE_A',authenticated_app_ref:'AUDIT_A',waba_id:'WABA_A',phone_number_id:'1234567890',at_ms:now,expected_revision:2}).ok,false);
 const response=await post(plan.candidate_registry);
 assert.equal(response.ok,false);if(!response.ok)assert.equal(response.reason,'CHANNEL_DENIED');
 assert.deepEqual(plan.candidate_registry.apps[1],reg.apps[1]);
});
test('WA-AUD-06 duplicate sender across Apps invalidates routing globally',()=>{
 const conflict:TrustedMetaRegistry={...reg,apps:[appA,{...appB,channels:[{...appB.channels[0],phone_number_id:'1234567890'}]}]};
 assert.equal(selectMetaCredential(conflict,{purpose:'POST_APP_SECRET',trusted_route_ref:'ROUTE_A',at_ms:now,expected_revision:1}).ok,false);
});
test('WA-AUD-07 GET rejects unexpected query parameters even with matching fixture token',async()=>{
 const q='hub.mode=subscribe&hub.verify_token=x&hub.challenge=42&canal_id=OTHER';
 assert.equal((await inspectMetaVerifyGet(q,'x')).status,403);
});
test('WA-AUD-08 meta status hint does not claim automatic deduplication',async()=>{
 const event:MetaIngressEvent={source:'meta_whatsapp',event_kind:'status_callback',waba_id:'WABA_A',phone_number_id:'1234567890',provider_message_id:'wamid.OUT',provider_timestamp:'2026-10-18T13:00:00.000Z',participant_identifier:'5581900000000',provider_kind:'read',position:{array_kind:'statuses',entry_index:0,change_index:0,item_index:0}};
 const result=await technicalKeyHint(event,'AUDIT_A');assert.equal(result.safe_to_auto_dedupe,false);
});
test('WA-AUD-09 receipt coercion cannot return ACK',()=>{
 const result=decideBatchAck(1,{outcome:{toString:()=> 'ACCEPTED_DURABLE'},commit_state:'COMMITTED',total:1,accepted:1,duplicates:0,quarantined:0});assert.equal(result.ack_allowed,false);
});
test('WA-AUD-10 all results remain offline and do not authorize operation',async()=>{
 const r=await post(reg);assert.equal(r.ok,true);
 assert.equal(r.ack_allowed,false);assert.equal(r.production_authorized,false);
 const proposal=tryProposal(reg,{...req,action:'REVOKE_CHANNEL',canal_id:'CH_A'});
 assert.equal(proposal.production_authorized,false);
});
