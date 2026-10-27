/** All fixtures are fabricated. No Graph/WABA lookup, token or network. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectMetaTemplateListPage as page,
 inspectMetaTemplateListPageSet as pages} from './graph-template-list-page.ts';

const t=(id:string,name:string,language='pt_BR')=>({
 id,name,language,status:'APPROVED',category:'UTILITY',
 components:[{type:'BODY',text:'Olá {{1}}'}],
 quality_score:{score:'GREEN'},
});
const one=()=>({data:[t('123456789012','fixture_a'),t('123456789013','fixture_b')]});
const second=()=>({data:[t('123456789014','fixture_c')]});
const withNext=(value:any)=>({...value,paging:{
 cursors:{before:'OPAQUE_BEFORE',after:'OPAQUE_AFTER'},
 next:'https://graph.facebook.com/v25.0/99999/message_templates?after=SECRET_ACCESS_TOKEN',
}});
const flag=(v:ReturnType<typeof page>|ReturnType<typeof pages>)=>{
 assert.equal(Object.isFrozen(v),true);
 for(const k of ['meta_approval_verified','production_authorized','send_authorized',
  'ack_allowed','retry_external','s0_write_authorized',
  'commercial_effect_authorized','waba_binding_verified',
  'page_chain_authenticated','page_set_complete_verified'] as const)
  assert.equal(v[k],false,k);
 assert.equal(JSON.stringify(v).includes('SECRET_ACCESS_TOKEN'),false);
 assert.equal(JSON.stringify(v).includes('OPAQUE_AFTER'),false);
};
test('LIST-01 isolates candidate identity from statuses, components and URLs',()=>{
 const r=page(withNext(one()));flag(r);
 assert.equal(r.decision,'PAGE_IDENTITIES_UNVERIFIED');
 if(r.decision!=='PAGE_IDENTITIES_UNVERIFIED')throw Error();
 assert.equal(r.candidates.length,2);
 assert.deepEqual(r.candidates[0],{
  provider_template_id:'123456789012',template_name:'fixture_a',
  language_code:'pt_BR',needs_detail_by_id:true,
 });
 assert.equal(r.reported_next_present,true);
 assert.equal(JSON.stringify(r).includes('APPROVED'),false);
});
test('LIST-02 terminal-looking page is never completeness proof',()=>{
 const r=page(one());flag(r);
 assert.equal(r.decision,'PAGE_IDENTITIES_UNVERIFIED');
 if(r.decision!=='PAGE_IDENTITIES_UNVERIFIED')throw Error();
 assert.equal(r.reported_next_present,false);
 assert.equal(r.page_set_complete_verified,false);
});
test('LIST-03 collect two independent page shapes without following URL',()=>{
 const v=pages([withNext(one()),second()]);flag(v);
 assert.equal(v.decision,'PAGE_SET_IDENTITIES_UNVERIFIED');
 if(v.decision!=='PAGE_SET_IDENTITIES_UNVERIFIED')throw Error();
 assert.equal(v.pages_inspected,2);
 assert.equal(v.candidates.length,3);
 assert.equal(v.reported_last_page_without_next,true);
 assert.equal(v.page_chain_authenticated,false);
});
test('LIST-04 a claimed APPROVED status never proves Meta approval',()=>{
 const v=pages([one()]);flag(v);
 assert.equal(v.decision,'PAGE_SET_IDENTITIES_UNVERIFIED');
 assert.equal(v.meta_approval_verified,false);
});
test('LIST-05 pagination advertised but final page not provided is denied',()=>{
 const v=pages([withNext(one())]);flag(v);
 assert.equal(v.decision,'DENIED');
 if(v.decision!=='DENIED')throw Error();
 assert.equal(v.reason,'INCOMPLETE_PAGE_SET');
 assert.equal(v.candidates.length,0);
});
test('LIST-06 disjoint supplied pages without previous next claim are denied',()=>{
 const v=pages([one(),second()]);flag(v);
 assert.equal(v.decision,'DENIED');
 if(v.decision!=='DENIED')throw Error();
 assert.equal(v.reason,'INCOMPLETE_PAGE_SET');
});
test('LIST-07 duplicate IDs across pages are conflict, not deduped',()=>{
 const v=pages([withNext(one()),{data:[t('123456789013','fixture_other')]}]);flag(v);
 assert.equal(v.decision,'DENIED');
 if(v.decision!=='DENIED')throw Error();
 assert.equal(v.reason,'DUPLICATE_OR_CONFLICTING_IDENTITY');
});
test('LIST-08 duplicate locale+name across pages are conflict',()=>{
 const v=pages([withNext(one()),{data:[t('123456789099','fixture_a')]}]);flag(v);
 assert.equal(v.decision,'DENIED');
 if(v.decision!=='DENIED')throw Error();
 assert.equal(v.reason,'DUPLICATE_OR_CONFLICTING_IDENTITY');
});
test('LIST-09 duplicate IDs or locale+name inside one page are denied',()=>{
 for(const v of [
  {data:[t('123456789012','first'),t('123456789012','other')]},
  {data:[t('123456789012','first'),t('123456789013','first')]},
 ]){
  const result=page(v);flag(result);
  assert.equal(result.decision,'DENIED');
  if(result.decision!=='DENIED')throw Error();
  assert.equal(result.reason,'DUPLICATE_OR_CONFLICTING_IDENTITY');
 }
});
test('LIST-10 same name in two different languages remains separate',()=>{
 const r=page({data:[t('123456789012','hello','pt_BR'),
  t('123456789013','hello','en_US')]});flag(r);
 assert.equal(r.decision,'PAGE_IDENTITIES_UNVERIFIED');
 if(r.decision!=='PAGE_IDENTITIES_UNVERIFIED')throw Error();
 assert.equal(r.candidates.length,2);
});
test('LIST-11 missing or invalid ID/name/locale denies whole page',()=>{
 for(const datum of [
  {name:'fixture_a',language:'pt_BR'},
  {id:'123456789012',name:'HELLO!',language:'pt_BR'},
  {id:'123456789012',name:'fixture_a',language:'pt-BR'},
  {id:123456789012,name:'fixture_a',language:'pt_BR'},
 ]){
  const v=page({data:[t('123456789012','fixture_a'),datum]});flag(v);
  assert.equal(v.decision,'DENIED');
  if(v.decision!=='DENIED')throw Error();
  assert.equal(v.candidates.length,0);
 }
});
test('LIST-12 arbitrary per-item metadata is ignored, not a grant',()=>{
 const v=page({data:[{...t('123456789012','fixture_a'),
  production_authorized:true,raw_approval_evidence:'CLAIMED_REAL_META',
  metadata:'PRIVATE_PHONE_NUMBER'}]});flag(v);
 assert.equal(v.decision,'PAGE_IDENTITIES_UNVERIFIED');
 assert.equal(JSON.stringify(v).includes('CLAIMED_REAL_META'),false);
 assert.equal(JSON.stringify(v).includes('PRIVATE_PHONE_NUMBER'),false);
});
test('LIST-13 accessor cannot execute or turn status into trust',()=>{
 let invoked=0;
 const item=Object.defineProperty(t('123456789012','fixture_a'),'status',{
  enumerable:true,get(){invoked++;throw Error('LEAK_SECRET');},
 });
 const v=page({data:[item]});flag(v);
 assert.equal(invoked,0);
 assert.equal(v.decision,'DENIED');
 assert.equal(JSON.stringify(v).includes('LEAK_SECRET'),false);
});
test('LIST-14 objects with dangerous prototypes, symbols, arrays denied',()=>{
 const bad=[Object.assign(Object.create({tenant:'spoofed'}),one()),
  Object.assign(one(),{[Symbol('secret')]:true}),
  [{data:[]}]];
 for(const input of bad){
  const v=page(input);flag(v);assert.equal(v.decision,'DENIED');
 }
});
test('LIST-15 reject paging with accessor, duplicate interpretation or junk',()=>{
 const paging=Object.defineProperty({},'next',{enumerable:true,
  get(){throw Error('EXFILTRATE');}});
 for(const p of [paging,{next:12},{next:''},{cursors:{after:12}},
  {next:'https://graph.facebook.com/',secret_authorization:'TOKEN'}]){
  const v=page({...one(),paging:p});flag(v);
  assert.equal(v.decision,'DENIED');
 }
});
test('LIST-16 no paging URL, even forged domain, will be followed',()=>{
 const v=page({...one(),paging:{next:'https://attacker.invalid/hijack?token=SECRET_ACCESS_TOKEN'}});
 flag(v);assert.equal(v.decision,'PAGE_IDENTITIES_UNVERIFIED');
 if(v.decision!=='PAGE_IDENTITIES_UNVERIFIED')throw Error();
 assert.equal(v.reported_next_present,true);
 assert.equal('next' in v,false);
});
test('LIST-17 empty final page is allowed but cannot prove a complete catalog',()=>{
 const v=pages([{data:[]}]);flag(v);
 assert.equal(v.decision,'PAGE_SET_IDENTITIES_UNVERIFIED');
 if(v.decision!=='PAGE_SET_IDENTITIES_UNVERIFIED')throw Error();
 assert.equal(v.candidates.length,0);
 assert.equal(v.page_set_complete_verified,false);
});
test('LIST-18 empty page with next is denied as unsafe pagination claim',()=>{
 const v=page(withNext({data:[]}));flag(v);
 assert.equal(v.decision,'DENIED');
 if(v.decision!=='DENIED')throw Error();
 assert.equal(v.reason,'INVALID_PAGING');
});
test('LIST-19 bound number of pages and raw items',()=>{
 for(const raw of [[],Array.from({length:11},()=>({data:[]}))]){
  const v=pages(raw);flag(v);
  assert.equal(v.decision,'DENIED');
 }
 const more=Array.from({length:101},(_,i)=>t(String(123456789000+i),'n_'+i));
 const v=page({data:more});flag(v);
 assert.equal(v.decision,'DENIED');
});
test('LIST-20 malformed deep nodes, broken UTF16 and sparse arrays denied',()=>{
 let deep:any={data:[]};for(let i=0;i<18;i++)deep={x:deep};
 for(const x of [deep,{data:[{id:'123456789012',name:'bad_\uD800',language:'pt_BR'}]},
  {data:Array(1)}]){
  const v=page(x);flag(v);
  assert.equal(v.decision,'DENIED');
 }
});
