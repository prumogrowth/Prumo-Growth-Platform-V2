/** WA59: bounded admission, slow sockets and sealed WA55 under saturation.
 * Local-only Node HTTP/1.1 + disposable PG17, no remote service or Meta ACK.
 * Adds NEW resource-limit proofs without re-running old HTTP/header matrices.
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

const DSN=process.env.PRUMO_TEST_DATABASE_URL??'';
const url=new URL(DSN);
if(url.protocol!=='postgresql:'||url.hostname!=='127.0.0.1'||url.port!=='5432'||
 url.username!=='postgres'||url.pathname!=='/prumo_s0_test_ci'||url.search||url.hash)
 throw Error('WA59 refuses anything but disposable PG17');
for(const k of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER',
 'PGSERVICE','PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT',
 'PGSSLKEY','PGSSLROOTCERT'])if(process.env[k])throw Error('WA59 libpq override '+k);
const CLIENT='prumo_s0_meta_wa48_client_lab';
const CLIENT_DSN='postgresql://'+CLIENT+'@127.0.0.1:5432/prumo_s0_test_ci';
const DBPASS=randomBytes(34).toString('hex'),DBKEY=randomUUID(),DBSECRET=randomBytes(48);
const APP_SECRET=Buffer.alloc(48,0x4d),ROUTE='ROUTE_WA59';
const NOW=Math.floor(Date.now()/1000),TS=String(NOW-911);
const R=Object.freeze({appTechnical:'12346000002',wabaTechnical:'22346000002',
 phoneTechnical:'32346000002',appRef:'FIXTURE_WA40_B',tenantRef:'SHOP_WA40_B',
 channelRef:'f7300000-0000-4000-8000-000000000002'});
const B=Object.freeze({appRef:R.appRef,tenantRef:R.tenantRef,channelRef:R.channelRef,
 intentRef:'f7400000-0000-4000-8000-000000000002',attemptRef:'ATTEMPT_B',
 correlationRef:'CORR_B',recipient:'5581900000000',wamid:'wamid.WA40.SHARED',
 bindingRevision:3});
const REG=Object.freeze({routeRef:ROUTE,revision:1,...R,secretSlot:'WA59_META_SECRET',enabled:true});
const raw=(stamp=TS)=>Buffer.from(JSON.stringify({object:'whatsapp_business_account',
 entry:[{id:R.wabaTechnical,changes:[{field:'messages',value:{
  metadata:{phone_number_id:R.phoneTechnical},statuses:[{
   id:B.wamid,status:'delivered',recipient_id:B.recipient,timestamp:stamp
  }]}}]}]}));
const RAW=raw();
const q=s=>"'"+String(s).replaceAll("'","''")+"'";
const sig=body=>'sha256='+createHmac('sha256',APP_SECRET).update(body).digest('hex');
const event=(stamp=TS)=>'WA46_'+createHash('sha256').update(JSON.stringify([
 R.wabaTechnical,R.phoneTechnical,B.wamid,B.recipient,'delivered',stamp])).digest('hex');
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const VERDICT=Object.freeze({decision:'LAB_META_RAW_TO_WA55_FORENSIC_ONLY',
 receipt:Object.freeze({entrypoint:'WA55_PG17_SINGLE_LAB_ONLY',lab_only:true}),
 meta_provenance_production_proven:false,service_authenticated:false,
 ack_allowed:false,send_authorized:false,production_authorized:false,
 case_transition_authorized:false});
const WA55='prumo_private.meta_wa55_single_entry_fixture_s0';
function pg(sql,client=false){
 const ds=client?CLIENT_DSN:DSN;
 const z=spawnSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
  '-v','VERBOSITY=verbose',ds,'-c',sql],{
  encoding:'utf8',timeout:16000,
  env:{...process.env,PGPASSWORD:client?DBPASS:'postgres'}});
 if(z.error||z.status!==0)throw Error('WA59 PG17 '+z.stderr?.slice(-800));
 return z.stdout.trim();
}
function pgAsync(sql){
 return new Promise((resolve,reject)=>{
  const p=spawn('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
   '-v','VERBOSITY=verbose',CLIENT_DSN,'-c',sql],
   {env:{...process.env,PGPASSWORD:DBPASS}});
  let output='',error='';
  p.stdout.on('data',d=>output+=d);
  p.stderr.on('data',d=>error+=d);
  p.on('error',reject);
  p.on('close',code=>code===0?resolve(output.trim()):reject(Error('WA59 writer '+error.slice(-650))));
 });
}
function dbcount(stamp=TS){
 return Number(pg('select count(*) from prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(event(stamp))));
}
function submit(address,body=RAW,extra={}){
 const headers={'Content-Type':'application/json','Content-Length':String(body.length),
  'X-Hub-Signature-256':sig(body),...extra};
 return new Promise((resolve,reject)=>{
  const req=http.request({host:'127.0.0.1',port:address.port,path:address.route,
   method:'POST',headers,agent:false},res=>{
   const buffers=[];
   res.on('data',d=>buffers.push(d));
   res.on('end',()=>{
    try{resolve({status:res.statusCode,
     headers:res.headers,body:JSON.parse(Buffer.concat(buffers).toString('utf8'))});}
    catch(e){reject(e);}
   });
  });
  req.on('error',reject);
  req.setTimeout(4800,()=>req.destroy(Error('WA59 REQUEST TIMEOUT')));
  req.end(body);
 });
}
function check(x,status,decision){
 assert.equal(x.status,status);
 assert.equal(x.body.decision,decision);
 assert.equal(x.body.lab_only,true);
 assert.equal(x.body.meta_ack_emitted,false);
 assert.equal(x.body.ack_allowed,false);
 assert.equal(x.body.send_authorized,false);
 assert.equal(x.headers['x-wa57-lab-only'],'true');
}
function rawSocket(a,header,body=Buffer.alloc(0)){
 return new Promise((resolve,reject)=>{
  const s=net.createConnection({host:'127.0.0.1',port:a.port});
  s.on('error',reject);
  s.once('connect',()=>{
   s.write(header.replaceAll('__PORT__',String(a.port)));
   if(body.length)s.write(body);
   resolve(s);
  });
 });
}
const makeHeader=(a,body=RAW,partial=false)=>[
 'POST '+a.route+' HTTP/1.1','Host: 127.0.0.1:__PORT__',
 'Content-Type: application/json','Content-Length: '+body.length,
 'X-Hub-Signature-256: '+sig(body),'Connection: close','',''
].join('\r\n');
async function fourSlow(a,body=RAW){
 return Promise.all(Array.from({length:4},async()=>{
  return rawSocket(a,makeHeader(a,body),body.subarray(0,9));
 }));
}
async function closeSockets(sockets){
 for(const s of sockets)s.destroy();
 await delay(85); // allow aborted readers to release admission slots
}
async function waitClose(socket,timeout=2600){
 return new Promise((resolve,reject)=>{
  let done=false;
  const timer=setTimeout(()=>{if(!done){done=true;socket.destroy();reject(Error('WA59 slow socket did not close'));}},timeout);
  socket.once('close',()=>{if(!done){done=true;clearTimeout(timer);resolve();}});
  socket.once('error',()=>{}); // EOF/reset is acceptable for slow abusive client
 });
}
function fake(impl=async()=>({...VERDICT})){
 let called=0;
 return {bridge:{receive:async(...args)=>{called++;return impl(...args);}},
  calls:()=>called};
}
async function lab(bridge,fn){
 const server=createWa57OfflineLoopback({bridge});
 assert.ok(server);
 const a=await server.start();
 try{return await fn(a,server);}
 finally{await server.stop();}
}
const cases=[];
let f,server,a,slow;
cases.push(async()=>{
 f=fake();server=createWa57OfflineLoopback({bridge:f.bridge});a=await server.start();
 slow=await fourSlow(a);await delay(80);
 assert.equal(a.host,'127.0.0.1');assert.equal(slow.length,4);
});
cases.push(async()=>{const r=await submit(a);check(r,503,'LAB_HTTP_BUSY');});
cases.push(async()=>{assert.equal(f.calls(),0);});
cases.push(async()=>{const r=await submit(a,RAW,{'Content-Type':'text/plain'});check(r,400,'LAB_HTTP_HEADERS_DENIED');});
cases.push(async()=>{await closeSockets(slow);assert.equal(f.calls(),0);});
cases.push(async()=>{check(await submit(a),202,'LAB_HTTP_FORENSIC_STORED_ONLY');});
cases.push(async()=>{await Promise.all(Array.from({length:4},()=>submit(a)));assert.equal(f.calls(),5);});
cases.push(async()=>{const sock=await rawSocket(a,
 'POST '+a.route+' HTTP/1.1\r\nHost: 127.0.0.1:__PORT__\r\nContent-Type: application/json\r\n');
 await waitClose(sock);assert.equal(f.calls(),5);
});
cases.push(async()=>{const sock=await rawSocket(a,makeHeader(a),RAW.subarray(0,7));
 await waitClose(sock);assert.equal(f.calls(),5);
});
cases.push(async()=>{check(await submit(a),202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(f.calls(),6);});
let releaseGate,seenGate,pending;
cases.push(async()=>{
 let n=0;
 const ready=new Promise(r=>seenGate=r);
 const gate=new Promise(r=>releaseGate=r);
 await server.stop();
 f=fake(async()=>{n++;if(n===4)seenGate();await gate;return {...VERDICT};});
 server=createWa57OfflineLoopback({bridge:f.bridge});
 a=await server.start();
 pending=Array.from({length:4},()=>submit(a));
 await Promise.race([ready,delay(2100).then(()=>{throw Error('WA59 gate was not saturated');})]);
 assert.equal(f.calls(),4);
});
cases.push(async()=>{check(await submit(a),503,'LAB_HTTP_BUSY');assert.equal(f.calls(),4);});
cases.push(async()=>{releaseGate();const results=await Promise.all(pending);
 results.forEach(x=>check(x,202,'LAB_HTTP_FORENSIC_STORED_ONLY'));});
cases.push(async()=>{check(await submit(a),202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(f.calls(),5);});
cases.push(async()=>{await server.stop();
 let n=0;
 f=fake(async()=>{if(++n===1)throw Error('WA59 transient writer');return {...VERDICT};});
 server=createWa57OfflineLoopback({bridge:f.bridge});a=await server.start();
 check(await submit(a),503,'LAB_HTTP_UNAVAILABLE');
 check(await submit(a),202,'LAB_HTTP_FORENSIC_STORED_ONLY');
 assert.equal(n,2);
});
cases.push(async()=>{await server.stop();assert.equal(server.address(),null);});

let physical,ap,physCalls=0,receipt=[];
function createPhysical(){
 pg('alter role '+CLIENT+' login password '+q(DBPASS));
 pg('insert into prumo_private.meta_wa48_shadow_keys_fixture_s0'+
  '(key_id,app,secret,active,valid_from,valid_until) values('+
  q(DBKEY)+','+q(R.appTechnical)+',decode('+q(DBSECRET.toString('hex'))+
  ",'hex'),true,clock_timestamp()-interval '3 minutes',clock_timestamp()+interval '1 hour')");
 const boundary=createWa45OfflineBoundary({
  getRegistry:async()=>R,lookupBinding:async()=>B,
  getInternalKey:async()=>Buffer.from(DBSECRET),
  newNonce:async()=>randomUUID(),nowSeconds:()=>NOW
 },DBKEY);
 const gate=createWa46OfflineMetaGate({
  getRegistry:async()=>REG,getMetaAppSecret:async()=>Buffer.from(APP_SECRET),
  nowSeconds:()=>NOW,wa45Boundary:boundary
 },ROUTE);
 const bridge=createWa56OfflineArchiveBridge({
  rawGate:gate,getInternalKey:async()=>Buffer.from(DBSECRET),nowSeconds:()=>NOW,
  appendWa55:async ticket=>{
   physCalls++;
   const args=[...ticket.candidate,ticket.macSha256]
    .map((x,i)=>i===13?String(Number(x)):q(x)).join(',');
   const x=JSON.parse(await pgAsync('select '+WA55+'('+args+')'));
   receipt.push({event:ticket.candidate[10],outcome:x.outcome});
   return x;
  }
 });
 physical=createWa57OfflineLoopback({bridge});
 assert.ok(physical);
}
let holds;
cases.push(async()=>{createPhysical();ap=await physical.start();assert.equal(dbcount(),0);});
cases.push(async()=>{holds=await fourSlow(ap);await delay(80);
 check(await submit(ap),503,'LAB_HTTP_BUSY');assert.equal(physCalls,0);assert.equal(dbcount(),0);
});
cases.push(async()=>{await closeSockets(holds);check(await submit(ap),202,'LAB_HTTP_FORENSIC_STORED_ONLY');
 assert.equal(physCalls,1);assert.equal(dbcount(),1);
});
cases.push(async()=>{const responses=await Promise.all(Array.from({length:4},()=>submit(ap)));
 responses.forEach(x=>check(x,202,'LAB_HTTP_FORENSIC_STORED_ONLY'));
 assert.equal(dbcount(),1);assert.equal(physCalls,5);
});
cases.push(async()=>{
 const list=receipt.filter(x=>x.event===event()).map(x=>x.outcome);
 assert.equal(list.filter(x=>x==='LAB_OBSERVED_UNVERIFIED').length,1);
 assert.equal(list.filter(x=>x==='LAB_EXACT_BODY_REPLAY').length,4);
});
cases.push(async()=>{const before=physCalls;check(await submit(ap,RAW,{
 'X-Hub-Signature-256':'sha256='+'0'.repeat(64)
 }),403,'LAB_HTTP_FORENSIC_DENIED');
 assert.equal(before,physCalls);assert.equal(dbcount(),1);
});
cases.push(async()=>{assert.equal(Number(pg(
  'select count(*) from prumo_private.meta_wa48_shadow_receipts_fixture_s0 where key_id='+q(DBKEY))),0);
 assert.equal(pg("select has_function_privilege('"+CLIENT+
  "','prumo_private.meta_wa52_locked_forensic_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)','EXECUTE')"),'f');
});
cases.push(async()=>{await physical.stop();assert.equal(physical.address(),null);});
assert.equal(cases.length,24);
for(let i=0;i<cases.length;i++){
 test('WA59-'+String(i+1).padStart(2,'0')+' bounded admission PG17',async()=>{
  await cases[i]();
  console.log('WA59-'+String(i+1).padStart(2,'0')+' PASS');
 });
}
