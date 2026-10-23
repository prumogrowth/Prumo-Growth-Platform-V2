// E04 OpenAI — pure, synthetic F02 lifecycle review; never a send authorization.
// S0 must authenticate/authorize each event and recheck before any real action.
const isRecord = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const validId = x => typeof x === 'string' && /^[A-Za-z0-9_.:-]{1,100}$/.test(x);
const validTime = x => typeof x === 'string' && /(Z|[+-]\d{2}:\d{2})$/.test(x) && Number.isFinite(Date.parse(x));
const only = (x, allowed) => isRecord(x) && Object.keys(x).every(k => allowed.includes(k));
const status = code => Object.freeze({status: code});
const terminal = new Set(['SENT', 'DEFINITIVE_FAILED', 'META_131049']);
const transport = new Set(['API_ACCEPTED', 'QUEUED', 'UNKNOWN', ...terminal]);
const controls = new Set(['CUSTOMER_INBOUND', 'HANDOFF', 'OPT_OUT', 'CANCEL']);

export function reconcileF02Plan(scope, plan, events) {
  // Do not leak plan existence, versions, attempt metadata or identity on denial.
  if (!isRecord(scope) || scope.authenticated !== true || scope.authorized !== true ||
      scope.tenantAllowed !== true || scope.optOut !== false || scope.planAuthorized !== true) {
    return status('DENIED');
  }
  if (!only(scope, ['authenticated','authorized','tenantAllowed','optOut','planAuthorized','storeId','personId','caseId',
                    'caseVersion','catalogVersion','chainVersion','now','handoff']) ||
      ![scope.storeId,scope.personId,scope.caseId].every(validId) || !validTime(scope.now) ||
      ![scope.caseVersion,scope.catalogVersion,scope.chainVersion].every(x=>Number.isSafeInteger(x)&&x>=0) ||
      typeof scope.handoff !== 'boolean' || !Array.isArray(events) ||
      !only(plan, ['id','storeId','personId','caseId','purpose','ownerRoute','caseVersion','catalogVersion','chainVersion','attempts']) ||
      ![plan.id,plan.storeId,plan.personId,plan.caseId,plan.purpose].every(validId) ||
      !['human','seller_ai'].includes(plan.ownerRoute) || !Array.isArray(plan.attempts) || plan.attempts.length===0 ||
      ![plan.caseVersion,plan.catalogVersion,plan.chainVersion].every(x=>Number.isSafeInteger(x)&&x>=0)) {
    return status('INVALID_INPUT');
  }
  if (plan.storeId!==scope.storeId || plan.personId!==scope.personId || plan.caseId!==scope.caseId) return status('DENIED');
  if ((scope.handoff && plan.ownerRoute==='seller_ai') ||
      (plan.purpose==='post_human' && plan.ownerRoute!=='human')) return status('DENIED');
  if (plan.caseVersion!==scope.caseVersion || plan.catalogVersion!==scope.catalogVersion ||
      plan.chainVersion!==scope.chainVersion) return status('STALE');

  const attempts = new Map();
  let prev = -Infinity, finals=0;
  for (const a of plan.attempts) {
    if (!only(a,['id','templateId','templateVersion','category','at','isFinal']) ||
        ![a.id,a.templateId,a.templateVersion].every(validId) || !validTime(a.at) ||
        !['MARKETING','UTILITY','AUTHENTICATION'].includes(a.category) || typeof a.isFinal !== 'boolean' ||
        attempts.has(a.id) || Date.parse(a.at) <= prev || (finals>0 && !a.isFinal)) return status('INVALID_INPUT');
    if (a.isFinal) finals++;
    if (finals>1) return status('INVALID_INPUT');
    prev=Date.parse(a.at);
    attempts.set(a.id,a);
  }

  const seen = new Map(), seqs = new Set();
  for (const e of events) {
    if (!only(e,['eventId','sequence','storeId','personId','caseId','planId','attemptId','kind','verified']) ||
        ![e.eventId,e.storeId,e.personId,e.caseId,e.planId].every(validId) ||
        !Number.isSafeInteger(e.sequence) || e.sequence<0 || !transport.has(e.kind) && !controls.has(e.kind) ||
        typeof e.verified!=='boolean' ||
        (transport.has(e.kind) && !validId(e.attemptId)) ||
        (controls.has(e.kind) && e.attemptId!==null)) return status('INVALID_INPUT');
    if (e.storeId!==scope.storeId || e.personId!==scope.personId || e.caseId!==scope.caseId || e.planId!==plan.id) return status('DENIED');
    if (transport.has(e.kind) && !attempts.has(e.attemptId)) return status('INVALID_INPUT');
    const serialized=JSON.stringify([e.eventId,e.sequence,e.storeId,e.personId,e.caseId,e.planId,e.attemptId,e.kind,e.verified]);
    if (seen.has(e.eventId)) {
      if (seen.get(e.eventId)!==serialized) return status('REVIEW_REQUIRED');
      continue; // exact replay is harmless
    }
    if (seqs.has(e.sequence)) return status('REVIEW_REQUIRED');
    seen.set(e.eventId,serialized); seqs.add(e.sequence);
  }
  const normalized=events.filter((e,i)=> events.findIndex(y=>y.eventId===e.eventId)===i).sort((a,b)=>a.sequence-b.sequence);
  if (normalized.some(e=>!e.verified)) return status('REVIEW_REQUIRED');
  const states=new Map();
  let hold=null, cancelled=false, ecosystemHold=false;
  for (const e of normalized) {
    if (controls.has(e.kind)) {
      if (e.kind==='OPT_OUT' || e.kind==='CANCEL' || e.kind==='HANDOFF' && plan.ownerRoute==='seller_ai') cancelled=true;
      // Customer response may invalidate the purpose; S0 must decide. No automatic F01 return.
      if (e.kind==='CUSTOMER_INBOUND' || e.kind==='HANDOFF') hold='HOLD_FOR_S0_REVIEW';
      continue;
    }
    const state=states.get(e.attemptId) || {terminal:null,pending:false};
    if (e.kind==='META_131049') ecosystemHold=true;
    if (terminal.has(e.kind)) {
      if (state.terminal && state.terminal!==e.kind) return status('REVIEW_REQUIRED');
      state.terminal=e.kind;
    } else if (!state.terminal) state.pending=true;
    states.set(e.attemptId,state);
  }
  if (cancelled) return status('CANCELLED');
  if (ecosystemHold) return status('META_ECOSYSTEM_REVIEW');
  if (hold) return status(hold);
  if ([...states.values()].some(s=>s.terminal==='DEFINITIVE_FAILED')) return status('REVIEW_REQUIRED');
  for (const a of plan.attempts) {
    const s=states.get(a.id);
    if (s?.terminal==='SENT') {
      if (a.isFinal) return status('FINAL_SENT_EVIDENCE_ONLY');
      continue;
    }
    if (s?.pending) return status('AWAITING_META_PROOF');
    if (Date.parse(a.at)>Date.parse(scope.now)) return status('NOT_DUE');
    return Object.freeze({status:'READY_FOR_S0_RECHECK',attemptId:a.id,templateId:a.templateId,
      templateVersion:a.templateVersion,category:a.category});
  }
  return status('NO_PENDING_ATTEMPT');
}
