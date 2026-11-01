import test from 'node:test';
import assert from 'node:assert/strict';
import {reviewResponseThroughDomain as review,OFF21_INPUT,OFF21_RESULT}
 from '../response-domain-review-lab.mjs';
import {OAI_RESPONSE_LAB_INPUT} from '../responses-shape-preflight-lab.mjs';
import {F01_PRIVATE,F01_RESPONSE,prepareF01Turn} from '../f01-sales-boundary.mjs';
import {F02_PRIVATE,F02_RESPONSE,prepareF02Plan} from '../f02-plan-boundary.mjs';
import {F03_HISTORY_SCHEMA,F03_PROPOSAL_SCHEMA,prepareF03History} from '../f03-history-boundary.mjs';
const own=()=>({case:1,cycle:2,assignment:3,catalog:4,policy:5,knowledge:6,route:7,consent:8});
const f02v=()=>({case:1,cycle:2,catalog:3,assignment:4,policy:5,consent:6,chain:7});
const f03v=()=>({case:1,cycle:1,form:1,catalog:1,assignment:1,identity:1,policy:1});
function f01(){
  return {schemaVersion:F01_PRIVATE,requestId:'req1',providerTag:'tag1',nowMs:100,deadlineMs:200,
    scope:{authenticated:true,authorized:true,tenantAllowed:true,storeId:'store1',caseId:'case1',
      personId:'person1',owner:'ai',handoffDefinitive:false,humanized:false,postRemittance:false,
      postSale:false,channelEligible:true,optOut:false,expectedVersions:own(),currentVersions:own()},
    privacy:{contentAuthorized:true,dataMinimized:true},
    instructions:{text:'Não prometer crédito ou aprovação',behavior:'Atendimento comercial limitado',version:'v1'},
    customerInput:{kind:'text',text:'Qual é a oferta?',transcriptState:'NOT_APPLICABLE'},
    recentContext:[{role:'customer',text:'Pergunta sintética'}],
    sources:[{id:'source_internal',storeId:'store1',mode:'current',approved:true,
      active:true,modelAllowed:true,content:'Somente sob consulta',
      allowedClaimCodes:['offer_available'],validUntilMs:1000}]};
}
function f02(){
 return {schemaVersion:F02_PRIVATE,requestId:'req2',providerTag:'tag2',nowMs:100,deadlineMs:200,
   scope:{authenticated:true,authorized:true,tenantAllowed:true,storeId:'store2',
     caseId:'case2',personId:'person2',expectedVersions:f02v(),currentVersions:f02v()},
   request:{explicitS0Request:true,optOut:false,ownerRoute:'human',purpose:'post_human',
     handoffDefinitive:true,priorAiPlanCancelled:true,
     windowStart:'2026-11-01T10:00:00Z',windowEnd:'2026-11-01T18:00:00Z',maxAttempts:2,
     templates:[{id:'internal_tpl',version:'v1',storeId:'store2',purpose:'post_human',category:'UTILITY',
       active:true,approved:true,eligible:true}],
     instructions:{text:'Agendar somente modelos autorizados',version:'v1'},
     privateRefs:{consentRef:'private_consent',authorizationRef:'private_grant',
       sessionRef:'private_session',s0EvidenceRef:'private_evidence'},
     continuity:{chainRef:'chain1',chainVersion:7,previousPlanRef:'old1',revision:1}}};
}
function f03(){
 return {schemaVersion:F03_HISTORY_SCHEMA,requestId:'req3',providerTag:'tag3',
   scope:{authenticated:true,authorized:true,tenantAllowed:true,storeId:'store3',personId:'person3',
     caseId:'case3',closureId:'closure3',humanClosed:true,closureAuthenticated:true,
     identityAttested:true,historyCompletenessAttested:true,
     expectedVersions:f03v(),currentVersions:f03v()},
   privacy:{modelContentAuthorized:true,dataMinimized:true},
   cutoff:{sequence:5,closedAt:'2026-10-31T09:00:00Z',eventId:'closed_event'},
   cases:[{id:'case3',storeId:'store3',personId:'person3',s0IdentityBound:true}],
   catalog:[{code:'name',type:'string',essential:true}],
   records:[{id:'record1',caseId:'case3',storeId:'store3',personId:'person3',sequence:1,
     at:'2026-10-31T08:00:00Z',authorClass:'customer',kind:'text',available:true,
     contentAuthorized:true,content:'Pessoa fictícia',
     claims:[{id:'claim1',code:'name',value:'Ficticio',explicit:true}]}]};
}
function data(kind='F01'){
  if(kind==='F01'){
    const request=f01(),prepared=prepareF01Turn(request);
    assert.equal(prepared.status,'READY_CANDIDATE');
    return {kind,prepared,tag:'tag1',model:'test_model',
      raw:JSON.stringify({schemaVersion:F01_RESPONSE,providerTag:'tag1',state:'completed',
        output:{replyText:'Consulte as condições atuais; SECRET_DRAFT_TEXT',commercial:true,
          sourceAliases:['src_001'],claims:[{claimCode:'offer_available',sourceAlias:'src_001'}],
          modalityHint:'text',handoffAdvisory:{needed:false,reason:'NONE'},uncertaintyCodes:[]}}),
      recheck:{nowMs:150,currentScope:structuredClone(prepared.private.scope),prior:null}};
  }
  if(kind==='F02'){
    const request=f02(),prepared=prepareF02Plan(request);
    assert.equal(prepared.status,'READY_CANDIDATE');
    return {kind,prepared,tag:'tag2',model:'test_model',
      raw:JSON.stringify({schemaVersion:F02_RESPONSE,providerTag:'tag2',
        attempts:[{templateAlias:'tpl_001',version:'v1',purpose:'post_human',at:'2026-11-01T11:00:00Z'}],
        finalTemplate:null}),
      recheck:{nowMs:150,scope:structuredClone(prepared.private.scope)}};
  }
  const request=f03(),prepared=prepareF03History(request);
  assert.equal(prepared.status,'READY');
  return {kind,prepared,tag:'tag3',model:'test_model',
    raw:JSON.stringify({schemaVersion:F03_PROPOSAL_SCHEMA,providerTag:'tag3',
      fields:[{code:'name',value:'Ficticio',sourceAliases:['src_001']}],
      missingFields:[],conflicts:[],commercialAdvisory:null,followupAdvisory:'none'}),
    recheck:{currentScope:structuredClone(prepared.privateContext.snapshot.scope),prior:null}};
}
function envelope(kind='F01'){
 const x=data(kind);
 const preflightInput={schemaVersion:OAI_RESPONSE_LAB_INPUT,operation:kind,
   providerTag:x.tag,modelRef:x.model,startedAtMs:100,observedAtMs:140,deadlineMs:200,
   response:{id:'resp1',model:x.model,status:'completed',error:null,incomplete_details:null,
     output:[{type:'message',role:'assistant',status:'completed',content:[{type:'output_text',text:x.raw}]}]}};
 return {schemaVersion:OFF21_INPUT,preflightInput,prepared:x.prepared,recheck:x.recheck};
}
function check(input,status,stage){
 const z=review(input);
 assert.equal(z.schemaVersion,OFF21_RESULT);
 assert.equal(z.status,status);
 if(stage)assert.equal(z.stage,stage);
 assert.equal(Object.isFrozen(z),true);
 for(const k of ['s0Authenticated','providerAuthenticated','sourceAuthenticated','modelInvocationAuthorized',
   'modelOutputTrusted','semanticVerified','publishAuthorized','sendAuthorized','schedulingAuthorized',
   'fieldApplicationAuthorized','commercialTransitionAuthorized','productionAuthorized',
   'modelCalled','liveApiCalled','rawModelOutputExposed','domainProposalExposed'])
   assert.equal(z[k],false,k);
 assert.equal(z.requiresS0TransactionalRecheck,true);
 for(const sensitive of ['SECRET_DRAFT_TEXT','Ficticio','internal_tpl','source_internal','private_consent',
   'person1','person2','person3','case1','case2','case3','closure3'])
   assert.ok(!JSON.stringify(z).includes(sensitive),sensitive);
 return z;
}
for(const kind of ['F01','F02','F03'])test('OFF21 valid '+kind+' domain remains review-only',()=>{
 check(envelope(kind),'LAB_DOMAIN_REVIEW_ONLY','NO_S0_AUTHORITY');
});
const cases=[
 ['F01 handoff in recheck denied', 'F01',i=>i.recheck.currentScope.handoffDefinitive=true,'LAB_DOMAIN_BLOCKED','DENIED'],
 ['F01 optout in recheck denied','F01',i=>i.recheck.currentScope.optOut=true,'LAB_DOMAIN_BLOCKED','DENIED'],
 ['F01 different store denied','F01',i=>i.recheck.currentScope.storeId='other','LAB_DOMAIN_BLOCKED','DENIED'],
 ['F01 changed knowledge version stale','F01',i=>i.recheck.currentScope.currentVersions.knowledge=99,'LAB_DOMAIN_BLOCKED','STALE'],
 ['F01 expired commercial source blocked','F01',i=>i.recheck.nowMs=1000,'LAB_DOMAIN_BLOCKED','LATE_RESPONSE'],
 ['F01 fabricated grant in model output','F01',i=>{const p=JSON.parse(i.preflightInput.response.output[0].content[0].text);p.output.publishAuthorized=true;i.preflightInput.response.output[0].content[0].text=JSON.stringify(p);},'LAB_DOMAIN_BLOCKED','SCHEMA_INVALID'],
 ['F01 unsupported source citation denied','F01',i=>{const p=JSON.parse(i.preflightInput.response.output[0].content[0].text);p.output.sourceAliases=['src_777'];i.preflightInput.response.output[0].content[0].text=JSON.stringify(p);},'LAB_DOMAIN_BLOCKED','SOURCE_INVALID'],
 ['F02 changed cycle stale','F02',i=>i.recheck.scope.currentVersions.cycle=99,'LAB_DOMAIN_BLOCKED','STALE'],
 ['F02 optout untrusted recheck extra field','F02',i=>i.recheck.scope.optOut=true,'LAB_DOMAIN_BLOCKED','DENIED'],
 ['F02 other template alias denied','F02',i=>{const p=JSON.parse(i.preflightInput.response.output[0].content[0].text);p.attempts[0].templateAlias='tpl_404';i.preflightInput.response.output[0].content[0].text=JSON.stringify(p);},'LAB_DOMAIN_BLOCKED','SCHEMA_INVALID'],
 ['F02 wrong purpose denied','F02',i=>{const p=JSON.parse(i.preflightInput.response.output[0].content[0].text);p.attempts[0].purpose='marketing';i.preflightInput.response.output[0].content[0].text=JSON.stringify(p);},'LAB_DOMAIN_BLOCKED','SCHEMA_INVALID'],
 ['F03 wrong person in recheck denied','F03',i=>i.recheck.currentScope.personId='different','LAB_DOMAIN_BLOCKED','DENIED'],
 ['F03 unsubstantiated name blocked','F03',i=>{const p=JSON.parse(i.preflightInput.response.output[0].content[0].text);p.fields[0].value='not_supported';i.preflightInput.response.output[0].content[0].text=JSON.stringify(p);},'LAB_DOMAIN_BLOCKED','SOURCE_INVALID'],
 ['F03 unknown source alias denied','F03',i=>{const p=JSON.parse(i.preflightInput.response.output[0].content[0].text);p.fields[0].sourceAliases=['src_999'];i.preflightInput.response.output[0].content[0].text=JSON.stringify(p);},'LAB_DOMAIN_BLOCKED','SOURCE_INVALID'],
 ['F03 missing essential requires review','F03',i=>{const p=JSON.parse(i.preflightInput.response.output[0].content[0].text);p.fields=[];p.missingFields=['name'];i.preflightInput.response.output[0].content[0].text=JSON.stringify(p);},'LAB_DOMAIN_REVIEW_REQUIRED','NO_S0_AUTHORITY'],
 ['F03 model attempts database commit','F03',i=>{const p=JSON.parse(i.preflightInput.response.output[0].content[0].text);p.commitAuthorized=true;i.preflightInput.response.output[0].content[0].text=JSON.stringify(p);},'LAB_DOMAIN_BLOCKED','SCHEMA_INVALID'],
 ['Provider incomplete','F01',i=>i.preflightInput.response.status='incomplete','PREFLIGHT_BLOCKED','INCOMPLETE_RESPONSE'],
 ['Provider queued','F02',i=>i.preflightInput.response.status='queued','PREFLIGHT_BLOCKED','AWAITING_PROVIDER'],
 ['Provider refusal','F01',i=>{i.preflightInput.response.output[0].content=[{type:'refusal',refusal:'cannot answer'}];},'PREFLIGHT_BLOCKED','MODEL_REFUSAL'],
 ['Provider tool call','F03',i=>i.preflightInput.response.output=[{type:'function_call',name:'write_form',arguments:'{}'}],'PREFLIGHT_BLOCKED','UNEXPECTED_OUTPUT'],
 ['Provider mismatch model','F02',i=>i.preflightInput.response.model='other_model','PREFLIGHT_BLOCKED','DENIED'],
 ['Provider duplicate JSON key','F01',i=>i.preflightInput.response.output[0].content[0].text='{"schemaVersion":"x","schemaVersion":"y","providerTag":"tag1"}','PREFLIGHT_BLOCKED','SCHEMA_INVALID'],
 ['Provider top-level schema swapped','F01',i=>{const p=JSON.parse(i.preflightInput.response.output[0].content[0].text);p.schemaVersion=F02_RESPONSE;i.preflightInput.response.output[0].content[0].text=JSON.stringify(p);},'PREFLIGHT_BLOCKED','SCHEMA_INVALID'],
 ['Input missing recheck','F01',i=>delete i.recheck,'INVALID_INPUT','ENVELOPE'],
 ['Input recheck grants forged','F01',i=>i.recheck.publishAuthorized=true,'INVALID_INPUT','RECHECK'],
 ['Input recheck missing time','F02',i=>delete i.recheck.nowMs,'INVALID_INPUT','RECHECK'],
 ['Input F03 explicit scope missing','F03',i=>delete i.recheck.currentScope,'INVALID_INPUT','RECHECK'],
 ['Input F03 unknown recheck field','F03',i=>i.recheck.fieldApplicationAuthorized=true,'INVALID_INPUT','RECHECK'],
 ['Input F01 unknown handle','F01',i=>i.prepared={status:'READY_CANDIDATE'},'LAB_DOMAIN_BLOCKED','INVALID_INPUT'],
 ['Input F02 swapped handle F01','F02',i=>i.prepared=data('F01').prepared,'LAB_DOMAIN_BLOCKED','INVALID_INPUT'],
 ['Input F03 swapped handle F02','F03',i=>i.prepared=data('F02').prepared,'LAB_DOMAIN_BLOCKED','DENIED'],
 ['Input F02 recheck accessor never executed','F02',i=>{let count=0;Object.defineProperty(i.recheck,'scope',{get(){count++;throw Error('getter');}});},'INVALID_INPUT','RECHECK'],
 ['Input F01 cyclic recheck','F01',i=>i.recheck.loop=i.recheck,'INVALID_INPUT','RECHECK'],
 ['Input preflight model getter','F01',i=>Object.defineProperty(i.preflightInput.response,'model',{get(){throw Error('model getter');}}),'PREFLIGHT_BLOCKED','INVALID_INPUT'],
 ['Input provider returned late','F02',i=>i.preflightInput.observedAtMs=201,'PREFLIGHT_BLOCKED','LATE_RESPONSE']
];
for(const [n,kind,mutate,status,stage] of cases){
 test('OFF21 '+n,()=>{const i=envelope(kind);mutate(i);check(i,status,stage);});
}
