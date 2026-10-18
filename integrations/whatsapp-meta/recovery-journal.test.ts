import { test } from 'node:test';
import assert from 'node:assert/strict';
import { FakeS0RecoveryJournal, type SimulatedBatch } from './recovery-journal.ts';
const b: SimulatedBatch = {batch_ref:'BATCH_A',app_ref:'APP_A',concessionaria_id:'STORE_A',
  canal_id:'CANAL_A',protected_payload_ref:'PROTECTED_A',payload_digest:'a'.repeat(64),
  events:[{array_kind:'messages',entry_index:0,change_index:0,item_index:0,provider_message_id:'wamid.IN_A'}]};
const several: SimulatedBatch = {...b,events:[b.events[0],
  {array_kind:'statuses',entry_index:0,change_index:0,item_index:0,provider_message_id:'wamid.OUT_A'}]};
const scope={app_ref:'APP_A',concessionaria_id:'STORE_A',canal_id:'CANAL_A'};
const claim = (j: FakeS0RecoveryJournal,owner='WORKER_A',tick=10) => j.claim(owner,tick,10,scope);

test('RECOV-01 metadata journal commit remains lab-only and never authorizes Meta ACK',()=>{
  const j=new FakeS0RecoveryJournal(), r=j.admit(b);
  assert.deepEqual(r,{decision:'LAB_COMMITTED',reason:'COMMITTED',count:1,ack_allowed:false,production_authorized:false});
  assert.equal(j.batchCount,1);assert.equal(j.occurrenceCount,1);
});
test('RECOV-02 failure before commit leaves absolutely no journal or work',()=>{
  const j=new FakeS0RecoveryJournal();assert.equal(j.admit(b,'before_commit').decision,'LAB_NOT_COMMITTED');
  assert.equal(j.batchCount,0);assert.equal(j.occurrenceCount,0);
  assert.equal(claim(j).decision,'NO_WORK');
});
test('RECOV-03 crash after commit loses result but preserves fake journal metadata',()=>{
  const j=new FakeS0RecoveryJournal();assert.equal(j.admit(b,'after_commit').decision,'LAB_RESULT_UNKNOWN');
  assert.equal(j.batchCount,1);assert.equal(j.recover(b).decision,'LAB_FOUND');
});
test('RECOV-04 retry same internal batch ref returns lab replay without duplicate occurrence',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(b,'after_commit');
  assert.equal(j.admit(b).decision,'LAB_ALREADY_COMMITTED');
  assert.equal(j.occurrenceCount,1);
});
test('RECOV-05 changing payload digest under same batch ref returns conflict',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(b);
  assert.equal(j.admit({...b,payload_digest:'b'.repeat(64)}).decision,'LAB_CONFLICT');
});
test('RECOV-06 changing tenant App under same batch ref returns conflict',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(b);
  for(const key of ['app_ref','concessionaria_id','canal_id'] as const){
    assert.equal(j.admit({...b,[key]:'FORGED_B'}).decision,'LAB_CONFLICT');
    assert.equal(j.recover({...b,[key]:'FORGED_B'}).decision,'LAB_MISMATCH');
  }
});
test('RECOV-07 new batch preserves same provider message ID as separate observation',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(b);
  j.admit({...b,batch_ref:'BATCH_B',protected_payload_ref:'PROTECTED_B'});
  assert.equal(j.batchCount,2);assert.equal(j.occurrenceCount,2);
});
test('RECOV-08 status and message position zero are distinct with array kind',()=>{
  const j=new FakeS0RecoveryJournal();assert.equal(j.admit(several).count,2);
  assert.equal(j.occurrenceCount,2);
});
test('RECOV-09 duplicate same-array position in one batch rejected all-or-none',()=>{
  const j=new FakeS0RecoveryJournal();const duplicate={...b,events:[b.events[0],{...b.events[0],provider_message_id:'wamid.OTHER'}]};
  assert.equal(j.admit(duplicate).decision,'LAB_INVALID');assert.equal(j.batchCount,0);
});
test('RECOV-10 malformed/untrusted descriptors return sanitized denial',()=>{
  const j=new FakeS0RecoveryJournal();
  for(const input of [{...b,batch_ref:'../oops'}, {...b,protected_payload_ref:''},
    {...b,payload_digest:'bad'}, {...b,events:[]},
    {...b,events:[{...b.events[0],entry_index:-1}]},
    {...b,events:[{...b.events[0],array_kind:'untrusted'}]}]){
    assert.equal(j.admit(input as SimulatedBatch).decision,'LAB_INVALID');
  }
  assert.equal(j.occurrenceCount,0);
});
test('RECOV-11 recovery lookup of nonexistent batch makes no fake ACK claim',()=>{
  const j=new FakeS0RecoveryJournal();assert.deepEqual(j.recover(b),
    {decision:'LAB_ABSENT',pending:0,done:0,ack_allowed:false,production_authorized:false});
});
test('RECOV-12 unmodified metadata is required for recovering committed batch',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(b);
  for(const change of [{...b,protected_payload_ref:'PROTECTED_B'},
    {...b,events:[{...b.events[0],provider_message_id:'wamid.OTHER'}]}]){
    assert.equal(j.recover(change).decision,'LAB_MISMATCH');
  }
});
test('RECOV-13 restarting the worker with SAME fake journal can resume pending work',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(b,'after_commit');
  const restarted=new FakeS0RecoveryJournal(); // a NEW JOURNAL is empty: not durable!
  assert.equal(restarted.recover(b).decision,'LAB_ABSENT');
  assert.equal(j.claim('RESTARTED',10,20,scope).decision,'CLAIMED');
});
test('RECOV-14 active lease prevents second worker from processing same occurrence',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(b);assert.equal(claim(j).decision,'CLAIMED');
  assert.equal(claim(j,'WORKER_B').decision,'NO_WORK');
});
test('RECOV-15 expired lease can be reclaimed but its stale token cannot finish',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(b);
  const old=claim(j);const next=claim(j,'WORKER_B',20);
  assert.equal(next.decision,'CLAIMED');assert.notEqual(old.lease_ref,next.lease_ref);
  assert.equal(j.finish('WORKER_A',old.occurrence_ref!,old.lease_ref!,20,'none',scope).decision,'STALE_LEASE');
  assert.equal(j.finish('WORKER_B',next.occurrence_ref!,next.lease_ref!,20,'none',scope).decision,'APPLIED_IN_LAB');
});
test('RECOV-16 wrong worker or forged lease cannot apply a technical effect',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(b);const c=claim(j);
  assert.equal(j.finish('WORKER_B',c.occurrence_ref!,c.lease_ref!,11,'none',scope).decision,'STALE_LEASE');
  assert.equal(j.finish('WORKER_A',c.occurrence_ref!,'FAKE_LEASE_FORGED',11,'none',scope).decision,'STALE_LEASE');
  assert.equal(j.appliedEffects,0);
});
test('RECOV-17 expired lease cannot finish without being reclaimed',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(b);const c=claim(j);
  assert.equal(j.finish('WORKER_A',c.occurrence_ref!,c.lease_ref!,20,'none',scope).decision,'STALE_LEASE');
});
test('RECOV-18 crash after internal effect loses response but cannot repeat that effect',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(b);
  const c=claim(j);assert.equal(j.finish('WORKER_A',c.occurrence_ref!,c.lease_ref!,11,'after_apply',scope).decision,'LAB_RESULT_UNKNOWN');
  assert.equal(j.appliedEffects,1);assert.equal(j.claim('RESTARTED',20,10,scope).decision,'NO_WORK');
  assert.equal(j.finish('WORKER_A',c.occurrence_ref!,c.lease_ref!,12,'none',scope).decision,'ALREADY_DONE');
  assert.equal(j.appliedEffects,1);
});
test('RECOV-19 journal recovery reports pending vs already applied technical effects',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(several);const c=claim(j);
  j.finish('WORKER_A',c.occurrence_ref!,c.lease_ref!,11,'none',scope);
  assert.deepEqual(j.recover(several),{decision:'LAB_FOUND',pending:1,done:1,ack_allowed:false,production_authorized:false});
});
test('RECOV-20 two statuses sharing wamid may each be processed independently',()=>{
  const j=new FakeS0RecoveryJournal();const status:SimulatedBatch={...b,events:[
    {array_kind:'statuses',entry_index:0,change_index:0,item_index:0,provider_message_id:'wamid.SAME'},
    {array_kind:'statuses',entry_index:0,change_index:0,item_index:1,provider_message_id:'wamid.SAME'}]};
  j.admit(status);const a=claim(j);j.finish('WORKER_A',a.occurrence_ref!,a.lease_ref!,11,'none',scope);
  const c=claim(j);assert.notEqual(c.occurrence_ref,a.occurrence_ref);
  j.finish('WORKER_A',c.occurrence_ref!,c.lease_ref!,11,'none',scope);
  assert.equal(j.appliedEffects,2);
});
test('RECOV-21 bad logical clock or duration never grants a lease',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(b);
  for(const time of [NaN,-1,Number.MAX_SAFE_INTEGER])assert.equal(j.claim('WORKER_A',time,10,scope).decision,'INVALID');
  assert.equal(j.claim('WORKER_A',10,0,scope).decision,'INVALID');
});
test('RECOV-22 invalid finish never increments effects or exposes raw payload',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(b);
  const r=j.finish('WORKER_A','..BAD','..BAD',-1,'none',scope);
  assert.equal(r.decision,'INVALID');assert.equal(j.appliedEffects,0);
  assert.equal(JSON.stringify(r).includes('PROTECTED_A'),false);
});
test('RECOV-23 recovery replay after crash before commit can be retried without partial state',()=>{
  const j=new FakeS0RecoveryJournal();j.admit(b,'before_commit');
  assert.equal(j.recover(b).decision,'LAB_ABSENT');
  assert.equal(j.admit(b).decision,'LAB_COMMITTED');assert.equal(j.occurrenceCount,1);
});
test('RECOV-24 all states are non-operational and never become S0 COMMITTED/HTTP ACK',()=>{
  const j=new FakeS0RecoveryJournal();const r=j.admit(b);
  const json=JSON.stringify([r,j.recover(b),claim(j)]);
  assert.equal(json.includes('commit_state'),false);assert.equal(json.includes('http_status'),false);
  assert.equal(json.includes('ack_allowed":true'),false);assert.equal(json.includes('production_authorized":true'),false);
});

test('RECOV-25 opaque padded wamid IDs are compatible with Graph adapter',()=>{
  const j=new FakeS0RecoveryJournal();
  const padded={...b,events:[{...b.events[0],provider_message_id:'wamid.HBgL+A/BC='}]};
  assert.equal(j.admit(padded).decision,'LAB_COMMITTED');
  assert.equal(j.recover(padded).decision,'LAB_FOUND');
  assert.equal(j.admit({...padded,batch_ref:'BATCH_NEW',events:[{...padded.events[0],provider_message_id:'wamid.bad\n'}]}).decision,'LAB_INVALID');
});
test('RECOV-26 noncloneable extra fixture input denies without throwing or partial commit',()=>{
  const j=new FakeS0RecoveryJournal();
  const hostile={...b,unsupported:()=>42};
  assert.doesNotThrow(()=>j.admit(hostile));
  assert.equal(j.admit(hostile).decision,'LAB_INVALID');
  assert.equal(j.occurrenceCount,0);
});
