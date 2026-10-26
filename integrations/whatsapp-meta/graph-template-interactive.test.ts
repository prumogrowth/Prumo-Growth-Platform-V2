/** Cloud quick-reply template tests: inert Graph body, no Meta/S0 access. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {
 prepareGraphQuickReplyTemplateRequest as prepare,
 type TrustedQuickReplyCatalog,
} from './graph-template-interactive.ts';
import {TemplatePreflightError, type TemplateIntent,
 type TrustedTemplateSnapshot, type TrustedTemplateScope} from './graph-template.ts';

const scope:TrustedTemplateScope={
 concessionaria_id:'SHOP_A',canal_id:'CHANNEL_A',meta_app_ref:'APP_A',
 meta_waba_id:'WABA_A',phone_number_id:'123456789012',
};
const intent:TemplateIntent={
 contract_version:'meta-s0.v0.1-proposed',
 intent_id:'intent_01',attempt_id:'attempt_01',correlation_id:'corr_01',
 authorized_business_action:'C06',authorized_state_version:5,
 ...scope,recipient_verified:'5581900000000',
 template_name:'followup_botao',language_code:'pt_BR',
 template_revision_ref:'REV_1',body_text_parameters:['Cliente fictício'],
};
const base:TrustedTemplateSnapshot={
 template_name:intent.template_name,language_code:intent.language_code,
 template_revision_ref:intent.template_revision_ref,status:'APPROVED',
 parameter_format:'POSITIONAL_TEXT_ONLY',header_text_parameter_count:0,
 body_text_parameter_count:1,schema_complete:true,
 components:[{type:'BODY',format:'TEXT',parameter_count:1}],...scope,
};
const catalog:TrustedQuickReplyCatalog={
 contract:'prumo.meta.quickreply.catalog.offline.v1',
 approval:'APPROVED',schema_complete:true,
 template_name:intent.template_name,language_code:intent.language_code,
 template_revision_ref:intent.template_revision_ref,scope:{...scope},
 buttons:[{kind:'QUICK_REPLY',index:0,payload:'CHOICE_A'},
  {kind:'QUICK_REPLY',index:1,payload:'CHOICE_B'}],
};
const run=(i:TemplateIntent=intent,b:TrustedTemplateSnapshot=base,
 c:TrustedQuickReplyCatalog=catalog,s:TrustedTemplateScope=scope)=>
 prepare(i,b,s,c,'v24.0');
const invalid=(action:()=>unknown,code:TemplatePreflightError['code'])=>
 assert.throws(action,e=>e instanceof TemplatePreflightError&&e.code===code);
test('QR-01 builds official button components with ordinal indices and payload',()=>{
 const r=run();
 assert.equal(r.method,'POST');
 assert.equal(r.relative_path,'/v24.0/123456789012/messages');
 assert.deepEqual(r.body.template.components,[
  {type:'body',parameters:[{type:'text',text:'Cliente fictício'}]},
  {type:'button',sub_type:'quick_reply',index:'0',parameters:[{type:'payload',payload:'CHOICE_A'}]},
  {type:'button',sub_type:'quick_reply',index:'1',parameters:[{type:'payload',payload:'CHOICE_B'}]},
 ]);
 assert.equal('authorization' in r,false);
 assert.equal('headers' in r,false);
 assert.equal('url' in r,false);
 assert.equal(Object.isFrozen(r),true);
 assert.equal(Object.isFrozen(r.body.template.components),true);
});
test('QR-02 catalog static payload not taken from text content',()=>{
 const r=run({...intent,body_text_parameters:['OPCAO_1 USUARIO']});
 assert.equal(r.body.template.components[1].type,'button');
 assert.equal(JSON.stringify(r.body.template.components[1]).includes('OPCAO_1 USUARIO'),false);
});
test('QR-03 single button is supported, no phantom buttons',()=>{
 const r=run(intent,base,{...catalog,buttons:[catalog.buttons[0]]});
 assert.equal(r.body.template.components.length,2);
});
test('QR-04 maximum three approved quick reply buttons',()=>{
 const r=run(intent,base,{...catalog,buttons:[...catalog.buttons,
  {kind:'QUICK_REPLY',index:2,payload:'CHOICE_C'}]});
 assert.equal(r.body.template.components.length,4);
});
test('QR-05 rejects missing and four buttons as incomplete/unsupported',()=>{
 invalid(()=>run(intent,base,{...catalog,buttons:[]}), 'UNSUPPORTED_COMPONENTS');
 invalid(()=>run(intent,base,{...catalog,buttons:[...catalog.buttons,
  {kind:'QUICK_REPLY',index:2,payload:'C'},{kind:'QUICK_REPLY',index:3,payload:'D'}]}),
 'UNSUPPORTED_COMPONENTS');
});
test('QR-06 gaps or duplicate button indices cannot silently reorder',()=>{
 invalid(()=>run(intent,base,{...catalog,buttons:[
  {kind:'QUICK_REPLY',index:1,payload:'A'}]}),'INVALID_PARAMETERS');
 invalid(()=>run(intent,base,{...catalog,buttons:[
  {kind:'QUICK_REPLY',index:0,payload:'A'},{kind:'QUICK_REPLY',index:0,payload:'B'}]}),
 'INVALID_PARAMETERS');
});
test('QR-07 rejects dynamic URL or call-to-action masquerading as quick reply',()=>{
 invalid(()=>run(intent,base,{...catalog,buttons:[
  {kind:'URL',index:0,payload:'https://evil.invalid'} as never]}),
 'INVALID_PARAMETERS');
 invalid(()=>run(intent,base,{...catalog,buttons:[
  {kind:'QUICK_REPLY',index:0,payload:'https://evil.invalid'}]}),
 'INVALID_PARAMETERS');
});
test('QR-08 rejects whitespace, PII-ish or non-ASCII untrusted payloads',()=>{
 for(const payload of ['','has spaces','é','abc\nsecret','x'.repeat(129),'{\"customer\":\"PII\"}']){
  invalid(()=>run(intent,base,{...catalog,buttons:[
   {kind:'QUICK_REPLY',index:0,payload}]}),'INVALID_PARAMETERS');
 }
});
test('QR-09 refuses pending and stale catalog approval',()=>{
 for(const approval of ['PENDING','PAUSED','REJECTED',null]){
  invalid(()=>run(intent,base,{...catalog,approval} as never),'TEMPLATE_NOT_APPROVED');
 }
});
test('QR-10 rejects catalog template/name/language/revision drift',()=>{
 for(const update of [
  {template_name:'other'}, {language_code:'en_US'},
  {template_revision_ref:'REV_2'},
 ]){
  invalid(()=>run(intent,base,{...catalog,...update}), 'TEMPLATE_REVISION_MISMATCH');
 }
});
test('QR-11 rejects WABA, tenant or phone scope drift from trusted source',()=>{
 for(const key of ['concessionaria_id','canal_id','meta_app_ref','meta_waba_id',
  'phone_number_id'] as const){
  invalid(()=>run(intent,base,{...catalog,scope:{...scope,[key]:'OTHER'}}),
   'SCOPE_MISMATCH');
 }
});
test('QR-12 also applies all existing text-only scope/version/recipient gates',()=>{
 invalid(()=>run({...intent,authorized_state_version:0}), 'INVALID_INTENT');
 invalid(()=>run({...intent,recipient_verified:'+5581900000000'}), 'INVALID_DESTINATION');
 invalid(()=>run({...intent,authorized_business_action:'C03' as never}), 'INVALID_INTENT');
});
test('QR-13 old snapshot PENDING cannot be promoted by button catalog',()=>{
 invalid(()=>run(intent,{...base,status:'PENDING'}),'TEMPLATE_NOT_APPROVED');
});
test('QR-14 text placeholder/schema mismatch fails before buttons',()=>{
 invalid(()=>run({...intent,body_text_parameters:[]}), 'INVALID_PARAMETERS');
 invalid(()=>run(intent,{...base,body_text_parameter_count:2}), 'UNSUPPORTED_COMPONENTS');
});
test('QR-15 unknown text base components cannot masquerade as approved buttons',()=>{
 invalid(()=>run(intent,{...base,components:[...base.components,
  {type:'FOOTER',format:'TEXT',parameter_count:0},
  {type:'HEADER',format:'IMAGE',parameter_count:1} as never]}),
 'UNSUPPORTED_COMPONENTS');
});
test('QR-16 unknown catalog fields and foreign button metadata fail closed',()=>{
 invalid(()=>run(intent,base,{...catalog,unknown_grant:true} as never),
 'UNSUPPORTED_COMPONENTS');
 invalid(()=>run(intent,base,{...catalog,buttons:[
  {...catalog.buttons[0],link:'https://attack.invalid'} as never]}),
 'UNSUPPORTED_COMPONENTS');
});
test('QR-17 direct caller extra button payload rejected before base preparation',()=>{
 invalid(()=>run({...intent,button_payload:'FORGED'} as never),
 'UNSUPPORTED_COMPONENTS');
});
test('QR-18 accessor and exotic catalog prototype cannot smuggle permission',()=>{
 const bad=Object.defineProperty({...catalog},'approval',{
  enumerable:true,get(){throw Error('SHOULD_NOT_RUN');}});
 invalid(()=>run(intent,base,bad),'UNSUPPORTED_COMPONENTS');
 invalid(()=>run(intent,base,Object.assign(Object.create({grant:true}),catalog)),
 'UNSUPPORTED_COMPONENTS');
});
