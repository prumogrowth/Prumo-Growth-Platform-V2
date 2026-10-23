/**
 * WA35 PG17 integration test ONLY. Fake Meta HMAC -> WA35 ticket -> WA34
 * internal HMAC verification -> privileged psql WA34 nonce consume.
 * This runner deliberately simulates the *missing* S0 service boundary.
 * SQL receives plain arguments, NOT a verified signature or GoTrue principal.
 */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {makeWa35SignedHandoffFixture as make}
 from '../wa35-signed-ingress-handoff-fixture.ts';
import {verifyWa34SyntheticFixture,type Wa34Scope}
 from '../wa34-service-forensic-handoff.ts';
import type {TrustedMetaRegistry} from '../credential-routing.ts';
import type {TrustedRoutingPorts} from '../routed-webhook.ts';
import type {Wa32AttemptLookup} from '../wa32-signed-status-s0-forensic-bridge.ts';

const dsn=process.env.PRUMO_TEST_DATABASE_URL||'';
const u=new URL(dsn);
assert.equal(u.protocol,'postgresql:');
assert.equal(u.hostname,'127.0.0.1');assert.equal(u.port,'5432');
assert.equal(u.username,'postgres');assert.equal(u.pathname,'/prumo_s0_test_ci');
assert.equal(u.search,'');assert.equal(u.hash,'');
for(const k of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER',
 'PGSERVICE','PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT',
 'PGSSLKEY','PGSSLROOTCERT'])assert.equal(process.env[k],undefined);
assert.equal(process.argv.length,3);
const raw=readFileSync(process.argv[2],'utf8').trim();
assert.ok(raw.length>100&&raw.length<4000&&!raw.includes('\n'));
const b=JSON.parse(raw) as Wa32AttemptLookup;
assert.deepEqual(Object.keys(b).sort(),[
 'app_ref','concessionaria_id','canal_id','waba_id','phone_number_id',
 'provider_message_id','recipient_verified','case_ref','attempt_ref',
 'binding_revision','claim_state',
].sort());
assert.equal(b.app_ref,'APP_A');assert.equal(b.concessionaria_id,'shop_A');
assert.equal(b.claim_state,'LAB_INVALIDATED');assert.equal(b.binding_revision,1);
const mark=(n:number)=>process.stdout.write(
 'WA35-'+String(n).padStart(2,'0')+' PASS\n');
const sql=(statement:string)=>{
 const out=execFileSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',dsn,
  '-c',statement],{encoding:'utf8',timeout:12000,maxBuffer:8192,
  env:{PATH:process.env.PATH||'/usr/bin:/bin',HOME:process.env.HOME||'/tmp',
    LC_ALL:'C',PGCONNECT_TIMEOUT:'5',PGAPPNAME:'wa35_signed_lab'}});
 return out.trim();
};
const quote=(s:string)=>{
 assert.match(s,/^[A-Za-z0-9_.:-]{1,128}$/);
 return "'"+s+"'";
};
const TIME=1792320000000, META='WA35_PG17_FAKE_META_SECRET';
const KEY=new Uint8Array(48).fill(0x56);
let nonceIndex=0;
const route={route_ref:'WA35_PG17_ROUTE',expected_revision:5};
const app={
 app_ref:b.app_ref,route_ref:route.route_ref,
 concessionaria_id:b.concessionaria_id,revision:5,active:true,
 valid_from_ms:TIME-1000,valid_until_ms:TIME+100000,
 secret_slots:{get_verify_token:'WA35_PG17_GET',
  post_app_secret:'WA35_PG17_POST',graph_access_token:'WA35_PG17_GRAPH'},
 channels:[{canal_id:b.canal_id,waba_id:b.waba_id,
  phone_number_id:b.phone_number_id,active:true}],
};
const registry:TrustedMetaRegistry={
 contract_version:'wa-meta-credential-routing.v0.1-proposed',apps:[app],
};
const ports:TrustedRoutingPorts={
 currentRegistry:async()=>registry,nowMs:()=>TIME,
 resolveSecret:async()=>META,
};
const s0={lookupExactAttempt:async()=>[b]};
const scopeFrom=(p:NonNullable<Awaited<ReturnType<typeof make>>['ticket']>):
 Wa34Scope=>({
 app_ref:p.payload.app_ref,concessionaria_id:p.payload.concessionaria_id,
 canal_id:p.payload.canal_id,waba_id:p.payload.waba_id,
 phone_number_id:p.payload.phone_number_id,
 provider_message_id:p.payload.provider_message_id,
 recipient_verified:p.payload.recipient_verified,case_ref:p.payload.case_ref,
 attempt_ref:p.payload.attempt_ref,binding_revision:p.payload.binding_revision,
 event_ref:p.payload.event_ref,provider_kind:p.payload.provider_kind,
 meta_body_sha256:p.payload.meta_body_sha256,
});
async function signed(status='delivered',secret=META){
 const bytes=new TextEncoder().encode(JSON.stringify({
 object:'whatsapp_business_account',
 entry:[{id:b.waba_id,changes:[{field:'messages',value:{
  metadata:{phone_number_id:b.phone_number_id},
  statuses:[{id:b.provider_message_id,recipient_id:b.recipient_verified,
   status,timestamp:'1792320000'}]}}]}]}));
 const key=await crypto.subtle.importKey('raw',new TextEncoder().encode(secret),
  {name:'HMAC',hash:'SHA-256'},false,['sign']);
 const mac=new Uint8Array(await crypto.subtle.sign('HMAC',key,bytes));
 return {raw_body:bytes,route,
  signature_header:'sha256='+Array.from(mac,
   x=>x.toString(16).padStart(2,'0')).join('')};
}
async function ticket(kind='delivered'){
 const result=await make(await signed(kind),{
  routing:ports,s0,internalKey:async()=>KEY,
  nonce:async()=> 'WA35_PG_NONCE_'+(++nonceIndex),
 });
 assert.equal(result.decision,'LAB_TICKET_FOR_S0_RECHECK_ONLY');
 assert.ok(result.ticket);
 assert.equal(result.ack_allowed,false);
 assert.equal(result.send_authorized,false);
 const verification=await verifyWa34SyntheticFixture(result.ticket,
  scopeFrom(result.ticket),TIME,KEY);
 assert.equal(verification.decision,'LAB_CONTRACT_PENDING');
 return result.ticket;
}
function consume(p:NonNullable<Awaited<ReturnType<typeof make>>['ticket']>){
 const v=p.payload;
 const types={
  sent:'SENT_REPORTED',delivered:'DELIVERED_REPORTED',
  read:'READ_REPORTED',failed:'FAILED_REPORTED',
 };
 return sql('SELECT wa34_lab.consume_fixture('+
  [v.nonce_ref,v.app_ref,v.waba_id,v.phone_number_id,v.provider_message_id,
   v.recipient_verified,v.event_ref,types[v.provider_kind]].map(quote).join(',')+
  ','+[v.binding_revision,v.issued_at_ms,v.expires_at_ms,TIME].join(',')+')');
}

mark(1);
const first=await ticket();mark(2);
assert.equal(first.payload.meta_body_sha256.length,64);
assert.match(first.payload.event_ref,/^EVT_[a-f0-9]{64}$/);mark(3);
assert.equal(consume(first),'LAB_NONCE_CONSUMED_ARCHIVED_NO_SEND');mark(4);
assert.equal(sql('SELECT count(*) FROM wa33_lab.events WHERE event_ref='+
 quote(first.payload.event_ref)),'1');mark(5);
assert.equal(sql('SELECT after_invalidation FROM wa33_lab.events WHERE event_ref='+
 quote(first.payload.event_ref)),'t');mark(6);
assert.equal(consume(first),'LAB_NONCE_CONSUMED_NO_RETRY');mark(7);
const repeat=await ticket();assert.equal(repeat.payload.event_ref,first.payload.event_ref);
assert.notEqual(repeat.payload.nonce_ref,first.payload.nonce_ref);
assert.equal(consume(repeat),'LAB_NONCE_CONSUMED_REPLAY_NO_SEND');mark(8);
assert.equal(sql('SELECT count(*) FROM wa33_lab.events WHERE event_ref='+
 quote(first.payload.event_ref)),'1');mark(9);
const wrongMeta=await make(await signed('delivered','FAKE_WRONG_META_KEY'),{
 routing:ports,s0,internalKey:async()=>KEY,
 nonce:async()=>'UNUSED_NONCE',
});
assert.equal(wrongMeta.decision,'LAB_ROUTING_DENIED');
assert.equal(wrongMeta.ticket,null);mark(10);
const modified={...first,payload:{...first.payload,case_ref:'case31_wrong'}};
assert.equal((await verifyWa34SyntheticFixture(modified,scopeFrom(first),
 TIME,KEY)).decision,'LAB_DENIED');mark(11);
assert.equal((await verifyWa34SyntheticFixture(first,scopeFrom(first),
 TIME+60000,KEY)).decision,'LAB_DENIED');mark(12);
const other=await make(await signed(),{routing:ports,
 s0:{lookupExactAttempt:async()=>[{...b,concessionaria_id:'shop_B'}]},
 internalKey:async()=>KEY,nonce:async()=>'BAD_TENANT',
});
assert.equal(other.decision,'LAB_BINDING_DENIED');mark(13);
const rotated=await ticket('read');
assert.equal(sql("SELECT wa33_lab.change_binding_fixture('shop_A','case31_late',"+
 "'5581900000099')"),'LAB_BINDING_CHANGED');
assert.equal(consume(rotated),'LAB_DENIED');
assert.equal(sql('SELECT count(*) FROM wa34_lab.consumed_nonces WHERE nonce_ref='+
 quote(rotated.payload.nonce_ref)),'0');mark(14);
assert.equal(sql('SELECT count(*) FROM wa34_lab.consumed_nonces WHERE '+
 'send_authorized OR production_authorized OR ack_allowed OR retry_external OR '+
 'case_transition_authorized OR definitive_failure_count_increment'),'0');mark(15);
assert.equal(sql('SELECT state FROM wa29_lab.claims WHERE '+
 "case_ref='case31_late'"),'LAB_INVALIDATED');mark(16);
process.stdout.write('PASS WA35: 16 signed Meta -> internal MAC -> PG17 checks, fixture only\n');
