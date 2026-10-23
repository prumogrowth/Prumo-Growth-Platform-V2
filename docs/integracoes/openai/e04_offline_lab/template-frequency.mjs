// E04 synthetic F02 preflight. No Meta API. No S0 write. No universal provider cap.
const rec = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const id = x => typeof x === 'string' && /^[A-Za-z0-9_.:-]{1,100}$/.test(x);
const iso = x => typeof x === 'string' && /(Z|[+-]\d{2}:\d{2})$/.test(x) && Number.isFinite(Date.parse(x));
const keys = (x, fields) => rec(x) && Object.keys(x).every(k => fields.includes(k));
const result = status => Object.freeze({status});
const STATES = new Set(['sent', 'pending', 'failed']);
const CATEGORIES = new Set(['MARKETING', 'UTILITY', 'AUTHENTICATION']);

/**
 * All data must come from an authenticated, authorized, up-to-date S0 fixture.
 * Positive results mean locally eligible only, NOT permission from Meta.
 */
export function assessTemplateFrequency(scope, attempt, policy, history) {
  if (!rec(scope) || scope.authenticated !== true || scope.authorized !== true || scope.tenantAllowed !== true) return result('DENIED');
  if (![scope.storeId, scope.personId, scope.caseId].every(id) || !Array.isArray(history)) return result('INVALID_INPUT');
  if (!keys(attempt, ['storeId','personId','templateId','category','purpose','approved','active','optIn','optOut','requestedAt','metaHold']) ||
      !id(attempt.templateId) || attempt.storeId !== scope.storeId || attempt.personId !== scope.personId ||
      !id(attempt.purpose) || !CATEGORIES.has(attempt.category) || !iso(attempt.requestedAt) ||
      typeof attempt.approved !== 'boolean' || typeof attempt.active !== 'boolean' ||
      typeof attempt.optIn !== 'boolean' || typeof attempt.optOut !== 'boolean' ||
      typeof attempt.metaHold !== 'boolean') return result('INVALID_INPUT');
  if (!attempt.optIn || attempt.optOut || !attempt.approved || !attempt.active) return result('DENIED');
  if (attempt.metaHold) return result('META_HOLD_REVIEW');
  // Non-marketing still needs ALL other S0/Meta guards (category, purpose, quality, throughput etc.).
  if (attempt.category !== 'MARKETING') return result('LOCAL_CATEGORY_NOT_CAPPED');
  if (!keys(policy, ['maxMarketingPerWindow','windowHours','policyVersion']) ||
      !Number.isSafeInteger(policy.maxMarketingPerWindow) || policy.maxMarketingPerWindow < 0 ||
      !Number.isSafeInteger(policy.windowHours) || policy.windowHours < 1 || policy.windowHours > 720 ||
      !id(policy.policyVersion)) return result('REVIEW_REQUIRED');
  const at = Date.parse(attempt.requestedAt), since = at - policy.windowHours * 3600000;
  const uniq = new Set(); let reserved = 0;
  for (const h of history) {
    if (!keys(h, ['eventId','storeId','personId','category','at','state','verified']) ||
        ![h.eventId,h.storeId,h.personId].every(id) || !CATEGORIES.has(h.category) ||
        !iso(h.at) || !STATES.has(h.state) || typeof h.verified !== 'boolean' ||
        h.storeId !== scope.storeId || h.personId !== scope.personId) return result('INVALID_INPUT');
    if (!h.verified || uniq.has(h.eventId)) return result('REVIEW_REQUIRED');
    uniq.add(h.eventId);
    const time = Date.parse(h.at);
    if (time > at) return result('REVIEW_REQUIRED');
    if (h.category === 'MARKETING' && h.state !== 'failed' && time > since) reserved++;
  }
  if (reserved >= policy.maxMarketingPerWindow) return Object.freeze({status:'HOLD_LOCAL_POLICY', reserved, policyVersion:policy.policyVersion});
  return Object.freeze({status:'LOCAL_ELIGIBLE_META_UNCONFIRMED', reserved, policyVersion:policy.policyVersion});
}

/** A Meta healthy-ecosystem rejection is not proven loss of customer interest. */
export function classifyMetaMarketingError(scope, event) {
  if (!rec(scope) || scope.authenticated !== true || scope.authorized !== true || scope.tenantAllowed !== true) return result('DENIED');
  if (!keys(event, ['storeId','personId','errorCode','providerVerified']) ||
      !id(event.storeId) || !id(event.personId) || !Number.isSafeInteger(event.errorCode) ||
      event.storeId !== scope.storeId || event.personId !== scope.personId || event.providerVerified !== true) return result('REVIEW_REQUIRED');
  if (event.errorCode === 131049) return Object.freeze({status:'META_ECOSYSTEM_REVIEW', retryAutomatically:false, countForTechnicalLoss:false});
  return result('REVIEW_REQUIRED'); // classification of other errors belongs to S0/Meta
}
