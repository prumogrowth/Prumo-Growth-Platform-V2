/** Synthetic WhatsApp media metadata; no Graph, downloads, S0 or ACK. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {inspectSignedMetaMediaMetadata as inspect}
 from './cloud-media-metadata-handoff.ts';

const SECRET='OFFLINE_MEDIA_TEST_KEY_NO_REAL_APP';
const ROUTE={waba_id:'123456789012',phone_number_id:'987654321098',revision:4};
const STAMP='1761000000';
const HASH=Buffer.alloc(32,0x11).toString('base64');
type Kind='image'|'audio'|'video'|'document'|'sticker';
const typeMime={image:'image/jpeg',audio:'audio/ogg; codecs=opus',
 video:'video/mp4',document:'application/pdf',sticker:'image/webp'};
const media=(kind:Kind='image',id='wamid.MEDIA_IN')=>({
 from:'5581888800000',id,timestamp:STAMP,type:kind,
 [kind]:{id:'987654321001',mime_type:typeMime[kind],sha256:HASH},
});
const text=()=>({from:'5581888800001',id:'wamid.TEXT',timestamp:STAMP,
 type:'text',text:{body:'Mensagem fictícia'}});
const status=(timestamp=STAMP)=>({
 id:'wamid.SENT',recipient_id:'5581888800000',
 status:'delivered',timestamp,
});
const root=(messages:unknown[]=[media()],statuses:unknown[]=[])=>({
 object:'whatsapp_business_account',entry:[{
 id:ROUTE.waba_id,changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:ROUTE.phone_number_id},
  messages,statuses,
 }}],
 }],
});
const bytes=(v:unknown)=>Buffer.from(JSON.stringify(v),'utf8');
const sign=(v:Uint8Array)=>
 'sha256='+createHmac('sha256',SECRET).update(v).digest('hex');
const run=(v:unknown=root(),route=ROUTE)=>{
 const b=bytes(v);return inspect(b,sign(b),SECRET,route);
};
function safe(result:Awaited<ReturnType<typeof inspect>>){
 assert.ok(Object.isFrozen(result));
 for(const key of [
  'ack_allowed','send_authorized','s0_write_authorized','retry_external',
  'production_authorized','delivery_confirmed','case_transition_authorized',
  'commercial_effect_authorized','consent_verified','deduplicated',
  'media_download_authorized','media_downloaded','media_content_verified',
  'mime_verified','checksum_verified','malware_scanned',
 ] as const)assert.equal(result[key],false,key);
}
function accepted(r:Awaited<ReturnType<typeof inspect>>){
 safe(r);assert.equal(r.decision,'SIGNED_MEDIA_REFERENCES_NOT_DURABLE');
 if(r.decision!=='SIGNED_MEDIA_REFERENCES_NOT_DURABLE')throw Error('denied');
 return r.observations;
}
function denied(r:Awaited<ReturnType<typeof inspect>>){
 safe(r);assert.equal(r.decision,'DENIED');
 if(r.decision!=='DENIED')throw Error('expected denial');
 assert.equal(r.observations.length,0);assert.equal(r.raw_sha256,null);
 return r.reason;
}

test('MEDIA-01 five supported kinds are extracted with technical identities',async()=>{
 const messages=(Object.keys(typeMime) as Kind[]).map((k,i)=>media(k,'wamid.MEDIA_'+i));
 const r=await run(root(messages));
 const obs=accepted(r);
 assert.deepEqual(obs.map(o=>o.media_kind),
  ['image','audio','video','document','sticker']);
 assert.deepEqual(obs.map(o=>o.position.item_index),[0,1,2,3,4]);
 assert.ok(obs.every(o=>o.provider_message_id.startsWith('wamid.MEDIA_')));
 assert.ok(obs.every(o=>o.media_id==='987654321001'));
 assert.equal(obs[0].sha256_claim,HASH);
 assert.equal(obs[0].mime_type_claim,'image/jpeg');
 assert.ok(Object.isFrozen(obs));assert.ok(Object.isFrozen(obs[0]));
 assert.ok(Object.isFrozen(obs[0].position));
 assert.match(r.raw_sha256!,/^[a-f0-9]{64}$/);
});
test('MEDIA-02 image, video and document captions remain untrusted',async()=>{
 const ims=['image','video','document'].map((k,i)=>{
  const m=media(k as Kind,'wamid.CAP_'+i);
  (m[k as Kind] as any).caption='Meu comprovante 🧾\nSegunda linha';
  return m;
 });
 const obs=accepted(await run(root(ims)));
 assert.ok(obs.every(o=>o.caption_untrusted==='Meu comprovante 🧾\nSegunda linha'));
 assert.ok(obs.every(o=>o.filename_untrusted===null));
});
test('MEDIA-03 document filename is preserved but never path-opened',async()=>{
 const m=media('document');
 (m.document as any).filename='contrato fictício.pdf';
 (m.document as any).caption='Veja o arquivo';
 const obs=accepted(await run(root([m])));
 assert.equal(obs[0].filename_untrusted,'contrato fictício.pdf');
 assert.equal(obs[0].caption_untrusted,'Veja o arquivo');
});
test('MEDIA-04 audio voice and sticker animated are optional observed hints',async()=>{
 const a=media('audio'),s=media('sticker','wamid.STICK');
 (a.audio as any).voice=true;
 (s.sticker as any).animated=false;
 const obs=accepted(await run(root([a,s])));
 assert.deepEqual(obs.map(x=>x.voice_hint),[true,null]);
 assert.deepEqual(obs.map(x=>x.animated_hint),[null,false]);
});
test('MEDIA-05 absent MIME/checksum are null, never fabricated',async()=>{
 const m=media();
 delete (m.image as any).mime_type;
 delete (m.image as any).sha256;
 const obs=accepted(await run(root([m])));
 assert.equal(obs[0].mime_type_claim,null);
 assert.equal(obs[0].sha256_claim,null);
});
test('MEDIA-06 mixed text, status and media preserve positions; no delivery inference',async()=>{
 const r=await run(root([text(),media(),text(),media('video','wamid.VID')],[status()]));
 const obs=accepted(r);
 assert.deepEqual(obs.map(x=>x.position.item_index),[1,3]);
 assert.ok(obs.every(x=>x.position.array_kind==='messages'));
 assert.equal(r.delivery_confirmed,false);
});
test('MEDIA-07 non-media callbacks return no media and no ACK permission',async()=>{
 const r=await run(root([text()],[status()]));
 assert.deepEqual(accepted(r),[]);
 assert.equal(r.ack_allowed,false);
});
test('MEDIA-08 missing, nonnumeric, empty, URL-shaped or oversized media ID denied',async()=>{
 for(const bad of [undefined,null,'','https://example.invalid/abc',
  'wamid.NOT_MEDIA_ID','34 55','9'.repeat(65)]){
  const m=media();
  if(bad===undefined)delete (m.image as any).id;
  else (m.image as any).id=bad;
  assert.equal(denied(await run(root([media(),m]))),'UNSUPPORTED_MEDIA_SHAPE');
 }
});
test('MEDIA-09 invalid or injected MIME type denied rather than normalized',async()=>{
 for(const bad of [null,4,'image/jpeg\r\nX-Foo: yes','nonsense',
  'image/','/jpeg','x'.repeat(129)]){
  const m=media();(m.image as any).mime_type=bad;
  assert.equal(denied(await run(root([m]))),'UNSUPPORTED_MEDIA_SHAPE');
 }
});
test('MEDIA-10 structurally invalid checksum is refused; not recomputed',async()=>{
 for(const bad of [null,23,'abc','0'.repeat(63),
  Buffer.alloc(31).toString('base64'),'%%%%']){
  const m=media();(m.image as any).sha256=bad;
  assert.equal(denied(await run(root([m]))),'UNSUPPORTED_MEDIA_SHAPE');
 }
});
test('MEDIA-11 captions and filenames with invalid types, controls or surrogates denied',async()=>{
 for(const bad of [123,null,'\u0000 bad','\uD800','a'.repeat(1025)]){
  const m=media('image');(m.image as any).caption=bad;
  assert.equal(denied(await run(root([m]))),'UNSUPPORTED_MEDIA_SHAPE');
 }
 for(const bad of [12,null,'\u0000evil','\uD800','b'.repeat(256)]){
  const m=media('document');(m.document as any).filename=bad;
  assert.equal(denied(await run(root([m]))),'UNSUPPORTED_MEDIA_SHAPE');
 }
});
test('MEDIA-12 unexpected URL, link, bytes, and commercial fields fail closed',async()=>{
 for(const extra of ['url','link','file_bytes','send_authorized','download_url']){
  const m=media();(m.image as any)[extra]='https://example.invalid/file';
  assert.equal(denied(await run(root([m]))),'UNSUPPORTED_MEDIA_SHAPE');
 }
});
test('MEDIA-13 media type-specific fields not transplanted between kinds',async()=>{
 for(const [kind,key] of [
  ['image','filename'],['document','voice'],['video','animated'],
  ['sticker','caption'],['audio','caption'],
 ] as [Kind,string][]){
  const m=media(kind);(m[kind] as any)[key]='incorrect';
  assert.equal(denied(await run(root([m]))),'UNSUPPORTED_MEDIA_SHAPE');
 }
});
test('MEDIA-14 malformed voice or animated flag is denied',async()=>{
 for(const val of ['true',1,null]){
  const a=media('audio');(a.audio as any).voice=val;
  const s=media('sticker');(s.sticker as any).animated=val;
  assert.equal(denied(await run(root([a]))),'UNSUPPORTED_MEDIA_SHAPE');
  assert.equal(denied(await run(root([s]))),'UNSUPPORTED_MEDIA_SHAPE');
 }
});
test('MEDIA-15 invalid signature, malformed signature and empty secret deny silently',async()=>{
 const b=bytes(root());
 for(const sig of ['sha256='+'0'.repeat(64),'invalid',null]){
  assert.equal(denied(await inspect(b,sig,SECRET,ROUTE)),'VERIFICATION_DENIED');
 }
 assert.equal(denied(await inspect(b,sign(b),'',ROUTE)),'VERIFICATION_DENIED');
});
test('MEDIA-16 wrong secret or trusted route cannot leak media candidates',async()=>{
 const b=bytes(root());
 for(const r of await Promise.all([
  inspect(b,sign(b),'WRONG_SECRET',ROUTE),
  inspect(b,sign(b),SECRET,{...ROUTE,waba_id:'900000000000'}),
  inspect(b,sign(b),SECRET,{...ROUTE,phone_number_id:'900000000000'}),
 ]))assert.equal(denied(r),'VERIFICATION_DENIED');
});
test('MEDIA-17 mixed WABA or phone changes deny entire signed batch',async()=>{
 const a=root();
 a.entry.push({id:'999999999999',changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:ROUTE.phone_number_id},
  messages:[media()],statuses:[],
 }}]});
 assert.equal(denied(await run(a)),'VERIFICATION_DENIED');
 const b=root();
 b.entry[0].changes.push({field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:'999999999999'},
  messages:[media()],statuses:[],
 }});
 assert.equal(denied(await run(b)),'VERIFICATION_DENIED');
});
test('MEDIA-18 invalid sibling status, unsupported field and empty media object block entire batch',async()=>{
 const a=await run(root([media()],[status('bad')]));
 assert.equal(denied(a),'VERIFICATION_DENIED');
 const b=root([media()]);
 (b.entry[0].changes[0] as any).field='contacts';
 assert.equal(denied(await run(b)),'VERIFICATION_DENIED');
 const m=media('document');(m as any).document={};
 assert.equal(denied(await run(root([media(),m]))),'UNSUPPORTED_MEDIA_SHAPE');
});
test('MEDIA-19 repeated media references remain separate pending durable dedupe',async()=>{
 const m=media();
 const r=await run(root([m,{...m}]));
 assert.deepEqual(accepted(r).map(x=>x.position.item_index),[0,1]);
 assert.equal(r.deduplicated,false);
});
test('MEDIA-20 byte mutation, body limit, event limit and invalid UTF8 fail safely',async()=>{
 const b=bytes(root([media()]));
 const action=inspect(b,sign(b),SECRET,ROUTE);
 b.fill(0);
 assert.equal(accepted(await action)[0].media_id,'987654321001');
 const original=bytes(root([media(),media('audio','wamid.AUD')]));
 assert.equal(denied(await inspect(original,sign(original),SECRET,ROUTE,
  {maxBodyBytes:original.length-1})),'VERIFICATION_DENIED');
 assert.equal(denied(await inspect(original,sign(original),SECRET,ROUTE,
  {maxEvents:1})),'VERIFICATION_DENIED');
 const invalid=Uint8Array.from([0xff,0xfe,0xfd]);
 assert.equal(denied(await inspect(invalid,sign(invalid),SECRET,ROUTE)),
  'VERIFICATION_DENIED');
});
