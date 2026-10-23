// E04: pure synthetic orchestration, NOT a production S0 integration.
// Each boolean and identity below must be supplied by a *trusted S0 fixture*.
import {validateF01, validateF02, prepareF03History, validateF03Proposal} from './core.mjs';
import {reconcileF02Plan} from './plan-lifecycle.mjs';
import {assessTemplateFrequency} from './template-frequency.mjs';

const obj = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const ident = x => typeof x === 'string' && /^[A-Za-z0-9_.:-]{1,100}$/.test(x);
const result = (status, stage) => Object.freeze({status, stage});
const same = (scope, root, needPerson = false) =>
  obj(scope) && scope.authenticated === true && scope.authorized === true &&
  scope.tenantAllowed === true && scope.storeId === root.storeId &&
  scope.caseId === root.caseId && (!needPerson || scope.personId === root.personId);

export function evaluateOfflineJourney(flow) {
  // Authorization check always precedes any identity or state disclosure.
  const root = flow?.scope;
  if (!obj(root) || root.authenticated !== true || root.authorized !== true || root.tenantAllowed !== true)
    return result('DENIED', 'S0');
  if (![root.storeId, root.caseId, root.personId].every(ident) ||
      !obj(flow.beforeHandoff) || !obj(flow.handoff) || !obj(flow.conclusion))
    return result('INVALID_INPUT', 'INPUT');

  const sales = flow.beforeHandoff;
  if (!same(sales.req?.scope, root)) return result('DENIED', 'F01');
  const f01 = validateF01(sales.req, sales.proposal);
  if (f01.status !== 'PROPOSED') return result(f01.status, 'F01');

  // The handoff is a separate authenticated S0 event: never inferred from conversation.
  if (flow.handoff.authenticated !== true || flow.handoff.storeId !== root.storeId ||
      flow.handoff.caseId !== root.caseId) return result('DENIED', 'HANDOFF');
  // A humanized case can never resume this F01, even when a late proposal arrives.
  const lateF01 = validateF01({...sales.req, owner:'human', handoff:true, humanized:true},sales.proposal);
  if (lateF01.status !== 'DENIED') return result('REVIEW_REQUIRED', 'HANDOFF');

  const extract = flow.conclusion;
  if (!same(extract.req?.scope, root) || extract.req.personId !== root.personId)
    return result('DENIED', 'F03_SCOPE');
  // A valid close must come from S0, independently of transfer and WhatsApp clocks.
  if (extract.req.humanClosed !== true || extract.req.closureAuthenticated !== true)
    return result('NO_F03_TRIGGER', 'HUMAN_CLOSE');
  const snapshot = prepareF03History(extract.req);
  if (snapshot.status !== 'READY') return result(snapshot.status, 'F03_HISTORY');
  const f03 = validateF03Proposal(extract.req, snapshot, extract.proposal);
  if (f03.status === 'REVIEW_REQUIRED') return result('HUMAN_COMPLEMENT_REVIEW', 'F03');
  if (f03.status !== 'PROPOSED') return result(f03.status, 'F03');
  if (extract.proposal.commercialAdvisory !== null)
    return result('COMMERCIAL_ADVISORY_REVIEW', 'F03');
  if (flow.postHuman === null || flow.postHuman === undefined)
    return result('F03_PROPOSAL_ONLY', 'F03');

  const followup = flow.postHuman;
  if (!obj(followup) || !obj(followup.request) ||
      followup.authenticatedS0Request !== true ||
      followup.oldAiPlanCancelled !== true) return result('DENIED', 'F02_REQUEST');
  if (!same(followup.request.scope, root) || followup.request.ownerRoute !== 'human' ||
      followup.request.purpose !== 'post_human' ||
      followup.request.explicitS0Request !== true ||
      followup.request.optOut !== false) return result('DENIED', 'F02_REQUEST');

  const f02 = validateF02(followup.request, followup.proposal);
  if (f02.status !== 'PROPOSED') return result(f02.status, 'F02_PROPOSAL');
  const ps = followup.planScope, plan = followup.plan;
  if (!same(ps, root, true) || !obj(plan) || !Array.isArray(plan.attempts) ||
      plan.purpose !== 'post_human' || plan.ownerRoute !== 'human' ||
      plan.storeId !== root.storeId || plan.caseId !== root.caseId ||
      plan.personId !== root.personId || ps.handoff !== true ||
      ps.caseVersion !== followup.request.scope.expected.case ||
      ps.catalogVersion !== followup.request.scope.expected.catalog)
    return result('DENIED', 'F02_PLAN_BINDING');

  // The model selects template IDs only. S0 independently binds immutable IDs,
  // versions, categories and schedule to a new plan. No model-created category.
  const proposed = [...followup.proposal.attempts,
    ...(followup.proposal.finalTemplate === null ? [] : [followup.proposal.finalTemplate])];
  if (plan.attempts.length !== proposed.length || !Array.isArray(followup.templateCategories))
    return result('INVALID_INPUT', 'F02_PLAN_BINDING');
  const categories = new Map();
  for (const t of followup.templateCategories) {
    if (!obj(t) || !ident(t.id) || !ident(t.version) ||
        t.storeId !== root.storeId || t.purpose !== 'post_human' ||
        !['MARKETING','UTILITY','AUTHENTICATION'].includes(t.category) ||
        categories.has(t.id+'@'+t.version))
      return result('INVALID_INPUT', 'F02_TEMPLATE_SOURCE');
    categories.set(t.id+'@'+t.version,t.category);
  }
  for (let i=0; i<proposed.length; i++) {
    const p = proposed[i],a=plan.attempts[i];
    if (!obj(a) || a.templateId !== p.templateId || a.templateVersion !== p.version ||
        a.at !== p.at || a.isFinal !== (i >= followup.proposal.attempts.length) ||
        a.category !== categories.get(a.templateId+'@'+a.templateVersion))
      return result('SOURCE_INVALID', 'F02_PLAN_BINDING');
  }
  const state = reconcileF02Plan(ps, plan, followup.events);
  if (state.status !== 'READY_FOR_S0_RECHECK')
    return result(state.status, 'F02_LIFECYCLE');

  // There is no universal Meta '2 per day' cap. Local policy is separately versioned.
  const freq = followup.frequency;
  if (!obj(freq) || !obj(freq.consent) || !Array.isArray(freq.history))
    return result('REVIEW_REQUIRED', 'F02_FREQUENCY');
  const preflight = assessTemplateFrequency(
    {...root, authenticated:true,authorized:true,tenantAllowed:true},
    {storeId:root.storeId,personId:root.personId,templateId:state.templateId,
      category:state.category,purpose:'post_human',approved:freq.consent.approved,
      active:freq.consent.active,optIn:freq.consent.optIn,optOut:freq.consent.optOut,
      requestedAt:ps.now,metaHold:freq.consent.metaHold},
    freq.policy,freq.history);
  if (preflight.status === 'HOLD_LOCAL_POLICY') return result('LOCAL_FREQUENCY_HOLD', 'F02_FREQUENCY');
  if (preflight.status === 'META_HOLD_REVIEW') return result('META_HOLD_REVIEW', 'F02_FREQUENCY');
  if (!['LOCAL_ELIGIBLE_META_UNCONFIRMED','LOCAL_CATEGORY_NOT_CAPPED'].includes(preflight.status))
    return result(preflight.status, 'F02_FREQUENCY');
  // No send, booking, status mutation or C09 starts here.
  return result('READY_FOR_S0_RECHECK_ONLY', 'F02');
}
