/** Live PG17 WA38 aggregates -> real strict TypeScript classifier.
 * Read only; no authority, secrets, HMAC or service identity.
 */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {classifyWa38CallbackAggregate as classify}
 from '../wa38-callback-ambiguity-classifier.ts';
const expectations=new Map<string,string>([
 ['none','LAB_NO_EVIDENCE'],
 ['late','LAB_LATE_EVIDENCE_UNVERIFIED'],
 ['variant_hold','LAB_QUARANTINE_HOLD'],
 ['kind_conflict','LAB_QUARANTINE_HOLD'],
 ['active_b','LAB_OBSERVATION_UNVERIFIED'],
 ['other_tenant_hold','LAB_QUARANTINE_HOLD'],
 ['late_b','LAB_LATE_EVIDENCE_UNVERIFIED'],
]);
const content=readFileSync(0,'utf8');
assert.ok(content.length>250&&content.length<20000);
const rows=content.trim().split('\n');
assert.equal(rows.length,expectations.size);
for(const row of rows){
 const record=JSON.parse(row) as {label:string;snapshot:unknown};
 assert.deepEqual(Object.keys(record).sort(),['label','snapshot']);
 assert.equal(typeof record.label,'string');
 const expected=expectations.get(record.label);
 assert.ok(expected,'WA38 unexpected/duplicate PG17 test readback');
 const decision=classify(record.snapshot);
 assert.equal(decision.decision,expected,'WA38 unexpected '+record.label);
 for(const key of ['retry_external','send_authorized','ack_allowed',
 'production_authorized','delivery_confirmed',
 'definitive_failure_count_increment','case_transition_authorized'] as const)
  assert.equal(decision[key],false);
 expectations.delete(record.label);
}
assert.equal(expectations.size,0);
process.stdout.write('WA38-TSDB PASS: 7 physical PG17 aggregates deny all authority\n');
