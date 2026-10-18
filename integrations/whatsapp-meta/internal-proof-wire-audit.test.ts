/** WA-06B-AUD2: regressions for DEC-WA-05 app ownership and sender/channel
 * mapping consistency. Local only; NOT authoritative authorization or S0 ACL.
 */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {test} from 'node:test';
import {canonicalizeInternalProofV1,WA06B_CANONICAL_VERSION,WA06B_PROOF_VERSION} from './internal-proof-wire-v1.ts';
function sample(){
 const claims={proof_version:WA06B_PROOF_VERSION,canonicalization_version:WA06B_CANONICAL_VERSION,service_ref:'meta_ingestor',request_ref:'req_1',nonce_ref:'nonce_1',key_epoch:1,purpose:'meta_s0.ingest',audience:'s0_internal_ingress',issued_at_ms:1000,expires_at_ms:2000};
 const o={position:{entry_index:0,change_index:0,array_kind:'statuses',item_index:0},event_kind:'status_callback',app_ref:'app_a',concessionaria_id:'loja_a',canal_id:'canal_a',waba_id:'waba_a',phone_number_id:'phone_a',provider_message_id:'wamid.ID=',provider_timestamp:'2026-10-18T12:00:00.000Z',provider_kind:'delivered'};
 const candidate={contract_version:'meta-s0-handoff.v0.1-proposed',batch_ref:'batch_1',route_ref:'route_1',route_revision:1,app_ref:'app_a',protected_payload_ref:'payload_1',payload_sha256:'a'.repeat(64),scope_sha256:'b'.repeat(64),event_count:1,occurrences:[o],ack_allowed:false,production_authorized:false};
 return {claims,candidate};
}
function two(){const x=sample();const o=structuredClone(x.candidate.occurrences[0]);o.position.item_index=1;x.candidate.occurrences.push(o);x.candidate.event_count=2;return x;}
function wire(x:ReturnType<typeof sample>){return canonicalizeInternalProofV1(x.claims,x.candidate);}
const denied=(x:ReturnType<typeof sample>)=>assert.throws(()=>wire(x),/INVALID_WA06B_PROOF_ENVELOPE/);
test('AUD-01: cross-shop batch under one App must be rejected',()=>{const x=two();x.candidate.occurrences[1].concessionaria_id='loja_b';denied(x);});
test('AUD-02: same sender cannot map to multiple channels in one batch',()=>{const x=two();x.candidate.occurrences[1].canal_id='canal_b';denied(x);});
test('AUD-03: same channel cannot map to multiple senders in one batch',()=>{const x=two();x.candidate.occurrences[1].phone_number_id='phone_b';denied(x);});
test('AUD-04: two distinct channels of same App and shop are allowed',()=>{const x=two();x.candidate.occurrences[1].canal_id='canal_b';x.candidate.occurrences[1].phone_number_id='phone_b';assert.ok(wire(x).length>0);});
test('AUD-05: duplicate callback occurrence, same shop+channel, remains distinct',()=>{const x=two();assert.ok(wire(x).length>0);});
test('AUD-06: existing canonical base vector remains unchanged',()=>{const x=sample();assert.equal(createHash('sha256').update(wire(x)).digest('hex'),'c94993710cfc4a90d41314c89026385e7cbd446753b2fa7d0ec0cc7f65083209');});
