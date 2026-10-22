/** WA30: PG17 fixtures -> real typed classifier; no API, credentials or ACK. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {classifyWa30RecoverySnapshot} from '../wa30-uncertain-dispatch-recovery.ts';
const expected=new Map<string,string>([
  ['unknown','LAB_HOLD_UNRESOLVED'],
  ['absent','LAB_ABSENT_STILL_UNCERTAIN'],
  ['accepted','LAB_ACCEPTED_NOT_SENT'],
  ['sent','LAB_SENT_REPORTED_UNVERIFIED'],
  ['failed','LAB_FAILURE_REPORTED_UNVERIFIED'],
  ['conflict','LAB_CONFLICT_QUARANTINE'],
  ['collision','LAB_CONFLICT_QUARANTINE'],
  ['invalidated','LAB_INVALIDATED_HOLD'],
  ['rolled_back','LAB_HOLD_UNRESOLVED'],
  ['other_shop','LAB_ACCEPTED_NOT_SENT'],
  ['race_invalidated','LAB_INVALIDATED_HOLD'],
]);
const content=readFileSync(0,'utf8');
assert.ok(content.length>100&&content.length<20000);
const rows=content.trim().split('\n');
assert.equal(rows.length,expected.size);
for(const line of rows){
  const root=JSON.parse(line) as {label?:unknown,snapshot?:unknown};
  assert.equal(Object.getPrototypeOf(root),Object.prototype);
  assert.deepEqual(Object.keys(root).sort(),['label','snapshot']);
  assert.equal(typeof root.label,'string');
  const decision=expected.get(root.label as string);
  assert.ok(decision,'unexpected or repeated WA30 PG17 case');
  const r=classifyWa30RecoverySnapshot(root.snapshot);
  assert.equal(r.decision,decision,'WA30 readback mismatch '+root.label);
  assert.equal(r.retry_external,false);
  assert.equal(r.send_authorized,false);
  assert.equal(r.ack_allowed,false);
  assert.equal(r.production_authorized,false);
  assert.equal(r.delivery_confirmed,false);
  assert.equal(r.definitive_failure_count_increment,false);
  assert.equal(r.case_transition_authorized,false);
  expected.delete(root.label as string);
}
assert.equal(expected.size,0);
process.stdout.write('WA30-TSDB PASS: 11 PG17 readbacks classified fail-closed\n');
