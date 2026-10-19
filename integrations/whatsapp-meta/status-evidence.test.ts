import test from 'node:test';
import assert from 'node:assert/strict';
import { isMetaWamid, isStatusPosition, isAcceptedGraphEvidence, isSafeEvidenceRef } from './status-evidence.ts';

const accepted = () => ({attempt_id:'FAKE_ATTEMPT', correlation_id:'FAKE_CORR',
  send_state:'API_ACCEPTED', api_accepted:true, http_status:200,
  provider_message_id:'wamid.FAKE_A=', meta_error_code:null,
  meta_error_subcode:null, retry_automatically:false});
const position = () => ({entry_index:0, change_index:0,
  array_kind:'statuses', item_index:0});

test('WA09-01: only canonical Meta wamid values pass', () => {
  assert.equal(isMetaWamid('wamid.FAKE_A='),true);
  for(const bad of ['wamid.', 'abc', 'wamid.x y', 'wamid.\n',
    'wamid.'+'a'.repeat(1025), null, 123, {}, ' wamid.A'])
    assert.equal(isMetaWamid(bad),false);
});
test('WA09-02: statuses position accepts zero and safe positive coordinates', () => {
  assert.equal(isStatusPosition(position()),true);
  assert.equal(isStatusPosition({...position(),entry_index:12,item_index:3}),true);
});
test('WA09-03: status positions reject messages, negatives, fractions, NaN and missing fields', () => {
  for(const bad of [{...position(),array_kind:'messages'},
    {...position(),entry_index:-1}, {...position(),item_index:0.25},
    {...position(),change_index:NaN}, {...position(),item_index:undefined},
    {entry_index:0,change_index:0,item_index:0}, null, []])
    assert.equal(isStatusPosition(bad),false);
});
test('WA09-04: status positions reject getters, inherited fields and unexpected keys', () => {
  const getter={...position()};
  Object.defineProperty(getter,'item_index',{get(){throw Error('unsafe getter');},enumerable:true});
  assert.equal(isStatusPosition(getter),false);
  assert.equal(isStatusPosition(Object.create(position())),false);
  assert.equal(isStatusPosition({...position(),raw_body:'NO'}),false);
});
test('WA09-05: coherent HTTP-accepted Graph result is only technical evidence', () => {
  assert.equal(isAcceptedGraphEvidence(accepted()),true);
  assert.equal('delivery_proven' in accepted(),false);
});
test('WA09-06: false 2xx and inconsistent statuses are refused', () => {
  for(const http_status of [null,199,300,400,500,NaN,200.5])
    assert.equal(isAcceptedGraphEvidence({...accepted(),http_status}),false);
  for(const value of [{...accepted(),send_state:'UNCERTAIN_EXTERNAL'},
    {...accepted(),api_accepted:false},{...accepted(),retry_automatically:true},
    {...accepted(),meta_error_code:131000}, {...accepted(),meta_error_subcode:1}])
    assert.equal(isAcceptedGraphEvidence(value),false);
});
test('WA09-07: evidence requires full data-only fields and no added data', () => {
  const missing=accepted() as Record<string,unknown>;
  delete missing.correlation_id;
  assert.equal(isAcceptedGraphEvidence(missing),false);
  assert.equal(isAcceptedGraphEvidence({...accepted(),access_token:'secret'}),false);
  const getter={...accepted()};
  Object.defineProperty(getter,'http_status',{get(){throw Error('unsafe getter');}});
  assert.equal(isAcceptedGraphEvidence(getter),false);
});
test('WA09-08: no body, tokens, phone or scope is emitted by predicate', () => {
  for(const result of [isMetaWamid('wamid.A'),isStatusPosition(position()),isAcceptedGraphEvidence(accepted())])
    assert.equal(typeof result,'boolean');
});

test('WA09-09: a 2xx Graph record without safe attempt/correlation IDs fails closed', () => {
  for (const field of ['attempt_id','correlation_id'] as const) {
    for (const malformed of [null,undefined,42,'','../leak','BAD ID','x'.repeat(129),'bad\nID']) {
      assert.equal(isAcceptedGraphEvidence({...accepted(),[field]:malformed}),false);
    }
  }
  assert.equal(isAcceptedGraphEvidence(accepted()),true);
});
test('WA09-10: pure correlation ref does not accept phone-bearing or control characters', () => {
  assert.equal(isSafeEvidenceRef('BATCH_42'),true);
  for(const malformed of ['',' x','BATCH\n42','id/1', 'a'.repeat(129),null,{}]) {
    assert.equal(isSafeEvidenceRef(malformed),false);
  }
});
