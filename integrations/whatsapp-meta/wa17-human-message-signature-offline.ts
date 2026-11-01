/**
 * M17: WA-21 fixed human signature, as an entirely OFFLINE LAB preview.
 * Caller-supplied session/case data are NOT authenticated S0 assertions.
 * Neither "CLAIMED_ACTIVE" nor a positive preview verifies authorization.
 * No Graph, HTTP, SQL, send, retry, MCP, or physical author identity.
 */
import {createHash} from 'node:crypto';

export type Wa17Request=Readonly<{
 contract_version:'wa17-human-free-text-request.lab.v0.1';
 selection_ref:string;concessionaria_id:string;waba_ref:string;
 case_ref:string;intent_ref:string;
 author_origin:'HUMAN_COMPOSED';transport_kind:'FREE_TEXT';
 draft_text:string;now_ms:number;max_age_ms:number;
}>;
export type Wa17Session=Readonly<{
 contract_version:'wa17-s0-session-claim.lab.v0.1';
 concessionaria_id:string;actor_ref:string;role:'CONSULTOR'|'GESTOR'|'DIRETOR';
 display_name:string;identity_revision:number;session_revision:number;
 session_state:'CLAIMED_ACTIVE';observed_at_ms:number;
}>;
export type Wa17Case=Readonly<{
 contract_version:'wa17-s0-case-claim.lab.v0.1';
 concessionaria_id:string;waba_ref:string;case_ref:string;
 actor_ref:string;case_version:number;assignment_revision:number;
 assigned_human:true;handoff_state:'HUMAN';
 free_text_window:'CLAIMED_OPEN';can_send_free_text:true;
 opt_out:false;observed_at_ms:number;
}>;
export type Wa17Preview=Readonly<{
 contract_version:'wa17-human-prefix-preview.lab.v0.1';
 selection_ref:string;concessionaria_id:string;waba_ref:string;
 case_ref:string;intent_ref:string;actor_ref:string;
 role:'CONSULTOR'|'GESTOR'|'DIRETOR';
 display_name_snapshot:string;
 case_version:number;assignment_revision:number;identity_revision:number;
 session_revision:number;
 draft_sha256:string;composed_sha256:string;
 composed_text:string;requires_s0_recheck:true;
 identity_verified:false;authorization_verified:false;
 send_authorized:false;production_authorized:false;
 graph_dispatch_authorized:false;
}>;
export type Wa17Reason='INVALID_INPUT'|'UNTRUSTED_SCOPE'|
 'SESSION_OR_ASSIGNMENT_DENIED'|'WINDOW_OR_POLICY_DENIED'|
 'NAME_OR_BODY_DENIED'|'DUPLICATE_OR_FORGED_PREFIX'|
 'INVALID_PREVIEW'|'REVISION_OR_AUTHOR_CHANGED';
export type Wa17Result=Readonly<{
 decision:'DENIED'|'LAB_HUMAN_PREFIX_UNVERIFIED'|
 'LAB_RECHECKED_UNVERIFIED';
 reason:Wa17Reason|null;preview:Wa17Preview|null;
 identity_verified:false;authorization_verified:false;
 send_authorized:false;production_authorized:false;
 graph_dispatch_authorized:false;
}>;
const FLAGS=Object.freeze({identity_verified:false,
 authorization_verified:false,send_authorized:false,
 production_authorized:false,graph_dispatch_authorized:false} as const);
const deny=(reason:Wa17Reason):Wa17Result=>
 Object.freeze({...FLAGS,decision:'DENIED' as const,reason,preview:null});
const yes=(preview:Wa17Preview,rechecked=false):Wa17Result=>
 Object.freeze({...FLAGS,
  decision:rechecked?'LAB_RECHECKED_UNVERIFIED' as const:
    'LAB_HUMAN_PREFIX_UNVERIFIED' as const,
  reason:null,preview,
 });
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const DIGITS=/^[0-9]{5,25}$/,REF=/^[A-Za-z0-9_.:-]{1,128}$/;
const NAME=/^\p{L}[\p{L}\p{M}]+(?:[ '\-]\p{L}[\p{L}\p{M}]+)*$/u;
const SIGNATURE=/^(?:Consultor|Gestor|Diretor)\s+[^\n:]{1,120}:\s*\n/iu;
const NUMERIC=(x:unknown):x is number=>typeof x==='number'&&
 Number.isSafeInteger(x)&&x>0;
const NONNEG=(x:unknown):x is number=>typeof x==='number'&&
 Number.isSafeInteger(x)&&x>=0;
const hex=(v:unknown):v is string=>typeof v==='string'&&
 /^[a-f0-9]{64}$/.test(v);
const sha=(s:string):string=>createHash('sha256').update(s,'utf8').digest('hex');
function own(raw:unknown,required:readonly string[]):
 Record<string,unknown>|null{
 try{
  if(raw===null||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const d=Object.getOwnPropertyDescriptors(raw),keys=Reflect.ownKeys(raw);
  if(keys.length!==required.length||keys.some(k=>typeof k!=='string'||
    !required.includes(k)||!Object.hasOwn(d[k],'value'))||
    required.some(k=>!Object.hasOwn(d,k)))return null;
  return Object.fromEntries(required.map(k=>[k,d[k].value]));
 }catch{return null;}
}
const REQ=['contract_version','selection_ref','concessionaria_id',
 'waba_ref','case_ref','intent_ref','author_origin','transport_kind',
 'draft_text','now_ms','max_age_ms'] as const;
const SESSION=['contract_version','concessionaria_id','actor_ref',
 'role','display_name','identity_revision','session_revision',
 'session_state','observed_at_ms'] as const;
const CASE=['contract_version','concessionaria_id','waba_ref',
 'case_ref','actor_ref','case_version','assignment_revision',
 'assigned_human','handoff_state','free_text_window',
 'can_send_free_text','opt_out','observed_at_ms'] as const;
const PREVIEW=['contract_version','selection_ref','concessionaria_id',
 'waba_ref','case_ref','intent_ref','actor_ref','role',
 'display_name_snapshot','case_version','assignment_revision',
 'identity_revision','session_revision','draft_sha256','composed_sha256',
 'composed_text','requires_s0_recheck','identity_verified',
 'authorization_verified','send_authorized','production_authorized',
 'graph_dispatch_authorized'] as const;
function request(x:Record<string,unknown>):boolean{
 return x.contract_version==='wa17-human-free-text-request.lab.v0.1'&&
  typeof x.selection_ref==='string'&&REF.test(x.selection_ref)&&
  typeof x.concessionaria_id==='string'&&UUID.test(x.concessionaria_id)&&
  typeof x.waba_ref==='string'&&DIGITS.test(x.waba_ref)&&
  typeof x.case_ref==='string'&&REF.test(x.case_ref)&&
  typeof x.intent_ref==='string'&&REF.test(x.intent_ref)&&
  x.author_origin==='HUMAN_COMPOSED'&&x.transport_kind==='FREE_TEXT'&&
  NONNEG(x.now_ms)&&NUMERIC(x.max_age_ms)&&x.max_age_ms<=300000&&
  typeof x.draft_text==='string';
}
function session(x:Record<string,unknown>):boolean{
 return x.contract_version==='wa17-s0-session-claim.lab.v0.1'&&
  typeof x.concessionaria_id==='string'&&UUID.test(x.concessionaria_id)&&
  typeof x.actor_ref==='string'&&REF.test(x.actor_ref)&&
  ['CONSULTOR','GESTOR','DIRETOR'].includes(x.role as string)&&
  typeof x.display_name==='string'&&x.display_name.length<=80&&
  x.display_name.length>=2&&NAME.test(x.display_name)&&
  x.display_name===x.display_name.normalize('NFC')&&
  NUMERIC(x.identity_revision)&&NUMERIC(x.session_revision)&&
  x.session_state==='CLAIMED_ACTIVE'&&NONNEG(x.observed_at_ms);
}
function context(x:Record<string,unknown>):boolean{
 return x.contract_version==='wa17-s0-case-claim.lab.v0.1'&&
  typeof x.concessionaria_id==='string'&&UUID.test(x.concessionaria_id)&&
  typeof x.waba_ref==='string'&&DIGITS.test(x.waba_ref)&&
  typeof x.case_ref==='string'&&REF.test(x.case_ref)&&
  typeof x.actor_ref==='string'&&REF.test(x.actor_ref)&&
  NUMERIC(x.case_version)&&NUMERIC(x.assignment_revision)&&
  x.assigned_human===true&&x.handoff_state==='HUMAN'&&
  NONNEG(x.observed_at_ms);
}
function fresh(now:number,observed:number,maxAge:number):boolean{
 return observed<=now&&now-observed<=maxAge;
}
function bodyOk(text:string,prefix:string):Wa17Reason|null{
 // Avoid ambiguous display/control characters and intentionally disallow
 // a user-typed role header, including a header claiming another human.
 if(!text||text.length>4096||text!==text.trim()||
    text!==text.normalize('NFC')||/[\p{Cc}\p{Cf}]/u.test(
     text.replace(/\n/g,''))||text.includes('\r'))
  return 'NAME_OR_BODY_DENIED';
 if(SIGNATURE.test(text))return 'DUPLICATE_OR_FORGED_PREFIX';
 if(text.startsWith(prefix))return 'DUPLICATE_OR_FORGED_PREFIX';
 return null;
}
/** Pure preview; never sign as a verified human without an authenticated S0
 * assertion obtained independently of AI, browser or caller-supplied claims. */
export function previewWa17HumanSignatureOffline(
 rawRequest:unknown,rawSession:unknown,rawCase:unknown,
):Wa17Result{
 try{
  const q=own(rawRequest,REQ),a=own(rawSession,SESSION),c=own(rawCase,CASE);
  if(!q||!a||!c||!request(q)||!session(a)||!context(c))
   return deny('INVALID_INPUT');
  if(q.concessionaria_id!==a.concessionaria_id||
     q.concessionaria_id!==c.concessionaria_id||
     q.waba_ref!==c.waba_ref||q.case_ref!==c.case_ref||
     a.actor_ref!==c.actor_ref)
   return deny('UNTRUSTED_SCOPE');
  if(!fresh(q.now_ms as number,a.observed_at_ms as number,
     q.max_age_ms as number)||
     !fresh(q.now_ms as number,c.observed_at_ms as number,
     q.max_age_ms as number))
   return deny('SESSION_OR_ASSIGNMENT_DENIED');
  if(c.assigned_human!==true||c.handoff_state!=='HUMAN')
   return deny('SESSION_OR_ASSIGNMENT_DENIED');
  if(c.free_text_window!=='CLAIMED_OPEN'||
     c.can_send_free_text!==true||c.opt_out!==false)
   return deny('WINDOW_OR_POLICY_DENIED');
  const role=a.role as Wa17Preview['role'];
  const pretty=role==='CONSULTOR'?'Consultor':
   role==='GESTOR'?'Gestor':'Diretor';
  const prefix=pretty+' '+a.display_name+':\n';
  const err=bodyOk(q.draft_text as string,prefix);
  if(err)return deny(err);
  const composed=prefix+q.draft_text;
  // Conservative LAB byte cap; this is not a Meta API size guarantee.
  if(Buffer.byteLength(composed,'utf8')>4096)
   return deny('NAME_OR_BODY_DENIED');
  const preview:Wa17Preview=Object.freeze({
   contract_version:'wa17-human-prefix-preview.lab.v0.1',
   selection_ref:q.selection_ref as string,
   concessionaria_id:q.concessionaria_id as string,
   waba_ref:q.waba_ref as string,case_ref:q.case_ref as string,
   intent_ref:q.intent_ref as string,actor_ref:a.actor_ref as string,
   role,display_name_snapshot:a.display_name as string,
   case_version:c.case_version as number,
   assignment_revision:c.assignment_revision as number,
   identity_revision:a.identity_revision as number,
   session_revision:a.session_revision as number,
   draft_sha256:sha(q.draft_text as string),
   composed_sha256:sha(composed),composed_text:composed,
   requires_s0_recheck:true,identity_verified:false,
   authorization_verified:false,send_authorized:false,
   production_authorized:false,graph_dispatch_authorized:false,
  });
  return yes(preview);
 }catch{return deny('INVALID_INPUT');}
}
function validPreview(raw:unknown):Record<string,unknown>|null{
 const x=own(raw,PREVIEW);
 if(!x||x.contract_version!=='wa17-human-prefix-preview.lab.v0.1'||
    !['selection_ref','case_ref','intent_ref','actor_ref'].every(k=>
      typeof x[k]==='string'&&REF.test(x[k]))||
    typeof x.concessionaria_id!=='string'||!UUID.test(x.concessionaria_id)||
    typeof x.waba_ref!=='string'||!DIGITS.test(x.waba_ref)||
    !['CONSULTOR','GESTOR','DIRETOR'].includes(x.role as string)||
    typeof x.display_name_snapshot!=='string'||
    !NAME.test(x.display_name_snapshot)||!NUMERIC(x.case_version)||
    !NUMERIC(x.assignment_revision)||!NUMERIC(x.identity_revision)||
    !NUMERIC(x.session_revision)||!hex(x.draft_sha256)||
    !hex(x.composed_sha256)||typeof x.composed_text!=='string'||
    x.composed_text.length>4096||
    sha(x.composed_text)!==x.composed_sha256||
    x.requires_s0_recheck!==true||x.identity_verified!==false||
    x.authorization_verified!==false||x.send_authorized!==false||
    x.production_authorized!==false||x.graph_dispatch_authorized!==false)
   return null;
 return x;
}
/** A retry/recheck uses ORIGINAL draft and a fresh S0 claim, never appends a
 * new prefix to the previous composed_text. No persist/commit/idempotency. */
export function recheckWa17HumanSignatureOffline(
 rawPrevious:unknown,freshRequest:unknown,
 freshSession:unknown,freshCase:unknown,
):Wa17Result{
 try{
  const previous=validPreview(rawPrevious);
  if(!previous)return deny('INVALID_PREVIEW');
  const current=previewWa17HumanSignatureOffline(
   freshRequest,freshSession,freshCase);
  if(current.decision==='DENIED')return current;
  if(!current.preview||PREVIEW.some(k=>
    previous[k]!==current.preview![k as keyof Wa17Preview]))
   return deny('REVISION_OR_AUTHOR_CHANGED');
  return yes(current.preview,true);
 }catch{return deny('INVALID_PREVIEW');}
}
