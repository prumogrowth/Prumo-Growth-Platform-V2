/** S0 -> OFF04 interop with exact independent pinned OpenAI consumer.
 * Provider output cannot see S0 private refs. No model/Graph/HTTP.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const pinned=process.env.S0_F02_OFF04_PIN;
const source=pinned?await import(pathToFileURL(resolve(pinned,
  'docs/integracoes/openai/e04_offline_lab/f02-plan-boundary.mjs')).href):null;
const enabled={skip:!source};
function privateFixture(){
  const versions={case:1,cycle:1,catalog:1,assignment:1,policy:1,consent:1,chain:1};
  const nowMs=1000;
  return {
    schemaVersion:'prumo.openai.f02-plan-private/0.1-candidate',
    requestId:'request_A',providerTag:'opaque_01',nowMs,deadlineMs:30000,
    scope:{authenticated:true,authorized:true,tenantAllowed:true,
      storeId:'store-A',caseId:'case_A',personId:'synthetic_person_01',
      expectedVersions:versions,currentVersions:{...versions}},
    request:{explicitS0Request:true,optOut:false,ownerRoute:'human',
      purpose:'followup_message',handoffDefinitive:false,
      priorAiPlanCancelled:false,windowStart:'2026-11-01T10:00:00Z',
      windowEnd:'2026-11-01T11:00:00Z',maxAttempts:2,
      templates:[{id:'tpl_A',version:'ver_1',storeId:'store-A',
        purpose:'followup_message',category:'UTILITY',active:true,
        approved:true,eligible:true}],
      instructions:{text:'Plan only authorized template aliases.',
        version:'config_v1'},
      privateRefs:{consentRef:'synthetic_consent',
        authorizationRef:'synthetic_authorization',
        sessionRef:'synthetic_session',s0EvidenceRef:'synthetic_evidence'},
      continuity:{chainRef:'synthetic_chain',chainVersion:1,
        previousPlanRef:null,revision:1}}
  };
}
let evidence=null;
if(process.env.S0_F02_PRIVATE_EVIDENCE){
  evidence=JSON.parse(await readFile(process.env.S0_F02_PRIVATE_EVIDENCE,'utf8'));
  assert.equal(evidence.lab_only,true);
}
function prepare(){
  const input=evidence?structuredClone(evidence.private):privateFixture();
  const handle=source.prepareF02Plan(input);
  assert.equal(handle.status,'READY_CANDIDATE');
  const view=source.f02ProviderView(handle);
  assert.equal(view.schemaVersion,'prumo.openai.f02-plan-provider/0.1-candidate');
  return {handle,view,input};
}
function modelReply(view){
  return JSON.stringify({
    schemaVersion:'prumo.openai.f02-plan-response/0.1-candidate',
    providerTag:view.providerTag,
    attempts:[{templateAlias:view.planning.templates[0].alias,
      version:view.planning.templates[0].version,
      purpose:view.planning.purpose,at:view.planning.windowStart}],
    finalTemplate:null,
  });
}
function evalPlan(handle,view,input,response){
  return source.evaluateF02Model(handle,response,{
    nowMs:input.nowMs+1,scope:structuredClone(input.scope)
  });
}

test('S0F02-OFF04-01 exact OpenAI original accepts private S0 candidate',
  enabled,()=>{
  const {handle,view,input}=prepare();
  assert.equal(view.planning.templates.length,1);
  assert.equal(view.planning.templates[0].alias,'tpl_001');
  assert.equal(input.request.templates[0].id,'tpl_A');
});
test('S0F02-OFF04-02 provider payload hides ALL S0 private IDs',
  enabled,()=>{
  const {view,input}=prepare();
  const raw=JSON.stringify(view);
  for(const hidden of [
    input.scope.storeId,input.scope.caseId,input.scope.personId,
    input.request.templates[0].id,
    input.request.privateRefs.consentRef,
    input.request.privateRefs.authorizationRef,
    input.request.privateRefs.sessionRef,
    input.request.privateRefs.s0EvidenceRef,
    input.request.continuity.chainRef,input.requestId,
  ])assert.ok(!raw.includes('"'+hidden+'"'),'private field in provider');
  assert.equal('scope' in view,false);
  assert.equal('consent' in view,false);
  assert.equal('authorized' in view,false);
});
test('S0F02-OFF04-03 model can only return S0_RECHECK_ONLY proposal',
  enabled,()=>{
  const {handle,view,input}=prepare();
  const out=evalPlan(handle,view,input,modelReply(view));
  assert.equal(out.status,'S0_RECHECK_ONLY');
  assert.equal(out.sendAuthorized,false);
  assert.equal(out.schedulingAuthorized,false);
  assert.equal(out.commercialTransitionAuthorized,false);
  assert.equal(out.attempts[0].templateId,input.request.templates[0].id);
  assert.equal(out.finalTemplate,null);
});
test('S0F02-OFF04-04 stale revision rejected by original consumer',
  enabled,()=>{
  const {handle,view,input}=prepare();
  const scope=structuredClone(input.scope);
  scope.currentVersions.consent+=1;
  assert.equal(source.evaluateF02Model(handle,modelReply(view),{
    nowMs:input.nowMs+1,scope
  }).status,'STALE');
});
test('S0F02-OFF04-05 forged alias is not resolved',
  enabled,()=>{
  const {handle,view,input}=prepare();
  const fake=JSON.parse(modelReply(view));
  fake.attempts[0].templateAlias='tpl_999';
  assert.equal(evalPlan(handle,view,input,JSON.stringify(fake)).status,
               'SCHEMA_INVALID');
});
test('S0F02-OFF04-06 model cannot append send/secret grant',
  enabled,()=>{
  const {handle,view,input}=prepare();
  const fake=JSON.parse(modelReply(view));
  fake.sendAuthorized=true;fake.secretSlots=['A'];
  assert.equal(evalPlan(handle,view,input,JSON.stringify(fake)).status,
               'SCHEMA_INVALID');
});
test('S0F02-OFF04-07 model cannot select outside window',
  enabled,()=>{
  const {handle,view,input}=prepare();
  const fake=JSON.parse(modelReply(view));
  fake.attempts[0].at='2001-01-01T00:00:00Z';
  assert.equal(evalPlan(handle,view,input,JSON.stringify(fake)).status,
               'SCHEMA_INVALID');
});
test('S0F02-OFF04-08 duplicate provider response keys rejected',
  enabled,()=>{
  const {handle,view,input}=prepare();
  const raw=modelReply(view).replace('{','{"providerTag":"ATTACK",');
  assert.equal(evalPlan(handle,view,input,raw).status,'SCHEMA_INVALID');
});
test('S0F02-OFF04-09 missing or tampered handle denied',
  enabled,()=>{
  const {view}=prepare();
  assert.equal(source.f02ProviderView({status:'READY_CANDIDATE'}).status,
               'INVALID_INPUT');
});
test('S0F02-OFF04-10 exact PG17 private envelope works with pinned OFF04',
 {skip:!source||!evidence},()=>{
  const {view,handle,input}=prepare();
  assert.ok(input.nowMs>1_700_000_000_000);
  // F02 independent physical sources are intentionally unequal.
  assert.equal(input.scope.expectedVersions.cycle,3);
  assert.equal(input.scope.expectedVersions.assignment,7);
  assert.equal(input.scope.currentVersions.cycle,3);
  assert.equal(input.scope.currentVersions.assignment,7);
  assert.equal(evidence.expected_aliases[0].alias,'tpl_001');
  const out=evalPlan(handle,view,input,modelReply(view));
  assert.equal(out.status,'S0_RECHECK_ONLY');
  assert.equal(out.attempts[0].templateId,
               evidence.expected_aliases[0].template_ref);
  assert.equal(out.attempts[0].templateVersion,
               evidence.expected_aliases[0].version_ref);
  assert.equal(out.sendAuthorized,false);
});

test('S0F02-OFF04-11 separately stale cycle and assignment denied',
 {skip:!source||!evidence},()=>{
  const {handle,view,input}=prepare();
  for(const key of ['cycle','assignment']){
    const scoped=structuredClone(input.scope);
    scoped.currentVersions[key]+=1;
    const out=source.evaluateF02Model(handle,modelReply(view),{
      nowMs:input.nowMs+1,scope:scoped
    });
    assert.equal(out.status,'STALE',key);
    // STALE from the immutable OFF04 consumer may omit authority flags.
    // Absence is not a grant; strictly no field may assert true.
    assert.notEqual(out.sendAuthorized,true);
    assert.notEqual(out.schedulingAuthorized,true);
    assert.notEqual(out.commercialTransitionAuthorized,true);
  }
});
