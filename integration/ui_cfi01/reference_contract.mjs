/** Unratified UI reference; no transport, dispatcher, auth or domain effects.
 * Kept outside frontend/. Web Crypto works in browser/Node22+, but this file
 * is a proposal for joint review, not a module connected to the current UI.
 */
export const COMMAND_SCHEMA='prumo.s0.cfi01.command/0.1-candidate';
export const RESULT_SCHEMA='prumo.s0.cfi01.result/0.1-candidate';
const CAPTURE='capture_human_closure',RECHECK='recheck_human_closure';
const COMMON=['schema_version','command','request_id','correlation_id','case_ref','idempotency_key','expected_version'];
const RESULT=['schema_version','command','request_id','correlation_id','case_ref','request_fingerprint','outcome'];
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const full=(pattern,value)=>typeof value==='string'&&pattern.exec(value)?.[0]===value;
const uuid=x=>full(UUID,x);
function record(raw,keys){
 if(!raw||typeof raw!=='object'||Array.isArray(raw)||
    ![null,Object.prototype].includes(Object.getPrototypeOf(raw)))throw Error('INVALID_CFI01_CANDIDATE');
 const d=Object.getOwnPropertyDescriptors(raw),own=Reflect.ownKeys(raw);
 if(own.length!==keys.length||!keys.every(k=>Object.hasOwn(d,k)&&Object.hasOwn(d[k],'value')))
  throw Error('INVALID_CFI01_CANDIDATE');
 return Object.freeze(Object.fromEntries(keys.map(k=>[k,d[k].value])));
}
export function parseCandidateCommand(raw){
 const command=raw&&Object.getOwnPropertyDescriptor(raw,'command')?.value;
 if(![CAPTURE,RECHECK].includes(command))throw Error('INVALID_CFI01_CANDIDATE');
 const c=record(raw,command===CAPTURE?COMMON:[...COMMON,'capture_request_id']);
 if(c.schema_version!==COMMAND_SCHEMA||!['request_id','correlation_id','case_ref'].every(k=>uuid(c[k]))||
    !full(/^[A-Za-z0-9._:-]{8,128}$/,c.idempotency_key)||
    command===RECHECK&&!uuid(c.capture_request_id))throw Error('INVALID_CFI01_CANDIDATE');
 const v=record(c.expected_version,['kind','value']);
 if(typeof v.kind!=='string'||typeof v.value!=='string')throw Error('INVALID_CFI01_CANDIDATE');
 if(v.kind==='cycle'){
  if(!full(/^[1-9][0-9]{0,18}$/,v.value)||BigInt(v.value)>9223372036854775807n)throw Error('INVALID_CFI01_CANDIDATE');
 }else if(v.kind==='case'){
  if(!full(/^[A-Za-z0-9._:-]{1,128}$/,v.value))throw Error('INVALID_CFI01_CANDIDATE');
 }else throw Error('INVALID_CFI01_CANDIDATE');
 return Object.freeze({...c,expected_version:v});
}
function tuple(c,logical=false){
 return [COMMAND_SCHEMA,c.command,...(logical?[]:[c.request_id,c.correlation_id]),c.case_ref,
  c.idempotency_key,c.expected_version.kind,c.expected_version.value,c.capture_request_id??'-'];
}
async function digest(c){
 const bytes=new TextEncoder().encode(JSON.stringify(tuple(c)));
 const value=await globalThis.crypto.subtle.digest('SHA-256',bytes);
 return Array.from(new Uint8Array(value),x=>x.toString(16).padStart(2,'0')).join('');
}
export async function requestFingerprint(raw){return digest(parseCandidateCommand(raw));}
export function compareRetry(previous,current){
 const a=parseCandidateCommand(previous),b=parseCandidateCommand(current);
 if(a.command!==b.command)return 'DIFFERENT_COMMAND_NOT_A_RETRY';
 if(a.idempotency_key!==b.idempotency_key)return 'NEW_INTENT_REVIEW_REQUIRED';
 if(JSON.stringify(tuple(a,true))!==JSON.stringify(tuple(b,true)))return 'IDEMPOTENCY_CONFLICT_REVIEW_REQUIRED';
 return 'SAME_INTENT_STRUCTURE_ONLY';
}
function validState(command,state){
 return ['CONTRACT_PENDING','REVIEW_REQUIRED','DENIED','STALE','UNAVAILABLE','INPUT_REJECTED',
  command===CAPTURE?'RECORDED_REVIEW_ONLY':'RECHECKED_REVIEW_ONLY'].includes(state);
}
const denied=()=>Object.freeze({accepted:false,state:'UNTRUSTED_RESPONSE',has_verified_effect:false,may_execute:false});
export async function stageCandidateResponse(raw,request,{sentContext,getCurrentContext}={}){
 try{
  const c=parseCandidateCommand(request),r=record(raw,RESULT),o=record(r.outcome,['state','commercial_effect_confirmed']);
  if(!uuid(sentContext)||typeof getCurrentContext!=='function'||getCurrentContext()!==sentContext||
     r.schema_version!==RESULT_SCHEMA||!['command','request_id','correlation_id','case_ref'].every(k=>r[k]===c[k])||
     o.commercial_effect_confirmed!==false||!validState(c.command,o.state))return denied();
  const expected=await digest(c);
  // Digest is async. Reread the LOCAL context after await to reject an actor,
  // store, case or pending-request change while hashing; never reuse epochs.
  if(r.request_fingerprint!==expected||getCurrentContext()!==sentContext)return denied();
  return Object.freeze({accepted:true,state:o.state,has_verified_effect:false,may_execute:false});
 }catch{return denied();}
}
