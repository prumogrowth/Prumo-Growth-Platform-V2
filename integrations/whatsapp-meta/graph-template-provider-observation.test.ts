/** Offline-only, no Graph credentials, GET requests, database or catalog trust. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectMetaTemplateProviderRecord as inspect} from './graph-template-provider-observation.ts';
const match={provider_template_id:'123456789012',template_name:'fixture_followup',
 language_code:'pt_BR'};
const fixture=()=>({
 id:'123456789012',name:'fixture_followup',language:'pt_BR',status:'APPROVED',
 category:'UTILITY',parameter_format:'POSITIONAL',
 components:[
  {type:'HEADER',format:'TEXT',text:'Atendimento {{1}}',example:{header_text:['Equipe fictícia']}},
  {type:'BODY',text:'Olá {{1}}',example:{body_text:[['Pessoa fictícia']]}},
  {type:'FOOTER',text:'Exemplo'},
  {type:'BUTTONS',buttons:[{type:'QUICK_REPLY',text:'Continuar'},
    {type:'QUICK_REPLY',text:'Encerrar'}]},
 ],
});
const run=(x:unknown=fixture(),e:unknown=match)=>inspect(x,e);
function noAuthority(r:ReturnType<typeof inspect>){
 for(const k of ['meta_approval_verified','production_authorized','send_authorized',
 'ack_allowed','retry_external','s0_write_authorized',
 'commercial_effect_authorized'] as const)assert.equal(r[k],false,k);
 assert.equal(Object.isFrozen(r),true);
}
test('PROV-01 exact ID,name,language and text/buttons normalize as untrusted shape',()=>{
 const r=run();noAuthority(r);
 assert.equal(r.decision,'SHAPE_ONLY_UNVERIFIED');
 if(r.decision!=='SHAPE_ONLY_UNVERIFIED')throw Error('unexpected');
 assert.equal(r.observed.provider_source_authenticated,false);
 assert.equal(r.observed.provider_manifest_complete_verified,false);
 assert.equal(r.observed.reported_status,'APPROVED');
 assert.deepEqual(r.observed.approved_components_candidate,[
  {type:'HEADER',format:'TEXT',text:'Atendimento {{1}}'},
  {type:'BODY',text:'Olá {{1}}'},{type:'FOOTER',text:'Exemplo'},
  {type:'BUTTONS',buttons:[{type:'QUICK_REPLY',text:'Continuar'},
   {type:'QUICK_REPLY',text:'Encerrar'}]},
 ]);
 assert.equal(Object.isFrozen(r.observed.approved_components_candidate),true);
 assert.equal('source_ref' in r.observed,false);
 assert.equal('approval_evidence' in r.observed,false);
});
test('PROV-02 APPROVED text is not a verified approval; never authorizes a send',()=>{
 const r=run();noAuthority(r);
 assert.equal(r.decision,'SHAPE_ONLY_UNVERIFIED');
 if(r.decision!=='SHAPE_ONLY_UNVERIFIED')throw Error();
 assert.equal(JSON.stringify(r).includes('meta_approval_verified":true'),false);
});
test('PROV-03 status PAUSED, PENDING, REJECTED, DISABLED stay inert',()=>{
 for(const status of ['PAUSED','PENDING','REJECTED','DISABLED']){
  const r=run({...fixture(),status});noAuthority(r);
  assert.equal(r.decision,'SHAPE_ONLY_UNVERIFIED');
  if(r.decision!=='SHAPE_ONLY_UNVERIFIED')throw Error();
  assert.equal(r.observed.reported_status,status);
 }
});
test('PROV-04 mismatched ID/name/language fails closed',()=>{
 for(const change of [{id:'123456789013'},{name:'other_name'},{language:'en_US'}]){
  const r=run({...fixture(),...change});noAuthority(r);
  assert.equal(r.decision,'DENIED');
  if(r.decision!=='DENIED')throw Error();
  assert.equal(r.reason,'IDENTITY_MISMATCH');
  assert.equal(r.observed,null);
 }
});
test('PROV-05 no WABA on provider record: never infer cross-tenant binding',()=>{
 const r=run();noAuthority(r);
 assert.equal(r.decision,'SHAPE_ONLY_UNVERIFIED');
 if(r.decision!=='SHAPE_ONLY_UNVERIFIED')throw Error();
 for(const key of ['meta_waba_id','concessionaria_id','binding_revision','catalog_revision'])
  assert.equal(key in r.observed,false);
});
test('PROV-06 incomplete default response without components cannot be accepted',()=>{
 const v=fixture();delete (v as any).components;
 const r=run(v);noAuthority(r);
 assert.equal(r.decision,'DENIED');
});
test('PROV-07 duplicated, reordered or unsupported components denied',()=>{
 for(const components of [
  [...fixture().components,fixture().components[1]],
  [fixture().components[1],fixture().components[0]],
  [{type:'BODY',text:'corpo'},{type:'CAROUSEL',cards:[]}],
 ]){
  const r=run({...fixture(),components});noAuthority(r);
  assert.equal(r.decision,'DENIED',JSON.stringify(components));
 }
});
test('PROV-08 rejects URL/PHONE_NUMBER and unknown button properties',()=>{
 for(const buttons of [
  [{type:'URL',text:'Visitar',url:'https://example.invalid'}],
  [{type:'PHONE_NUMBER',text:'Ligar',phone_number:'000000'}],
  [{type:'QUICK_REPLY',text:'Continuar',payload:'FORGED'}],
 ]){
  const r=run({...fixture(),components:[
   {type:'BODY',text:'Mensagem'}, {type:'BUTTONS',buttons}]});noAuthority(r);
  assert.equal(r.decision,'DENIED');
 }
});
test('PROV-09 exactly three buttons allowed; four denied',()=>{
 const base={...fixture(),components:[{type:'BODY',text:'Ola'},
  {type:'BUTTONS',buttons:[{type:'QUICK_REPLY',text:'Um'},
   {type:'QUICK_REPLY',text:'Dois'},{type:'QUICK_REPLY',text:'Tres'}]}]};
 const a=run(base);noAuthority(a);assert.equal(a.decision,'SHAPE_ONLY_UNVERIFIED');
 const b=run({...base,components:[base.components[0],{
  type:'BUTTONS',buttons:[...(base.components[1] as any).buttons,
   {type:'QUICK_REPLY',text:'Quatro'}]}]});noAuthority(b);
 assert.equal(b.decision,'DENIED');
});
test('PROV-10 media header and dynamic provider format not silently converted',()=>{
 const r=run({...fixture(),components:[
  {type:'HEADER',format:'IMAGE',example:{header_handle:['test']}},
  {type:'BODY',text:'hello'}]});
 assert.equal(r.decision,'DENIED');noAuthority(r);
});
test('PROV-11 no BUTTONS allowed only if the observed record has none',()=>{
 const r=run({...fixture(),components:[{type:'BODY',text:'Só texto'}]});
 noAuthority(r);assert.equal(r.decision,'SHAPE_ONLY_UNVERIFIED');
 if(r.decision!=='SHAPE_ONLY_UNVERIFIED')throw Error();
 assert.deepEqual(r.observed.approved_components_candidate,[{type:'BODY',text:'Só texto'}]);
});
test('PROV-12 unknown meaningful component field fails closed',()=>{
 const r=run({...fixture(),components:[{type:'BODY',text:'Olá',
  required_action:'CLICK'}]});
 noAuthority(r);assert.equal(r.decision,'DENIED');
});
test('PROV-13 getter and injected top-level send permission never execute',()=>{
 let reads=0;
 const p=Object.defineProperty(fixture(),'status',{
  enumerable:true,get(){reads++;throw Error('SENSITIVE');},
 });
 const a=run(p);assert.equal(reads,0);noAuthority(a);assert.equal(a.decision,'DENIED');
 const b=run({...fixture(),send_authorized:true});noAuthority(b);
 assert.equal(b.decision,'DENIED');
});
test('PROV-14 malformed UTF-16, hidden symbols and prototype denied',()=>{
 const a=run({...fixture(),components:[{type:'BODY',text:'\uD800'}]});
 const b=run(Object.assign(Object.create({hasPermission:true}),fixture()));
 const c=run(Object.assign(fixture(),{[Symbol('META_SECRET')]:true}));
 for(const r of [a,b,c]){noAuthority(r);assert.equal(r.decision,'DENIED');}
});
test('PROV-15 invalid expected identity and partial match fail',()=>{
 const r=run(fixture(),{...match,language_code:'pt_BR',tenant:'FORGED'});
 const s=run(fixture(),{provider_template_id:'',template_name:match.template_name,
  language_code:match.language_code});
 for(const x of [r,s]){noAuthority(x);assert.equal(x.decision,'DENIED');}
});
test('PROV-16 missing category/ambiguous status cannot be silently completed',()=>{
 for(const change of [{category:'MYSTERY'},{status:'APPROVED?'}]){
  const r=run({...fixture(),...change});noAuthority(r);
  assert.equal(r.decision,'DENIED');
 }
});
test('PROV-17 input array is not a paginated response and fails closed',()=>{
 const r=run({data:[fixture()],paging:{next:'https://graph.facebook.com/etc'}});
 noAuthority(r);assert.equal(r.decision,'DENIED');
});
test('PROV-18 oversized text/data cannot silently be projected',()=>{
 const r=run({...fixture(),components:[{type:'BODY',text:'x'.repeat(8193)}]});
 noAuthority(r);assert.equal(r.decision,'DENIED');
});
