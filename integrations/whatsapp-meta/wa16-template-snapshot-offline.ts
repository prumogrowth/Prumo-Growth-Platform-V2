/**
 * M16 / WA16: immutable LAB-only composition snapshot, NOT provider approval.
 * The pre-existing WA-17B validates the components, variables and media refs.
 * This adds content/mapping/media digests + a closed-world candidate recheck.
 * No real Meta, MCP server, source registry, SQL, media upload or dispatch.
 * M13 provider inspector only supports a narrow subset; a multimedia digest
 * MUST NOT be treated as Meta-approved component evidence.
 */
import {createHash} from 'node:crypto';
import {composeMcpTemplateDraft,mapMcpTemplateSources,
 type MultiFormatInput} from './template-mcp-multiformat.ts';

const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const REF=/^[A-Za-z0-9_.:-]{1,128}$/,NUM=/^[0-9]{5,25}$/;
const SHA=/^[0-9a-f]{64}$/,SOURCE=/^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){1,3}$/;
const MIME={IMAGE:['image/jpeg','image/png'],VIDEO:['video/mp4'],
 DOCUMENT:['application/pdf']} as const;
const RAW_KEYS=['contract_version','selection_ref','concessionaria_id','waba_ref',
 'template_ref','version_ref','content_version','mapping_revision',
 'media_revision','now_ms','max_age_ms','authoring','bindings',
 'source_registry','media_evidence','review_state'] as const;
const MEDIA=['concessionaria_id','waba_ref','asset_ref','kind',
 'mime_type','sha256','asset_revision',
 'valid_from_ms','valid_until_ms','observed_at_ms','state'] as const;
const CAND=['contract_version','selection_ref','concessionaria_id','waba_ref',
 'template_ref','version_ref','content_version','mapping_revision',
 'media_revision','component_sha256','binding_sha256','media_sha256',
 'snapshot_sha256','slot_count','media_kind','review_state',
 'send_authorized','production_authorized','meta_approval_verified',
 'source_registry_authenticated','media_verified','mcp_execution_authorized',
 'requires_s0_recheck'] as const;
export type Wa16Reason='INVALID_INPUT'|'SCOPE_MISMATCH'|
 'COMPONENTS_OR_BINDINGS_DENIED'|'MEDIA_EVIDENCE_DENIED'|
 'INVALID_CANDIDATE'|'VERSION_OR_SNAPSHOT_CHANGED';
export type Wa16Snapshot=Readonly<{
 contract_version:'wa16-frozen-snapshot.lab.v0.1';
 selection_ref:string;concessionaria_id:string;waba_ref:string;
 template_ref:string;version_ref:string;content_version:number;
 mapping_revision:number;media_revision:number;
 component_sha256:string;binding_sha256:string;media_sha256:string;
 snapshot_sha256:string;slot_count:number;
 media_kind:'NONE'|'IMAGE'|'VIDEO'|'DOCUMENT';
 review_state:'LAB_REPORTED_APPROVED';
 send_authorized:false;production_authorized:false;
 meta_approval_verified:false;source_registry_authenticated:false;
 media_verified:false;mcp_execution_authorized:false;
 requires_s0_recheck:true;
}>;
export type Wa16Result=Readonly<{
 decision:'DENIED'|'LAB_FROZEN_SNAPSHOT_UNVERIFIED'|'LAB_RECHECKED_UNVERIFIED';
 reason:Wa16Reason|null;candidate:Wa16Snapshot|null;
 send_authorized:false;production_authorized:false;
 meta_approval_verified:false;media_verified:false;
 mcp_execution_authorized:false;
}>;
const FLAGS=Object.freeze({
 send_authorized:false,production_authorized:false,
 meta_approval_verified:false,media_verified:false,
 mcp_execution_authorized:false,
} as const);
const deny=(reason:Wa16Reason):Wa16Result=>Object.freeze({
 ...FLAGS,decision:'DENIED' as const,reason,candidate:null,
});
const positive=(candidate:Wa16Snapshot,
 decision:'LAB_FROZEN_SNAPSHOT_UNVERIFIED'|'LAB_RECHECKED_UNVERIFIED'):Wa16Result=>
 Object.freeze({...FLAGS,decision,reason:null,candidate});
const id=(v:unknown):v is string=>typeof v==='string'&&REF.test(v);
const positiveInt=(v:unknown):v is number=>typeof v==='number'&&
 Number.isSafeInteger(v)&&v>0;
const nonneg=(v:unknown):v is number=>typeof v==='number'&&
 Number.isSafeInteger(v)&&v>=0;
const digest=(v:unknown):string=>
 createHash('sha256').update(JSON.stringify(v),'utf8').digest('hex');
function record(raw:unknown,keys:readonly string[]):Record<string,unknown>|null{
 if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
 const proto=Object.getPrototypeOf(raw);
 if(proto!==Object.prototype&&proto!==null)return null;
 const descriptors=Object.getOwnPropertyDescriptors(raw),all=Reflect.ownKeys(raw);
 if(all.length!==keys.length||all.some(k=>typeof k!=='string'||
    !keys.includes(k)||!Object.hasOwn(descriptors[k],'value'))||
    keys.some(k=>!Object.hasOwn(descriptors,k)))return null;
 return Object.fromEntries(keys.map(k=>[k,descriptors[k].value]));
}
/** Copy all user-supplied graph nodes from data descriptors before passing
 * anything to legacy WA-17B. Reject getters, symbols, sparse arrays,
 * exotic objects, cycles, unsafe numbers and resource amplification. */
function clone(raw:unknown,n={nodes:0},level=0,anc=new WeakSet<object>()):any{
 if(++n.nodes>5000||level>20)throw Error('LAB_CAP');
 if(raw===null||typeof raw==='boolean')return raw;
 // Reject oversized string values before copying or hashing the source
 // registry and component metadata. WA-17B has tighter content limits.
 if(typeof raw==='string'){
  if(raw.length>8192)throw Error('LAB_STRING_LIMIT');
  return raw;
 }
 if(typeof raw==='number'&&Number.isSafeInteger(raw))return raw;
 if(!raw||typeof raw!=='object'||anc.has(raw))throw Error('BAD_VALUE');
 const array=Array.isArray(raw),proto=Object.getPrototypeOf(raw);
 if(array?proto!==Array.prototype:proto!==Object.prototype&&proto!==null)
  throw Error('BAD_PROTO');
 const d=Object.getOwnPropertyDescriptors(raw),keys=Reflect.ownKeys(raw);
 if(keys.some(k=>typeof k!=='string'||!Object.hasOwn(d[k],'value')))
  throw Error('BAD_DESCRIPTOR');
 if(array){
  const len=d.length?.value;
  if(!Number.isSafeInteger(len)||len>100||keys.length!==len+1)
   throw Error('BAD_ARRAY');
  for(let i=0;i<len;i++)if(!Object.hasOwn(d,String(i)))throw Error('SPARSE');
 }else if(keys.length>150)throw Error('OVERSIZED');
 anc.add(raw);
 const out:any=array?[]:Object.create(null);
 for(const k of keys){
  if(k==='length'&&array)continue;
  // Own "__proto__" key remains an ordinary null-prototype data property.
  Object.defineProperty(out,k,{value:clone(d[k].value,n,level+1,anc),
   enumerable:true,writable:false,configurable:false});
 }
 anc.delete(raw);
 return Object.freeze(out);
}
function snapshotCandidate(raw:unknown):Wa16Snapshot|null{
 const c=record(raw,CAND);
 if(!c||c.contract_version!=='wa16-frozen-snapshot.lab.v0.1'||
   !id(c.selection_ref)||typeof c.concessionaria_id!=='string'||
   !UUID.test(c.concessionaria_id)||
   typeof c.waba_ref!=='string'||!NUM.test(c.waba_ref)||
   !id(c.template_ref)||!id(c.version_ref)||
   !positiveInt(c.content_version)||!positiveInt(c.mapping_revision)||
   !nonneg(c.media_revision)||!nonneg(c.slot_count)||
   c.slot_count>25||
   !['NONE','IMAGE','VIDEO','DOCUMENT'].includes(c.media_kind as string)||
   c.review_state!=='LAB_REPORTED_APPROVED'||
   !['component_sha256','binding_sha256','media_sha256','snapshot_sha256']
    .every(k=>typeof c[k]==='string'&&SHA.test(c[k] as string))||
   c.send_authorized!==false||c.production_authorized!==false||
   c.meta_approval_verified!==false||
   c.source_registry_authenticated!==false||
   c.media_verified!==false||c.mcp_execution_authorized!==false||
   c.requires_s0_recheck!==true)return null;
 return c as Wa16Snapshot;
}
function produce(raw:unknown):Wa16Result{
 try{
  const x=record(raw,RAW_KEYS);
  if(!x||x.contract_version!=='wa16-template-freeze.lab.v0.1'||
     !id(x.selection_ref)||typeof x.concessionaria_id!=='string'||
     !UUID.test(x.concessionaria_id)||
     typeof x.waba_ref!=='string'||!NUM.test(x.waba_ref)||
     !id(x.template_ref)||!id(x.version_ref)||
     !positiveInt(x.content_version)||!positiveInt(x.mapping_revision)||
     !nonneg(x.media_revision)||!nonneg(x.now_ms)||
     !positiveInt(x.max_age_ms)||x.max_age_ms>300000||
     x.review_state!=='LAB_REPORTED_APPROVED')return deny('INVALID_INPUT');
  const frozen=clone(raw),s=record(frozen,RAW_KEYS)!;
  const authoring=s.authoring as MultiFormatInput;
  if(!authoring||authoring.concessionaria_id!==s.concessionaria_id||
     authoring.waba_ref!==s.waba_ref)
   return deny('SCOPE_MISMATCH');
  let draft;
  try{draft=composeMcpTemplateDraft(authoring);}
  catch{return deny('COMPONENTS_OR_BINDINGS_DENIED');}
  const mapping=record(s.bindings,draft.slots.map(x=>x.slot_key));
  const registry=s.source_registry;
  if(!mapping||!Array.isArray(registry)||registry.length>100||
     registry.some(x=>typeof x!=='string'||!SOURCE.test(x))||
     new Set(registry).size!==registry.length)
   return deny('COMPONENTS_OR_BINDINGS_DENIED');
  try{
   // The returned mapping revision 1 is just the WA-17B local draft helper;
   // the host's expected mapping_revision is a distinct untrusted fixture.
   draft=mapMcpTemplateSources(draft,0,mapping as Record<string,string>,
    registry as string[]);
  }catch{return deny('COMPONENTS_OR_BINDINGS_DENIED');}
  let kind:'NONE'|'IMAGE'|'VIDEO'|'DOCUMENT'='NONE';
  let mediaSha=digest(['NONE',s.media_revision]);
  if(authoring.header&&authoring.header.kind!=='TEXT'){
   kind=authoring.header.kind;
   const m=record(s.media_evidence,MEDIA);
   if(!m||m.concessionaria_id!==s.concessionaria_id||
      m.waba_ref!==s.waba_ref||
      m.asset_ref!==authoring.header.asset_ref||
      m.kind!==kind||typeof m.mime_type!=='string'||
      !(MIME[kind] as readonly string[]).includes(m.mime_type)||
      typeof m.sha256!=='string'||!SHA.test(m.sha256)||
      !positiveInt(m.asset_revision)||m.asset_revision!==s.media_revision||
      !nonneg(m.valid_from_ms)||!positiveInt(m.valid_until_ms)||
      m.valid_until_ms<=m.valid_from_ms||
      !nonneg(m.observed_at_ms)||m.observed_at_ms>s.now_ms||
      s.now_ms-m.observed_at_ms>s.max_age_ms||
      m.valid_from_ms>s.now_ms||m.valid_until_ms<=s.now_ms||
      m.state!=='LAB_READY')
    return deny('MEDIA_EVIDENCE_DENIED');
   mediaSha=digest([s.concessionaria_id,s.waba_ref,
    kind,m.asset_ref,m.mime_type,m.sha256,m.asset_revision,
    m.valid_from_ms,m.valid_until_ms,m.observed_at_ms,m.state]);
  }else if(s.media_evidence!==null||s.media_revision!==0)
   return deny('MEDIA_EVIDENCE_DENIED');
  const compSha=digest([s.content_version,draft.input,draft.slots]);
  // sorted mapping by actual position, NOT registry insertion order;
  // every positional slot is bound to an allowlisted source in the fixture.
  const bindSha=digest([s.content_version,s.mapping_revision,
   draft.slots.map(slot=>[slot.slot_key,draft.mappings[slot.slot_key]]),
   // Include the WHOLE alleged source registry, not only sources currently
   // referenced by slots. Reordering is harmless; changes are rejected.
   [...(registry as string[])].sort()]);
  const finalSha=digest([s.selection_ref,s.concessionaria_id,s.waba_ref,
   s.template_ref,s.version_ref,
   s.content_version,s.mapping_revision,s.media_revision,
   compSha,bindSha,mediaSha,kind,s.review_state]);
  const candidate:Wa16Snapshot=Object.freeze({
   contract_version:'wa16-frozen-snapshot.lab.v0.1',
   selection_ref:s.selection_ref as string,
   concessionaria_id:s.concessionaria_id as string,
   waba_ref:s.waba_ref as string,template_ref:s.template_ref as string,
   version_ref:s.version_ref as string,
   content_version:s.content_version as number,
   mapping_revision:s.mapping_revision as number,
   media_revision:s.media_revision as number,
   component_sha256:compSha,binding_sha256:bindSha,
   media_sha256:mediaSha,snapshot_sha256:finalSha,
   slot_count:draft.slots.length,media_kind:kind,
   review_state:'LAB_REPORTED_APPROVED',
   send_authorized:false,production_authorized:false,
   meta_approval_verified:false,source_registry_authenticated:false,
   media_verified:false,mcp_execution_authorized:false,
   requires_s0_recheck:true,
  });
  return positive(candidate,'LAB_FROZEN_SNAPSHOT_UNVERIFIED');
 }catch{return deny('INVALID_INPUT');}
}
/** Snapshot digest is NOT an S0 content release, Graph approval, signature
 * or any authenticated proof. Every input is an untrusted LAB fixture. */
export function freezeWa16TemplateOffline(raw:unknown):Wa16Result{
 return produce(raw);
}
/** Caller must supply a fresh LAB fixture; any content, mapping, media,
 * scope, version or recorded evidence change denies continuation. No CAS,
 * write reservation, source freshness guarantee or ABA defense. */
export function recheckWa16TemplateOffline(
 rawCandidate:unknown,freshFixture:unknown,
):Wa16Result{
 try{
  const previous=snapshotCandidate(rawCandidate);
  if(!previous)return deny('INVALID_CANDIDATE');
  const current=produce(freshFixture);
  if(current.decision==='DENIED')return current;
  if(!current.candidate||
     CAND.some(k=>previous[k as keyof Wa16Snapshot]!==
      current.candidate![k as keyof Wa16Snapshot]))
   return deny('VERSION_OR_SNAPSHOT_CHANGED');
  return positive(current.candidate,'LAB_RECHECKED_UNVERIFIED');
 }catch{return deny('INVALID_CANDIDATE');}
}
