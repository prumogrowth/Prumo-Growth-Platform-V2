import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {WA36_REQUIREMENTS} from './wa36-ratification-gate.ts';
import {WA37_CHECKS,createWa37PendingReviewPacket as create,
 evaluateWa37ReviewPacket as evaluate} from './wa37-acceptance-handoff.ts';

const draft=()=>({...create(),entries:create().entries.map(x=>({...x}))});
const safe=(d:ReturnType<typeof evaluate>)=>{
 assert.equal(Object.isFrozen(d),true);
 assert.equal(Object.keys(d).length,11);
 assert.equal(d.required_owner_decisions,12);
 for(const flag of ['service_authenticated','s0_write_authorized',
  'production_authorized','ack_allowed','send_authorized','retry_external',
  'case_transition_authorized','delivery_confirmed'] as const)
   assert.equal(d[flag],false,flag);
};
function valid(x:unknown){
 const d=evaluate(x);assert.equal(d.outcome,'LAB_REVIEW_BLOCKED');safe(d);
 assert.equal(d.matched_criteria,12);
}
function invalid(x:unknown){
 const d=evaluate(x);assert.equal(d.outcome,'INVALID_REVIEW_PACKET');safe(d);
 assert.equal(d.matched_criteria,0);
}
test('WA37-01 all 12 positive/negative probes exactly track WA36 IDs and owners',()=>{
 assert.equal(WA37_CHECKS.length,12);
 assert.equal(new Set(WA37_CHECKS.map(x=>x.id)).size,12);
 assert.equal(Object.isFrozen(WA37_CHECKS),true);
 for(const check of WA37_CHECKS)assert.equal(Object.isFrozen(check),true);
 assert.deepEqual(WA37_CHECKS.map(x=>x.id),WA36_REQUIREMENTS.map(x=>x.id));
 assert.deepEqual(WA37_CHECKS.map(x=>x.owner),WA36_REQUIREMENTS.map(x=>x.owner));
});
test('WA37-02 acceptance probes each have independent positive and negative scenario IDs',()=>{
 const probes=new Set<string>();
 for(let i=0;i<WA37_CHECKS.length;i++){
  const x=WA37_CHECKS[i];
  assert.equal(x.positive,'WA37-P'+String(i+1).padStart(2,'0'));
  assert.equal(x.negative,'WA37-N'+String(i+1).padStart(2,'0'));
  assert.ok(x.criterion.length>=60);
  assert.ok(!probes.has(x.positive));assert.ok(!probes.has(x.negative));
  probes.add(x.positive);probes.add(x.negative);
 }
 assert.equal(probes.size,24);
});
test('WA37-03 no submitted packet is production approval',()=>{
 valid(draft());safe(evaluate(draft()));
});
test('WA37-04 all lab-only evidence still stays blocked',()=>{
 const p=draft();
 valid({...p,entries:p.entries.map(x=>({...x,evidence_state:'LAB_FIXTURE_ONLY'}))});
});
test('WA37-05 other-front draft signoffs do not replace owner decision',()=>{
 const p=draft();
 valid({...p,entries:p.entries.map(x=>({...x,evidence_state:'OTHER_FRONT_DRAFT'}))});
});
test('WA37-06 any APPROVED status is an invalid injection',()=>{
 const p=draft();invalid({...p,entries:[
  {...p.entries[0],ratification:'APPROVED'},...p.entries.slice(1)]});
});
test('WA37-07 stale WA36 ownership and human role substitution are rejected',()=>{
 const p=draft();
 for(const owner of ['DIRECTOR','GESTOR','CONSULTOR','S1','FAKE_AI']){
  invalid({...p,entries:[{...p.entries[0],requested_owner:owner},...p.entries.slice(1)]});
 }
});
test('WA37-08 principal/JWT/GoTrue field cannot sneak into packet',()=>{
 for(const k of ['gotrue_token','service_principal','jwt','role','user_id']){
  invalid({...draft(),[k]:'DIRETOR'});
 }
});
test('WA37-09 malicious production/Graph/ACK positive flags at root denied',()=>{
 for(const key of ['send_authorized','ack_allowed','s0_write_authorized',
 'production_authorized','retry_external','case_transition_authorized'])
 invalid({...draft(),[key]:true});
});
test('WA37-10 missing requirement fails',()=>{
 const p=draft();invalid({...p,entries:p.entries.slice(0,-1)});
});
test('WA37-11 duplicate requirement is not completeness',()=>{
 const p=draft();invalid({...p,entries:[p.entries[0],p.entries[0],...p.entries.slice(2)]});
});
test('WA37-12 invented acceptance probe cannot be substituted',()=>{
 const p=draft();invalid({...p,entries:[
  {...p.entries[0],positive_probe:'WA37-P99'},...p.entries.slice(1)]});
});
test('WA37-13 omitting negative probe is not acceptance',()=>{
 const p=draft();const a={...p.entries[0]} as Record<string,unknown>;
 delete a.negative_probe;
 invalid({...p,entries:[a,...p.entries.slice(1)]});
});
test('WA37-14 unknown negative probe cannot replace tenant attack',()=>{
 const p=draft();invalid({...p,entries:[
  {...p.entries[3],negative_probe:'WA37-N11'},...p.entries.filter((_,i)=>i!==3)]});
});
test('WA37-15 mismatched criterion ID is rejected',()=>{
 const p=draft();invalid({...p,entries:[
  {...p.entries[0],id:'WA36-UNLIMITED-WRITE'},...p.entries.slice(1)]});
});
test('WA37-16 transport receipt/sent evidence is not an independent signoff',()=>{
 const p=draft();
 invalid({...p,entries:[{...p.entries[0],evidence_state:'DELIVERED'},
   ...p.entries.slice(1)]});
});
test('WA37-17 no signed-by-human approver is accepted as an extra field',()=>{
 const p=draft();
 for(const key of ['approved_by','signature','reviewer','date','waiver'])
 invalid({...p,entries:[{...p.entries[0],[key]:'FAKE'},
  ...p.entries.slice(1)]});
});
test('WA37-18 extra byte content or person identifiers cannot be smuggled',()=>{
 const p=draft();
 for(const key of ['recipient_id','access_token','phone_number_id','raw_body','wamid'])
 invalid({...p,entries:[{...p.entries[0],[key]:'FAKE'},
  ...p.entries.slice(1)]});
});
test('WA37-19 unsupported contract and purpose deny',()=>{
 invalid({...draft(),contract:'wa37.crossfront.acceptance.production.v1'});
 invalid({...draft(),purpose:'DEPLOY_APPROVED'});
});
test('WA37-20 null, scalar, arrays, missing root fail closed',()=>{
 for(const v of [null,undefined,0,true,[],42,'WA37',{}, {entries:[]},
  {contract:'wa37.crossfront.acceptance.offline.v1'}])invalid(v);
});
test('WA37-21 inherited and symbol properties rejected',()=>{
 const p=draft();
 invalid(Object.assign(Object.create({role:'DIRECTOR'}),p));
 invalid(Object.assign({...p},{[Symbol('secret')]:true}));
});
test('WA37-22 malicious accessor, proxy and throwing ownKeys fail closed',()=>{
 const p=draft();
 const x={...p};
 Object.defineProperty(x,'entries',{get(){throw Error('GETTER')}});
 invalid(x);
 const evil=new Proxy(p,{ownKeys(){throw Error('KEYS')}});
 invalid(evil);
});
test('WA37-23 row prototypes and getters cannot forge owner attestation',()=>{
 const p=draft();
 const original=p.entries[0];
 invalid({...p,entries:[Object.assign(Object.create({approved:true}),original),
 ...p.entries.slice(1)]});
 const x={...original};Object.defineProperty(x,'ratification',
  {get(){throw Error('TRAP')}});
 invalid({...p,entries:[x,...p.entries.slice(1)]});
});
test('WA37-24 checklist order does not change ownership or proof obligation',()=>{
 const p=draft();valid({...p,entries:[...p.entries].reverse()});
});
test('WA37-25 the builder returns frozen, data-only proof obligations',()=>{
 const d=create();
 assert.ok(Object.isFrozen(d));assert.ok(Object.isFrozen(d.entries));
 for(const e of d.entries)assert.ok(Object.isFrozen(e));
 assert.deepEqual(Object.keys(d).sort(),['contract','entries','purpose']);
 valid(d);
});
test('WA37-26 all decisions exclude identities, keys and hidden grants',()=>{
 for(const raw of [draft(),null,{...draft(),ack_allowed:true}]){
  const d=evaluate(raw);safe(d);
  const serialized=JSON.stringify(d);
  for(const word of ['APP_SECRET','wamid','service_principal','CONSULTOR','phone',
   'case_ref','DIRETOR','jwt','SQL'])assert.equal(serialized.includes(word),false);
 }
});
test('WA37-27 documentation traces every acceptance requirement and probe',()=>{
 const doc=readFileSync(new URL(
  '../../docs/integracoes/whatsapp-meta/wa37-contrato-aceite-interfrentes-m2m-2026-10-23.md',
  import.meta.url),'utf8');
 assert.ok(doc.length>3000);
 for(const x of WA37_CHECKS){
  assert.equal(doc.includes(x.id),true,'missing '+x.id);
  assert.equal(doc.includes(x.positive),true,'missing '+x.positive);
  assert.equal(doc.includes(x.negative),true,'missing '+x.negative);
 }
});
