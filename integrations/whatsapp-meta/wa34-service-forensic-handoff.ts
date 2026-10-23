/**
 * WA34 -- isolated, SYNTHETIC privileged-service handoff envelope proposal.
 * Not a real service principal, not a Meta HMAC verifier, not a S0 API and
 * not a replay store. Only synthetic TEST ports may hold the fake internal
 * signing secret. A verified packet is CONTRACT_PENDING, NEVER write authority.
 * S0 must ratify issuer authentication + atomic nonce/revision consume.
 */
export type Wa34Scope=Readonly<{
  app_ref:string;concessionaria_id:string;canal_id:string;waba_id:string;
  phone_number_id:string;provider_message_id:string;recipient_verified:string;
  case_ref:string;attempt_ref:string;binding_revision:number;
  event_ref:string;provider_kind:'sent'|'delivered'|'read'|'failed';
  meta_body_sha256:string;
}>;
export type Wa34HandoffPayload=Wa34Scope & Readonly<{
  contract:'wa34-service-forensic-handoff.lab.v1';
  purpose:'FORENSIC_APPEND_ONLY';
  issuer:'WA34_SYNTHETIC_META_INGRESS';
  audience:'WA34_SYNTHETIC_S0_READER';
  nonce_ref:string;
  issued_at_ms:number;
  expires_at_ms:number;
  ack_allowed:false;send_authorized:false;retry_external:false;
  production_authorized:false;case_transition_authorized:false;
  definitive_failure_count_increment:false;
}>;
export type Wa34SignedPacket=Readonly<{
  payload:Wa34HandoffPayload;
  mac_sha256:string;
}>;
export type Wa34HandoffDecision=Readonly<{
  decision:'LAB_CONTRACT_PENDING'|'LAB_DENIED'|'LAB_UNAVAILABLE';
  ack_allowed:false;send_authorized:false;retry_external:false;
  production_authorized:false;case_transition_authorized:false;
  definitive_failure_count_increment:false;
}>;
const scopeKeys=['app_ref','concessionaria_id','canal_id','waba_id',
 'phone_number_id','provider_message_id','recipient_verified','case_ref',
 'attempt_ref','binding_revision','event_ref','provider_kind',
 'meta_body_sha256'] as const;
const packetKeys=['contract','purpose','issuer','audience','nonce_ref',
 'issued_at_ms','expires_at_ms',...scopeKeys,
 'ack_allowed','send_authorized','retry_external','production_authorized',
 'case_transition_authorized','definitive_failure_count_increment'] as const;
const invariantKeys=['ack_allowed','send_authorized','retry_external',
 'production_authorized','case_transition_authorized',
 'definitive_failure_count_increment'] as const;
const decision=(result:Wa34HandoffDecision['decision']):Wa34HandoffDecision=>
 Object.freeze({decision,ack_allowed:false,send_authorized:false,
   retry_external:false,production_authorized:false,
   case_transition_authorized:false,definitive_failure_count_increment:false});
const identifier=(x:unknown):x is string=>
 typeof x==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(x);
const isWamid=(x:unknown):x is string=>
 typeof x==='string'&&/^wamid[.][A-Za-z0-9+/_=:.-]{1,1024}$/.test(x);
const same=(a:Wa34Scope,b:Wa34Scope):boolean=>
 scopeKeys.every(k=>a[k]===b[k]);
function dataOnly(raw:unknown,keys:readonly string[]):Record<string,unknown>|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const d=Object.getOwnPropertyDescriptors(raw);
  if(Reflect.ownKeys(raw).length!==keys.length||
     Object.keys(d).length!==keys.length||
     !keys.every(k=>Object.hasOwn(d,k)&&Object.hasOwn(d[k],'value')))return null;
  return Object.fromEntries(keys.map(k=>[k,d[k].value]));
 }catch{return null;}
}
function validScope(v:Record<string,unknown>):v is Record<string,unknown>&Wa34Scope{
 return ['app_ref','concessionaria_id','canal_id','waba_id','case_ref',
    'attempt_ref','event_ref'].every(k=>identifier(v[k]))&&
   typeof v.phone_number_id==='string'&&/^\d{5,25}$/.test(v.phone_number_id)&&
   isWamid(v.provider_message_id)&&
   typeof v.recipient_verified==='string'&&/^\d{8,15}$/.test(v.recipient_verified)&&
   Number.isSafeInteger(v.binding_revision)&&Number(v.binding_revision)>0&&
   ['sent','delivered','read','failed'].includes(String(v.provider_kind))&&
   typeof v.meta_body_sha256==='string'&&/^[0-9a-f]{64}$/.test(v.meta_body_sha256);
}
function validPayload(v:Record<string,unknown>,now:number):v is Record<string,unknown>&Wa34HandoffPayload{
 return v.contract==='wa34-service-forensic-handoff.lab.v1'&&
   v.purpose==='FORENSIC_APPEND_ONLY'&&
   v.issuer==='WA34_SYNTHETIC_META_INGRESS'&&
   v.audience==='WA34_SYNTHETIC_S0_READER'&&identifier(v.nonce_ref)&&
   invariantKeys.every(k=>v[k]===false)&&validScope(v)&&
   Number.isSafeInteger(v.issued_at_ms)&&Number.isSafeInteger(v.expires_at_ms)&&
   Number(v.issued_at_ms)>=0&&Number(v.expires_at_ms)>Number(v.issued_at_ms)&&
   Number(v.expires_at_ms)-Number(v.issued_at_ms)<=120000&&
   now>=Number(v.issued_at_ms)&&now<Number(v.expires_at_ms);
}
function validKey(key:unknown):key is Uint8Array{
 return key instanceof Uint8Array&&key.byteLength>=32&&key.byteLength<=128;
}
function serialized(v:Record<string,unknown>):Uint8Array{
 return new TextEncoder().encode(JSON.stringify(packetKeys.map(k=>v[k])));
}
async function hmac(key:Uint8Array,v:Record<string,unknown>):Promise<string>{
 const k=await crypto.subtle.importKey('raw',Uint8Array.from(key),
    {name:'HMAC',hash:'SHA-256'},false,['sign']);
 const signed=new Uint8Array(await crypto.subtle.sign('HMAC',k,serialized(v)));
 return Array.from(signed,x=>x.toString(16).padStart(2,'0')).join('');
}
async function isHmac(key:Uint8Array,v:Record<string,unknown>,hex:string):Promise<boolean>{
 if(!/^[0-9a-f]{64}$/.test(hex))return false;
 const k=await crypto.subtle.importKey('raw',Uint8Array.from(key),
    {name:'HMAC',hash:'SHA-256'},false,['verify']);
 const bytes=Uint8Array.from(hex.match(/../g)!,x=>parseInt(x,16));
 return crypto.subtle.verify('HMAC',k,bytes,serialized(v));
}
/** A fake privileged issuer; caller MUST NOT be the HTTP/AI/client boundary. */
export async function issueWa34SyntheticFixture(
 rawScope:unknown,nonce_ref:string,issued_at_ms:number,
 lifetime_ms:number,internalKey:Uint8Array,
):Promise<Wa34SignedPacket|null>{
 try{
  const scope=dataOnly(rawScope,scopeKeys);
  if(!scope||!validScope(scope)||!identifier(nonce_ref)||
     !Number.isSafeInteger(issued_at_ms)||issued_at_ms<0||
     !Number.isSafeInteger(lifetime_ms)||lifetime_ms<1||
     lifetime_ms>120000||!validKey(internalKey))return null;
  const expires_at_ms=issued_at_ms+lifetime_ms;
  if(!Number.isSafeInteger(expires_at_ms))return null;
  const payload={
   contract:'wa34-service-forensic-handoff.lab.v1',
   purpose:'FORENSIC_APPEND_ONLY',issuer:'WA34_SYNTHETIC_META_INGRESS',
   audience:'WA34_SYNTHETIC_S0_READER',
   nonce_ref,issued_at_ms,expires_at_ms,...scope,
   ack_allowed:false,send_authorized:false,retry_external:false,
   production_authorized:false,case_transition_authorized:false,
   definitive_failure_count_increment:false,
  } as Wa34HandoffPayload;
  const mac_sha256=await hmac(internalKey,payload);
  return Object.freeze({payload:Object.freeze(payload),mac_sha256});
 }catch{return null;}
}
/** Contract-only, stateless: replay remains allowed unless S0 consumes nonce atomically. */
export async function verifyWa34SyntheticFixture(
 wire:unknown, expectedScope:unknown,nowMs:number,internalKey:Uint8Array,
):Promise<Wa34HandoffDecision>{
 try{
  if(!Number.isSafeInteger(nowMs)||nowMs<0||!validKey(internalKey))
    return decision('LAB_UNAVAILABLE');
  const packet=dataOnly(wire,['payload','mac_sha256']);
  const expected=dataOnly(expectedScope,scopeKeys);
  if(!packet||!expected||!validScope(expected))
    return decision('LAB_DENIED');
  const payload=dataOnly(packet.payload,packetKeys);
  if(!payload||!validPayload(payload,nowMs)||
     !same(payload,expected)||typeof packet.mac_sha256!=='string')
    return decision('LAB_DENIED');
  if(!await isHmac(internalKey,payload,packet.mac_sha256))
    return decision('LAB_DENIED');
  return decision('LAB_CONTRACT_PENDING');
 }catch{return decision('LAB_UNAVAILABLE');}
}
