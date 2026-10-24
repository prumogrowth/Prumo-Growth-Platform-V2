/** WA47 independent signatures and explicit, versioned field mapping. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash,createHmac,randomUUID} from 'node:crypto';
import {makeWa44CandidateFixture,signWa44Fixture} from './s0_wa_048_meta_handoff_adapter.mjs';
import {createWa47OfflineWireAgreement} from './s0_wa_051_dual_wire_agreement.mjs';
const K34=Buffer.alloc(48,0x32),KS0=Buffer.alloc(48,0x61),NOW=1782320000000;
const C=Object.freeze({appRef:'FIXTURE_WA40_B',tenantRef:'SHOP_WA40_B',
 channelRef:'f7300000-0000-4000-8000-000000000002',wabaTechnical:'22346000002',
 phoneTechnical:'32346000002',appTechnical:'12346000002',
 intentRef:'f7400000-0000-4000-8000-000000000002',caseRef:'CASE_B',attemptRef:'ATTEMPT_B',
 correlationRef:'CORR_B',bindingRevision:3,recipient:'5581900000000',
 wamid:'wamid.WA40.SHARED',providerTimestampSeconds:'1782320000',
 wa34KeySlot:'WA34_INTERNAL_FIXTURE_B',s0KeyId:'f7900000-0000-4000-8000-000000000001'});
const PAYLOAD=['contract','purpose','issuer','audience','nonce_ref','issued_at_ms','expires_at_ms',
 'app_ref','concessionaria_id','canal_id','waba_id','phone_number_id','provider_message_id',
 'recipient_verified','case_ref','attempt_ref','binding_revision','event_ref','provider_kind',
 'meta_body_sha256','ack_allowed','send_authorized','retry_external',
 'production_authorized','case_transition_authorized','definitive_failure_count_increment'];
const dh=s=>createHash('sha256').update(s).digest('hex');
function fixture(c=C){
 const kind='delivered',bodyHash='d'.repeat(64);
 const iso=new Date(Number(c.providerTimestampSeconds)*1000).toISOString();
 const wa34Id='EVT_'+dh(JSON.stringify([c.appRef,c.wabaTechnical,c.phoneTechnical,
  c.wamid,c.recipient,kind,iso]));
 const wa46Id='WA46_'+dh(JSON.stringify([c.wabaTechnical,c.phoneTechnical,
  c.wamid,c.recipient,kind,c.providerTimestampSeconds]));
 const wa34={contract:'wa34-service-forensic-handoff.lab.v1',purpose:'FORENSIC_APPEND_ONLY',
  issuer:'WA34_SYNTHETIC_META_INGRESS',audience:'WA34_SYNTHETIC_S0_READER',
  nonce_ref:'WA34_NONCE_B',issued_at_ms:NOW-1000,expires_at_ms:NOW+60000,
  app_ref:c.appRef,concessionaria_id:c.tenantRef,canal_id:c.channelRef,
  waba_id:c.wabaTechnical,phone_number_id:c.phoneTechnical,
  provider_message_id:c.wamid,recipient_verified:c.recipient,case_ref:c.caseRef,
  attempt_ref:c.attemptRef,binding_revision:c.bindingRevision,
  event_ref:wa34Id,provider_kind:kind,meta_body_sha256:bodyHash,
  ack_allowed:false,send_authorized:false,retry_external:false,
  production_authorized:false,case_transition_authorized:false,
  definitive_failure_count_increment:false};
 const sign=p=>({payload:p,mac_sha256:createHmac('sha256',K34)
  .update(JSON.stringify(PAYLOAD.map(k=>p[k]))).digest('hex')});
 const cand=makeWa44CandidateFixture({registry:{appTechnical:c.appTechnical,
  wabaTechnical:c.wabaTechnical,phoneTechnical:c.phoneTechnical,appRef:c.appRef,
  tenantRef:c.tenantRef,channelRef:c.channelRef},binding:{appRef:c.appRef,
  tenantRef:c.tenantRef,channelRef:c.channelRef,intentRef:c.intentRef,
  attemptRef:c.attemptRef,correlationRef:c.correlationRef,recipient:c.recipient,
  wamid:c.wamid,bindingRevision:c.bindingRevision},event:{eventRef:wa46Id,
  kind,bodySha256:bodyHash},keyId:c.s0KeyId,nonce:randomUUID(),
  issuedAtSeconds:NOW/1000,expectedRevision:c.bindingRevision});
 assert.ok(cand);
 const ticket=signWa44Fixture(cand,KS0);assert.ok(ticket);
 const wa46={decision:'LAB_META_HMAC_AND_S0_CANDIDATE_ONLY',ticket,
  ack_allowed:false,send_authorized:false,retry_external:false,
  production_authorized:false,service_authenticated:false,
  meta_provenance_production_proven:false,delivery_confirmed:false,
  case_transition_authorized:false};
 return {wa34:sign(wa34),wa46,sign};
}
function gate(o={}){return createWa47OfflineWireAgreement({
 getContext:o.getContext??(async()=>C),getWa34Key:o.getWa34Key??(async()=>Buffer.from(K34)),
 getS0Key:o.getS0Key??(async()=>Buffer.from(KS0)),nowMs:o.nowMs??(()=>NOW)
 });}
async function run(o={}){
 const f=fixture();return gate(o).compare(o.wa34??f.wa34,o.wa46??f.wa46);
}
const deny=x=>{
 assert.equal(x.wire_agreement,false);
 for(const k of ['service_authenticated','ack_allowed','send_authorized','retry_external',
  'production_authorized','delivery_confirmed','case_transition_authorized',
  'definitive_failure_count_increment','s0_write_authorized',
  'meta_provenance_production_proven'])assert.equal(x[k],false,k);
};
const checks=[
 async()=>{const r=await run();assert.equal(r.decision,'LAB_DUAL_WIRE_AGREEMENT_ONLY');assert.equal(r.wire_agreement,true);},
 async()=>{const r=await run();for(const k of ['service_authenticated','ack_allowed','send_authorized','retry_external','production_authorized','delivery_confirmed','case_transition_authorized','definitive_failure_count_increment','s0_write_authorized','meta_provenance_production_proven'])assert.equal(r[k],false,k);},
 async()=>{const f=fixture();const w={...f.wa34,payload:{...f.wa34.payload,issuer:'FAKE'}};deny(await run({wa34:w}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,audience:'OTHER'}}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,purpose:'SEND'}}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,app_ref:'OTHER'}}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,concessionaria_id:'OTHER'}}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,canal_id:randomUUID()}}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,binding_revision:4}}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,event_ref:'EVT_FORGED'}}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,meta_body_sha256:'0'.repeat(64)}}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,ack_allowed:true}}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,nonce_ref:'NEW_NONCE'}}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,expires_at_ms:NOW-1}}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,extra:'x'}}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,mac_sha256:'0'.repeat(64)}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,mac_sha256:f.wa46.ticket.macSha256}}));},
 async()=>{const f=fixture();deny(await run({wa46:{...f.wa46,ticket:{...f.wa46.ticket,macSha256:'0'.repeat(64)}}}));},
 async()=>{const f=fixture();deny(await run({wa46:{...f.wa46,service_authenticated:true}}));},
 async()=>{const f=fixture();deny(await run({wa46:{...f.wa46,decision:'PRODUCTION_AUTHORIZED'}}));},
 async()=>{const f=fixture();deny(await run({wa46:{...f.wa46,ticket:{...f.wa46.ticket,audience:'WA34_SYNTHETIC_S0_READER'}}}));},
 async()=>{const f=fixture();deny(await run({wa46:{...f.wa46,ticket:{...f.wa46.ticket,candidate:Object.freeze(f.wa46.ticket.candidate.map((v,i)=>i===4?randomUUID():v))}}}));},
 async()=>{deny(await run({getWa34Key:async()=>Buffer.alloc(4)}));},
 async()=>{deny(await run({getS0Key:async()=>Buffer.alloc(4)}));},
 async()=>{deny(await run({getWa34Key:async()=>Buffer.from(KS0)}));},
 async()=>{deny(await run({getS0Key:async()=>Buffer.from(K34)}));},
 async()=>{deny(await run({getContext:async()=>({...C,appRef:'DIFFERENT'})}));},
 async()=>{let n=0;deny(await run({getContext:async()=>++n===1?C:{...C,bindingRevision:4}}));},
 async()=>{let n=0;deny(await run({nowMs:()=>++n===1?NOW:NOW+21000}));},
 async()=>{deny(await run({getContext:async()=>{throw Error('db')}}));},
 async()=>{const f=fixture();const v={...f.wa34.payload};Object.defineProperty(v,'purpose',{get(){throw Error('getter')}});deny(await run({wa34:{...f.wa34,payload:v}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,[Symbol('hidden')]:true}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,provider_kind:'unknown'}}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,case_ref:'WRONG'}}}));},
 async()=>{const f=fixture();deny(await run({wa34:{...f.wa34,payload:{...f.wa34.payload,attempt_ref:'WRONG'}}}));},
 async()=>{const f=fixture();deny(await run({wa46:{...f.wa46,ticket:{...f.wa46.ticket,candidate:f.wa46.ticket.candidate.map((v,i)=>i===10?'EVT_WRONG':v)}}}));},
 async()=>{assert.equal(createWa47OfflineWireAgreement({getContext:()=>C}),null);},
];
for(let i=0;i<checks.length;i++)test('WA47-'+String(i+1).padStart(2,'0')+' dual-wire fixture',async()=>{
 await checks[i]();console.log('WA47-'+String(i+1).padStart(2,'0')+' PASS');
});
