import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire,syncBuiltinESMExports} from 'node:module';
const require=createRequire(import.meta.url);
const fs=require('node:fs');
const cp=require('node:child_process');
import * as mod from '../f03-history-boundary.mjs';
const {
  F03_HISTORY_SCHEMA,F03_PROVIDER_SCHEMA,F03_PROPOSAL_SCHEMA,
  prepareF03History,projectF03History,reviewF03Extraction,auditF03History
}=mod;
const clone=x=>structuredClone(x);
const versions=()=>Object.fromEntries(['case','cycle','form','catalog','assignment','identity','policy'].map(x=>[x,1]));
const fixture=()=>({
  schemaVersion:F03_HISTORY_SCHEMA,requestId:'req1',providerTag:'opaque_attempt_A',
  scope:{authenticated:true,authorized:true,tenantAllowed:true,
    storeId:'storeA',personId:'personA',caseId:'case2',closureId:'closure2',
    humanClosed:true,closureAuthenticated:true,identityAttested:true,historyCompletenessAttested:true,
    expectedVersions:versions(),currentVersions:versions()},
  privacy:{modelContentAuthorized:true,dataMinimized:true},
  cutoff:{sequence:5,closedAt:'2026-10-31T09:00:00Z',eventId:'closed-event'},
  cases:[{id:'case1',storeId:'storeA',personId:'personA',s0IdentityBound:true},
         {id:'case2',storeId:'storeA',personId:'personA',s0IdentityBound:true}],
  catalog:[{code:'name',type:'string',essential:true},{code:'income',type:'number',essential:false}],
  records:[
    {id:'r1',caseId:'case1',storeId:'storeA',personId:'personA',sequence:1,
     at:'2026-10-31T08:00:00Z',authorClass:'customer',kind:'text',
     available:true,contentAuthorized:true,content:'Nome de exemplo, sem dados reais.',
     claims:[{id:'cl1',code:'name',value:'Example',explicit:true}]},
    {id:'r2',caseId:'case2',storeId:'storeA',personId:'personA',sequence:2,
     at:'2026-10-31T08:15:00Z',authorClass:'customer',kind:'media',
     available:false,contentAuthorized:false,content:'',claims:[]},
    {id:'r3',caseId:'case2',storeId:'storeA',personId:'personA',sequence:3,
     at:'2026-10-31T08:20:00Z',authorClass:'human',kind:'text',
     available:true,contentAuthorized:true,content:'Renda fictícia para teste.',
     claims:[{id:'cl3',code:'income',value:1000,explicit:true}]},
    {id:'r4',caseId:'case2',storeId:'storeA',personId:'personA',sequence:9,
     at:'2026-10-31T10:00:00Z',authorClass:'customer',kind:'text',
     available:true,contentAuthorized:true,content:'LATE_SECRET_AFTER_CUTOFF',
     claims:[{id:'cl4',code:'name',value:'Late Example',explicit:true}]}
  ]
});
const proposal=()=>({schemaVersion:F03_PROPOSAL_SCHEMA,providerTag:'opaque_attempt_A',
  fields:[{code:'name',value:'Example',sourceAliases:['src_001']},
          {code:'income',value:1000,sourceAliases:['src_003']}],
  missingFields:[],conflicts:[],commercialAdvisory:null,followupAdvisory:'none'});
const prep=(request=fixture())=>{
  const x=prepareF03History(request);assert.equal(x.status,'READY',JSON.stringify(x));return x;
};
const invalid=(mutate,status='INVALID_INPUT')=>{
  const x=fixture();mutate(x);const r=prepareF03History(x);assert.equal(r.status,status,JSON.stringify(r));return r;
};
const badProposal=(mutate,status='SCHEMA_INVALID')=>{
  const r=proposal();mutate(r);const out=reviewF03Extraction(prep(),r);assert.equal(out.status,status,JSON.stringify(out));return out;
};

test('OFF03 baseline positive remains S0 recheck only, no APPLIED',()=>{
  const r=reviewF03Extraction(prep(),proposal());
  assert.equal(r.status,'PROPOSED');assert.equal(r.stage,'S0_RECHECK_ONLY');
  assert.deepEqual(r.privateCandidate.fields.map(x=>x.code),['name','income']);
  assert.equal(r.privateCandidate.assurance.applied,false);
  assert.equal(r.privateCandidate.assurance.semanticVerified,false);
  assert.equal(r.privateCandidate.assurance.historyCompletenessProved,false);
});
test('OFF03 public projection strips private identities and late content',()=>{
  const payload=projectF03History(prep());
  assert.equal(payload.schemaVersion,F03_PROVIDER_SCHEMA);
  assert.deepEqual(payload.evidence.map(x=>x.alias),['src_001','src_003']);
  assert.equal(payload.unavailableEvidenceCount,1);
  const json=JSON.stringify(payload);
  for(const forbidden of ['storeA','personA','case1','case2','closure2','req1','LATE_SECRET_AFTER_CUTOFF','cl1'])
    assert.equal(json.includes(forbidden),false,forbidden);
});
test('OFF03 multiple historical cases of same tenant and person can contribute',()=>{
  const p=prep(),r=reviewF03Extraction(p,proposal());
  assert.equal(r.status,'PROPOSED');
  assert.deepEqual(r.privateCandidate.fields.map(f=>f.recordIds[0]),['r1','r3']);
});
test('OFF03 immutable copy: mutating fixture after prepare does not change projection',()=>{
  const f=fixture(),p=prep(f);
  f.records[0].content='CHANGED';f.scope.currentVersions.form=99;
  assert.equal(projectF03History(p).evidence[0].content,'Nome de exemplo, sem dados reais.');
  assert.equal(reviewF03Extraction(p,proposal()).status,'PROPOSED');
});
test('OFF03 private issued context cannot be forged using spread',()=>{
  const p=prep();const fake={status:'READY',privateContext:{...p.privateContext}};
  assert.equal(projectF03History(fake).status,'INVALID_INPUT');
  assert.equal(reviewF03Extraction(fake,proposal()).status,'DENIED');
});
test('OFF03 frozen private context cannot be modified',()=>{
  const p=prep();assert.equal(Object.isFrozen(p.privateContext.snapshot.records[0].claims),true);
  assert.throws(()=>{p.privateContext.snapshot.records[0].content='modified';},TypeError);
});
for(const [name,fn] of [
  ['no authentication',x=>x.scope.authenticated=false],
  ['no authorization',x=>x.scope.authorized=false],
  ['wrong tenant grant',x=>x.scope.tenantAllowed=false],
  ['missing scope',x=>delete x.scope],
])test(`OFF03 denied before identity and stale disclosure: ${name}`,()=>{
  const x=fixture();fn(x);assert.equal(prepareF03History(x).status,'DENIED');
});
test('OFF03 revoked and stale input returns DENIED before STALE',()=>{
  const x=fixture();x.scope.currentVersions.case=2;x.scope.authorized=false;
  assert.equal(prepareF03History(x).status,'DENIED');
});
test('OFF03 version stale preserves domain distinctions',()=>invalid(x=>x.scope.currentVersions.form=2,'STALE'));
for(const k of ['case','cycle','form','catalog','assignment','identity','policy'])
  test(`OFF03 independent ${k} version mismatch`,()=>invalid(x=>x.scope.currentVersions[k]=2,'STALE'));
for(const [name,fn] of [
  ['incorrect schema',x=>x.schemaVersion='new'],
  ['unexpected root field',x=>x.authorized=true],
  ['extra scope field',x=>x.scope.hmac='secret'],
  ['missing human closure',x=>x.scope.humanClosed=false],
  ['untrusted closure',x=>x.scope.closureAuthenticated=false],
  ['untrusted person binding',x=>x.scope.identityAttested=false],
  ['incomplete history asserted',x=>x.scope.historyCompletenessAttested=false],
  ['content authorization missing',x=>x.privacy.modelContentAuthorized=false],
  ['minimization missing',x=>x.privacy.dataMinimized=false],
  ['no current case in coverage',x=>x.cases=x.cases.slice(0,1)],
  ['wrong tenant in case',x=>x.cases[0].storeId='storeB'],
  ['wrong person in case',x=>x.cases[0].personId='personB'],
  ['wrong tenant record',x=>x.records[0].storeId='storeB'],
  ['wrong person record',x=>x.records[0].personId='personB'],
  ['unlisted case',x=>x.records[0].caseId='case999'],
  ['unattested case',x=>x.cases[0].s0IdentityBound=false],
  ['duplicate case ID',x=>x.cases.push(clone(x.cases[0]))],
  ['duplicate record ID',x=>x.records.push(clone(x.records[0]))],
  ['same global sequence',x=>x.records[1].sequence=x.records[0].sequence],
  ['media without bytes',x=>{x.records[1].available=true;x.records[1].contentAuthorized=true;}],
  ['unavailable media with content',x=>x.records[1].content='invented'],
  ['available media without grant',x=>x.records[0].contentAuthorized=false],
  ['timestamp later than closure but within cutoff',x=>x.records[2].at='2026-10-31T10:00:00Z'],
  ['unexpected code type',x=>x.records[2].claims[0].value='1000'],
  ['duplicate claim ID',x=>x.records[2].claims[0].id='cl1'],
  ['invented bank field',x=>x.catalog.push({code:'sold',type:'object',essential:true})],
  ['embedded token field',x=>x.records[0].accessToken='secret'],
  ['unauthorized extra claim code',x=>x.records[0].claims.push({id:'z1',code:'credit_limit',value:6000,explicit:true})],
  ['withdrawal is not a free-form string',x=>x.records[0].claims.push({id:'z2',code:'customer_withdrawal',value:'yes',explicit:true})],
  ['unavailable evidence cannot carry claims',x=>x.records[1].claims.push({id:'z3',code:'name',value:'Leak',explicit:true})],
  ['nested tool command',x=>x.records[0].claims[0].sql='UPDATE'],
  ['non-finite value',x=>x.records[2].claims[0].value=Infinity],
  ['correction refers to nonexistent claim',x=>Object.assign(x.records[2].claims[0],{corrects:'cl404',s0CorrectionAttested:true})],
  ['correction without S0 attestation',x=>Object.assign(x.records[2].claims[0],{corrects:'cl1'})],
])test(`OFF03 reject invalid history fixture: ${name}`,()=>invalid(fn));
test('OFF03 reject getter without executing it',()=>{
  let touched=false;const x=fixture();
  Object.defineProperty(x.records[0],'danger',{get(){touched=true;throw Error('leak');},enumerable:true});
  assert.equal(prepareF03History(x).status,'INVALID_INPUT');assert.equal(touched,false);
});
test('OFF03 reject arrays with holes',()=>invalid(x=>{x.records=new Array(4);x.records[0]=fixture().records[0];}));
test('OFF03 reject prototype pollution even if JSON otherwise parses',()=>{
  const x=fixture();Object.defineProperty(x.scope,'__proto__',{value:{admin:true},enumerable:true});
  assert.equal(prepareF03History(x).status,'INVALID_INPUT');
});
for(const [name,fn,status] of [
  ['extra model key',p=>p.writes=true,'SCHEMA_INVALID'],
  ['sold status payload',p=>p.sold=true,'SCHEMA_INVALID'],
  ['duplicate field',p=>p.fields.push(clone(p.fields[0])),'SCHEMA_INVALID'],
  ['unknown field',p=>p.fields[0].code='unknown','SOURCE_INVALID'],
  ['future alias',p=>p.fields[0].sourceAliases=['src_004'],'SOURCE_INVALID'],
  ['unavailable alias',p=>p.fields[0].sourceAliases=['src_002'],'SOURCE_INVALID'],
  ['field without cited explicit claim',p=>p.fields[0].value='Fabricated','SOURCE_INVALID'],
  ['declared number as string',p=>p.fields[1].value='1000','SOURCE_INVALID'],
  ['field without sources',p=>p.fields[0].sourceAliases=[],'SOURCE_INVALID'],
  ['duplicate source',p=>p.fields[0].sourceAliases=['src_001','src_001'],'SOURCE_INVALID'],
  ['wrong final status',p=>p.followupAdvisory='send','SCHEMA_INVALID'],
  ['unknown missing',p=>p.missingFields=['fake'],'SCHEMA_INVALID'],
  ['missing includes existing',p=>p.missingFields=['name'],'SCHEMA_INVALID'],
  ['unknown advisory',p=>p.commercialAdvisory={kind:'vendido',sourceAliases:['src_001']},'SOURCE_INVALID'],
  ['unproved lost advisory',p=>p.commercialAdvisory={kind:'perdido',sourceAliases:['src_001']},'SOURCE_INVALID'],
  ['provider tool calls',p=>p.tool_calls=[{name:'update'}],'SCHEMA_INVALID'],
])test(`OFF03 reject model output: ${name}`,()=>badProposal(fn,status));
test('OFF03 json parser rejects duplicate key including escaped alias',()=>{
  const p=JSON.stringify(proposal());
  assert.equal(reviewF03Extraction(prep(),p.replace('{','{"schemaVersion":"other",')).status,'SCHEMA_INVALID');
  assert.equal(reviewF03Extraction(prep(),p.replace('{','{"schema\\u0056ersion":"other",')).status,'SCHEMA_INVALID');
});
test('OFF03 output may omit optional but not essential fields',()=>{
  const p=proposal();p.fields.pop();p.missingFields=['income'];
  assert.equal(reviewF03Extraction(prep(),p).status,'PROPOSED');
});
test('OFF03 missing essential field mandates review, never automated filling',()=>{
  const p=proposal();p.fields.shift();p.missingFields=['name'];
  const x=reviewF03Extraction(prep(),p);assert.equal(x.status,'REVIEW_REQUIRED');
  assert.deepEqual(x.reasons,['ESSENTIAL_MISSING']);
});
test('OFF03 missing essential without explicit missing field is invalid',()=>{
  const p=proposal();p.fields.shift();assert.equal(reviewF03Extraction(prep(),p).status,'SCHEMA_INVALID');
});
test('OFF03 actual historical contradiction cannot be concealed by model',()=>{
  const x=fixture();x.records[2].claims.push({id:'cl5',code:'name',value:'Another Example',explicit:true});
  const o=reviewF03Extraction(prep(x),proposal());assert.equal(o.status,'REVIEW_REQUIRED');
  assert.equal(o.stage,'HISTORY_CONFLICT');
});
test('OFF03 independent conflict without a selected field triggers human review',()=>{
  const x=fixture();x.records[2].claims.push({id:'cl5',code:'income',value:2000,explicit:true});
  const p=proposal();p.fields=p.fields.slice(0,1);p.missingFields=['income'];
  const o=reviewF03Extraction(prep(x),p);assert.equal(o.status,'REVIEW_REQUIRED');
  assert.ok(o.reasons.includes('HISTORICAL_CONFLICT'));
});
test('OFF03 independent identical claims are not a conflict',()=>{
  const x=fixture();x.records[2].claims.push({id:'cl5',code:'name',value:'Example',explicit:true});
  assert.equal(reviewF03Extraction(prep(x),proposal()).status,'PROPOSED');
});
test('OFF03 explicit S0-attested correction chain is a candidate, never semantic proof',()=>{
  const x=fixture();x.records[2].claims.push({id:'cl5',code:'name',value:'Corrected',explicit:true,
    corrects:'cl1',s0CorrectionAttested:true});
  const p=proposal();p.fields[0]={code:'name',value:'Corrected',sourceAliases:['src_003']};
  const o=reviewF03Extraction(prep(x),p);assert.equal(o.status,'PROPOSED');
  assert.equal(o.privateCandidate.assurance.correctionProved,false);
});
test('OFF03 correction fork is refused',()=>invalid(x=>{
  x.records[2].claims.push({id:'cl5',code:'name',value:'B',explicit:true,corrects:'cl1',s0CorrectionAttested:true});
  x.records[2].claims.push({id:'cl6',code:'name',value:'C',explicit:true,corrects:'cl1',s0CorrectionAttested:true});
}));
test('OFF03 correction targeting another field is refused',()=>invalid(x=>{
  Object.assign(x.records[2].claims[0],{corrects:'cl1',s0CorrectionAttested:true});
}));
test('OFF03 correction targeting later claim is refused',()=>invalid(x=>{
  Object.assign(x.records[0].claims[0],{corrects:'cl3',s0CorrectionAttested:true});
}));
test('OFF03 reported conflict returns REVIEW_REQUIRED even if content agrees',()=>{
  const p=proposal();p.conflicts=[{code:'name',sourceAliases:['src_001','src_003']}];
  const o=reviewF03Extraction(prep(),p);assert.equal(o.status,'REVIEW_REQUIRED');
  assert.ok(o.reasons.includes('DECLARED_CONFLICT'));
});
test('OFF03 commercial withdrawal advisory never triggers lost status',()=>{
  const x=fixture();x.records[0].claims.push({id:'withdrawal',code:'customer_withdrawal',value:true,explicit:true});
  const p=proposal();p.commercialAdvisory={kind:'perdido',sourceAliases:['src_001']};
  const o=reviewF03Extraction(prep(x),p);assert.equal(o.status,'REVIEW_REQUIRED');
  assert.equal(o.privateCandidate.commercialAdvisory.kind,'perdido');
  assert.equal(o.privateCandidate.assurance.applied,false);
});
test('OFF03 followup is advisory only, never F02 request',()=>{
  const p=proposal();p.followupAdvisory='consider';
  const o=reviewF03Extraction(prep(),p);assert.equal(o.status,'PROPOSED');
  assert.equal(o.privateCandidate.followupAdvisory,'consider');
  assert.equal('f02Request' in o.privateCandidate,false);
});
test('OFF03 revoked on S0 return takes precedence over stale',()=>{
  const x=prep(),s=clone(x.privateContext.snapshot.scope);s.authorized=false;s.currentVersions.form=2;
  assert.equal(reviewF03Extraction(x,proposal(),{currentScope:s}).status,'DENIED');
});
test('OFF03 cross-person scope on return cannot view proposals',()=>{
  const x=prep(),s=clone(x.privateContext.snapshot.scope);s.personId='other';
  assert.equal(reviewF03Extraction(x,proposal(),{currentScope:s}).status,'DENIED');
});
test('OFF03 stale form on return requires S0 recheck',()=>{
  const x=prep(),s=clone(x.privateContext.snapshot.scope);s.currentVersions.form=2;
  assert.equal(reviewF03Extraction(x,proposal(),{currentScope:s}).status,'STALE');
});
test('OFF03 stale identity on return requires recheck',()=>{
  const x=prep(),s=clone(x.privateContext.snapshot.scope);s.currentVersions.identity=2;
  assert.equal(reviewF03Extraction(x,proposal(),{currentScope:s}).status,'STALE');
});
test('OFF03 exact replay is candidate ALREADY_HANDLED only on supplied S0 fixture',()=>{
  const prior={requestId:'req1',closureId:'closure2',snapshotSequence:5,s0Verified:true};
  assert.equal(reviewF03Extraction(prep(),proposal(),{prior}).status,'ALREADY_HANDLED');
});
test('OFF03 conflicting replay is not authorized',()=>{
  const prior={requestId:'req1',closureId:'different',snapshotSequence:5,s0Verified:true};
  assert.equal(reviewF03Extraction(prep(),proposal(),{prior}).status,'REVIEW_REQUIRED');
});
test('OFF03 poisoned model return does not execute getters',()=>{
  let called=false;const p=proposal();Object.defineProperty(p,'tool',{enumerable:true,get(){called=true;throw Error('secret');}});
  assert.equal(reviewF03Extraction(prep(),p).status,'SCHEMA_INVALID');assert.equal(called,false);
});
test('OFF03 audit contains no PII or customer values',()=>{
  const out=reviewF03Extraction(prep(),proposal()),audit=auditF03History(out);
  assert.deepEqual(Object.keys(audit).sort(),['operation','schemaVersion','status']);
  for(const x of ['Example','personA','closure2','r1','1000'])assert.ok(!JSON.stringify(audit).includes(x));
});
test('OFF03 tripwire no filesystem, commands or network from the pure module',()=>{
  const original={read:fs.readFileSync,write:fs.writeFileSync,spawn:cp.spawnSync,fetch:globalThis.fetch};
  let calls=0;const trip=()=>{calls++;throw Error('IO_FORBIDDEN');};
  fs.readFileSync=trip;fs.writeFileSync=trip;cp.spawnSync=trip;syncBuiltinESMExports();globalThis.fetch=trip;
  try { const x=prep();projectF03History(x);reviewF03Extraction(x,proposal());assert.equal(calls,0); }
  finally {fs.readFileSync=original.read;fs.writeFileSync=original.write;cp.spawnSync=original.spawn;syncBuiltinESMExports();globalThis.fetch=original.fetch;}
});

// Audit of OFF-02/OFF-03 on 31/10: additional adversarial findings.
test('AUD-F03-01 every claimed source must support the exact field and value',()=>{
  const r=proposal();r.fields[0].sourceAliases.push('src_003'); // income evidence only
  const result=reviewF03Extraction(prep(),r);
  assert.equal(result.status,'SOURCE_INVALID');
});
test('AUD-F03-02 AI-authored statement cannot certify customer withdrawal',()=>{
  const f=fixture();f.records[0].authorClass='ai';
  f.records[0].claims.push({id:'withdraw1',code:'customer_withdrawal',value:true,explicit:true});
  const p=proposal();p.commercialAdvisory={kind:'perdido',sourceAliases:['src_001']};
  const result=reviewF03Extraction(prep(f),p);
  assert.equal(result.status,'SOURCE_INVALID');
  assert.equal(result.privateCandidate,undefined);
});
test('AUD-F03-03 corrected withdrawal cannot sustain obsolete lost advisory',()=>{
  const f=fixture();f.records[0].claims.push({id:'withdraw1',code:'customer_withdrawal',value:true,explicit:true});
  f.records[2].claims.push({id:'withdraw2',code:'customer_withdrawal',value:false,explicit:true,
    corrects:'withdraw1',s0CorrectionAttested:true});
  const p=proposal();p.commercialAdvisory={kind:'perdido',sourceAliases:['src_001']};
  const result=reviewF03Extraction(prep(f),p);
  assert.equal(result.status,'SOURCE_INVALID');
  assert.equal(result.privateCandidate,undefined);
});

test('AUD-F03-04 response from another operation cannot be attached to this history',()=>{
  const f=fixture();f.providerTag='opaque_attempt_B';
  assert.equal(projectF03History(prep(f)).providerTag,'opaque_attempt_B');
  const result=reviewF03Extraction(prep(f),proposal());
  assert.equal(result.status,'SCHEMA_INVALID');
});

// OFF-07 audit: an AI statement about a customer field is not a customer fact.
test('AUD-F03-100 AI-only evidence requires human review instead of PROPOSED',()=>{
  const f=fixture();f.records[0].authorClass='ai';
  const p=proposal();p.fields=p.fields.filter(x=>x.code==='name');p.missingFields=[];
  const r=reviewF03Extraction(prep(f),p);
  assert.equal(r.status,'REVIEW_REQUIRED');assert.equal(r.stage,'AUTHORSHIP');
  assert.equal(r.privateCandidate,undefined);
});

// OFF-08: a corrected citation cannot be laundered by adding the valid later source.
test('AUD-F03-101 corrected alias + current alias still rejects obsolete citation',()=>{
  const f=fixture();
  f.records[2].claims.push({id:'cl5',code:'name',value:'Example',explicit:true,
    corrects:'cl1',s0CorrectionAttested:true});
  const p=proposal();p.fields[0].sourceAliases=['src_001','src_003'];
  const o=reviewF03Extraction(prep(f),p);
  assert.equal(o.status,'SOURCE_INVALID');assert.equal(o.stage,'OBSOLETE_CITATION');
  p.fields[0].sourceAliases=['src_003'];
  assert.equal(reviewF03Extraction(prep(f),p).status,'PROPOSED');
});
