import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectResponsesShape as inspect,OAI_RESPONSE_LAB_INPUT,OAI_RESPONSE_LAB_RESULT}
 from '../responses-shape-preflight-lab.mjs';
import {F01_RESPONSE} from '../f01-sales-boundary.mjs';
import {F02_RESPONSE} from '../f02-plan-boundary.mjs';
import {F03_PROPOSAL_SCHEMA} from '../f03-history-boundary.mjs';

const schemas={F01:F01_RESPONSE,F02:F02_RESPONSE,F03:F03_PROPOSAL_SCHEMA};
const raw=(kind='F01')=>JSON.stringify({schemaVersion:schemas[kind],providerTag:'tag1',state:'completed',output:{}});
const message=(text=raw())=>({type:'message',role:'assistant',status:'completed',
  content:[{type:'output_text',text}]});
function fixture(kind='F01'){
 return {schemaVersion:OAI_RESPONSE_LAB_INPUT,operation:kind,providerTag:'tag1',
  modelRef:'model1',startedAtMs:100,observedAtMs:130,deadlineMs:200,
  response:{id:'resp1',model:'model1',status:'completed',output:[message(raw(kind))],
    error:null,incomplete_details:null}};
}
function expectZero(o){
  assert.equal(o.schemaVersion,OAI_RESPONSE_LAB_RESULT);
  for(const k of ['providerAuthenticated','sourceS0Authenticated','modelInvocationAuthorized',
    'modelOutputTrusted','responseSemanticsValidated','modelContentAuthorized',
    'publishAuthorized','schedulingAuthorized','sendAuthorized','fieldApplicationAuthorized',
    'productionAuthorized','costApproved','liveApiCalled'])assert.equal(o[k],false,k);
  assert.equal(o.requiresS0Recheck,true);
  assert.equal(Object.isFrozen(o),true);
}
for(const kind of ['F01','F02','F03'])test('OFF16 positive untrusted JSON candidate '+kind,()=>{
  const data=fixture(kind),res=inspect(data);
  assert.equal(res.status,'UNTRUSTED_JSON_CANDIDATE');
  assert.equal(res.operation,kind);
  assert.equal(res.candidateRaw,data.response.output[0].content[0].text);
  expectZero(res);
});
const cases=[
 ['missing response',i=>{i.response=null;},'TRANSPORT_UNKNOWN','NO_RESPONSE'],
 ['model mismatch',i=>{i.response.model='other';},'DENIED','MODEL_MISMATCH'],
 ['queued is not a candidate',i=>{i.response.status='queued';},'AWAITING_PROVIDER','NOT_FINAL'],
 ['in progress is not a candidate',i=>{i.response.status='in_progress';},'AWAITING_PROVIDER','NOT_FINAL'],
 ['incomplete is not a candidate',i=>{i.response.status='incomplete';},'INCOMPLETE_RESPONSE','NO_CANDIDATE'],
 ['failed is not a candidate',i=>{i.response.status='failed';},'PROVIDER_TERMINATED','NO_CANDIDATE'],
 ['cancelled is not a candidate',i=>{i.response.status='cancelled';},'PROVIDER_TERMINATED','NO_CANDIDATE'],
 ['completed with error is conflicting',i=>{i.response.error={code:'rate_limit'};},'REVIEW_REQUIRED','CONFLICTING_PROVIDER_STATE'],
 ['completed with incomplete detail is conflicting',i=>{i.response.incomplete_details={reason:'max_output_tokens'};},'REVIEW_REQUIRED','CONFLICTING_PROVIDER_STATE'],
 ['clock rolls back',i=>{i.observedAtMs=99;},'REVIEW_REQUIRED','CLOCK'],
 ['response late',i=>{i.observedAtMs=201;},'LATE_RESPONSE','DEADLINE'],
 ['malformed raw json',i=>{i.response.output=[message('{broken')];},'SCHEMA_INVALID','MODEL_JSON'],
 ['duplicate JSON key',i=>{i.response.output=[message('{"schemaVersion":"a","schemaVersion":"b","providerTag":"tag1"}')];},'SCHEMA_INVALID','MODEL_JSON'],
 ['wrong provider tag',i=>{i.response.output=[message(JSON.stringify({schemaVersion:F01_RESPONSE,providerTag:'tag2'}))];},'SCHEMA_INVALID','MODEL_JSON'],
 ['wrong top-level schema',i=>{i.response.output=[message(JSON.stringify({schemaVersion:F02_RESPONSE,providerTag:'tag1'}))];},'SCHEMA_INVALID','MODEL_JSON'],
 ['non-object raw JSON',i=>{i.response.output=[message('[]')];},'SCHEMA_INVALID','MODEL_JSON'],
 ['refusal cannot be published',i=>{i.response.output=[{type:'message',role:'assistant',status:'completed',content:[{type:'refusal',refusal:'No'}]}];},'MODEL_REFUSAL','CONTENT'],
 ['tool call cannot be promoted',i=>{i.response.output=[{type:'function_call',name:'send',arguments:'{}'}];},'UNEXPECTED_OUTPUT','CONTENT'],
 ['unexpected output type',i=>{i.response.output=[{type:'web_search_call'}];},'UNEXPECTED_OUTPUT','CONTENT'],
 ['two assistant messages ambiguous',i=>{i.response.output.push(message());},'AMBIGUOUS_MESSAGES','CONTENT'],
 ['missing assistant message',i=>{i.response.output=[{type:'reasoning'}];},'EMPTY_OUTPUT','CONTENT'],
 ['empty content array',i=>{i.response.output[0].content=[];},'AMBIGUOUS_CONTENT','CONTENT'],
 ['two content elements',i=>{i.response.output[0].content.push({type:'output_text',text:raw()});},'AMBIGUOUS_CONTENT','CONTENT'],
 ['non assistant role',i=>{i.response.output[0].role='user';},'UNEXPECTED_OUTPUT','CONTENT'],
 ['message still in progress',i=>{i.response.output[0].status='in_progress';},'UNEXPECTED_OUTPUT','CONTENT'],
 ['wrong content type',i=>{i.response.output[0].content[0].type='input_text';},'UNEXPECTED_CONTENT','CONTENT'],
 ['empty output text',i=>{i.response.output[0].content[0].text='';},'UNEXPECTED_CONTENT','CONTENT'],
 ['oversized output text',i=>{i.response.output[0].content[0].text='x'.repeat(10001);},'UNEXPECTED_CONTENT','CONTENT'],
 ['missing version marker',i=>{delete i.schemaVersion;},'INVALID_INPUT','REQUEST'],
 ['unexpected request authority',i=>{i.authorized=true;},'INVALID_INPUT','REQUEST'],
 ['unexpected response authority',i=>{i.response.publishAuthorized=true;},'INVALID_INPUT','RESPONSE'],
 ['invalid operation',i=>{i.operation='F04';},'INVALID_INPUT','REQUEST'],
 ['invalid timing',i=>{i.deadlineMs=100;},'INVALID_INPUT','REQUEST'],
 ['sparse output array',i=>{i.response.output=new Array(2);i.response.output[0]=message();},'INVALID_INPUT','REQUEST'],
 ['unexpected response status',i=>{i.response.status='sent';},'INVALID_INPUT','RESPONSE'],
 ['unexpected response error schema',i=>{i.response.error={code:'x',message:'secret'};},'INVALID_INPUT','RESPONSE'],
 ['hidden getter rejects without invocation',i=>{Object.defineProperty(i.response,'model',{get(){throw Error('getter');}});},'INVALID_INPUT','REQUEST'],
 ['cyclic payload rejects',i=>{i.cycle=i;},'INVALID_INPUT','REQUEST'],
 ['provider response cannot assert cost approval',i=>{i.response.output[0].content[0].costApproved=true;},'UNEXPECTED_CONTENT','CONTENT']
];
if(cases.length!==39)throw Error('cases must be 39 but got '+cases.length);
for(const [idx,[name,mutate,status,stage]] of cases.entries())test('OFF16-'+String(idx+4).padStart(2,'0')+' '+name,()=>{
 const data=fixture();mutate(data);const result=inspect(data);
 assert.equal(result.status,status,name);assert.equal(result.stage,stage,name);
 expectZero(result);assert.equal(Object.hasOwn(result,'candidateRaw'),false);
});
