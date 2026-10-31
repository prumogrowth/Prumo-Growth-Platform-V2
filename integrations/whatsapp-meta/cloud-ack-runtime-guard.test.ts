/** Static ACK guard regression cases; no external IO or HTTP. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {scanRuntimeAckSource as scan} from './cloud-ack-runtime-guard.mjs';

const runtime='integrations/whatsapp-meta/unsafe.ts';
const def='integrations/whatsapp-meta/durable-receipt.ts';
test('ACK-GUARD-01 catches legacy helper imported under any alias',()=>{
 assert.deepEqual(scan(runtime,
  "import {decideBatchAck as unsafe} from './durable-receipt.ts';"),
 ['LEGACY_SHAPE_ONLY_HELPER_REFERENCE']);
});
test('ACK-GUARD-02 catches status property 200 including return object',()=>{
 assert.deepEqual(scan(runtime,'return {status: 200, action: unknown};'),
  ['UNRATIFIED_HTTP_200_LITERAL']);
});
test('ACK-GUARD-03 catches Express status(200)',()=>{
 assert.deepEqual(scan(runtime,'reply.status(200).end();'),
  ['UNRATIFIED_HTTP_200_LITERAL']);
});
test('ACK-GUARD-04 catches writeHead and sendStatus 200',()=>{
 for(const code of ['res.writeHead(200)','res.sendStatus(200)']){
  assert.deepEqual(scan(runtime,code),['UNRATIFIED_HTTP_200_LITERAL']);
 }
});
test('ACK-GUARD-05 catches numerical aliases for 200',()=>{
 for(const code of ['status=2e2','statusCode:0xc8','httpStatus = 200']){
  assert.deepEqual(scan(runtime,code),['UNRATIFIED_HTTP_200_LITERAL']);
 }
});
test('ACK-GUARD-06 catches ACK action even without HTTP status',()=>{
 assert.deepEqual(scan(runtime,"return {action:'ACK',reason:'ALL_ITEMS_DURABLE'};"),
  ['UNRATIFIED_ACK_ACTION']);
});
test('ACK-GUARD-07 catches positive HTTP authority flags',()=>{
 for(const code of ['ack_allowed:true','http_ack_allowed = true',
  'http_response_authorized:true']){
  assert.deepEqual(scan(runtime,code),['UNRATIFIED_ACK_AUTHORITY_FLAG']);
 }
});
test('ACK-GUARD-08 definition cannot revive HTTP200 while keeping legacy identifier',()=>{
 assert.deepEqual(scan(def,'export function decideBatchAck(){return {status:200}}'),
  ['UNRATIFIED_HTTP_200_LITERAL']);
});
test('ACK-GUARD-09 comments or historical tests do not trigger',()=>{
 assert.deepEqual(scan(runtime,
  '// decideBatchAck() emits {status:200,action:"ACK"} in history\n'
  +'const noAuthority={ack_allowed:false};'),[]);
 assert.deepEqual(scan('integrations/whatsapp-meta/unsafe.test.ts',
  'res.status(200); decideBatchAck();'),[]);
});
test('ACK-GUARD-10 pure denied result and provider status comparisons are fine',()=>{
 assert.deepEqual(scan(runtime,
  "return {decision:'DENIED',ack_allowed:false,http_ack_allowed:false};"+
  "const delivered=(event.status===200);"),[]);
});
test('ACK-GUARD-11 no cross-repository HTTP control beyond Meta scope',()=>{
 assert.deepEqual(scan('backend/other.ts','res.status(200);'),[]);
 assert.deepEqual(scan('backend/other.ts','decideBatchAck();'),
  ['LEGACY_SHAPE_ONLY_HELPER_REFERENCE']);
});
test('ACK-GUARD-12 scanner is deterministic for combined violations',()=>{
 const code="decideBatchAck(); res.status(200); return {ack_allowed:true,action:'ACK'}";
 assert.deepEqual(scan(runtime,code),[
  'LEGACY_SHAPE_ONLY_HELPER_REFERENCE','UNRATIFIED_HTTP_200_LITERAL',
  'UNRATIFIED_ACK_ACTION','UNRATIFIED_ACK_AUTHORITY_FLAG']);
});
