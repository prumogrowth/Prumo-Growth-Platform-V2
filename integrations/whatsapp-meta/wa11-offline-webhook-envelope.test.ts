import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac,createHash} from 'node:crypto';
import {inspectWa11OfflineWebhookEnvelope as inspect} from './wa11-offline-webhook-envelope.ts';
import type {TrustedMetaRegistry} from './credential-routing.ts';
import type {TrustedRoutingPorts} from './routed-webhook.ts';

const NOW=1792320000000;
const POST_KEY='WA11_FAKE_HMAC_APP_A',GET_KEY='WA11_FAKE_GET_TOKEN_APP_A';
const otherPOST='WA11_FAKE_HMAC_APP_B';
const appA={
 app_ref:'APP_A',route_ref:'TRUSTED_ROUTE_A',concessionaria_id:'SHOP_A',
 active:true,revision:4,valid_from_ms:NOW-5000,valid_until_ms:NOW+5000,
 secret_slots:{get_verify_token:'WA11_GET_A',post_app_secret:'WA11_POST_A',
  graph_access_token:'WA11_GRAPH_A'},
 channels:[
  {canal_id:'CHANNEL_A1',waba_id:'100001',phone_number_id:'12345678901',active:true},
  {canal_id:'CHANNEL_A2',waba_id:'100002',phone_number_id:'12345678902',active:true},
 ],
};
const appB={...appA,app_ref:'APP_B',route_ref:'TRUSTED_ROUTE_B',
 concessionaria_id:'SHOP_B',revision:6,
 secret_slots:{get_verify_token:'WA11_GET_B',post_app_secret:'WA11_POST_B',
  graph_access_token:'WA11_GRAPH_B'},
 channels:[{canal_id:'CHANNEL_B1',waba_id:'200001',
  phone_number_id:'98765432100',active:true}],
};
const REG:TrustedMetaRegistry={
 contract_version:'wa-meta-credential-routing.v0.1-proposed',apps:[appA,appB],
};
const route=()=>({route_ref:'TRUSTED_ROUTE_A',expected_revision:4});
const query=(token=GET_KEY)=>new URLSearchParams({
 'hub.mode':'subscribe','hub.verify_token':token,'hub.challenge':'000021',
}).toString();
const makeEntry=(waba='100001',phone='12345678901',msg='wamid.M1')=>({
 id:waba,changes:[{field:'messages',value:{metadata:{phone_number_id:phone},
  messages:[{id:msg,from:'5581888800000',type:'text',timestamp:'1792320000',
   text:{body:'CONFIDENTIAL_DO_NOT_LEAK'}}]}}],
});
const payload=(entries:unknown[]=[makeEntry()])=>({
 object:'whatsapp_business_account',entry:entries,
});
const raw=(entries?:unknown[])=>Buffer.from(JSON.stringify(payload(entries)),'utf8');
const sign=(data:Uint8Array,key=POST_KEY)=>
 'sha256='+createHmac('sha256',key).update(data).digest('hex');
const ports=(option:{registry?:()=>TrustedMetaRegistry;
 secret?:((slot:string)=>string|undefined);
 clock?:()=>number;calls?:string[]}={}):TrustedRoutingPorts=>({
 currentRegistry:option.registry??(()=>REG),
 resolveSecret:(slot:string)=>{option.calls?.push(slot);
  return option.secret?.(slot)??({
   WA11_GET_A:GET_KEY,WA11_POST_A:POST_KEY,
   WA11_POST_B:otherPOST,WA11_GET_B:'OTHER_GET',
  } as Record<string,string>)[slot];},
 nowMs:option.clock??(()=>NOW),
});
const post=(data=raw(),headers?:string[][])=>({
 method:'POST',route:route(),raw_query:null,raw_body:data,
 headers:headers??[['Content-Type','application/json'],
   ['X-Hub-Signature-256',sign(data)],['Content-Length',String(data.length)]],
});
const get=()=>({
 method:'GET',route:route(),raw_query:query(),raw_body:null,
 headers:[['Accept','text/plain']],
});
type Result=Awaited<ReturnType<typeof inspect>>;
const flags=(result:Result)=>{
 for(const k of ['ack_allowed','http_ack_allowed','http_response_authorized',
  'partial_ack_allowed','send_authorized','s0_write_authorized',
  'production_authorized','persisted','commit_verified','durable_receipt_verified',
  'm2m_verified','service_identity_verified','retry_external',
  'automatic_retry_authorized','batch_partition_authorized',
  'channel_policy_ratified','commercial_transition_authorized'] as const)
  assert.equal(result[k],false,k);
 assert.equal('status' in result,false);
 assert.equal('http_code' in result,false);
 assert.equal('events' in result,false);
 assert.equal('channels' in result,false);
 assert.equal(Object.isFrozen(result),true);
};
const denied=(x:Result,reason?:string)=>{
 flags(x);assert.equal(x.decision,'DENIED');
 if(reason)assert.equal(x.reason,reason);
 assert.equal(x.challenge,null);assert.equal(x.event_count,0);
 assert.equal(x.scope_count,0);assert.equal(x.raw_sha256,null);
};
test('M11-01 valid GET challenge is challenge-only, never HTTP response authority',async()=>{
 const v=await inspect(get(),ports());flags(v);
 assert.equal(v.decision,'LAB_GET_CHALLENGE_VERIFIED_UNRATIFIED');
 assert.equal(v.challenge,'000021');assert.equal(v.raw_sha256,null);
});
test('M11-02 GET uses only verify-token slot, never HMAC',async()=>{
 const calls:string[]=[];const v=await inspect(get(),ports({calls}));
 assert.equal(v.decision,'LAB_GET_CHALLENGE_VERIFIED_UNRATIFIED');
 assert.deepEqual(calls,['WA11_GET_A']);
});
test('M11-03 GET invalid verification token refused',async()=>{
 denied(await inspect({...get(),raw_query:query('BAD')},ports()),
  'ROUTING_OR_VERIFICATION_DENIED');
});
test('M11-04 GET unknown route cannot infer from query',async()=>{
 const q={...get(),route:{route_ref:'UNKNOWN',expected_revision:4}};
 denied(await inspect(q,ports()),'ROUTING_OR_VERIFICATION_DENIED');
});
test('M11-05 GET stale route revision denies',async()=>{
 denied(await inspect({...get(),route:{...route(),expected_revision:3}},
  ports()),'ROUTING_OR_VERIFICATION_DENIED');
});
test('M11-06 GET unexpected body denied before secret lookup',async()=>{
 const calls:string[]=[];
 denied(await inspect({...get(),raw_body:new Uint8Array([1])},ports({calls})),
  'INVALID_ENVELOPE');assert.deepEqual(calls,[]);
});
test('M11-07 GET with HMAC signature header is unsupported',async()=>{
 denied(await inspect({...get(),headers:[['X-Hub-Signature-256',sign(raw())]]},
  ports()),'UNSUPPORTED_FRAMING');
});
test('M11-08 GET duplicate hub query parameter rejected',async()=>{
 denied(await inspect({...get(),raw_query:query()+'&hub.challenge=999'},
  ports()),'ROUTING_OR_VERIFICATION_DENIED');
});
test('M11-09 GET query oversized denied',async()=>{
 denied(await inspect({...get(),raw_query:'x'.repeat(8193)},ports()),
  'INVALID_ENVELOPE');
});
test('M11-10 GET never discloses verify token in denial',async()=>{
 const v=await inspect({...get(),raw_query:query('BAD')},ports());
 denied(v);assert.equal(JSON.stringify(v).includes(GET_KEY),false);
});
test('M11-11 correctly signed single physical POST remains uncommitted',async()=>{
 const data=raw(),v=await inspect(post(data),ports());flags(v);
 assert.equal(v.decision,'LAB_SIGNED_SINGLE_CHANNEL_UNCOMMITTED');
 assert.equal(v.event_count,1);assert.equal(v.scope_count,1);
 assert.equal(v.challenge,null);
 assert.equal(v.raw_sha256,createHash('sha256').update(data).digest('hex'));
});
test('M11-12 one POST with two WABAs under same App remains unratified',async()=>{
 const data=raw([makeEntry(),makeEntry('100002','12345678902','wamid.M2')]);
 const v=await inspect(post(data),ports());flags(v);
 assert.equal(v.decision,'LAB_SIGNED_MULTICHANNEL_UNRATIFIED');
 assert.equal(v.event_count,2);assert.equal(v.scope_count,2);
});
test('M11-13 POST cannot inject channel of another App',async()=>{
 const data=raw([makeEntry(),makeEntry('200001','98765432100')]);
 denied(await inspect(post(data),ports()),'HMAC_OR_SCOPE_DENIED');
});
test('M11-14 wrong App HMAC denies entire POST',async()=>{
 const data=raw(),q=post(data);q.headers[1][1]=sign(data,otherPOST);
 denied(await inspect(q,ports()),'HMAC_OR_SCOPE_DENIED');
});
test('M11-15 one byte altered after signing denies',async()=>{
 const original=raw(),changed=Buffer.from(original);changed[8]^=1;
 denied(await inspect(post(changed,[['Content-Type','application/json'],
   ['X-Hub-Signature-256',sign(original)]]),ports()),'HMAC_OR_SCOPE_DENIED');
});
test('M11-16 missing signature refused before accessing secrets',async()=>{
 const calls:string[]=[],data=raw();
 denied(await inspect(post(data,[['Content-Type','application/json']]),
  ports({calls})),'UNSUPPORTED_FRAMING');
 assert.deepEqual(calls,[]);
});
test('M11-17 duplicate HMAC header cannot be collapsed to good signature',async()=>{
 const data=raw();
 denied(await inspect(post(data,[['Content-Type','application/json'],
  ['X-Hub-Signature-256',sign(data)],
  ['x-hub-signature-256',sign(data,otherPOST)]]),ports()),'AMBIGUOUS_HEADERS');
});
test('M11-18 duplicate content type rejected before secret access',async()=>{
 const calls:string[]=[],data=raw();
 denied(await inspect(post(data,[['Content-Type','application/json'],
  ['content-type','application/json'],['X-Hub-Signature-256',sign(data)]]),
  ports({calls})),'AMBIGUOUS_HEADERS');
 assert.deepEqual(calls,[]);
});
test('M11-19 compressed body header rejected, no auto decompression',async()=>{
 const data=raw(),q=post(data);
 q.headers.push(['Content-Encoding','gzip']);
 denied(await inspect(q,ports()),'UNSUPPORTED_FRAMING');
});
test('M11-20 transfer-encoding ambiguity rejected',async()=>{
 const data=raw(),q=post(data);q.headers.push(['Transfer-Encoding','chunked']);
 denied(await inspect(q,ports()),'UNSUPPORTED_FRAMING');
});
test('M11-21 method override cannot reinterpret POST as GET',async()=>{
 const data=raw(),q=post(data);q.headers.push(['X-HTTP-Method-Override','GET']);
 denied(await inspect(q,ports()),'UNSUPPORTED_FRAMING');
});
test('M11-22 content-length mismatch denies before HMAC',async()=>{
 const data=raw(),q=post(data);q.headers[2][1]=String(data.length-1);
 denied(await inspect(q,ports()),'UNSUPPORTED_FRAMING');
});
test('M11-23 leading-zero content length refused',async()=>{
 const data=raw(),q=post(data);q.headers[2][1]='00'+data.length;
 denied(await inspect(q,ports()),'UNSUPPORTED_FRAMING');
});
test('M11-24 malicious JSON content type parameters rejected',async()=>{
 const data=raw(),q=post(data);q.headers[0][1]='application/json; boundary=other';
 denied(await inspect(q,ports()),'UNSUPPORTED_FRAMING');
});
test('M11-25 exact UTF-8 charset accepted for JSON',async()=>{
 const data=raw(),q=post(data);q.headers[0][1]='application/json; charset=utf-8';
 const x=await inspect(q,ports());assert.equal(x.decision,'LAB_SIGNED_SINGLE_CHANNEL_UNCOMMITTED');flags(x);
});
test('M11-26 unrecognized method denied',async()=>{
 denied(await inspect({...get(),method:'PUT'},ports()),'INVALID_ENVELOPE');
});
test('M11-27 a POST cannot also carry GET verification parameters',async()=>{
 const q={...post(raw()),raw_query:query()};
 denied(await inspect(q,ports()),'INVALID_BODY');
});
test('M11-28 wrong POST data type denied (no text reconstruction)',async()=>{
 const q={...post(raw()),raw_body:'{"object":"test"}'};
 denied(await inspect(q,ports()),'INVALID_BODY');
});
test('M11-29 overlarge POST refused before secret lookup',async()=>{
 const calls:string[]=[],q=post(raw());
 const data=new Uint8Array(256*1024+1);
 denied(await inspect({...q,raw_body:data},ports({calls})),'INVALID_BODY');
 assert.deepEqual(calls,[]);
});
test('M11-30 extra request property cannot supply fake ACK decision',async()=>{
 const q={...post(raw()),http_ack_allowed:true};
 denied(await inspect(q,ports()),'INVALID_ENVELOPE');
});
test('M11-31 invalid route revision cannot select a secret',async()=>{
 denied(await inspect({...post(raw()),route:{route_ref:'TRUSTED_ROUTE_A',expected_revision:0}},
  ports()),'INVALID_ENVELOPE');
});
test('M11-32 inactive or revoked registry denies signed POST',async()=>{
 denied(await inspect(post(raw()),ports({registry:()=>({
  ...REG,apps:[{...appA,active:false},appB]})})), 'HMAC_OR_SCOPE_DENIED');
});
test('M11-33 unknown route fails closed with valid signature',async()=>{
 const q={...post(raw()),route:{route_ref:'UNKNOWN',expected_revision:4}};
 denied(await inspect(q,ports()),'HMAC_OR_SCOPE_DENIED');
});
test('M11-34 unexpected non-ASCII or CRLF header refused',async()=>{
 const q=post(raw());q.headers.push(['X-Test','one\r\nX-Evil: yes']);
 denied(await inspect(q,ports()),'INVALID_ENVELOPE');
});
test('M11-35 accessors are never executed while snapshotting headers',async()=>{
 let touched=0;const q=post(raw());
 Object.defineProperty(q.headers[0],'1',{enumerable:true,
  get(){touched++;throw Error('getter touched');}});
 denied(await inspect(q,ports()),'INVALID_ENVELOPE');
 assert.equal(touched,0);
});
test('M11-36 malicious Proxy in header list rejected without throwing',async()=>{
 const q={...post(raw()),headers:new Proxy([['Content-Type','application/json']],
  {ownKeys(){throw Error('proxy');}})};
 denied(await inspect(q,ports()),'INVALID_ENVELOPE');
});
test('M11-37 asynchronous port must not see mutated POST caller bytes',async()=>{
 const original=raw(),q=post(original);
 const p=inspect(q,ports({registry:()=>REG}));
 original.fill(0);
 const out=await p;
 assert.equal(out.decision,'LAB_SIGNED_SINGLE_CHANNEL_UNCOMMITTED');
 flags(out);
});
test('M11-38 async mutation of header value does not change captured signature',async()=>{
 const data=raw(),q=post(data);
 const p=inspect(q,ports());
 q.headers[1][1]=sign(data,otherPOST);
 const out=await p;flags(out);
 assert.equal(out.decision,'LAB_SIGNED_SINGLE_CHANNEL_UNCOMMITTED');
});
test('M11-39 missing port dependency denies without HTTP output',async()=>{
 denied(await inspect(post(raw()),null as unknown as TrustedRoutingPorts),
  'INVALID_ENVELOPE');
});
test('M11-40 secret resolution failure not disclosed to caller',async()=>{
 const q=post(raw());
 const x=await inspect(q,{
  currentRegistry:()=>REG,nowMs:()=>NOW,
  resolveSecret:()=>{throw Error('PRIVATE_VAULT_DETAILS');},
 });denied(x,'HMAC_OR_SCOPE_DENIED');
 assert.equal(JSON.stringify(x).includes('PRIVATE_VAULT_DETAILS'),false);
});
test('M11-41 stale App revision fails before technical classification',async()=>{
 const q={...post(raw()),route:{route_ref:'TRUSTED_ROUTE_A',expected_revision:3}};
 denied(await inspect(q,ports()),'HMAC_OR_SCOPE_DENIED');
});
test('M11-42 no partial output for one invalid channel in mixed batch',async()=>{
 const data=raw([makeEntry(),makeEntry('100002','99999999999','wamid.M2')]);
 const x=await inspect(post(data),ports());denied(x,'HMAC_OR_SCOPE_DENIED');
});
test('M11-43 identical repeated webhook is NOT deduplication/ACK authority',async()=>{
 const q=post(raw()),v1=await inspect(q,ports()),v2=await inspect(q,ports());
 flags(v1);flags(v2);assert.deepEqual(v1,v2);
 assert.equal('deduplicated' in v1,false);
});
test('M11-44 fail on duplicated unrelated header (no HTTP parser ambiguity)',async()=>{
 const q=post(raw());q.headers.push(['X-Example','a'],['x-example','b']);
 denied(await inspect(q,ports()),'AMBIGUOUS_HEADERS');
});


test('AUD-M11-01 GET revocation during token lookup denies challenge',async()=>{
 let revoked=false;
 const scope=ports({
  registry:()=>({...REG,apps:[{...appA,active:!revoked},appB]}),
  secret:(slot)=>{revoked=true;return slot==='WA11_GET_A'?GET_KEY:undefined;},
 });
 denied(await inspect(get(),scope),'ROUTING_OR_VERIFICATION_DENIED');
});
test('AUD-M11-02 POST revocation during HMAC secret lookup denies batch',async()=>{
 let revoked=false;
 const scope=ports({
  registry:()=>({...REG,apps:[{...appA,active:!revoked},appB]}),
  secret:(slot)=>{revoked=true;return slot==='WA11_POST_A'?POST_KEY:undefined;},
 });
 denied(await inspect(post(raw()),scope),'HMAC_OR_SCOPE_DENIED');
});
test('AUD-M11-03 header list with getter is denied without executing it',async()=>{
 let n=0;const q=post(raw());
 const header=q.headers[1];
 Object.defineProperty(q.headers,'1',{enumerable:true,configurable:true,
  get(){n++;return header;}});
 denied(await inspect(q,ports()),'INVALID_ENVELOPE');
 assert.equal(n,0);
});
test('AUD-M11-04 GET with forged two-purpose slot registry is denied',async()=>{
 const forged={...REG,apps:[{...appA,secret_slots:{
  ...appA.secret_slots,post_app_secret:appA.secret_slots.get_verify_token}},appB]};
 denied(await inspect(get(),ports({registry:()=>forged})),
  'ROUTING_OR_VERIFICATION_DENIED');
});
