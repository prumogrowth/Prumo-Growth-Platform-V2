import { test } from 'node:test';
import assert from 'node:assert/strict';
import { FakeMetaStatusReconciler, type CorrelationReference } from './technical-reconciliation.ts';
import type { MetaIngressEvent } from './inbound.ts';
import type { GraphSendOutcome } from './graph-outbound.ts';

const reference: CorrelationReference = {
  app_ref: 'FIXTURE_APP_A', intent_id: 'FIXTURE_INTENT_A',
  recipient_verified: '5581900000000', scope: {
    concessionaria_id: 'FIXTURE_SHOP_A', canal_id: 'FIXTURE_CHANNEL_A',
    meta_app_ref: 'FIXTURE_APP_A', meta_waba_id: 'FIXTURE_WABA_A',
    phone_number_id: '123456789012',
  },
};
const accepted: GraphSendOutcome = {
  attempt_id: 'FIXTURE_ATTEMPT_A', correlation_id: 'FIXTURE_CORR_A',
  send_state: 'API_ACCEPTED', api_accepted: true, http_status: 200,
  provider_message_id: 'wamid.FIXTURE_A=', meta_error_code: null,
  meta_error_subcode: null, retry_automatically: false,
};
const callback = (provider_kind: string, at = '2026-10-18T13:00:01.000Z',
  changes: Partial<MetaIngressEvent> = {}): MetaIngressEvent => ({
  source: 'meta_whatsapp', event_kind: 'status_callback',
  waba_id: 'FIXTURE_WABA_A', phone_number_id: '123456789012',
  provider_message_id: 'wamid.FIXTURE_A=', participant_identifier: '5581900000000',
  provider_timestamp: at, provider_kind,
  position: { entry_index: 0, change_index: 0, array_kind: 'statuses', item_index: 0 }, ...changes,
});
const newLinked = () => {
  const x = new FakeMetaStatusReconciler();
  assert.equal(x.registerAcceptedSend(reference, accepted).decision, 'LINKED');
  return x;
};
const observe = (x: FakeMetaStatusReconciler, evt: MetaIngressEvent, app = reference.app_ref) =>
  x.observeAuthenticatedFixture(evt, app);

test('REC-01: accepted Graph response creates technical link, not delivered state', () => {
  const x = newLinked();
  assert.deepEqual(x.projectionFor(reference, accepted.provider_message_id!), {
    progress: 'NONE', failure_observed: false, observation_count: 0,
  });
});
test('REC-02: status sent correlates to the same scoped message', () => {
  const x = newLinked(); const r = observe(x, callback('sent'));
  assert.equal(r.decision, 'CORRELATED');
  assert.equal(r.progress, 'SENT'); assert.equal(r.observation_count, 1);
});
test('REC-03: delivered and read update technical projection only', () => {
  const x = newLinked(); observe(x, callback('sent'));
  observe(x, callback('delivered', '2026-10-18T13:00:02.000Z'));
  const r = observe(x, callback('read', '2026-10-18T13:00:03.000Z'));
  assert.equal(r.progress, 'READ'); assert.equal(r.observation_count, 3);
  assert.equal('vendido' in r, false); assert.equal('ciclo_comercial' in r, false);
});
test('REC-04: read before delivered/sent is never downgraded', () => {
  const x = newLinked(); observe(x, callback('read', '2026-10-18T13:00:03.000Z'));
  observe(x, callback('sent', '2026-10-18T13:00:01.000Z'));
  const r = observe(x, callback('delivered', '2026-10-18T13:00:02.000Z'));
  assert.equal(r.progress, 'READ'); assert.equal(r.observation_count, 3);
});
test('REC-05: failed callback is a separate technical observation', () => {
  const x = newLinked(); const r = observe(x, callback('failed'));
  assert.equal(r.progress, 'NONE'); assert.equal(r.failure_observed, true);
});
test('REC-06: failed after read never undoes read or implies commercial loss', () => {
  const x = newLinked(); observe(x, callback('read'));
  const r = observe(x, callback('failed', '2026-10-18T13:00:06.000Z'));
  assert.equal(r.progress, 'READ'); assert.equal(r.failure_observed, true);
  assert.equal('perdido' in r, false);
});
test('REC-07: repeated status observation is counted, NOT auto-deduped', () => {
  const x = newLinked(); observe(x, callback('delivered'));
  const r = observe(x, callback('delivered'));
  assert.equal(r.possible_repeat, true);
  assert.equal(r.observation_count, 2); assert.equal(r.progress, 'DELIVERED');
});
test('REC-08: same status but different second is a distinct observation', () => {
  const x = newLinked(); observe(x, callback('delivered'));
  const r = observe(x, callback('delivered', '2026-10-18T13:00:02.000Z'));
  assert.equal(r.possible_repeat, false); assert.equal(r.observation_count, 2);
});
test('REC-09: callback before Graph result stays pending and is later correlated', () => {
  const x = new FakeMetaStatusReconciler();
  assert.equal(observe(x, callback('read')).decision, 'PENDING_RECONCILIATION');
  assert.equal(x.pendingCount, 1);
  const link = x.registerAcceptedSend(reference, accepted);
  assert.equal(link.pending_correlated, 1); assert.equal(x.pendingCount, 0);
  assert.equal(x.projectionFor(reference, accepted.provider_message_id!)?.progress, 'READ');
});
test('REC-10: pending callback wrong recipient does not attach after send', () => {
  const x = new FakeMetaStatusReconciler();
  observe(x, callback('delivered', undefined, { participant_identifier: '558100000000' }));
  assert.equal(x.registerAcceptedSend(reference, accepted).pending_correlated, 0);
  assert.equal(x.pendingCount, 1);
  assert.equal(x.projectionFor(reference, accepted.provider_message_id!)?.progress, 'NONE');
});
test('REC-11: wrong App with same message ID never matches', () => {
  const x = newLinked(); const r = observe(x, callback('read'), 'FIXTURE_APP_B');
  assert.equal(r.decision, 'PENDING_RECONCILIATION');
  assert.equal(x.projectionFor(reference, accepted.provider_message_id!)?.progress, 'NONE');
});
test('REC-12: wrong WABA and sender cannot match even with same wamid', () => {
  const x = newLinked();
  for (const change of [ { waba_id: 'FIXTURE_WABA_B' },
    { phone_number_id: '999999999999' } ]) {
    const r = observe(x, callback('read', undefined, change));
    assert.equal(r.decision, 'PENDING_RECONCILIATION');
  }
  assert.equal(x.pendingCount, 2);
});
test('REC-13: exact same wamid can be independently linked to distinct App contexts', () => {
  const x = newLinked();
  const b: CorrelationReference = { ...reference,
    app_ref: 'FIXTURE_APP_B', intent_id: 'FIXTURE_INTENT_B',
    scope: { ...reference.scope, meta_app_ref: 'FIXTURE_APP_B',
      meta_waba_id: 'FIXTURE_WABA_B', phone_number_id: '999999999999' } };
  assert.equal(x.registerAcceptedSend(b, { ...accepted, attempt_id: 'FIXTURE_ATTEMPT_B' }).decision, 'LINKED');
  const r = observe(x, callback('read', undefined, {
    waba_id: 'FIXTURE_WABA_B', phone_number_id: '999999999999',
  }), 'FIXTURE_APP_B');
  assert.equal(r.decision, 'CORRELATED');
  assert.equal(x.projectionFor(reference, accepted.provider_message_id!)?.progress, 'NONE');
  assert.equal(x.projectionFor(b, accepted.provider_message_id!)?.progress, 'READ');
});
test('REC-14: malformed timestamp and unsupported statuses never update projection', () => {
  const x = newLinked();
  assert.equal(observe(x, callback('deleted')).reason, 'UNSUPPORTED_STATUS');
  assert.equal(observe(x, callback('read', '2026-13-99T13:00:01.000Z')).reason, 'INVALID_EVENT');
  assert.equal(x.projectionFor(reference, accepted.provider_message_id!)?.observation_count, 0);
});
test('REC-15: inbound message cannot be mistaken for a status callback', () => {
  const x = newLinked();
  assert.equal(observe(x, callback('read', undefined,
    { event_kind: 'inbound_message' })).reason, 'INVALID_EVENT');
});
test('REC-16: no Graph acceptance or wamid means no link, no recipient fallback', () => {
  const x = new FakeMetaStatusReconciler();
  for (const outcome of [
    { ...accepted, send_state: 'UNCERTAIN_EXTERNAL' as const, api_accepted: false },
    { ...accepted, send_state: 'PROVIDER_REJECTED' as const, api_accepted: false },
  ]) assert.equal(x.registerAcceptedSend(reference, outcome).decision, 'NOT_ACCEPTED');
  assert.equal(x.registerAcceptedSend(reference, { ...accepted, provider_message_id: null }).decision,
    'INVALID_REFERENCE');
  assert.equal(x.linkedCount, 0);
});
test('REC-17: same scoped wamid cannot be silently re-owned by different intent', () => {
  const x = newLinked();
  assert.equal(x.registerAcceptedSend(reference, accepted).decision, 'ALREADY_LINKED');
  assert.equal(x.registerAcceptedSend({ ...reference, intent_id: 'OTHER_INTENT' }, accepted).decision, 'CONFLICT');
  assert.equal(x.registerAcceptedSend(reference,
    { ...accepted, attempt_id: 'OTHER_ATTEMPT' }).decision, 'CONFLICT');
});
test('REC-18: reference app does not match S0-asserted scope; reject', () => {
  const x = new FakeMetaStatusReconciler();
  assert.equal(x.registerAcceptedSend({ ...reference, app_ref: 'FIXTURE_APP_B' }, accepted).decision,
    'INVALID_REFERENCE');
});
test('REC-19: no raw IDs, recipient, tokens, or message content in callback decision', () => {
  const x = newLinked(); const result = observe(x, callback('delivered'));
  const json = JSON.stringify(result);
  for (const secret of ['wamid.FIXTURE_A', '5581900000000', 'FIXTURE_APP_A', '123456789012',
    'FIXTURE_SHOP_A', 'Bearer', 'recipient_verified']) assert.equal(json.includes(secret), false);
  assert.equal(result.retry_automatically, false);
});
test('REC-20: projectionFor only exposes own exact-scope recipient', () => {
  const x = newLinked();
  assert.equal(x.projectionFor({ ...reference, recipient_verified: '558100000000' },
    accepted.provider_message_id!), undefined);
  assert.equal(x.projectionFor({ ...reference, app_ref: 'FIXTURE_APP_B' },
    accepted.provider_message_id!), undefined);
});
test('REC-21: unknown status before link is not fabricated as a delivery', () => {
  const x = new FakeMetaStatusReconciler();
  assert.equal(observe(x, callback('unknown')).decision, 'REJECTED_EVENT');
  assert.equal(x.pendingCount, 0);
});
test('REC-22: in-memory pending cap returns error; it is NOT an ACK', () => {
  const x = new FakeMetaStatusReconciler();
  for (let i = 0; i < 100; i++) {
    const r = observe(x, callback('sent', undefined, { provider_message_id: 'wamid.' + i }));
    assert.equal(r.decision, 'PENDING_RECONCILIATION');
  }
  const r = observe(x, callback('sent', undefined, { provider_message_id: 'wamid.overflow' }));
  assert.equal(r.decision, 'CAPACITY_REACHED'); assert.equal(x.pendingCount, 100);
  assert.equal('http_status' in r, false);
});
test('REC-23: per-message observation cap fails closed, no silent overwrites', () => {
  const x = newLinked();
  for (let i = 0; i < 100; i++) {
    assert.equal(observe(x, callback('sent')).decision, 'CORRELATED');
  }
  const r = observe(x, callback('delivered'));
  assert.equal(r.decision, 'CAPACITY_REACHED'); assert.equal(r.observation_count, 100);
});
test('REC-24: fixture is not a durable receipt, an ACK, or a commercial update', () => {
  const x = newLinked(); const status = observe(x, callback('read'));
  assert.equal('commit_state' in status, false);
  assert.equal('canal_id' in status, false);
  assert.equal('commercial_status' in status, false);
  assert.equal('http_status' in status, false);
});

 
// REC-25..32: strengthen the seam between an observed Graph response and an
// already authenticated, persistently accepted status. All tests are OFFLINE.
test('REC-25: forged Graph accepted flag with non-2xx HTTP cannot link', () => {
  const x = new FakeMetaStatusReconciler();
  for (const status of [null, 199, 302, 400, 500, Number.NaN]) {
    const result = x.registerAcceptedSend(reference, { ...accepted, http_status: status });
    assert.equal(result.decision, 'NOT_ACCEPTED');
  }
  assert.equal(x.linkedCount, 0);
});
test('REC-26: accepted Graph record requires canonical wamid, not arbitrary key', () => {
  const x = new FakeMetaStatusReconciler();
  for (const provider_message_id of ['OTHER', 'wamid.', 'wamid.A B', 'wamid.A\nB', 'wamid.A'.repeat(300)]) {
    assert.equal(x.registerAcceptedSend(reference, { ...accepted, provider_message_id }).decision,
      'INVALID_REFERENCE');
  }
  assert.equal(x.linkedCount, 0);
});
test('REC-27: technical link rejects forged automatic-retry or provider error flags', () => {
  const x = new FakeMetaStatusReconciler();
  const bads: GraphSendOutcome[] = [
    { ...accepted, retry_automatically: true as false },
    { ...accepted, meta_error_code: 100 },
    { ...accepted, meta_error_subcode: 33 },
  ];
  for (const bad of bads)
    assert.equal(x.registerAcceptedSend(reference, bad).decision, 'INVALID_REFERENCE');
  assert.equal(x.linkedCount, 0);
});
test('REC-28: status must include a statuses-array position with safe indices', () => {
  const x = newLinked();
  const base = callback('sent');
  for (const position of [
    { ...base.position, array_kind: 'messages' as const },
    { ...base.position, item_index: -1 },
    { ...base.position, entry_index: 1.5 },
    { ...base.position, change_index: Number.NaN },
    null,
  ]) {
    const r = observe(x, { ...base, position } as MetaIngressEvent);
    assert.equal(r.reason, 'INVALID_EVENT');
  }
  assert.equal(x.projectionFor(reference, accepted.provider_message_id!)?.observation_count, 0);
});
test('REC-29: malformed callback wamid cannot create pending or alter linked state', () => {
  const x = newLinked();
  for (const provider_message_id of ['OTHER', 'wamid.', 'wamid.A B', 'wamid.\n', 'wamid.A'.repeat(300)]) {
    const r = observe(x, callback('sent', undefined, { provider_message_id }));
    assert.equal(r.decision, 'REJECTED_EVENT');
    assert.equal(r.reason, 'INVALID_EVENT');
  }
  assert.equal(x.pendingCount, 0);
  assert.equal(x.projectionFor(reference, accepted.provider_message_id!)?.observation_count, 0);
});
test('REC-30: projection lookup refuses non-wamid keys even in trusted scope', () => {
  const x = newLinked();
  assert.equal(x.projectionFor(reference, 'FAKE_INTERNAL_KEY'), undefined);
});
test('REC-31: reject recipient scope with malformed numeric sender when linking', () => {
  const x = new FakeMetaStatusReconciler();
  const invalid = { ...reference, scope: { ...reference.scope, phone_number_id: 'CANAL_A' } };
  assert.equal(x.registerAcceptedSend(invalid, accepted).decision, 'INVALID_REFERENCE');
  assert.equal(x.linkedCount, 0);
});
test('REC-32: a valid scoped Graph acceptance still links and status progresses only technically', () => {
  const x = new FakeMetaStatusReconciler();
  assert.equal(x.registerAcceptedSend(reference, accepted).decision, 'LINKED');
  const r = observe(x, callback('sent'));
  assert.equal(r.decision, 'CORRELATED');
  assert.equal(r.progress, 'SENT');
  assert.equal(r.retry_automatically, false);
  assert.equal('commercial_status' in r, false);
  assert.equal('http_status' in r, false);
});
