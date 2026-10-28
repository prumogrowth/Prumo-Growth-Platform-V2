/**
 * Candidate laboratory protocol. No production credential, JWT, Graph or HTTP.
 * HMAC profile is NEW and deliberately incompatible with WA34/WA44/GoTrue.
 */
import {createHash, createHmac, timingSafeEqual} from 'node:crypto';
export class InputRejected extends Error {}
export const VERSION = 'prumo.meta-s0.lab/0.1-candidate';
export const DOMAIN = 'PRUMO_META_S0_CANDIDATE_LAB_ONLY';
export const MAX_WIRE = 524288; // fixture budget, not a public ingress SLO
export const FLAGS = Object.freeze({
  production_authorized:false, send_authorized:false, ack_allowed:false,
  retry_automatically:false, delivery_confirmed:false,
  case_transition_authorized:false, definitive_failure_count_increment:false,
});
export const sha = bytes => createHash('sha256').update(bytes).digest('hex');
export const ident = x => typeof x === 'string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(x);
export const revision = x => typeof x === 'string' && /^[1-9][0-9]{0,18}$/.test(x)
  && BigInt(x) <= 9223372036854775807n;
export function exact(x, keys) {
  return x !== null && typeof x === 'object' && !Array.isArray(x)
    && [Object.prototype,null].includes(Object.getPrototypeOf(x))
    && Reflect.ownKeys(x).length === keys.length
    && keys.every(k => Object.hasOwn(x,k)
      && Object.hasOwn(Object.getOwnPropertyDescriptor(x,k),'value'));
}
export function decodeBase64(s, max) {
  if (typeof s !== 'string' || s.length > Math.ceil(max/3)*4
    || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(s))
    throw Error('INVALID_BASE64');
  const b = Buffer.from(s,'base64');
  if (b.length > max || b.toString('base64') !== s) throw Error('INVALID_BASE64');
  return b;
}
export function parseEnvelope(raw) {
  if (!(raw instanceof Uint8Array) || raw.length < 1 || raw.length > MAX_WIRE)
    throw Error('INPUT_REJECTED');
  const bytes = Buffer.from(raw);
  const text = new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);
  const p = JSON.parse(text);
  // This restricted INTERNAL lab profile accepts ONLY JSON.stringify bytes.
  // Duplicate names, escaped aliases, BOM and noncanonical encodings cannot
  // round-trip. This is NOT a general public Meta JSON parser.
  if (JSON.stringify(p) !== text || !exact(p,[
    'version','operation','request_id','correlation_id','nonce',
    'issued_at_ms','expires_at_ms','body',
  ]) || p.version !== VERSION || !ident(p.operation)
    || !ident(p.request_id) || !ident(p.correlation_id) || !ident(p.nonce)
    || !Number.isSafeInteger(p.issued_at_ms) || p.issued_at_ms < 0
    || !Number.isSafeInteger(p.expires_at_ms) || p.expires_at_ms <= p.issued_at_ms
    || p.expires_at_ms-p.issued_at_ms > 30000)
    throw Error('INPUT_REJECTED');
  return {bytes, payload:p, digest:sha(bytes)};
}
export function mac(key, keyId, raw) {
  return createHmac('sha256',key)
    .update(JSON.stringify([DOMAIN,keyId,sha(raw)])).digest('hex');
}
export function verifyMac(key, proof, raw) {
  if (!exact(proof,['kind','key_id','mac_sha256']) || proof.kind !== 'LAB_M2M_HMAC'
    || !ident(proof.key_id) || typeof proof.mac_sha256 !== 'string'
    || !/^[0-9a-f]{64}$/.test(proof.mac_sha256)) return false;
  return timingSafeEqual(Buffer.from(mac(key,proof.key_id,raw),'hex'),
    Buffer.from(proof.mac_sha256,'hex'));
}
// Only tests may use this issuer. Possessing a packet gives no send/ACK right.
export function signFixture(keyId,key,payload) {
  const bytes=Buffer.from(JSON.stringify(payload));
  return {bytes, proof:{kind:'LAB_M2M_HMAC',key_id:keyId,mac_sha256:mac(key,keyId,bytes)}};
}
export function response(code, request=null, extra={}) {
  return Object.freeze({code, request_id:request?.request_id??null,
    correlation_id:request?.correlation_id??null, ...extra,
    lab_ack_ready:false, ...FLAGS});
}
