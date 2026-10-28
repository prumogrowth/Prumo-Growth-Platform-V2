/**
 * Ed25519 receipt consumer for S0–Meta–Ingress–01 LAB profile (PR #48).
 * Contract source (READ-ONLY): S0 protocol.py + ingress.py code SHA
 * 9e3077d222df2b3184ee6ea568fdac7c9da75567.
 *
 * This is a laboratory interoperability check, NOT a public ACK endpoint.
 * A pinned public key and context MUST originate from a separately trusted
 * host. No public key / key ID / tenant claim inside a receipt is authority.
 * No transport, storage, Meta Graph, HTTP status, dispatch or S0 write.
 */
import {createHash,createPublicKey,verify as verifySignature} from 'node:crypto';

const DOMAIN=Buffer.from('PRUMO/S0-META-INGRESS/RECEIPT/LAB/v1\0','utf8');
const VERSION='prumo.s0-meta-ingress.receipt.lab/1-candidate';
const DURABILITY='PG17_LOCAL_WAL_FSYNC_ON_SYNC_COMMIT_ON';
const HEX=/^[0-9a-f]{64}$/;
const IDENT=/^[A-Za-z0-9_.:-]{1,128}$/;
const REV=/^[1-9][0-9]{0,17}$/;
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const SPKI=Buffer.from('302a300506032b6570032100','hex');
const RECEIPT_FIELDS=[
 'version','instance','app','route','route_revision','batch_id',
 'raw_sha256','item_count','occurrence_ids','items_sha256',
 'binding_sha256','bindings','m2m_issuer','m2m_key_id',
 'm2m_key_revision','receipt_key_id','receipt_key_revision',
 'receipt_public_key','audit_id','recorded_at','state',
 'durability_profile','production_authorized',
 'commercial_transition_authorized',
] as const;
const RIGHTS=Object.freeze({
 ack_allowed:false,http_ack_allowed:false,partial_ack_allowed:false,
 http_response_authorized:false,production_authorized:false,
 send_authorized:false,s0_write_authorized:false,
 durable_receipt_verified:false,commit_verified:false,
 service_identity_verified:false,m2m_verified:false,
 channel_policy_ratified:false,commercial_effect_authorized:false,
 retry_external:false,automatic_retry_authorized:false,
 replay_suppression_authorized:false,
} as const);

type Rights=typeof RIGHTS;
export type TrustedExpectedS0LabBinding=Readonly<{
 waba:string;phone:string;channel:string;tenant:string;revision:string;
}>;
export type TrustedExpectedS0LabReceipt=Readonly<{
 app:string;route:string;route_revision:string;
 instance:string;receipt_key_id:string;receipt_key_revision:string;
 expected_item_count:number;
 bindings:readonly TrustedExpectedS0LabBinding[];
}>;
type Rejection='INVALID_INPUT'|'INVALID_RECEIPT_STRUCTURE'|
 'UNTRUSTED_OR_MISMATCHED_KEY'|'S0_SIGNATURE_DENIED'|
 'CONTEXT_OR_BODY_MISMATCH'|'BINDING_SCOPE_MISMATCH';
export type S0LabReceiptInterop=Rights&(
 Readonly<{decision:'DENIED';reason:Rejection;
  receipt_signature_matched:false;physical_bytes_matched:false;
  trusted_context_matched:false;}>|
 Readonly<{decision:'S0_LAB_SIGNATURE_AND_CONTEXT_MATCH_UNRATIFIED';
  reason:null;receipt_signature_matched:true;
  physical_bytes_matched:true;trusted_context_matched:true;}>
);
const deny=(reason:Rejection):S0LabReceiptInterop=>
 Object.freeze({...RIGHTS,decision:'DENIED' as const,reason,
  receipt_signature_matched:false as const,
  physical_bytes_matched:false as const,
  trusted_context_matched:false as const});
const match=():S0LabReceiptInterop=>Object.freeze({
 ...RIGHTS,
 decision:'S0_LAB_SIGNATURE_AND_CONTEXT_MATCH_UNRATIFIED' as const,
 reason:null,receipt_signature_matched:true as const,
 physical_bytes_matched:true as const,
 trusted_context_matched:true as const,
});
function dataRecord(raw:unknown):raw is Record<string,unknown>{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return false;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return false;
  return Reflect.ownKeys(raw).every(k=>
   typeof k==='string'&&
   Object.hasOwn(Object.getOwnPropertyDescriptor(raw,k)??{},'value'));
 }catch{return false;}
}
function exact(raw:unknown,keys:readonly string[]):raw is Record<string,unknown>{
 if(!dataRecord(raw))return false;
 const own=Reflect.ownKeys(raw);
 return own.length===keys.length&&keys.every(k=>Object.hasOwn(raw,k));
}
function string(raw:unknown,max=256):raw is string{
 return typeof raw==='string'&&raw.length>0&&raw.length<=max&&
  !/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(raw);
}
const identifier=(v:unknown):v is string=>
 typeof v==='string'&&IDENT.test(v);
const revision=(v:unknown):v is string=>
 typeof v==='string'&&REV.test(v);
const sha=(v:unknown):v is string=>
 typeof v==='string'&&HEX.test(v);
const uuid=(v:unknown):v is string=>
 typeof v==='string'&&UUID.test(v);
function strictB64(x:unknown,n:number):Buffer|null{
 if(typeof x!=='string'||x.length>200||
    !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(x))
  return null;
 const b=Buffer.from(x,'base64');
 return b.length===n&&b.toString('base64')===x?b:null;
}
/** Python json.dumps(sort_keys=True,separators=(',', ':'),ensure_ascii=False),
 * restricted to this lab's JSON-safe integer, ASCII-key object profile.
 * Throws on getters, cycles, sparse arrays, floats and unsupported primitives.
 */
function pyCanonical(v:unknown,depth=0,seen=new Set<object>()):string{
 if(depth>24)throw Error('NESTING');
 if(v===null)return 'null';
 if(typeof v==='string'){
  if(!string(v,65536))throw Error('INVALID_STRING');
  return JSON.stringify(v);
 }
 if(typeof v==='boolean')return v?'true':'false';
 if(typeof v==='number'&&Number.isSafeInteger(v)&&!Object.is(v,-0))
  return String(v);
 if(typeof v!=='object'||v===null||seen.has(v))
  throw Error('UNSUPPORTED_JSON');
 seen.add(v);
 try{
  if(Array.isArray(v)){
   if(v.length>1000||Reflect.ownKeys(v).length!==v.length+1)
    throw Error('ARRAY_LIMIT');
   const out=[];
   for(let i=0;i<v.length;i++){
    const desc=Object.getOwnPropertyDescriptor(v,String(i));
    if(!desc||!Object.hasOwn(desc,'value'))throw Error('ARRAY_ACCESSOR');
    out.push(pyCanonical(desc.value,depth+1,seen));
   }
   return '['+out.join(',')+']';
  }
  if(!dataRecord(v))throw Error('OBJECT_DESCRIPTOR');
  const entries=Object.entries(Object.getOwnPropertyDescriptors(v));
  if(entries.length>200)throw Error('OBJECT_LIMIT');
  entries.sort((a,b)=>a[0]<b[0]?-1:a[0]>b[0]?1:0);
  return '{'+entries.map(([k,desc])=>{
   if(!/^[A-Za-z0-9_]{1,128}$/.test(k)||!Object.hasOwn(desc,'value'))
    throw Error('UNSUPPORTED_KEY');
   return JSON.stringify(k)+':'+pyCanonical(desc.value,depth+1,seen);
  }).join(',')+'}';
 }finally{seen.delete(v);}
}
function bindingKey(v:{waba:string;phone:string;channel:string;tenant:string;revision:string}){
 return JSON.stringify([v.waba,v.phone,v.channel,v.tenant,v.revision]);
}
function validateBindings(v:unknown,expected:TrustedExpectedS0LabReceipt):boolean{
 if(!Array.isArray(v)||v.length<1||v.length>100||
    !Array.isArray(expected.bindings)||
    v.length!==expected.bindings.length)return false;
 const left=new Set<string>(),right=new Set<string>();
 for(const e of expected.bindings){
  if(!exact(e,['waba','phone','channel','tenant','revision'])||
     ![e.waba,e.phone,e.channel,e.tenant].every(identifier)||
     !revision(e.revision))return false;
  const k=bindingKey(e);
  if(right.has(k))return false;
  right.add(k);
 }
 for(const b of v){
  if(!exact(b,['route','waba','phone','app','tenant',
               'channel','revision','active'])||
     b.route!==expected.route||b.app!==expected.app||
     b.active!==true||
     ![b.waba,b.phone,b.tenant,b.channel].every(identifier)||
     !revision(b.revision))return false;
  const k=bindingKey(b as Parameters<typeof bindingKey>[0]);
  if(left.has(k)||!right.has(k))return false;
  left.add(k);
 }
 return left.size===right.size;
}
function receiptBodyValid(v:unknown,expected:TrustedExpectedS0LabReceipt):v is Record<string,unknown>{
 if(!exact(v,RECEIPT_FIELDS))return false;
 if(v.version!==VERSION||v.state!=='DURABLY_COMMITTED'||
    v.durability_profile!==DURABILITY||
    v.production_authorized!==false||
    v.commercial_transition_authorized!==false||
    v.app!==expected.app||v.route!==expected.route||
    v.route_revision!==expected.route_revision||
    v.instance!==expected.instance||
    v.receipt_key_id!==expected.receipt_key_id||
    v.receipt_key_revision!==expected.receipt_key_revision||
    v.item_count!==expected.expected_item_count||
    !uuid(v.batch_id)||!uuid(v.audit_id)||
    !sha(v.raw_sha256)||!sha(v.items_sha256)||!sha(v.binding_sha256)||
    !identifier(v.m2m_issuer)||!identifier(v.m2m_key_id)||
    !revision(v.m2m_key_revision)||
    !string(v.recorded_at,100)||
    !Array.isArray(v.occurrence_ids)||
    v.occurrence_ids.length!==v.item_count||
    v.occurrence_ids.length<1||v.occurrence_ids.length>100||
    v.occurrence_ids.some(x=>!uuid(x))||
    new Set(v.occurrence_ids).size!==v.occurrence_ids.length||
    !validateBindings(v.bindings,expected))return false;
 try{
  if(createHash('sha256').update(pyCanonical(v.bindings)).digest('hex')!==
     v.binding_sha256)return false;
 }catch{return false;}
 return true;
}
/** Never use this API as the authority for an HTTP ACK. The caller must have
 * authenticated the S0 public-key anchor independently. Any successful
 * laboratory signature check is still UNRATIFIED for a production decision.
 */
export function inspectPinnedS0LabReceipt(
 rawBody:Uint8Array,receipt:unknown,
 trustedExpected:TrustedExpectedS0LabReceipt,
 trustedS0PublicKey:Uint8Array,
):S0LabReceiptInterop{
 try{
  if(!(rawBody instanceof Uint8Array)||rawBody.byteLength<1||
      rawBody.byteLength>262144||
      !(trustedS0PublicKey instanceof Uint8Array)||
      trustedS0PublicKey.byteLength!==32||
      !exact(trustedExpected,[
       'app','route','route_revision','instance',
       'receipt_key_id','receipt_key_revision',
       'expected_item_count','bindings',
      ])||![trustedExpected.app,trustedExpected.route,
       trustedExpected.instance,trustedExpected.receipt_key_id]
       .every(identifier)||
      !revision(trustedExpected.route_revision)||
      !revision(trustedExpected.receipt_key_revision)||
      !Number.isSafeInteger(trustedExpected.expected_item_count)||
      trustedExpected.expected_item_count<1||
      trustedExpected.expected_item_count>100)
   return deny('INVALID_INPUT');
  if(!exact(receipt,['body','signature']))
   return deny('INVALID_RECEIPT_STRUCTURE');
  const body=receipt.body;
  if(!receiptBodyValid(body,trustedExpected))
   return deny('CONTEXT_OR_BODY_MISMATCH');
  const pinned=Buffer.from(trustedS0PublicKey);
  if(strictB64(body.receipt_public_key,32)?.equals(pinned)!==true)
   return deny('UNTRUSTED_OR_MISMATCHED_KEY');
  const signature=strictB64(receipt.signature,64);
  if(!signature)return deny('INVALID_RECEIPT_STRUCTURE');
  const digest=createHash('sha256').update(Buffer.from(rawBody)).digest('hex');
  if(digest!==body.raw_sha256)
   return deny('CONTEXT_OR_BODY_MISMATCH');
  const payload=Buffer.concat([DOMAIN,Buffer.from(pyCanonical(body),'utf8')]);
  const pub=createPublicKey({key:Buffer.concat([SPKI,pinned]),
   format:'der',type:'spki'});
  if(!verifySignature(null,payload,pub,signature))
   return deny('S0_SIGNATURE_DENIED');
  return match();
 }catch{return deny('INVALID_RECEIPT_STRUCTURE');}
}
