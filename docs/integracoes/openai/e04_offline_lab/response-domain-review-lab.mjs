/**
 * OFF-21 — An isolated, synthetic Responses -> F01/F02/F03 domain evaluator.
 *
 * This component has no model SDK, database, network, stdout, disk, events,
 * external side effects or authorization. It never exposes a model draft,
 * citations, private IDs, S0 snapshots or raw model text in ANY result.
 *
 * The caller must supply a minted LAB handle and an explicit second S0-like
 * fixture. It is NOT authenticated S0; on success this is still review-only.
 */
import {OAI_RESPONSE_LAB_INPUT,inspectResponsesShape}
  from './responses-shape-preflight-lab.mjs';
import {evaluateF01Model} from './f01-sales-boundary.mjs';
import {evaluateF02Model} from './f02-plan-boundary.mjs';
import {reviewF03Extraction} from './f03-history-boundary.mjs';

export const OFF21_INPUT='prumo.openai.response-domain-review/0.1-lab';
export const OFF21_RESULT='prumo.openai.response-domain-review-result/0.1-lab';
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const plain=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&
 (Object.getPrototypeOf(x)===Object.prototype||Object.getPrototypeOf(x)===null);
function shape(x,keys){
  if(!plain(x)||Reflect.ownKeys(x).length!==keys.length)return false;
  return keys.every(k=>{
    const d=Object.getOwnPropertyDescriptor(x,k);
    return d&&own(d,'value');
  })&&Reflect.ownKeys(x).every(k=>typeof k==='string'&&keys.includes(k));
}
function safe(x,depth=0,seen=new Set()){
  if(depth>13)return false;
  if(x===null||typeof x==='boolean'||typeof x==='string')return true;
  if(typeof x==='number')return Number.isFinite(x);
  if(typeof x!=='object'||seen.has(x)||(!plain(x)&&!Array.isArray(x)))return false;
  if(Array.isArray(x)&&(x.length>150||Object.keys(x).length!==x.length))return false;
  seen.add(x);
  try{
    for(const k of Reflect.ownKeys(x)){
      if(typeof k!=='string'||['__proto__','constructor','prototype'].includes(k))return false;
      const d=Object.getOwnPropertyDescriptor(x,k);
      if(!d||!own(d,'value')||!safe(d.value,depth+1,seen))return false;
      if(Array.isArray(x)&&k!=='length'&&
        (!/^(0|[1-9]\d*)$/.test(k)||Number(k)>=x.length))return false;
    }
    return true;
  }finally{seen.delete(x);}
}
const FLAG=Object.freeze({
  s0Authenticated:false,providerAuthenticated:false,
  sourceAuthenticated:false,modelInvocationAuthorized:false,
  modelOutputTrusted:false,semanticVerified:false,
  publishAuthorized:false,sendAuthorized:false,schedulingAuthorized:false,
  fieldApplicationAuthorized:false,commercialTransitionAuthorized:false,
  productionAuthorized:false,modelCalled:false,liveApiCalled:false,
  rawModelOutputExposed:false,domainProposalExposed:false,
  requiresS0TransactionalRecheck:true
});
const result=(status,stage,operation)=>Object.freeze({
  schemaVersion:OFF21_RESULT,status,stage,
  operation:['F01','F02','F03'].includes(operation)?operation:'UNKNOWN',
  ...FLAG
});
const F01_KEYS=['nowMs','currentScope','prior'];
const F02_KEYS=['nowMs','scope'];
const F03_KEYS=['currentScope','prior'];
const PRE_STATUSES=new Set(['INVALID_INPUT','TRANSPORT_UNKNOWN','DENIED',
  'REVIEW_REQUIRED','LATE_RESPONSE','AWAITING_PROVIDER','INCOMPLETE_RESPONSE',
  'PROVIDER_TERMINATED','UNEXPECTED_OUTPUT','AMBIGUOUS_MESSAGES',
  'EMPTY_OUTPUT','AMBIGUOUS_CONTENT','MODEL_REFUSAL','UNEXPECTED_CONTENT',
  'SCHEMA_INVALID']);
const DOMAIN_STATUSES=new Set(['DENIED','STALE','INVALID_INPUT','SCHEMA_INVALID',
  'SOURCE_INVALID','REVIEW_REQUIRED','MODEL_FAILURE','MODEL_REFUSAL',
  'ALREADY_HANDLED','ALREADY_HANDLED_REVIEW_ONLY','REPLAY_CONFLICT',
  'LATE_RESPONSE','S0_RECHECK_ONLY','PROPOSED']);
/**
 * Passing a forged handle, an accessor, a wrong operation, a stale version or
 * a provider tool call cannot grant anything. No domain proposal leaves this
 * function, even when the domain evaluator returns a private one.
 */
export function reviewResponseThroughDomain(input){
  try{
    if(!shape(input,['schemaVersion','preflightInput','prepared','recheck'])||
       input.schemaVersion!==OFF21_INPUT)return result('INVALID_INPUT','ENVELOPE');
    const p=input.preflightInput;
    // Inspect untrusted transport first; never read raw outside this point.
    const pre=inspectResponsesShape(p);
    if(pre.status!=='UNTRUSTED_JSON_CANDIDATE'){
      return result('PREFLIGHT_BLOCKED',
        PRE_STATUSES.has(pre.status)?pre.status:'UNKNOWN','UNKNOWN');
    }
    const op=p.operation;
    if(!safe(input.recheck))return result('INVALID_INPUT','RECHECK',op);
    if(op==='F01'&&!shape(input.recheck,F01_KEYS)||
       op==='F02'&&!shape(input.recheck,F02_KEYS)||
       op==='F03'&&!shape(input.recheck,F03_KEYS))
      return result('INVALID_INPUT','RECHECK',op);
    // The preflight has already validated a normalized single completed
    // message with a single output_text item and strict JSON correlation.
    const raw=p.response.output.find(x=>x.type==='message').content[0].text;
    let domain;
    if(op==='F01'){
      domain=evaluateF01Model(input.prepared,raw,input.recheck);
    }else if(op==='F02'){
      domain=evaluateF02Model(input.prepared,raw,input.recheck);
    }else if(op==='F03'){
      domain=reviewF03Extraction(input.prepared,raw,input.recheck);
    }else{
      return result('INVALID_INPUT','OPERATION');
    }
    const status=DOMAIN_STATUSES.has(domain?.status)?domain.status:'UNKNOWN';
    if((op==='F01'||op==='F02')&&status==='S0_RECHECK_ONLY'||
       op==='F03'&&status==='PROPOSED')
      return result('LAB_DOMAIN_REVIEW_ONLY','NO_S0_AUTHORITY',op);
    if(status==='REVIEW_REQUIRED')
      return result('LAB_DOMAIN_REVIEW_REQUIRED','NO_S0_AUTHORITY',op);
    // Do not propagate any private/domain status to an external caller:
    // only sanitize a known generic reason, never the model text or draft.
    return result('LAB_DOMAIN_BLOCKED',status,op);
  }catch{return result('INVALID_INPUT','EXCEPTION');}
}
