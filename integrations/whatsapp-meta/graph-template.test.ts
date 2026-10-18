import { test } from 'node:test';
import assert from 'node:assert/strict';
import { prepareGraphTemplateRequest, TemplatePreflightError,
  type TemplateIntent, type TrustedTemplateSnapshot, type TrustedTemplateScope } from './graph-template.ts';

const scope: TrustedTemplateScope = {
  concessionaria_id: 'fixture_shop_A', canal_id: 'fixture_channel_A',
  meta_app_ref: 'fixture_app_A', meta_waba_id: 'fixture_waba_A',
  phone_number_id: '123456789012',
};
const intent: TemplateIntent = {
  contract_version: 'meta-s0.v0.1-proposed', intent_id: 'fixture-intent1',
  attempt_id: 'fixture-attempt1', correlation_id: 'fixture-corr1',
  authorized_business_action: 'C06', authorized_state_version: 42,
  ...scope, phone_number_id: '123456789012', recipient_verified: '5581900000000',
  template_name: 'pedido_confirmado', language_code: 'pt_BR',
  template_revision_ref: 'fixture-rev1', body_text_parameters: ['Pessoa Fictícia', '1234'],
};
const catalog: TrustedTemplateSnapshot = {
  template_name: 'pedido_confirmado', language_code: 'pt_BR',
  template_revision_ref: 'fixture-rev1', status: 'APPROVED',
  parameter_format: 'POSITIONAL_TEXT_ONLY', header_text_parameter_count: 0,
  body_text_parameter_count: 2,
  ...scope, schema_complete: true,
  components: [{ type: 'BODY', format: 'TEXT', parameter_count: 2 }],
};
const run = (i: TemplateIntent = intent, c: TrustedTemplateSnapshot = catalog,
  trusted: TrustedTemplateScope = scope) =>
  prepareGraphTemplateRequest(i, c, trusted, 'v24.0');
const code = (fn: () => unknown, expected: string) =>
  assert.throws(fn, (e: unknown) => e instanceof TemplatePreflightError && e.code === expected);

test('WA-TPL-01: C06 template body with two ordered text substitutions', () => {
  const req = run();
  assert.equal(req.method, 'POST');
  assert.equal(req.relative_path, '/v24.0/123456789012/messages');
  assert.deepEqual(req.body, {
    messaging_product: 'whatsapp', recipient_type: 'individual',
    to: '5581900000000', type: 'template', template: {
      name: 'pedido_confirmado', language: { code: 'pt_BR' }, components: [{
        type: 'body', parameters: [{ type: 'text', text: 'Pessoa Fictícia' },
          { type: 'text', text: '1234' }],
      }],
    },
  });
  assert.equal('authorization' in req, false);
});
test('WA-TPL-02: zero placeholders omit components', () => {
  const req = run({ ...intent, body_text_parameters: undefined },
    { ...catalog, body_text_parameter_count: 0, components: [{ type: 'BODY', format: 'TEXT', parameter_count: 0 }] });
  assert.equal('components' in req.body.template, false);
});
test('WA-TPL-03: text header + body components preserve order', () => {
  const req = run({ ...intent, header_text_parameter: 'Título Fictício' },
    { ...catalog, header_text_parameter_count: 1, components: [
      { type: 'HEADER', format: 'TEXT', parameter_count: 1 },
      { type: 'BODY', format: 'TEXT', parameter_count: 2 },
    ] });
  assert.deepEqual(req.body.template.components?.map(x => x.type), ['header', 'body']);
  assert.deepEqual(req.body.template.components?.[0], {
    type: 'header', parameters: [{ type: 'text', text: 'Título Fictício' }],
  });
});
test('WA-TPL-04: non-C06 intent rejected', () => {
  for (const action of ['C03', 'C12', 'SYSTEM', ''] as const) {
    code(() => run({ ...intent, authorized_business_action: action as TemplateIntent['authorized_business_action'] }), 'INVALID_INTENT');
  }
});
test('WA-TPL-05: missing/unsafe identifiers and state version rejected', () => {
  for (const invalid of [
    { ...intent, intent_id: '../tenant' },
    { ...intent, attempt_id: '' },
    { ...intent, correlation_id: 'a/b' },
    { ...intent, authorized_state_version: 0 },
    { ...intent, authorized_state_version: 1.5 },
  ]) code(() => run(invalid), 'INVALID_INTENT');
});
test('WA-TPL-06: invalid relative API versions rejected', () => {
  for (const version of ['latest', 'v24.0?token=1', '/v24.0', 'v1.0/messages']) {
    code(() => prepareGraphTemplateRequest(intent, catalog, scope, version), 'INVALID_INTENT');
  }
});
test('WA-TPL-07: sender and destination cannot be URLs, +phones or aliases inferred', () => {
  for (const number of ['+5581900000000', '55 81 900000000', 'https://example.test', '']) {
    code(() => run({ ...intent, recipient_verified: number }), 'INVALID_DESTINATION');
  }
  code(() => run({ ...intent, phone_number_id: '../other-sender' }), 'INVALID_DESTINATION');
  assert.equal(run({ ...intent, recipient_verified: '558100000000' }).body.to, '558100000000');
});
test('WA-TPL-08: rejects unapproved, pending and paused templates', () => {
  for (const status of ['PENDING', 'PAUSED', 'REJECTED', 'DISABLED'] as const) {
    code(() => run(intent, { ...catalog, status }), 'TEMPLATE_NOT_APPROVED');
  }
});
test('WA-TPL-09: template name/language/revision must match trusted record', () => {
  for (const changes of [
    { template_name: 'outro_nome' }, { language_code: 'en_US' },
    { template_revision_ref: 'fixture-rev2' },
  ]) code(() => run({ ...intent, ...changes }), 'TEMPLATE_REVISION_MISMATCH');
});
test('WA-TPL-10: rejects unsafe names and locales', () => {
  for (const invalid of [
    { ...intent, template_name: '../pedido' },
    { ...intent, template_name: 'Pedido Validado' },
    { ...intent, language_code: 'pt-BR' },
    { ...intent, language_code: 'x'.repeat(300) },
    { ...intent, template_revision_ref: '' },
  ]) code(() => run(invalid), 'INVALID_TEMPLATE');
});
test('WA-TPL-11: exact positional counts are required', () => {
  for (const values of [[], ['só um'], ['a', 'b', 'c']]) {
    code(() => run({ ...intent, body_text_parameters: values }), 'INVALID_PARAMETERS');
  }
});
test('WA-TPL-12: reject malformed or control-containing body text', () => {
  for (const values of [['', 'x'], ['   ', 'x'], ['A\u0000B', 'x'], ['x'.repeat(1025), 'y'], [42, 'x']]) {
    code(() => run({ ...intent, body_text_parameters: values as string[] }), 'INVALID_PARAMETERS');
  }
});
test('WA-TPL-13: no invented header value, no header when not in catalog', () => {
  code(() => run({ ...intent, header_text_parameter: 'extra' }), 'INVALID_PARAMETERS');
  code(() => run(intent, { ...catalog, header_text_parameter_count: 1, components: [
       { type: 'HEADER', format: 'TEXT', parameter_count: 1 },
       { type: 'BODY', format: 'TEXT', parameter_count: 2 },
     ] }), 'INVALID_PARAMETERS');
  code(() => run({ ...intent, header_text_parameter: 'x'.repeat(61) },
    { ...catalog, header_text_parameter_count: 1, components: [
       { type: 'HEADER', format: 'TEXT', parameter_count: 1 },
       { type: 'BODY', format: 'TEXT', parameter_count: 2 },
     ] }), 'INVALID_PARAMETERS');
});
test('WA-TPL-14: media/named/buttons unsupported until explicitly implemented', () => {
  code(() => run(intent, { ...catalog, parameter_format: 'NAMED' as TrustedTemplateSnapshot['parameter_format'] }), 'UNSUPPORTED_COMPONENTS');
  code(() => run(intent, { ...catalog, body_text_parameter_count: 11 }), 'UNSUPPORTED_COMPONENTS');
  code(() => run(intent, { ...catalog, header_text_parameter_count: 2 as 0 | 1 }), 'UNSUPPORTED_COMPONENTS');
});
test('WA-TPL-15: no template components are taken from caller-provided arbitrary keys', () => {
  const evil = { ...intent, components: [{ type: 'button', parameters: [{ type: 'payload', payload: 'UNSAFE' }] }] };
  const result = run(evil);
  assert.equal(JSON.stringify(result).includes('UNSAFE'), false);
  assert.equal(JSON.stringify(result).includes('button'), false);
});
test('WA-TPL-16: result has no access token, template catalog or credentials', () => {
  const result = run();
  const representation = JSON.stringify(result);
  for (const forbidden of ['access_token', 'app_secret', 'authorization', 'fixture-rev1']) {
    assert.equal(representation.includes(forbidden), false);
  }
});
test('WA-TPL-17: status alone does not provide proof of current commercial consent', () => {
  const result = run();
  assert.equal('opt_in' in result, false);
  assert.equal('authorized' in result, false);
  assert.equal('business_state' in result, false);
});
test('WA-TPL-18: rejects null catalog/intent and malformed parameter arrays safely', () => {
  code(() => run(null as unknown as TemplateIntent), 'INVALID_INTENT');
  code(() => run(intent, null as unknown as TrustedTemplateSnapshot), 'TEMPLATE_NOT_APPROVED');
  code(() => run({ ...intent, body_text_parameters: 'hello' as unknown as string[] }), 'INVALID_PARAMETERS');
});

test('WA-TPL-19: scope mismatches across intent, catalog and trusted dispatch fail closed', () => {
  for (const key of ['concessionaria_id','canal_id','meta_app_ref','meta_waba_id','phone_number_id'] as const) {
    const other = key === 'phone_number_id' ? '999999999999' : 'other_tenant';
    code(() => run({ ...intent, [key]: other }), 'SCOPE_MISMATCH');
    code(() => run(intent, { ...catalog, [key]: other }), 'SCOPE_MISMATCH');
    code(() => run(intent, catalog, { ...scope, [key]: other }), 'SCOPE_MISMATCH');
  }
  code(() => run(intent, catalog, null as unknown as TrustedTemplateScope), 'SCOPE_MISMATCH');
});
test('WA-TPL-20: missing/incomplete descriptor cannot authorize template shape', () => {
  for (const invalid of [
    { ...catalog, schema_complete: false as true },
    { ...catalog, components: undefined as unknown as TrustedTemplateSnapshot['components'] },
    { ...catalog, components: [] },
    { ...catalog, components: [{ type: 'HEADER' as const, format: 'TEXT' as const, parameter_count: 0 }] },
  ]) code(() => run(intent, invalid), 'UNSUPPORTED_COMPONENTS');
});
test('WA-TPL-21: other required components are never silently discarded', () => {
  const withButton = { ...catalog, components: [
    ...catalog.components,
    { type: 'BUTTON', format: 'TEXT', parameter_count: 1 },
  ] as unknown as TrustedTemplateSnapshot['components'] };
  code(() => run(intent, withButton), 'UNSUPPORTED_COMPONENTS');
  code(() => run(intent, { ...catalog, required_buttons: [{ type: 'url' }] } as TrustedTemplateSnapshot), 'UNSUPPORTED_COMPONENTS');
  code(() => run(intent, { ...catalog, components: [
    { type: 'HEADER', format: 'IMAGE', parameter_count: 0 },
    ...catalog.components,
  ] as unknown as TrustedTemplateSnapshot['components'] }), 'UNSUPPORTED_COMPONENTS');
});
test('WA-TPL-22: component counts, duplicates and unsupported keys reject', () => {
  code(() => run(intent, { ...catalog, components: [
    { type: 'BODY', format: 'TEXT', parameter_count: 1 },
  ] }), 'UNSUPPORTED_COMPONENTS');
  code(() => run(intent, { ...catalog, components: [
    { type: 'BODY', format: 'TEXT', parameter_count: 2 },
    { type: 'BODY', format: 'TEXT', parameter_count: 2 },
  ] }), 'UNSUPPORTED_COMPONENTS');
  code(() => run(intent, { ...catalog, components: [
    { type: 'BODY', format: 'TEXT', parameter_count: 2, required_buttons: 1 },
  ] }), 'UNSUPPORTED_COMPONENTS');
});
test('WA-TPL-23: static text footer is representable without extra outbound data', () => {
  const req = run(intent, { ...catalog, components: [
    { type: 'BODY', format: 'TEXT', parameter_count: 2 },
    { type: 'FOOTER', format: 'TEXT', parameter_count: 0 },
  ] });
  assert.deepEqual(req.body.template.components?.map(x => x.type), ['body']);
  code(() => run(intent, { ...catalog, components: [
    { type: 'BODY', format: 'TEXT', parameter_count: 2 },
    { type: 'FOOTER', format: 'TEXT', parameter_count: 1 },
  ] }), 'UNSUPPORTED_COMPONENTS');
});
test('WA-TPL-24: invalid UTF-16 never leaks into provider message', () => {
  for (const invalid of ['\uD800','\uDC00','prefix\uD800suffix']) {
    code(() => run({ ...intent, body_text_parameters: [invalid,'okay'] }), 'INVALID_PARAMETERS');
  }
  assert.equal(run({ ...intent, body_text_parameters: ['✨','ok'] }).body.type, 'template');
});
