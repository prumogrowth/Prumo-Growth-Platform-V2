/**
 * OFF-02 — candidate, pure offline S0-fixture -> minimal provider view -> S0-only proposal.
 * No network, persistence, SDK, model execution, authentication or authority.
 */
import {createHash} from 'node:crypto';
import {versionGate, validateF01, validateF02, prepareF03History, validateF03Proposal} from './core.mjs';

export const PRIVATE_SCHEMA = 'prumo.openai.private-exchange/0.1-candidate';
export const PROVIDER_SCHEMA = 'prumo.openai.provider-input/0.1-candidate';
export const RESPONSE_SCHEMA = 'prumo.openai.provider-result/0.1-candidate';
const KINDS = ['F01', 'F02', 'F03'];
const issued = new WeakSet();
const VERSION_KEYS = ['case', 'cycle', 'form', 'catalog', 'assignment', 'policy'];
const RECORD_LIMIT = 48;
const TEXT_LIMIT = 3000;
const ID = /^[A-Za-z0-9_.:-]{1,120}$/;
const CODE = /^[A-Za-z][A-Za-z0-9_.:-]{0,79}$/;
const bad = (status, stage) => Object.freeze({status, stage});
const own = (x,k) => Object.prototype.hasOwnProperty.call(x,k);
const plain = x => x !== null && typeof x === 'object' && !Array.isArray(x) &&
  (Object.getPrototypeOf(x) === Object.prototype || Object.getPrototypeOf(x) === null);
const keys = (x, required, optional = []) => plain(x) &&
  required.every(k => own(x,k)) && Reflect.ownKeys(x).every(k => typeof k==='string' && (required.includes(k) || optional.includes(k)));
const id = x => typeof x === 'string' && ID.test(x);
const code = x => typeof x === 'string' && CODE.test(x);
const text = (x, max = TEXT_LIMIT) => typeof x === 'string' && x.trim().length > 0 && x.length <= max && !/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(x);
const int = x => Number.isSafeInteger(x) && x >= 0;
const bool = x => typeof x === 'boolean';
const array = (a, max = RECORD_LIMIT) => Array.isArray(a) && a.length <= max;
const unique = (items) => new Set(items).size === items.length;
const iso = x => typeof x === 'string' && /(Z|[+-]\d\d:\d\d)$/.test(x) && Number.isFinite(Date.parse(x));
const same = (a,b) => JSON.stringify(a) === JSON.stringify(b);
function freezeTree(x) {
  if (x && typeof x==='object') {for(const v of Object.values(x))freezeTree(v); Object.freeze(x);}
  return x;
}
const boundedValue = x => typeof x === 'string' ? text(x,400) : typeof x === 'boolean' || (typeof x === 'number' && Number.isFinite(x));

function safeTree(value, depth=0, seen=new Set()) {
  if (depth > 12) return false;
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return true;
  if (typeof value === 'number') return Number.isFinite(value);
  if (typeof value !== 'object' || seen.has(value)) return false;
  if (!Array.isArray(value) && !plain(value)) return false;
  if (Array.isArray(value) && (value.length>128 || Object.keys(value).length!==value.length ||
      Object.keys(value).some(k=> !/^(0|[1-9][0-9]*)$/.test(k) || Number(k)>=value.length)))return false;
  if (Reflect.ownKeys(value).some(k => typeof k !== 'string' || ['__proto__','constructor','prototype'].includes(k))) return false;
  seen.add(value);
  const descriptors = Object.getOwnPropertyDescriptors(value);
  for (const [k,d] of Object.entries(descriptors)) {
    if (!own(d,'value') || !safeTree(d.value, depth+1, seen)) return false;
  }
  seen.delete(value);
  return true;
}

/** JSON.parse alone accepts duplicate keys; reject them, including escaped aliases. */
export function parseStrictJSON(raw) {
  if (typeof raw !== 'string' || Buffer.byteLength(raw,'utf8') > 32768) return bad('SCHEMA_INVALID','JSON');
  try {
    const value = JSON.parse(raw);
    const stack = [];
    const lexical = /"(?:\\.|[^"\\])*"|[{}\[\]]/g;
    for (const m of raw.matchAll(lexical)) {
      const t=m[0];
      if (t==='{' || t==='[') {
        stack.push(t==='{' ? new Set() : null);
        if (stack.length>12) return bad('SCHEMA_INVALID','JSON');
      } else if (t==='}' || t===']') stack.pop();
      else if (/^\s*:/.test(raw.slice(m.index+t.length))) {
        const set=stack.at(-1), k=JSON.parse(t);
        if (!(set instanceof Set) || set.has(k)) return bad('SCHEMA_INVALID','JSON');
        set.add(k);
      }
    }
    return safeTree(value) ? {status:'PARSED',value} : bad('SCHEMA_INVALID','JSON');
  } catch { return bad('SCHEMA_INVALID','JSON'); }
}

function checkVersions(s) {
  return keys(s,['authenticated','authorized','tenantAllowed','storeId','caseId','personId','expected','current']) &&
    [s.storeId,s.caseId,s.personId].every(id) &&
    keys(s.expected,VERSION_KEYS) && keys(s.current,VERSION_KEYS) &&
    VERSION_KEYS.every(k=>int(s.expected[k])&&int(s.current[k]));
}
function baseEnvelope(e) {
  return keys(e,['schemaVersion','operation','requestId','attemptId','providerTag','nowMs','deadlineMs','scope','privacy','instructions','task']) &&
    e.schemaVersion===PRIVATE_SCHEMA && KINDS.includes(e.operation) &&
    [e.requestId,e.attemptId,e.providerTag].every(id) &&
    int(e.nowMs)&&int(e.deadlineMs) && e.deadlineMs>e.nowMs &&
    keys(e.privacy,['modelContentAuthorized','dataMinimized']) &&
    e.privacy.modelContentAuthorized===true && e.privacy.dataMinimized===true &&
    checkVersions(e.scope) &&
    keys(e.instructions, e.operation==='F01' ? ['text','behavior','version'] : ['text','version']) &&
    text(e.instructions.text,2000) && id(e.instructions.version) &&
    (e.operation!=='F01'||text(e.instructions.behavior,2000));
}
function f01Task(t,scope,nowMs) {
  if (!keys(t,['owner','handoff','humanized','modality','recentContext','sources']) ||
      t.owner!=='ai'||t.handoff!==false||t.humanized!==false||!['text','audio'].includes(t.modality)||
      !array(t.recentContext,20)||!array(t.sources)||!unique(t.sources.map(s=>s?.id))) return false;
  if (!t.recentContext.every(x=>keys(x,['role','text'])&&['customer','ai'].includes(x.role)&&text(x.text))) return false;
  return t.sources.every(s=>keys(s,['id','storeId','approved','active','mode','content','modelAllowed'],['validUntil'])&&
    id(s.id)&&s.storeId===scope.storeId&&s.approved===true&&bool(s.active)&&s.modelAllowed===true&&
    ['current','historical'].includes(s.mode)&&text(s.content)&&
    (!own(s,'validUntil')||iso(s.validUntil)) &&
    (s.mode!=='current'||(s.active===true&&(!own(s,'validUntil')||Date.parse(s.validUntil)>nowMs))));
}
function f02Task(t,scope) {
  return keys(t,['explicitS0Request','optOut','handoffPlanReuse','ownerRoute','purpose','allowedTemplates','maxAttempts','windowStart','windowEnd']) &&
    t.explicitS0Request===true&&t.optOut===false&&t.handoffPlanReuse===false&&
    ['human','seller_ai'].includes(t.ownerRoute) && id(t.purpose) &&
    !(t.purpose==='post_human'&&t.ownerRoute!=='human') &&
    int(t.maxAttempts)&&t.maxAttempts<=16&&iso(t.windowStart)&&iso(t.windowEnd)&&
    Date.parse(t.windowStart)<Date.parse(t.windowEnd) &&
    array(t.allowedTemplates) && unique(t.allowedTemplates.map(x=>x?.id+'@'+x?.version)) &&
    t.allowedTemplates.every(x=>keys(x,['id','version','storeId','purpose','active','eligible'])&&
      id(x.id)&&id(x.version)&&x.storeId===scope.storeId&&x.purpose===t.purpose&&
      x.active===true&&x.eligible===true);
}
function f03Task(t,scope) {
  if (!keys(t,['humanClosed','closureAuthenticated','closureId','personId','cutoffSequence','records','catalog','verifiedWithdrawalSourceIds']) ||
      t.humanClosed!==true||t.closureAuthenticated!==true||!id(t.closureId)||t.personId!==scope.personId||
      !int(t.cutoffSequence)||!array(t.records)||!array(t.catalog)||!array(t.verifiedWithdrawalSourceIds) ||
      !unique(t.records.map(r=>r?.id))||!unique(t.catalog.map(f=>f?.code))||!unique(t.verifiedWithdrawalSourceIds)) return false;
  if (!t.catalog.every(f=>keys(f,['code','essential'])&&code(f.code)&&bool(f.essential))) return false;
  if (!t.records.every(r=>keys(r,['id','storeId','personId','caseId','sequence','author','kind','available','contentAuthorized','content','claims'])&&
      [r.id,r.caseId,r.author].every(id)&&r.storeId===scope.storeId&&r.personId===scope.personId&&
      int(r.sequence)&&['text','media'].includes(r.kind)&&bool(r.available)&&bool(r.contentAuthorized)&&
      (r.available ? r.contentAuthorized===true&&text(r.content) : r.content===''&&r.contentAuthorized===false) &&
      array(r.claims) && r.claims.every(c=>keys(c,['code','value','explicit']) && code(c.code) &&
        boundedValue(c.value) && bool(c.explicit)))) return false;
  return t.verifiedWithdrawalSourceIds.every(id=> t.records.some(r=>r.id===id&&r.available&&r.sequence<=t.cutoffSequence));
}
function coreRequest(e) {
  const scope=e.scope,t=e.task;
  if (e.operation==='F01') return {scope,owner:t.owner,handoff:t.handoff,humanized:t.humanized,nowMs:e.nowMs,
    sources:t.sources.map(({id,storeId,approved,active,mode,validUntil})=>({id,storeId,approved,active,mode,...(validUntil===undefined?{}:{validUntil})}))};
  if (e.operation==='F02') return {scope,explicitS0Request:t.explicitS0Request,optOut:t.optOut,handoffPlanReuse:t.handoffPlanReuse,
    ownerRoute:t.ownerRoute,purpose:t.purpose,maxAttempts:t.maxAttempts,windowStart:t.windowStart,windowEnd:t.windowEnd,
    allowedTemplates:t.allowedTemplates.map(({id,version,storeId,purpose,active})=>({id,version,storeId,purpose,active}))};
  return {scope,humanClosed:t.humanClosed,closureAuthenticated:t.closureAuthenticated,closureId:t.closureId,personId:t.personId,
    cutoffSequence:t.cutoffSequence,records:t.records.map(({claims,...r})=>r),catalog:t.catalog,verifiedWithdrawalSourceIds:t.verifiedWithdrawalSourceIds};
}
function aliasTable(e) {
  const items=e.operation==='F01'?e.task.sources:e.operation==='F02'?e.task.allowedTemplates:e.task.records
    .filter(r=>r.sequence<=e.task.cutoffSequence&&r.available);
  return items.map((x,i)=>({alias:(e.operation==='F02'?'tpl_':'src_')+String(i+1).padStart(3,'0'),id:x.id}));
}

/** Returns only candidate private state; NEVER pass its output to the supplier. */
export function validatePrivateEnvelope(envelope) {
  try {
    // Read the authorization scope through descriptors first; a caller-supplied
    // accessor must never run even in a rejection path.
    if (!plain(envelope)) return bad('DENIED','S0');
    const descriptor=Object.getOwnPropertyDescriptor(envelope,'scope');
    if (!descriptor || !own(descriptor,'value') || !plain(descriptor.value)) return bad('DENIED','S0');
    const scope=descriptor.value;
    const authorized=k=>Object.getOwnPropertyDescriptor(scope,k)?.value===true;
    if (!authorized('authenticated')||!authorized('authorized')||!authorized('tenantAllowed'))
      return bad('DENIED','S0');
    if (!safeTree(envelope) || !baseEnvelope(envelope)) return bad('INVALID_INPUT','PRIVATE');
    const v=versionGate(envelope.scope);
    if (v.status!=='READY') return bad(v.status,'S0');
    const valid=envelope.operation==='F01'?f01Task(envelope.task,envelope.scope,envelope.nowMs):
      envelope.operation==='F02'?f02Task(envelope.task,envelope.scope):f03Task(envelope.task,envelope.scope);
    if (!valid) return bad('INVALID_INPUT','TASK');
    const req=coreRequest(envelope);
    if (envelope.operation==='F03') {
      const history=prepareF03History(req);
      if (history.status!=='READY') return bad(history.status,'F03_HISTORY');
    }
    // Snapshot keeps this immutable-from-caller. No implicit Date.now or model reads.
    const copy=freezeTree(structuredClone(envelope));
    const privateContext=Object.freeze({envelope:copy,aliases:freezeTree(aliasTable(copy))});
    issued.add(privateContext);
    return Object.freeze({status:'READY',privateContext});
  } catch { return bad('MODEL_FAILURE','PRIVATE'); }
}

/** Provider view deliberately does not contain private operation identifiers or grants. */
export function buildProviderPayload(ready) {
  try {
    if (ready?.status!=='READY'||!plain(ready.privateContext)||!issued.has(ready.privateContext)) return bad('INVALID_INPUT','PROJECTION');
    const {envelope:e,aliases}=ready.privateContext;
    if (!baseEnvelope(e)||!safeTree(e)) return bad('INVALID_INPUT','PROJECTION');
    const a=new Map(aliases.map(x=>[x.id,x.alias]));
    const instructions=e.operation==='F01'?
      {text:e.instructions.text,behavior:e.instructions.behavior} : {text:e.instructions.text};
    let material;
    if (e.operation==='F01') material={modality:e.task.modality,context:e.task.recentContext.map(x=>({...x})),
      sources:e.task.sources.map(x=>({alias:a.get(x.id),mode:x.mode,content:x.content}))};
    else if (e.operation==='F02') material={purpose:e.task.purpose,windowStart:e.task.windowStart,
      windowEnd:e.task.windowEnd,maxAttempts:e.task.maxAttempts,
      templates:e.task.allowedTemplates.map(x=>({alias:a.get(x.id),version:x.version}))};
    else material={evidence:e.task.records.filter(r=>r.sequence<=e.task.cutoffSequence&&r.available)
      .map(r=>({alias:a.get(r.id),kind:r.kind,content:r.content})),
      catalog:e.task.catalog.map(x=>({code:x.code,essential:x.essential}))};
    return {schemaVersion:PROVIDER_SCHEMA,operation:e.operation,providerTag:e.providerTag,instructions,material};
  } catch { return bad('MODEL_FAILURE','PROJECTION'); }
}

function aliasMap(context){return new Map(context.aliases.map(x=>[x.alias,x.id]));}
function parseAnswer(raw){
  if (typeof raw==='string') {const parsed=parseStrictJSON(raw);return parsed.status==='PARSED'?parsed.value:null;}
  return safeTree(raw) ? raw : null;
}
function f01Proposal(value, table) {
  if (!keys(value,['text','sourceAliases','commercial','modality'],['handoffAdvisory']) ||
      !text(value.text)||!array(value.sourceAliases)||!unique(value.sourceAliases)||
      !value.sourceAliases.every(a=>id(a)&&table.has(a))||!bool(value.commercial)||
      !['text','audio'].includes(value.modality)||
      (own(value,'handoffAdvisory') && typeof value.handoffAdvisory!=='boolean')) return null;
  return {text:value.text,sourceIds:value.sourceAliases.map(a=>table.get(a)),commercial:value.commercial,
    modality:value.modality,...(own(value,'handoffAdvisory')?{handoffAdvisory:value.handoffAdvisory}:{})};
}
function f02Proposal(value, table, task) {
  if (!keys(value,['attempts','finalTemplate'])||!array(value.attempts,16)||value.attempts.length>task.maxAttempts) return null;
  const tr = p => {
    if (!keys(p,['templateAlias','version','purpose','at'])||!id(p.templateAlias)||!table.has(p.templateAlias)||
        !id(p.version)||!id(p.purpose)||!iso(p.at)) return null;
    return {templateId:table.get(p.templateAlias),version:p.version,purpose:p.purpose,at:p.at};
  };
  const attempts=value.attempts.map(tr);
  if(attempts.some(p=>p===null))return null;
  const finalTemplate=value.finalTemplate===null?null:tr(value.finalTemplate);
  if(value.finalTemplate!==null&&finalTemplate===null)return null;
  return {attempts,finalTemplate};
}
function f03Proposal(value, table) {
  if (!keys(value,['fields','conflicts','commercialAdvisory'])||!array(value.fields)||!array(value.conflicts))return null;
  const fields=[];const conflicts=[];
  if(!unique(value.fields.map(x=>x?.code))||!unique(value.conflicts.map(x=>x?.code)))return null;
  for(const f of value.fields){
    if(!keys(f,['code','value','sourceAlias'])||!code(f.code)||!boundedValue(f.value)||!id(f.sourceAlias)||!table.has(f.sourceAlias))return null;
    fields.push({code:f.code,value:f.value,sourceId:table.get(f.sourceAlias)});
  }
  for(const c of value.conflicts){
    if(!keys(c,['code','sourceAliases'])||!code(c.code)||!array(c.sourceAliases)||c.sourceAliases.length<2||
        !unique(c.sourceAliases)||!c.sourceAliases.every(a=>id(a)&&table.has(a)))return null;
    conflicts.push({code:c.code,sourceIds:c.sourceAliases.map(a=>table.get(a))});
  }
  let commercialAdvisory=null;
  if(value.commercialAdvisory!==null){
    const adv=value.commercialAdvisory;
    if(!keys(adv,['kind','sourceAliases'])||adv.kind!=='perdido'||!array(adv.sourceAliases)||
       !adv.sourceAliases.length||!unique(adv.sourceAliases)||!adv.sourceAliases.every(a=>id(a)&&table.has(a)))return null;
    commercialAdvisory={kind:'perdido',sourceIds:adv.sourceAliases.map(a=>table.get(a))};
  }
  return {fields,conflicts,commercialAdvisory};
}

/** Model output is untrusted; correlation is checked against the *private* context. */
export function validateProviderCandidate(ready, raw) {
  try {
    if (ready?.status!=='READY'||!issued.has(ready.privateContext)) return bad('DENIED','RESULT');
    const e=ready.privateContext.envelope;
    if (e.scope.authenticated!==true||e.scope.authorized!==true||e.scope.tenantAllowed!==true) return bad('DENIED','S0');
    if (versionGate(e.scope).status!=='READY') return bad('STALE','S0');
    const answer=parseAnswer(raw);
    if (!keys(answer,['schemaVersion','operation','providerTag','state','output'])||
        answer.schemaVersion!==RESPONSE_SCHEMA||!KINDS.includes(answer.operation)||
        answer.operation!==e.operation||answer.providerTag!==e.providerTag||
        !['completed','refused'].includes(answer.state)) return bad('SCHEMA_INVALID','RESULT');
    if (answer.state==='refused')return answer.output===null?bad('MODEL_REFUSAL','PROVIDER'):bad('SCHEMA_INVALID','RESULT');
    const table=aliasMap(ready.privateContext);
    const prop=e.operation==='F01'?f01Proposal(answer.output,table):
      e.operation==='F02'?f02Proposal(answer.output,table,e.task):f03Proposal(answer.output,table);
    if (!prop)return bad('SCHEMA_INVALID','PROPOSAL');
    const req=coreRequest(e);
    const gate=e.operation==='F01'?validateF01(req,prop):
      e.operation==='F02'?validateF02(req,prop):validateF03Proposal(req,prepareF03History(req),prop);
    if(gate.status!=='PROPOSED')return bad(gate.status,'S2_GATE');
    if (e.operation==='F03') {
      // Independent synthetically attested claims: never silently select a conflicting latest value.
      // These claims are NOT semantic/S0 evidence; operational S0 must validate them itself.
      const observed=new Map();
      for(const f of prop.fields) {
        const origin=e.task.records.find(r=>r.id===f.sourceId&&r.available&&r.sequence<=e.task.cutoffSequence);
        if(!origin?.claims.some(c=>c.explicit&&c.code===f.code&&same(c.value,f.value)))
          return bad('REVIEW_REQUIRED','F03_CLAIM');
      }
      if(prop.commercialAdvisory!==null && !prop.commercialAdvisory.sourceIds.every(sourceId =>
        e.task.records.some(r=>r.id===sourceId&&r.claims.some(c=>c.code==='customer_withdrawal'&&c.explicit&&c.value===true))))
        return bad('REVIEW_REQUIRED','F03_CLAIM');
      for(const r of e.task.records) {
        if(r.sequence>e.task.cutoffSequence||!r.available)continue;
        for(const c of r.claims) {
          if(!c.explicit||!e.task.catalog.some(f=>f.code===c.code))continue;
          if(observed.has(c.code)&&!same(observed.get(c.code),c.value)) return bad('REVIEW_REQUIRED','F03_CONFLICT');
          observed.set(c.code,c.value);
        }
      }
    }
    // No APPLIED, SENT, recheck success, identity authorization or business effect.
    return {status:'PROPOSED',stage:'S0_RECHECK_PENDING',operation:e.operation,
      privateReceipt:{requestId:e.requestId,attemptId:e.attemptId,storeId:e.scope.storeId,
        caseId:e.scope.caseId,personId:e.scope.personId,expectedVersions:structuredClone(e.scope.expected),
        ...(e.operation==='F03'?{closureId:e.task.closureId,cutoffSequence:e.task.cutoffSequence}:{}),
        sourceIds:[...table.values()]},proposal:prop,
      assurance:{s0AuthorizedOperationally:false,semanticVerified:false,providerCalled:false,e02Homologated:false}};
  } catch {return bad('MODEL_FAILURE','RESULT');}
}

const fingerprint = raw => createHash('sha256').update(typeof raw==='string'?raw:JSON.stringify(raw)).digest('hex');
/** All inputs synthetic. Replay state is caller-supplied, not a durable idempotency ledger. */
export function simulateOfflineExchange(envelope, providerEvent, options={}) {
  try {
    const prepared=validatePrivateEnvelope(envelope);
    if(prepared.status!=='READY')return prepared;
    const e=prepared.privateContext.envelope;
    const current=options.currentScope??e.scope;
    if(!plain(current)||current.authenticated!==true||current.authorized!==true||current.tenantAllowed!==true)
      return bad('DENIED','RETURN_S0');
    if(!checkVersions(current)||current.storeId!==e.scope.storeId||current.caseId!==e.scope.caseId||
       current.personId!==e.scope.personId)return bad('DENIED','RETURN_S0');
    if(!same(current.expected,e.scope.expected)||!same(current.current,e.scope.current)||
       versionGate(current).status!=='READY')return bad('STALE','RETURN_S0');
    const time=options.timeMs??e.nowMs;
    if(!int(time))return bad('INVALID_INPUT','CLOCK');
    if(time>e.deadlineMs)return bad('TIMEOUT','RETURN_S0');
    if(!keys(providerEvent,['kind'],['raw'])||!['reply','refusal','timeout','quota','unavailable','exception'].includes(providerEvent.kind))
      return bad('INVALID_INPUT','SIMULATOR');
    if(providerEvent.kind==='timeout')return bad('TIMEOUT','PROVIDER');
    if(providerEvent.kind==='quota')return bad('QUOTA_EXCEEDED','PROVIDER');
    if(providerEvent.kind==='unavailable'||providerEvent.kind==='exception')return bad('MODEL_FAILURE','PROVIDER');
    if(providerEvent.kind==='refusal')return bad('MODEL_REFUSAL','PROVIDER');
    if(!own(providerEvent,'raw'))return bad('SCHEMA_INVALID','RESULT');
    const prior=options.prior??null;
    if(prior!==null){
      if(!keys(prior,['providerTag','fingerprint'])||!id(prior.providerTag)||!/^[0-9a-f]{64}$/.test(prior.fingerprint))
        return bad('INVALID_INPUT','REPLAY');
      if(prior.providerTag!==e.providerTag)return bad('REPLAY_CONFLICT','REPLAY');
    }
    if(typeof providerEvent.raw!=='string' && !safeTree(providerEvent.raw))return bad('SCHEMA_INVALID','RESULT');
    const f=fingerprint(providerEvent.raw);
    if(prior!==null)return bad(prior.fingerprint===f?'ALREADY_HANDLED':'REPLAY_CONFLICT','REPLAY');
    const validated=validateProviderCandidate(prepared,providerEvent.raw);
    return validated.status==='PROPOSED' ? {...validated,replayCandidate:{providerTag:e.providerTag,fingerprint:f}} : validated;
  } catch {return bad('MODEL_FAILURE','SIMULATOR');}
}

/** Sanitized diagnostics only: no raw request, content, stack, path, or credentials. */
const AUDITABLE_STATUSES=new Set(['DENIED','INVALID_INPUT','STALE','SCHEMA_INVALID',
  'SOURCE_INVALID','MODEL_REFUSAL','MODEL_FAILURE','TIMEOUT','QUOTA_EXCEEDED',
  'REPLAY_CONFLICT','ALREADY_HANDLED','REVIEW_REQUIRED','PROPOSED']);
export function safeAuditEvent(outcome,operation) {
  return Object.freeze({operation:KINDS.includes(operation)?operation:'UNKNOWN',
    status:AUDITABLE_STATUSES.has(outcome?.status)?outcome.status:'MODEL_FAILURE',
    stage:typeof outcome?.stage==='string'&&/^[A-Z_]+$/.test(outcome.stage)?outcome.stage:'UNKNOWN',
    schemaVersion:PRIVATE_SCHEMA});
}
