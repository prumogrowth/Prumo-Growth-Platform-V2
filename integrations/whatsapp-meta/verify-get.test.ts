import { test } from 'node:test';
import assert from 'node:assert/strict';
import { inspectMetaVerifyGet } from './verify-get.ts';

const secretA = 'FIXTURE_GET_TOKEN_FOR_APP_A_ONLY';
const secretB = 'FIXTURE_GET_TOKEN_FOR_APP_B_ONLY';
const query = (token = secretA, challenge = '0012034', mode = 'subscribe') =>
  new URLSearchParams({ 'hub.mode': mode, 'hub.verify_token': token, 'hub.challenge': challenge }).toString();

test('WA-GET-01 valid per-app token echoes exact numeric challenge', async () => {
  assert.deepEqual(await inspectMetaVerifyGet(query(), secretA), {
    status: 200, body: '0012034', headers: {
      'content-type': 'text/plain; charset=utf-8', 'cache-control': 'no-store',
    },
  });
});
test('WA-GET-02 mismatched app token never verifies', async () => {
  const result = await inspectMetaVerifyGet(query(secretA), secretB);
  assert.equal(result.status, 403);
  assert.equal(result.body, '');
});
test('WA-GET-03 mismatched arbitrary token rejects', async () => {
  assert.equal((await inspectMetaVerifyGet(query('not-secret-a'), secretA)).status, 403);
});
test('WA-GET-04 mode must be subscribe', async () => {
  assert.equal((await inspectMetaVerifyGet(query(secretA, '1', 'unsubscribe'), secretA)).status, 403);
});
test('WA-GET-05 required query fields cannot be omitted', async () => {
  for (const missing of ['hub.mode', 'hub.verify_token', 'hub.challenge']) {
    const p = new URLSearchParams(query());
    p.delete(missing);
    assert.equal((await inspectMetaVerifyGet(p.toString(), secretA)).status, 403);
  }
});
test('WA-GET-06 duplicate query parameters cannot override token/mode/challenge', async () => {
  for (const repeated of ['hub.mode', 'hub.verify_token', 'hub.challenge']) {
    const p = new URLSearchParams(query());
    p.append(repeated, p.get(repeated)!);
    assert.equal((await inspectMetaVerifyGet(p.toString(), secretA)).status, 403);
  }
});
test('WA-GET-07 unexpected query parameters reject', async () => {
  const p = new URLSearchParams(query());
  p.append('concessionaria_id', 'fixture-other-tenant');
  assert.equal((await inspectMetaVerifyGet(p.toString(), secretA)).status, 403);
});
test('WA-GET-08 malformed challenge rejected with no secret reflection', async () => {
  for (const bad of ['', '12x', '-12', '<script>', '1'.repeat(33)]) {
    const answer = await inspectMetaVerifyGet(query(secretA, bad), secretA);
    assert.equal(answer.status, 403);
    assert.equal(answer.body.includes(secretA), false);
    assert.equal(answer.body, '');
  }
});
test('WA-GET-09 valid URL encoded verify token is compared after decoding', async () => {
  const token = 'FIXTURE_token+with/=?:&';
  const result = await inspectMetaVerifyGet('?' + query(token, '42'), token);
  assert.equal(result.status, 200);
  assert.equal(result.body, '42');
});
test('WA-GET-10 query limit prevents oversized inputs', async () => {
  assert.equal((await inspectMetaVerifyGet(query() + '&x=' + 'A'.repeat(9000), secretA)).status, 403);
});
test('WA-GET-11 reject fragments and empty query', async () => {
  assert.equal((await inspectMetaVerifyGet(query() + '#fragment', secretA)).status, 403);
  assert.equal((await inspectMetaVerifyGet('', secretA)).status, 403);
});
test('WA-GET-12 missing trusted configuration fails closed without disclosing secrets', async () => {
  await assert.rejects(inspectMetaVerifyGet(query(), ''), /not configured/);
  await assert.rejects(inspectMetaVerifyGet(query(), 'X'.repeat(1025)), /not configured/);
});
