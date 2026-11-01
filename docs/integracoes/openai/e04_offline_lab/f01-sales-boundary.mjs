/**
 * OAI-OFF-05 — F01 synthetic sales boundary. Candidate, local-only.
 * No OpenAI SDK, network, I/O, SQL, Meta, STT/TTS, business mutation or clock reads.
 * Every S0 assertion supplied here is a TEST FIXTURE, never authenticated authority.
 */
import {createHash} from 'node:crypto';

export const F01_PRIVATE = 'prumo.openai.f01-private/0.1-candidate';
export const F01_PROVIDER = 'prumo.openai.f01-provider/0.1-candidate';
export const F01_RESPONSE = 'prumo.openai.f01-response/0.1-candidate';
const VERSIONS = ['case','cycle','assignment','catalog','policy','knowledge','route','consent'];
const ID = /^[A-Za-z0-9_.:-]{1,120}$/;
const CODE = /^[A-Za-z][A-Za-z0-9_.:-]{0,79}$/;
const ADVISORY = ['NONE','CUSTOMER_REQUEST','UNCERTAINTY','ESCALATION'];
const issued = new WeakSet();
const has = (o,k) => Object.prototype.hasOwnProperty.call(o,k);
const plain = x => x!==null && typeof x==='object' && !Array.isArray(x) &&
  (Object.getPrototypeOf(x)===Object.prototype || Object.getPrototypeOf(x)===null);
const exact = (x,r,o=[]) => plain(x) && r.every(k=>has(x,k)) &&
  Reflect.ownKeys(x).every(k=>typeof k==='string' && (r.includes(k)||o.includes(k)));
const identifier = x => typeof x==='string' && ID.test(x);
const code = x => typeof x==='string' && CODE.test(x);
const natural = x => Number.isSafeInteger(x) && x>=0;
const bounded = (x,n=2500) => typeof x==='string' && x.length>0 && x.length<=n &&
  x.trim().length>0 && !/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(x);
const list = (x,max=48) => Array.isArray(x) && x.length<=max &&
  Object.keys(x).length===x.length && Reflect.ownKeys(x).every(k=>k==='length'||/^(0|[1-9]\d*)$/.test(k));
const unique = a => new Set(a).size===a.length;
const fail = (status,stage) => Object.freeze({status,stage});
function safeData(x,depth=0,seen=new Set()) {
  if(depth>12)return false;
  if(x===null||typeof x==='string'||typeof x==='boolean')return true;
  if(typeof x==='number')return Number.isFinite(x);
  if(typeof x!=='object'||seen.has(x)||(!plain(x)&&!Array.isArray(x)))return false;
  if(Array.isArray(x)&&!list(x,80))return false;
  if(Reflect.ownKeys(x).some(k=>typeof k!=='string'||['__proto__','constructor','prototype'].includes(k)))return false;
  seen.add(x);
  for(const d of Object.values(Object.getOwnPropertyDescriptors(x)))
    if(!has(d,'value')||!safeData(d.value,depth+1,seen))return false;
  seen.delete(x);return true;
}
const clone = x => structuredClone(x);
function freeze(x) {if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;}
const versions = x => exact(x,VERSIONS)&&VERSIONS.every(k=>natural(x[k]));
const grant = x => plain(x)&&['authenticated','authorized','tenantAllowed'].every(k=>{
  const d=Object.getOwnPropertyDescriptor(x,k);return d && has(d,'value')&&d.value===true;
});
function scope(s) {
  return exact(s,['authenticated','authorized','tenantAllowed','storeId','caseId','personId',
    'owner','handoffDefinitive','humanized','postRemittance','postSale','channelEligible',
    'optOut','expectedVersions','currentVersions']) &&
    [s.storeId,s.caseId,s.personId].every(identifier)&&s.owner==='ai'&&
    s.handoffDefinitive===false&&s.humanized===false&&s.postRemittance===false&&
    s.postSale===false&&s.channelEligible===true&&s.optOut===false&&
    versions(s.expectedVersions)&&versions(s.currentVersions);
}
const sameVersions=(a,b)=>VERSIONS.every(k=>a[k]===b[k]);
function inputValid(e) {
  if(!exact(e,['schemaVersion','requestId','providerTag','nowMs','deadlineMs','scope','privacy',
    'instructions','customerInput','recentContext','sources'])||e.schemaVersion!==F01_PRIVATE||
    ![e.requestId,e.providerTag].every(identifier)||!natural(e.nowMs)||!natural(e.deadlineMs)||
    e.deadlineMs<=e.nowMs||!scope(e.scope)||
    !exact(e.privacy,['contentAuthorized','dataMinimized'])||
    e.privacy.contentAuthorized!==true||e.privacy.dataMinimized!==true||
    !exact(e.instructions,['text','behavior','version'])||!bounded(e.instructions.text,1600)||
    !bounded(e.instructions.behavior,1600)||!identifier(e.instructions.version)||
    !exact(e.customerInput,['kind','text','transcriptState'])||
    !['text','stt_transcript'].includes(e.customerInput.kind)||!bounded(e.customerInput.text,3000)||
    !['NOT_APPLICABLE','CONFIRMED','UNCERTAIN'].includes(e.customerInput.transcriptState)||
    (e.customerInput.kind==='text'&&e.customerInput.transcriptState!=='NOT_APPLICABLE')||
    (e.customerInput.kind==='stt_transcript'&&e.customerInput.transcriptState==='NOT_APPLICABLE')||
    !list(e.recentContext,20)||!e.recentContext.every(m=>exact(m,['role','text'])&&
      ['customer','ai'].includes(m.role)&&bounded(m.text,3000))||
    !list(e.sources,48)||!unique(e.sources.map(s=>s?.id))||
    !e.sources.every(s=>exact(s,['id','storeId','mode','approved','active','modelAllowed',
      'content','allowedClaimCodes'],['validUntilMs'])&&identifier(s.id)&&s.storeId===e.scope.storeId&&
      ['current','historical'].includes(s.mode)&&s.approved===true&&s.modelAllowed===true&&
      typeof s.active==='boolean'&&bounded(s.content,3000)&&
      list(s.allowedClaimCodes,30)&&unique(s.allowedClaimCodes)&&
      s.allowedClaimCodes.every(code)&&
      (!has(s,'validUntilMs')||natural(s.validUntilMs))))return false;
  return true;
}
/** Never call client getter before checking the S0 fixture grant. */
export function prepareF01Turn(envelope) {
  try{
    if(!plain(envelope)||!grant(Object.getOwnPropertyDescriptor(envelope,'scope')?.value))
      return fail('DENIED','S0_SCOPE');
    if(!safeData(envelope))return fail('INVALID_INPUT','PRIVATE');
    const s=Object.getOwnPropertyDescriptor(envelope,'scope')?.value;
    if(!plain(s)||s.owner!=='ai'||s.handoffDefinitive!==false||s.humanized!==false||
       s.postRemittance!==false||s.postSale!==false||s.channelEligible!==true||s.optOut!==false)
      return fail('DENIED','S0_SCOPE');
    if(!inputValid(envelope))return fail('INVALID_INPUT','PRIVATE');
    if(!sameVersions(envelope.scope.expectedVersions,envelope.scope.currentVersions))
      return fail('STALE','S0_VERSION');
    if(envelope.customerInput.transcriptState==='UNCERTAIN')
      return fail('REVIEW_REQUIRED','TRANSCRIPTION');
    if(envelope.sources.some(s=>s.mode==='current' &&
       (!s.active||(has(s,'validUntilMs')&&s.validUntilMs<=envelope.nowMs))))
      return fail('SOURCE_INVALID','KNOWLEDGE');
    const saved=freeze(clone(envelope));
    const aliases=freeze(saved.sources.map((s,i)=>({alias:'src_'+String(i+1).padStart(3,'0'),id:s.id})));
    const h=Object.freeze({status:'READY_CANDIDATE',private:saved,aliases});
    issued.add(h);return h;
  }catch{return fail('INVALID_INPUT','PRIVATE');}
}
/** Projection: only global F01 settings, approved/minimized conversation, aliased sources. */
export function f01ProviderView(handle) {
  try{
    if(!issued.has(handle))return fail('INVALID_INPUT','HANDLE');
    const e=handle.private;
    return freeze({schemaVersion:F01_PROVIDER,providerTag:e.providerTag,
      instructions:{text:e.instructions.text,behavior:e.instructions.behavior},
      task:{kind:e.customerInput.kind,customerText:e.customerInput.text,
        recentContext:e.recentContext.map(m=>({...m})),
        sources:e.sources.map((s,i)=>({alias:handle.aliases[i].alias,mode:s.mode,
          content:s.content,allowedClaimCodes:[...s.allowedClaimCodes]}))}});
  }catch{return fail('INVALID_INPUT','PROJECTION');}
}
// JSON.parse silently accepts duplicate object keys. Detect duplicate decoded keys
// in each object while respecting quoted strings and array boundaries.
function parseReply(raw){
  if(typeof raw!=='string'||Buffer.byteLength(raw,'utf8')>16384)return null;
  try{
    const v=JSON.parse(raw), stack=[];
    for(const m of raw.matchAll(/"(?:\\.|[^"\\])*"|[{}\[\]]/g)){
      const t=m[0];
      if(t==='{'||t==='['){stack.push(t==='{'?new Set():null);if(stack.length>12)return null;}
      else if(t==='}'||t===']')stack.pop();
      else if(/^\s*:/.test(raw.slice(m.index+t.length))){
        const s=stack.at(-1),k=JSON.parse(t);if(!(s instanceof Set)||s.has(k))return null;s.add(k);
      }
    }
    return safeData(v)?v:null;
  }catch{return null;}
}
function liveRecheck(current,origin){
  if(!grant(current))return fail('DENIED','S0_RECHECK');
  if(!safeData(current)||!scope(current)||
     current.storeId!==origin.storeId||current.caseId!==origin.caseId||
     current.personId!==origin.personId)return fail('DENIED','S0_RECHECK');
  if(!sameVersions(current.expectedVersions,origin.expectedVersions)||
     !sameVersions(current.currentVersions,current.expectedVersions))return fail('STALE','S0_RECHECK');
  return null;
}
/** A model supplies a DRAFT only. No publication or human handoff execution. */
export function evaluateF01Model(handle,raw,options={}){
  try{
    if(!issued.has(handle))return fail('INVALID_INPUT','HANDLE');
    if(!safeData(options)||!exact(options,['nowMs','currentScope'],['prior']))
      return fail('INVALID_INPUT','OPTIONS');
    const {nowMs,currentScope,prior=null}=options;
    const e=handle.private;
    const gate=liveRecheck(currentScope,e.scope);if(gate)return gate;
    if(!natural(nowMs))return fail('INVALID_INPUT','CLOCK');
    // An S0-fixture clock may never move backwards relative to the issued turn.
    // Fail closed rather than treating a backdated result as a valid draft.
    if(nowMs<e.nowMs)return fail('REVIEW_REQUIRED','CLOCK');
    if(nowMs>e.deadlineMs)return fail('LATE_RESPONSE','DEADLINE');
    if(prior!==null){
      if(!exact(prior,['requestId','providerTag','replySha256','reviewOnly'])||
         prior.requestId!==e.requestId||prior.providerTag!==e.providerTag||
         !/^[a-f0-9]{64}$/.test(prior.replySha256)||prior.reviewOnly!==true)
        return fail('REPLAY_CONFLICT','PRIOR');
      if(typeof raw!=='string')return fail('SCHEMA_INVALID','RESULT');
      const digest=createHash('sha256').update(raw,'utf8').digest('hex');
      // Caller-supplied prior is a fixture, never a durable/verified idempotency record.
      return fail(prior.replySha256===digest?'ALREADY_HANDLED_REVIEW_ONLY':'REPLAY_CONFLICT','REPLAY');
    }
    const x=parseReply(raw);
    if(!exact(x,['schemaVersion','providerTag','state','output'])||x.schemaVersion!==F01_RESPONSE||
       x.providerTag!==e.providerTag||!['completed','refused'].includes(x.state))
      return fail('SCHEMA_INVALID','RESULT');
    if(x.state==='refused')return x.output===null?fail('MODEL_REFUSAL','PROVIDER'):fail('SCHEMA_INVALID','RESULT');
    const o=x.output;
    if(!exact(o,['replyText','commercial','sourceAliases','claims','modalityHint','handoffAdvisory','uncertaintyCodes'])||
      !bounded(o.replyText,3000)||typeof o.commercial!=='boolean'||
      !list(o.sourceAliases,48)||!unique(o.sourceAliases)||!o.sourceAliases.every(identifier)||
      !list(o.claims,40)||!unique(o.claims.map(c=>c?.claimCode+'@'+c?.sourceAlias))||
      !o.claims.every(c=>exact(c,['claimCode','sourceAlias'])&&code(c.claimCode)&&identifier(c.sourceAlias))||
      !['text','audio'].includes(o.modalityHint)||
      !exact(o.handoffAdvisory,['needed','reason'])||typeof o.handoffAdvisory.needed!=='boolean'||
      !ADVISORY.includes(o.handoffAdvisory.reason)||
      (o.handoffAdvisory.needed===(o.handoffAdvisory.reason==='NONE'))||
      !list(o.uncertaintyCodes,16)||!unique(o.uncertaintyCodes)||!o.uncertaintyCodes.every(code))
      return fail('SCHEMA_INVALID','OUTPUT');
    const table=new Map(handle.aliases.map((a,i)=>[a.alias,e.sources[i]]));
    if(!o.sourceAliases.every(a=>table.has(a))||
       !o.claims.every(c=>table.has(c.sourceAlias)&&o.sourceAliases.includes(c.sourceAlias)&&
          table.get(c.sourceAlias).allowedClaimCodes.includes(c.claimCode)))
      return fail('SOURCE_INVALID','EVIDENCE');
    if(o.commercial && (o.sourceAliases.length===0||o.claims.length===0||
       o.sourceAliases.some(a=>table.get(a).mode!=='current'||!table.get(a).active||
         (has(table.get(a),'validUntilMs')&&table.get(a).validUntilMs<=nowMs))))
      return fail('SOURCE_INVALID','COMMERCIAL');
    if(o.modalityHint==='audio' && e.customerInput.kind==='text')
      return fail('REVIEW_REQUIRED','MODALITY');
    // We cannot prove that free text semantically matches cited facts: ALWAYS review at S0.
    return freeze({status:'S0_RECHECK_ONLY',stage:'F01_DRAFT',requestId:e.requestId,
      expectedVersions:clone(e.scope.expectedVersions),
      proposal:{text:o.replyText,commercial:o.commercial,sourceIds:o.sourceAliases.map(a=>table.get(a).id),
        claims:o.claims.map(c=>({code:c.claimCode,sourceId:table.get(c.sourceAlias).id})),
        modalityHint:o.modalityHint,handoffAdvisory:clone(o.handoffAdvisory),
        uncertaintyCodes:[...o.uncertaintyCodes]},
      publishAuthorized:false,handoffAuthorized:false,customerMessageSent:false,
      semanticVerified:false,physicalS0Recheck:false,
      replayCandidate:{requestId:e.requestId,providerTag:e.providerTag,
        replySha256:createHash('sha256').update(raw,'utf8').digest('hex'),reviewOnly:true}});
  }catch{return fail('SCHEMA_INVALID','RESULT');}
}

/** Offline handoff event journal; S0 must supply and authenticate real events. */
export function reviewF01Handoff(args={}){
  try{
    if(!safeData(args)||!exact(args,['scope','events'],['prior']))return fail('INVALID_INPUT','JOURNAL');
    const {scope:sc,events,prior=null}=args;
    if(!grant(sc))return fail('DENIED','S0_SCOPE');
    if(!safeData({scope:sc,events,prior})||!exact(sc,['authenticated','authorized','tenantAllowed','storeId','caseId','personId'])||
       ![sc.storeId,sc.caseId,sc.personId].every(identifier)||!list(events,80)||
       (prior!==null&&!exact(prior,['lastSequence','handoffDefinitive','verified'])))
      return fail('INVALID_INPUT','JOURNAL');
    const ids=new Map(),seqs=new Set();
    for(const ev of events){
      if(!exact(ev,['eventId','sequence','storeId','caseId','personId','kind','verified'])||
         !identifier(ev.eventId)||!natural(ev.sequence)||
         ev.storeId!==sc.storeId||ev.caseId!==sc.caseId||ev.personId!==sc.personId||
         !['AI_TURN','HANDOFF_TO_HUMAN','HUMAN_MESSAGE','HUMAN_CLOSE','NEW_INBOUND'].includes(ev.kind)||
         ev.verified!==true)return fail('INVALID_INPUT','EVENT');
      const fp=JSON.stringify(ev);
      if(ids.has(ev.eventId)){
        if(ids.get(ev.eventId)!==fp)return fail('REVIEW_REQUIRED','REPLAY');
        continue;
      }
      if(seqs.has(ev.sequence))return fail('REVIEW_REQUIRED','ORDER');
      ids.set(ev.eventId,fp);seqs.add(ev.sequence);
    }
    if(prior!==null && (!natural(prior.lastSequence)||typeof prior.handoffDefinitive!=='boolean'||prior.verified!==true))
      return fail('REVIEW_REQUIRED','PRIOR');
    let handoff=prior?.handoffDefinitive===true, lastSeq=prior?.lastSequence??-1;
    for(const ev of [...events].sort((a,b)=>a.sequence-b.sequence)){
      if(prior!==null&&ev.sequence<=prior.lastSequence)return fail('REVIEW_REQUIRED','ORDER');
      lastSeq=ev.sequence;
      if(ev.kind==='HANDOFF_TO_HUMAN')handoff=true;
      if(handoff && ev.kind==='AI_TURN')return fail('DENIED','POST_HANDOFF_AI');
    }
    return freeze({status:handoff?'HUMAN_ONLY_REVIEW':'AI_ELIGIBILITY_S0_RECHECK',
      stage:'HANDOFF',lastSequence:lastSeq,handoffDefinitive:handoff,
      aiResumeAuthorized:false,sendAuthorized:false});
  }catch{return fail('INVALID_INPUT','JOURNAL');}
}

/** Fixed vocabulary: no customer content, IDs, prompts, or error traces. */
export function f01SafeAudit(result){
  const allow=new Set(['DENIED','INVALID_INPUT','STALE','SOURCE_INVALID','SCHEMA_INVALID',
    'MODEL_REFUSAL','REVIEW_REQUIRED','LATE_RESPONSE','REPLAY_CONFLICT',
    'ALREADY_HANDLED_REVIEW_ONLY','S0_RECHECK_ONLY','HUMAN_ONLY_REVIEW','AI_ELIGIBILITY_S0_RECHECK']);
  const stages=new Set(['S0_SCOPE','PRIVATE','S0_VERSION','TRANSCRIPTION','KNOWLEDGE',
    'HANDLE','PROJECTION','OPTIONS','S0_RECHECK','CLOCK','DEADLINE','PRIOR','REPLAY','RESULT','PROVIDER',
    'OUTPUT','EVIDENCE','COMMERCIAL','MODALITY','F01_DRAFT','JOURNAL','EVENT','ORDER',
    'POST_HANDOFF_AI','HANDOFF']);
  const status=plain(result)?Object.getOwnPropertyDescriptor(result,'status')?.value:undefined;
  const stage=plain(result)?Object.getOwnPropertyDescriptor(result,'stage')?.value:undefined;
  return Object.freeze({operation:'F01',status:allow.has(status)?status:'SCHEMA_INVALID',
    stage:stages.has(stage)?stage:'UNKNOWN',schemaVersion:F01_PRIVATE});
}
