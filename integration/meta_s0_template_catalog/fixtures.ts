/** Synthetic data only. Source observations are NOT actual Meta approvals. */
import {VERSION,type CatalogRecord,type CatalogBundle} from './contract.ts';
import {digest,createFixtureCatalogReader} from './adapter.ts';
export const scope={
 concessionaria_id:'22222222-2222-4222-8222-222222222222',canal_id:'CHANNEL_FIXTURE_A',
 meta_app_ref:'APP_FIXTURE_A',meta_waba_id:'111111',phone_number_id:'222222',
};
export const query={
 template_name:'fixture_quick_reply',language_code:'pt_BR',
 expected_template_revision_ref:'TEMPLATE_REV_1',expected_catalog_revision:'7',expected_binding_revision:'3',
};
export function record():CatalogRecord {
 return {
  contract:VERSION,scope:{...scope},binding_revision:'3',catalog_revision:'7',
  template_revision_ref:'TEMPLATE_REV_1',content_version:'1',mapping_revision:'1',
  provider_template_id:'333333',meta_status:'APPROVED',schema_complete:true,
  parameter_format:'POSITIONAL_TEXT_ONLY',
  definition:{
   local_id:'11111111-1111-4111-8111-111111111111',concessionaria_id:scope.concessionaria_id,
   waba_ref:scope.meta_waba_id,name:query.template_name,language:'pt_BR',category:'UTILITY',
   origin:'HUMAN_SPECIFIED',body:{text:'Olá {{1}}.',examples:['Pessoa fictícia']},
   header:{kind:'TEXT',text:'Atendimento {{1}}',example:'Equipe fictícia'},
   footer:'Demonstração',
   buttons:[{kind:'QUICK_REPLY',label:'Continuar'},{kind:'QUICK_REPLY',label:'Encerrar'}],
  },
  approved_components:[
   {type:'HEADER',format:'TEXT',text:'Atendimento {{1}}'},
   {type:'BODY',text:'Olá {{1}}.'},{type:'FOOTER',text:'Demonstração'},
   {type:'BUTTONS',buttons:[{type:'QUICK_REPLY',text:'Continuar'},{type:'QUICK_REPLY',text:'Encerrar'}]},
  ],
  mappings:{'body.1':'cliente.nome','header.1':'operador.nome'},
  quick_reply_policy:{mode:'STATIC_BACKEND_CATALOG',policy_ref:'FIXTURE_POLICY',revision_ref:'POLICY_REV_1',
   buttons:[{kind:'QUICK_REPLY',index:0,payload:'CHOICE_CONTINUE'},
    {kind:'QUICK_REPLY',index:1,payload:'CHOICE_STOP'}]},
  source:{kind:'LAB_FIXTURE',source_ref:'FIXTURE_SOURCE',observation_ref:'FAKE_OBSERVATION_1',
   approval_evidence:'SYNTHETIC_NOT_META_APPROVAL',
   status_observed_at_ms:10000,manifest_observed_at_ms:10000},
 };
}
export function bundle(r=record(),epoch='1'):CatalogBundle {
 return {record:r,head:{source_ref:r.source.source_ref,source_epoch:epoch,record_sha256:digest(r),
  catalog_revision:r.catalog_revision,binding_revision:r.binding_revision,
  template_revision_ref:r.template_revision_ref,provider_template_id:r.provider_template_id,
  meta_status:r.meta_status}};
}
export function setup(){
 const state:{bundle:any;now:number;calls:number;port:(q:unknown)=>Promise<unknown>}={
  bundle:bundle(),now:10000,calls:0,port:async()=>state.bundle,
 };
 const source={readCurrent:async(q:any)=>{state.calls++;return state.port(q);}};
 const reader=createFixtureCatalogReader({optIn:'DISPOSABLE_CATALOG_05_ONLY',
  sourceRef:'FIXTURE_SOURCE',trustedScope:scope,
  variableSourceKeys:['cliente.nome','operador.nome'],source,maxAgeMs:60000,clock:()=>state.now});
 const seal=(epoch=state.bundle.head.source_epoch)=>{
  state.bundle=bundle(state.bundle.record,epoch);
 };
 const intent=()=>({
  contract_version:'meta-s0.v0.1-proposed' as const,intent_id:'FIXTURE_INTENT',
  attempt_id:'FIXTURE_ATTEMPT',correlation_id:'FIXTURE_CORRELATION',
  authorized_business_action:'C06' as const,authorized_state_version:1,
  ...scope,recipient_verified:'5500000000000',template_name:query.template_name,
  language_code:query.language_code,template_revision_ref:'TEMPLATE_REV_1',
  header_text_parameter:'Equipe fictícia',body_text_parameters:['Pessoa fictícia'],
 });
 return {state,reader,seal,intent};
}
