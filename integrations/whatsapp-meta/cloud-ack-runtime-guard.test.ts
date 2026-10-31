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

test('ACK-GUARD-13 authenticated Meta GET challenge 200 is not POST ACK',()=>{
 assert.deepEqual(scan('integrations/whatsapp-meta/verify-get.ts',
  "return matches ? {status:200,body:challenge,headers} : forbidden();"),[]);
});
test('ACK-GUARD-14 observed outbound Graph HTTP200 is not webhook ACK',()=>{
 assert.deepEqual(scan(runtime,
  "const provider={http_status:200,send_state:'API_ACCEPTED'};"),[]);
});

test('ACK-GUARD-15 GET module cannot hide an unrelated ACK200',()=>{
 const path='integrations/whatsapp-meta/verify-get.ts';
 assert.deepEqual(scan(path,
  "return matches ? {status:200,body:challenge,headers} : forbidden(); "+
  "const webhook={status:200,action:'ACK',ack_allowed:true};"),[
  'UNRATIFIED_HTTP_200_LITERAL',
  'UNRATIFIED_ACK_ACTION',
  'UNRATIFIED_ACK_AUTHORITY_FLAG',
 ]);
});
test('ACK-GUARD-16 the exact GET response type is permitted but others are not',()=>{
 const path='integrations/whatsapp-meta/verify-get.ts';
 assert.deepEqual(scan(path,'readonly status: 200;'),[]);
 assert.deepEqual(scan(path,'readonly status: 200; const x={status:200};'),[
  'UNRATIFIED_HTTP_200_LITERAL',
 ]);
});
test('ACK-GUARD-17 altered GET success code must be reviewed',()=>{
 const path='integrations/whatsapp-meta/verify-get.ts';
 assert.deepEqual(scan(path,
  "return untrusted ? { status:200, body:challenge, headers }: forbidden();"),[
  'UNRATIFIED_HTTP_200_LITERAL',
 ]);
});


test('ACK-GUARD-18 slash inside string cannot hide live HTTP 200 or ACK',()=>{
 const code='const marker="safe // marker"; return {status:200,action:"ACK",ack_allowed:true};';
 assert.deepEqual(scan(runtime,code),[
  'UNRATIFIED_HTTP_200_LITERAL',
  'UNRATIFIED_ACK_ACTION',
  'UNRATIFIED_ACK_AUTHORITY_FLAG',
 ]);
});
test('ACK-GUARD-19 block-comment markers inside quoted strings do not mask code',()=>{
 const code='const marker="safe /* comment */ marker"; res.status(200);';
 assert.deepEqual(scan(runtime,code),['UNRATIFIED_HTTP_200_LITERAL']);
});
test('ACK-GUARD-20 real inline comments do not trigger false positives',()=>{
 const code="const ok={ack_allowed:false}; /* status:200, action:'ACK' */";
 assert.deepEqual(scan(runtime,code),[]);
});
test('ACK-GUARD-21 GET bypass cannot hide code behind quoted slash',()=>{
 const code='const marker="safe // marker"; return {status:200,action:"ACK"};';
 assert.deepEqual(scan('integrations/whatsapp-meta/verify-get.ts',code),[
  'UNRATIFIED_HTTP_200_LITERAL','UNRATIFIED_ACK_ACTION',
 ]);
});
