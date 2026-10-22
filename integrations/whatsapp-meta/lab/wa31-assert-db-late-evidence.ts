/** WA31 PG17 snapshots -> actual TS classifier, no provider or auth claims. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {classifyWa31LateEvidence} from '../wa31-late-evidence-classifier.ts';

const expected=new Map<string,string>([
 ['empty','LAB_NO_OBSERVATIONS'],
 ['no_claim','LAB_ABSENT_OR_WRONG_SCOPE'],
 ['active','LAB_ACTIVE_EVIDENCE_UNVERIFIED'],
 ['historical','LAB_INVALIDATED_HISTORICAL_UNVERIFIED'],
 ['late','LAB_POST_REVOCATION_UNVERIFIED'],
 ['conflict','LAB_QUARANTINE_CONFLICT'],
 ['post_only','LAB_POST_REVOCATION_UNVERIFIED'],
 ['wrong_scope','LAB_ABSENT_OR_WRONG_SCOPE'],
 ['rolled_back','LAB_NO_OBSERVATIONS'],
 ['other_shop','LAB_ACTIVE_EVIDENCE_UNVERIFIED'],
 ['race_post','LAB_POST_REVOCATION_UNVERIFIED'],
 ['race_historical','LAB_INVALIDATED_HISTORICAL_UNVERIFIED'],
]);
const content=readFileSync(0,'utf8');
assert.ok(content.length>200&&content.length<20000);
const rows=content.trim().split('\n');
assert.equal(rows.length,expected.size);
for(const line of rows){
 const obj=JSON.parse(line) as {label:string;snapshot:unknown};
 assert.deepEqual(Object.keys(obj).sort(),['label','snapshot']);
 assert.equal(typeof obj.label,'string');
 const decision=expected.get(obj.label);
 assert.ok(decision,'unknown or duplicate WA31 snapshot');
 const actual=classifyWa31LateEvidence(obj.snapshot);
 assert.equal(actual.decision,decision,'WA31 unexpected recovery for '+obj.label);
 for(const key of ['retry_external','send_authorized','ack_allowed',
  'production_authorized','delivery_confirmed','definitive_failure_count_increment',
  'case_transition_authorized'] as const)assert.equal(actual[key],false);
 expected.delete(obj.label);
}
assert.equal(expected.size,0);
process.stdout.write('WA31-TSDB PASS: 12 PG17 readbacks classified fail-closed\n');
