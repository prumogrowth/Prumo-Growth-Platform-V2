import { test } from 'node:test';
import assert from 'node:assert/strict';
import { inspectMetaWebhook, type InspectionResult } from './inbound.ts';

const secret = 'SYNTHETIC_TEST_SECRET_NOT_REAL';
const enc = new TextEncoder();
const inbound = (id: string, from = '5581900000000') => ({
  id, from, timestamp: '1792270000', type: 'text', text: { body: 'FIXTURE_ONLY' },
});
const status = (id: string, state = 'delivered') => ({
  id, recipient_id: '5581900000000', timestamp: '1792270001', status: state,
});
const change = (messages?: unknown[], statuses?: unknown[]) => ({
  field: 'messages', value: { metadata: { phone_number_id: 'fixture_sender' }, messages, statuses },
});
const payload = (changes: unknown[] = [change([inbound('wamid.fixture')])]) => ({
  object: 'whatsapp_business_account',
  entry: [{ id: 'fixture_waba', changes }],
});
async function signed(raw: Uint8Array, key = secret): Promise<string> {
  const hmacKey = await crypto.subtle.importKey('raw', enc.encode(key),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const digest = new Uint8Array(await crypto.subtle.sign('HMAC', hmacKey, raw));
  return `sha256=${Array.from(digest, b => b.toString(16).padStart(2, '0')).join('')}`;
}
async function inspect(obj: unknown, opts?: { maxEvents?: number; maxBodyBytes?: number }): Promise<InspectionResult> {
  const bytes = enc.encode(JSON.stringify(obj));
  return inspectMetaWebhook(bytes, await signed(bytes), secret, opts);
}
function failure(result: InspectionResult) {
  if ('failure' in result) return result.failure;
  throw new Error('Expected a failed inspection');
}

test('IN-01: validates HMAC over exactly the received raw bytes', async () => {
  const bytes = enc.encode(JSON.stringify(payload()));
  const sig = await signed(bytes);
  const ok = await inspectMetaWebhook(bytes, sig, secret);
  assert.equal(ok.ok, true);
  const altered = enc.encode(`${new TextDecoder().decode(bytes)} `);
  const bad = await inspectMetaWebhook(altered, sig, secret);
  assert.deepEqual(bad, { ok: false, failure: { code: 'INVALID_SIGNATURE' } });
});

test('IN-01: missing, malformed, wrong-app and invalid signatures reject', async () => {
  const bytes = enc.encode(JSON.stringify(payload()));
  assert.equal((await inspectMetaWebhook(bytes, null, secret)).ok, false);
  assert.deepEqual(failure(await inspectMetaWebhook(bytes, 'sha1=wrong', secret)),
    { code: 'INVALID_SIGNATURE_FORMAT' });
  assert.deepEqual(failure(await inspectMetaWebhook(bytes, await signed(bytes, 'another_app'), secret)),
    { code: 'INVALID_SIGNATURE' });
  assert.deepEqual(failure(await inspectMetaWebhook(bytes, `sha256=${'0'.repeat(64)}`, secret)),
    { code: 'INVALID_SIGNATURE' });
});

test('IN-02: extracts two inbound and two callbacks from one signed HTTP POST', async () => {
  const result = await inspect(payload([
    change([inbound('wamid.a'), inbound('wamid.b', '558100000000')], [status('wamid.out1')]),
    change(undefined, [status('wamid.out2', 'read')]),
  ]));
  assert.equal(result.ok, true);
  if (!result.ok) return;
  assert.deepEqual(result.events.map(e => e.event_kind),
    ['inbound_message', 'inbound_message', 'status_callback', 'status_callback']);
  assert.deepEqual(result.events.map(e => e.position), [
    { entry_index: 0, change_index: 0, item_index: 0 },
    { entry_index: 0, change_index: 0, item_index: 1 },
    { entry_index: 0, change_index: 0, item_index: 0 },
    { entry_index: 0, change_index: 1, item_index: 0 },
  ]);
  assert.equal(result.events[0].phone_number_id, 'fixture_sender');
  assert.equal(result.events[1].participant_identifier, '558100000000');
  assert.equal('concessionaria_id' in result.events[0], false);
  assert.equal('canal_id' in result.events[0], false);
});

test('IN-02B: handles multiple entry[] without silently using only the first', async () => {
  const document = payload();
  document.entry.push({ id: 'fixture_second_waba', changes: [change(undefined, [status('wamid.other')])] });
  const result = await inspect(document);
  assert.equal(result.ok, true);
  if (result.ok) {
    assert.equal(result.events.length, 2);
    assert.equal(result.events[1].waba_id, 'fixture_second_waba');
  }
});

test('CB-01: preserves callbacks with the same message id as separate events', async () => {
  const result = await inspect(payload([change(undefined,
    [status('wamid.same', 'sent'), status('wamid.same', 'delivered'), status('wamid.same', 'read')])]));
  assert.equal(result.ok, true);
  if (result.ok) {
    assert.equal(result.events.length, 3);
    assert.deepEqual(result.events.map(e => e.provider_kind), ['sent', 'delivered', 'read']);
    assert.equal('callback_event_id' in result.events[0], false);
  }
});

test('SEC: invalid event inside aggregate fails whole inspection, no partial result', async () => {
  const result = await inspect(payload([change([inbound('wamid.ok'), { from: '5581900000000' }])]));
  assert.deepEqual(result, { ok: false, failure: {
    code: 'INVALID_MESSAGE', position: { entry_index: 0, change_index: 0, item_index: 1 },
  } });
});

test('SEC: unsupported changes are not silently discarded', async () => {
  const result = await inspect(payload([{ field: 'other', value: { something: 'fixture' } }]));
  assert.deepEqual(result, { ok: false, failure: {
    code: 'UNSUPPORTED_CHANGE_FIELD', position: { entry_index: 0, change_index: 0 },
  } });
});

test('SEC: invalid envelope/metadata/relevant arrays reject', async () => {
  assert.deepEqual(failure(await inspect({ object: 'other', entry: [] })), { code: 'INVALID_ENVELOPE' });
  assert.equal(failure(await inspect(payload([{ field: 'messages', value: { messages: [] } }]))).code,
    'INVALID_CHANGE');
  assert.equal(failure(await inspect(payload([change([], [])]))).code, 'INVALID_CHANGE');
  assert.equal(failure(await inspect(payload([{ field: 'messages', value: {
    metadata: { phone_number_id: 'fixture_sender' }, messages: 'wrong',
  } }]))).code, 'INVALID_CHANGE');
});

test('SEC: body and event caps reject before output; failure does not reveal PII', async () => {
  const raw = enc.encode(JSON.stringify(payload()));
  assert.deepEqual(await inspectMetaWebhook(raw, await signed(raw), secret, { maxBodyBytes: raw.length - 1 }),
    { ok: false, failure: { code: 'BODY_TOO_LARGE' } });
  const result = await inspect(payload([change([inbound('wamid.a'), inbound('wamid.b')])]), { maxEvents: 1 });
  assert.equal(failure(result).code, 'TOO_MANY_EVENTS');
  assert.equal(JSON.stringify(result).includes('5581900000000'), false);
});

test('SEC: invalid UTF-8 and malformed JSON reject only after valid signatures', async () => {
  const nonUtf8 = new Uint8Array([0xff, 0xfe]);
  assert.deepEqual(failure(await inspectMetaWebhook(nonUtf8, await signed(nonUtf8), secret)),
    { code: 'INVALID_UTF8' });
  const malformed = enc.encode('{not json}');
  assert.deepEqual(failure(await inspectMetaWebhook(malformed, await signed(malformed), secret)),
    { code: 'INVALID_JSON' });
});

test('SEC: configuration errors fail closed', async () => {
  const raw = enc.encode('{}');
  await assert.rejects(inspectMetaWebhook(raw, null, ''), /not configured/);
  await assert.rejects(inspectMetaWebhook(raw, null, secret, { maxEvents: 0 }), RangeError);
});
