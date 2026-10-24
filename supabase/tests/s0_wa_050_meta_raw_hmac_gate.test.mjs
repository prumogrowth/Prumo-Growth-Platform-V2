/** WA46: raw Meta HMAC fixture -> independently checked WA45 candidate. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac,createHash,randomUUID} from 'node:crypto';
import {createWa45OfflineBoundary} from './s0_wa_049_meta_trusted_boundary.mjs';
import {createWa46OfflineMetaGate} from './s0_wa_050_meta_raw_hmac_gate.mjs';

const APP=Buffer.alloc(48,0x4d),INTERNAL=Buffer.alloc(48,0x61);
const KEY_ID='f7900000-0000-4000-8000-000000000001',ROUTE='ROUTE_WA46_A';
const R=Object.freeze({appTechnical:'12346000002',wabaTechnical:'22346000002',
 phoneTechnical:'32346000002',appRef:'FIXTURE_WA40_B',tenantRef:'SHOP_WA40_B',
 channelRef:'f7300000-0000-4000-8000-000000000002'});
const REG=Object.freeze({routeRef:ROUTE,revision:4,...R,secretSlot:'APP_SECRET_WA46_FIXTURE',enabled:true});
const B=Object.freeze({appRef:R.appRef,tenantRef:R.tenantRef,channelRef:R.channelRef,
 intentRef:'f7400000-0000-4000-8000-000000000002',attemptRef:'ATTEMPT_B',
 correlationRef:'CORR_B',recipient:'5581900000000',wamid:'wamid.WA40.SHARED',
 bindingRevision:3});
const NOW=1782320000;
const meta=(o={})=>({object:'whatsapp_business_account',
 entry:[{id:R.wabaTechnical,changes:[{field:'messages',value:{
 metadata:{phone_number_id:R.phoneTechnical},statuses:[{
 id:B.wamid,status:'delivered',recipient_id:B.recipient,timestamp:'1782320000',
 ...o}]}}]}]});
const encode=x=>Buffer.from(JSON.stringify(x));
const signature=(raw,key=APP)=>'sha256='+createHmac('sha256',key).update(raw).digest('hex');
function setup(o={}){
 let registries=0;
 const registryPort=o.getRegistry??(async()=>{registries++;return REG;});
 const wa45=o.wa45Boundary??createWa45OfflineBoundary({
  getRegistry:async()=>R,lookupBinding:async()=>B,
  getInternalKey:async()=>Buffer.from(INTERNAL),newNonce:async()=>randomUUID(),
  nowSeconds:()=>NOW
 },KEY_ID);
 assert.ok(wa45);
 const gate=createWa46OfflineMetaGate({
  getRegistry:registryPort,getMetaAppSecret:o.getMetaAppSecret??(async()=>Buffer.from(APP)),
  nowSeconds:o.nowSeconds??(()=>NOW),wa45Boundary:wa45,
 },ROUTE);
 assert.ok(gate);
 return {gate,registryReads:()=>registries};
}
const call=async(o={},body=encode(meta()),header)=>setup(o).gate.receive(body,header??signature(body));
const assertClosed=v=>{
 assert.equal(v.ticket,null);
 for(const k of ['ack_allowed','send_authorized','retry_external','production_authorized',
  'service_authenticated','meta_provenance_production_proven','delivery_confirmed',
  'case_transition_authorized'])assert.equal(v[k],false,k);
};
const checks=[
 async()=>{const body=encode(meta());const v=await call({},body);assert.equal(v.decision,'LAB_META_HMAC_AND_S0_CANDIDATE_ONLY');assert.ok(v.ticket);assert.equal(v.ticket.candidate[12],createHash('sha256').update(body).digest('hex'));},
 async()=>{const v=await call();for(const k of ['ack_allowed','send_authorized','retry_external','production_authorized','service_authenticated','meta_provenance_production_proven','delivery_confirmed','case_transition_authorized'])assert.equal(v[k],false,k);},
 async()=>{const raw=encode(meta());raw[raw.length-2]^=1;const v=await call({},raw,signature(encode(meta())));assert.equal(v.decision,'LAB_META_SIGNATURE_DENIED');assertClosed(v);},
 async()=>{const raw=encode(meta());assert.equal((await call({},raw,signature(raw,Buffer.alloc(48,0x61)))).decision,'LAB_META_SIGNATURE_DENIED');},
 async()=>{const raw=encode(meta());assert.equal((await call({},raw,'sha1='+signature(raw).slice(7))).decision,'LAB_DENIED');},
 async()=>{const raw=encode(meta());assert.equal((await call({},raw,signature(raw).toUpperCase())).decision,'LAB_DENIED');},
 async()=>{assert.equal((await call({},encode(meta({id:'wamid.WRONG'})))).decision,'LAB_SCOPE_DENIED');},
 async()=>{assert.equal((await call({},encode(meta({recipient_id:'5581999999999'})))).decision,'LAB_SCOPE_DENIED');},
 async()=>{assert.equal((await call({},encode(meta({status:'deleted'})))).decision,'LAB_SCOPE_DENIED');},
 async()=>{const x=meta();x.entry[0].id='123456789';assert.equal((await call({},encode(x))).decision,'LAB_SCOPE_DENIED');},
 async()=>{const x=meta();x.entry[0].changes[0].value.metadata.phone_number_id='76543210';assert.equal((await call({},encode(x))).decision,'LAB_SCOPE_DENIED');},
 async()=>{const x=meta();x.entry[0].changes[0].value.statuses.push({...x.entry[0].changes[0].value.statuses[0]});assert.equal((await call({},encode(x))).decision,'LAB_SCOPE_DENIED');},
 async()=>{const x=meta();x.entry.push(x.entry[0]);assert.equal((await call({},encode(x))).decision,'LAB_SCOPE_DENIED');},
 async()=>{const x=meta();x.entry[0].changes[0].value.messages=[];assert.equal((await call({},encode(x))).decision,'LAB_SCOPE_DENIED');},
 async()=>{assert.equal((await call({},encode({payload:{purpose:'FORENSIC_APPEND_ONLY'},mac_sha256:'a'.repeat(64)}))).decision,'LAB_SCOPE_DENIED');},
 async()=>{const raw=Buffer.from('{"object":','utf8');assert.equal((await call({},raw)).decision,'LAB_SCOPE_DENIED');},
 async()=>{const raw=Buffer.from([0xff,0xfe]);assert.equal((await call({},raw)).decision,'LAB_SCOPE_DENIED');},
 async()=>{assert.equal((await call({getRegistry:async()=>({...REG,enabled:false})})).decision,'LAB_SCOPE_DENIED');},
 async()=>{let n=0;assert.equal((await call({getRegistry:async()=>++n===1?REG:{...REG,revision:5}})).decision,'LAB_STALE');},
 async()=>{let n=0;assert.equal((await call({getRegistry:async()=>++n<3?REG:{...REG,enabled:false}})).decision,'LAB_STALE');},
 async()=>{assert.equal((await call({getMetaAppSecret:async()=>Buffer.alloc(10)})).decision,'LAB_UNAVAILABLE');},
 async()=>{const v=await call({getMetaAppSecret:async()=>{throw Error('secret backend down')}});assert.equal(v.decision,'LAB_UNAVAILABLE');assertClosed(v);},
 async()=>{let n=0;assert.equal((await call({nowSeconds:()=>++n===1?NOW:NOW+21})).decision,'LAB_STALE');},
 async()=>{const x=meta();const original=encode(x);const gate=setup({getMetaAppSecret:async()=>{original.fill(0);return Buffer.from(APP)}}).gate;const sig=signature(encode(x));const result=await gate.receive(original,sig);assert.equal(result.decision,'LAB_META_HMAC_AND_S0_CANDIDATE_ONLY');},
 async()=>{const stub={issue:async()=>({decision:'LAB_CANDIDATE_ONLY',ticket:{candidate:Object.freeze([KEY_ID,'OTHER_APP',R.wabaTechnical,R.phoneTechnical,R.channelRef,'','','','','','','','','',''])}})};assert.equal((await call({wa45Boundary:stub})).decision,'LAB_SCOPE_DENIED');},
 async()=>{assert.equal(createWa46OfflineMetaGate({getRegistry:async()=>REG},ROUTE),null);},
 async()=>{const x={...REG};Object.defineProperty(x,'secretSlot',{get(){throw Error('access')}});assert.equal((await call({getRegistry:async()=>x})).decision,'LAB_SCOPE_DENIED');},
 async()=>{const v=await call({},Buffer.alloc(262145));assert.equal(v.decision,'LAB_DENIED');assertClosed(v);},
];
for(let i=0;i<checks.length;i++)
 test('WA46-'+String(i+1).padStart(2,'0')+' raw-HMAC/scope lab check',async()=>{
  await checks[i]();console.log('WA46-'+String(i+1).padStart(2,'0')+' PASS');
 });
