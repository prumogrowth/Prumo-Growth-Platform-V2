/** Pure offline Graph wire observations — never a real HTTP client. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {classifyCloudWireObservation as classify} from './cloud-wire-observation.ts';
const A='ATTEMPT_META_CONTRACT_1',C='CORR_META_CONTRACT_1';
const JSON_HEADERS={'Content-Type':'application/json'};
const B=(data:unknown)=>Buffer.from(JSON.stringify(data),'utf8');
const snap=(http_status:number,body:unknown,headers:Record<string,string>=JSON_HEADERS)=>({
 kind:'http_response',http_status,headers,response_bytes:B(body),
});
const check=(result:ReturnType<typeof classify>)=>{
 assert.equal(Object.isFrozen(result),true);
 assert.equal(result.ack_allowed,false);
 assert.equal(result.send_authorized,false);
 assert.equal(result.production_authorized,false);
 assert.equal(result.delivery_confirmed,false);
 assert.equal(result.s0_write_authorized,false);
 assert.equal(result.case_transition_authorized,false);
 assert.equal(result.retry_automatically,false);
 assert.ok(!('response_json' in result));
 assert.ok(!('raw_body' in result));
 return result;
};
test('WIRE-01 not attempted is not an HTTP observation and needs no retry',()=>{
 const v=check(classify(A,C,{kind:'not_attempted'}));
 assert.equal(v.outcome,'NOT_ATTEMPTED');assert.equal(v.reason,'NO_DISPATCH');
 assert.equal(v.requires_authorized_reconciliation,false);assert.equal(v.http_status,null);
});
test('WIRE-02 lost connection always uncertain, with no automatic retry',()=>{
 const v=check(classify(A,C,{kind:'transport_error'}));
 assert.equal(v.reason,'EXTERNAL_UNCERTAIN');assert.equal(v.send_state,'UNCERTAIN_EXTERNAL');
 assert.equal(v.requires_authorized_reconciliation,true);
});
test('WIRE-03 accepted Graph reply is not delivered/read or business authorized',()=>{
 const v=check(classify(A,C,snap(200,{messaging_product:'whatsapp',
  contacts:[{input:'test',wa_id:'5581900000000'}],
  messages:[{id:'wamid.SIMULATED_100'}]})));
 assert.equal(v.outcome,'OBSERVED');
 assert.equal(v.reason,'GRAPH_API_ACCEPTED_NOT_DELIVERED');
 assert.equal(v.send_state,'API_ACCEPTED');assert.equal(v.provider_message_id,'wamid.SIMULATED_100');
 assert.equal(v.requires_authorized_reconciliation,false);
});
test('WIRE-04 202 valid Graph acceptance is not webhook ACK',()=>{
 const v=check(classify(A,C,snap(202,{messages:[{id:'wamid.B'}]})));
 assert.equal(v.send_state,'API_ACCEPTED');assert.equal(v.ack_allowed,false);
});
test('WIRE-05 invalid 200 receipt has uncertain external outcome',()=>{
 const v=check(classify(A,C,snap(200,{messages:[]})));
 assert.equal(v.reason,'INVALID_RESPONSE_UNCERTAIN');
 assert.equal(v.send_state,'UNCERTAIN_EXTERNAL');
 assert.equal(v.requires_authorized_reconciliation,true);
});
test('WIRE-06 rate limited 429 yields sanitized numeric cooldown hint, NO retry',()=>{
 const v=check(classify(A,C,snap(429,{
  error:{code:130429,error_subcode:0,message:'PRIVATE PHONE AND TOKEN'}},
  {'Content-Type':'application/json','Retry-After':'120'})));
 assert.equal(v.reason,'RATE_LIMIT_UNCERTAIN');
 assert.equal(v.send_state,'UNCERTAIN_EXTERNAL');
 assert.equal(v.meta_error_code,130429);
 assert.equal(v.retry_after_hint_seconds,120);
 assert.equal(v.requires_authorized_reconciliation,true);
 assert.equal(JSON.stringify(v).includes('PRIVATE'),false);
});
test('WIRE-07 429 with HTTP date does not invent cooldown scheduling',()=>{
 const v=check(classify(A,C,snap(429,{error:{code:4}},{
  'Content-Type':'application/json','retry-after':'Wed, 21 Oct 2030 07:28:00 GMT'})));
 assert.equal(v.reason,'RATE_LIMIT_UNCERTAIN');
 assert.equal(v.retry_after_hint_seconds,null);
});
test('WIRE-08 503 has advisory seconds, still hold uncertain',()=>{
 const v=check(classify(A,C,snap(503,{error:{code:131056}},{
  'content-type':'application/json','retry-after':'30'})));
 assert.equal(v.reason,'EXTERNAL_UNCERTAIN');
 assert.equal(v.retry_after_hint_seconds,30);
 assert.equal(v.requires_authorized_reconciliation,true);
});
test('WIRE-09 reject exaggerated, decimal and signed retry headers as hint',()=>{
 for(const value of ['86401','0007','+3','1.5','-1','NaN','9999999999999']){
  const v=check(classify(A,C,snap(429,{error:{code:4}},{
   'content-type':'application/json','retry-after':value})));
  assert.equal(v.retry_after_hint_seconds,null,value);
  assert.equal(v.send_state,'UNCERTAIN_EXTERNAL');
 }
});
test('WIRE-10 definitive 400 Graph error: no automatic resending',()=>{
 const v=check(classify(A,C,snap(400,{error:{code:100,error_subcode:33,
  message:'private message should never surface',error_data:{details:'PII'}}})));
 assert.equal(v.send_state,'PROVIDER_REJECTED');
 assert.equal(v.reason,'PROVIDER_REJECTION');
 assert.equal(v.meta_error_code,100);assert.equal(v.meta_error_subcode,33);
 assert.equal(v.requires_authorized_reconciliation,false);
 assert.equal(JSON.stringify(v).includes('private message'),false);
});
test('WIRE-11 401/403 token or permission errors do not disclose secrets',()=>{
 for(const status of [401,403]){
  const v=check(classify(A,C,snap(status,{error:{code:190,
   message:'SECRET token leaked in provider text'}})));
  assert.equal(v.send_state,'PROVIDER_REJECTED');
  assert.equal(v.meta_error_code,190);
  assert.equal(JSON.stringify(v).includes('SECRET'),false);
 }
});
test('WIRE-12 timeouts, early and 5xx are always ambiguous',()=>{
 for(const status of [408,425,500,502,504]){
  const v=check(classify(A,C,snap(status,{error:{code:4}})));
  assert.equal(v.send_state,'UNCERTAIN_EXTERNAL',String(status));
  assert.equal(v.requires_authorized_reconciliation,true);
 }
});
test('WIRE-13 unexpected redirect is not a safe Graph retry',()=>{
 const v=check(classify(A,C,snap(302,{location:'https://untrusted.example'})));
 assert.equal(v.reason,'EXTERNAL_UNCERTAIN');
 assert.equal(v.send_state,'UNCERTAIN_EXTERNAL');
});
test('WIRE-14 invalid or absent Content-Type on 2xx is ambiguous',()=>{
 for(const headers of [{},{'Content-Type':'text/html'}]){
  const v=check(classify(A,C,snap(200,{messages:[{id:'wamid.SHOULD_NOT_ACCEPT'}]},headers)));
  assert.equal(v.send_state,'UNCERTAIN_EXTERNAL');
  assert.equal(v.provider_message_id,null);
 }
});
test('WIRE-15 malformed JSON and UTF-8 cannot create Graph acceptance',()=>{
 for(const data of [Buffer.from('{"messages":'),Buffer.from([0x7b,0xff,0x7d])]){
  const v=check(classify(A,C,{kind:'http_response',http_status:200,
   headers:JSON_HEADERS,response_bytes:data}));
  assert.equal(v.reason,'INVALID_RESPONSE_UNCERTAIN');
  assert.equal(v.provider_message_id,null);
 }
});
test('WIRE-16 oversized 2xx response refused before trusted JSON parse',()=>{
 const v=check(classify(A,C,{kind:'http_response',http_status:200,
  headers:JSON_HEADERS,response_bytes:Buffer.from(' '.repeat(65537))}));
 assert.equal(v.reason,'INVALID_RESPONSE_UNCERTAIN');
 assert.equal(v.send_state,'UNCERTAIN_EXTERNAL');
});
test('WIRE-17 duplicate content-type headers are untrusted, even if case differs',()=>{
 const v=check(classify(A,C,snap(200,{messages:[{id:'wamid.A'}]},{
  'Content-Type':'application/json','content-type':'application/json'})));
 assert.equal(v.outcome,'UNTRUSTED_SNAPSHOT');assert.equal(v.reason,'UNTRUSTED_INPUT');
 assert.equal(v.provider_message_id,null);
});
test('WIRE-18 header injection/accessor/proxy never leaks data',()=>{
 const h=Object.defineProperty({},'content-type',{enumerable:true,
  get(){throw new Error('SENSITIVE SECRET');}});
 const v=check(classify(A,C,snap(200,{messages:[{id:'wamid.A'}]},h)));
 assert.equal(v.outcome,'UNTRUSTED_SNAPSHOT');
 assert.equal(JSON.stringify(v).includes('SENSITIVE'),false);
 const j=check(classify(A,C,snap(200,{messages:[{id:'wamid.A'}]},{
  'Content-Type':'application/json\r\nAuthorization: Bearer SECRET'})));
 assert.equal(j.outcome,'UNTRUSTED_SNAPSHOT');
});
test('WIRE-19 reject caller-forged extra keys or getters on observation',()=>{
 for(const data of [
  {...snap(200,{messages:[{id:'wamid.A'}]}),send_authorized:true},
  Object.defineProperty({},'kind',{enumerable:true,get(){throw Error('token');}}),
  {kind:'http_response',http_status:200,headers:JSON_HEADERS,response_bytes:'not-buffer'},
 ]){
  const v=check(classify(A,C,data));
  assert.equal(v.outcome,'UNTRUSTED_SNAPSHOT');
 }
});
test('WIRE-20 preserve safe metadata without exporting Authorization header',()=>{
 const v=check(classify(A,C,snap(200,{messages:[{id:'wamid.SAFE'}]},{
  'Content-Type':'application/json; charset=UTF-8',
  'Authorization':'Bearer DO_NOT_LOG',
  'X-Internal-Token':'DO_NOT_LOG',
 })));
 assert.equal(v.send_state,'API_ACCEPTED');
 assert.equal(JSON.stringify(v).includes('DO_NOT_LOG'),false);
 assert.equal(v.retry_after_hint_seconds,null);
});
