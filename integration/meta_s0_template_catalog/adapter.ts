/**
 * Explicit fixture adapter only. No productive issuer, HMAC, dispatch, ACK,
 * database, cache registry, Graph, credentials, or policy implementation.
 */
import {createHash} from 'node:crypto';
import {composeMcpTemplateDraft,mapMcpTemplateSources,prepareMcpTemplateReview,
  type MultiFormatInput} from '../../integrations/whatsapp-meta/template-mcp-multiformat.ts';
import {prepareGraphTemplateRequest,type TemplateIntent,type TrustedTemplateSnapshot}
  from '../../integrations/whatsapp-meta/graph-template.ts';
import {prepareGraphQuickReplyTemplateRequest,type TrustedQuickReplyCatalog}
  from '../../integrations/whatsapp-meta/graph-template-interactive.ts';
import {VERSION,FLAGS,denied,type Denial,type CatalogQuery,type Scope,
  type CatalogRecord,type CatalogBundle,type FixtureSourcePort} from './contract.ts';
class Reject extends Error {
  reason:Denial;
  constructor(reason:Denial){super(reason);this.reason=reason;}
}
const need=(ok:unknown,reason:Denial):void=>{if(!ok)throw new Reject(reason);};
const id=(x:unknown):x is string=>typeof x==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(x);
const rev=(x:unknown):x is string=>typeof x==='string'&&/^[1-9][0-9]{0,18}$/.test(x)
  &&BigInt(x)<=9223372036854775807n;
const scopeKeys=['concessionaria_id','canal_id','meta_app_ref','meta_waba_id','phone_number_id'];
const qKeys=['template_name','language_code','expected_template_revision_ref',
 'expected_catalog_revision','expected_binding_revision'];
function keys(x:any,required:readonly string[],optional:readonly string[]=[]){
  need(x!==null&&typeof x==='object'&&!Array.isArray(x)
    &&required.every(k=>Object.hasOwn(x,k))
    &&Object.keys(x).every(k=>required.includes(k)||optional.includes(k)), 'INVALID_INPUT');
}
/** Bounded own-data snapshot, no getters/prototypes/symbols/sparse arrays. */
export function copyData(raw:unknown):any {
  let nodes=0;
  function walk(x:any,depth:number):any {
    need(++nodes<=4096&&depth<=16,'INVALID_INPUT');
    if(x===null||typeof x==='boolean')return x;
    if(typeof x==='string'){need(x.length<=8192,'INVALID_INPUT');return x;}
    if(typeof x==='number'){need(Number.isSafeInteger(x)&&x>=0,'INVALID_INPUT');return x;}
    need(x!==null&&typeof x==='object','INVALID_INPUT');
    const array=Array.isArray(x),proto=Object.getPrototypeOf(x);
    need(array?proto===Array.prototype:proto===Object.prototype||proto===null,'INVALID_INPUT');
    const own=Reflect.ownKeys(x),d=Object.getOwnPropertyDescriptors(x);
    need(own.every(k=>typeof k==='string'&&Object.hasOwn(d[k],'value')),'INVALID_INPUT');
    if(array){
      need(x.length<=100&&own.length===x.length+1
        &&Array.from({length:x.length},(_,i)=>Object.hasOwn(d,String(i))).every(Boolean),'INVALID_INPUT');
      return Array.from({length:x.length},(_,i)=>walk(d[String(i)].value,depth+1));
    }
    need(own.length<=64,'INVALID_INPUT');
    return Object.fromEntries((own as string[]).map(k=>[k,walk(d[k].value,depth+1)]));
  }
  return walk(raw,0);
}
function freeze<T>(x:T):T {
  if(x&&typeof x==='object'){for(const v of Object.values(x))freeze(v);Object.freeze(x);}
  return x;
}
/** Sorted ASCII object keys; array order and UTF-8/string content are preserved. */
export function digest(raw:unknown):string {
  const x=copyData(raw);
  const canonical=(v:any):any=>Array.isArray(v)?v.map(canonical):
    v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
  return createHash('sha256').update(JSON.stringify(canonical(x)),'utf8').digest('hex');
}
function parseQuery(raw:unknown):CatalogQuery {
  const q=copyData(raw);keys(q,qKeys);
  need(typeof q.template_name==='string'&&/^[a-z][a-z0-9_]{0,127}$/.test(q.template_name)
    &&typeof q.language_code==='string'&&/^[a-z]{2}(?:_[A-Z]{2})?$/.test(q.language_code)
    &&id(q.expected_template_revision_ref)&&rev(q.expected_catalog_revision)
    &&rev(q.expected_binding_revision),'INVALID_INPUT');
  return freeze(q);
}
function projectedManifest(components:any[]):any[]{
  return components.map(c=>Object.fromEntries(Object.entries(c).filter(([k])=>k!=='example')));
}
const recordKeys=['contract','scope','binding_revision','catalog_revision','template_revision_ref',
 'content_version','mapping_revision','provider_template_id','meta_status','schema_complete',
 'parameter_format','definition','approved_components','mappings','quick_reply_policy','source'];
const headKeys=['source_ref','source_epoch','record_sha256','catalog_revision','binding_revision',
 'template_revision_ref','provider_template_id','meta_status'];
export function createFixtureCatalogReader(options:{
  optIn:'DISPOSABLE_CATALOG_05_ONLY';sourceRef:string;trustedScope:Scope;
  variableSourceKeys:readonly string[];source:FixtureSourcePort;maxAgeMs:number;clock:()=>number;
}) {
  need(options.optIn==='DISPOSABLE_CATALOG_05_ONLY','UNTRUSTED_SOURCE');
  const scope=freeze(copyData(options.trustedScope));keys(scope,scopeKeys);
  need(scopeKeys.every(k=>id(scope[k]))&&/^\d{5,25}$/.test(scope.meta_waba_id)
    &&/^\d{5,25}$/.test(scope.phone_number_id),'INVALID_INPUT');
  need(id(options.sourceRef)&&Number.isSafeInteger(options.maxAgeMs)&&options.maxAgeMs>0
    &&options.maxAgeMs<=3600000&&typeof options.clock==='function'
    &&typeof options.source?.readCurrent==='function','INVALID_INPUT');
  const sourceRef=options.sourceRef,source=Object.freeze({readCurrent:options.source.readCurrent.bind(options.source)}),clock=options.clock,maxAgeMs=options.maxAgeMs;
  const registry=freeze(copyData(options.variableSourceKeys));
  const handles=new WeakMap<object,any>(),seen=new Map<string,any>(),versions=new Map<string,string>();
  const policies=new Map<string,string>(),catalogs=new Map<string,string>();
  let lastClock=0;
  function inspect(raw:unknown,q:CatalogQuery){
    const b=copyData(raw);keys(b,['record','head']);const r=b.record,h=b.head;
    keys(r,recordKeys);keys(h,headKeys);keys(r.scope,scopeKeys);
    need(r.contract===VERSION,'INVALID_INPUT');
    need(scopeKeys.every(k=>r.scope[k]===scope[k]),'SCOPE_MISMATCH');
    keys(r.source,['kind','source_ref','observation_ref','approval_evidence',
      'status_observed_at_ms','manifest_observed_at_ms']);
    need(r.source.kind==='LAB_FIXTURE'&&r.source.source_ref===sourceRef
      &&h.source_ref===sourceRef&&r.source.approval_evidence==='SYNTHETIC_NOT_META_APPROVAL'
      &&id(r.source.observation_ref),'UNTRUSTED_SOURCE');
    need(rev(r.binding_revision)&&rev(r.catalog_revision)&&rev(r.content_version)
      &&rev(r.mapping_revision)&&rev(h.source_epoch)&&id(r.template_revision_ref)
      &&typeof r.provider_template_id==='string'&&/^\d{5,25}$/.test(r.provider_template_id),'INVALID_INPUT');
    need(['APPROVED','PENDING','PAUSED','REJECTED','DISABLED'].includes(r.meta_status),'CATALOG_NOT_APPROVED');
    need(r.schema_complete===true,'INCOMPLETE_MANIFEST');
    need(r.parameter_format==='POSITIONAL_TEXT_ONLY','UNSUPPORTED_COMPONENTS');
    need(r.definition?.name===q.template_name&&r.definition?.language===q.language_code
      &&r.definition?.concessionaria_id===scope.concessionaria_id
      &&r.definition?.waba_ref===scope.meta_waba_id,'SCOPE_MISMATCH');
    const now=clock();
    need(Number.isSafeInteger(now)&&now>=lastClock,'STALE_OBSERVATION');
    lastClock=now;
    for(const key of ['status_observed_at_ms','manifest_observed_at_ms']){
      const t=r.source[key];
      need(Number.isSafeInteger(t)&&t>=0&&t<=now&&now-t<maxAgeMs,'STALE_OBSERVATION');
    }
    need(digest(r)===h.record_sha256
      &&['catalog_revision','binding_revision','template_revision_ref','provider_template_id','meta_status']
        .every(k=>r[k]===h[k]),'INTEGRITY_MISMATCH');
    // WA17B already validates template text, slots, labels, counts and mappings.
    // Reject profiles broader than the two certified outbound builders support.
    need(!r.definition.header||r.definition.header.kind==='TEXT','UNSUPPORTED_COMPONENTS');
    need(!r.definition.buttons||r.definition.buttons.every((b:any)=>b.kind==='QUICK_REPLY'),
      'UNSUPPORTED_COMPONENTS');
    let draft;
    try{
      draft=composeMcpTemplateDraft(r.definition as MultiFormatInput);
      need(draft.slots.filter(s=>s.part==='BODY').length<=10,'UNSUPPORTED_COMPONENTS');
      draft=mapMcpTemplateSources(draft,0,r.mappings,registry);
    }catch(e){if(e instanceof Reject)throw e;throw new Reject('INVALID_BINDINGS');}
    const reviewed=prepareMcpTemplateReview(draft);
    const manifest=projectedManifest(reviewed.payload.components);
    need(reviewed.binding_snapshot.complete===true,'INVALID_BINDINGS');
    need(digest(manifest)===digest(r.approved_components),'INCOMPLETE_MANIFEST');
    keys(r.quick_reply_policy,['mode','policy_ref','revision_ref','buttons']);
    const policy=r.quick_reply_policy,buttons=r.definition.buttons??[];
    need(policy.mode==='STATIC_BACKEND_CATALOG'&&id(policy.policy_ref)&&id(policy.revision_ref)
      &&Array.isArray(policy.buttons)&&policy.buttons.length===buttons.length,'INVALID_BUTTON_POLICY');
    for(let i=0;i<policy.buttons.length;i++){
      const b=policy.buttons[i];keys(b,['kind','index','payload']);
      need(b.kind==='QUICK_REPLY'&&b.index===i&&typeof b.payload==='string'
        &&/^[A-Za-z0-9_.:-]{1,128}$/.test(b.payload),'INVALID_BUTTON_POLICY');
    }
    const lineageKey=q.template_name+':'+q.language_code;
    const prior=seen.get(lineageKey);
    need(!prior||(BigInt(h.source_epoch)>=BigInt(prior.epoch)
      &&BigInt(r.catalog_revision)>=BigInt(prior.catalog)
      &&BigInt(r.binding_revision)>=BigInt(prior.binding)
      &&(h.source_epoch!==prior.epoch||h.record_sha256===prior.hash)),
      'SOURCE_ROLLBACK_OR_CONFLICT');
    const versionKey=lineageKey+':'+r.template_revision_ref;
    const immutable=digest({manifest,mappings:r.mappings,content_version:r.content_version,
      mapping_revision:r.mapping_revision,provider_template_id:r.provider_template_id,
      meta_category:r.definition.category});
    need(!versions.has(versionKey)||versions.get(versionKey)===immutable,'SOURCE_ROLLBACK_OR_CONFLICT');
    const policyKey=policy.policy_ref+':'+policy.revision_ref,policyHash=digest(policy.buttons);
    need(!policies.has(policyKey)||policies.get(policyKey)===policyHash,'SOURCE_ROLLBACK_OR_CONFLICT');
    const catalogKey=lineageKey+':'+r.catalog_revision;
    const material=digest({immutable,policy,binding_revision:r.binding_revision,
      template_revision_ref:r.template_revision_ref});
    need(!catalogs.has(catalogKey)||catalogs.get(catalogKey)===material,'SOURCE_ROLLBACK_OR_CONFLICT');
    policies.set(policyKey,policyHash);catalogs.set(catalogKey,material);
    seen.set(lineageKey,{epoch:h.source_epoch,catalog:r.catalog_revision,binding:r.binding_revision,hash:h.record_sha256});
    versions.set(versionKey,immutable);
    // Remember valid denial observations, including PAUSED, before rejecting.
    need(q.expected_binding_revision===r.binding_revision
      &&q.expected_catalog_revision===r.catalog_revision
      &&q.expected_template_revision_ref===r.template_revision_ref,'STALE_REVISION');
    need(r.meta_status==='APPROVED','CATALOG_NOT_APPROVED');
    return freeze({bundle:b as CatalogBundle,draft,manifest});
  }
  async function readInternal(q:CatalogQuery){return inspect(await source.readCurrent(q),q);}
  function error(e:unknown){return denied(e instanceof Reject?e.reason:'DEPENDENCY_UNAVAILABLE');}
  return Object.freeze({
    async read(rawQuery:unknown){
      try{
        const q=parseQuery(rawQuery),data=await readInternal(q);
        const handle=freeze({decision:'LAB_CATALOG_VALIDATED' as const,
          snapshot:data.bundle.record,snapshot_sha256:data.bundle.head.record_sha256,
          source_epoch:data.bundle.head.source_epoch,...FLAGS});
        handles.set(handle,{q,data});return handle;
      }catch(e){return error(e);}
    },
    async prepare(handle:object,intent:TemplateIntent,apiVersion:string){
      try{
        // Snapshot request and method argument BEFORE asynchronous source recheck.
        const safe=copyData(intent);
        keys(safe,['contract_version','intent_id','attempt_id','correlation_id','authorized_business_action',
          'authorized_state_version',...scopeKeys,'recipient_verified','template_name','language_code',
          'template_revision_ref'],['header_text_parameter','body_text_parameters']);
        const issued=handles.get(handle);need(issued,'HANDLE_NOT_ISSUED_HERE');
        const fresh=await readInternal(issued.q);
        need(fresh.bundle.head.record_sha256===issued.data.bundle.head.record_sha256
          &&fresh.bundle.head.source_epoch===issued.data.bundle.head.source_epoch,'HANDLE_CHANGED');
        const r=fresh.bundle.record,draft=fresh.draft;
        const base:TrustedTemplateSnapshot={
          template_name:r.definition.name,language_code:r.definition.language,
          template_revision_ref:r.template_revision_ref,status:'APPROVED',
          parameter_format:'POSITIONAL_TEXT_ONLY',schema_complete:true,...r.scope,
          header_text_parameter_count:draft.slots.some(s=>s.part==='HEADER')?1:0,
          body_text_parameter_count:draft.slots.filter(s=>s.part==='BODY').length,
          components:fresh.manifest.filter((c:any)=>c.type!=='BUTTONS').map((c:any)=>({
            type:c.type,format:'TEXT',parameter_count:draft.slots.filter(s=>s.part===c.type).length,
          })),
        };
        const quick:TrustedQuickReplyCatalog={
          contract:'prumo.meta.quickreply.catalog.offline.v1',approval:'APPROVED',
          schema_complete:true,template_name:base.template_name,language_code:base.language_code,
          template_revision_ref:base.template_revision_ref,scope:r.scope,
          buttons:r.quick_reply_policy.buttons,
        };
        let descriptor;
        try {
          descriptor=quick.buttons.length?prepareGraphQuickReplyTemplateRequest(safe,base,r.scope,quick,apiVersion)
            :prepareGraphTemplateRequest(safe,base,r.scope,apiVersion);
        }catch{throw new Reject('BUILDER_REJECTED');}
        return freeze({decision:'LAB_INERT_DESCRIPTOR' as const,
          descriptor,projections:{base,quick_reply:quick.buttons.length?quick:null},...FLAGS});
      }catch(e){return error(e);}
    },
  });
}
