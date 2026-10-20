import test from 'node:test';
import assert from 'node:assert/strict';
import {
 createManualTemplate,prepareMetaReviewPayload,recordReviewSubmission,
 applyVerifiedMetaStatus,configureVariableSources,createEditedContentVersion,
 prepareApprovedTemplateParameters,
} from './template-catalog-control.ts';
import type {ManualTemplateInput,SourceDefinition} from './template-catalog-control.ts';

const draftInput:ManualTemplateInput={
 local_id:'f7200000-0000-4000-8000-000000000001',
 concessionaria_id:'f7200000-0000-4000-8000-000000000010',
 meta_account_ref:'123456789012345',
 name:'contato_manual_a',language:'pt_BR',category:'MARKETING',
 body:'Olá {{1}}, quem acompanha seu atendimento é {{2}}.',
 examples:['Pessoa Exemplo','Atendente Exemplo'],
};
const registry:SourceDefinition[]=[
 {source_key:'cliente.nome',value_type:'text',enabled:true},
 {source_key:'operador.nome',value_type:'text',enabled:true},
 {source_key:'caso.codigo',value_type:'text',enabled:true},
 {source_key:'sistema.token',value_type:'text',enabled:false},
];
const mappings=[
 {position:1,source_key:'cliente.nome'},
 {position:2,source_key:'operador.nome'},
] as const;
const submitted=()=>recordReviewSubmission(createManualTemplate(draftInput),'456789012345678');
const approved=()=>applyVerifiedMetaStatus(submitted(),'456789012345678','APPROVED');

test('WA17-01: humans supply body and sample values, no automatic generated text',()=>{
 const t=createManualTemplate(draftInput);
 assert.equal(t.body,draftInput.body);
 assert.deepEqual(t.positions,[1,2]);
 assert.equal(t.stage,'DRAFT');
 assert.equal(t.provider_template_id,null);
 assert.equal(t.mappings.length,0);
 assert.equal(Object.isFrozen(t),true);
});
test('WA17-02: submission builds documented Meta review body but no network',()=>{
 const request=prepareMetaReviewPayload(createManualTemplate(draftInput));
 assert.equal(request.operation,'CREATE_FOR_REVIEW');
 assert.equal(request.network_performed,false);
 assert.equal(request.approved,false);
 assert.equal(request.meta_account_ref,draftInput.meta_account_ref);
 assert.deepEqual(request.payload.components,[{
  type:'BODY',text:draftInput.body,example:{body_text:[draftInput.examples]},
 }]);
});
test('WA17-03: submission receipt is only IN_REVIEW, not Meta approval',()=>{
 const submittedTemplate=submitted();
 assert.equal(submittedTemplate.stage,'IN_REVIEW');
 assert.equal(submittedTemplate.provider_template_id,'456789012345678');
 assert.throws(()=>prepareApprovedTemplateParameters(submittedTemplate,{}),/TEMPLATE_NOT_APPROVED/);
 assert.throws(()=>prepareMetaReviewPayload(submittedTemplate),/SUBMISSION_ONLY_FOR_DRAFT/);
});
test('WA17-04: only matching template provider ID can accept status from trusted sync',()=>{
 const t=submitted();
 assert.throws(()=>applyVerifiedMetaStatus(t,'other','APPROVED'),/UNTRUSTED_STATUS_SCOPE/);
 assert.throws(()=>applyVerifiedMetaStatus(t,'456789012345678','HACKED' as 'APPROVED'),/UNKNOWN_META_STATUS/);
 assert.equal(applyVerifiedMetaStatus(t,'456789012345678','APPROVED').stage,'APPROVED');
});
test('WA17-05: rejection, pause, disable and pending each block preparation',()=>{
 for(const status of ['REJECTED','PAUSED','DISABLED','PENDING'] as const){
  const t=configureVariableSources(
   applyVerifiedMetaStatus(submitted(),'456789012345678',status),
   0,mappings,registry);
  assert.throws(()=>prepareApprovedTemplateParameters(t,{
   'cliente.nome':'Cliente Fictício','operador.nome':'Operador Fictício',
  }),/TEMPLATE_NOT_APPROVED/);
 }
});
test('WA17-06: mapping is editable independently and preserves approved text/status',()=>{
 const t=approved();
 const first=configureVariableSources(t,0,mappings,registry);
 const changed=configureVariableSources(first,1,[
  {position:1,source_key:'cliente.nome'},
  {position:2,source_key:'caso.codigo'},
 ],registry);
 assert.equal(changed.mapping_revision,2);
 assert.equal(changed.stage,'APPROVED');
 assert.equal(changed.body,draftInput.body);
 assert.equal(changed.provider_template_id,'456789012345678');
 assert.equal(first.mappings[1].source_key,'operador.nome');
});
test('WA17-07: new variables can come from extensible trusted registry, not arbitrary code',()=>{
 const t=configureVariableSources(approved(),0,[
  {position:1,source_key:'cliente.nome'},
  {position:2,source_key:'caso.codigo'},
 ],registry);
 const result=prepareApprovedTemplateParameters(t,{
  'cliente.nome':'Pessoa de Teste','caso.codigo':'PROTOCOLO-EXEMPLO',
 });
 assert.deepEqual(result.components,[{
  type:'body',parameters:[
   {type:'text',text:'Pessoa de Teste'},
   {type:'text',text:'PROTOCOLO-EXEMPLO'},
  ],
 }]);
 assert.equal(result.network_performed,false);
 assert.equal(result.send_authorized,false);
});
test('WA17-08: missing variable values fail closed; never send raw placeholders',()=>{
 const t=configureVariableSources(approved(),0,mappings,registry);
 assert.throws(()=>prepareApprovedTemplateParameters(t,{'cliente.nome':'Teste'}),
   /MISSING_VARIABLE_VALUE/);
 assert.throws(()=>prepareApprovedTemplateParameters(t,{
  'cliente.nome':'Teste','operador.nome':'   ',
 }),/INVALID_VARIABLE_VALUE/);
});
test('WA17-09: cannot source values from disabled or unknown tenant registry keys',()=>{
 const t=approved();
 for(const source_key of ['sistema.token','outra_loja.nome','process.env','__proto__']){
  assert.throws(()=>configureVariableSources(t,0,[
   {position:1,source_key:'cliente.nome'},{position:2,source_key},
  ],registry),/UNREGISTERED_VARIABLE_SOURCE/);
 }
});
test('WA17-10: optimistic concurrency blocks stale operator mapping edits',()=>{
 const t=configureVariableSources(approved(),0,mappings,registry);
 assert.throws(()=>configureVariableSources(t,0,mappings,registry),
   /STALE_MAPPING_REVISION/);
});
test('WA17-11: no gap/zero/missing examples in placeholders',()=>{
 for(const body of ['Olá {{2}}','Olá {{0}}','{{1}} {{3}}','Olá {{nome}}','Oi {{1']){
  assert.throws(()=>createManualTemplate({...draftInput,body}),/VARIABLES_|INVALID_PLACEHOLDER|MISSING_META_EXAMPLES/);
 }
 assert.throws(()=>createManualTemplate({...draftInput,examples:['A']}),/MISSING_META_EXAMPLES/);
});
test('WA17-12: text changes create a new draft, with new version and approval cycle',()=>{
 const first=configureVariableSources(approved(),0,mappings,registry);
 const newer=createEditedContentVersion(first,{
  ...draftInput,local_id:'f7200000-0000-4000-8000-000000000002',
  name:'contato_manual_b',body:'Mensagem alterada por responsável: {{1}}.',
  examples:['Pessoa Exemplo'],
 });
 assert.equal(newer.content_version,2);
 assert.equal(newer.stage,'DRAFT');
 assert.equal(newer.provider_template_id,null);
 assert.equal(newer.mapping_revision,0);
 assert.equal(newer.mappings.length,0);
 assert.equal(first.stage,'APPROVED');
 assert.equal(first.body,draftInput.body);
});
test('WA17-13: content version cannot cross concessionaria or Meta account',()=>{
 const prior=approved();
 const next={...draftInput,local_id:'f7200000-0000-4000-8000-000000000003',name:'contato_v3'};
 assert.throws(()=>createEditedContentVersion(prior,{
  ...next,concessionaria_id:'f7200000-0000-4000-8000-000000000011',
 }),/CROSS_TENANT_EDIT_DENIED/);
 assert.throws(()=>createEditedContentVersion(prior,{
  ...next,meta_account_ref:'223456789012345',
 }),/CROSS_TENANT_EDIT_DENIED/);
});
test('WA17-14: cannot reuse ID/name as new approved content version',()=>{
 assert.throws(()=>createEditedContentVersion(approved(),draftInput),/NEW_CONTENT_REQUIRES/);
});
test('WA17-15: validation prohibits unsupported special categories for v0',()=>{
 assert.throws(()=>createManualTemplate({...draftInput,category:'AUTHENTICATION' as 'UTILITY'}),/UNSUPPORTED_CATEGORY/);
 assert.throws(()=>createManualTemplate({...draftInput,name:'Wrong Case'}),/INVALID_TEMPLATE_NAME/);
});
test('WA17-16: approve alone never authorizes sending without mapping or consent gates',()=>{
 const t=approved();
 assert.throws(()=>prepareApprovedTemplateParameters(t,{}),/UNCONFIGURED_VARIABLES/);
 const mapped=configureVariableSources(t,0,mappings,registry);
 const p=prepareApprovedTemplateParameters(mapped,{
  'cliente.nome':'Pessoa Fictícia','operador.nome':'Pessoa Operadora',
 });
 assert.equal(p.send_authorized,false);
 assert.equal('access_token' in p,false);
 assert.equal('recipient' in p,false);
});
