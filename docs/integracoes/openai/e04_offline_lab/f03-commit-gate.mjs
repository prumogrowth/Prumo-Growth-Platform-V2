// E04 synthetic F03 commit preflight. No writes or model/provider calls.
// All identity, evidence and prior-result assertions must come from S0; not from F03.
const rec = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const id = x => typeof x === 'string' && /^[A-Za-z0-9_.:-]{1,120}$/.test(x);
const fail = status => Object.freeze({status});
const fields = ['case','cycle','form','catalog','assignment','identity'];
const versions = v => rec(v) && fields.every(k => Number.isSafeInteger(v[k]) && v[k]>=0)
  && Object.keys(v).length===fields.length;
const sameValue = (a,b) => typeof a === typeof b && (typeof a==='string' || typeof a==='number' || typeof a==='boolean') && a === b;
const allowed = (x,keys) => rec(x) && Object.keys(x).every(k=>keys.includes(k));

export function evaluateF03CommitCandidate({scope,cutoff,proposal,catalog,current,prior} = {}) {
  // Authorize before returning any identity, history, version, field or replay information.
  if (!rec(scope) || scope.authenticated!==true || scope.authorized!==true || scope.tenantAllowed!==true)
    return fail('DENIED');
  if (![scope.storeId,scope.personId,scope.caseId,scope.closureId,scope.requestId].every(id) ||
      !rec(cutoff) || !rec(current) || !rec(proposal) || !Array.isArray(catalog))
    return fail('INVALID_INPUT');
  if (![cutoff.storeId,cutoff.personId,cutoff.closureId].every(id) ||
      cutoff.storeId!==scope.storeId || cutoff.personId!==scope.personId || cutoff.closureId!==scope.closureId)
    return fail('DENIED');
  if (cutoff.s0ClosureVerified!==true || cutoff.historyComplete!==true || !id(cutoff.snapshotRef) ||
      !Number.isSafeInteger(cutoff.watermark) || cutoff.watermark<0 || !Array.isArray(cutoff.sources))
    return fail('HISTORY_REVIEW_REQUIRED');
  if (!versions(cutoff.expectedVersions) || !versions(current.versions) || current.closureStillAuthorized!==true ||
      current.assignmentAuthorized!==true || current.personScopeVerified!==true)
    return fail('REVIEW_REQUIRED');
  if (fields.some(k=>cutoff.expectedVersions[k]!==current.versions[k])) return fail('STALE');
  if (prior!==null && prior!==undefined) {
    if (!allowed(prior,['requestId','closureId','snapshotRef','proposalRef','s0Verified']) ||
        ![prior.requestId,prior.closureId,prior.snapshotRef,prior.proposalRef].every(id) || prior.s0Verified!==true)
      return fail('REVIEW_REQUIRED');
    if (prior.requestId===scope.requestId && prior.closureId===scope.closureId &&
        prior.snapshotRef===cutoff.snapshotRef && prior.proposalRef===proposal.proposalRef)
      return fail('ALREADY_HANDLED');
    return fail('REVIEW_REQUIRED'); // no replay using another closure, content or snapshot
  }
  if (!id(proposal.proposalRef) || !Array.isArray(proposal.fields) || !Array.isArray(proposal.conflicts) ||
      !Object.prototype.hasOwnProperty.call(proposal,'advisory')) return fail('SCHEMA_INVALID');
  const known = new Map();
  for (const f of catalog) {
    if (!allowed(f,['code','essential']) || !id(f.code) || typeof f.essential!=='boolean' || known.has(f.code))
      return fail('INVALID_INPUT');
    known.set(f.code,f);
  }
  const sources = new Map();
  for (const s of cutoff.sources) {
    if (!allowed(s,['id','storeId','personId','caseId','sequence','available','s0Verified','claims']) ||
        ![s.id,s.storeId,s.personId,s.caseId].every(id) || sources.has(s.id) ||
        s.storeId!==scope.storeId || s.personId!==scope.personId ||
        !Number.isSafeInteger(s.sequence) || s.sequence<0 || s.sequence>cutoff.watermark ||
        typeof s.available!=='boolean' || typeof s.s0Verified!=='boolean' || !Array.isArray(s.claims))
      return fail('SOURCE_INVALID');
    sources.set(s.id,s);
  }
  const proposed = new Set();
  for (const f of proposal.fields) {
    if (!allowed(f,['code','value','sourceId']) || !id(f.code) || !id(f.sourceId) ||
        !known.has(f.code) || proposed.has(f.code) || !sources.has(f.sourceId) ||
        !['string','number','boolean'].includes(typeof f.value) ||
        typeof f.value==='string' && !f.value.trim() ||
        typeof f.value==='number' && !Number.isFinite(f.value)) return fail('SOURCE_INVALID');
    const s=sources.get(f.sourceId);
    if (!s.available || !s.s0Verified || !s.claims.some(c=>allowed(c,['code','value','explicit']) &&
        c.code===f.code && c.explicit===true && sameValue(c.value,f.value)))
      return fail('SOURCE_INVALID');
    proposed.add(f.code);
  }
  for (const c of proposal.conflicts) {
    if (!allowed(c,['code','sourceIds']) || !known.has(c.code) || !Array.isArray(c.sourceIds) ||
        c.sourceIds.length<2 || c.sourceIds.some(sourceId=>!sources.has(sourceId) ||
        !sources.get(sourceId).available || !sources.get(sourceId).s0Verified)) return fail('SOURCE_INVALID');
  }
  if (proposal.advisory!==null) {
    if (!allowed(proposal.advisory,['kind','sourceId']) || proposal.advisory.kind!=='perdido' ||
        !id(proposal.advisory.sourceId) || !sources.has(proposal.advisory.sourceId) ||
        !sources.get(proposal.advisory.sourceId).claims.some(c=>c.code==='customer_withdrawal' &&
        c.explicit===true && c.value===true)) return fail('SOURCE_INVALID');
    return fail('COMMERCIAL_ADVISORY_REVIEW');
  }
  if (proposal.conflicts.length>0 || [...known.values()].some(f=>f.essential&&!proposed.has(f.code)))
    return fail('HUMAN_REVIEW_REQUIRED');
  // No customer values, SQL commands or commercial statuses in the result.
  return Object.freeze({status:'S0_RECHECK_ONLY',fieldCodes:[...proposed].sort(),snapshotRef:cutoff.snapshotRef});
}
