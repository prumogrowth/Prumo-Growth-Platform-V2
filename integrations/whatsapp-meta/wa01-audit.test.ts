import { test } from 'node:test';
import assert from 'node:assert/strict';
import { inspectMetaVerifyGet } from './verify-get.ts';
import { technicalKeyHint } from './technical-keys.ts';
import type { MetaIngressEvent } from './inbound.ts';
const ev:MetaIngressEvent={source:'meta_whatsapp',event_kind:'inbound_message',waba_id:'WABA_A',phone_number_id:'PHONE_A',provider_message_id:'wamid.IN_A',provider_timestamp:'2026-10-18T00:00:00.000Z',participant_identifier:'5581900000000',provider_kind:'text',position:{entry_index:0,change_index:0,item_index:0,array_kind:'messages'}};
test('AUD-WA01-01 GET does not verify with another App token',async()=>{
 const query=new URLSearchParams({'hub.mode':'subscribe','hub.verify_token':'APPA_SECRET','hub.challenge':'00042'}).toString();
 assert.equal((await inspectMetaVerifyGet(query,'APPB_SECRET')).status,403);
 assert.equal((await inspectMetaVerifyGet(query,'APPA_SECRET')).body,'00042');
});
test('AUD-WA01-02 GET rejects duplicate and unknown parameters',async()=>{
 const baseline='hub.mode=subscribe&hub.verify_token=secret&hub.challenge=7';
 for(const q of [baseline+'&hub.challenge=5', baseline+'&canal_id=B'])assert.equal((await inspectMetaVerifyGet(q,'secret')).status,403);
});
test('AUD-WA01-03 GET rejects injected/nondecimal challenge',async()=>{
 for(const c of ['1%0A','%3Cscript%3E','-1','0'.repeat(33)])assert.equal((await inspectMetaVerifyGet('hub.mode=subscribe&hub.verify_token=x&hub.challenge='+c,'x')).status,403);
});
test('AUD-WA01-04 correlation hint always refuses automatic dedupe',async()=>{
 const key=await technicalKeyHint(ev,'APP_A'); assert.equal(key.safe_to_auto_dedupe,false);
 assert.equal(JSON.stringify(key).includes('5581900000000'),false);
});
test('AUD-WA01-05 even same status and timestamp might be distinct callbacks',async()=>{
 const status={...ev,event_kind:'status_callback' as const,provider_kind:'delivered',position:{...ev.position,array_kind:'statuses' as const}};
 const a=await technicalKeyHint(status,'APP_A'); const b=await technicalKeyHint({...status,position:{...status.position,item_index:1}},'APP_A');
 assert.equal(a.candidate_sha256,b.candidate_sha256); assert.equal(a.safe_to_auto_dedupe,false);
});
test('AUD-WA01-06 app, WABA, and phone number scope hints are separated',async()=>{
 const h=(e:MetaIngressEvent,app='APP_A')=>technicalKeyHint(e,app).then(x=>x.candidate_sha256);
 const baseline=await h(ev);for(const other of [await h(ev,'APP_B'),await h({...ev,waba_id:'WABA_B'}),await h({...ev,phone_number_id:'PHONE_B'})])assert.notEqual(other,baseline);
});
test('AUD-WA01-07 phone 8-9 variant never changes raw message correlation hint',async()=>{
 const a=await technicalKeyHint(ev,'APP_A'); const b=await technicalKeyHint({...ev,participant_identifier:'558100000000'},'APP_A');
 assert.equal(a.candidate_sha256,b.candidate_sha256);
});
