import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectWa21HandoffOffline as inspect,
 recheckWa21HandoffOffline as recheck} from './wa21-human-handoff-f01-f03-offline.ts';
const NOW=1800000000000,SHOP='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const c=()=>({
 contract_version:'wa21-s0-case-state.lab.v0.1',
 concessionaria_id:SHOP,app_ref:'APP_A',waba_ref:'WABA_A',
 phone_number_id:'10000001',case_ref:'CASE_A',lead_ref:'LEAD_A',
 case_revision:6,assignment_revision:4,handoff_revision:2,
 f03_cutoff_revision:3,case_state:'LAB_HUMAN_HANDOFF_DEFINITIVE',
 handoff_ever_definitive:true,handoff_at_ms:NOW-4000,
 human_assignment_ref:'HUMAN_A',meta_window_claim:'LAB_OPEN',
 opt_out_claim:false,observed_at_ms:NOW-1000,now_ms:NOW,
 max_age_ms:60000,s0_source_authenticated:false,
 case_authority_verified:false,
});
const ev=(kind='LAB_INBOUND_MESSAGE')=>({
 contract_version:'wa21-case-event.lab.v0.1',
 concessionaria_id:SHOP,app_ref:'APP_A',waba_ref:'WABA_A',
 phone_number_id:'10000001',case_ref:'CASE_A',lead_ref:'LEAD_A',
 event_ref:'EV_1',event_digest:'a'.repeat(64),event_kind:kind,
 event_at_ms:NOW-2000,
 closure_ref:kind==='LAB_HUMAN_CLOSURE_EXPLICIT'?'CLOSURE_A':null,
 actor_ref:kind==='LAB_HUMAN_CLOSURE_EXPLICIT'?'HUMAN_A':null,
 actor_role:kind==='LAB_HUMAN_CLOSURE_EXPLICIT'?'CONSULTOR':null,
 closure_cutoff_ms:kind==='LAB_HUMAN_CLOSURE_EXPLICIT'?NOW-2000:null,
 s0_event_authenticated:false,human_closure_verified:false,
});
const active=()=>({...c(),case_state:'LAB_F01_ACTIVE',
 handoff_ever_definitive:false,handoff_at_ms:null,
 human_assignment_ref:null});
const closed=()=>({...c(),case_state:'LAB_HUMAN_CLOSED'});
const run=(ctx:any=c(),event:any=ev())=>inspect(ctx,event);
function good(x:any,decision:string){
 assert.equal(x.decision,decision);assert.equal(x.reason,null);
 assert.ok(x.snapshot);assert.equal(Object.isFrozen(x),true);
 assert.equal(Object.isFrozen(x.snapshot),true);
 assert.equal(x.snapshot.decision,
  decision==='LAB_RECHECKED_UNVERIFIED'?x.snapshot.decision:decision);
 assert.equal(x.snapshot.f03_requires_explicit_human_closure,true);
 assert.equal(x.snapshot.meta_window_is_not_f03_cutoff,true);
 assert.equal(x.snapshot.s0_recheck_required,true);
 assert.match(x.snapshot.snapshot_sha256,/^[a-f0-9]{64}$/);
 for(const k of ['source_authenticated','case_verified','closure_verified',
 'f01_invocation_authorized','f03_invocation_authorized',
 'human_dispatch_authorized','graph_dispatch_authorized',
 'human_closure_apply_authorized','commercial_transition_authorized',
 'c09_window_authorized','ack_allowed','production_authorized']){
  assert.equal(x[k],false,k);assert.equal(x.snapshot[k],false,k);
 }
 for(const hidden of [SHOP,'APP_A','WABA_A','CASE_A','LEAD_A','HUMAN_A',
 'CLOSURE_A','10000001','EV_1'])assert.equal(JSON.stringify(x).includes(hidden),false);
 return x.snapshot;
}
function denied(x:any,reason:string){
 assert.equal(x.decision,'DENIED');assert.equal(x.reason,reason);
 assert.equal(x.snapshot,null);assert.equal(x.production_authorized,false);
 assert.equal(x.f01_invocation_authorized,false);
 assert.equal(x.f03_invocation_authorized,false);
}
test('M21-01 inbound after definitive handoff routes human only',()=>{
 const s=good(run(),'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED');
 assert.equal(s.f01_resume_denied,true);
});
test('M21-02 active F01 inbound can only be a review candidate',()=>{
 const s=good(run(active()),'LAB_F01_ACTIVE_UNVERIFIED');
 assert.equal(s.f01_resume_denied,false);
});
test('M21-03 F01 active cannot regain control after definitive history',()=>{
 denied(run({...active(),handoff_ever_definitive:true}),
  'DEF_HANDOFF_CANNOT_RESUME_F01');
});
test('M21-04 F01 active with handoff timestamp is contradictory',()=>{
 denied(run({...active(),handoff_at_ms:NOW-3000}),
  'DEF_HANDOFF_CANNOT_RESUME_F01');
});
test('M21-05 F01 active with human assignment is contradictory',()=>{
 denied(run({...active(),human_assignment_ref:'HUMAN_A'}),
  'DEF_HANDOFF_CANNOT_RESUME_F01');
});
test('M21-06 terminal handoff without sticky history denied',()=>{
 denied(run({...c(),handoff_ever_definitive:false}),
 'DEF_HANDOFF_CANNOT_RESUME_F01');
});
test('M21-07 terminal handoff requires human assignment',()=>{
 denied(run({...c(),human_assignment_ref:null}),'TIMELINE_INCOHERENT');
});
test('M21-08 terminal handoff requires timestamp',()=>{
 denied(run({...c(),handoff_at_ms:null}),'TIMELINE_INCOHERENT');
});
test('M21-09 terminal handoff in future denied',()=>{
 denied(run({...c(),handoff_at_ms:NOW+1}),'TIMELINE_INCOHERENT');
});
test('M21-10 inbound in closed case holds without F01 or F03',()=>{
 const s=good(run(closed()),'LAB_POST_CLOSURE_HOLD');
 assert.equal(s.f01_resume_denied,true);
});
test('M21-11 explicit human closure candidate only on closed case',()=>{
 const s=good(run(closed(),ev('LAB_HUMAN_CLOSURE_EXPLICIT')),
  'LAB_F03_CUTOFF_CANDIDATE_UNVERIFIED');
 assert.equal(s.f01_resume_denied,true);
});
test('M21-12 explicit closure while handoff still active denied',()=>{
 denied(run(c(),ev('LAB_HUMAN_CLOSURE_EXPLICIT')),
  'CLOSURE_IN_WRONG_STATE');
});
test('M21-13 explicit closure while F01 active denied',()=>{
 denied(run(active(),ev('LAB_HUMAN_CLOSURE_EXPLICIT')),
  'CLOSURE_IN_WRONG_STATE');
});
test('M21-14 window timeout cannot trigger F03',()=>{
 good(run(closed(),ev('LAB_META_WINDOW_TIMEOUT')),'LAB_POST_CLOSURE_HOLD');
});
test('M21-15 template sent claim cannot trigger F03',()=>{
 good(run(closed(),ev('LAB_TEMPLATE_SENT_CLAIM')),'LAB_POST_CLOSURE_HOLD');
});
test('M21-16 human message sent claim cannot trigger F03',()=>{
 good(run(closed(),ev('LAB_HUMAN_MESSAGE_SENT_CLAIM')),'LAB_POST_CLOSURE_HOLD');
});
test('M21-17 inbound even after 24h meta-window closed routes human',()=>{
 const s=good(run({...c(),meta_window_claim:'LAB_CLOSED'}),
  'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED');
 assert.equal(s.f03_requires_explicit_human_closure,true);
});
test('M21-18 unknown Meta window never equals F03 cutoff',()=>{
 const s=good(run({...c(),meta_window_claim:'LAB_UNKNOWN'}),
  'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED');
 assert.equal(s.meta_window_is_not_f03_cutoff,true);
});
test('M21-19 opt-out does not authorize F01 revival',()=>{
 good(run({...c(),opt_out_claim:true}),'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED');
});
test('M21-20 inbound after opt-out does not create opt-in proof',()=>{
 const s=good(run({...c(),opt_out_claim:true}),
 'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED');
 assert.equal(s.graph_dispatch_authorized,false);
});
test('M21-21 F03 closure request without closure_ref rejected',()=>{
 const e=ev('LAB_HUMAN_CLOSURE_EXPLICIT');e.closure_ref=null;
 denied(run(closed(),e),'INVALID_INPUT');
});
test('M21-22 closure actor absent rejected',()=>{
 const e=ev('LAB_HUMAN_CLOSURE_EXPLICIT');e.actor_ref=null;
 denied(run(closed(),e),'INVALID_INPUT');
});
test('M21-23 closure actor must be a human role',()=>{
 const e=ev('LAB_HUMAN_CLOSURE_EXPLICIT');e.actor_role='F01';
 denied(run(closed(),e),'INVALID_INPUT');
});
test('M21-24 closure cutoff cannot be after/earlier than closure event',()=>{
 const e=ev('LAB_HUMAN_CLOSURE_EXPLICIT');e.closure_cutoff_ms=NOW-1999;
 denied(run(closed(),e),'TIMELINE_INCOHERENT');
});
test('M21-25 cutoff before terminal handoff is forbidden',()=>{
 const e=ev('LAB_HUMAN_CLOSURE_EXPLICIT');e.closure_cutoff_ms=NOW-5000;
 e.event_at_ms=NOW-5000;
 denied(run(closed(),e),'TIMELINE_INCOHERENT');
});
test('M21-26 human role Gestor supported only as LAB claim',()=>{
 const e=ev('LAB_HUMAN_CLOSURE_EXPLICIT');e.actor_role='GESTOR';
 good(run(closed(),e),'LAB_F03_CUTOFF_CANDIDATE_UNVERIFIED');
});
test('M21-27 Diretor supported only as LAB claim',()=>{
 const e=ev('LAB_HUMAN_CLOSURE_EXPLICIT');e.actor_role='DIRETOR';
 good(run(closed(),e),'LAB_F03_CUTOFF_CANDIDATE_UNVERIFIED');
});
test('M21-28 impersonated closure fields on inbound rejected',()=>{
 const e=ev();e.actor_ref='HUMAN_A';
 denied(run(c(),e),'INVALID_INPUT');
});
test('M21-29 meta-window timeout with fake closure refused',()=>{
 const e=ev('LAB_META_WINDOW_TIMEOUT');e.closure_ref='FAKE_C';
 denied(run(closed(),e),'INVALID_INPUT');
});
test('M21-30 cross concessionaria denied',()=>{
 const e=ev();e.concessionaria_id='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
 denied(run(c(),e),'SCOPE_MISMATCH');
});
test('M21-31 cross WABA denied',()=>{
 const e=ev();e.waba_ref='WABA_B';denied(run(c(),e),'SCOPE_MISMATCH');
});
test('M21-32 cross App denied',()=>{
 const e=ev();e.app_ref='APP_B';denied(run(c(),e),'SCOPE_MISMATCH');
});
test('M21-33 cross phone denied',()=>{
 const e=ev();e.phone_number_id='10000002';
 denied(run(c(),e),'SCOPE_MISMATCH');
});
test('M21-34 cross case denied',()=>{
 const e=ev();e.case_ref='CASE_B';denied(run(c(),e),'SCOPE_MISMATCH');
});
test('M21-35 cross lead denied',()=>{
 const e=ev();e.lead_ref='LEAD_B';denied(run(c(),e),'SCOPE_MISMATCH');
});
test('M21-36 stale context denied',()=>{
 const v=c();v.observed_at_ms=NOW-60001;
 denied(run(v,ev()),'TIMELINE_INCOHERENT');
});
test('M21-37 future context denied',()=>{
 const v=c();v.observed_at_ms=NOW+1;
 denied(run(v,ev()),'TIMELINE_INCOHERENT');
});
test('M21-38 event after context observation denied',()=>{
 const e=ev();e.event_at_ms=NOW;
 denied(run(c(),e),'TIMELINE_INCOHERENT');
});
test('M21-39 caller cannot assert S0 source verified',()=>{
 const v=c();v.s0_source_authenticated=true;
 denied(run(v,ev()),'INVALID_INPUT');
});
test('M21-40 caller cannot assert S0 case authority verified',()=>{
 const v=c();v.case_authority_verified=true;
 denied(run(v,ev()),'INVALID_INPUT');
});
test('M21-41 caller cannot assert closure event authenticated',()=>{
 const e=ev('LAB_HUMAN_CLOSURE_EXPLICIT');e.s0_event_authenticated=true;
 denied(run(closed(),e),'INVALID_INPUT');
});
test('M21-42 caller cannot assert closure author verified',()=>{
 const e=ev('LAB_HUMAN_CLOSURE_EXPLICIT');e.human_closure_verified=true;
 denied(run(closed(),e),'INVALID_INPUT');
});
test('M21-43 unknown event kind cannot generate F03',()=>{
 const e=ev();e.event_kind='AUTO_CLOSURE';
 denied(run(closed(),e),'INVALID_INPUT');
});
test('M21-44 added commercial permission rejected',()=>{
 const e:any=ev();e.close_case=true;
 denied(run(closed(),e),'INVALID_INPUT');
});
test('M21-45 getter on event not executed',()=>{
 const e:any=ev();let calls=0;
 Object.defineProperty(e,'event_kind',{enumerable:true,get(){
  calls++;return 'LAB_INBOUND_MESSAGE';
 }});
 denied(run(c(),e),'INVALID_INPUT');assert.equal(calls,0);
});
test('M21-46 getter on S0 state not executed',()=>{
 const v:any=c();let calls=0;
 Object.defineProperty(v,'case_state',{enumerable:true,get(){
  calls++;return 'LAB_F01_ACTIVE';
 }});
 denied(run(v,ev()),'INVALID_INPUT');assert.equal(calls,0);
});
test('M21-47 stable recheck stays LAB-only',()=>{
 const s=good(run(c(),ev()),'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED');
 good(recheck(s,c(),ev()),'LAB_RECHECKED_UNVERIFIED');
});
test('M21-48 changed case revision rejects recheck',()=>{
 const s=good(run(c(),ev()),'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED');
 const v=c();v.case_revision++;
 denied(recheck(s,v,ev()),'CONTEXT_CHANGED');
});
test('M21-49 changed handoff revision rejects recheck',()=>{
 const s=good(run(c(),ev()),'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED');
 const v=c();v.handoff_revision++;
 denied(recheck(s,v,ev()),'CONTEXT_CHANGED');
});
test('M21-50 new closure cutoff revision rejects recheck',()=>{
 const s=good(run(closed(),ev('LAB_HUMAN_CLOSURE_EXPLICIT')),
  'LAB_F03_CUTOFF_CANDIDATE_UNVERIFIED');
 const v=closed();v.f03_cutoff_revision++;
 denied(recheck(s,v,ev('LAB_HUMAN_CLOSURE_EXPLICIT')),'CONTEXT_CHANGED');
});
test('M21-51 forged old permission is denied',()=>{
 const s=good(run(c(),ev()),'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED');
 denied(recheck({...s,f01_invocation_authorized:true},c(),ev()),
  'PREVIOUS_INVALID');
});
test('M21-52 old hash changes on altered event',()=>{
 const s=good(run(c(),ev()),'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED');
 const e=ev();e.event_digest='b'.repeat(64);
 denied(recheck(s,c(),e),'CONTEXT_CHANGED');
});
test('M21-53 old snapshot corrupted version denied',()=>{
 const s=good(run(c(),ev()),'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED');
 denied(recheck({...s,contract_version:'wa21-human-handoff-snapshot.lab.v0.0'},
  c(),ev()),'PREVIOUS_INVALID');
});
test('M21-54 S0 LAB cutoffs never open commercial C09',()=>{
 const s=good(run(closed(),ev('LAB_HUMAN_CLOSURE_EXPLICIT')),
  'LAB_F03_CUTOFF_CANDIDATE_UNVERIFIED');
 assert.equal(s.c09_window_authorized,false);
 assert.equal(s.f03_invocation_authorized,false);
});


test('M21-55 historical inbound before terminal handoff cannot be rerouted',()=>{
 const e=ev();e.event_at_ms=NOW-5000;
 const s=good(run(c(),e),'LAB_PRE_HANDOFF_EVENT_HOLD');
 assert.equal(s.f01_resume_denied,true);
});
test('M21-56 historical Meta timeout before handoff stays held',()=>{
 const e=ev('LAB_META_WINDOW_TIMEOUT');e.event_at_ms=NOW-5000;
 good(run(c(),e),'LAB_PRE_HANDOFF_EVENT_HOLD');
});
test('M21-57 event exactly at handoff is routed human in LAB',()=>{
 const e=ev();e.event_at_ms=NOW-4000;
 good(run(c(),e),'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED');
});
test('M21-58 pre-handoff inbound on closed case cannot trigger F03',()=>{
 const e=ev();e.event_at_ms=NOW-5000;
 good(run(closed(),e),'LAB_PRE_HANDOFF_EVENT_HOLD');
});
test('M21-59 changed historical timestamp invalidates recheck',()=>{
 const e=ev();e.event_at_ms=NOW-5000;
 const s=good(run(c(),e),'LAB_PRE_HANDOFF_EVENT_HOLD');
 const newer={...e,event_at_ms:NOW-6000};
 denied(recheck(s,c(),newer),'CONTEXT_CHANGED');
});
test('M21-60 claims of human handoff never prove Meta sent',()=>{
 const s=good(run(c(),ev('LAB_HUMAN_MESSAGE_SENT_CLAIM')),
 'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED');
 assert.equal(s.graph_dispatch_authorized,false);
 assert.equal(s.human_dispatch_authorized,false);
});
