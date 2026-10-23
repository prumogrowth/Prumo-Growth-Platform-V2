/** WA32 signed HMAC -> physical PG17 WA29/31 claims -> pure fake S0 port.
 * HMAC uses made-up secrets; SQL rows are privileged lab exports, not S0 auth.
 * No HTTP ACK, Graph POST, retry, S0 inserts, tokens or real recipient.
 */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {inspectWa32SignedStatusForensicFixture as inspect,
 type Wa32AttemptLookup,type Wa32S0FixturePort} from '../wa32-signed-status-s0-forensic-bridge.ts';
import type {TrustedRoutingPorts} from '../routed-webhook.ts';
import type {TrustedMetaRegistry,TrustedMetaScope} from '../credential-routing.ts';

const file=process.argv[2];
assert.equal(process.argv.length,3);
const bytes=readFileSync(file,'utf8');
assert.ok(bytes.length>100&&bytes.length<6000);
const root=JSON.parse(bytes);
assert.deepEqual(Object.keys(root).sort(),['absent','active_b','counts','revoked_a']);
const A=root.revoked_a as Wa32AttemptLookup,B=root.active_b as Wa32AttemptLookup;
const BASE=1792320000000;
const SECRET_A='WA32_PG17_FAKE_SECRET_A';
const SECRET_B='WA32_PG17_FAKE_SECRET_B';
const apps=[
 {app_ref:'WA32_LAB_APP_A',route_ref:'WA32_LAB_ROUTE_A',
  concessionaria_id:'shop_A',revision:7,active:true,
  valid_from_ms:BASE-1000,valid_until_ms:BASE+1000,
  secret_slots:{get_verify_token:'WA32_LAB_A_GET',
   post_app_secret:'WA32_LAB_A_POST',graph_access_token:'WA32_LAB_A_GRAPH'},
  channels:[{canal_id:'WA32_LAB_CHANNEL_A',waba_id:'111111',
   phone_number_id:'1234567890',active:true}]},
 {app_ref:'WA32_LAB_APP_B',route_ref:'WA32_LAB_ROUTE_B',
  concessionaria_id:'shop_B',revision:7,active:true,
  valid_from_ms:BASE-1000,valid_until_ms:BASE+1000,
  secret_slots:{get_verify_token:'WA32_LAB_B_GET',
   post_app_secret:'WA32_LAB_B_POST',graph_access_token:'WA32_LAB_B_GRAPH'},
  channels:[{canal_id:'WA32_LAB_CHANNEL_B',waba_id:'222222',
   phone_number_id:'9876543210',active:true}]},
] as const;
let registry:TrustedMetaRegistry={contract_version:'wa-meta-credential-routing.v0.1-proposed',apps};
const routing:TrustedRoutingPorts={
 currentRegistry:async()=>registry,
 resolveSecret:async slot=>slot==='WA32_LAB_A_POST'?SECRET_A:
   slot==='WA32_LAB_B_POST'?SECRET_B:undefined,
 nowMs:()=>BASE,
};
async function signed(row:Wa32AttemptLookup,appIndex:number,secret:string){
 const entry={id:row.waba_id,changes:[{field:'messages',
   value:{metadata:{phone_number_id:row.phone_number_id},statuses:[{
    id:row.provider_message_id,recipient_id:row.recipient_verified,
    status:'delivered',timestamp:'1792320000',
   }]}}]};
 const raw_body=new TextEncoder().encode(JSON.stringify({
  object:'whatsapp_business_account',entry:[entry],
 }));
 const key=await crypto.subtle.importKey('raw',new TextEncoder().encode(secret),
  {name:'HMAC',hash:'SHA-256'},false,['sign']);
 const mac=new Uint8Array(await crypto.subtle.sign('HMAC',key,raw_body));
 return {route:{route_ref:apps[appIndex].route_ref,
   expected_revision:apps[appIndex].revision},
  raw_body,signature_header:'sha256'+
   '='+Array.from(mac,x=>x.toString(16).padStart(2,'0')).join(''),
 };
}
const port=(list:readonly Wa32AttemptLookup[] | ((phase:'LOOKUP'|'RECHECK')=>readonly Wa32AttemptLookup[])):Wa32S0FixturePort=>
 ({lookupExactAttempt:async(_s:Readonly<TrustedMetaScope>,_w:string,phase)=>
   typeof list==='function'?list(phase):list});
function assertSafe(result:Awaited<ReturnType<typeof inspect>>){
 for(const k of ['send_authorized','retry_external','ack_allowed',
  'production_authorized','delivery_confirmed',
  'definitive_failure_count_increment','case_transition_authorized'] as const)
  assert.equal(result[k],false);
 assert.equal(JSON.stringify(result).includes('wamid.'),false);
}
const check=async(request:Awaited<ReturnType<typeof signed>>,
 s0:Wa32S0FixturePort,decision:string)=>{
 const r=await inspect(request,routing,s0);
 assert.equal(r.decision,decision);
 assertSafe(r);return r;
};
const pass=(n:number)=>process.stdout.write(
 'WA32-'+String(n).padStart(2,'0')+' PASS\n');
assert.equal(A.case_ref,'case31_hist');
assert.equal(A.claim_state,'LAB_INVALIDATED');
assert.ok(A.binding_revision>1);pass(1);
assert.equal(B.case_ref,'case31_b');
assert.equal(B.claim_state,'LAB_CLAIMED');pass(2);
assert.equal(root.absent,null);
assert.deepEqual(root.counts,{a_claims:1,b_claims:1});pass(3);

const reqA=await signed(A,0,SECRET_A),reqB=await signed(B,1,SECRET_B);
const a=await check(reqA,port([A]),'LAB_FORENSIC_SCOPED');
assert.equal(a.scoped_event_count,1);
assert.equal(a.invalidated_attempts,1);pass(4);
const b=await check(reqB,port([B]),'LAB_FORENSIC_SCOPED');
assert.equal(b.invalidated_attempts,0);pass(5);
await check(reqA,port([B]),'LAB_S0_BINDING_DENIED');pass(6);
await check(reqB,port([A]),'LAB_S0_BINDING_DENIED');pass(7);
const noBinding=port([]);
await check(reqA,noBinding,'LAB_S0_BINDING_DENIED');pass(8);
await check(reqA,port([A,A]),'LAB_S0_BINDING_DENIED');pass(9);
await check(reqA,port([{...A,recipient_verified:'5581900000001'}]),
 'LAB_S0_BINDING_DENIED');pass(10);
await check(reqA,port([{...A,provider_message_id:'wamid.UNRELATED'}]),
 'LAB_S0_BINDING_DENIED');pass(11);
await check(reqA,port(phase=>phase==='LOOKUP'?[A]:[{
 ...A,binding_revision:A.binding_revision+1,
}]),'LAB_STALE_OR_CHANGED');pass(12);
const invalidHmac=await signed(A,0,SECRET_B);
await check(invalidHmac,port([A]),'LAB_ROUTING_DENIED');pass(13);
const crossRoute={...reqA,route:{...reqB.route}};
await check(crossRoute,port([A]),'LAB_ROUTING_DENIED');pass(14);
const altered={...reqA,raw_body:Uint8Array.from(reqA.raw_body)};
altered.raw_body[altered.raw_body.length-2]^=1;
await check(altered,port([A]),'LAB_ROUTING_DENIED');pass(15);
registry={contract_version:registry.contract_version,apps:[{
 ...apps[0],active:false,
},apps[1]]};
await check(reqA,port([A]),'LAB_ROUTING_DENIED');pass(16);
registry={contract_version:'wa-meta-credential-routing.v0.1-proposed',apps};
assert.equal(a.ack_allowed,false);
assert.equal(a.send_authorized,false);
assert.equal(a.retry_external,false);
assert.equal(a.case_transition_authorized,false);pass(17);
assert.equal(JSON.stringify(a).includes('shop_A'),false);
assert.equal(JSON.stringify(a).includes(A.attempt_ref),false);pass(18);
process.stdout.write('PASS WA32: 18 PG17-to-signed-TypeScript checks; no real S0 authentication\n');
