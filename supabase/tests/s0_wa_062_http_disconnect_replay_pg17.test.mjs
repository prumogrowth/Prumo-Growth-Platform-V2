/** WA58: response-loss, client-abort, safe replay, and PG17 persistence proofs.
 * Executed only AFTER all WA39–57 regressions and WA55 entrypoint sealing.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import net from 'node:net';
import {spawn,spawnSync} from 'node:child_process';
import {createHmac,createHash,randomBytes,randomUUID} from 'node:crypto';
import {createWa57OfflineLoopback} from './s0_wa_061_meta_http_loopback_transport.mjs';
import {createWa56OfflineArchiveBridge} from './s0_wa_060_meta_raw_to_pg17_bridge.mjs';
import {createWa46OfflineMetaGate} from './s0_wa_050_meta_raw_hmac_gate.mjs';
import {createWa45OfflineBoundary} from './s0_wa_049_meta_trusted_boundary.mjs';

const APP_SECRET=Buffer.alloc(48,0x4d);
const KEY_SECRET=randomBytes(48),KEY_ID=randomUUID(),PASSWORD=randomBytes(33).toString('hex');
const CLIENT='prumo_s0_meta_wa48_client_lab';
const DSN=process.env.PRUMO_TEST_DATABASE_URL??'';
const u=new URL(DSN);
if(u.protocol!=='postgresql:'||u.hostname!=='127.0.0.1'||u.port!=='5432'||
 u.username!=='postgres'||u.pathname!=='/prumo_s0_test_ci'||u.search||u.hash)
 throw Error('WA58 REFUSED: disposable PostgreSQL 17 only');
for(const name of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER','PGSERVICE',
 'PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT','PGSSLKEY','PGSSLROOTCERT']){
 if(process.env[name])throw Error('WA58 libpq override refused '+name);
}
const LOGIN='postgresql://'+CLIENT+'@127.0.0.1:5432/prumo_s0_test_ci';
const R=Object.freeze({appTechnical:'12346000002',wabaTechnical:'22346000002',
 phoneTechnical:'32346000002',appRef:'FIXTURE_WA40_B',tenantRef:'SHOP_WA40_B',
 channelRef:'f7300000-0000-4000-8000-000000000002'});
const B=Object.freeze({appRef:R.appRef,tenantRef:R.tenantRef,channelRef:R.channelRef,
 intentRef:'f7400000-0000-4000-8000-000000000002',attemptRef:'ATTEMPT_B',
 correlationRef:'CORR_B',recipient:'5581900000000',wamid:'wamid.WA40.SHARED',
 bindingRevision:3});
const ROUTE='WA58_ONLY_LOCAL';
const REG=Object.freeze({routeRef:ROUTE,revision:1,...R,secretSlot:'WA58_META_FIXTURE',enabled:true});
const NOW=Math.floor(Date.now()/1000);
const TS=String(NOW-153); // isolate WA58 event_ref from WA56/57 runs
const q=x=>"'"+String(x).replaceAll("'","''")+"'";
const sec=x=>'sha256='+createHmac('sha256',APP_SECRET).update(x).digest('hex');
const mkRaw=(time=TS,over={})=>Buffer.from(JSON.stringify({object:'whatsapp_business_account',
 entry:[{id:R.wabaTechnical,changes:[{field:'messages',value:{
 metadata:{phone_number_id:R.phoneTechnical},statuses:[{
 id:B.wamid,status:'delivered',recipient_id:B.recipient,timestamp:time,...over}]}}]}]}));
const RAW=mkRaw();
const event=(ts=TS,kind='delivered')=>'WA46_'+createHash('sha256').update(
 JSON.stringify([R.wabaTechnical,R.phoneTechnical,B.wamid,B.recipient,kind,ts])).digest('hex');
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const YES=Object.freeze({decision:'LAB_META_RAW_TO_WA55_FORENSIC_ONLY',
 receipt:Object.freeze({entrypoint:'WA55_PG17_SINGLE_LAB_ONLY',lab_only:true}),
 meta_provenance_production_proven:false,service_authenticated:false,
 ack_allowed:false,send_authorized:false,production_authorized:false,
 case_transition_authorized:false});
function sql(statement,client=false){
 const cmd=['-X','-qAt','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose',
 client?LOGIN:DSN,'-c',statement];
 const env={...process.env,PGPASSWORD:client?PASSWORD:'postgres'};
 const out=spawnSync('psql',cmd,{encoding:'utf8',timeout:18000,env});
 if(out.error||out.status!==0)throw Error('WA58 SQL '+String(out.stderr).slice(-800));
 return out.stdout.trim();
}
function asyncSQL(statement){
 const args=['-X','-qAt','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose',LOGIN,'-c',statement];
 return new Promise((resolve,reject)=>{
  const proc=spawn('psql',args,{env:{...process.env,PGPASSWORD:PASSWORD}});
  let output='',error='';
  proc.stdout.on('data',d=>output+=d);
  proc.stderr.on('data',d=>error+=d);
  proc.on('error',reject);
  proc.on('close',code=>code===0?resolve(output.trim()):
   reject(Error('WA58 SQL async '+error.slice(-700))));
 });
}
function count(table,where='true'){return Number(sql('select count(*) from prumo_private.'+table+' where '+where));}
function send(address,data=RAW,header=sec(data)){
 return new Promise((resolve,reject)=>{
  const req=http.request({host:'127.0.0.1',port:address.port,path:address.route,
   method:'POST',agent:false,headers:{'content-type':'application/json',
    'content-length':String(data.length),'x-hub-signature-256':header}},res=>{
   const pieces=[];
   res.on('data',d=>pieces.push(d));
   res.on('end',()=>{
    let body;
    try{body=JSON.parse(Buffer.concat(pieces).toString('utf8'));}catch(e){return reject(e);}
    resolve({status:res.statusCode,body,headers:res.headers});
   });
  });
  req.on('error',reject);req.setTimeout(9000,()=>req.destroy(Error('WA58_REQUEST_TIMEOUT')));
  req.end(data);
 });
}
function assertResult(x,status,decision){
 assert.equal(x.status,status);
 assert.equal(x.body.decision,decision);
 assert.equal(x.body.lab_only,true);
 assert.equal(x.body.meta_ack_emitted,false);
 assert.equal(x.body.ack_allowed,false);
 assert.equal(x.body.send_authorized,false);
 assert.equal(x.headers['x-wa57-lab-only'],'true');
}
function createStub(impl=async()=>YES){
 let calls=0;
 return {bridge:{receive:async(...args)=>{calls++;return impl(...args);}},
 calls:()=>calls};
}
async function local(bridge,fn){
 const server=createWa57OfflineLoopback({bridge});assert.ok(server);
 const a=await server.start();
 try{return await fn(a,server);}finally{await server.stop();}
}
function abortPartial(a,body=RAW,countBytes=12){
 return new Promise((resolve,reject)=>{
  const s=net.createConnection({host:'127.0.0.1',port:a.port});
  s.on('error',reject);s.on('close',resolve);
  s.on('connect',()=>{
   const h=['POST '+a.route+' HTTP/1.1','Host: 127.0.0.1:'+a.port,
    'Content-Type: application/json','Content-Length: '+body.length,
    'X-Hub-Signature-256: '+sec(body),'Connection: close','',''].join('\r\n');
   s.write(h+body.subarray(0,countBytes).toString('utf8'));
   setTimeout(()=>s.destroy(),35);
  });
 });
}
function sendSocket(a,raw=RAW){
 return new Promise((resolve,reject)=>{
  const socket=net.createConnection({host:'127.0.0.1',port:a.port});
  socket.on('error',reject);
  socket.on('connect',()=>{
   const hdr=['POST '+a.route+' HTTP/1.1','Host: 127.0.0.1:'+a.port,
    'Content-Type: application/json','Content-Length: '+raw.length,
    'X-Hub-Signature-256: '+sec(raw),'Connection: close','',''].join('\r\n');
   socket.write(hdr);socket.write(raw);
   resolve(socket);
  });
 });
}
const cases=[
 async()=>{const s=createStub();await local(s.bridge,async a=>{assert.equal(a.host,'127.0.0.1');assert.ok(a.port>0);});},
 async()=>{const s=createStub();await local(s.bridge,async a=>{assertResult(await send(a),202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(s.calls(),1);});},
 async()=>{const s=createStub();await local(s.bridge,async a=>{await send(a);await send(a);assert.equal(s.calls(),2);});},
 async()=>{const s=createStub();await local(s.bridge,async a=>{await abortPartial(a);await sleep(70);assert.equal(s.calls(),0);});},
 async()=>{const s=createStub();await local(s.bridge,async a=>{await abortPartial(a,RAW,0);await sleep(70);assert.equal(s.calls(),0);});},
 async()=>{const s=createStub();await local(s.bridge,async a=>{await abortPartial(a,RAW,RAW.length-1);await sleep(70);assert.equal(s.calls(),0);});},
 async()=>{const s=createStub();await local(s.bridge,async a=>{for(let i=0;i<3;i++)await abortPartial(a,RAW,5);await sleep(70);assert.equal(s.calls(),0);});},
 async()=>{const s=createStub();await local(s.bridge,async a=>{await abortPartial(a);assertResult(await send(a),202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(s.calls(),1);});},
 async()=>{const s=createStub();await local(s.bridge,async a=>{const v=await send(a,RAW,'sha256='+'0'.repeat(64));assertResult(v,202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(s.calls(),1);});}, // Stub isolates HTTP framing; HMAC gate tested physically.
 async()=>{const s=createStub(async()=>{throw Error('fixture DB down');});await local(s.bridge,async a=>{assertResult(await send(a),503,'LAB_HTTP_UNAVAILABLE');assert.equal(s.calls(),1);});},
 async()=>{let n=0;const s=createStub(async()=>++n===1?Promise.reject(Error('fixture fail')):YES);await local(s.bridge,async a=>{assertResult(await send(a),503,'LAB_HTTP_UNAVAILABLE');assertResult(await send(a),202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(n,2);});},
 async()=>{const s=createStub(async()=>({...YES,ack_allowed:true}));await local(s.bridge,async a=>{assertResult(await send(a),403,'LAB_HTTP_FORENSIC_DENIED');});},
 async()=>{const s=createStub(async()=>({...YES,receipt:{entrypoint:'WA40',lab_only:true}}));await local(s.bridge,async a=>{assertResult(await send(a),403,'LAB_HTTP_FORENSIC_DENIED');});},
 async()=>{const s=createStub();await local(s.bridge,async a=>{await Promise.all(Array.from({length:4},()=>send(a)));assert.equal(s.calls(),4);});},
 async()=>{const s=createStub();await local(s.bridge,async a=>{assertResult(await send(a,RAW),202,'LAB_HTTP_FORENSIC_STORED_ONLY');assertResult(await send(a,RAW),202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(s.calls(),2);});},
 async()=>{let active=0,max=0;const s=createStub(async()=>{active++;max=Math.max(max,active);await sleep(50);active--;return YES;});await local(s.bridge,async a=>{await Promise.all(Array.from({length:3},()=>send(a)));assert.equal(max,3);});},
 async()=>{const s=createStub();await local(s.bridge,async(a,server)=>{assert.equal(server.address().host,'127.0.0.1');await send(a);});},
 async()=>{let release,seen;const waiting=new Promise(r=>seen=r),gate=new Promise(r=>release=r);
  const s=createStub(async()=>{seen();await gate;return YES;});
  await local(s.bridge,async a=>{const socket=await sendSocket(a);await waiting;socket.destroy();await sleep(35);release();await sleep(35);assert.equal(s.calls(),1);});},
];

let real,addr,writes=0,receipts=[],fault='none',hold=false;
let releaseHold,heldStarted,holdGate,holdSeen;
function configureHold(){
 hold=true;holdGate=new Promise(r=>releaseHold=r);holdSeen=new Promise(r=>heldStarted=r);
}
function setupReal(){
 sql('alter role '+CLIENT+' login password '+q(PASSWORD));
 sql('insert into prumo_private.meta_wa48_shadow_keys_fixture_s0'+
  '(key_id,app,secret,active,valid_from,valid_until) values('+
  q(KEY_ID)+','+q(R.appTechnical)+',decode('+q(KEY_SECRET.toString('hex'))+
  ",'hex'),true,clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '1 hour')");
 const boundary=createWa45OfflineBoundary({getRegistry:async()=>R,lookupBinding:async()=>B,
  getInternalKey:async()=>Buffer.from(KEY_SECRET),newNonce:async()=>randomUUID(),
  nowSeconds:()=>NOW},KEY_ID);
 const rawGate=createWa46OfflineMetaGate({getRegistry:async()=>REG,
  getMetaAppSecret:async()=>Buffer.from(APP_SECRET),nowSeconds:()=>NOW,
  wa45Boundary:boundary},ROUTE);
 const bridge=createWa56OfflineArchiveBridge({rawGate,
  getInternalKey:async()=>Buffer.from(KEY_SECRET),nowSeconds:()=>NOW,
  appendWa55:async ticket=>{
   writes++;
   if(hold){heldStarted();await holdGate;hold=false;}
   if(fault==='before'){fault='none';throw Error('WA58 simulated precommit failure');}
   const args=[...ticket.candidate,ticket.macSha256]
    .map((x,i)=>i===13?String(Number(x)):q(x)).join(',');
   const result=JSON.parse(await asyncSQL(
    'select prumo_private.meta_wa55_single_entry_fixture_s0('+args+')'));
   receipts.push({event:ticket.candidate[10],outcome:result.outcome});
   if(fault==='after'){fault='none';throw Error('WA58 response lost postcommit');}
   return result;
  }});
 real=createWa57OfflineLoopback({bridge});assert.ok(real);
}
function currentCount(eventRef){return count('meta_status_forense_fixture_s0','event_ref='+q(eventRef));}
const X1=RAW,X2=mkRaw(String(NOW-154)),X3=mkRaw(String(NOW-155)),X4=mkRaw(String(NOW-156));
const X5=mkRaw(String(NOW-157)),X6=mkRaw(String(NOW-158));
const E1=event(TS),E2=event(String(NOW-154)),E3=event(String(NOW-155)),
 E4=event(String(NOW-156)),E5=event(String(NOW-157)),E6=event(String(NOW-158));

cases.push(async()=>{setupReal();addr=await real.start();assert.equal(addr.host,'127.0.0.1');});
cases.push(async()=>{const x=await send(addr,X1);assertResult(x,202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(currentCount(E1),1);});
cases.push(async()=>{assertResult(await send(addr,X1),202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(currentCount(E1),1);});
cases.push(async()=>{assert.deepEqual(receipts.filter(x=>x.event===E1).map(x=>x.outcome),['LAB_OBSERVED_UNVERIFIED','LAB_EXACT_BODY_REPLAY']);});
cases.push(async()=>{const c=writes;await abortPartial(addr,X2,9);await sleep(90);assert.equal(writes,c);assert.equal(currentCount(E2),0);});
cases.push(async()=>{const c=writes;assertResult(await send(addr,X2,'sha256='+'0'.repeat(64)),403,'LAB_HTTP_FORENSIC_DENIED');assert.equal(writes,c);assert.equal(currentCount(E2),0);});
cases.push(async()=>{fault='before';assertResult(await send(addr,X2),403,'LAB_HTTP_FORENSIC_DENIED');assert.equal(currentCount(E2),0);});
cases.push(async()=>{assertResult(await send(addr,X2),202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(currentCount(E2),1);});
cases.push(async()=>{fault='after';assertResult(await send(addr,X3),403,'LAB_HTTP_FORENSIC_DENIED');assert.equal(currentCount(E3),1);});
cases.push(async()=>{assertResult(await send(addr,X3),202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(currentCount(E3),1);assert.equal(receipts.filter(x=>x.event===E3).at(-1).outcome,'LAB_EXACT_BODY_REPLAY');});
cases.push(async()=>{configureHold();const socket=await sendSocket(addr,X4);await holdSeen;socket.destroy();await sleep(40);releaseHold();await sleep(180);assert.equal(currentCount(E4),1);});
cases.push(async()=>{assertResult(await send(addr,X4),202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(currentCount(E4),1);assert.equal(receipts.filter(x=>x.event===E4).at(-1).outcome,'LAB_EXACT_BODY_REPLAY');});
cases.push(async()=>{const before=writes;const all=await Promise.all(Array.from({length:4},()=>send(addr,X5)));all.forEach(x=>assertResult(x,202,'LAB_HTTP_FORENSIC_STORED_ONLY'));assert.equal(writes-before,4);assert.equal(currentCount(E5),1);});
cases.push(async()=>{const statuses=receipts.filter(x=>x.event===E5).map(x=>x.outcome);assert.equal(statuses.filter(x=>x==='LAB_OBSERVED_UNVERIFIED').length,1);assert.equal(statuses.filter(x=>x==='LAB_EXACT_BODY_REPLAY').length,3);});
cases.push(async()=>{const rawVariant=Buffer.from(X6.toString('utf8')+' ');assertResult(await send(addr,X6),202,'LAB_HTTP_FORENSIC_STORED_ONLY');assertResult(await send(addr,rawVariant),202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(currentCount(E6),2);});
cases.push(async()=>{const x=receipts.filter(x=>x.event===E6).map(x=>x.outcome);assert.deepEqual(x,['LAB_OBSERVED_UNVERIFIED','LAB_BODY_VARIANT_QUARANTINED']);});
cases.push(async()=>{assert.equal(count('meta_wa48_shadow_receipts_fixture_s0','key_id='+q(KEY_ID)),0);assert.equal(Number(sql("select count(*) from prumo_private.meta_status_forense_fixture_s0 where ack_allowed or send_authorized or retry_external or production_authorized or delivery_confirmed or case_transition_authorized or definitive_failure_count_increment")),0);});
cases.push(async()=>{await real.stop();assert.equal(real.address(),null);assert.equal(sql("select has_function_privilege('"+CLIENT+"','prumo_private.meta_wa52_locked_forensic_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)','EXECUTE')"),'f');});

assert.equal(cases.length,36);
for(let i=0;i<cases.length;i++){
 test('WA58-'+String(i+1).padStart(2,'0')+' disconnect/retransmit S0 PG17',async()=>{
  await cases[i]();
  console.log('WA58-'+String(i+1).padStart(2,'0')+' PASS');
 });
}
