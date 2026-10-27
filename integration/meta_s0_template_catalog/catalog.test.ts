import test from 'node:test';
import assert from 'node:assert/strict';
import {FLAGS,readProductionTemplateCatalog} from './contract.ts';
import {digest,createFixtureCatalogReader} from './adapter.ts';
import {scope,query,record,bundle,setup} from './fixtures.ts';
import {prepareGraphTemplateRequest} from '../../integrations/whatsapp-meta/graph-template.ts';
import {prepareGraphQuickReplyTemplateRequest} from '../../integrations/whatsapp-meta/graph-template-interactive.ts';

const safe=(r:any)=>{for(const k of Object.keys(FLAGS))assert.equal(r[k],false,k);};
async function read(h=setup()){return h.reader.read(query);}
async function prepared(h=setup()){
 const receipt=await read(h);
 assert.equal(receipt.decision,'LAB_CATALOG_VALIDATED');
 return h.reader.prepare(receipt,h.intent(),'v24.0');
}
test('production source is absent; a caller APPROVED object cannot enable it',async()=>{
 const r=await readProductionTemplateCatalog({status:'APPROVED',schema_complete:true});
 assert.equal(r.decision,'DENIED');assert.equal(r.reason,'SOURCE_NOT_IMPLEMENTED');safe(r);
});
test('fixture opt-in is explicit and the returned snapshot never attests real approval',async()=>{
 assert.throws(()=>createFixtureCatalogReader({optIn:'PRODUCTION'} as never));
 const r=await read();assert.equal(r.decision,'LAB_CATALOG_VALIDATED');safe(r);
 if(r.snapshot)assert.equal(r.snapshot.source.approval_evidence,'SYNTHETIC_NOT_META_APPROVAL');
});
test('complete five-field scope, version domains and manifest are preserved in a typed snapshot',async()=>{
 const r:any=await read();assert.deepEqual(r.snapshot.scope,scope);
 assert.equal(r.snapshot.catalog_revision,'7');assert.equal(r.snapshot.binding_revision,'3');
 assert.equal(r.snapshot.template_revision_ref,'TEMPLATE_REV_1');
 assert.deepEqual(r.snapshot.approved_components.map((c:any)=>c.type),['HEADER','BODY','FOOTER','BUTTONS']);
 assert.equal(r.snapshot.quick_reply_policy.revision_ref,'POLICY_REV_1');
});
test('one record produces mutually consistent base-text and button projections and a reused builder descriptor',async()=>{
 const h=setup(),r:any=await prepared(h);safe(r);assert.equal(r.decision,'LAB_INERT_DESCRIPTOR');
 assert.deepEqual(r.descriptor,prepareGraphQuickReplyTemplateRequest(
  h.intent(),r.projections.base,scope,r.projections.quick_reply,'v24.0'));
 assert.deepEqual(r.descriptor.body.template.components.map((c:any)=>c.type),
  ['header','body','button','button']);
 assert.equal(r.projections.base.template_revision_ref,r.projections.quick_reply.template_revision_ref);
 assert.equal(h.state.calls,2);
});
test('base builder text-only compatibility requires a complete manifest with no buttons',async()=>{
 const h=setup(),r=h.state.bundle.record;
 delete r.definition.buttons;r.approved_components.pop();r.quick_reply_policy.buttons=[];
 h.seal();const out:any=await prepared(h);
 assert.equal(out.projections.quick_reply,null);
 assert.deepEqual(out.descriptor,prepareGraphTemplateRequest(h.intent(),out.projections.base,scope,'v24.0'));
});
test('all 1..3 quick replies are retained in catalog order without phantom buttons',async()=>{
 for(const n of [1,2,3]){
  const h=setup(),r=h.state.bundle.record;
  r.definition.buttons=Array.from({length:n},(_,i)=>({kind:'QUICK_REPLY',label:'Opção '+i}));
  r.approved_components.at(-1).buttons=r.definition.buttons.map((b:any)=>({type:b.kind,text:b.label}));
  r.quick_reply_policy.buttons=Array.from({length:n},(_,i)=>({kind:'QUICK_REPLY',index:i,payload:'CHOICE_'+i}));
  h.seal();const out:any=await prepared(h);
  assert.deepEqual(out.descriptor.body.template.components.filter((c:any)=>c.type==='button').map((c:any)=>c.index),
    Array.from({length:n},(_,i)=>String(i)));
 }
});
test('PENDING PAUSED REJECTED DISABLED and unknown status deny before producing a handle',async()=>{
 for(const status of ['PENDING','PAUSED','REJECTED','DISABLED','UNKNOWN']){
  const h=setup();h.state.bundle.record.meta_status=status;h.seal();
  const r:any=await read(h);assert.equal(r.decision,'DENIED');safe(r);
  assert.equal(r.snapshot,null);
 }
});
test('self-declared source, source mismatch or production-shaped provenance deny',async()=>{
 for(const [key,value] of [['source_ref','UNTRUSTED'],['kind','META_LIVE'],
  ['approval_evidence','APPROVED_BY_META']]){
  const h=setup();h.state.bundle.record.source[key]=value;h.seal();
  assert.equal((await read(h)).decision,'DENIED');
 }
});
test('record source and current head source must both match server composition',async()=>{
 const h=setup();h.state.bundle.head.source_ref='OTHER';
 assert.equal((await read(h)).reason,'UNTRUSTED_SOURCE');
});
test('each concessionaria channel App WABA and phone mismatch is denied independently',async()=>{
 for(const k of Object.keys(scope)){
  const h=setup();h.state.bundle.record.scope[k]=k==='phone_number_id'?'999999':'OTHER';h.seal();
  assert.equal((await read(h)).reason,'SCOPE_MISMATCH',k);
 }
});
test('definition tenant WABA name and language must match the scoped query',async()=>{
 for(const [k,v] of [['concessionaria_id','33333333-3333-4333-8333-333333333333'],
  ['waba_ref','999999'],['name','different'],['language','en_US']]){
  const h=setup();h.state.bundle.record.definition[k]=v;h.seal();
  assert.equal((await read(h)).decision,'DENIED');
 }
});
test('missing completeness, omitted whole components or undeclared provider accessories deny',async()=>{
 for(const mutate of [
  (r:any)=>r.schema_complete=false,
  (r:any)=>r.approved_components.pop(),
  (r:any)=>r.approved_components.push({type:'CAROUSEL',items:[]}),
  (r:any)=>r.approved_components[1].extra_required_component=true,
 ]){
  const h=setup();mutate(h.state.bundle.record);h.seal();
  assert.equal((await read(h)).decision,'DENIED');
 }
});
test('complete provider labels/order/content must equal the existing WA17B definition projection',async()=>{
 for(const mutate of [
  (r:any)=>r.approved_components[1].text='Texto diferente',
  (r:any)=>r.approved_components.at(-1).buttons.reverse(),
  (r:any)=>r.approved_components.at(-1).buttons[0].text='Outro rótulo',
  (r:any)=>r.approved_components.reverse(),
 ]){
  const h=setup();mutate(h.state.bundle.record);h.seal();
  assert.equal((await read(h)).reason,'INCOMPLETE_MANIFEST');
 }
});
test('header media URL PHONE_NUMBER Flow and named formats fail closed without stripping',async()=>{
 for(const mutate of [
  (r:any)=>r.definition.header={kind:'IMAGE',asset_ref:'asset_fake_123'},
  (r:any)=>r.definition.buttons[0]={kind:'URL',label:'Site',url:'https://example.invalid'},
  (r:any)=>r.definition.buttons[0]={kind:'PHONE_NUMBER',label:'Telefone',phone_number:'+5500000000000'},
  (r:any)=>r.definition.buttons[0]={kind:'FLOW',label:'Fluxo'},
  (r:any)=>r.parameter_format='NAMED',
 ]){
  const h=setup();mutate(h.state.bundle.record);h.seal();
  assert.equal((await read(h)).reason,'UNSUPPORTED_COMPONENTS');
 }
});
test('four or duplicate-label quick replies cannot evade the existing WA17B validator',async()=>{
 for(const n of [4,2]){
  const h=setup(),r=h.state.bundle.record;
  r.definition.buttons=Array.from({length:n},()=>({kind:'QUICK_REPLY',label:'Duplicado'}));
  h.seal();assert.equal((await read(h)).decision,'DENIED');
 }
});
test('missing body/header variable binding and unknown source are denied using WA17B mappings',async()=>{
 for(const mutate of [
  (r:any)=>delete r.mappings['body.1'],(r:any)=>delete r.mappings['header.1'],
  (r:any)=>r.mappings['body.1']='cliente.nao_autorizado',
  (r:any)=>r.mappings['extra.1']='cliente.nome',
 ]){
  const h=setup();mutate(h.state.bundle.record);h.seal();
  assert.equal((await read(h)).reason,'INVALID_BINDINGS');
 }
});
test('gapped placeholders and >10 positional body fields are never translated to the base builder',async()=>{
 for(const text of ['Olá {{2}}.',Array.from({length:11},(_,i)=>'{{'+(i+1)+'}}').join(' ')]){
  const h=setup();h.state.bundle.record.definition.body.text=text;
  h.seal();assert.equal((await read(h)).decision,'DENIED');
 }
});
test('button policy requires exact quantity contiguous integer indices and QUICK_REPLY type',async()=>{
 for(const mutate of [
  (r:any)=>r.quick_reply_policy.buttons.pop(),
  (r:any)=>r.quick_reply_policy.buttons[0].index=1,
  (r:any)=>r.quick_reply_policy.buttons[1].index=0,
  (r:any)=>r.quick_reply_policy.buttons[0].index='0',
  (r:any)=>r.quick_reply_policy.buttons[0].kind='URL',
  (r:any)=>r.quick_reply_policy.buttons[0].parameters=[{type:'text',text:'injected'}],
 ]){
  const h=setup();mutate(h.state.bundle.record);h.seal();
  assert.equal((await read(h)).decision,'DENIED');
 }
});
test('opaque backend payloads reject dynamic mode URL whitespace Unicode controls and overlength',async()=>{
 for(const payload of ['','https://example.invalid','nome pessoa','á','X\nY','x'.repeat(129)]){
  const h=setup();h.state.bundle.record.quick_reply_policy.buttons[0].payload=payload;h.seal();
  assert.equal((await read(h)).reason,'INVALID_BUTTON_POLICY');
 }
 const h=setup();h.state.bundle.record.quick_reply_policy.mode='SIGNED_DYNAMIC';h.seal();
 assert.equal((await read(h)).reason,'INVALID_BUTTON_POLICY');
});
test('stale template catalog and binding preconditions have independent domains',async()=>{
 const h=setup();
 for(const delta of [{expected_template_revision_ref:'TEMPLATE_REV_2'},
  {expected_catalog_revision:'8'},{expected_binding_revision:'4'}]){
  assert.equal((await h.reader.read({...query,...delta})).reason,'STALE_REVISION');
 }
});
test('canonical int64 string revisions survive beyond JS safe integers and reject coercion/overflow',async()=>{
 const h=setup();h.state.bundle.record.catalog_revision='9223372036854775807';h.seal();
 const r:any=await h.reader.read({...query,expected_catalog_revision:'9223372036854775807'});
 assert.equal(r.decision,'LAB_CATALOG_VALIDATED');
 for(const value of [7,'07','7e0','9223372036854775808']){
  assert.equal((await h.reader.read({...query,expected_catalog_revision:value})).decision,'DENIED');
 }
});
test('status and manifest observations must both be fresh and never future-dated',async()=>{
 for(const key of ['status_observed_at_ms','manifest_observed_at_ms']){
  for(const time of [0,10001]){
   const h=setup();h.state.now=time===0?70000:10000;h.state.bundle.record.source[key]=time;h.seal();
   assert.equal((await read(h)).reason,'STALE_OBSERVATION');
  }
 }
});
test('expiry at the exact max-age boundary denies cached preparation',async()=>{
 const h=setup(),handle=await read(h);h.state.now=70000;
 assert.equal((await h.reader.prepare(handle,h.intent(),'v24.0')).reason,'STALE_OBSERVATION');
});
test('clock rollback is denied even when observation values would fit the local TTL',async()=>{
 const h=setup();await read(h);h.state.now=9999;
 assert.equal((await read(h)).reason,'STALE_OBSERVATION');
});
test('changed record bytes cannot pass a head digest check and a digest alone grants no trust',async()=>{
 const h=setup();h.state.bundle.record.quick_reply_policy.buttons[0].payload='FORGED';
 assert.equal((await read(h)).reason,'INTEGRITY_MISMATCH');
 const r:any=await readProductionTemplateCatalog({digest:digest(h.state.bundle.record)});
 assert.equal(r.reason,'SOURCE_NOT_IMPLEMENTED');
});
test('head status provider identity and revisions must bind the entire record',async()=>{
 for(const key of ['meta_status','provider_template_id','catalog_revision','binding_revision','template_revision_ref']){
  const h=setup();h.state.bundle.head[key]='OTHER';
  assert.equal((await read(h)).reason,'INTEGRITY_MISMATCH',key);
 }
});
test('raw JSON clones and handles from a different reader are not accepted as trusted local receipts',async()=>{
 const h=setup(),handle=await read(h),other=setup();
 assert.equal((await h.reader.prepare(JSON.parse(JSON.stringify(handle)),h.intent(),'v24.0')).reason,'HANDLE_NOT_ISSUED_HERE');
 assert.equal((await other.reader.prepare(handle,other.intent(),'v24.0')).reason,'HANDLE_NOT_ISSUED_HERE');
});
test('a newer PAUSED observation revokes a handle immediately despite a fresh TTL',async()=>{
 const h=setup(),handle=await read(h);
 h.state.bundle.record.meta_status='PAUSED';h.seal('2');
 assert.equal((await h.reader.prepare(handle,h.intent(),'v24.0')).reason,'CATALOG_NOT_APPROVED');
});
test('after observing PAUSED the same reader refuses replay of the old APPROVED epoch',async()=>{
 const h=setup(),old=structuredClone(h.state.bundle);
 await read(h);h.state.bundle.record.meta_status='PAUSED';h.seal('2');await read(h);
 h.state.bundle=old;assert.equal((await read(h)).reason,'SOURCE_ROLLBACK_OR_CONFLICT');
});
test('source epochs cannot mutate in place or roll back even with recomputed valid hashes',async()=>{
 const h=setup();await read(h);
 h.state.bundle.record.source.observation_ref='OTHER';h.seal();
 assert.equal((await read(h)).reason,'SOURCE_ROLLBACK_OR_CONFLICT');
});
test('same approved template revision cannot remap a frozen source or alter provider-visible text',async()=>{
 for(const mutate of [
  (r:any)=>r.mappings['body.1']='operador.nome',
  (r:any)=>{r.definition.body.text='Outra {{1}}';r.approved_components[1].text='Outra {{1}}';},
 ]){
  const h=setup();await read(h);mutate(h.state.bundle.record);
  h.state.bundle.record.catalog_revision='8';h.seal('2');
  assert.equal((await h.reader.read({...query,expected_catalog_revision:'8'})).reason,'SOURCE_ROLLBACK_OR_CONFLICT');
 }
});
test('same payload policy revision cannot change an opaque button value',async()=>{
 const h=setup();await read(h);h.state.bundle.record.quick_reply_policy.buttons[0].payload='CHANGED';
 h.state.bundle.record.catalog_revision='8';h.seal('2');
 assert.equal((await h.reader.read({...query,expected_catalog_revision:'8'})).reason,'SOURCE_ROLLBACK_OR_CONFLICT');
});
test('new backend payload policy revision requires new catalog revision and invalidates old handle',async()=>{
 const h=setup(),handle=await read(h),r=h.state.bundle.record;
 r.quick_reply_policy.revision_ref='POLICY_REV_2';r.quick_reply_policy.buttons[0].payload='CHOICE_NEW';
 h.seal('2');
 assert.equal((await read(h)).reason,'SOURCE_ROLLBACK_OR_CONFLICT');
 r.catalog_revision='8';h.seal('3');
 const next:any=await h.reader.read({...query,expected_catalog_revision:'8'});
 assert.equal(next.decision,'LAB_CATALOG_VALIDATED');
 assert.equal((await h.reader.prepare(handle,h.intent(),'v24.0')).decision,'DENIED');
});
test('even a same-content refresh with a new source epoch requires a newly issued handle',async()=>{
 const h=setup(),handle=await read(h);
 h.state.bundle.record.source.observation_ref='REFRESH';h.seal('2');
 assert.equal((await h.reader.prepare(handle,h.intent(),'v24.0')).reason,'HANDLE_CHANGED');
});
test('body/header parameter counts and types remain enforced by the unchanged builders',async()=>{
 for(const delta of [{body_text_parameters:[]},{body_text_parameters:[42]},
  {header_text_parameter:undefined},{body_text_parameters:['\u0000']}]){
  const h=setup(),handle=await read(h),intent:any={...h.intent(),...delta};
  if(intent.header_text_parameter===undefined)delete intent.header_text_parameter;
  assert.equal((await h.reader.prepare(handle,intent,'v24.0')).decision,'DENIED');
 }
});
test('caller cannot inject a button payload or change tenant revision or language at preparation',async()=>{
 for(const delta of [{button_payload:'FORGED'},{phone_number_id:'999999'},
  {template_revision_ref:'OTHER'},{language_code:'en_US'}]){
  const h=setup(),handle=await read(h);
  assert.equal((await h.reader.prepare(handle,{...h.intent(),...delta},'v24.0')).decision,'DENIED');
 }
});
test('descriptors use catalog payloads while text parameters remain separate and never grant sending',async()=>{
 const h=setup(),handle=await read(h),i=h.intent();i.body_text_parameters=['CHOICE_IN_USER_TEXT'];
 const r:any=await h.reader.prepare(handle,i,'v24.0');safe(r);
 assert.equal(r.descriptor.body.template.components[2].parameters[0].payload,'CHOICE_CONTINUE');
 assert.equal('authorization' in r.descriptor,false);
 assert.equal('url' in r.descriptor,false);
});
test('untrusted accessors symbols sparse arrays and exotic prototypes deny without invoking getters',async()=>{
 let calls=0;
 const h=setup();
 Object.defineProperty(h.state.bundle.record,'meta_status',{get(){calls++;return 'APPROVED';}});
 assert.equal((await read(h)).decision,'DENIED');assert.equal(calls,0);
 for(const mutate of [
  (r:any)=>r[Symbol('grant')]=true,
  (r:any)=>r.quick_reply_policy.buttons.length++,
  (r:any)=>Object.setPrototypeOf(r,{approval:'APPROVED'}),
 ]){
  const x=setup();mutate(x.state.bundle.record);assert.equal((await read(x)).decision,'DENIED');
 }
});
test('input snapshots and generated descriptor graphs are deeply immutable and do not alias source memory',async()=>{
 const h=setup(),handle:any=await read(h);
 assert.equal(Object.isFrozen(handle.snapshot.definition.body),true);
 h.state.bundle.record.definition.body.text='Mutated source';
 assert.equal(handle.snapshot.definition.body.text,'Olá {{1}}.');
 const r:any=await prepared();
 assert.equal(Object.isFrozen(r.descriptor.body.template.components[0].parameters),true);
});
test('port failures return sanitized denial and never leak source errors',async()=>{
 const h=setup();h.state.port=async()=>{throw Error('SYNTHETIC_SECRET');};
 const r=await read(h);assert.equal(r.reason,'DEPENDENCY_UNAVAILABLE');
 assert.equal(JSON.stringify(r).includes('SYNTHETIC_SECRET'),false);safe(r);
});
test('intent is snapshotted before awaiting the source recheck',async()=>{
 const h=setup(),handle=await read(h),intent=h.intent();
 let release:()=>void=()=>{},entered:()=>void=()=>{};
 const gate=new Promise<void>(r=>{release=r;}),ready=new Promise<void>(r=>{entered=r;});
 h.state.port=async()=>{entered();await gate;return h.state.bundle;};
 const result=h.reader.prepare(handle,intent,'v24.0');
 await ready;intent.body_text_parameters[0]='MUTATED_CALLER_VALUE';release();
 const out:any=await result;
 assert.equal(out.descriptor.body.template.components[1].parameters[0].text,'Pessoa fictícia');
});

test('Meta category is part of an immutable approved content revision, independently of S0 purpose',async()=>{
 const h=setup();await read(h);
 h.state.bundle.record.definition.category='MARKETING';h.state.bundle.record.catalog_revision='8';h.seal('2');
 assert.equal((await h.reader.read({...query,expected_catalog_revision:'8'})).reason,'SOURCE_ROLLBACK_OR_CONFLICT');
});
