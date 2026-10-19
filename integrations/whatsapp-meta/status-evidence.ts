/**
 * WA-09: pure, OFFLINE technical validation at the Graph -> status boundary.
 * No network, database, HTTP ACK, business status, credentials, or retry.
 * These predicates do NOT authenticate Meta or attest durable persistence.
 */
/** Internal correlation identifiers never carry recipient, token or raw Meta payload. */
export function isSafeEvidenceRef(value: unknown): value is string {
  return typeof value === 'string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(value);
}

export function isMetaWamid(value: unknown): value is string {
  return typeof value === 'string' && /^wamid\.[A-Za-z0-9+\/_=:.-]{1,1024}$/.test(value);
}

export function isStatusPosition(value: unknown): boolean {
  try {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
    const prototype = Object.getPrototypeOf(value);
    if (prototype !== Object.prototype && prototype !== null) return false;
    const fields = Object.getOwnPropertyDescriptors(value);
    const keys = ['entry_index', 'change_index', 'array_kind', 'item_index'];
    if (Object.keys(fields).length !== keys.length ||
        !keys.every(key => Object.prototype.hasOwnProperty.call(fields, key) &&
          Object.prototype.hasOwnProperty.call(fields[key], 'value'))) return false;
    const p = value as Record<string, unknown>;
    return p.array_kind === 'statuses' &&
      [p.entry_index, p.change_index, p.item_index].every(n =>
        typeof n === 'number' && Number.isSafeInteger(n) && n >= 0);
  } catch {
    return false;
  }
}

/**
 * Coherent result of an *already observed* Graph HTTP response, not evidence
 * of delivery/sent callback, opt-in, tenant permission, or commercial status.
 */
export function isAcceptedGraphEvidence(value: unknown): boolean {
  try {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
    const prototype = Object.getPrototypeOf(value);
    if (prototype !== Object.prototype && prototype !== null) return false;
    const fields = Object.getOwnPropertyDescriptors(value);
    const keys = ['attempt_id', 'correlation_id', 'send_state', 'api_accepted',
      'http_status', 'provider_message_id', 'meta_error_code',
      'meta_error_subcode', 'retry_automatically'];
    if (Object.keys(fields).length !== keys.length ||
        !keys.every(key => Object.prototype.hasOwnProperty.call(fields, key) &&
          Object.prototype.hasOwnProperty.call(fields[key], 'value'))) return false;
    const o = value as Record<string, unknown>;
    return isSafeEvidenceRef(o.attempt_id) && isSafeEvidenceRef(o.correlation_id) &&
      o.send_state === 'API_ACCEPTED' && o.api_accepted === true &&
      typeof o.http_status === 'number' && Number.isSafeInteger(o.http_status) &&
      o.http_status >= 200 && o.http_status < 300 &&
      isMetaWamid(o.provider_message_id) &&
      o.meta_error_code === null && o.meta_error_subcode === null &&
      o.retry_automatically === false;
  } catch {
    return false;
  }
}
