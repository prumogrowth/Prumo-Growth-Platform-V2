/**
 * OFF-03: candidate, deterministic F03 multi-case history and provenance boundary.
 * The S0 "attestations" here are synthetic inputs, never verified grants or signatures.
 * No model, bank, Meta, Supabase, disk, network, mutation or commercial effect.
 */
import {parseStrictJSON} from './typed-boundary.mjs';

export const F03_HISTORY_SCHEMA = 'prumo.openai.f03-history-private/0.2-candidate';
export const F03_PROVIDER_SCHEMA = 'prumo.openai.f03-history-provider/0.2-candidate';
export const F03_PROPOSAL_SCHEMA = 'prumo.openai.f03-history-proposal/0.2-candidate';
const VERSIONS = ['case','cycle','form','catalog','assignment','identity','policy'];
const ID = /^[A-Za-z0-9_.:-]{1,120}$/;
const CODE = /^[A-Za-z][A-Za-z0-9_.:-]{0,79}$/;
const MAX_RECORDS = 100;
const MAX_CASES = 30;
const MAX_FIELDS = 80;
const issued = new WeakSet();
const has = (o,k) => Object.prototype.hasOwnProperty.call(o,k);
const plain = x => x !== null && typeof x==='object' && !Array.isArray(x) &&
  (Object.getPrototypeOf(x)===Object.prototype || Object.getPrototypeOf(x)===null);
const exact = (x,required,optional=[]) => plain(x) && required.every(k=>has(x,k)) &&
  Reflect.ownKeys(x).every(k=>typeof k==='string'&&(required.includes(k)||optional.includes(k)));
const id = x => typeof x==='string' && ID.test(x);
const code = x => typeof x==='string' && CODE.test(x);
const time = x => typeof x==='string' && /(Z|[+-]\d\d:\d\d)$/.test(x) && Number.isFinite(Date.parse(x));
const integer = x => Number.isSafeInteger(x)&&x>=0;
const bounded = x => typeof x==='string' ? x.length<=1500&&x.trim().length>0&&!/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(x) :
  (typeof x==='number'&&Number.isFinite(x))||typeof x==='boolean';
const list = (x,max) => Array.isArray(x) && x.length<=max;
const uniq = xs => new Set(xs).size===xs.length;
const failure=(status,stage)=>Object.freeze({status,stage});
const grant = (s) => plain(s) && ['authenticated','authorized','tenantAllowed'].every(k => {
  const d=Object.getOwnPropertyDescriptor(s,k);return d && has(d,'value')&&d.value===true;
});

// Never invoke a caller-supplied getter, toJSON or prototype method while validating.
function safeData(x,depth=0,seen=new Set()) {
  if(depth>14)return false;
  if(x===null||typeof x==='string'||typeof x==='boolean')return true;
  if(typeof x==='number')return Number.isFinite(x);
  if(typeof x!=='object'||seen.has(x)||(!plain(x)&&!Array.isArray(x)))return false;
  if(Array.isArray(x)&&(x.length>MAX_RECORDS+20 || Object.keys(x).length!==x.length ||
     Object.keys(x).some(k=>!/^(0|[1-9]\d*)$/.test(k)||+k>=x.length)))return false;
  if(Reflect.ownKeys(x).some(k=>typeof k!=='string'||['__proto__','constructor','prototype'].includes(k)))return false;
  seen.add(x);
  for(const descriptor of Object.values(Object.getOwnPropertyDescriptors(x)))
    if(!has(descriptor,'value')||!safeData(descriptor.value,depth+1,seen))return false;
  seen.delete(x);
  return true;
}
function freeze(x) {if(x&&typeof x==='object') {for(const v of Object.values(x))freeze(v);Object.freeze(x);}return x;}
function versions(x){return exact(x,VERSIONS)&&VERSIONS.every(k=>integer(x[k]));}
function matchVersions(s){return VERSIONS.every(k=>s.expectedVersions[k]===s.currentVersions[k]);}
function scopeValid(s){return exact(s, ['authenticated','authorized','tenantAllowed','storeId','personId','caseId',
  'closureId','humanClosed','closureAuthenticated','identityAttested','historyCompletenessAttested',
  'expectedVersions','currentVersions'])&&
  [s.storeId,s.personId,s.caseId,s.closureId].every(id)&&
  s.humanClosed===true&&s.closureAuthenticated===true&&s.identityAttested===true&&
  s.historyCompletenessAttested===true&&versions(s.expectedVersions)&&versions(s.currentVersions);
}
function taskValid(req) {
  if(!exact(req,['schemaVersion','requestId','providerTag','scope','privacy','cutoff','cases','records','catalog'])||
     req.schemaVersion!==F03_HISTORY_SCHEMA||!id(req.requestId)||!id(req.providerTag)||
     !exact(req.privacy,['modelContentAuthorized','dataMinimized'])||
     req.privacy.modelContentAuthorized!==true||req.privacy.dataMinimized!==true||
     !scopeValid(req.scope)||
     !exact(req.cutoff,['sequence','closedAt','eventId'])||!integer(req.cutoff.sequence)||
     !time(req.cutoff.closedAt)||!id(req.cutoff.eventId)||
     !list(req.cases,MAX_CASES)||!list(req.records,MAX_RECORDS)||!list(req.catalog,MAX_FIELDS)||
     !uniq(req.cases.map(c=>c?.id))||!uniq(req.records.map(r=>r?.id))||
     !uniq(req.catalog.map(f=>f?.code)))return false;
  const s=req.scope, cases=new Set();
  for(const c of req.cases){
    if(!exact(c,['id','storeId','personId','s0IdentityBound'])||!id(c.id)||
       c.storeId!==s.storeId||c.personId!==s.personId||c.s0IdentityBound!==true)return false;
    cases.add(c.id);
  }
  if(!cases.has(s.caseId))return false;
  const catalog=new Map();
  for(const f of req.catalog){
    if(!exact(f,['code','type','essential'])||!code(f.code)||
       !['string','number','boolean'].includes(f.type)||typeof f.essential!=='boolean')return false;
    catalog.set(f.code,f);
  }
  const sequence=new Set(),claims=new Map();
  for(const r of req.records){
    if(!exact(r,['id','caseId','storeId','personId','sequence','at','authorClass','kind',
                'available','contentAuthorized','content','claims'])||
       !id(r.id)||!cases.has(r.caseId)||r.storeId!==s.storeId||r.personId!==s.personId||
       !integer(r.sequence)||!time(r.at)||!['customer','human','ai'].includes(r.authorClass)||
       !['text','media'].includes(r.kind)||typeof r.available!=='boolean'||
       typeof r.contentAuthorized!=='boolean'||!list(r.claims,MAX_FIELDS))return false;
    // A private snapshot may carry late events; those must never enter the extracted cutoff.
    // Within the cutoff, a timestamp after the confirmed human-close time is inconsistent.
    if(r.sequence<=req.cutoff.sequence&&Date.parse(r.at)>Date.parse(req.cutoff.closedAt))return false;
    if(sequence.has(r.sequence))return false;
    sequence.add(r.sequence);
    if(!r.available && r.claims.length!==0)return false;
    if(r.available) {
      if(!r.contentAuthorized||typeof r.content!=='string'||!bounded(r.content))return false;
    } else if(r.contentAuthorized!==false||r.content!=='')return false;
    if(!uniq(r.claims.map(c=>c?.id)))return false;
    for(const c of r.claims){
      if(!exact(c,['id','code','value','explicit'],['corrects','s0CorrectionAttested'])||
         !id(c.id)||!code(c.code)||!bounded(c.value)||typeof c.explicit!=='boolean'||
         (!catalog.has(c.code)&&c.code!=='customer_withdrawal')||
         (c.code==='customer_withdrawal'&&typeof c.value!=='boolean')||
         (catalog.has(c.code)&&typeof c.value!==catalog.get(c.code).type)||
         (has(c,'corrects')!==has(c,'s0CorrectionAttested'))||
         (has(c,'corrects')&&(!id(c.corrects)||c.s0CorrectionAttested!==true))||
         claims.has(c.id))return false;
      claims.set(c.id,{...c,record:r});
    }
  }
  // A correction is only a synthetically S0-attested link to an earlier eligible
  // claim in the same field; no text-model guess is ever promoted to correction.
  const corrected=new Set();
  for(const c of claims.values()){
    if(!has(c,'corrects'))continue;
    const previous=claims.get(c.corrects);
    if(!previous||previous.code!==c.code||previous.record.sequence>=c.record.sequence||
       previous.record.sequence>req.cutoff.sequence||c.record.sequence>req.cutoff.sequence||
       !previous.record.available||!c.record.available||!previous.explicit||!c.explicit||
       corrected.has(c.corrects))return false;
    corrected.add(c.corrects);
  }
  return true;
}
function frozenView(request){return freeze(structuredClone(request));}

/** A private, immutable snapshot: nothing in this object is a provider payload. */
export function prepareF03History(request){
  try{
    const sd=plain(request)?Object.getOwnPropertyDescriptor(request,'scope'):null;
    if(!sd||!has(sd,'value')||!grant(sd.value)) return failure('DENIED','S0');
    if(!safeData(request)||!taskValid(request))return failure('INVALID_INPUT','MANIFEST');
    if(!matchVersions(request.scope))return failure('STALE','S0');
    const snapshot=frozenView(request);
    const eligible=snapshot.records.filter(r=>r.sequence<=snapshot.cutoff.sequence).sort((a,b)=>
      a.sequence-b.sequence||a.id.localeCompare(b.id));
    const aliases=eligible.map((r,i)=>({alias:'src_'+String(i+1).padStart(3,'0'),recordId:r.id}));
    const context=Object.freeze({snapshot,eligible:freeze([...eligible]),aliases:freeze(aliases)});
    issued.add(context);
    return Object.freeze({status:'READY',privateContext:context});
  }catch{return failure('INVALID_INPUT','MANIFEST');}
}

/** No tenant/case/person/request/closure IDs, proofs, sessions, HMAC or S0 versions. */
export function projectF03History(prepared){
  try{
    if(prepared?.status!=='READY'||!issued.has(prepared.privateContext))return failure('INVALID_INPUT','PROJECTION');
    const ctx=prepared.privateContext, s=ctx.snapshot;
    const aliases=new Map(ctx.aliases.map(x=>[x.recordId,x.alias]));
    return {schemaVersion:F03_PROVIDER_SCHEMA,operation:'F03',providerTag:s.providerTag,catalog:s.catalog.map(x=>({...x})),
      evidence:ctx.eligible.filter(r=>r.available).map(r=>({alias:aliases.get(r.id),
        authorClass:r.authorClass,kind:r.kind,content:r.content})),
      unavailableEvidenceCount:ctx.eligible.filter(r=>!r.available).length};
  }catch{return failure('INVALID_INPUT','PROJECTION');}
}
function parsedProposal(raw){
  if(typeof raw==='string'){
    const p=parseStrictJSON(raw);
    return p.status==='PARSED'?p.value:null;
  }
  return safeData(raw)?raw:null;
}
function recheck(original,current){
  if(!grant(current))return failure('DENIED','S0_RECHECK');
  if(!safeData(current))return failure('INVALID_INPUT','S0_RECHECK');
  if(!scopeValid(current)||[current.storeId,current.personId,current.caseId,current.closureId]
      .some((x,i)=>x!==[original.storeId,original.personId,original.caseId,original.closureId][i]))
    return failure('DENIED','S0_RECHECK');
  if(!VERSIONS.every(k=>current.expectedVersions[k]===original.expectedVersions[k])||
     !matchVersions(current))return failure('STALE','S0_RECHECK');
  return null;
}
function sameClaim(a,b){return typeof a===typeof b && a===b;}
function evidenceIndex(ctx){
  const cutoff=ctx.snapshot.cutoff.sequence;
  const eligible=ctx.eligible.filter(r=>r.available);
  const recordByAlias=new Map(ctx.aliases.map(x=>[x.alias,eligible.find(r=>r.id===x.recordId)]));
  const claims=new Map();const corrected=new Set();
  for(const r of eligible){
    for(const c of r.claims){claims.set(c.id,{...c,record:r});if(has(c,'corrects'))corrected.add(c.corrects);}
  }
  const terminal=new Map(), conflictCodes=new Set();
  for(const c of claims.values()){
    if(!c.explicit||corrected.has(c.id))continue;
    if(!terminal.has(c.code))terminal.set(c.code,[]);
    terminal.get(c.code).push(c);
  }
  for(const [code,group] of terminal){
    if(group.some(x=>!sameClaim(x.value,group[0].value)))conflictCodes.add(code);
  }
  return {recordByAlias,terminal,conflictCodes,cutoff};
}
/**
 * Provider proposal is untrusted. Positive result remains a private candidate for
 * an independent S0 recheck, not a semantic proof or authorization to write.
 */
export function reviewF03Extraction(prepared,raw,{currentScope,prior}={}){
  try{
    if(prepared?.status!=='READY'||!issued.has(prepared.privateContext))return failure('DENIED','CONTEXT');
    const ctx=prepared.privateContext,s=ctx.snapshot;
    const changed=recheck(s.scope,currentScope??s.scope);
    if(changed)return changed;
    if(prior!==undefined&&prior!==null){
      if(!exact(prior,['requestId','closureId','snapshotSequence','s0Verified'])||
         !id(prior.requestId)||!id(prior.closureId)||!integer(prior.snapshotSequence)||
         prior.s0Verified!==true)return failure('REVIEW_REQUIRED','REPLAY');
      return prior.requestId===s.requestId&&prior.closureId===s.scope.closureId&&
        prior.snapshotSequence===s.cutoff.sequence ?
        failure('ALREADY_HANDLED','REPLAY'):failure('REVIEW_REQUIRED','REPLAY');
    }
    const p=parsedProposal(raw);
    if(!exact(p,['schemaVersion','providerTag','fields','missingFields','conflicts','commercialAdvisory','followupAdvisory'])||
       p.schemaVersion!==F03_PROPOSAL_SCHEMA||p.providerTag!==s.providerTag||!list(p.fields,MAX_FIELDS)||
       !list(p.missingFields,MAX_FIELDS)||!list(p.conflicts,MAX_FIELDS)||
       !['none','consider'].includes(p.followupAdvisory)||
       !uniq(p.fields.map(f=>f?.code))||!uniq(p.missingFields)||!uniq(p.conflicts.map(c=>c?.code)))
      return failure('SCHEMA_INVALID','PROPOSAL');
    const catalog=new Map(s.catalog.map(f=>[f.code,f]));
    const {recordByAlias,terminal,conflictCodes}=evidenceIndex(ctx);
    const selected=[],present=new Set();
    for(const f of p.fields){
      if(!exact(f,['code','value','sourceAliases'])||!catalog.has(f.code)||
         !bounded(f.value)||typeof f.value!==catalog.get(f.code).type||
         !list(f.sourceAliases,MAX_RECORDS)||!f.sourceAliases.length||
         !uniq(f.sourceAliases)||f.sourceAliases.some(a=>!id(a)||!recordByAlias.get(a)))
        return failure('SOURCE_INVALID','FIELD');
      // Every cited record must substantiate this exact field/value, not just one
      // record in a list padded with unrelated sources.
      if(!f.sourceAliases.every(a=>recordByAlias.get(a).claims.some(c=>c.code===f.code&&
          c.explicit&&sameClaim(c.value,f.value))))return failure('SOURCE_INVALID','CLAIM');
      // A citation must independently point at a *terminal*, non-corrected claim.
      // A valid later correction cannot launder an obsolete citation merely by
      // appearing in the same sourceAliases[] array.
      if(!f.sourceAliases.every(a=>(terminal.get(f.code)??[]).some(c=>
          c.record.id===recordByAlias.get(a).id && sameClaim(c.value,f.value))))
        return failure('SOURCE_INVALID','OBSOLETE_CITATION');
      selected.push({code:f.code,value:f.value,recordIds:f.sourceAliases.map(a=>recordByAlias.get(a).id)});
      present.add(f.code);
    }
    for(const codeName of p.missingFields){if(!catalog.has(codeName)||present.has(codeName))return failure('SCHEMA_INVALID','MISSING');}
    const declaredConflicts=[];
    for(const c of p.conflicts){
      if(!exact(c,['code','sourceAliases'])||!catalog.has(c.code)||
         !list(c.sourceAliases,MAX_RECORDS)||c.sourceAliases.length<2||!uniq(c.sourceAliases)||
         c.sourceAliases.some(a=>!id(a)||!recordByAlias.get(a)))return failure('SOURCE_INVALID','CONFLICT');
      declaredConflicts.push({code:c.code,recordIds:c.sourceAliases.map(a=>recordByAlias.get(a).id)});
    }
    let advisory=null;
    if(p.commercialAdvisory!==null){
      const x=p.commercialAdvisory;
      if(!exact(x,['kind','sourceAliases'])||x.kind!=='perdido'||
         !list(x.sourceAliases,MAX_RECORDS)||!x.sourceAliases.length||!uniq(x.sourceAliases)||
         x.sourceAliases.some(a=>!id(a)||!recordByAlias.get(a)))
        return failure('SOURCE_INVALID','ADVISORY');
      // An explicit withdrawal may be attributed only to a customer-originated
      // terminal claim. A corrected withdrawal or contradictory current claims
      // never support proposing a technical/commercial loss.
      const terminalWithdrawals=terminal.get('customer_withdrawal')??[];
      if(!terminalWithdrawals.length||terminalWithdrawals.some(c=>c.value!==true)||
         x.sourceAliases.some(a=>!terminalWithdrawals.some(c=>c.record.id===recordByAlias.get(a).id&&
           c.record.authorClass==='customer'&&c.value===true)))
        return failure('SOURCE_INVALID','WITHDRAWAL_EVIDENCE');
      advisory={kind:'perdido',recordIds:x.sourceAliases.map(a=>recordByAlias.get(a).id)};
    }
    const missingEssential=s.catalog.filter(f=>f.essential&&!present.has(f.code)).map(f=>f.code);
    if(missingEssential.some(x=>!p.missingFields.includes(x)))return failure('SCHEMA_INVALID','MISSING');
    // Inconsistent declared corrections or conflict omissions never silently choose latest.
    const conflicts=[...conflictCodes].filter(k=>catalog.has(k));
    const unprovenSelected=selected.some(f=>conflictCodes.has(f.code)||
      !terminal.get(f.code)?.some(c=>sameClaim(c.value,f.value)&&f.recordIds.includes(c.record.id)));
    if(unprovenSelected)return failure('REVIEW_REQUIRED','HISTORY_CONFLICT');
    // Model-authored history is interpretive, never independent confirmation of
    // a customer's fact. Require at least one cited, non-AI terminal claim.
    const aiOnlySelected=selected.some(f=>!(terminal.get(f.code)??[]).some(c=>
      sameClaim(c.value,f.value)&&f.recordIds.includes(c.record.id)&&c.record.authorClass!=='ai'));
    if(aiOnlySelected)return failure('REVIEW_REQUIRED','AUTHORSHIP');
    const privateCandidate=freeze({requestId:s.requestId,storeId:s.scope.storeId,personId:s.scope.personId,
      caseId:s.scope.caseId,closureId:s.scope.closureId,cutoffSequence:s.cutoff.sequence,
      cutoffEventId:s.cutoff.eventId,expectedVersions:{...s.scope.expectedVersions},
      fields:selected,missingFields:[...p.missingFields],conflicts:declaredConflicts,
      commercialAdvisory:advisory,followupAdvisory:p.followupAdvisory,
      assurance:{s0OperationallyAuthorized:false,semanticVerified:false,historyCompletenessProved:false,
        correctionProved:false,applied:false,e02Homologated:false}});
    if(conflicts.length||missingEssential.length||declaredConflicts.length||advisory)
      return {status:'REVIEW_REQUIRED',stage:'S0_HUMAN_REVIEW',
        reasons:[...(conflicts.length?['HISTORICAL_CONFLICT']:[]),
          ...(missingEssential.length?['ESSENTIAL_MISSING']:[]),
          ...(declaredConflicts.length?['DECLARED_CONFLICT']:[]),
          ...(advisory?['COMMERCIAL_ADVISORY']:[])],privateCandidate};
    return {status:'PROPOSED',stage:'S0_RECHECK_ONLY',privateCandidate};
  }catch{return failure('SCHEMA_INVALID','PROPOSAL');}
}
/** Diagnostic deliberately cannot disclose identity, history, financial values or receipt. */
export function auditF03History(outcome){
  const codes=new Set(['READY','PROPOSED','REVIEW_REQUIRED','DENIED','STALE','INVALID_INPUT',
    'SCHEMA_INVALID','SOURCE_INVALID','ALREADY_HANDLED']);
  return Object.freeze({operation:'F03',schemaVersion:F03_HISTORY_SCHEMA,
    status:codes.has(outcome?.status)?outcome.status:'INVALID_INPUT'});
}
