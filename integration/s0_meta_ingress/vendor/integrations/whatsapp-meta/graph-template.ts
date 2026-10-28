/**
 * WA-02B: inert WhatsApp Cloud API TEMPLATE request preparation.
 * No transport, credentials, authorization checks, opt-in decisions or real sends.
 * Only approved-catalog POSITIONAL TEXT (optional text header) fixtures supported.
 */

export type TemplateIntent = {
  contract_version: 'meta-s0.v0.1-proposed';
  intent_id: string;
  attempt_id: string;
  correlation_id: string;
  authorized_business_action: 'C06';
  authorized_state_version: number;
  /** Claimed business context, MUST match the separate verified scope. */
  concessionaria_id: string;
  canal_id: string;
  meta_app_ref: string;
  meta_waba_id: string;
  phone_number_id: string;
  recipient_verified: string;
  template_name: string;
  language_code: string;
  template_revision_ref: string;
  header_text_parameter?: string;
  body_text_parameters?: readonly string[];
};

/**
 * A snapshot supplied ONLY by a future trusted, scoped S0 catalog service.
 * This is NOT evidence of current approval merely because status says APPROVED.
 */
export type TrustedTemplateSnapshot = {
  template_name: string;
  language_code: string;
  template_revision_ref: string;
  status: 'APPROVED' | 'PENDING' | 'PAUSED' | 'REJECTED' | 'DISABLED';
  parameter_format: 'POSITIONAL_TEXT_ONLY';
  header_text_parameter_count: 0 | 1;
  body_text_parameter_count: number;
  /** Full current Meta catalog schema, issued by trusted backend. */
  schema_complete: true;
  components: readonly {
    type: 'HEADER' | 'BODY' | 'FOOTER';
    format: 'TEXT';
    parameter_count: number;
  }[];
  /** Binding must match the authenticated dispatch scope. */
  concessionaria_id: string;
  canal_id: string;
  meta_app_ref: string;
  meta_waba_id: string;
  phone_number_id: string;
};

/** Provided only by a verified S0 service, never by the caller's JSON. */
export type TrustedTemplateScope = {
  concessionaria_id: string;
  canal_id: string;
  meta_app_ref: string;
  meta_waba_id: string;
  phone_number_id: string;
};

type TextParameter = { type: 'text'; text: string };
type TextHeader = { type: 'header'; parameters: [TextParameter] };
type TextBody = { type: 'body'; parameters: TextParameter[] };

export type GraphTemplateRequest = {
  method: 'POST';
  relative_path: string;
  content_type: 'application/json';
  body: {
    messaging_product: 'whatsapp';
    recipient_type: 'individual';
    to: string;
    type: 'template';
    template: {
      name: string;
      language: { code: string };
      components?: (TextHeader | TextBody)[];
    };
  };
};

export class TemplatePreflightError extends Error {
  readonly code: 'INVALID_INTENT' | 'INVALID_DESTINATION' | 'INVALID_TEMPLATE' |
    'TEMPLATE_NOT_APPROVED' | 'TEMPLATE_REVISION_MISMATCH' |
    'UNSUPPORTED_COMPONENTS' | 'INVALID_PARAMETERS' | 'SCOPE_MISMATCH';
  constructor(code: TemplatePreflightError['code']) {
    super(code);
    this.code = code;
    this.name = 'TemplatePreflightError';
  }
}

const ref = (v: unknown): v is string =>
  typeof v === 'string' && v.length > 0 && v.length <= 128 && /^[A-Za-z0-9_.:-]+$/.test(v);
const name = (v: unknown): v is string =>
  typeof v === 'string' && /^[a-z][a-z0-9_]{0,127}$/.test(v);
const locale = (v: unknown): v is string =>
  typeof v === 'string' && /^[a-z]{2,3}(?:_[A-Z]{2})?$/.test(v);
const textParameter = (v: unknown, max: number): v is string =>
  typeof v === 'string' && v.trim().length > 0 &&
  [...v].length <= max && !/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/.test(v) &&
  // Reject malformed UTF-16; UTF-8 serializers may silently replace it.
  !/(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]|[\uD800-\uDBFF](?![\uDC00-\uDFFF])/.test(v);

/**
 * Creates an inert relative request description, NEVER a send authorization.
 * The caller must obtain and verify a fresh template status, current customer
 * eligibility/opt-in, window, handoff and intent version in the trusted S0
 * backend immediately before any real HTTP dispatch. A stale APPROVED snapshot
 * or any caller-provided 'authorized' field is insufficient.
 *
 * The output contains a real recipient and interpolated text and is sensitive:
 * do not log/trace/store this structure without the approved protections.
 */
export function prepareGraphTemplateRequest(
  intent: TemplateIntent,
  trustedSnapshot: TrustedTemplateSnapshot,
  trustedScope: TrustedTemplateScope,
  apiVersion: string,
): GraphTemplateRequest {
  if (!intent || intent.contract_version !== 'meta-s0.v0.1-proposed' ||
      intent.authorized_business_action !== 'C06' ||
      !ref(intent.intent_id) || !ref(intent.attempt_id) || !ref(intent.correlation_id) ||
      !Number.isSafeInteger(intent.authorized_state_version) || intent.authorized_state_version <= 0 ||
      !/^v\d{1,2}\.\d{1,2}$/.test(apiVersion)) {
    throw new TemplatePreflightError('INVALID_INTENT');
  }
  if (typeof intent.phone_number_id !== 'string' || !/^\d{5,25}$/.test(intent.phone_number_id) ||
      typeof intent.recipient_verified !== 'string' || !/^\d{8,15}$/.test(intent.recipient_verified)) {
    throw new TemplatePreflightError('INVALID_DESTINATION');
  }
  if (!name(intent.template_name) || !locale(intent.language_code) ||
      !ref(intent.template_revision_ref)) {
    throw new TemplatePreflightError('INVALID_TEMPLATE');
  }
  // Runtime boundary: a snapshot with unknown fields (e.g. required_buttons)
  // or without a complete component manifest is NOT supported.
  if (!trustedSnapshot || trustedSnapshot.status !== 'APPROVED') {
    throw new TemplatePreflightError('TEMPLATE_NOT_APPROVED');
  }
  if (trustedSnapshot.template_name !== intent.template_name ||
      trustedSnapshot.language_code !== intent.language_code ||
      trustedSnapshot.template_revision_ref !== intent.template_revision_ref) {
    throw new TemplatePreflightError('TEMPLATE_REVISION_MISMATCH');
  }
  const scopeFields = ['concessionaria_id', 'canal_id', 'meta_app_ref', 'meta_waba_id', 'phone_number_id'] as const;
  if (!trustedScope || !scopeFields.every(key =>
    ref(trustedScope[key]) && ref(trustedSnapshot[key]) && ref(intent[key]) &&
    trustedScope[key] === trustedSnapshot[key] && trustedScope[key] === intent[key])) {
    throw new TemplatePreflightError('SCOPE_MISMATCH');
  }
  const knownKeys = new Set([
    'template_name', 'language_code', 'template_revision_ref', 'status',
    'parameter_format', 'header_text_parameter_count', 'body_text_parameter_count',
    'schema_complete', 'components', ...scopeFields,
  ]);
  if (Object.keys(trustedSnapshot).some(key => !knownKeys.has(key)) ||
      trustedSnapshot.schema_complete !== true ||
      trustedSnapshot.parameter_format !== 'POSITIONAL_TEXT_ONLY' ||
      ![0, 1].includes(trustedSnapshot.header_text_parameter_count) ||
      !Number.isSafeInteger(trustedSnapshot.body_text_parameter_count) ||
      trustedSnapshot.body_text_parameter_count < 0 ||
      trustedSnapshot.body_text_parameter_count > 10 ||
      !Array.isArray(trustedSnapshot.components) ||
      trustedSnapshot.components.length === 0 || trustedSnapshot.components.length > 3) {
    throw new TemplatePreflightError('UNSUPPORTED_COMPONENTS');
  }
  const kinds = new Set<string>();
  for (const component of trustedSnapshot.components) {
    if (!component || typeof component !== 'object' ||
        Object.keys(component).some(key => !['type','format','parameter_count'].includes(key)) ||
        !['HEADER','BODY','FOOTER'].includes(component.type) ||
        component.format !== 'TEXT' ||
        !Number.isSafeInteger(component.parameter_count) || component.parameter_count < 0 ||
        kinds.has(component.type)) {
      throw new TemplatePreflightError('UNSUPPORTED_COMPONENTS');
    }
    kinds.add(component.type);
    if (component.type === 'HEADER' && component.parameter_count !== trustedSnapshot.header_text_parameter_count ||
        component.type === 'BODY' && component.parameter_count !== trustedSnapshot.body_text_parameter_count ||
        component.type === 'FOOTER' && component.parameter_count !== 0) {
      throw new TemplatePreflightError('UNSUPPORTED_COMPONENTS');
    }
  }
  if (!kinds.has('BODY') || (!kinds.has('HEADER') && trustedSnapshot.header_text_parameter_count !== 0)) {
    throw new TemplatePreflightError('UNSUPPORTED_COMPONENTS');
  }
  const bodyParams = intent.body_text_parameters ?? [];
  if (!Array.isArray(bodyParams) ||
      bodyParams.length !== trustedSnapshot.body_text_parameter_count ||
      bodyParams.some(p => !textParameter(p, 1024)) ||
      (trustedSnapshot.header_text_parameter_count === 1
        ? !textParameter(intent.header_text_parameter, 60)
        : intent.header_text_parameter !== undefined)) {
    throw new TemplatePreflightError('INVALID_PARAMETERS');
  }
  const components: (TextHeader | TextBody)[] = [];
  if (trustedSnapshot.header_text_parameter_count === 1) {
    components.push({ type: 'header', parameters: [
      { type: 'text', text: intent.header_text_parameter! },
    ] });
  }
  if (bodyParams.length) {
    components.push({ type: 'body', parameters: bodyParams.map(text => ({ type: 'text', text })) });
  }
  return {
    method: 'POST', relative_path: '/' + apiVersion + '/' + intent.phone_number_id + '/messages',
    content_type: 'application/json',
    body: {
      messaging_product: 'whatsapp', recipient_type: 'individual',
      to: intent.recipient_verified, type: 'template',
      template: {
        name: intent.template_name, language: { code: intent.language_code },
        ...(components.length ? { components } : {}),
      },
    },
  };
}
