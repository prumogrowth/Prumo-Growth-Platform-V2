import test from 'node:test';
import assert from 'node:assert/strict';
import {FakeAttemptBindingLedger, type AttemptIdentity} from './attempt-binding.ts';
const a:AttemptIdentity = {
  app_ref:'APP_A',concessionaria_id:'SHOP_A',canal_id:'CHANNEL_A',
  waba_id:'WABA_A',phone_number_id:'12345678901',
  intent_id:'INTENT_A',attempt_id:'ATTEMPT_A',correlation_id:'CORR_A',
  recipient_verified:'5581900000000',provider_message_id:'wamid.OUT_A',
};
test('WA10-01: one accepted synthetic Graph attempt creates only technical binding',()=>{
 const j=new FakeAttemptBindingLedger();assert.equal(j.claim(a),'NEW');assert.equal(j.size,1);
});
test('WA10-02: exact same tuple is idempotent, not a new send',()=>{
 const j=new FakeAttemptBindingLedger();assert.equal(j.claim(a),'NEW');
 assert.equal(j.claim({...a}),'SAME');assert.equal(j.size,1);
});
test('WA10-03: a changed provider wamid never binds to already used attempt',()=>{
 const j=new FakeAttemptBindingLedger();j.claim(a);
 assert.equal(j.claim({...a,provider_message_id:'wamid.OUT_B'}),'CONFLICT');assert.equal(j.size,1);
});
test('WA10-04: changing channel, WABA, phone, recipient, intent or correlation fails',()=>{
 for (const [k,v] of [
   ['canal_id','CHANNEL_B'],['waba_id','WABA_B'],['phone_number_id','98765432101'],
   ['recipient_verified','5581999999999'],['intent_id','INTENT_B'],
   ['correlation_id','CORR_B'] ] as const){
   const j=new FakeAttemptBindingLedger();j.claim(a);
   assert.equal(j.claim({...a,[k]:v}),'CONFLICT',k);
 }
});
test('WA10-05: different attempts can be tracked independently',()=>{
 const j=new FakeAttemptBindingLedger();j.claim(a);
 assert.equal(j.claim({...a,attempt_id:'ATTEMPT_B',provider_message_id:'wamid.OUT_B'}),'NEW');
 assert.equal(j.size,2);
});
test('WA10-06: equal attempt IDs from different shops or Apps stay isolated',()=>{
 const j=new FakeAttemptBindingLedger();j.claim(a);
 assert.equal(j.claim({...a,app_ref:'APP_B',concessionaria_id:'SHOP_B'}),'NEW');
 assert.equal(j.size,2);
});
test('WA10-07: invalid keys, wamids, or sender identifiers are refused',()=>{
 const j=new FakeAttemptBindingLedger();
 for (const v of [{...a,attempt_id:'a b'}, {...a,provider_message_id:'MSG'},
   {...a,phone_number_id:'PHONE_A'}, {...a,recipient_verified:'+5581900000000'},
   {...a,app_ref:''},{...a,attempt_id:'x'.repeat(129)}])
   assert.equal(j.claim(v),'INVALID');
 assert.equal(j.size,0);
});
test('WA10-08: getters, symbols, arrays and extra fields fail closed',()=>{
 const j=new FakeAttemptBindingLedger();
 const accessor={...a}; Object.defineProperty(accessor,'app_ref',{get(){throw Error('accessor')}});
 for(const bad of [accessor, {...a, extra:'x'}, {...a,[Symbol('secret')]:'x'}, [a],null])
   assert.equal(j.claim(bad),'INVALID');
 assert.equal(j.size,0);
});
test('WA10-09: capacity is bounded and refuses an extra attempt',()=>{
 const j=new FakeAttemptBindingLedger();
 for(let i=0;i<100;i++)assert.equal(j.claim({...a,attempt_id:'ATTEMPT_'+i}),'NEW');
 assert.equal(j.size,100);
 assert.equal(j.claim({...a,attempt_id:'ATTEMPT_EXTRA'}),'INVALID');
 assert.equal(j.claim(a),'INVALID');
 assert.equal(j.claim({...a,attempt_id:'ATTEMPT_0'}),'SAME');
});
test('WA10-10: responses contain no message IDs, customer identifiers, or credentials',()=>{
 const j=new FakeAttemptBindingLedger();
 const res=JSON.stringify([j.claim(a),j.claim({...a,provider_message_id:'wamid.ALT'})]);
 for (const s of [a.recipient_verified,a.provider_message_id,a.app_ref,'Bearer'])
   assert.equal(res.includes(s),false);
});
test('WA10-11: RegExp coercion cannot turn numeric references into accepted identity',()=>{
 const j=new FakeAttemptBindingLedger();
 for(const bad of [{...a,attempt_id:1234},{...a,phone_number_id:12345678901},
   {...a,recipient_verified:5581900000000},{...a,intent_id:123}])
   assert.equal(j.claim(bad),'INVALID');
 assert.equal(j.size,0);
});
