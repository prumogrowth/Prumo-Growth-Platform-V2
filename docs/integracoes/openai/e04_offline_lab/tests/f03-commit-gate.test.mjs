import test from 'node:test';
import assert from 'node:assert/strict';
import {evaluateF03CommitCandidate as gate} from '../f03-commit-gate.mjs';
const v=()=>({case:1,cycle:2,form:3,catalog:4,assignment:5,identity:6});
const fixture=()=>({
  scope:{authenticated:true,authorized:true,tenantAllowed:true,storeId:'A',personId:'P',caseId:'K2',closureId:'E2',requestId:'R1'},
  cutoff:{storeId:'A',personId:'P',closureId:'E2',s0ClosureVerified:true,historyComplete:true,snapshotRef:'snap2',watermark:20,
    expectedVersions:v(),sources:[
      {id:'old',storeId:'A',personId:'P',caseId:'K1',sequence:4,available:true,s0Verified:true,claims:[{code:'cor',value:'azul',explicit:true}]},
      {id:'new',storeId:'A',personId:'P',caseId:'K2',sequence:19,available:true,s0Verified:true,claims:[{code:'renda',value:3500,explicit:true},{code:'customer_withdrawal',value:true,explicit:true}]}
    ]},
  proposal:{proposalRef:'prop2',fields:[{code:'renda',value:3500,sourceId:'new'},{code:'cor',value:'azul',sourceId:'old'}],conflicts:[],advisory:null},
  catalog:[{code:'renda',essential:true},{code:'cor',essential:false}],
  current:{versions:v(),closureStillAuthorized:true,assignmentAuthorized:true,personScopeVerified:true},prior:null
});
const check=(s,mutate)=>{const x=fixture();mutate?.(x);assert.equal(gate(x).status,s);};
test('valid explicit multi-case fields require S0 recheck only',()=>{const x=gate(fixture());assert.deepEqual(x,{status:'S0_RECHECK_ONLY',fieldCodes:['cor','renda'],snapshotRef:'snap2'});});
test('authorization revocation hides stale versions',()=>check('DENIED',x=>{x.scope.authorized=false;x.current.versions.form=8;}));
test('tenant revocation hides history existence',()=>check('DENIED',x=>x.scope.tenantAllowed=false));
test('missing authentication is denied',()=>check('DENIED',x=>delete x.scope.authenticated));
test('different store fails before source lookup',()=>check('DENIED',x=>x.cutoff.storeId='B'));
test('different person fails before source lookup',()=>check('DENIED',x=>x.cutoff.personId='OTHER'));
test('different closure fails',()=>check('DENIED',x=>x.cutoff.closureId='E1'));
test('not human-closed cannot extract',()=>check('HISTORY_REVIEW_REQUIRED',x=>x.cutoff.s0ClosureVerified=false));
test('incomplete multi-case history blocks',()=>check('HISTORY_REVIEW_REQUIRED',x=>x.cutoff.historyComplete=false));
test('missing snapshot binding blocks',()=>check('HISTORY_REVIEW_REQUIRED',x=>x.cutoff.snapshotRef=''));
test('stale form blocks',()=>check('STALE',x=>x.current.versions.form++));
test('stale assignment blocks',()=>check('STALE',x=>x.current.versions.assignment++));
test('stale identity blocks',()=>check('STALE',x=>x.current.versions.identity++));
test('stale catalog blocks',()=>check('STALE',x=>x.current.versions.catalog++));
test('stale cycle blocks',()=>check('STALE',x=>x.current.versions.cycle++));
test('stale case blocks',()=>check('STALE',x=>x.current.versions.case++));
test('new customer inbound after cutoff does not itself change immutable snapshot',()=>{const x=fixture();x.current.latestInboundSequence=21;assert.equal(gate(x).status,'S0_RECHECK_ONLY');});
test('lost case rights blocks despite matching versions',()=>check('REVIEW_REQUIRED',x=>x.current.assignmentAuthorized=false));
test('invalid approval of identity blocks',()=>check('REVIEW_REQUIRED',x=>x.current.personScopeVerified=false));
test('retry same request and proven proposal is ALREADY_HANDLED',()=>{const x=fixture();x.prior={requestId:'R1',closureId:'E2',snapshotRef:'snap2',proposalRef:'prop2',s0Verified:true};assert.equal(gate(x).status,'ALREADY_HANDLED');});
test('replay with changed proposal cannot apply again',()=>check('REVIEW_REQUIRED',x=>x.prior={requestId:'R1',closureId:'E2',snapshotRef:'snap2',proposalRef:'other',s0Verified:true}));
test('forged prior receipt cannot prevent review',()=>check('REVIEW_REQUIRED',x=>x.prior={requestId:'R1',closureId:'E2',snapshotRef:'snap2',proposalRef:'prop2',s0Verified:false}));
test('cross-store evidence rejected',()=>check('SOURCE_INVALID',x=>x.cutoff.sources[0].storeId='B'));
test('cross-person evidence rejected',()=>check('SOURCE_INVALID',x=>x.cutoff.sources[0].personId='OTHER'));
test('historical prior case same store allowed',()=>check('S0_RECHECK_ONLY'));
test('future message beyond cutoff cannot be source',()=>check('SOURCE_INVALID',x=>x.cutoff.sources[1].sequence=21));
test('missing available media fails source',()=>check('SOURCE_INVALID',x=>x.cutoff.sources[1].available=false));
test('unverified source cannot serve evidence',()=>check('SOURCE_INVALID',x=>x.cutoff.sources[1].s0Verified=false));
test('invented value rejected even when source id is valid',()=>check('SOURCE_INVALID',x=>x.proposal.fields[0].value=4000));
test('nonexplicit claim cannot justify value',()=>check('SOURCE_INVALID',x=>x.cutoff.sources[1].claims[0].explicit=false));
test('noncatalogue field rejected',()=>check('SOURCE_INVALID',x=>x.proposal.fields[0].code='cpf'));
test('duplicate proposed field rejected',()=>check('SOURCE_INVALID',x=>x.proposal.fields.push({...x.proposal.fields[0]})));
test('required field missing routes to human',()=>check('HUMAN_REVIEW_REQUIRED',x=>x.proposal.fields.shift()));
test('optional field missing alone does not block',()=>check('S0_RECHECK_ONLY',x=>x.proposal.fields.pop()));
test('conflict with verified sources routes to human',()=>check('HUMAN_REVIEW_REQUIRED',x=>x.proposal.conflicts=[{code:'renda',sourceIds:['old','new']}]));
test('conflict with nonexistent source rejected',()=>check('SOURCE_INVALID',x=>x.proposal.conflicts=[{code:'renda',sourceIds:['old','none']}]));
test('explicit withdrawal advisory is not a commercial mutation',()=>check('COMMERCIAL_ADVISORY_REVIEW',x=>x.proposal.advisory={kind:'perdido',sourceId:'new'}));
test('sold advisory never accepted',()=>check('SOURCE_INVALID',x=>x.proposal.advisory={kind:'vendido',sourceId:'new'}));
test('withdrawal without explicit S0-verified claim refused',()=>check('SOURCE_INVALID',x=>x.proposal.advisory={kind:'perdido',sourceId:'old'}));
test('proposal cannot claim applied status',()=>check('SCHEMA_INVALID',x=>{x.proposal={...x.proposal};delete x.proposal.advisory;}));
test('source unavailable cannot be made up by the model',()=>check('SOURCE_INVALID',x=>x.proposal.fields[0].sourceId='imaginary'));
test('result has no mutation, sends or bank proof',()=>{const out=gate(fixture());for(const key of ['applied','sent','commercialStatus','bankReceipt','databaseWrite']) assert.equal(key in out,false);});

 // Extra adversarial cases: hidden contradictions cannot be trusted to F03's self-report.
test('hidden income conflict across historical cases requires human review',()=>check('HUMAN_REVIEW_REQUIRED',x=>x.cutoff.sources[0].claims.push({code:'renda',value:2400,explicit:true})));
test('equal explicit income in both cases is not automatically a contradiction',()=>check('S0_RECHECK_ONLY',x=>x.cutoff.sources[0].claims.push({code:'renda',value:3500,explicit:true})));
test('conflict in optional field also requests review',()=>check('HUMAN_REVIEW_REQUIRED',x=>x.cutoff.sources[1].claims.push({code:'cor',value:'vermelho',explicit:true})));
test('hypothetical or nonexplicit old value is not a conflicting fact',()=>check('S0_RECHECK_ONLY',x=>x.cutoff.sources[0].claims.push({code:'renda',value:2400,explicit:false})));
test('identical explicit value from more than one case is allowed',()=>check('S0_RECHECK_ONLY',x=>x.cutoff.sources[0].claims.push({code:'renda',value:3500,explicit:true})));
test('two different explicit claims within one source require review',()=>check('HUMAN_REVIEW_REQUIRED',x=>x.cutoff.sources[1].claims.push({code:'renda',value:4000,explicit:true})));
test('unknown claim payload key is rejected even if not proposed',()=>check('SOURCE_INVALID',x=>x.cutoff.sources[1].claims.push({code:'unknown',value:'x',explicit:true,systemOverride:true})));
test('object value in unused claim cannot be treated as verified',()=>check('SOURCE_INVALID',x=>x.cutoff.sources[1].claims.push({code:'unknown',value:{nested:'x'},explicit:true})));
test('nonfinite numeric claim cannot become evidence',()=>check('SOURCE_INVALID',x=>x.cutoff.sources[1].claims.push({code:'renda',value:Infinity,explicit:true})));
test('blank string claim cannot become evidence',()=>check('SOURCE_INVALID',x=>x.cutoff.sources[1].claims.push({code:'cor',value:'  ',explicit:true})));
test('historical zero and nonzero produce conflict, including falsey first value',()=>check('HUMAN_REVIEW_REQUIRED',x=>{x.cutoff.sources[0].claims.push({code:'renda',value:0,explicit:true});}));
test('falsy boolean first value still participates in conflicts',()=>check('HUMAN_REVIEW_REQUIRED',x=>{x.cutoff.sources[0].claims.push({code:'cor',value:false,explicit:true});}));
test('unverified alternate evidence is not a verified contradiction',()=>check('S0_RECHECK_ONLY',x=>{x.proposal.fields.pop();x.cutoff.sources[0].s0Verified=false;x.cutoff.sources[0].claims=[{code:'renda',value:1000,explicit:true}];}));
test('unavailable alternate evidence cannot determine the true value',()=>check('S0_RECHECK_ONLY',x=>{x.proposal.fields.pop();x.cutoff.sources[0].available=false;x.cutoff.sources[0].claims=[{code:'renda',value:1000,explicit:true}];}));
test('withdrawal evidence excluded from catalogue conflict, advisory is review only',()=>check('COMMERCIAL_ADVISORY_REVIEW',x=>{x.cutoff.sources[0].claims.push({code:'customer_withdrawal',value:false,explicit:true});x.proposal.advisory={kind:'perdido',sourceId:'new'};}));
