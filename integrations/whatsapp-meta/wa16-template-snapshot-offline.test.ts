import test from 'node:test';
import assert from 'node:assert/strict';
import {freezeWa16TemplateOffline as freeze,
 recheckWa16TemplateOffline as recheck} from './wa16-template-snapshot-offline.ts';
const NOW=1800000000000;
const SHOP='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const OTHER_SHOP='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
const ID='dddddddd-dddd-4ddd-8ddd-dddddddddddd';
const img=(kind='IMAGE')=>({
 kind,asset_ref:'asset_demo_123456',mime_type:'image/jpeg',
 sha256:'a'.repeat(64),asset_revision:4,
 valid_from_ms:NOW-20000,valid_until_ms:NOW+20000,
 observed_at_ms:NOW-1000,state:'LAB_READY',
});
const fixture=()=>({
 contract_version:'wa16-template-freeze.lab.v0.1',
 selection_ref:'SELECTION_A',concessionaria_id:SHOP,waba_ref:'100001',
 template_ref:'TEMPLATE_A',version_ref:'VERSION_2',
 content_version:2,mapping_revision:3,media_revision:0,
 now_ms:NOW,max_age_ms:60000,
 authoring:{
  local_id:ID,concessionaria_id:SHOP,waba_ref:'100001',
  name:'demo_update',language:'pt_BR',category:'UTILITY',
  origin:'AI_ASSISTED',
  body:{text:'Ola {{1}}, codigo {{2}}',examples:['Exemplo','ABC123']},
  header:{kind:'TEXT',text:'Aviso {{1}}',example:'Exemplo'},
  footer:'Atendimento',buttons:[{
   kind:'URL',label:'Verificar',url:'https://example.com/item/{{1}}',
   example_suffix:'example123',
  },{kind:'QUICK_REPLY',label:'Agora'}],
 },
 bindings:{'body.1':'cliente.nome','body.2':'caso.codigo',
  'header.1':'cliente.nome','button.0.url.1':'caso.codigo'},
 source_registry:['cliente.nome','caso.codigo'],
 media_evidence:null,review_state:'LAB_REPORTED_APPROVED',
});
type Result=ReturnType<typeof freeze>;
function noAuthority(r:Result){
 for(const k of ['send_authorized','production_authorized',
  'meta_approval_verified','media_verified',
  'mcp_execution_authorized'] as const)assert.equal(r[k],false,k);
 assert.equal(Object.isFrozen(r),true);
 const wire=JSON.stringify(r);
 for(const value of ['Ola {{1}}','example.com','cliente.nome',
  'caso.codigo','asset_demo_123456','ABC123','Exemplo'])
  assert.equal(wire.includes(value),false,value);
}
function good(r:Result,decision:'LAB_FROZEN_SNAPSHOT_UNVERIFIED'|
 'LAB_RECHECKED_UNVERIFIED'='LAB_FROZEN_SNAPSHOT_UNVERIFIED'){
 noAuthority(r);assert.equal(r.decision,decision);
 assert.equal(r.reason,null);assert.ok(r.candidate);
 assert.equal(Object.isFrozen(r.candidate),true);
 assert.equal(r.candidate!.send_authorized,false);
 for(const key of ['component_sha256','binding_sha256','media_sha256',
  'snapshot_sha256'] as const)assert.match(r.candidate![key],/^[a-f0-9]{64}$/);
 return r.candidate!;
}
function denied(r:Result,reason?:string){
 noAuthority(r);assert.equal(r.decision,'DENIED');
 if(reason)assert.equal(r.reason,reason);
 assert.equal(r.candidate,null);
}
const inspect=(f:unknown=fixture())=>freeze(f);
const check=(f:ReturnType<typeof fixture>,alter?:ReturnType<typeof fixture>)=>{
 const first=good(inspect(f));
 return recheck(first,alter??fixture());
};
test('M16-01 frozen content/binding snapshot is LAB only',()=>{
 const x=good(inspect());assert.equal(x.slot_count,4);
 assert.equal(x.media_kind,'NONE');assert.equal(x.mapping_revision,3);
});
test('M16-02 stable fresh fixture rechecks but never authorizes',()=>{
 const f=fixture();good(check(f),'LAB_RECHECKED_UNVERIFIED');
});
test('M16-03 changed BODY under same version denied',()=>{
 const f=fixture(),g=fixture();g.authoring.body.text='Alterado {{1}} {{2}}';
 denied(check(f,g),'VERSION_OR_SNAPSHOT_CHANGED');
});
test('M16-04 changed HEADER text under same version denied',()=>{
 const f=fixture(),g=fixture();g.authoring.header.text='Outro {{1}}';
 denied(check(f,g),'VERSION_OR_SNAPSHOT_CHANGED');
});
test('M16-05 FOOTER changed under same version denied',()=>{
 const f=fixture(),g=fixture();g.authoring.footer='Mudou';
 denied(check(f,g),'VERSION_OR_SNAPSHOT_CHANGED');
});
test('M16-06 quick reply label mutation denied',()=>{
 const f=fixture(),g=fixture();
 g.authoring.buttons[1].label='Depois';
 denied(check(f,g),'VERSION_OR_SNAPSHOT_CHANGED');
});
test('M16-07 static URL host change denied',()=>{
 const f=fixture(),g=fixture();
 g.authoring.buttons[0].url='https://other.example.org/item/{{1}}';
 denied(check(f,g),'VERSION_OR_SNAPSHOT_CHANGED');
});
test('M16-08 dynamic suffix sample change denied',()=>{
 const f=fixture(),g=fixture();
 g.authoring.buttons[0].example_suffix='new123';
 denied(check(f,g),'VERSION_OR_SNAPSHOT_CHANGED');
});
test('M16-09 changed sample example alters content digest',()=>{
 const f=fixture(),g=fixture();
 g.authoring.body.examples[0]='OutroExemplo';
 denied(check(f,g),'VERSION_OR_SNAPSHOT_CHANGED');
});
test('M16-10 changed allowed variable binding denied',()=>{
 const f=fixture(),g=fixture();
 g.bindings['body.1']='caso.codigo';
 denied(check(f,g),'VERSION_OR_SNAPSHOT_CHANGED');
});
test('M16-11 changed content revision denied',()=>{
 const f=fixture(),g=fixture();
 g.content_version=3;
 denied(check(f,g),'VERSION_OR_SNAPSHOT_CHANGED');
});
test('M16-12 changed mapping revision denied',()=>{
 const f=fixture(),g=fixture();
 g.mapping_revision=4;
 denied(check(f,g),'VERSION_OR_SNAPSHOT_CHANGED');
});
test('M16-13 changed template_ref denied',()=>{
 const f=fixture(),g=fixture();g.template_ref='TEMPLATE_B';
 denied(check(f,g),'VERSION_OR_SNAPSHOT_CHANGED');
});
test('M16-14 changed WABA denied',()=>{
 const f=fixture(),g=fixture();g.waba_ref='100002';g.authoring.waba_ref='100002';
 denied(check(f,g),'VERSION_OR_SNAPSHOT_CHANGED');
});
test('M16-15 changed concessionaria denied',()=>{
 const f=fixture(),g=fixture();g.concessionaria_id=OTHER_SHOP;
 g.authoring.concessionaria_id=OTHER_SHOP;
 denied(check(f,g),'VERSION_OR_SNAPSHOT_CHANGED');
});
test('M16-16 cross-tenant authoring mismatch denied',()=>{
 const f=fixture();f.authoring.concessionaria_id=OTHER_SHOP;
 denied(inspect(f),'SCOPE_MISMATCH');
});
test('M16-17 invalid sources outside registry denied',()=>{
 const f=fixture();f.bindings['body.1']='financeiro.segredo';
 denied(inspect(f),'COMPONENTS_OR_BINDINGS_DENIED');
});
test('M16-18 missing binding denied',()=>{
 const f:any=fixture();delete f.bindings['header.1'];
 denied(inspect(f),'COMPONENTS_OR_BINDINGS_DENIED');
});
test('M16-19 noncontiguous slots denied',()=>{
 const f=fixture();f.authoring.body.text='Ola {{3}}';
 denied(inspect(f),'COMPONENTS_OR_BINDINGS_DENIED');
});
test('M16-20 unsupported location header denied',()=>{
 const f:any=fixture();
 f.authoring.header={kind:'LOCATION',asset_ref:'asset_demo_123456'};
 denied(inspect(f),'COMPONENTS_OR_BINDINGS_DENIED');
});
test('M16-21 invalid URL scheme denied',()=>{
 const f=fixture();f.authoring.buttons[0].url='http://example.com/item/{{1}}';
 denied(inspect(f),'COMPONENTS_OR_BINDINGS_DENIED');
});
test('M16-22 duplicate button labels denied',()=>{
 const f=fixture();f.authoring.buttons[1].label='Verificar';
 denied(inspect(f),'COMPONENTS_OR_BINDINGS_DENIED');
});
test('M16-23 media IMAGE with matching fixture builds digest',()=>{
 const f:any=fixture();f.authoring.header={
  kind:'IMAGE',asset_ref:'asset_demo_123456'};
 f.media_evidence=img();f.media_revision=4;
 const c=good(inspect(f));assert.equal(c.media_kind,'IMAGE');
 assert.equal(c.media_revision,4);
});
test('M16-24 media digest changes when asset checksum changes',()=>{
 const f:any=fixture();f.authoring.header={
  kind:'IMAGE',asset_ref:'asset_demo_123456'};
 f.media_evidence=img();f.media_revision=4;
 const c=good(inspect(f)),g:any=structuredClone(f);
 g.media_evidence.sha256='b'.repeat(64);
 denied(recheck(c,g),'VERSION_OR_SNAPSHOT_CHANGED');
});
test('M16-25 media revision differs from claim denied',()=>{
 const f:any=fixture();f.authoring.header={
  kind:'IMAGE',asset_ref:'asset_demo_123456'};
 f.media_evidence=img();f.media_revision=5;
 denied(inspect(f),'MEDIA_EVIDENCE_DENIED');
});
test('M16-26 absent media evidence denies media draft',()=>{
 const f:any=fixture();f.authoring.header={
  kind:'IMAGE',asset_ref:'asset_demo_123456'};
 f.media_revision=4;
 denied(inspect(f),'MEDIA_EVIDENCE_DENIED');
});
test('M16-27 media asset scope/name mismatch denied',()=>{
 const f:any=fixture();f.authoring.header={
  kind:'IMAGE',asset_ref:'asset_other_123456'};
 f.media_revision=4;f.media_evidence=img();
 denied(inspect(f),'MEDIA_EVIDENCE_DENIED');
});
test('M16-28 media MIME inconsistent with declared kind denied',()=>{
 const f:any=fixture();f.authoring.header={
  kind:'VIDEO',asset_ref:'asset_demo_123456'};
 f.media_revision=4;f.media_evidence={...img('VIDEO'),mime_type:'image/jpeg'};
 denied(inspect(f),'MEDIA_EVIDENCE_DENIED');
});
test('M16-29 media expiry denied',()=>{
 const f:any=fixture();f.authoring.header={
  kind:'IMAGE',asset_ref:'asset_demo_123456'};
 f.media_revision=4;f.media_evidence={...img(),valid_until_ms:NOW};
 denied(inspect(f),'MEDIA_EVIDENCE_DENIED');
});
test('M16-30 stale media observation denied',()=>{
 const f:any=fixture();f.authoring.header={
  kind:'IMAGE',asset_ref:'asset_demo_123456'};
 f.media_revision=4;f.media_evidence={...img(),observed_at_ms:NOW-60001};
 denied(inspect(f),'MEDIA_EVIDENCE_DENIED');
});
test('M16-31 VIDEO with media/sample local fixture accepted only LAB',()=>{
 const f:any=fixture();f.authoring.header={
  kind:'VIDEO',asset_ref:'asset_demo_123456'};
 f.media_revision=4;f.media_evidence={...img('VIDEO'),mime_type:'video/mp4'};
 const c=good(inspect(f));assert.equal(c.media_kind,'VIDEO');
});
test('M16-32 DOCUMENT with PDF allowed LAB metadata only',()=>{
 const f:any=fixture();f.authoring.header={
  kind:'DOCUMENT',asset_ref:'asset_demo_123456'};
 f.media_revision=4;f.media_evidence={...img('DOCUMENT'),
  mime_type:'application/pdf'};
 const c=good(inspect(f));assert.equal(c.media_kind,'DOCUMENT');
});
test('M16-33 media evidence with TEXT header denied',()=>{
 const f:any=fixture();f.media_evidence=img();
 denied(inspect(f),'MEDIA_EVIDENCE_DENIED');
});
test('M16-34 unexpected authority field denied',()=>{
 const f:any=fixture();f.meta_approval_verified=true;
 denied(inspect(f),'INVALID_INPUT');
});
test('M16-35 root getter denied without invocation',()=>{
 const f:any=fixture();let hits=0;
 Object.defineProperty(f,'selection_ref',{enumerable:true,get(){hits++;return 'SELECTION_A';}});
 denied(inspect(f),'INVALID_INPUT');assert.equal(hits,0);
});
test('M16-36 nested BODY getter denied without invocation',()=>{
 const f:any=fixture();let hits=0;
 Object.defineProperty(f.authoring.body,'text',{enumerable:true,get(){
  hits++;return 'Ola {{1}} {{2}}';}});
 denied(inspect(f),'INVALID_INPUT');assert.equal(hits,0);
});
test('M16-37 sparse buttons array denied',()=>{
 const f:any=fixture();f.authoring.buttons.length=3;
 denied(inspect(f),'INVALID_INPUT');
});
test('M16-38 cyclic input denied without recursion',()=>{
 const f:any=fixture();f.authoring.loop=f.authoring;
 denied(inspect(f),'INVALID_INPUT');
});
test('M16-39 candidate fake authorization fields cannot recheck',()=>{
 const c:any=good(inspect());const f=fixture();
 denied(recheck({...c,send_authorized:true},f),'INVALID_CANDIDATE');
});
test('M16-40 candidate added provider-approval flag denied',()=>{
 const c:any=good(inspect());const f=fixture();
 denied(recheck({...c,provider_sync:true},f),'INVALID_CANDIDATE');
});
test('M16-41 hostile WABA candidate object never coerced',()=>{
 const c:any=good(inspect());const f=fixture();let hits=0;
 denied(recheck({...c,waba_ref:{toString(){hits++;return '100001';}}},f),
  'INVALID_CANDIDATE');
 assert.equal(hits,0);
});
test('M16-42 media evidence cannot be treated as verified Meta upload',()=>{
 const f:any=fixture();f.authoring.header={
  kind:'IMAGE',asset_ref:'asset_demo_123456'};
 f.media_revision=4;f.media_evidence=img();
 const r=inspect(f),c=good(r);
 assert.equal(c.media_verified,false);
 assert.equal(c.meta_approval_verified,false);
 assert.equal(c.mcp_execution_authorized,false);
});
