import test from 'node:test';
import assert from 'node:assert/strict';
import { prepareWa15FixtureCommand as prepare } from './s0-technical-binding-contract.ts';
import type { CorrelationReference } from './technical-reconciliation.ts';
import type { GraphSendOutcome } from './graph-outbound.ts';

const reference:CorrelationReference={
  app_ref:'12345678901',
  intent_id:'f5400000-0000-4000-8000-000000000001',
  recipient_verified:'5581900000000',
  scope:{
    concessionaria_id:'f5200000-0000-4000-8000-000000000001',
    canal_id:'f5300000-0000-4000-8000-000000000001',
    meta_app_ref:'12345678901',
    meta_waba_id:'33345678901',
    phone_number_id:'55545678901',
  },
};
const graph:GraphSendOutcome={
  attempt_id:'ATTEMPT_A',correlation_id:'CORR_A',send_state:'API_ACCEPTED',
  api_accepted:true,http_status:200,provider_message_id:'wamid.WA15.ONE',
  meta_error_code:null,meta_error_subcode:null,retry_automatically:false,
};
const flags=(v:ReturnType<typeof prepare>)=>{
  assert.ok(v);
  assert.equal(v.ack_allowed,false);
  assert.equal(v.retry_external,false);
  assert.equal(v.production_authorized,false);
  assert.equal('commercial_status' in v,false);
  assert.equal('sql' in v,false,'never output interpolated SQL');
};

test('WA15B-01: technical Graph + UUID S0 scope become ten bound SQL parameters',()=>{
 const r=prepare(reference,graph,'REGISTER_FIXTURE');
 assert.ok(r);flags(r);
 assert.equal(r.function_name,'prumo_private.registrar_vinculo_meta_tecnico_fixture_s0');
 assert.deepEqual(r.args,[
  '12345678901','33345678901','55545678901',
  'f5300000-0000-4000-8000-000000000001',
  'f5400000-0000-4000-8000-000000000001',
  'ATTEMPT_A','CORR_A','5581900000000','wamid.WA15.ONE',200,
 ]);
 assert.equal(r.args.includes(reference.scope.concessionaria_id),false,
  'owner must be resolved only by S0');
});
test('WA15B-02: recovery uses nine bound args and cannot issue SQL/Graph',()=>{
 const r=prepare(reference,graph,'RECOVER_FIXTURE');
 assert.ok(r);flags(r);
 assert.equal(r.function_name,'prumo_private.consultar_vinculo_meta_tecnico_fixture_s0');
 assert.equal(r.args.length,9);
 assert.equal('http_status' in r,false);
});
test('WA15B-03: preexisting legacy fixture aliases cannot masquerade as Meta technical IDs',()=>{
 assert.equal(prepare({...reference,app_ref:'FIXTURE_WA15_APP_A'},graph,'REGISTER_FIXTURE'),undefined);
 assert.equal(prepare({...reference,scope:{...reference.scope,meta_waba_id:'WABA_A'}},graph,'REGISTER_FIXTURE'),undefined);
 assert.equal(prepare({...reference,scope:{...reference.scope,phone_number_id:'FIXTURE_PHONE_A'}},graph,'REGISTER_FIXTURE'),undefined);
});
test('WA15B-04: mismatched app vs scope app fails',()=>{
 assert.equal(prepare({...reference,app_ref:'22345678901'},graph,'REGISTER_FIXTURE'),undefined);
});
test('WA15B-05: nonexistent or malformed internal identifiers fail before DB',()=>{
 for(const key of ['concessionaria_id','canal_id'] as const){
   assert.equal(prepare({...reference,scope:{...reference.scope,[key]:'SHOP_A'}},graph,'REGISTER_FIXTURE'),undefined);
 }
 assert.equal(prepare({...reference,intent_id:'INTENT_A'},graph,'REGISTER_FIXTURE'),undefined);
});
test('WA15B-06: Graph HTTP nonaccepted/uncertain observations never prepare a DB registration',()=>{
 for(const o of [
  {...graph,http_status:503},
  {...graph,api_accepted:false},
  {...graph,send_state:'UNCERTAIN_EXTERNAL'},
  {...graph,retry_automatically:true},
  {...graph,provider_message_id:'BAD'},
  {...graph,meta_error_code:42},
 ]){
  assert.equal(prepare(reference,o as GraphSendOutcome,'REGISTER_FIXTURE'),undefined);
  assert.equal(prepare(reference,o as GraphSendOutcome,'RECOVER_FIXTURE'),undefined);
 }
});
test('WA15B-07: untrusted WABA, sender, and App must be numeric 5..25 chars',()=>{
 for(const id of ['', '1234','1'.repeat(26),'1234-5','not_numeric']){
   assert.equal(prepare({...reference,app_ref:id},graph,'REGISTER_FIXTURE'),undefined);
   assert.equal(prepare({...reference,scope:{...reference.scope,meta_waba_id:id}},graph,'REGISTER_FIXTURE'),undefined);
   assert.equal(prepare({...reference,scope:{...reference.scope,phone_number_id:id}},graph,'REGISTER_FIXTURE'),undefined);
 }
});
test('WA15B-08: exact shape; reject additional fields and accessors',()=>{
 assert.equal(prepare({...reference,privileged:true} as CorrelationReference,graph,'REGISTER_FIXTURE'),undefined);
 const hostile={...reference};
 Object.defineProperty(hostile,'scope',{get(){throw Error('UNTRUSTED_GETTER');}});
 assert.equal(prepare(hostile as CorrelationReference,graph,'REGISTER_FIXTURE'),undefined);
 assert.equal(prepare(reference,{...graph,token:'unsafe'} as GraphSendOutcome,'REGISTER_FIXTURE'),undefined);
});
test('WA15B-09: prepared fields are immutable snapshots, not reused caller objects',()=>{
 const ref={...reference,scope:{...reference.scope}};
 const g={...graph};
 const r=prepare(ref,g,'REGISTER_FIXTURE');
 assert.ok(r);
 ref.scope.phone_number_id='99999999999';
 g.provider_message_id='wamid.FORGED';
 assert.equal(r.args[2],'55545678901');
 assert.equal(r.args[8],'wamid.WA15.ONE');
 assert.equal(Object.isFrozen(r.args),true);
 assert.equal(Object.isFrozen(r),true);
});
test('WA15B-10: invalid operation cannot be promoted to a SQL call',()=>{
 assert.equal(prepare(reference,graph,'SENT' as 'REGISTER_FIXTURE'),undefined);
});
test('WA15B-11: Graph 202 is accepted at API boundary, never delivery',()=>{
 const r=prepare(reference,{...graph,http_status:202},'REGISTER_FIXTURE');
 assert.ok(r);flags(r);
 assert.equal(r.args[9],202);
 assert.equal('delivered' in r,false);
});
test('WA15B-12: read-only recovery still requires valid accepted Graph evidence',()=>{
 assert.equal(prepare(reference,{...graph,send_state:'UNCERTAIN_EXTERNAL'} as GraphSendOutcome,'RECOVER_FIXTURE'),undefined);
 const r=prepare(reference,graph,'RECOVER_FIXTURE');
 assert.ok(r);
 assert.equal(r.args[8],'wamid.WA15.ONE');
 flags(r);
});
