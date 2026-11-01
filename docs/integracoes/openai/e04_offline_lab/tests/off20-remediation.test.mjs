import test from 'node:test';
import assert from 'node:assert/strict';
import {onlyKeys,validateF01,validateF02,prepareF03History,validateF03Proposal} from '../core.mjs';
import {inspectResponsesShape,OAI_RESPONSE_LAB_INPUT,OAI_RESPONSE_LAB_RESULT}
  from '../responses-shape-preflight-lab.mjs';
import {F01_RESPONSE} from '../f01-sales-boundary.mjs';
import {F02_RESPONSE} from '../f02-plan-boundary.mjs';
import {F03_PROPOSAL_SCHEMA} from '../f03-history-boundary.mjs';

const versions=()=>({case:1,cycle:3,form:1,catalog:1,assignment:7});
const scope=()=>({authenticated:true,authorized:true,tenantAllowed:true,storeId:'A',caseId:'K',expected:versions(),current:versions()});
const f01=()=>({scope:scope(),owner:'ai',handoff:false,humanized:false,nowMs:2000,
 sources:[{id:'S',storeId:'A',approved:true,active:true,mode:'current',validUntil:'1970-01-01T00:00:03Z'}]});
const reply=()=>({text:'Resposta sintética',sourceIds:['S'],commercial:true,modality:'text'});
const f02=()=>({scope:scope(),explicitS0Request:true,optOut:false,handoffPlanReuse:false,
 ownerRoute:'human',purpose:'post_human',windowStart:'2026-11-01T10:00:00Z',
 windowEnd:'2026-11-02T10:00:00Z',maxAttempts:0,
 allowedTemplates:[{id:'T',version:'v1',storeId:'A',purpose:'post_human',active:true}]});
const f03=()=>({scope:scope(),humanClosed:true,closureAuthenticated:true,closureId:'closed',
 personId:'P',cutoffSequence:10,
 records:[{id:'M1',storeId:'A',personId:'P',caseId:'K',sequence:1,
 author:'customer',kind:'text',available:true,contentAuthorized:true}],
 catalog:[],verifiedWithdrawalSourceIds:[]});
const input=(operation,raw)=>({
 schemaVersion:OAI_RESPONSE_LAB_INPUT,operation,providerTag:'tag1',
 modelRef:'test_model',startedAtMs:100,observedAtMs:110,deadlineMs:200,
 response:{id:'response1',model:'test_model',status:'completed',
  output:[{type:'message',role:'assistant',status:'completed',
   content:[{type:'output_text',text:raw}]}],error:null,incomplete_details:null}
});
const positive=(kind,version)=>{
 const raw=JSON.stringify({schemaVersion:version,providerTag:'tag1',
  note:'confidential canary never send',state:'completed',output:{}});
 const out=inspectResponsesShape(input(kind,raw));
 assert.equal(out.status,'UNTRUSTED_JSON_CANDIDATE');
 assert.equal(out.schemaVersion,OAI_RESPONSE_LAB_RESULT);
 assert.equal(out.candidateRawExposed,false);
 assert.equal(out.requiresDomainEvaluation,true);
 assert.equal(out.publishAuthorized,false);
 assert.equal(out.productionAuthorized,false);
 assert.equal(Object.hasOwn(out,'candidateRaw'),false);
 assert.equal(JSON.stringify(out).includes('confidential canary'),false);
 return out;
};
test('OFF20-01 F01 positive preflight never exposes raw content',()=>positive('F01',F01_RESPONSE));
test('OFF20-02 F02 positive preflight never exposes raw content',()=>positive('F02',F02_RESPONSE));
test('OFF20-03 F03 positive preflight never exposes raw content',()=>positive('F03',F03_PROPOSAL_SCHEMA));
test('OFF20-04 legacy shape rejects own accessor without reading it',()=>{
 let called=0;const q={x:1};Object.defineProperty(q,'y',{enumerable:true,get(){called++;return 2;}});
 assert.equal(onlyKeys(q,['x','y']),false);assert.equal(called,0);
});
test('OFF20-05 legacy shape rejects inherited key on custom prototype',()=>{
 const q=Object.assign(Object.create({x:1}),{y:2});
 assert.equal(onlyKeys(q,['x','y']),false);
});
test('OFF20-06 legacy shape rejects symbol property',()=>{
 const q={x:1};q[Symbol('hidden')]=1;
 assert.equal(onlyKeys(q,['x']),false);
});
test('OFF20-07 legacy shape rejects array masquerading as record',()=>{
 assert.equal(onlyKeys([1],['0']),false);
});
test('OFF20-08 legacy shape preserves simple own-property records',()=>{
 assert.equal(onlyKeys({x:1},['x','y']),true);
});
test('OFF20-09 F01 request owner accessor is never invoked',()=>{
 const q=f01();let called=0;
 Object.defineProperty(q,'owner',{get(){called++;throw Error('unexpected');}});
 assert.equal(validateF01(q,reply()).status,'INVALID_INPUT');assert.equal(called,0);
});
test('OFF20-10 F01 source expiry getter is never invoked',()=>{
 const q=f01();let called=0;
 Object.defineProperty(q.sources[0],'validUntil',{get(){called++;throw Error('unexpected');}});
 assert.equal(validateF01(q,reply()).status,'INVALID_INPUT');assert.equal(called,0);
});
test('OFF20-11 F01 prototype altered nested source denied',()=>{
 const q=f01();Object.setPrototypeOf(q.sources[0],{approved:true});
 assert.equal(validateF01(q,reply()).status,'INVALID_INPUT');
});
test('OFF20-12 F01 cyclic request denied',()=>{
 const q=f01();q.loop=q;
 assert.equal(validateF01(q,reply()).status,'INVALID_INPUT');
});
test('OFF20-13 F01 malicious response getter is never invoked',()=>{
 const p=reply();let called=0;
 Object.defineProperty(p,'commercial',{get(){called++;throw Error('unexpected');}});
 assert.equal(validateF01(f01(),p).status,'SCHEMA_INVALID');assert.equal(called,0);
});
test('OFF20-14 F02 purpose getter denied before business rules',()=>{
 const q=f02();let called=0;
 Object.defineProperty(q,'purpose',{get(){called++;throw Error('unexpected');}});
 assert.equal(validateF02(q,{attempts:[],finalTemplate:null}).status,'INVALID_INPUT');assert.equal(called,0);
});
test('OFF20-15 F02 malformed/sparse proposal array denied',()=>{
 const p={attempts:new Array(2),finalTemplate:null};p.attempts[0]={};
 assert.equal(validateF02(f02(),p).status,'SCHEMA_INVALID');
});
test('OFF20-16 F02 nested template getter denied',()=>{
 const q=f02();let called=0;
 Object.defineProperty(q.allowedTemplates[0],'version',{get(){called++;throw Error('unexpected');}});
 assert.equal(validateF02(q,{attempts:[],finalTemplate:null}).status,'INVALID_INPUT');assert.equal(called,0);
});
test('OFF20-17 F02 clean synthetic request still returns proposal only',()=>{
 assert.equal(validateF02(f02(),{attempts:[],finalTemplate:null}).status,'PROPOSED');
});
test('OFF20-18 F03 records getter denied before extraction',()=>{
 const q=f03();let called=0;
 Object.defineProperty(q,'records',{get(){called++;throw Error('unexpected');}});
 assert.equal(prepareF03History(q).status,'INVALID_INPUT');assert.equal(called,0);
});
test('OFF20-19 F03 nested record getter denied',()=>{
 const q=f03();let called=0;
 Object.defineProperty(q.records[0],'available',{get(){called++;throw Error('unexpected');}});
 assert.equal(prepareF03History(q).status,'INVALID_INPUT');assert.equal(called,0);
});
test('OFF20-20 F03 proposal getter denied before inspection',()=>{
 const q=f03(),s=prepareF03History(q);
 assert.equal(s.status,'READY');
 const p={fields:[],conflicts:[],commercialAdvisory:null};let called=0;
 Object.defineProperty(p,'fields',{get(){called++;throw Error('unexpected');}});
 assert.equal(validateF03Proposal(q,s,p).status,'SCHEMA_INVALID');assert.equal(called,0);
});
test('OFF20-21 F03 snapshot with untrusted prototype denied',()=>{
 const q=f03(),s=prepareF03History(q);
 Object.setPrototypeOf(s,{private:true});
 assert.equal(validateF03Proposal(q,s,{fields:[],conflicts:[],commercialAdvisory:null}).status,'INVALID_INPUT');
});
test('OFF20-22 F03 clean synthetic prepared history still proposes only',()=>{
 const q=f03(),s=prepareF03History(q);
 assert.equal(s.status,'READY');
 assert.equal(validateF03Proposal(q,s,{fields:[],conflicts:[],commercialAdvisory:null}).status,'PROPOSED');
});
