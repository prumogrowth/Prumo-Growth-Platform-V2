/**
 * WA44: exact wire-format builder for S0/044 *offline fixture only*.
 * Inputs called "trusted" are injected test fixtures, NOT authenticated claims.
 * No network, Meta Graph, DB write, S1 scope decision or production API.
 * In particular WA34's JSON HMAC cannot be translated/accepted as proof.
 */
import {createHmac, timingSafeEqual} from 'node:crypto';

export const WA44_AUDIENCE = 'WA44_S0_PG17_FIXTURE_ONLY';
const IDENT = /^[A-Za-z0-9_.:-]{1,128}$/;
const DIGITS = /^[0-9]{5,25}$/;
const RECIPIENT = /^[0-9]{8,15}$/;
const WAMID = /^wamid\.[A-Za-z0-9+/_=:.-]{1,1024}$/;
const HASH = /^[0-9a-f]{64}$/;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const KINDS = Object.freeze(['sent', 'delivered', 'read', 'failed']);
const RKEYS = Object.freeze(['appTechnical','wabaTechnical','phoneTechnical','appRef','tenantRef','channelRef']);
const BKEYS = Object.freeze(['appRef','tenantRef','channelRef','intentRef','attemptRef','correlationRef','recipient','wamid','bindingRevision']);
const EKEYS = Object.freeze(['eventRef','kind','bodySha256']);
export const WA44_WIRE_FIELDS = Object.freeze(['keyId','appTechnical','wabaTechnical','phoneTechnical','channelRef',
 'intentRef','attemptRef','correlationRef','recipient','wamid','eventRef','kind','bodySha256','issuedAtSeconds','nonce']);

function record(v, keys) {
 try {
  if(!v || typeof v !== 'object' || Array.isArray(v))return null;
  const proto=Object.getPrototypeOf(v);
  if(proto!==Object.prototype && proto!==null)return null;
  const own=Reflect.ownKeys(v);
  if(own.length!==keys.length || own.some(k=>typeof k!=='string'))return null;
  const desc=Object.getOwnPropertyDescriptors(v);
  if(!keys.every(k=>Object.hasOwn(desc,k) && Object.hasOwn(desc[k],'value')))return null;
  return Object.fromEntries(keys.map(k=>[k,desc[k].value]));
 }catch{return null;}
}
const id=x=>typeof x==='string' && IDENT.test(x);
const uuid=x=>typeof x==='string' && UUID.test(x);
const tech=x=>typeof x==='string' && DIGITS.test(x);
const sha=x=>typeof x==='string' && HASH.test(x);
const keybuf=x=>Buffer.isBuffer(x) && x.byteLength>=32 && x.byteLength<=128;

/**
 * Returns a *candidate* immutable 15-element tuple for the S0/044 fixture
 * after mock registry and S0 binding agree. It does not establish an identity.
 */
export function makeWa44CandidateFixture({registry, binding, event, keyId, nonce, issuedAtSeconds, expectedRevision}={}) {
 const r=record(registry,RKEYS),b=record(binding,BKEYS),e=record(event,EKEYS);
 if(!r||!b||!e||!uuid(keyId)||!uuid(nonce) ||
  !Number.isSafeInteger(issuedAtSeconds)||issuedAtSeconds<0||
  !Number.isSafeInteger(expectedRevision)||expectedRevision<1||
  !tech(r.appTechnical)||!tech(r.wabaTechnical)||!tech(r.phoneTechnical)||
  !id(r.appRef)||!id(r.tenantRef)||!uuid(r.channelRef)||
  !id(b.appRef)||!id(b.tenantRef)||!uuid(b.channelRef)||
  !uuid(b.intentRef)||!id(b.attemptRef)||!id(b.correlationRef)||
  typeof b.recipient!=='string'||!RECIPIENT.test(b.recipient)||
  typeof b.wamid!=='string'||!WAMID.test(b.wamid)||
  !Number.isSafeInteger(b.bindingRevision)||b.bindingRevision<1||
  !id(e.eventRef)||!KINDS.includes(e.kind)||!sha(e.bodySha256)||
  r.appRef!==b.appRef||r.tenantRef!==b.tenantRef||
  r.channelRef!==b.channelRef||b.bindingRevision!==expectedRevision)return null;
 return Object.freeze([
  keyId,r.appTechnical,r.wabaTechnical,r.phoneTechnical,r.channelRef,
  b.intentRef,b.attemptRef,b.correlationRef,b.recipient,b.wamid,
  e.eventRef,e.kind,e.bodySha256,String(issuedAtSeconds),nonce
 ]);
}

/** Exact S0/044 bytes, not WA34 JSON. Never returns a browser-facing API. */
export function wa44CanonicalBytes(candidate) {
 if(!Array.isArray(candidate)||candidate.length!==15||
    !Object.isFrozen(candidate))return null;
 const v=candidate;
 if(!uuid(v[0])||!tech(v[1])||!tech(v[2])||!tech(v[3])||
    !uuid(v[4])||!uuid(v[5])||!id(v[6])||!id(v[7])||
    typeof v[8]!=='string'||!RECIPIENT.test(v[8])||
    typeof v[9]!=='string'||!WAMID.test(v[9])||
    !id(v[10])||!KINDS.includes(v[11])||!sha(v[12])||
    !/^(0|[1-9][0-9]*)$/.test(v[13])||
    !Number.isSafeInteger(Number(v[13]))||!uuid(v[14]))return null;
 return Buffer.from(['prumo-meta-handoff-lab-v1','FORENSIC_APPEND_ONLY',...v].join('|'),'utf8');
}
/** Signs only the lab candidate; never asserts verified Meta provenance. */
export function signWa44Fixture(candidate, internalKey) {
 const material=wa44CanonicalBytes(candidate);
 if(!material||!keybuf(internalKey))return null;
 return Object.freeze({
  contract:'WA40_PG17_LAB_ONLY',audience:WA44_AUDIENCE,
  candidate,macSha256:createHmac('sha256',internalKey).update(material).digest('hex'),
  ack_allowed:false,send_authorized:false,retry_external:false,
  production_authorized:false,service_authenticated:false
 });
}
export function compareWa44FixtureSignature(candidate, internalKey, mac) {
 try{
  const bytes=wa44CanonicalBytes(candidate);
  if(!bytes||!keybuf(internalKey)||!sha(mac))return false;
  const x=createHmac('sha256',internalKey).update(bytes).digest();
  return timingSafeEqual(x,Buffer.from(mac,'hex'));
 }catch{return false;}
}
