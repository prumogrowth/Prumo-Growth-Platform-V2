import test from 'node:test';
import assert from 'node:assert/strict';
import { composeMcpTemplateDraft,prepareMcpTemplateReview,
  mapMcpTemplateSources,MCP_TEMPLATE_TOOLS,TEMPLATE_CAPABILITIES,
} from './template-mcp-multiformat.ts';
import type {MultiFormatInput} from './template-mcp-multiformat.ts';
const base:MultiFormatInput={
 local_id:'f8200000-0000-4000-8000-000000000001',
 concessionaria_id:'f8200000-0000-4000-8000-000000000002',
 waba_ref:'1234567890000',name:'oferta_ia_draft',
 language:'pt_BR',category:'MARKETING',origin:'AI_GENERATED',
 body:{text:'Olá {{1}}, você pode falar com {{2}}.',examples:['Pessoa Teste','Operador Teste']},
 header:{kind:'IMAGE',asset_ref:'asset_synthetic_image_01'},
 footer:'Equipe de atendimento',
 buttons:[
  {kind:'URL',label:'Saiba mais',url:'https://example.com/consulta/{{1}}',
   example_suffix:'protocolo_teste'},
  {kind:'QUICK_REPLY',label:'Falar com atendente'},
 ],
};
test('WA17B-01: AI-generated authoring can create drafts through future MCP service',()=>{
 const draft=composeMcpTemplateDraft(base);
 assert.equal(draft.stage,'DRAFT');
 assert.equal(draft.meta_approved,false);
 assert.equal(draft.network_performed,false);
 assert.equal(draft.input.origin,'AI_GENERATED');
 assert.deepEqual(draft.slots.map(x=>x.slot_key),
  ['body.1','body.2','button.0.url.1']);
});
test('WA17B-02: Meta review includes IMAGE header, human-visible URL button and URL suffix example',()=>{
 const draft=composeMcpTemplateDraft(base);
 assert.throws(()=>prepareMcpTemplateReview(draft),/VERIFIED_MEDIA_HANDLE_REQUIRED/);
 const result=prepareMcpTemplateReview(draft,'4::synthetic_verified_handle');
 assert.equal(result.operation,'PREPARE_META_REVIEW');
 assert.equal(result.requires_mcp_service_auth,true);
 assert.equal(result.network_performed,false);
 assert.equal(result.meta_approved,false);
 assert.equal(result.send_authorized,false);
 const components=result.payload.components as any[];
 assert.deepEqual(components.map(x=>x.type),['HEADER','BODY','FOOTER','BUTTONS']);
 assert.deepEqual(components[0],{type:'HEADER',format:'IMAGE',
  example:{header_handle:['4::synthetic_verified_handle']}});
 assert.deepEqual(components[3].buttons[0],{
  type:'URL',text:'Saiba mais',url:'https://example.com/consulta/{{1}}',
  example:['https://example.com/consulta/protocolo_teste'],
 });
});
test('WA17B-03: header VIDEO and DOCUMENT are structural alternatives',()=>{
 for(const kind of ['VIDEO','DOCUMENT'] as const){
  const d=composeMcpTemplateDraft({...base,header:{kind,asset_ref:'asset_demo_safe_17'}});
  const p=prepareMcpTemplateReview(d,'4::synthetic_verified_handle');
  assert.equal((p.payload.components[0] as any).format,kind);
 }
});
test('WA17B-04: header TEXT and static URL plus phone button can coexist',()=>{
 const d=composeMcpTemplateDraft({...base,
  header:{kind:'TEXT',text:'Atendimento {{1}}',example:'Atendente Teste'},
  buttons:[
   {kind:'URL',label:'Abrir site',url:'https://example.com/home'},
   {kind:'PHONE_NUMBER',label:'Ligar',phone_number:'+5581999999999'},
  ],
 });
 assert.deepEqual(d.slots.map(x=>x.slot_key),['body.1','body.2','header.1']);
 const p=prepareMcpTemplateReview(d);
 assert.deepEqual((p.payload.components[0] as any).example,{header_text:['Atendente Teste']});
 assert.equal((p.payload.components[3] as any).buttons[1].phone_number,'+5581999999999');
});
test('WA17B-05: variable sources include body and URL button separately',()=>{
 const draft=composeMcpTemplateDraft(base);
 const mapped=mapMcpTemplateSources(draft,0,{
  'body.1':'cliente.nome','body.2':'operador.nome',
  'button.0.url.1':'caso.codigo',
 },['cliente.nome','operador.nome','caso.codigo']);
 assert.equal(mapped.mapping_revision,1);
 assert.equal(mapped.mappings['button.0.url.1'],'caso.codigo');
 assert.equal(mapped.input.body.text,base.body.text);
 assert.equal(mapped.input.buttons?.[0].label,'Saiba mais');
 assert.throws(()=>mapMcpTemplateSources(mapped,0,{},[]),/STALE_MAPPING_REVISION/);
});
test('WA17B-06: values are limited to trusted scoped variable registry',()=>{
 const draft=composeMcpTemplateDraft(base);
 assert.throws(()=>mapMcpTemplateSources(draft,0,{
  'body.1':'cliente.nome','body.2':'operador.nome',
  'button.0.url.1':'process.env',
 },['cliente.nome','operador.nome','caso.codigo']),/INVALID_OR_UNAUTHORIZED_MAPPING/);
});
test('WA17B-07: missing dynamic URL example, unsafe host or credentials fail closed',()=>{
 const replaceButton=(url:string,example_suffix?:string):MultiFormatInput=>({...base,
  buttons:[{kind:'URL',label:'Saiba mais',url,...(example_suffix?{example_suffix}:{})}],
 });
 assert.throws(()=>composeMcpTemplateDraft(replaceButton('https://example.com/{{1}}')),
  /INVALID_URL_EXAMPLE_SUFFIX/);
 assert.throws(()=>composeMcpTemplateDraft(replaceButton('http://example.com/{{1}}','ok')),
  /UNSAFE_URL/);
 assert.throws(()=>composeMcpTemplateDraft(replaceButton('https://localhost/{{1}}','ok')),
  /UNSAFE_URL/);
 assert.throws(()=>composeMcpTemplateDraft(replaceButton('https://name:secret@example.com/{{1}}','ok')),
  /UNSAFE_URL/);
});
test('WA17B-08: URL variables only in final suffix, no arbitrary link constructions',()=>{
 assert.throws(()=>composeMcpTemplateDraft({...base,buttons:[
  {kind:'URL',label:'Abrir',url:'https://example.com/{{1}}/extra',example_suffix:'safe'},
 ]}),/DYNAMIC_URL_REQUIRES_FINAL_SUFFIX/);
});
test('WA17B-09: unsupported Flow, catalog, auth and location require specialized contract',()=>{
 for(const kind of ['FLOW','COPY_CODE','CATALOG'] as const){
  assert.throws(()=>composeMcpTemplateDraft({...base,
   buttons:[{kind,label:'Futuro'}] as any}),/BUTTON_REQUIRES_SPECIALIZED_VALIDATOR/);
 }
 assert.throws(()=>composeMcpTemplateDraft({...base,
  header:{kind:'LOCATION',asset_ref:'asset_dummy_example'} as any}),
  /HEADER_REQUIRES_SPECIALIZED_VALIDATOR/);
 assert.ok(TEMPLATE_CAPABILITIES.reserved_requires_separate_validator.includes('AUTHENTICATION'));
});
test('WA17B-10: preview never silently grants Meta approval or send authorization',()=>{
 const d=composeMcpTemplateDraft({...base,origin:'HUMAN_SPECIFIED'});
 assert.equal(d.meta_approved,false);
 assert.equal(d.input.origin,'HUMAN_SPECIFIED');
 const v=prepareMcpTemplateReview(d,'4::synthetic_verified_handle');
 assert.equal(v.meta_approved,false);
 assert.equal(v.send_authorized,false);
});
test('WA17B-11: reject extra data, getters and arbitrary MCP-origin token fields',()=>{
 assert.throws(()=>composeMcpTemplateDraft({...base,access_token:'secret'} as MultiFormatInput),
  /UNEXPECTED_FIELDS_OR_GETTERS/);
 const hostile={...base};
 Object.defineProperty(hostile,'body',{get(){throw Error('EXPLOIT_GETTER');}});
 assert.throws(()=>composeMcpTemplateDraft(hostile as MultiFormatInput),
  /UNEXPECTED_FIELDS_OR_GETTERS/);
});
test('WA17B-12: labels and position counts enforced; no invisible unsupported params',()=>{
 assert.throws(()=>composeMcpTemplateDraft({...base,buttons:[
  {kind:'QUICK_REPLY',label:'Sim'},{kind:'QUICK_REPLY',label:'Sim'},
 ]}),/DUPLICATE_BUTTON_LABEL/);
 assert.throws(()=>composeMcpTemplateDraft({...base,body:{
  text:'Olá {{2}}',examples:['A'],
 }}),/NONCONTIGUOUS_POSITIONS/);
});
test('WA17B-13: MCP tool contract includes review and independent mappings',()=>{
 assert.ok(MCP_TEMPLATE_TOOLS.includes('templates.create_draft'));
 assert.ok(MCP_TEMPLATE_TOOLS.includes('templates.configure_variable_sources'));
 assert.ok(MCP_TEMPLATE_TOOLS.includes('templates.submit_for_meta_review'));
 assert.ok(MCP_TEMPLATE_TOOLS.includes('templates.sync_meta_status'));
 assert.equal(TEMPLATE_CAPABILITIES.network_implemented,false);
 assert.equal(TEMPLATE_CAPABILITIES.message_send_implemented,false);
});
test('WA17B-14: Meta body can be human-provided, AI-assisted or generated',()=>{
 for(const origin of ['HUMAN_SPECIFIED','AI_ASSISTED','AI_GENERATED'] as const){
  const d=composeMcpTemplateDraft({...base,origin});
  assert.equal(d.input.origin,origin);
 }
});

test('WA17B-15: reject IP literals, internal domains and repeated URL placeholders',()=>{
 for(const url of [
  'https://127.0.0.2/visit/{{1}}',
  'https://service.internal/visit/{{1}}',
  'https://[::1]/visit/{{1}}',
 ]){
  assert.throws(()=>composeMcpTemplateDraft({...base,buttons:[
   {kind:'URL',label:'Abrir',url,example_suffix:'test'}
  ]}),/UNSAFE_URL/);
 }
 assert.throws(()=>composeMcpTemplateDraft({...base,buttons:[
  {kind:'URL',label:'Abrir',url:'https://example.com/{{1}}/{{1}}',
   example_suffix:'test'}
 ]}),/DYNAMIC_URL_REQUIRES_FINAL_SUFFIX/);
});
test('WA17B-16: JSON-described MCP tools are contracts, not privileged executable tools',async()=>{
 const {readFileSync}=await import('node:fs');
 const spec=JSON.parse(readFileSync(
   new URL('./mcp-template-tools.v0.json',import.meta.url),'utf8'));
 assert.equal(spec.status,'CONTRACT_ONLY_NOT_AN_INSTALLED_MCP_SERVER');
 assert.equal(spec.no_real_meta_calls,true);
 assert.equal(spec.operations.length,12);
 assert.equal(spec.operations.some((x:{name:string})=>
   x.name==='templates.submit_for_meta_review'),true);
 for(const tool of spec.operations){
  assert.equal(tool.inputSchema.additionalProperties,false);
  assert.equal('principal_id' in tool.inputSchema.properties,false);
  assert.equal('access_token' in tool.inputSchema.properties,false);
 }
});
