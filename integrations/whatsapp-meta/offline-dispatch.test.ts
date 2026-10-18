import { test } from 'node:test';
import assert from 'node:assert/strict';
import { FakeS0Outbox, ScriptedFakeGraph, simulateOfflineDispatch,
  type OfflineCommand, type FakeS0Decision } from './offline-dispatch.ts';
import type { GraphTextIntent } from './graph-outbound.ts';
import type { TemplateIntent, TrustedTemplateScope, TrustedTemplateSnapshot } from './graph-template.ts';

const scope: TrustedTemplateScope = {
  concessionaria_id: 'fixture_shop_A', canal_id: 'fixture_channel_A',
  meta_app_ref: 'fixture_app_A', meta_waba_id: 'fixture_waba_A',
  phone_number_id: '123456789012',
};
const textIntent: GraphTextIntent = {
  contract_version: 'meta-s0.v0.1-proposed', intent_id: 'intent1',
  attempt_id: 'attempt1', correlation_id: 'corr1', authorized_business_action: 'C03',
  authorized_state_version: 5, phone_number_id: scope.phone_number_id,
  recipient_verified: '5581900000000', text_body: 'Mensagem FICTICIA',
};
const manifest: TrustedTemplateSnapshot = {
  template_name: 'exemplo_aprovado', language_code: 'pt_BR',
  template_revision_ref: 'fixture_revA', status: 'APPROVED',
  parameter_format: 'POSITIONAL_TEXT_ONLY', header_text_parameter_count: 0,
  body_text_parameter_count: 1, schema_complete: true,
  components: [{ type: 'BODY', format: 'TEXT', parameter_count: 1 }], ...scope,
};
const templateIntent: TemplateIntent = {
  ...textIntent, ...scope, authorized_business_action: 'C06',
  template_name: 'exemplo_aprovado', language_code: 'pt_BR',
  template_revision_ref: 'fixture_revA', body_text_parameters: ['Ficticio'],
};
const textCommand: OfflineCommand = { kind: 'text', intent: textIntent, asserted_scope: scope };
const templateCommand: OfflineCommand = { kind: 'template', intent: templateIntent, asserted_scope: scope };
const accepted = { kind: 'http_response' as const, http_status: 200,
  response_json: { messages: [{ id: 'wamid.SYNTHETIC=' }] } };
const current = (cmd: OfflineCommand = textCommand): FakeS0Decision => ({
  intent_id: cmd.intent.intent_id, attempt_id: cmd.intent.attempt_id,
  correlation_id: cmd.intent.correlation_id,
  authorized_business_action: cmd.intent.authorized_business_action,
  current_state_version: cmd.intent.authorized_state_version,
  scope, recipient_verified: cmd.intent.recipient_verified,
  allowed_now: true, ...(cmd.kind === 'template' ? { template_snapshot: manifest } : {}),
});
const fixture = (cmd: OfflineCommand = textCommand,
  observations = [accepted] as ConstructorParameters<typeof ScriptedFakeGraph>[0]) => {
  const s0 = new FakeS0Outbox();
  s0.upsertCurrent(current(cmd));
  const graph = new ScriptedFakeGraph(observations);
  return { s0, graph, run: () => simulateOfflineDispatch(cmd, s0, graph, 'v24.0') };
};

test('SIM-01: C03 text accepted only after simulated S0 revalidation', () => {
  const f = fixture(); const res = f.run();
  assert.equal(res.decision, 'SIMULATED');
  assert.equal(res.observation?.send_state, 'API_ACCEPTED');
  assert.equal(res.observation?.provider_message_id, 'wamid.SYNTHETIC=');
  assert.deepEqual(f.graph.kinds, ['text']);
  assert.equal(f.s0.recordedFor('intent1')?.api_accepted, true);
});
test('SIM-02: C12 human text uses same fake transport after independent check', () => {
  const cmd: OfflineCommand = { kind: 'text', asserted_scope: scope,
    intent: { ...textIntent, authorized_business_action: 'C12' } };
  const f = fixture(cmd); assert.equal(f.run().decision, 'SIMULATED');
  assert.deepEqual(f.graph.kinds, ['text']);
});
test('SIM-03: C06 passes approved current fixture catalog; only template is observed', () => {
  const f = fixture(templateCommand);
  assert.equal(f.run().observation?.send_state, 'API_ACCEPTED');
  assert.deepEqual(f.graph.kinds, ['template']);
});
test('SIM-04: revoked after intent creation blocks with zero fake calls', () => {
  const f = fixture(); f.s0.upsertCurrent({ ...current(), allowed_now: false });
  assert.equal(f.run().reason, 'S0_DENIED'); assert.equal(f.graph.calls, 0);
});
test('SIM-05: missing backend state blocks, not an authorization by claimed flags', () => {
  const fake = new FakeS0Outbox(); const graph = new ScriptedFakeGraph([accepted]);
  const r = simulateOfflineDispatch(textCommand, fake, graph, 'v24.0');
  assert.equal(r.reason, 'S0_DENIED'); assert.equal(graph.calls, 0);
});
test('SIM-06: changed authorization version blocks a stale queued intent', () => {
  const f = fixture(); f.s0.upsertCurrent({ ...current(), current_state_version: 6 });
  assert.equal(f.run().reason, 'STALE_INTENT'); assert.equal(f.graph.calls, 0);
});
test('SIM-07: changed action, attempt ID and correlation are rejected', () => {
  for (const change of [{ authorized_business_action: 'C12' as const },
    { attempt_id: 'anotherAttempt' }, { correlation_id: 'otherCorr' }]) {
    const f = fixture(); f.s0.upsertCurrent({ ...current(), ...change });
    assert.equal(f.run().reason, 'STALE_INTENT'); assert.equal(f.graph.calls, 0);
  }
});
test('SIM-08: cross-shop, app, WABA, channel or sender cannot pass', () => {
  for (const field of ['concessionaria_id', 'canal_id', 'meta_app_ref',
    'meta_waba_id', 'phone_number_id'] as const) {
    const f = fixture();
    f.s0.upsertCurrent({ ...current(), scope: { ...scope, [field]: 'otherTenant' } });
    assert.equal(f.run().reason, 'SCOPE_MISMATCH'); assert.equal(f.graph.calls, 0);
  }
});
test('SIM-09: changed recipient blocks instead of guessing 8↔9 variant', () => {
  const f = fixture(); f.s0.upsertCurrent({ ...current(), recipient_verified: '558100000000' });
  assert.equal(f.run().reason, 'SCOPE_MISMATCH'); assert.equal(f.graph.calls, 0);
});
test('SIM-10: asserted tenant scope must match trusted fake-S0 state', () => {
  const cmd: OfflineCommand = { ...textCommand,
    asserted_scope: { ...scope, concessionaria_id: 'fixture_shop_B' } };
  const f = fixture(cmd);
  assert.equal(f.run().reason, 'SCOPE_MISMATCH'); assert.equal(f.graph.calls, 0);
});
test('SIM-11: malformed Graph text is never reserved or observed', () => {
  const cmd: OfflineCommand = { kind: 'text', asserted_scope: scope,
    intent: { ...textIntent, text_body: '   ' } };
  const f = fixture(cmd);
  assert.equal(f.run().reason, 'INVALID_PREPARATION'); assert.equal(f.graph.calls, 0);
});
test('SIM-12: paused template cannot pass even if send flag true', () => {
  const f = fixture(templateCommand);
  f.s0.upsertCurrent({ ...current(templateCommand), template_snapshot: { ...manifest, status: 'PAUSED' } });
  assert.equal(f.run().reason, 'INVALID_PREPARATION'); assert.equal(f.graph.calls, 0);
});
test('SIM-13: template cross-shop/missing required components blocks', () => {
  for (const patch of [{ concessionaria_id: 'shop_B' },
    { components: [{ type: 'BUTTON', format: 'TEXT', parameter_count: 1 }] }]) {
    const f = fixture(templateCommand);
    f.s0.upsertCurrent({ ...current(templateCommand),
      template_snapshot: { ...manifest, ...patch } as TrustedTemplateSnapshot });
    assert.equal(f.run().reason, 'INVALID_PREPARATION'); assert.equal(f.graph.calls, 0);
  }
});
test('SIM-14: same S0 intent is not dispatched twice even after accepted Graph', () => {
  const f = fixture(); assert.equal(f.run().decision, 'SIMULATED');
  assert.equal(f.run().reason, 'ATTEMPT_ALREADY_RESERVED'); assert.equal(f.graph.calls, 1);
});
test('SIM-15: lost Graph connection creates UNCERTAIN_EXTERNAL, no retries', () => {
  const f = fixture(textCommand, [{ kind: 'transport_error' }]);
  const result = f.run();
  assert.equal(result.observation?.send_state, 'UNCERTAIN_EXTERNAL');
  assert.equal(result.observation?.retry_automatically, false);
  assert.equal(f.run().reason, 'ATTEMPT_ALREADY_RESERVED'); assert.equal(f.graph.calls, 1);
});
test('SIM-16: HTTP timeout/429/5xx stays uncertain without automatic replay', () => {
  for (const status of [408, 425, 429, 500, 503]) {
    const f = fixture(textCommand, [{ kind: 'http_response', http_status: status, response_json: {} }]);
    assert.equal(f.run().observation?.send_state, 'UNCERTAIN_EXTERNAL');
    assert.equal(f.graph.calls, 1);
  }
});
test('SIM-17: Graph 4xx rejection does not become success or auto retry', () => {
  const f = fixture(textCommand, [{ kind: 'http_response', http_status: 400,
    response_json: { error: { code: 131030, message: 'Sensitive material' } } }]);
  const result = f.run();
  assert.equal(result.observation?.send_state, 'PROVIDER_REJECTED');
  assert.equal(result.observation?.meta_error_code, 131030);
  assert.equal(JSON.stringify(result).includes('Sensitive'), false);
});
test('SIM-18: HTTP 200 without unambiguous wamid is uncertain', () => {
  const f = fixture(textCommand, [{ kind: 'http_response', http_status: 200,
    response_json: { messages: [] } }]);
  assert.equal(f.run().observation?.send_state, 'UNCERTAIN_EXTERNAL');
});
test('SIM-19: recording failure leaves reserved intent and requires manual reconciliation', () => {
  const f = fixture(); f.s0.failNextRecording = true;
  const result = f.run();
  assert.equal(result.decision, 'RECORD_UNCERTAIN');
  assert.equal(result.reason, 'RECORD_FAILURE');
  assert.equal(result.retry_automatically, false);
  assert.equal(f.s0.recordedFor('intent1'), undefined);
  assert.equal(f.run().reason, 'ATTEMPT_ALREADY_RESERVED');
  assert.equal(f.graph.calls, 1);
});
test('SIM-20: absent scripted HTTP result is modeled as uncertain transport', () => {
  const f = fixture(textCommand, []);
  assert.equal(f.run().observation?.send_state, 'UNCERTAIN_EXTERNAL');
});
test('SIM-21: invalid intent and invalid API version fail closed', () => {
  const f = fixture();
  const bad = { ...textCommand, intent: { ...textIntent, intent_id: 'x/secret' } };
  assert.equal(simulateOfflineDispatch(bad, f.s0, f.graph, 'v24.0').reason, 'INVALID_PREPARATION');
  assert.equal(simulateOfflineDispatch(textCommand, f.s0, f.graph, 'latest').reason, 'INVALID_PREPARATION');
  assert.equal(f.graph.calls, 0);
});
test('SIM-22: result never exposes recipient, text, template variables or Graph bearer tokens', () => {
  const f = fixture(); const result = f.run();
  const printable = JSON.stringify(result);
  for (const forbidden of ['5581900000000', 'Mensagem FICTICIA', 'Bearer',
    'fixture_app_A', 'fixture_shop_A', '123456789012']) {
    assert.equal(printable.includes(forbidden), false);
  }
  assert.equal('payload' in result, false);
});
test('SIM-23: record of simulation cannot be treated as durable S0 acknowledgment', () => {
  const f = fixture(); const r = f.run();
  assert.equal(r.decision, 'SIMULATED');
  assert.equal('commit_state' in r, false);
  assert.equal('s0_receipt' in r, false);
});
