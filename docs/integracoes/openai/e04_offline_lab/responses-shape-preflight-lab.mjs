/**
 * OFF-16 — Responses API-shaped laboratory output gate.
 * NO OpenAI SDK, fetch(), HTTP, API key, clock, disk, SQL, customer data,
 * model invocation, retry, tools or business effects.
 *
 * Accepts a narrowly normalized SYNTHETIC Responses object. The production
 * provider adapter / auth / S0 readback / pricing must be separately approved.
 */
import {parseStrictJSON} from './typed-boundary.mjs';
import {F01_RESPONSE} from './f01-sales-boundary.mjs';
import {F02_RESPONSE} from './f02-plan-boundary.mjs';
import {F03_PROPOSAL_SCHEMA} from './f03-history-boundary.mjs';

export const OAI_RESPONSE_LAB_INPUT='prumo.openai.responses-preflight/0.1-lab';
export const OAI_RESPONSE_LAB_RESULT='prumo.openai.responses-preflight-result/0.2-lab';
const EXPECTED=Object.freeze({F01:F01_RESPONSE,F02:F02_RESPONSE,F03:F03_PROPOSAL_SCHEMA});
const ID=/^[A-Za-z0-9_.:-]{1,120}$/;
const has=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const plain=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&
 (Object.getPrototypeOf(x)===Object.prototype||Object.getPrototypeOf(x)===null);
const exact=(x,keys)=>plain(x)&&Reflect.ownKeys(x).length===keys.length&&
 keys.every(k=>has(x,k))&&Reflect.ownKeys(x).every(k=>typeof k==='string'&&keys.includes(k));
const id=x=>typeof x==='string'&&ID.test(x);
const nat=x=>Number.isSafeInteger(x)&&x>=0;
const array=(a,max)=>Array.isArray(a)&&a.length<=max&&Object.keys(a).length===a.length&&
 Reflect.ownKeys(a).every(k=>k==='length'||/^(0|[1-9]\d*)$/.test(String(k)));
function safe(x,depth=0,seen=new Set()){
  if(depth>11)return false;
  if(x===null||typeof x==='boolean')return true;
  if(typeof x==='string')return x.length<=12000;
  if(typeof x==='number')return Number.isFinite(x);
  if(typeof x!=='object'||seen.has(x)||(!plain(x)&&!Array.isArray(x)))return false;
  if(Array.isArray(x)&&!array(x,8))return false;
  seen.add(x);
  try{
    for(const k of Reflect.ownKeys(x)){
      if(typeof k!=='string'||['__proto__','constructor','prototype'].includes(k))return false;
      const d=Object.getOwnPropertyDescriptor(x,k);
      if(!d||!has(d,'value')||!safe(d.value,depth+1,seen))return false;
    }
    return true;
  }finally{seen.delete(x);}
}
const FLAGS=Object.freeze({
  providerAuthenticated:false,sourceS0Authenticated:false,
  modelInvocationAuthorized:false,modelOutputTrusted:false,
  responseSemanticsValidated:false,modelContentAuthorized:false,
  publishAuthorized:false,schedulingAuthorized:false,
  sendAuthorized:false,fieldApplicationAuthorized:false,
  productionAuthorized:false,requiresS0Recheck:true,
  costApproved:false,liveApiCalled:false,
  candidateRawExposed:false,requiresDomainEvaluation:true
});
const verdict=(status,stage)=>Object.freeze({
  schemaVersion:OAI_RESPONSE_LAB_RESULT,status,stage,...FLAGS
});
function requestValid(x){
  return exact(x,['schemaVersion','operation','providerTag','modelRef','startedAtMs',
    'observedAtMs','deadlineMs','response'])&&
    x.schemaVersion===OAI_RESPONSE_LAB_INPUT&&has(EXPECTED,x.operation)&&
    id(x.providerTag)&&id(x.modelRef)&&
    nat(x.startedAtMs)&&nat(x.observedAtMs)&&nat(x.deadlineMs)&&
    x.deadlineMs>x.startedAtMs;
}
function responseValid(x){
  return exact(x,['id','model','status','output','error','incomplete_details'])&&
    id(x.id)&&id(x.model)&&
    ['completed','queued','in_progress','incomplete','failed','cancelled'].includes(x.status)&&
    array(x.output,8)&&
    (x.error===null||exact(x.error,['code'])&&id(x.error.code))&&
    (x.incomplete_details===null||
      exact(x.incomplete_details,['reason'])&&id(x.incomplete_details.reason));
}
function inspectOutput(items){
  let message=null;
  for(const item of items){
    // Reasoning outputs are not forwarded to any downstream consumer.
    if(exact(item,['type'])&&item.type==='reasoning')continue;
    if(!exact(item,['type','role','status','content'])||item.type!=='message'||
       item.role!=='assistant'||item.status!=='completed'||!array(item.content,3))
      return {status:'UNEXPECTED_OUTPUT'};
    if(message!==null)return {status:'AMBIGUOUS_MESSAGES'};
    message=item;
  }
  if(message===null)return {status:'EMPTY_OUTPUT'};
  if(message.content.length!==1)return {status:'AMBIGUOUS_CONTENT'};
  const item=message.content[0];
  if(exact(item,['type','refusal'])&&item.type==='refusal'&&typeof item.refusal==='string')
    return {status:'MODEL_REFUSAL'};
  if(!exact(item,['type','text'])||item.type!=='output_text'||
     typeof item.text!=='string'||item.text.length>10000||item.text.length===0)
    return {status:'UNEXPECTED_CONTENT'};
  return {status:'UNTRUSTED_TEXT',raw:item.text};
}
/**
 * Structural inspection intentionally never returns raw model content.
 * A later trusted transport must separately deliver untrusted text to the
 * F01/F02/F03 domain evaluator; neither this gate nor a JSON candidate
 * can grant S0 authority, semantic correctness, sending or field writes.
 * Breaking change from lab result 0.1: candidateRaw is REMOVED.
 */
export function inspectResponsesShape(input){
  try{
    if(!safe(input)||!requestValid(input))return verdict('INVALID_INPUT','REQUEST');
    const {response:r}=input;
    if(r===null)return verdict('TRANSPORT_UNKNOWN','NO_RESPONSE');
    if(!responseValid(r))return verdict('INVALID_INPUT','RESPONSE');
    if(r.model!==input.modelRef)return verdict('DENIED','MODEL_MISMATCH');
    if(input.observedAtMs<input.startedAtMs)return verdict('REVIEW_REQUIRED','CLOCK');
    if(input.observedAtMs>input.deadlineMs)return verdict('LATE_RESPONSE','DEADLINE');
    if(r.status==='queued'||r.status==='in_progress')
      return verdict('AWAITING_PROVIDER','NOT_FINAL');
    if(r.status==='incomplete')
      return verdict('INCOMPLETE_RESPONSE','NO_CANDIDATE');
    if(r.status==='failed'||r.status==='cancelled')
      return verdict('PROVIDER_TERMINATED','NO_CANDIDATE');
    if(r.error!==null||r.incomplete_details!==null)
      return verdict('REVIEW_REQUIRED','CONFLICTING_PROVIDER_STATE');
    const candidate=inspectOutput(r.output);
    if(candidate.status!=='UNTRUSTED_TEXT')
      return verdict(candidate.status,'CONTENT');
    const parsed=parseStrictJSON(candidate.raw);
    if(parsed.status!=='PARSED'||!plain(parsed.value)||
       parsed.value.schemaVersion!==EXPECTED[input.operation]||
       parsed.value.providerTag!==input.providerTag)
      return verdict('SCHEMA_INVALID','MODEL_JSON');
    // The evaluator for the selected F0x domain must validate the REST of
    // the proposal. We check only provider correlation and top-level schema.
    return Object.freeze({...verdict('UNTRUSTED_JSON_CANDIDATE','NO_S0_AUTHORITY'),
      operation:input.operation});
  }catch{return verdict('INVALID_INPUT','EXCEPTION');}
}
