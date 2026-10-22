import test from 'node:test';
import assert from 'node:assert/strict';
import {projectCandidateIntegrationGate, INTEGRATION_GATE_PROPOSAL}
  from '../integration-gate-view.mjs';
import {S0_READ_PROPOSAL_VERSION} from '../s0-read-contract.mjs';
import {S0_COMMAND_RESULT_PROPOSAL} from '../s0-command-result.mjs';

const readExpected=()=>({
  query_id:'UQ02',query_version:'candidate1',request_id:'req-read-demo',
  correlation_id:'corr-demo',actor_id:'rafael',scope_ref:'shop-aurora',
  returned_projection:'case_minimized'
});
const readResponse=(expected=readExpected())=>({
  ...expected,schema_version:S0_READ_PROPOSAL_VERSION,leitura_minimizada:true,
  source_of_truth_version:'fixture-v1',as_of:'synthetic',
  outcome:{status:'APPLIED',reason_code:null},records:[{synthetic_client_ref:'SECRET_DEMO'}],
  next_cursor:null
});
const commandExpected=()=>({
  contract_id:'C11',contract_version:'proposal1',request_id:'req-command-demo',
  correlation_id:'corr-command',actor_id:'rafael',scope_ref:'shop-aurora',
  aggregate_ref:'A-102',expected_version:'case-v1'
});
const commandResponse=(status='APPLIED',expected=commandExpected())=>({
  ...expected,schema_version:S0_COMMAND_RESULT_PROPOSAL,
  outcome:status==='APPLIED'?
    {status,confirmed_persisted:true,effect_id:'effect-secret-demo',
      source_of_truth_version:'case-v2'}:
    {status,reason_code:status==='REJECTED'?'AUTH_SECRET_REASON':null}
});
const safe=view=>{
  assert.equal(view.proposal,INTEGRATION_GATE_PROPOSAL);
  for(const key of ['integrationReady','authenticatedByS0','canExposeRecords',
      'canPerformCommand','hasVerifiedEffect','automaticRetry','canChangeCommercialStatus'])
    assert.equal(view[key],false,key);
  assert.equal(Object.isFrozen(view),true);
  for(const token of ['SECRET_DEMO','effect-secret-demo','AUTH_SECRET_REASON',
      'req-read-demo','rafael','A-102','shop-aurora'])
    assert.equal(JSON.stringify(view).includes(token),false,'leak '+token);
};

test('FV-UI-021: sem fonte autenticada = gate não conectado e incapaz de agir',()=>{
 const view=projectCandidateIntegrationGate();
 assert.equal(view.readState,'not_connected');
 assert.equal(view.commandState,'not_connected');safe(view);
});

test('FV-UI-021: envelope de leitura formalmente válido não expõe records',()=>{
 const view=projectCandidateIntegrationGate({
   readExpected:readExpected(),readResponse:readResponse()
 });
 assert.equal(view.readState,'structural_candidate_only');
 assert.equal(view.commandState,'not_connected');safe(view);
});

test('FV-UI-021: comando candidato APPLIED não é efeito verificado',()=>{
 const view=projectCandidateIntegrationGate({
   commandExpected:commandExpected(),commandResponse:commandResponse()
 });
 assert.equal(view.commandState,'claimed_applied_unverified');safe(view);
});

test('FV-UI-021: pendente externo, incerteza e recusa não autorizam retry',()=>{
 for(const [status,expectedState] of [
   ['ACCEPTED_FOR_PROCESSING','pending_unverified'],
   ['UNCERTAIN_EXTERNAL','pending_unverified'],
   ['PENDING_EXTERNAL','pending_unverified'],
   ['REJECTED','rejected_unverified']]){
   const view=projectCandidateIntegrationGate({
     commandExpected:commandExpected(),commandResponse:commandResponse(status)
   });
   assert.equal(view.commandState,expectedState);safe(view);
 }
});

test('FV-UI-021: contextos divergentes de ator ou loja são rejeitados antes de staged read',()=>{
 for(const different of [{actor_id:'outra-pessoa'},{scope_ref:'shop-horizonte'}]){
   const cmdExpected={...commandExpected(),...different};
   const view=projectCandidateIntegrationGate({readExpected:readExpected(),
     readResponse:readResponse(),commandExpected:cmdExpected,
     commandResponse:commandResponse('APPLIED',cmdExpected)});
   assert.equal(view.readState,'context_mismatch');
   assert.equal(view.commandState,'context_mismatch');safe(view);
 }
});

test('FV-UI-021: contexto sem prova, falsificado ou retorno inválido é untrusted',()=>{
 for(const bad of [
   {readExpected:{...readExpected(),actor_id:''},readResponse:readResponse()},
   {readExpected:readExpected(),readResponse:{...readResponse(),leitura_minimizada:false}},
   {commandExpected:commandExpected(),commandResponse:{...commandResponse(),actor_id:'outra-pessoa'}},
   {commandExpected:commandExpected(),commandResponse:commandResponse('APPLIED',
     {...commandExpected(),contract_id:'C13'})}
 ]){
   const view=projectCandidateIntegrationGate(bad);
   assert.ok(view.readState==='untrusted' || view.commandState==='untrusted');
   safe(view);
 }
});

test('FV-UI-021: envelopes aparentemente bons em conjunto continuam sem autorização',()=>{
 const view=projectCandidateIntegrationGate({readExpected:readExpected(),
   readResponse:readResponse(),commandExpected:commandExpected(),
   commandResponse:commandResponse()});
 assert.equal(view.readState,'structural_candidate_only');
 assert.equal(view.commandState,'claimed_applied_unverified');safe(view);
});

test('FV-UI-021: não transporta dados e não modifica as entradas',()=>{
 const response=readResponse(),command=commandResponse();
 const before=JSON.stringify([response,command]);
 safe(projectCandidateIntegrationGate({readExpected:readExpected(),readResponse:response,
   commandExpected:commandExpected(),commandResponse:command}));
 assert.equal(JSON.stringify([response,command]),before);
});
