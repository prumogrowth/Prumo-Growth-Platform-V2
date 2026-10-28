import test from 'node:test';
import assert from 'node:assert/strict';
import {setup,reservation,http,begun} from './fixtures.mjs';
import {FLAGS,VERSION,signFixture} from './protocol.mjs';
import {CandidateLab} from './candidate.mjs';
import {planLocks,assertAcquisitionOrder} from './lock-plan.mjs';

const invariants=r=>{
  for(const k of Object.keys(FLAGS))assert.equal(r[k],false,k);
};
const observe=(h,attempt_ref,wire,observation_ref='obs_A')=>
  h.call('observe',{attempt_ref,observation_ref,wire});

test('requires an explicit disposable laboratory opt-in',()=>{
  assert.throws(()=>new CandidateLab({}),/LAB_OPT_IN_REQUIRED/);
});
test('GoTrue-shaped identity is not M2M and writes no nonce',async()=>{
  const h=setup(),p=h.packet('reserve',reservation());
  const r=await h.lab.call(p.bytes,{kind:'Bearer',key_id:'dispatch',mac_sha256:'human.jwt.token'});
  assert.equal(r.code,'M2M_DENIED');assert.deepEqual(h.store.state.nonces,{});invariants(r);
});
test('wrong MAC, issuer, audience, principal kind and expired key are denied',async()=>{
  for(const mutation of [
    s=>s.keys.dispatch.issuer='someone_else',s=>s.keys.dispatch.audience='GoTrue',
    s=>s.keys.dispatch.kind='HUMAN',s=>s.keys.dispatch.not_after_ms=10000,
  ]) {
    const h=setup();mutation(h.store.state);
    assert.equal((await h.call('reserve',reservation())).code,'M2M_DENIED');
    assert.equal(Object.keys(h.store.state.attempts).length,0);
  }
  const h=setup(),p=h.packet('reserve',reservation());
  p.proof.mac_sha256='0'.repeat(64);
  assert.equal((await h.lab.call(p.bytes,p.proof)).code,'M2M_DENIED');
});
test('M2M operation ACL prevents ingress from dispatch and dispatcher from review',async()=>{
  const h=setup();
  assert.equal((await h.call('reserve',reservation(),'ingress')).code,'M2M_DENIED');
  assert.equal((await h.call('review',{},'dispatch')).code,'M2M_DENIED');
});
test('expired, future, overlong TTL and noninteger clock envelopes fail closed',async()=>{
  for(const extra of [{issued_at_ms:9000,expires_at_ms:10000},
    {issued_at_ms:10001,expires_at_ms:11000},{expires_at_ms:50000}]) {
    const h=setup(),r=await h.call('reserve',reservation(),'dispatch',extra);
    assert.ok(['M2M_DENIED','INPUT_REJECTED'].includes(r.code));
  }
  const h=setup();h.setNow(NaN);
  assert.equal((await h.call('reserve',reservation())).code,'INPUT_REJECTED');
});
test('canonical internal JSON rejects duplicates, escaped names, BOM and extras',async()=>{
  const h=setup(),p=h.packet('reserve',reservation());
  const text=p.bytes.toString();
  for(const raw of [
    text.replace('"version":','"version":"bad","version":'),
    text.replace('"version"','"\\u0076ersion"'),'\ufeff'+text,text+' ',
    text.replace('"body":','"identity":"admin","body":'),
  ])assert.equal((await h.lab.call(Buffer.from(raw),p.proof)).code,'INPUT_REJECTED');
});
test('unknown body authority and invalid int64 preconditions roll back nonce/audit',async()=>{
  for(const extra of [{send_authorized:true},{expected_revision:1},
    {expected_revision:'01'},{expected_revision:'9223372036854775808'}]) {
    const h=setup(),r=await h.call('reserve',reservation(extra));
    assert.equal(r.code,'INPUT_REJECTED');
    assert.equal(Object.keys(h.store.state.nonces).length,0);
    assert.equal(h.store.state.audit.length,0);
  }
});
test('tenant, channel and technical route are selected from server-side M2M ACL',async()=>{
  const h=setup();
  assert.equal((await h.call('reserve',reservation(),'other')).code,'SCOPE_DENIED');
  assert.equal((await h.call('reserve',reservation({intent_ref:'intent_B'}))).code,'SCOPE_DENIED');
  assert.equal(Object.keys(h.store.state.attempts).length,0);
});
test('reserve atomically creates attempt, idempotency record, nonce and audit',async()=>{
  const h=setup(),r=await h.call('reserve',reservation());invariants(r);
  assert.equal(r.code,'LAB_RESERVED_NO_SEND_RIGHTS');
  assert.equal(h.store.state.attempts[r.attempt_ref].phase,'RESERVED');
  assert.equal(Object.keys(h.store.state.idempotency).length,1);
  assert.equal(Object.keys(h.store.state.nonces).length,1);
  assert.equal(h.store.state.audit.length,1);
});
test('20 concurrent reservations produce one attempt and no new execution on replay',async()=>{
  const h=setup(),rs=await Promise.all(Array.from({length:20},()=>h.call('reserve',reservation())));
  assert.equal(rs.filter(r=>r.code==='LAB_RESERVED_NO_SEND_RIGHTS').length,1);
  assert.equal(new Set(rs.map(r=>r.attempt_ref)).size,1);
  assert.equal(Object.keys(h.store.state.attempts).length,1);
});
test('same idempotency key with changed intent conflicts; a fresh key does not bypass occupancy',async()=>{
  const h=setup();await h.call('reserve',reservation());
  assert.equal((await h.call('reserve',reservation({intent_ref:'intent_A2'}))).code,'IDEMPOTENCY_CONFLICT');
  assert.equal((await h.call('reserve',reservation({idempotency_key:'another'}))).code,'INTENT_OCCUPIED_NO_RETRY');
});
test('M2M nonce replay and divergent reuse never execute twice',async()=>{
  const h=setup(),p=h.packet('reserve',reservation());
  const rs=await Promise.all([h.lab.call(p.bytes,p.proof),h.lab.call(p.bytes,p.proof)]);
  assert.equal(rs.filter(r=>r.code==='LAB_RESERVED_NO_SEND_RIGHTS').length,1);
  assert.equal(rs.filter(r=>r.code==='NONCE_REPLAY_NO_EXECUTION').length,1);
  const payload=JSON.parse(p.bytes);payload.body.idempotency_key='other';
  const p2=signFixture('dispatch',h.secrets.dispatch,payload);
  assert.equal((await h.lab.call(p2.bytes,p2.proof)).code,'NONCE_CONFLICT');
  assert.equal(h.store.state.audit.length,1);
});
test('rollback on persistence failure leaves no attempt, nonce or audit',async()=>{
  const h=setup({hook:async phase=>{if(phase==='before_commit')throw Error('INJECTED');}});
  assert.equal((await h.call('reserve',reservation())).code,'COMMIT_OR_RESULT_UNKNOWN');
  assert.equal(Object.keys(h.store.state.attempts).length,0);
  assert.equal(Object.keys(h.store.state.nonces).length,0);assert.equal(h.store.state.audit.length,0);
});
test('lost result after commit does not open a second reservation',async()=>{
  let fail=true;
  const h=setup({hook:async phase=>{if(phase==='after_commit'&&fail){fail=false;throw Error('LOST');}}});
  assert.equal((await h.call('reserve',reservation())).code,'COMMIT_OR_RESULT_UNKNOWN');
  assert.equal((await h.call('reserve',reservation())).code,'ALREADY_RESERVED_NO_EXECUTION');
  assert.equal(Object.keys(h.store.state.attempts).length,1);
});
test('one begin winner and no reusable permission after concurrent begin/restart',async()=>{
  const h=setup(),r=await h.call('reserve',reservation());
  const rs=await Promise.all(Array.from({length:10},()=>h.call('begin',
    {attempt_ref:r.attempt_ref,expected_revision:'1'})));
  assert.equal(rs.filter(x=>x.code==='LAB_BEGIN_RECORDED_NO_SEND_RIGHTS').length,1);
  assert.equal(rs.filter(x=>x.code==='BEGIN_ALREADY_CONSUMED_NO_RETRY').length,9);
  const r2=await h.call('reserve',reservation());invariants(r2);
  assert.equal(r2.code,'ALREADY_RESERVED_NO_EXECUTION');
});
test('stale revision and each existing authority gate refuse reservation',async()=>{
  const h=setup();
  assert.equal((await h.call('reserve',reservation({expected_revision:'2'}))).code,'STALE_REVISION');
  for(const gate of Object.keys(h.seed.authorities.intent_A.gates)){
    const x=setup();x.store.state.authorities.intent_A.gates[gate]=false;
    assert.equal((await x.call('reserve',reservation())).code,'AUTHORITY_REVOKED',gate);
  }
});
test('S0/S1/cancel/opt-out before begin prevent execution and keep tombstone',async()=>{
  for(const kind of ['S0','S1','CANCEL','OPT_OUT']) {
    const h=setup(),r=await h.call('reserve',reservation());
    await h.lab.revokeFixture(kind,'intent_A');
    assert.equal((await h.call('begin',{attempt_ref:r.attempt_ref,expected_revision:'1'})).code,'AUTHORITY_REVOKED');
    assert.equal(h.store.state.attempts[r.attempt_ref].phase,'CANCELLED');
    assert.equal(Object.keys(h.store.state.attempts).length,1);
  }
});
test('both modeled begin/revocation orderings preserve uncertainty and never reopen',async()=>{
  for(const first of ['begin','revoke']){
    const h=setup(),r=await h.call('reserve',reservation());
    const begin=()=>h.call('begin',{attempt_ref:r.attempt_ref,expected_revision:'1'});
    const revoke=()=>h.lab.revokeFixture('S1','intent_A');
    const rs=first==='begin'?await Promise.all([begin(),revoke()]):await Promise.all([revoke(),begin()]);
    const b=first==='begin'?rs[0]:rs[1];
    assert.equal(b.code,first==='begin'?'LAB_BEGIN_RECORDED_NO_SEND_RIGHTS':'AUTHORITY_REVOKED');
    const a=h.store.state.attempts[r.attempt_ref];
    assert.equal(a.cancelled,true);
    assert.equal(a.phase,first==='begin'?'EXTERNAL_UNCERTAIN':'CANCELLED');
    assert.equal((await h.call('reserve',reservation())).code,'AUTHORITY_REVOKED');
  }
});
test('key and route revocation deny authenticated packets queued for later',async()=>{
  for(const [kind,ref] of [['KEY','dispatch'],['ROUTE','route_A']]) {
    const h=setup(),p=h.packet('reserve',reservation());
    await h.lab.revokeFixture(kind,ref);
    const r=await h.lab.call(p.bytes,p.proof);
    assert.ok(['M2M_DENIED','TECHNICAL_BINDING_REVOKED'].includes(r.code));
  }
});
test('observation requires previous begin and correct tenant/attempt binding',async()=>{
  const h=setup(),r=await h.call('reserve',reservation());
  assert.equal((await observe(h,r.attempt_ref,http(200))).code,'EXTERNAL_BEGIN_REQUIRED');
  assert.equal((await h.call('observe',{attempt_ref:r.attempt_ref,observation_ref:'obs_A',
    wire:http(200)},'other')).code,'SCOPE_DENIED');
});
test('reuse existing Cloud classifier for timeout, 429, 503 and malformed 2xx without retry',async()=>{
  for(const wire of [{kind:'transport_error'},http(429,{}, {'retry-after':'12'}),
    http(503,{}),http(200,{}),{kind:'not_attempted'}]) {
    const h=setup(),ref=await begun(h),r=await observe(h,ref,wire);
    assert.equal(r.state,'EXTERNAL_UNCERTAIN');invariants(r);
    assert.equal((await h.call('begin',{attempt_ref:ref,expected_revision:'1'})).code,'BEGIN_ALREADY_CONSUMED_NO_RETRY');
  }
});
test('API acceptance is technical evidence and never delivered or a cadence failure',async()=>{
  const h=setup(),ref=await begun(h),r=await observe(h,ref,http(200));
  assert.equal(r.state,'API_ACCEPTED_NOT_DELIVERED');invariants(r);
  assert.equal(h.store.state.attempts[ref].evidence[0].provider_message_id,'wamid.SYNTHETIC_A');
});
test('explicit rejection stays occupied and never creates an automatic retry',async()=>{
  const h=setup(),ref=await begun(h),r=await observe(h,ref,http(400,{error:{code:100}}));
  assert.equal(r.state,'PROVIDER_REJECTED_NO_RETRY');invariants(r);
  assert.equal((await h.call('reserve',reservation({idempotency_key:'fresh'}))).code,'INTENT_OCCUPIED_NO_RETRY');
});
test('uncertainty followed by late acceptance refines readback without another begin',async()=>{
  const h=setup(),ref=await begun(h);
  await observe(h,ref,{kind:'transport_error'},'unknown');
  await observe(h,ref,http(200),'accepted');
  const r=await h.call('read',{attempt_ref:ref});
  assert.equal(r.state,'API_ACCEPTED_NOT_DELIVERED');assert.equal(r.evidence_count,2);invariants(r);
});
test('same observation replay is idempotent and a variant under that ref quarantines',async()=>{
  const h=setup(),ref=await begun(h);
  await observe(h,ref,http(200));
  assert.equal((await observe(h,ref,http(200))).code,'OBSERVATION_REPLAY_NO_RETRY');
  assert.equal((await observe(h,ref,http(400))).code,'EVIDENCE_CONFLICT_QUARANTINED');
  assert.equal((await h.call('read',{attempt_ref:ref})).state,'QUARANTINED_REVIEW');
  assert.equal(h.store.state.attempts[ref].evidence.length,1);
});
test('incompatible wamids or accepted/rejected evidence across refs quarantines',async()=>{
  for(const wire of [http(200,{messages:[{id:'wamid.SYNTHETIC_B'}]}),http(400)]){
    const h=setup(),ref=await begun(h);await observe(h,ref,http(200),'one');
    assert.equal((await observe(h,ref,wire,'two')).code,'EVIDENCE_CONFLICT_QUARANTINED');
  }
});
test('late evidence survives human S1 revocation, cancellation and opt-out without reopening',async()=>{
  for(const kind of ['S0','S1','CANCEL','OPT_OUT']){
    const h=setup(),ref=await begun(h);await h.lab.revokeFixture(kind,'intent_A');
    const r=await observe(h,ref,http(200));
    assert.equal(r.state,'API_ACCEPTED_NOT_DELIVERED');invariants(r);
    assert.equal((await h.call('read',{attempt_ref:ref})).cancelled,true);
    assert.equal((await h.call('begin',{attempt_ref:ref,expected_revision:'2'})).code,'AUTHORITY_REVOKED');
  }
});
test('authorized reconciliation is annotation only, references evidence, never releases',async()=>{
  const h=setup(),ref=await begun(h);await observe(h,ref,{kind:'transport_error'});
  const r=await h.call('review',{attempt_ref:ref,decision_ref:'decision_A',
    evidence_refs:['obs_A']},'reviewer');
  assert.equal(r.code,'REVIEW_ANNOTATED_NO_RELEASE');invariants(r);
  const read=await h.call('read',{attempt_ref:ref});assert.equal(read.state,'EXTERNAL_UNCERTAIN');
  assert.equal(read.review_count,1);
  assert.equal((await h.call('reserve',reservation({idempotency_key:'review_bypass'}))).code,'INTENT_OCCUPIED_NO_RETRY');
});
test('response and audit exclude raw response text and provider secrets',async()=>{
  const h=setup(),ref=await begun(h);
  const r=await observe(h,ref,http(400,{error:{code:100,message:'SYNTHETIC_SECRET_DO_NOT_RETURN'}}));
  assert.ok(!JSON.stringify([r,h.store.state.audit,h.store.state.attempts]).includes('SYNTHETIC_SECRET'));
  invariants(r);
});
test('in-memory receipt never claims durable ACK; every item retains position',async()=>{
  const h=setup(),r=await h.call('append_batch',h.batch(),'ingress');
  assert.equal(r.lab_receipt_committed,true);assert.equal(r.lab_ack_ready,false);
  assert.deepEqual(r.items,[{index:0,state:'ARCHIVED_UNVERIFIED'},{index:1,state:'ARCHIVED_UNVERIFIED'}]);invariants(r);
  const receipt=Object.values(h.store.state.batches)[0];
  assert.equal(receipt.observations[1].observation.position.item_index,1);
});
test('raw batch replay with new nonce and alias reuses full receipt',async()=>{
  const h=setup(),b=h.batch(),first=await h.call('append_batch',b,'ingress');
  for(const next of [b,{...b,batch_ref:'batch_alias'}]){
    const r=await h.call('append_batch',next,'ingress');
    assert.equal(r.code,'BATCH_ALREADY_DURABLE_CANDIDATE');
    assert.equal(r.receipt_ref,first.receipt_ref);
  }
  assert.equal(Object.keys(h.store.state.raw_receipts).length,1);
});
test('same batch id with different raw bytes refuses ACK, variants with new id are preserved',async()=>{
  const h=setup(),r=await h.call('append_batch',h.batch(),'ingress');
  assert.equal((await h.call('append_batch',h.batch(['read'],{variant:true}),'ingress')).code,
    'BATCH_IDEMPOTENCY_CONFLICT_NO_ACK');
  const r2=await h.call('append_batch',h.batch(['read'],{variant:true,batch_ref:'variant'}),'ingress');
  assert.notEqual(r2.receipt_ref,r.receipt_ref);
  assert.equal(Object.keys(h.store.state.raw_receipts).length,2);
});
test('invalid Meta signature, mixed scope or one invalid item reject whole batch',async()=>{
  for(const b of [h=>({...h.batch(),meta_signature:'sha256='+'0'.repeat(64)}),
    h=>h.batch(['sent'],{waba:'100002'}),h=>h.batch(['sent','unsupported'])]){
    const h=setup(),r=await h.call('append_batch',b(h),'ingress');
    assert.equal(r.code,'META_BATCH_DENIED');assert.equal(r.lab_ack_ready,false);
    assert.equal(Object.keys(h.store.state.batches).length,0);
  }
});
test('stale route, wrong M2M route and revoked ingress cannot archive or ACK',async()=>{
  const h=setup();
  assert.equal((await h.call('append_batch',h.batch(['sent'],{route_revision:'2'}),'ingress')).code,'STALE_ROUTE');
  assert.equal((await h.call('append_batch',h.batch(),'other')).code,'META_BATCH_DENIED');
  await h.lab.revokeFixture('KEY','ingress');
  assert.equal((await h.call('append_batch',h.batch(),'ingress')).code,'M2M_DENIED');
});
test('S1 revocation does not erase callback evidence or turn status into inbound/closure',async()=>{
  const h=setup();await h.lab.revokeFixture('S1','intent_A');
  const r=await h.call('append_batch',h.batch(['delivered']),'ingress');invariants(r);
  assert.equal(r.lab_receipt_committed,true);
  const item=Object.values(h.store.state.batches)[0].observations[0];
  assert.equal(item.observation.kind,'status_callback');assert.equal(item.state,'ARCHIVED_UNVERIFIED');
});
test('batch memory rollback undoes every item, nonce, receipt and audit',async()=>{
  const h=setup({hook:async phase=>{if(phase==='before_commit')throw Error('INJECTED');}});
  const r=await h.call('append_batch',h.batch(),'ingress');
  assert.equal(r.code,'COMMIT_OR_RESULT_UNKNOWN');assert.equal(r.lab_ack_ready,false);
  for(const k of ['batches','raw_receipts','nonces'])assert.equal(Object.keys(h.store.state[k]).length,0);
  assert.equal(h.store.state.audit.length,0);
});
test('candidate global order preserves final WA55 outbox/event/key relative order',()=>{
  const r=planLocks([{kind:'TECHNICAL_KEY',key:'key'},{kind:'EVENT',key:'event'},
    {kind:'OUTBOX',key:'outbox'},{kind:'S1_AUTHORITY_FENCE',key:'tenant'}]);
  assert.deepEqual(r.map(x=>x.kind),['S1_AUTHORITY_FENCE','OUTBOX','EVENT','TECHNICAL_KEY']);
  assert.equal(assertAcquisitionOrder(r),true);
});
test('lock plan rejects historical key/event inversion and sorts multiple resources by byte order',()=>{
  assert.throws(()=>assertAcquisitionOrder([{kind:'TECHNICAL_KEY',key:'key'},
    {kind:'EVENT',key:'event'}]),/LOCK_ORDER_INVERSION/);
  assert.deepEqual(planLocks([{kind:'OUTBOX',key:'b'},{kind:'OUTBOX',key:'A'}]).map(x=>x.key),['A','b']);
  assert.throws(()=>planLocks([{kind:'OUTBOX',key:'a'},{kind:'OUTBOX',key:'a'}]),/DUPLICATE_RESOURCE/);
});

test('identical callback items in one lot remain two observations; 101 items deny whole lot',async()=>{
  const h=setup(),r=await h.call('append_batch',h.batch(['sent','sent']),'ingress');
  assert.equal(r.items.length,2);
  const before=Object.keys(h.store.state.raw_receipts).length;
  const denied=await h.call('append_batch',h.batch(Array(101).fill('sent'),{batch_ref:'too_many'}),'ingress');
  assert.equal(denied.code,'META_BATCH_DENIED');assert.equal(denied.lab_ack_ready,false);
  assert.equal(Object.keys(h.store.state.raw_receipts).length,before);
});
test('conflict fingerprints are retained without overwriting the original observation',async()=>{
  const h=setup(),ref=await begun(h);
  await observe(h,ref,http(200));
  await observe(h,ref,http(400));
  assert.equal(h.store.state.conflicts.length,1);
  assert.notEqual(h.store.state.conflicts[0].expected,h.store.state.conflicts[0].received);
});

test('technical attempt correlation is server-owned and durable audit binds request, scope and receipt',async()=>{
  const h=setup(),ref=await begun(h),internal=h.store.state.attempts[ref].correlation_ref;
  await h.call('observe',{attempt_ref:ref,observation_ref:'obs_fixed',wire:http(200)},
    'dispatch',{correlation_id:'changed_transport_correlation'});
  const evidence=h.store.state.attempts[ref].evidence[0];
  assert.equal(evidence.correlation_ref,internal);
  assert.notEqual(internal,'changed_transport_correlation');
  const audit=h.store.state.audit.at(-1);
  assert.equal(audit.requested_attempt_ref,ref);assert.equal(audit.tenant_ref,'tenant_A');
  assert.match(audit.envelope_sha256,/^[a-f0-9]{64}$/);
  const batch=await h.call('append_batch',h.batch(),'ingress');
  assert.equal(h.store.state.audit.at(-1).receipt_ref,batch.receipt_ref);
});
test('a review ref reused with different evidence cannot overwrite reconciliation',async()=>{
  const h=setup(),ref=await begun(h);
  await observe(h,ref,{kind:'transport_error'},'one');
  await observe(h,ref,http(200),'two');
  await h.call('review',{attempt_ref:ref,decision_ref:'review_fixed',evidence_refs:['one']},'reviewer');
  const r=await h.call('review',{attempt_ref:ref,decision_ref:'review_fixed',evidence_refs:['two']},'reviewer');
  assert.equal(r.code,'REVIEW_CONFLICT_QUARANTINED');
  assert.deepEqual(h.store.state.attempts[ref].reviews[0].evidence_refs,['one']);
  assert.equal(h.store.state.attempts[ref].quarantined,true);invariants(r);
});
