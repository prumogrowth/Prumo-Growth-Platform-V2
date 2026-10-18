import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classifyGraphSendResult, prepareGraphTextRequest, OutboundPreflightError,
  type GraphTextIntent } from './graph-outbound.ts';

const sample: GraphTextIntent = {
  contract_version: 'meta-s0.v0.1-proposed',
  intent_id: 'fixture-intent-1', attempt_id: 'fixture-attempt-1',
  correlation_id: 'fixture-correlation-1', authorized_business_action: 'C12',
  authorized_state_version: 42, phone_number_id: '12345678901',
  recipient_verified: '5581900000000', text_body: 'Mensagem de teste, sem cliente real',
};
const observe = (http_status: number, response_json: unknown) =>
  classifyGraphSendResult(sample.attempt_id, sample.correlation_id,
    { kind: 'http_response', http_status, response_json });

test('WA-OUT-01: builds only relative Graph POST with authorized text shape', () => {
  const req = prepareGraphTextRequest(sample, 'v24.0');
  assert.equal(req.relative_path, '/v24.0/12345678901/messages');
  assert.equal(req.method, 'POST');
  assert.deepEqual(req.body, {
    messaging_product: 'whatsapp', recipient_type: 'individual',
    to: '5581900000000', type: 'text',
    text: { preview_url: false, body: sample.text_body },
  });
  assert.equal('authorization' in req, false);
});
test('WA-OUT-02: IA C03 text allowed as inert preparation only', () => {
  assert.equal(prepareGraphTextRequest({ ...sample, authorized_business_action: 'C03' }, 'v24.0').body.type, 'text');
});
test('WA-OUT-03: templates C06 cannot masquerade as free text', () => {
  assert.throws(() => prepareGraphTextRequest({ ...sample, authorized_business_action: 'C06' }, 'v24.0'),
    (e: unknown) => e instanceof OutboundPreflightError && e.code === 'UNSUPPORTED_ACTION');
});
test('WA-OUT-04: refuses unknown authorization versions or opaque IDs', () => {
  for (const invalid of [{ ...sample, authorized_state_version: 0 },
    { ...sample, correlation_id: 'a/b' }, { ...sample, intent_id: '' },
    { ...sample, contract_version: 'invalid' as GraphTextIntent['contract_version'] }]) {
    assert.throws(() => prepareGraphTextRequest(invalid, 'v24.0'));
  }
  for (const version of ['', 'latest', '../v24.0', 'v24.0?fields=token']) {
    assert.throws(() => prepareGraphTextRequest(sample, version));
  }
});
test('WA-OUT-05: rejects unverified/malformed destinations rather than guessing BR variants', () => {
  for (const recipient of ['+5581900000000', '55 81 900000000', '0', '']) {
    assert.throws(() => prepareGraphTextRequest({ ...sample, recipient_verified: recipient }, 'v24.0'));
  }
  assert.equal(prepareGraphTextRequest({ ...sample, recipient_verified: '558100000000' }, 'v24.0')
    .body.to, '558100000000');
});
test('WA-OUT-06: rejects missing, blank, and oversized messages', () => {
  for (const content of ['', '   ', 'x'.repeat(4097)]) {
    assert.throws(() => prepareGraphTextRequest({ ...sample, text_body: content }, 'v24.0'));
  }
});
test('WA-OUT-07: provider wamid + HTTP 200 means accepted, not delivered', () => {
  const result = observe(200, { messaging_product: 'whatsapp',
    contacts: [{ input: 'fixture', wa_id: 'fixture' }],
    messages: [{ id: 'wamid.FIXTUREabc_123' }] });
  assert.deepEqual(result, {
    attempt_id: sample.attempt_id, correlation_id: sample.correlation_id,
    send_state: 'API_ACCEPTED', api_accepted: true, http_status: 200,
    provider_message_id: 'wamid.FIXTUREabc_123', meta_error_code: null,
    meta_error_subcode: null, retry_automatically: false,
  });
});
test('WA-OUT-08: malformed 2xx / missing wamid is UNCERTAIN, never delivered', () => {
  for (const body of [null, {}, { messages: [] }, { messages: [{ id: 'not-wamid' }] },
    { messages: [{ id: 'wamid.A' }, { id: 'wamid.B' }] }]) {
    assert.equal(observe(200, body).send_state, 'UNCERTAIN_EXTERNAL');
    assert.equal(observe(200, body).retry_automatically, false);
  }
});
test('WA-OUT-09: transport error after possible transmission is uncertain', () => {
  const result = classifyGraphSendResult(sample.attempt_id, sample.correlation_id,
    { kind: 'transport_error' });
  assert.equal(result.send_state, 'UNCERTAIN_EXTERNAL');
  assert.equal(result.http_status, null);
});
test('WA-OUT-10: HTTP 4xx explicit provider denial is not a retry command', () => {
  const result = observe(400, { error: { code: 131030, error_subcode: 123,
    message: 'PII must not appear in outcome', fbtrace_id: 'secret' } });
  assert.equal(result.send_state, 'PROVIDER_REJECTED');
  assert.equal(result.meta_error_code, 131030);
  assert.equal(result.meta_error_subcode, 123);
  assert.equal(JSON.stringify(result).includes('PII'), false);
  assert.equal(JSON.stringify(result).includes('secret'), false);
});
test('WA-OUT-11: rate-limit and provider 5xx are uncertain with no blind retry', () => {
  for (const status of [429, 500, 502, 503, 504]) {
    const result = observe(status, { error: { code: 131000, message: 'details' } });
    assert.equal(result.send_state, 'UNCERTAIN_EXTERNAL');
    assert.equal(result.retry_automatically, false);
  }
});
test('WA-OUT-12: 401 token failure rejected but token details never returned', () => {
  const result = observe(401, { error: { code: 190, message: 'Bearer SECRET' } });
  assert.equal(result.send_state, 'PROVIDER_REJECTED');
  assert.equal(result.meta_error_code, 190);
  assert.equal(JSON.stringify(result).includes('SECRET'), false);
});
test('WA-OUT-13: bad status or invalid provider error codes fail conservatively', () => {
  assert.equal(observe(0, null).send_state, 'UNCERTAIN_EXTERNAL');
  assert.equal(observe(399, null).send_state, 'UNCERTAIN_EXTERNAL');
  assert.equal(observe(400, { error: { code: '190', error_subcode: -1 } }).meta_error_code, null);
});
test('WA-OUT-14: attempt identifiers are validated without leaking input', () => {
  assert.throws(() => classifyGraphSendResult('ATTEMPT BAD', 'corr', { kind: 'transport_error' }));
});


test('WA-OUT-15: HTTP 408 and 425 remain uncertain, no automatic retry', () => {
  for (const status of [408, 425]) {
    const result = observe(status, { error: { code: 131000, message: 'possibly already accepted' } });
    assert.equal(result.send_state, 'UNCERTAIN_EXTERNAL');
    assert.equal(result.retry_automatically, false);
    assert.equal(result.api_accepted, false);
  }
});
test('WA-OUT-16: opaque Meta wamid accepts base64 padding without claiming delivery', () => {
  for (const id of ['wamid.HBgLMjM0NTY3ODkwPUI=', 'wamid.ABC+/=_-:def']) {
    const result = observe(200, { messages: [{ id }] });
    assert.equal(result.provider_message_id, id);
    assert.equal(result.send_state, 'API_ACCEPTED');
    assert.equal(result.retry_automatically, false);
  }
});
test('WA-OUT-17: malformed wamid with controls, spaces, or overlength is uncertain', () => {
  for (const id of ['wamid.x' + String.fromCharCode(10) + 'y', 'wamid.bad id',
    'wamid.A' + String.fromCharCode(10), 'wamid.A' + String.fromCharCode(13),
    'wamid.' + 'A'.repeat(1025)]) {
    const result = observe(200, { messages: [{ id }] });
    assert.equal(result.send_state, 'UNCERTAIN_EXTERNAL');
    assert.equal(result.provider_message_id, null);
  }
});
