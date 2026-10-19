import test from 'node:test';
import assert from 'node:assert/strict';
import {FakeMetaS0BindingBridge} from './s0-binding-bridge.ts';
import type {CorrelationReference} from './technical-reconciliation.ts';
import type {GraphSendOutcome} from './graph-outbound.ts';
import type {MetaIngressEvent} from './inbound.ts';
const ref:CorrelationReference={
  app_ref:'APP_A',intent_id:'INTENT_A',recipient_verified:'5581900000000',
  scope:{concessionaria_id:'SHOP_A',canal_id:'CHANNEL_A',meta_app_ref:'APP_A',
    meta_waba_id:'WABA_A',phone_number_id:'12345678901'},
};
const outcome:GraphSendOutcome={
  attempt_id:'ATTEMPT_A',correlation_id:'CORR_A',send_state:'API_ACCEPTED',
  api_accepted:true,http_status:200,provider_message_id:'wamid.OUT_A',
  meta_error_code:null,meta_error_subcode:null,retry_automatically:false,
};
const callback=(status:string,position=0,changes:Partial<MetaIngressEvent>={}):MetaIngressEvent=>({
  source:'meta_whatsapp',event_kind:'status_callback',waba_id:'WABA_A',
  phone_number_id:'12345678901',provider_message_id:'wamid.OUT_A',
  participant_identifier:'5581900000000',provider_timestamp:'2026-10-19T18:00:00.000Z',
  provider_kind:status,position:{entry_index:0,change_index:0,array_kind:'statuses',item_index:position},
  ...changes,
});
const assertNoAuthority=(x:unknown)=>{
  const s=JSON.stringify(x);
  for(const token of ['wamid.',ref.recipient_verified,ref.app_ref,'commercial_status','http_status','access_token'])
    assert.equal(s.includes(token),false,token);
  assert.equal(s.includes('true'),false,'never allow ACK / external retry / production');
};
test('WA13-01: linked Graph observation still starts at technical NONE, not delivered',()=>{
  const x=new FakeMetaS0BindingBridge();
  assert.equal(x.recordAcceptedFixture(ref,outcome).decision,'LAB_COMMITTED');
  assert.equal(x.recoverAndLinkFixture(ref,outcome).decision,'LAB_LINKED');
  assert.deepEqual(x.projectionFor(ref,'wamid.OUT_A'),{
    progress:'NONE',failure_observed:false,observation_count:0});
});
test('WA13-02: response lost AFTER lab commit, exact recovery attaches pending status',()=>{
  const x=new FakeMetaS0BindingBridge();
  assert.equal(x.observeAuthenticatedFixture(callback('read'),'APP_A').decision,'PENDING_RECONCILIATION');
  assert.equal(x.recordAcceptedFixture(ref,outcome,'after_commit_response_lost').decision,'LAB_COMMIT_UNKNOWN');
  const result=x.recoverAndLinkFixture(ref,outcome);
  assert.equal(result.decision,'LAB_LINKED');assert.equal(result.pending_correlated,1);
  assert.equal(x.projectionFor(ref,'wamid.OUT_A')?.progress,'READ');
  assert.equal(x.pendingCount,0);assertNoAuthority(result);
});
test('WA13-03: response lost BEFORE lab commit leaves binding absent and status pending',()=>{
  const x=new FakeMetaS0BindingBridge();
  x.observeAuthenticatedFixture(callback('sent'),'APP_A');
  assert.equal(x.recordAcceptedFixture(ref,outcome,'before_commit_response_lost').decision,'LAB_COMMIT_UNKNOWN');
  const r=x.recoverAndLinkFixture(ref,outcome);
  assert.equal(r.decision,'LAB_COMMIT_ABSENT');assert.equal(x.bindingCount,0);
  assert.equal(x.linkedCount,0);assert.equal(x.pendingCount,1);assertNoAuthority(r);
});
test('WA13-04: recovery lookup never inserts or sends missing Graph observation',()=>{
  const x=new FakeMetaS0BindingBridge();
  for(let i=0;i<5;i++)assert.equal(x.recoverAndLinkFixture(ref,outcome).decision,'LAB_COMMIT_ABSENT');
  assert.equal(x.bindingCount,0);assert.equal(x.linkedCount,0);
});
test('WA13-05: scope changed after commit cannot be projected',()=>{
  const x=new FakeMetaS0BindingBridge();x.recordAcceptedFixture(ref,outcome);
  const changed={...ref,scope:{...ref.scope,canal_id:'CHANNEL_B'}};
  assert.equal(x.recoverAndLinkFixture(changed,outcome).decision,'LAB_BINDING_CONFLICT');
  assert.equal(x.linkedCount,0);
});
test('WA13-06: mismatched claimed App and trusted scope denied before committing',()=>{
  const x=new FakeMetaS0BindingBridge();
  const changed={...ref,app_ref:'APP_B'};
  assert.equal(x.recordAcceptedFixture(changed,outcome).decision,'LAB_REJECTED');
  assert.equal(x.recoverAndLinkFixture(changed,outcome).decision,'LAB_INVALID');
  assert.equal(x.bindingCount,0);
});
test('WA13-07: same attempt cannot silently receive a second wamid',()=>{
  const x=new FakeMetaS0BindingBridge();x.recordAcceptedFixture(ref,outcome);
  const second={...outcome,provider_message_id:'wamid.OUT_B'};
  assert.equal(x.recordAcceptedFixture(ref,second).decision,'LAB_CONFLICT');
  assert.equal(x.recoverAndLinkFixture(ref,second).decision,'LAB_BINDING_CONFLICT');
  assert.equal(x.bindingCount,1);
});
test('WA13-08: same wamid cannot be attributed to another attempt',()=>{
  const x=new FakeMetaS0BindingBridge();x.recordAcceptedFixture(ref,outcome);
  const second={...outcome,attempt_id:'ATTEMPT_B'};
  assert.equal(x.recordAcceptedFixture(ref,second).decision,'LAB_CONFLICT');
  assert.equal(x.recoverAndLinkFixture(ref,second).decision,'LAB_BINDING_CONFLICT');
});
test('WA13-09: idempotent recovery does not duplicate technical link',()=>{
  const x=new FakeMetaS0BindingBridge();x.recordAcceptedFixture(ref,outcome);
  assert.equal(x.recoverAndLinkFixture(ref,outcome).decision,'LAB_LINKED');
  assert.equal(x.recoverAndLinkFixture(ref,outcome).decision,'LAB_ALREADY_LINKED');
  assert.equal(x.linkedCount,1);
});
test('WA13-10: callback from wrong App is pending and not assigned to local link',()=>{
  const x=new FakeMetaS0BindingBridge();x.recordAcceptedFixture(ref,outcome);
  x.recoverAndLinkFixture(ref,outcome);
  assert.equal(x.observeAuthenticatedFixture(callback('read'),'APP_B').decision,'PENDING_RECONCILIATION');
  assert.equal(x.projectionFor(ref,'wamid.OUT_A')?.observation_count,0);
});
test('WA13-11: wrong WABA, sender, or recipient cannot correlate',()=>{
  const x=new FakeMetaS0BindingBridge();x.recordAcceptedFixture(ref,outcome);
  x.recoverAndLinkFixture(ref,outcome);
  for(const c of [{waba_id:'WABA_B'}, {phone_number_id:'9999999999'},
    {participant_identifier:'5581999999999'}])
    assert.equal(x.observeAuthenticatedFixture(callback('read',0,c),'APP_A').decision,'PENDING_RECONCILIATION');
  assert.equal(x.projectionFor(ref,'wamid.OUT_A')?.progress,'NONE');
});
test('WA13-12: distinct status positions remain separate, never deduped by wamid',()=>{
  const x=new FakeMetaS0BindingBridge();x.recordAcceptedFixture(ref,outcome);
  x.recoverAndLinkFixture(ref,outcome);
  assert.equal(x.observeAuthenticatedFixture(callback('sent',0),'APP_A').observation_count,1);
  assert.equal(x.observeAuthenticatedFixture(callback('sent',1),'APP_A').observation_count,2);
  assert.equal(x.projectionFor(ref,'wamid.OUT_A')?.observation_count,2);
});
test('WA13-13: failed callback never sets sold or lost state',()=>{
  const x=new FakeMetaS0BindingBridge();x.recordAcceptedFixture(ref,outcome);
  x.recoverAndLinkFixture(ref,outcome);
  const r=x.observeAuthenticatedFixture(callback('failed'),'APP_A');
  assert.equal(r.failure_observed,true);assert.equal(r.progress,'NONE');
  assert.equal('commercial_status' in r,false);
});
test('WA13-14: nonaccepted Graph evidence cannot establish a binding',()=>{
  const x=new FakeMetaS0BindingBridge();
  for(const o of [{...outcome,http_status:503}, {...outcome,send_state:'UNCERTAIN_EXTERNAL'},
     {...outcome,api_accepted:false},{...outcome,meta_error_code:99}]){
    assert.equal(x.recordAcceptedFixture(ref,o as GraphSendOutcome).decision,'LAB_REJECTED');
    assert.notEqual(x.recoverAndLinkFixture(ref,o as GraphSendOutcome).decision,'LAB_LINKED');
  }
  assert.equal(x.bindingCount,0);
});
test('WA13-15: hostile getter, extra fields and mutation are rejected or snapshot-isolated',()=>{
  const x=new FakeMetaS0BindingBridge();
  const getter={...ref};Object.defineProperty(getter,'app_ref',{get(){throw Error('X')}});
  assert.equal(x.recordAcceptedFixture(getter as CorrelationReference,outcome).decision,'LAB_REJECTED');
  assert.equal(x.recordAcceptedFixture({...ref,secret:'x'} as CorrelationReference,outcome).decision,'LAB_REJECTED');
  const hostile=new Proxy({...outcome},{get(target,key,recv){
    return key==='provider_message_id'?'wamid.ATTACK':Reflect.get(target,key,recv);
  }});
  assert.equal(x.recordAcceptedFixture(ref,hostile).decision,'LAB_COMMITTED');
  assert.equal(x.recoverAndLinkFixture(ref,outcome).decision,'LAB_LINKED');
});
test('WA13-16: new bridge is not durable: fake records disappear on restart',()=>{
  const one=new FakeMetaS0BindingBridge();one.recordAcceptedFixture(ref,outcome);
  const two=new FakeMetaS0BindingBridge();
  assert.equal(two.recoverAndLinkFixture(ref,outcome).decision,'LAB_COMMIT_ABSENT');
  assert.equal(one.recoverAndLinkFixture(ref,outcome).decision,'LAB_LINKED');
});
test('WA13-17: same provider wamid under independent App is technically isolated',()=>{
  const x=new FakeMetaS0BindingBridge();x.recordAcceptedFixture(ref,outcome);
  const other={...ref,app_ref:'APP_B',intent_id:'INTENT_B',scope:{...ref.scope,
    meta_app_ref:'APP_B',concessionaria_id:'SHOP_B',canal_id:'CHANNEL_B',
    meta_waba_id:'WABA_B',phone_number_id:'9999999999'}};
  const outB={...outcome,attempt_id:'ATTEMPT_B'};
  assert.equal(x.recordAcceptedFixture(other,outB).decision,'LAB_COMMITTED');
  assert.equal(x.recoverAndLinkFixture(other,outB).decision,'LAB_LINKED');
  assert.equal(x.recoverAndLinkFixture(ref,outcome).decision,'LAB_LINKED');
  assert.equal(x.linkedCount,2);
});
test('WA13-18: exposed decisions never disclose IDs, grant retry or ACK',()=>{
  const x=new FakeMetaS0BindingBridge();
  assertNoAuthority(x.recordAcceptedFixture(ref,outcome));
  assertNoAuthority(x.recoverAndLinkFixture(ref,outcome));
});
