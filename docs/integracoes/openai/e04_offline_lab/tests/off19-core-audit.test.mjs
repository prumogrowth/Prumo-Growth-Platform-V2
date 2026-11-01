import test from 'node:test';
import assert from 'node:assert/strict';
import {versionGate,validateF01,validateF02,prepareF03History} from '../core.mjs';
const scope=()=>({
  authenticated:true,authorized:true,tenantAllowed:true,storeId:'shopA',caseId:'caseA',
  expected:{case:1,cycle:3,form:1,catalog:1,assignment:7,policy:2},
  current:{case:1,cycle:3,form:1,catalog:1,assignment:7,policy:2}
});
const req=()=>({
  scope:scope(),owner:'ai',handoff:false,humanized:false,nowMs:2000,
  sources:[{id:'src',storeId:'shopA',approved:true,active:true,mode:'current',validUntil:'1970-01-01T00:00:03Z'}]
});
const response=()=>({
  text:'Valor sujeito a confirmacao oficial.',sourceIds:['src'],
  commercial:true,modality:'text'
});
const f02=()=>({
  scope:scope(),explicitS0Request:true,optOut:false,handoffPlanReuse:false,
  ownerRoute:'human',purpose:'post_human',maxAttempts:0,
  windowStart:'2026-11-01T10:00:00Z',windowEnd:'2026-11-02T10:00:00Z',
  allowedTemplates:[{id:'t',version:'v1',storeId:'shopA',purpose:'post_human',active:true}]
});
const f03=()=>({
  scope:scope(),humanClosed:true,closureAuthenticated:true,closureId:'closure',
  personId:'personA',cutoffSequence:1,records:[],catalog:[],verifiedWithdrawalSourceIds:[]
});
test('OFF19-01 ordinary own versions independently cycle and assignment accepted',()=>{
  assert.equal(versionGate(scope()).status,'READY');
});
test('OFF19-02 value drift correctly marked stale',()=>{
  const s=scope();s.current.assignment=8;
  assert.equal(versionGate(s).status,'STALE');
});
test('OFF19-03 inherited case version cannot impersonate owned key',()=>{
  const s=scope();s.current=Object.create({case:1});
  for(const k of ['cycle','form','catalog','assignment','policy'])s.current[k]=s.expected[k];
  s.current.noise=33;
  assert.equal(versionGate(s).status,'INVALID_INPUT');
});
test('OFF19-04 same-count unexpected current key rejected',()=>{
  const s=scope();delete s.current.case;s.current.noise=1;
  assert.equal(versionGate(s).status,'INVALID_INPUT');
});
test('OFF19-05 inherited caller authentication cannot authorize',()=>{
  const s=scope();delete s.authenticated;
  Object.setPrototypeOf(s,{authenticated:true});
  assert.equal(versionGate(s).status,'DENIED');
});
test('OFF19-06 inherited expected version on custom prototype denied',()=>{
  const s=scope();s.expected=Object.assign(Object.create({evil:true}),s.expected);
  assert.equal(versionGate(s).status,'INVALID_INPUT');
});
test('OFF19-07 accessor for expected revision never invoked',()=>{
  const s=scope();let count=0;
  Object.defineProperty(s.expected,'case',{enumerable:true,get(){count++;return 1;}});
  assert.equal(versionGate(s).status,'INVALID_INPUT');assert.equal(count,0);
});
test('OFF19-08 accessor for current revision never invoked',()=>{
  const s=scope();let count=0;
  Object.defineProperty(s.current,'case',{enumerable:true,get(){count++;return 1;}});
  assert.equal(versionGate(s).status,'INVALID_INPUT');assert.equal(count,0);
});
test('OFF19-09 accessor for grant never invoked',()=>{
  const s=scope();let count=0;
  Object.defineProperty(s,'authorized',{enumerable:true,get(){count++;return true;}});
  assert.equal(versionGate(s).status,'DENIED');assert.equal(count,0);
});
test('OFF19-10 accessor for current object never invoked',()=>{
  const s=scope();let count=0;
  Object.defineProperty(s,'current',{enumerable:true,get(){count++;return scope().current;}});
  assert.equal(versionGate(s).status,'INVALID_INPUT');assert.equal(count,0);
});
test('OFF19-11 symbol property on revision map denied',()=>{
  const s=scope();s.expected[Symbol('unsafe')]=1;
  assert.equal(versionGate(s).status,'INVALID_INPUT');
});
test('OFF19-12 null prototype maps with all OWN keys remain valid',()=>{
  const s=scope();s.expected=Object.assign(Object.create(null),s.expected);
  s.current=Object.assign(Object.create(null),s.current);
  assert.equal(versionGate(s).status,'READY');
});
test('OFF19-13 missing S0 time with expiring source fails closed',()=>{
  const q=req();delete q.nowMs;
  assert.equal(validateF01(q,response()).status,'INVALID_INPUT');
});
test('OFF19-14 expiring source with invalid S0 time fails closed',()=>{
  const q=req();q.nowMs=-1;
  assert.equal(validateF01(q,response()).status,'INVALID_INPUT');
});
test('OFF19-15 expiration uses caller supplied S0 time deterministically',()=>{
  const q=req();q.nowMs=3000;
  assert.equal(validateF01(q,response()).status,'SOURCE_INVALID');
});
test('OFF19-16 valid offer relative to caller S0 time remains a draft only',()=>{
  assert.equal(validateF01(req(),response()).status,'PROPOSED');
});
test('OFF19-17 invalid version source propagates to F02 without scheduling',()=>{
  const q=f02();q.scope.current=Object.create({cycle:3});
  for(const k of ['case','form','catalog','assignment','policy'])q.scope.current[k]=q.scope.expected[k];
  q.scope.current.noise=1;
  assert.equal(validateF02(q,{attempts:[],finalTemplate:null}).status,'INVALID_INPUT');
});
test('OFF19-18 invalid version source propagates to F03 without extraction',()=>{
  const q=f03();q.scope.current=Object.create({cycle:3});
  for(const k of ['case','form','catalog','assignment','policy'])q.scope.current[k]=q.scope.expected[k];
  q.scope.current.noise=1;
  assert.equal(prepareF03History(q).status,'INVALID_INPUT');
});
