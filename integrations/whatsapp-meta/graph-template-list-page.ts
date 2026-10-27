/**
 * Offline structural inspection of Graph GET /<WABA-ID>/message_templates
 * paginated LIST replies. No HTTP client, cursor follower, tokens, credentials,
 * DB, S0 integration, ACK or permission. Responses are untrusted even when
 * their contents say APPROVED.
 *
 * The list gives candidate IDs ONLY; individual records MUST be resolved
 * through an independently authenticated WABA-scoped source (T1-T6 / PR #19).
 * The page envelope does not certify WABA, freshness or approval.
 */
export type TemplateIdentityCandidate=Readonly<{
 provider_template_id:string;template_name:string;language_code:string;
 needs_detail_by_id:true;
}>;
type Denial='INVALID_ENVELOPE'|'INVALID_DATA'|'DUPLICATE_OR_CONFLICTING_IDENTITY'|
 'INVALID_PAGING'|'INCOMPLETE_PAGE_SET'|'RESOURCE_LIMIT';
type NoAuthority=Readonly<{
 meta_approval_verified:false;production_authorized:false;
 send_authorized:false;ack_allowed:false;retry_external:false;
 s0_write_authorized:false;commercial_effect_authorized:false;
 waba_binding_verified:false;page_chain_authenticated:false;
 page_set_complete_verified:false;
}>;
type PageSuccess=Readonly<{
 decision:'PAGE_IDENTITIES_UNVERIFIED';reason:null;
 candidates:readonly TemplateIdentityCandidate[];
 reported_next_present:boolean; // NOT a safe URL or a validated page chain
}>;
type PageDenied=Readonly<{
 decision:'DENIED';reason:Denial;
 candidates:readonly [];reported_next_present:null;
}>;
export type PageInspection=NoAuthority&(PageSuccess|PageDenied);
type SetSuccess=Readonly<{
 decision:'PAGE_SET_IDENTITIES_UNVERIFIED';reason:null;
 candidates:readonly TemplateIdentityCandidate[];
 pages_inspected:number;reported_last_page_without_next:true;
}>;
type SetDenied=Readonly<{
 decision:'DENIED';reason:Denial;
 candidates:readonly [];pages_inspected:0;
 reported_last_page_without_next:false;
}>;
export type PageSetInspection=NoAuthority&(SetSuccess|SetDenied);
const FLAGS=Object.freeze({
 meta_approval_verified:false,production_authorized:false,
 send_authorized:false,ack_allowed:false,retry_external:false,
 s0_write_authorized:false,commercial_effect_authorized:false,
 waba_binding_verified:false,page_chain_authenticated:false,
 page_set_complete_verified:false,
} as const);
const ID=/^[0-9]{5,25}$/,NAME=/^[a-z][a-z0-9_]{0,127}$/,
 LOCALE=/^[a-z]{2}(?:_[A-Z]{2})?$/;
const badUtf16=/(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]|[\uD800-\uDBFF](?![\uDC00-\uDFFF])/;
class Reject extends Error {readonly code:Denial;
 constructor(code:Denial){super(code);this.code=code;}
}
const reject=(code:Denial):never=>{throw new Reject(code);};
const deniedPage=(code:Denial):PageInspection=>Object.freeze({...FLAGS,
 decision:'DENIED' as const,reason:code,candidates:Object.freeze([]) as readonly [],
 reported_next_present:null});
const deniedSet=(code:Denial):PageSetInspection=>Object.freeze({...FLAGS,
 decision:'DENIED' as const,reason:code,candidates:Object.freeze([]) as readonly [],
 pages_inspected:0,reported_last_page_without_next:false as const});
function shape(raw:unknown,depth=0,stats={nodes:0}):any {
 if(++stats.nodes>4096||depth>16)reject('RESOURCE_LIMIT');
 if(raw===null||typeof raw==='boolean')return raw;
 if(typeof raw==='string'){
  if(raw.length>8192||badUtf16.test(raw))reject('RESOURCE_LIMIT');
  return raw;
 }
 if(typeof raw==='number'){
  if(!Number.isSafeInteger(raw))reject('INVALID_DATA');
  return raw;
 }
 if(!raw||typeof raw!=='object')reject('INVALID_DATA');
 const arr=Array.isArray(raw),proto=Object.getPrototypeOf(raw);
 if(arr?proto!==Array.prototype:proto!==Object.prototype&&proto!==null)
  reject('INVALID_DATA');
 const descriptors=Object.getOwnPropertyDescriptors(raw),keys=Reflect.ownKeys(raw);
 if(keys.some(k=>typeof k!=='string'||!Object.hasOwn(descriptors[k],'value')))
  reject('INVALID_DATA');
 if(arr){
  if(raw.length>100||keys.length!==raw.length+1)reject('RESOURCE_LIMIT');
  for(let i=0;i<raw.length;i++)if(!Object.hasOwn(descriptors,String(i)))
   reject('INVALID_DATA');
  return Array.from({length:raw.length},(_,i)=>
   shape(descriptors[String(i)].value,depth+1,stats));
 }
 if(keys.length>64)reject('RESOURCE_LIMIT');
 return Object.fromEntries((keys as string[]).map(k=>
  [k,shape(descriptors[k].value,depth+1,stats)]));
}
function exact(x:any,mandatory:readonly string[],optional:readonly string[],err:Denial){
 if(!x||typeof x!=='object'||Array.isArray(x)||
    mandatory.some(k=>!Object.hasOwn(x,k))||
    Object.keys(x).some(k=>!mandatory.includes(k)&&!optional.includes(k)))
  reject(err);
}
function opaquePaging(x:any){
 if(x===undefined)return false;
 exact(x,[],['next','previous','cursors'],'INVALID_PAGING');
 for(const key of ['next','previous']){
  if(Object.hasOwn(x,key)&&x[key]!==null&&
     (typeof x[key]!=='string'||x[key].length<1||x[key].length>4096))
   reject('INVALID_PAGING');
 }
 if(x.cursors!==undefined){
  exact(x.cursors,[],['before','after'],'INVALID_PAGING');
  for(const key of ['before','after'])
   if(Object.hasOwn(x.cursors,key)&&
      (typeof x.cursors[key]!=='string'||x.cursors[key].length<1||
       x.cursors[key].length>4096))reject('INVALID_PAGING');
 }
 // Never follow, parse, return, log, or trust paging URLs/cursors.
 return typeof x.next==='string'&&x.next.length>0;
}
function freeze<T>(v:T):T{
 if(v&&typeof v==='object'){
  for(const x of Object.values(v))freeze(x);
  Object.freeze(v);
 }
 return v;
}
/**
 * Only inspect one list response. Arbitrary extra fields of each *template
 * item* are intentionally ignored as non-authoritative metadata, never as
 * permissions, complete definitions, source receipts, or binding. Every item
 * must still include a valid unique ID/name/language triplet.
 */
export function inspectMetaTemplateListPage(raw:unknown):PageInspection {
 try {
  const page=shape(raw);
  exact(page,['data'],['paging'],'INVALID_ENVELOPE');
  if(!Array.isArray(page.data)||page.data.length>100)reject('INVALID_DATA');
  const next=opaquePaging(page.paging);
  if(next&&page.data.length===0)reject('INVALID_PAGING');
  const byId=new Set<string>(),byNameLocale=new Set<string>();
  const candidates:TemplateIdentityCandidate[]=[];
  for(const item of page.data){
   if(!item||typeof item!=='object'||Array.isArray(item)||
      typeof item.id!=='string'||!ID.test(item.id)||
      typeof item.name!=='string'||!NAME.test(item.name)||
      typeof item.language!=='string'||!LOCALE.test(item.language))
    reject('INVALID_DATA');
   const nameLocale=JSON.stringify([item.name,item.language]);
   if(byId.has(item.id)||byNameLocale.has(nameLocale))
    reject('DUPLICATE_OR_CONFLICTING_IDENTITY');
   byId.add(item.id);byNameLocale.add(nameLocale);
   candidates.push(Object.freeze({provider_template_id:item.id,
    template_name:item.name,language_code:item.language,
    needs_detail_by_id:true as const}));
  }
  return Object.freeze({...FLAGS,decision:'PAGE_IDENTITIES_UNVERIFIED',
   reason:null,candidates:Object.freeze(candidates),reported_next_present:next});
 } catch(e){return deniedPage(e instanceof Reject?e.code:'INVALID_DATA');}
}
/**
 * Bounded, INERT assembly of supplied page SHAPES. No continuity proof is
 * possible without an authenticated transport binding every page request to
 * the SAME WABA, cursor sequence and source generation. Even a "terminal"
 * page only reports what the supplied JSON claims.
 */
export function inspectMetaTemplateListPageSet(raw:unknown):PageSetInspection {
 try {
  if(!Array.isArray(raw)||Object.getPrototypeOf(raw)!==Array.prototype||
     raw.length<1||raw.length>10)reject('RESOURCE_LIMIT');
  const seenIds=new Set<string>(),seenNames=new Set<string>();
  const merged:TemplateIdentityCandidate[]=[];
  for(let i=0;i<raw.length;i++){
   if(!Object.hasOwn(raw,i))reject('INVALID_DATA');
   const inspected=inspectMetaTemplateListPage(raw[i]);
   if(inspected.decision!=='PAGE_IDENTITIES_UNVERIFIED')
    reject(inspected.reason);
   const shouldHaveNext=i<raw.length-1;
   if(inspected.reported_next_present!==shouldHaveNext)
    reject('INCOMPLETE_PAGE_SET');
   for(const item of inspected.candidates){
    const key=JSON.stringify([item.template_name,item.language_code]);
    if(seenIds.has(item.provider_template_id)||seenNames.has(key))
     reject('DUPLICATE_OR_CONFLICTING_IDENTITY');
    seenIds.add(item.provider_template_id);seenNames.add(key);
    if(merged.length>=500)reject('RESOURCE_LIMIT');
    merged.push(item);
   }
  }
  return Object.freeze({...FLAGS,decision:'PAGE_SET_IDENTITIES_UNVERIFIED',
   reason:null,candidates:freeze(merged),pages_inspected:raw.length,
   reported_last_page_without_next:true});
 }catch(e){return deniedSet(e instanceof Reject?e.code:'INVALID_DATA');}
}
