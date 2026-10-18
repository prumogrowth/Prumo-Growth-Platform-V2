import { test } from 'node:test';
import assert from 'node:assert/strict';
import { technicalKeyHint } from './technical-keys.ts';
import type { MetaIngressEvent } from './inbound.ts';

const inbound: MetaIngressEvent = {
  source: 'meta_whatsapp', event_kind: 'inbound_message',
  waba_id: 'fixture_waba_A', phone_number_id: 'fixture_sender_A',
  provider_message_id: 'wamid.FIXTURE-1', provider_timestamp: '2026-10-17T00:00:00Z',
  participant_identifier: '5581900000000', provider_kind: 'text',
  position: { entry_index: 0, change_index: 0, array_kind: 'messages', item_index: 0 },
};
const status: MetaIngressEvent = {
  ...inbound, event_kind: 'status_callback', provider_kind: 'delivered',
};
const key = async (evt: MetaIngressEvent, app = 'trusted_app_A') =>
  (await technicalKeyHint(evt, app)).candidate_sha256;

test('WA-KEY-01: same message replay with 8↔9 variant has same candidate key', async () => {
  assert.equal(await key(inbound), await key({
    ...inbound, participant_identifier: '558100000000',
    provider_timestamp: '2026-10-18T00:00:00Z',
    position: { entry_index: 2, change_index: 3, array_kind: 'messages', item_index: 4 },
  }));
});
test('WA-KEY-02: two message IDs remain distinct even with equal text/phone', async () => {
  assert.notEqual(await key(inbound), await key({ ...inbound, provider_message_id: 'wamid.FIXTURE-2' }));
});
test('WA-KEY-03: two apps isolate the same external message ID', async () => {
  assert.notEqual(await key(inbound, 'trusted_app_A'), await key(inbound, 'trusted_app_B'));
});
test('WA-KEY-04: distinct WABAs and senders isolate messages', async () => {
  assert.notEqual(await key(inbound), await key({ ...inbound, waba_id: 'fixture_waba_B' }));
  assert.notEqual(await key(inbound), await key({ ...inbound, phone_number_id: 'fixture_sender_B' }));
});
test('WA-KEY-05: status messages correlate by ID but different states do not collapse', async () => {
  assert.notEqual(await key(status), await key({ ...status, provider_kind: 'read' }));
  assert.notEqual(await key(status), await key({ ...status, provider_kind: 'failed' }));
});
test('WA-KEY-06: same status at different timestamps remains a separate observation', async () => {
  assert.notEqual(await key(status), await key({ ...status, provider_timestamp: '2026-10-17T00:00:02Z' }));
});
test('WA-KEY-07: same status/id/time is only a hint, never an event ID', async () => {
  const hint = await technicalKeyHint(status, 'trusted_app_A');
  assert.equal(hint.candidate_sha256, await key({ ...status }));
  assert.equal(hint.interpretation, 'STATUS_OBSERVATION_HINT');
  assert.equal(hint.safe_to_auto_dedupe, false);
});
test('WA-KEY-08: inbound message identifier is candidate only, not authorization', async () => {
  const hint = await technicalKeyHint(inbound, 'trusted_app_A');
  assert.equal(hint.interpretation, 'INBOUND_MESSAGE_ID');
  assert.equal(hint.safe_to_auto_dedupe, false);
});
test('WA-KEY-09: no PII or provider IDs appear in hint', async () => {
  const hint = await technicalKeyHint(status, 'trusted_app_A');
  const exposed = JSON.stringify(hint);
  for (const secret of ['5581900000000', 'wamid.FIXTURE-1', 'trusted_app_A', 'fixture_waba_A']) {
    assert.equal(exposed.includes(secret), false);
  }
  assert.match(hint.candidate_sha256, /^[a-f0-9]{64}$/);
});
test('WA-KEY-10: domain or tenant IDs are never derived or returned', async () => {
  const hint = await technicalKeyHint(inbound, 'trusted_app_A');
  assert.equal('concessionaria_id' in hint, false);
  assert.equal('canal_id' in hint, false);
  assert.equal('lead_id' in hint, false);
});
test('WA-KEY-11: missing trusted app ref and malformed events fail closed', async () => {
  await assert.rejects(technicalKeyHint(inbound, ''), /Invalid trusted app reference/);
  await assert.rejects(technicalKeyHint({ ...inbound, provider_message_id: '' }, 'trusted_app_A'),
    /Invalid provider message ID/);
  await assert.rejects(technicalKeyHint({ ...status, provider_kind: '' }, 'trusted_app_A'),
    /Invalid status/);
});
test('WA-KEY-12: boundary-safe encoding prevents field concatenation ambiguity', async () => {
  assert.notEqual(await key({ ...inbound, waba_id: 'ab', phone_number_id: 'c' }),
    await key({ ...inbound, waba_id: 'a', phone_number_id: 'bc' }));
});
