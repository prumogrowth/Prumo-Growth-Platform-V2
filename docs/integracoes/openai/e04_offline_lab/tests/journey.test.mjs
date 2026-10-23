import test from 'node:test';
import assert from 'node:assert/strict';
import {evaluateOfflineJourney as go} from '../journey.mjs';

// All identities, authorizations, event receipts and templates are synthetic.
const fixture=()=>{
 const vers=()=>({case:1,cycle:2,form:3,catalog:1,assignment:5});
 const scope=()=>({authenticated:true,authorized:true,tenantAllowed:true,storeId:'A',caseId:'K1',expected:vers(),current:vers()});
 const reqF01={scope:scope(),owner:'ai',handoff:false,humanized:false,nowMs:1793350000000,
   sources:[{id:'price',storeId:'A',approved:true,active:true,mode:'current'}]};
 const beforeHandoff={req:reqF01,proposal:{text:'Informação comercial sujeita a confirmação',sourceIds:['price'],commercial:true,modality:'text'}};
 const reqF03={scope:scope(),humanClosed:true,closureAuthenticated:true,closureId:'close1',personId:'P1',cutoffSequence:7,
   records:[
     {id:'m1',storeId:'A',personId:'P1',caseId:'K0',sequence:1,author:'customer',kind:'text',available:true,contentAuthorized:true},
     {id:'m2',storeId:'A',personId:'P1',caseId:'K1',sequence:7,author:'customer',kind:'text',available:true,contentAuthorized:true},
     {id:'later',storeId:'A',personId:'P1',caseId:'K1',sequence:8,author:'customer',kind:'text',available:true,contentAuthorized:true}],
   catalog:[{code:'renda',essential:true},{code:'cor',essential:false}],verifiedWithdrawalSourceIds:['m2']};
 const request={scope:scope(),explicitS0Request:true,optOut:false,handoffPlanReuse:false,ownerRoute:'human',purpose:'post_human',maxAttempts:1,
   windowStart:'2026-11-01T00:00:00Z',windowEnd:'2026-11-10T23:59:59Z',
   allowedTemplates:[
     {id:'t1',version:'v1',storeId:'A',purpose:'post_human',active:true},
     {id:'tf',version:'v1',storeId:'A',purpose:'post_human',active:true}]};
 const proposal={attempts:[{templateId:'t1',version:'v1',purpose:'post_human',at:'2026-11-02T12:00:00Z'}],
   finalTemplate:{templateId:'tf',version:'v1',purpose:'post_human',at:'2026-11-05T12:00:00Z'}};
 const planScope={authenticated:true,authorized:true,tenantAllowed:true,optOut:false,planAuthorized:true,
   storeId:'A',caseId:'K1',personId:'P1',caseVersion:1,catalogVersion:1,chainVersion:1,
   now:'2026-11-02T18:00:00Z',handoff:true};
 const plan={id:'plan_new',storeId:'A',caseId:'K1',personId:'P1',purpose:'post_human',ownerRoute:'human',
   caseVersion:1,catalogVersion:1,chainVersion:1,
   attempts:[
     {id:'a1',templateId:'t1',templateVersion:'v1',category:'MARKETING',at:'2026-11-02T12:00:00Z',isFinal:false},
     {id:'af',templateId:'tf',templateVersion:'v1',category:'MARKETING',at:'2026-11-05T12:00:00Z',isFinal:true}]};
 return {
   scope:{authenticated:true,authorized:true,tenantAllowed:true,storeId:'A',caseId:'K1',personId:'P1'},
   beforeHandoff,
   handoff:{authenticated:true,storeId:'A',caseId:'K1'},
   conclusion:{req:reqF03,proposal:{fields:[{code:'renda',value:3500,sourceId:'m2'},{code:'cor',value:'azul',sourceId:'m1'}],conflicts:[],commercialAdvisory:null}},
   postHuman:{authenticatedS0Request:true,oldAiPlanCancelled:true,request,proposal,planScope,plan,events:[],
     templateCategories:[{id:'t1',version:'v1',category:'MARKETING',storeId:'A',purpose:'post_human'},
       {id:'tf',version:'v1',category:'MARKETING',storeId:'A',purpose:'post_human'}],
     frequency:{consent:{approved:true,active:true,optIn:true,optOut:false,metaHold:false},
       policy:{maxMarketingPerWindow:2,windowHours:24,policyVersion:'LOCAL_V1'},history:[]}}
 };
};
const event=(n,kind,attemptId='a1')=>({eventId:'evt'+n,sequence:n,storeId:'A',personId:'P1',caseId:'K1',planId:'plan_new',attemptId,kind,verified:true});
const code=(status,x)=>assert.equal(go(x).status,status);

test('all four stages end in another S0 check, never in a send',()=>{
 const r=go(fixture()); assert.deepEqual(r,{status:'READY_FOR_S0_RECHECK_ONLY',stage:'F02'});
 assert.equal('sent' in r,false);assert.equal('commercialStatus' in r,false);
});
test('F01 plus human closure and F03 do not automatically invoke F02',()=>{
 const x=fixture();delete x.postHuman;assert.deepEqual(go(x),{status:'F03_PROPOSAL_ONLY',stage:'F03'});
});
test('explicit null posthuman means F03 only',()=>{const x=fixture();x.postHuman=null;code('F03_PROPOSAL_ONLY',x);});
test('missing initial authorization precedes any stage disclosure',()=>{const x=fixture();x.scope.authorized=false;x.postHuman=null;assert.deepEqual(go(x),{status:'DENIED',stage:'S0'});});
test('cross-store F01 input blocked',()=>{const x=fixture();x.beforeHandoff.req.scope.storeId='B';code('DENIED',x);});
test('F01 late human route not allowed as initial seller',()=>{const x=fixture();x.beforeHandoff.req.owner='human';code('DENIED',x);});
test('a customer cannot forge the handoff',()=>{const x=fixture();x.handoff.authenticated=false;code('DENIED',x);});
test('handoff must belong to same case',()=>{const x=fixture();x.handoff.caseId='K2';code('DENIED',x);});
test('WhatsApp inactivity never implies human closure',()=>{const x=fixture();x.conclusion.req.humanClosed=false;code('NO_F03_TRIGGER',x);});
test('unauthenticated closure never triggers F03',()=>{const x=fixture();x.conclusion.req.closureAuthenticated=false;code('NO_F03_TRIGGER',x);});
test('F03 multi-case same-person history may include previous case',()=>code('READY_FOR_S0_RECHECK_ONLY',fixture()));
test('F03 cross-store historic source rejected',()=>{const x=fixture();x.conclusion.req.records[0].storeId='B';code('INVALID_INPUT',x);});
test('F03 wrong-person historic source rejected',()=>{const x=fixture();x.conclusion.req.records[0].personId='P2';code('INVALID_INPUT',x);});
test('F03 post-cutoff source cannot be proposed',()=>{const x=fixture();x.conclusion.proposal.fields[0].sourceId='later';code('SOURCE_INVALID',x);});
test('F03 essential missing routes to human not F02',()=>{const x=fixture();x.conclusion.proposal.fields=x.conclusion.proposal.fields.slice(1);assert.deepEqual(go(x),{status:'HUMAN_COMPLEMENT_REVIEW',stage:'F03'});});
test('F03 optional absent is not a blocker',()=>{const x=fixture();x.conclusion.proposal.fields=x.conclusion.proposal.fields.slice(0,1);code('READY_FOR_S0_RECHECK_ONLY',x);});
test('F03 conflict routes to human review',()=>{const x=fixture();x.conclusion.proposal.conflicts=[{code:'renda',sourceIds:['m1','m2']}];code('HUMAN_COMPLEMENT_REVIEW',x);});
test('F03 valid withdrawal is advisory and stops recontact chain',()=>{
 const x=fixture();x.conclusion.proposal.commercialAdvisory={kind:'perdido',sourceIds:['m2']};
 assert.deepEqual(go(x),{status:'COMMERCIAL_ADVISORY_REVIEW',stage:'F03'});
});
test('F03 cannot mark sold',()=>{const x=fixture();x.conclusion.proposal.commercialAdvisory={kind:'vendido',sourceIds:['m2']};code('SOURCE_INVALID',x);});
test('F03 stale form denied for application stage',()=>{const x=fixture();x.conclusion.req.scope.current.form=4;code('STALE',x);});
test('S0 must authorize a NEW F02 request',()=>{const x=fixture();x.postHuman.authenticatedS0Request=false;code('DENIED',x);});
test('old pre-handoff AI chain must be cancelled',()=>{const x=fixture();x.postHuman.oldAiPlanCancelled=false;code('DENIED',x);});
test('post-human F02 cannot route seller_ai',()=>{const x=fixture();x.postHuman.request.ownerRoute='seller_ai';code('DENIED',x);});
test('F02 must have explicit S0 request flag',()=>{const x=fixture();x.postHuman.request.explicitS0Request=false;code('DENIED',x);});
test('F02 optout blocks even a syntactically valid plan',()=>{const x=fixture();x.postHuman.request.optOut=true;code('DENIED',x);});
test('template is selected only from allowlisted versions',()=>{const x=fixture();x.postHuman.proposal.attempts[0].version='v2';code('SOURCE_INVALID',x);});
test('plan must use exactly the template proposed',()=>{const x=fixture();x.postHuman.plan.attempts[0].templateId='tf';code('SOURCE_INVALID',x);});
test('plan cannot forge an earlier schedule than proposal',()=>{const x=fixture();x.postHuman.plan.attempts[0].at='2026-11-01T12:00:00Z';code('SOURCE_INVALID',x);});
test('template category cannot be reclassified to avoid marketing cap',()=>{const x=fixture();x.postHuman.plan.attempts[0].category='UTILITY';code('SOURCE_INVALID',x);});
test('template category comes only from S0-authorized registry',()=>{const x=fixture();x.postHuman.templateCategories[0].category='AUTHENTICATION';code('SOURCE_INVALID',x);});
test('posthuman plan version drift fails closed',()=>{const x=fixture();x.postHuman.plan.chainVersion=2;code('STALE',x);});
test('F02 plan must be bound to the exact S0 scope',()=>{const x=fixture();x.postHuman.planScope.caseId='K2';code('DENIED',x);});
test('queued Meta receipt keeps plan awaiting proof',()=>{const x=fixture();x.postHuman.events=[event(1,'QUEUED')];code('AWAITING_META_PROOF',x);});
test('verified final sent is evidence only',()=>{const x=fixture();x.postHuman.events=[event(1,'SENT'),event(2,'SENT','af')];code('FINAL_SENT_EVIDENCE_ONLY',x);});
test('131049 holds campaign without marking loss',()=>{const x=fixture();x.postHuman.events=[event(1,'META_131049')];code('META_ECOSYSTEM_REVIEW',x);});
test('new customer inbound holds the cadence',()=>{const x=fixture();x.postHuman.events=[event(1,'CUSTOMER_INBOUND',null)];code('HOLD_FOR_S0_REVIEW',x);});
test('explicit optout event cancels the cadence',()=>{const x=fixture();x.postHuman.events=[event(1,'OPT_OUT',null)];code('CANCELLED',x);});
test('two conflicting receipts lead to review',()=>{const x=fixture();x.postHuman.events=[event(1,'SENT'),event(2,'META_131049')];code('REVIEW_REQUIRED',x);});
test('local cap does not assume fixed Meta daily maximum',()=>{const x=fixture();x.postHuman.frequency.policy.maxMarketingPerWindow=0;code('LOCAL_FREQUENCY_HOLD',x);});
test('Meta holds even without local cap',()=>{const x=fixture();x.postHuman.frequency.consent.metaHold=true;code('META_HOLD_REVIEW',x);});
test('missing frequency policy never implies Meta permission',()=>{const x=fixture();x.postHuman.frequency.policy=null;code('REVIEW_REQUIRED',x);});
test('consent revoked after F02 planning still denies',()=>{const x=fixture();x.postHuman.frequency.consent.optOut=true;code('DENIED',x);});
test('privacy: case-level data cannot cross to different person',()=>{const x=fixture();x.postHuman.plan.personId='P2';code('DENIED',x);});
