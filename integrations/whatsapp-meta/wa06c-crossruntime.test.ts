/** WA-06C: Node execution of the published TypeScript encoder against
 * independently produced Python reference vectors. Offline, synthetic only.
 */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {test} from 'node:test';
import {canonicalizeInternalProofV1,WA06B_CANONICAL_VERSION,WA06B_PROOF_VERSION} from './internal-proof-wire-v1.ts';

function fixture(): {claims:Record<string,unknown>;candidate:Record<string,unknown>} {
  const claims:Record<string,unknown>={
    proof_version:WA06B_PROOF_VERSION,canonicalization_version:WA06B_CANONICAL_VERSION,
    service_ref:'meta_ingestor',request_ref:'req_1',nonce_ref:'nonce_1',key_epoch:1,
    purpose:'meta_s0.ingest',audience:'s0_internal_ingress',issued_at_ms:1000,expires_at_ms:2000
  };
  const occurrence={position:{entry_index:0,change_index:0,array_kind:'statuses',item_index:0},
    event_kind:'status_callback',app_ref:'app_a',concessionaria_id:'loja_a',canal_id:'canal_a',
    waba_id:'waba_a',phone_number_id:'phone_a',provider_message_id:'wamid.ID=',
    provider_timestamp:'2026-10-18T12:00:00.000Z',provider_kind:'delivered'};
  const candidate:Record<string,unknown>={
    contract_version:'meta-s0-handoff.v0.1-proposed',batch_ref:'batch_1',route_ref:'route_1',
    route_revision:1,app_ref:'app_a',protected_payload_ref:'payload_1',payload_sha256:'a'.repeat(64),
    scope_sha256:'b'.repeat(64),event_count:1,occurrences:[occurrence],
    ack_allowed:false,production_authorized:false
  };
  return {claims,candidate};
}
type Fixture=ReturnType<typeof fixture>;
function scenario(name:string):Fixture {
  const v=fixture();
  if(name==='BASE') return v;
  if(name==='NONCE_ROTATED'){v.claims.nonce_ref='nonce_2';return v;}
  const all=v.candidate.occurrences as Array<{position:{item_index:number};canal_id:string;phone_number_id:string;provider_kind:string}>;
  if(name==='CALLBACK_REPEAT'||name==='TWO_CHANNELS'){
    const second=structuredClone(all[0]);second.position.item_index=1;
    if(name==='TWO_CHANNELS'){second.canal_id='canal_b';second.phone_number_id='phone_b';}
    all.push(second);v.candidate.event_count=2;return v;
  }
  if(name==='READ_STATUS'){all[0].provider_kind='read';return v;}
  throw Error('UNKNOWN_SCENARIO');
}
const hash=(input:Uint8Array)=>createHash('sha256').update(input).digest('hex');
const vectors = [
  {name:'BASE',length:585,digest:'c94993710cfc4a90d41314c89026385e7cbd446753b2fa7d0ec0cc7f65083209'},
  {name:'NONCE_ROTATED',length:585,digest:'219aec893fc30e0f96870d1170643033c8b169515c853085dc58baba6ef3e549'},
  {name:'CALLBACK_REPEAT',length:736,digest:'577cad6732765d18b4ee62af0feef71d2c62c86023a8ecd406f8ca3e2977f5e5'},
  {name:'TWO_CHANNELS',length:736,digest:'444411a4acf020fb799fd3aeb78b85f77ec0b482f0d10fdf1d91508e1b9cb267'},
  {name:'READ_STATUS',length:580,digest:'9dc572689a0ec12fdb45b6b21f8ddddad44aa1f10d1ef6acd32a911f1889eb93'}
] as const;
for(const v of vectors){
  test(`WA06C-VECTOR-${v.name}: TypeScript agrees with independent Python`,()=>{
    const x=scenario(v.name),wire=canonicalizeInternalProofV1(x.claims,x.candidate);
    assert.equal(wire.byteLength,v.length);assert.equal(hash(wire),v.digest);
  });
}
test('WA06C-NEG-01 fixed order independently of object property enumeration',()=>{
  const original=scenario('BASE');const reordered=structuredClone(original);
  reordered.claims=Object.fromEntries(Object.entries(reordered.claims).reverse());
  reordered.candidate=Object.fromEntries(Object.entries(reordered.candidate).reverse());
  assert.equal(hash(canonicalizeInternalProofV1(original.claims,original.candidate)),
    hash(canonicalizeInternalProofV1(reordered.claims,reordered.candidate)));
});
test('WA06C-NEG-02 callback status and channel tampering change result',()=>{
  const original=scenario('BASE');const altered=structuredClone(original);
  const entries=altered.candidate.occurrences as Array<{provider_kind:string;canal_id:string}>;
  entries[0].provider_kind='read';entries[0].canal_id='canal_other';
  assert.notEqual(hash(canonicalizeInternalProofV1(original.claims,original.candidate)),
    hash(canonicalizeInternalProofV1(altered.claims,altered.candidate)));
});
test('WA06C-NEG-03 no unsigned extra keys or ACK flag accepted',()=>{
  const extra=scenario('BASE');extra.claims.internal_secret='never';
  assert.throws(()=>canonicalizeInternalProofV1(extra.claims,extra.candidate),/INVALID_WA06B_PROOF_ENVELOPE/);
  const ack=scenario('BASE');ack.candidate.ack_allowed=true;
  assert.throws(()=>canonicalizeInternalProofV1(ack.claims,ack.candidate),/INVALID_WA06B_PROOF_ENVELOPE/);
});
