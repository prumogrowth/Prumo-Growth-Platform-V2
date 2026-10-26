/**
 * Pure Graph Cloud API wire-observation normalizer for FUTURE homologation.
 * No fetch, transport, auth, database, retries, Graph POST or webhook ACK.
 *
 * This processes a *scripted or trusted-transport* snapshot; it CANNOT prove
 * that a network request was authorized or that a result was persisted by S0.
 * Existing graph-outbound.ts owns the provider-result classification.
 */
import {classifyGraphSendResult, type GraphSendOutcome} from './graph-outbound.ts';

type WireInput =
 | Readonly<{kind:'not_attempted'}>
 | Readonly<{kind:'transport_error'}>
 | Readonly<{kind:'http_response';http_status:number;
     headers:Readonly<Record<string,string>>;response_bytes:Uint8Array}>;

export type CloudWireDecision=Readonly<{
 outcome:'NOT_ATTEMPTED'|'OBSERVED'|'UNTRUSTED_SNAPSHOT';
 reason:'NO_DISPATCH'|'GRAPH_API_ACCEPTED_NOT_DELIVERED'|
 'PROVIDER_REJECTION'|'RATE_LIMIT_UNCERTAIN'|'EXTERNAL_UNCERTAIN'|
 'INVALID_RESPONSE_UNCERTAIN'|'UNTRUSTED_INPUT';
 send_state:GraphSendOutcome['send_state']|null;
 http_status:number|null;
 /** Only validated wamid; not evidence of sent, delivered, or read. */
 provider_message_id:string|null;
 meta_error_code:number|null;
 meta_error_subcode:number|null;
 /** Diagnostic for 429/503 only. This NEVER schedules an external retry. */
 retry_after_hint_seconds:number|null;
 requires_authorized_reconciliation:boolean;
 retry_automatically:false;
 ack_allowed:false;
 send_authorized:false;
 production_authorized:false;
 delivery_confirmed:false;
 case_transition_authorized:false;
 s0_write_authorized:false;
}>;

const ID=/^[A-Za-z0-9_.:-]{1,128}$/;
const FLAGS=Object.freeze({
 retry_automatically:false,ack_allowed:false,send_authorized:false,
 production_authorized:false,delivery_confirmed:false,
 case_transition_authorized:false,s0_write_authorized:false,
} as const);
const empty=(outcome:CloudWireDecision['outcome'],
 reason:CloudWireDecision['reason'],reconciliation=false):CloudWireDecision=>
 Object.freeze({...FLAGS,outcome,reason,send_state:null,http_status:null,
  provider_message_id:null,meta_error_code:null,meta_error_subcode:null,
  retry_after_hint_seconds:null,requires_authorized_reconciliation:reconciliation});

function record(value:unknown,required:readonly string[]):Record<string,unknown>|null{
 try{
  if(!value||typeof value!=='object'||Array.isArray(value))return null;
  const proto=Object.getPrototypeOf(value);
  if(proto!==Object.prototype&&proto!==null)return null;
  const keys=Reflect.ownKeys(value);
  if(keys.length!==required.length||keys.some(k=>typeof k!=='string'))return null;
  const d=Object.getOwnPropertyDescriptors(value);
  if(!required.every(k=>Object.hasOwn(d,k)&&Object.hasOwn(d[k],'value')))return null;
  return Object.fromEntries(required.map(k=>[k,d[k].value]));
 }catch{return null;}
}
function hints(raw:unknown):{contentType:string|null;retryAfter:number|null}|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const ds=Object.getOwnPropertyDescriptors(raw),keys=Reflect.ownKeys(raw);
  if(keys.length>64||keys.some(k=>typeof k!=='string'))return null;
  const found=new Map<string,string>();
  for(const key of keys as string[]){
   const d=ds[key],name=key.toLowerCase();
   if(!d||!Object.hasOwn(d,'value')||typeof d.value!=='string'||
      d.value.length>256||/[\r\n\u0000-\u001f\u007f]/.test(d.value))return null;
   if(name==='content-type'||name==='retry-after'){
    if(found.has(name))return null;
    found.set(name,d.value.trim());
   }
  }
  const retry=found.get('retry-after')??'';
  // HTTP-date Retry-After is deliberately NOT scheduled without a trusted clock.
  const retryAfter=/^(0|[1-9]\d{0,5})$/.test(retry)
    ? Number(retry)<=86400?Number(retry):null:null;
  return {contentType:found.get('content-type')??null,retryAfter};
 }catch{return null;}
}
function parseJson(bytes:Uint8Array,ctype:string|null):unknown{
 if(!ctype||!/^application\/json(?:\s*;\s*charset\s*=\s*"?utf-8"?)?$/i.test(ctype))
  throw Error('CONTENT_TYPE');
 if(bytes.byteLength<1||bytes.byteLength>65536)throw Error('BOUNDED_RESPONSE');
 const text=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);
 if(!text||text.charCodeAt(0)===0xfeff)throw Error('INVALID_UTF8_BOM');
 return JSON.parse(text);
}
/** Parse only the response bytes from a trusted transport, never send them. */
export function classifyCloudWireObservation(
 attemptId:string,correlationId:string,observation:unknown,
):CloudWireDecision{
 if(typeof attemptId!=='string'||!ID.test(attemptId)||
    typeof correlationId!=='string'||!ID.test(correlationId))
  return empty('UNTRUSTED_SNAPSHOT','UNTRUSTED_INPUT');
 const base=record(observation,['kind']);
 if(base?.kind==='not_attempted')return empty('NOT_ATTEMPTED','NO_DISPATCH');
 if(base?.kind==='transport_error'){
  const r=classifyGraphSendResult(attemptId,correlationId,{kind:'transport_error'});
  return Object.freeze({...FLAGS,outcome:'OBSERVED' as const,
   reason:'EXTERNAL_UNCERTAIN' as const,send_state:r.send_state,
   http_status:r.http_status,provider_message_id:null,meta_error_code:null,
   meta_error_subcode:null,retry_after_hint_seconds:null,
   requires_authorized_reconciliation:true});
 }
 const full=record(observation,['kind','http_status','headers','response_bytes']);
 if(!full||full.kind!=='http_response'||!Number.isSafeInteger(full.http_status)||
    (full.http_status as number)<100||(full.http_status as number)>599 ||
    !(full.response_bytes instanceof Uint8Array))
  return empty('UNTRUSTED_SNAPSHOT','UNTRUSTED_INPUT',true);
 const h=hints(full.headers);
 if(!h)return empty('UNTRUSTED_SNAPSHOT','UNTRUSTED_INPUT',true);
 let body:unknown=null,parseOk=false;
 try{
  body=parseJson(full.response_bytes,h.contentType);
  parseOk=true;
 }catch{/* Fail closed: HTTP success without trusted structured reply = unknown */}
 const status=full.http_status as number;
 // A real provider response code can still be meaningful if error JSON is
 // missing; 408, 425, 429 and 5xx remain UNCERTAIN, not automatic retries.
 let classified:GraphSendOutcome;
 try{
  classified=classifyGraphSendResult(attemptId,correlationId,{
   kind:'http_response',http_status:status,response_json:parseOk?body:null,
  });
 }catch{
  return empty('UNTRUSTED_SNAPSHOT','UNTRUSTED_INPUT',true);
 }
 let reason:CloudWireDecision['reason'];
 if(status===429)reason='RATE_LIMIT_UNCERTAIN';
 else if(classified.send_state==='API_ACCEPTED')
  reason='GRAPH_API_ACCEPTED_NOT_DELIVERED';
 else if(classified.send_state==='PROVIDER_REJECTED')
  reason='PROVIDER_REJECTION';
 else reason=(status>=200&&status<300)?'INVALID_RESPONSE_UNCERTAIN':'EXTERNAL_UNCERTAIN';
 const uncertain=classified.send_state==='UNCERTAIN_EXTERNAL';
 return Object.freeze({...FLAGS,outcome:'OBSERVED' as const,reason,
  send_state:classified.send_state,http_status:classified.http_status,
  provider_message_id:classified.provider_message_id,
  meta_error_code:classified.meta_error_code,
  meta_error_subcode:classified.meta_error_subcode,
  retry_after_hint_seconds:(status===429||status===503)?h.retryAfter:null,
  requires_authorized_reconciliation:uncertain});
}
