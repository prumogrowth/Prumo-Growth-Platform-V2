/** WA57: HTTP/1.1 *loopback only*; 40 proofs, including sealed PG17 append. */
import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import net from 'node:net';
import {createHash,createHmac,randomBytes,randomUUID} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {createWa57OfflineLoopback} from './s0_wa_061_meta_http_loopback_transport.mjs';
import {createWa56OfflineArchiveBridge} from './s0_wa_060_meta_raw_to_pg17_bridge.mjs';
import {createWa46OfflineMetaGate} from './s0_wa_050_meta_raw_hmac_gate.mjs';
import {createWa45OfflineBoundary} from './s0_wa_049_meta_trusted_boundary.mjs';

const APP_SECRET=Buffer.alloc(48,0x4d),INTERNAL=Buffer.alloc(48,0x61);
const ROUTE_REF='ROUTE_WA57';
const R=Object.freeze({appTechnical:'12346000002',wabaTechnical:'22346000002',
 phoneTechnical:'32346000002',appRef:'FIXTURE_WA40_B',tenantRef:'SHOP_WA40_B',
 channelRef:'f7300000-0000-4000-8000-000000000002'});
const B=Object.freeze({appRef:R.appRef,tenantRef:R.tenantRef,channelRef:R.channelRef,
 intentRef:'f7400000-0000-4000-8000-000000000002',attemptRef:'ATTEMPT_B',
 correlationRef:'CORR_B',recipient:'5581900000000',wamid:'wamid.WA40.SHARED',
 bindingRevision:3});
const REG=Object.freeze({routeRef:ROUTE_REF,revision:1,...R,
 secretSlot:'WA57_META_SECRET',enabled:true});
const NOW=Math.floor(Date.now()/1000);
const rawStatus=(over={})=>Buffer.from(JSON.stringify({object:'whatsapp_business_account',
 entry:[{id:R.wabaTechnical,changes:[{field:'messages',value:{
  metadata:{phone_number_id:R.phoneTechnical},statuses:[{
   id:B.wamid,status:'delivered',recipient_id:B.recipient,timestamp:String(NOW),
   ...over}]}}]}]}));
const sig=x=>'sha256='+createHmac('sha256',APP_SECRET).update(x).digest('hex');
const RECEIPT=Object.freeze({entrypoint:'WA55_PG17_SINGLE_LAB_ONLY',lab_only:true});
const VERDICT=Object.freeze({decision:'LAB_META_RAW_TO_WA55_FORENSIC_ONLY',
 receipt:RECEIPT,meta_provenance_production_proven:false,
 service_authenticated:false,ack_allowed:false,send_authorized:false,
 production_authorized:false,case_transition_authorized:false});
function stub(behavior=async()=>({...VERDICT})){
 let calls=0,received;
 const bridge={receive:async(body,signature)=>{
  calls++;received={body:Buffer.from(body),signature};return behavior(body,signature);
 }};
 return {bridge,calls:()=>calls,last:()=>received};
}
async function service(bridge,fn){
 const server=createWa57OfflineLoopback({bridge});
 assert.ok(server);
 const address=await server.start();
 try{return await fn(address,server);}
 finally{await server.stop();}
}
function request(address,body=rawStatus(),options={}){
 const data=Buffer.isBuffer(body)?body:Buffer.from(body);
 const normal={'Content-Type':'application/json',
  'Content-Length':String(data.length),
  'X-Hub-Signature-256':sig(data)};
 const headers=options.headers===undefined?normal:options.headers;
 return new Promise((resolve,reject)=>{
  const req=http.request({host:'127.0.0.1',port:address.port,
   path:options.path??address.route,method:options.method??'POST',
   headers,agent:false},res=>{
    const chunks=[];
    res.on('data',x=>chunks.push(x));
    res.on('end',()=>{
     let parsed=null;
     try{parsed=JSON.parse(Buffer.concat(chunks).toString('utf8'));}catch{}
     resolve({status:res.statusCode,headers:res.headers,body:parsed});
    });
  });
  req.on('error',reject);
  req.setTimeout(5000,()=>req.destroy(Error('WA57_CLIENT_TIMEOUT')));
  req.end(data);
 });
}
function rawRequest(address,lines){
 return new Promise((resolve,reject)=>{
  const socket=net.createConnection({host:'127.0.0.1',port:address.port});
  let bytes='';
  socket.setTimeout(3500,()=>socket.destroy(Error('WA57_RAW_TIMEOUT')));
  socket.on('connect',()=>socket.end(lines.replaceAll('__PORT__',String(address.port))));
  socket.on('data',data=>{bytes+=data.toString('latin1');});
  socket.on('end',()=>resolve(bytes));
  socket.on('error',reject);
 });
}
const baseRaw=rawStatus();
const normalHeaders={
 'Host':'127.0.0.1:__PORT__',
 'Content-Type':'application/json',
 'Content-Length':String(baseRaw.length),
 'X-Hub-Signature-256':sig(baseRaw)};
const withHeaders=(a,change={})=>Object.fromEntries(Object.entries(
 {...normalHeaders,...change}).map(([k,v])=>[k,v==='127.0.0.1:__PORT__'?'127.0.0.1:'+a.port:v]));
const assertLab=(r,status,code)=>{
 assert.equal(r.status,status);
 assert.equal(r.body?.decision,code);
 assert.equal(r.body?.lab_only,true);
 assert.equal(r.body?.meta_ack_emitted,false);
 assert.equal(r.body?.ack_allowed,false);
 assert.equal(r.body?.send_authorized,false);
 assert.equal(r.headers?.['x-wa57-lab-only'],'true');
 assert.equal(r.headers?.['cache-control'],'no-store');
};
const checks=[
 async()=>{assert.equal(createWa57OfflineLoopback(null),null);},
 async()=>{assert.equal(createWa57OfflineLoopback({}),null);},
 async()=>{assert.equal(createWa57OfflineLoopback({bridge:{receive:1}}),null);},
 async()=>{await service(stub().bridge,async(a,s)=>{assert.equal(a.host,'127.0.0.1');assert.equal(a.route,'/__wa57_lab/status');assert.equal(s.address().port,a.port);});},
 async()=>{await service(stub().bridge,async a=>{const r=await request(a);assertLab(r,202,'LAB_HTTP_FORENSIC_STORED_ONLY');});},
 async()=>{const s=stub();await service(s.bridge,async a=>{await request(a);assert.equal(s.calls(),1);assert.deepEqual(s.last().body,baseRaw);});},
 async()=>{const s=stub();await service(s.bridge,async a=>{await request(a);assert.equal(s.last().signature,sig(baseRaw));});},
 async()=>{const s=stub();await service(s.bridge,async a=>{const r=await request(a,baseRaw,{method:'GET'});assertLab(r,404,'LAB_HTTP_ROUTE_DENIED');assert.equal(s.calls(),0);});},
 async()=>{const s=stub();await service(s.bridge,async a=>{const r=await request(a,baseRaw,{method:'PUT'});assertLab(r,404,'LAB_HTTP_ROUTE_DENIED');assert.equal(s.calls(),0);});},
 async()=>{const s=stub();await service(s.bridge,async a=>{assertLab(await request(a,baseRaw,{path:'/'}),404,'LAB_HTTP_ROUTE_DENIED');assert.equal(s.calls(),0);});},
 async()=>{await service(stub().bridge,async a=>{assertLab(await request(a,baseRaw,{path:a.route+'?q=1'}),404,'LAB_HTTP_ROUTE_DENIED');});},
 async()=>{const s=stub();await service(s.bridge,async a=>{assertLab(await request(a,baseRaw,{headers:withHeaders(a,{'Content-Type':'text/plain'})}),400,'LAB_HTTP_HEADERS_DENIED');assert.equal(s.calls(),0);});},
 async()=>{await service(stub().bridge,async a=>{assertLab(await request(a,baseRaw,{headers:withHeaders(a,{'Content-Type':'application/json; charset=utf-8'})}),400,'LAB_HTTP_HEADERS_DENIED');});},
 async()=>{await service(stub().bridge,async a=>{assertLab(await request(a,baseRaw,{headers:withHeaders(a,{'X-Hub-Signature-256':'sha256='+'0'.repeat(63)})}),400,'LAB_HTTP_HEADERS_DENIED');});},
 async()=>{await service(stub().bridge,async a=>{assertLab(await request(a,baseRaw,{headers:withHeaders(a,{'X-Hub-Signature-256':sig(baseRaw).toUpperCase()})}),400,'LAB_HTTP_HEADERS_DENIED');});},
 async()=>{await service(stub().bridge,async a=>{assertLab(await request(a,baseRaw,{headers:withHeaders(a,{'X-Hub-Signature-256':'sha1='+'0'.repeat(64)})}),400,'LAB_HTTP_HEADERS_DENIED');});},
 async()=>{await service(stub().bridge,async a=>{assertLab(await request(a,baseRaw,{headers:withHeaders(a,{'Host':'evil.example'})}),400,'LAB_HTTP_HEADERS_DENIED');});},
 async()=>{await service(stub().bridge,async a=>{const h=withHeaders(a);delete h['X-Hub-Signature-256'];assertLab(await request(a,baseRaw,{headers:h}),400,'LAB_HTTP_HEADERS_DENIED');});},
 async()=>{await service(stub().bridge,async a=>{const h=withHeaders(a);delete h['Content-Length'];assertLab(await request(a,baseRaw,{headers:h}),400,'LAB_HTTP_HEADERS_DENIED');});},
 async()=>{await service(stub().bridge,async a=>{assertLab(await request(a,baseRaw,{headers:withHeaders(a,{'Content-Length':'262145'})}),400,'LAB_HTTP_HEADERS_DENIED');});},
 async()=>{await service(stub().bridge,async a=>{assertLab(await request(a,baseRaw,{headers:withHeaders(a,{'Content-Length':'0'})}),400,'LAB_HTTP_HEADERS_DENIED');});},
 async()=>{await service(stub().bridge,async a=>{assertLab(await request(a,baseRaw,{headers:withHeaders(a,{'X-Forwarded-For':'192.0.2.10'})}),400,'LAB_HTTP_HEADERS_DENIED');});},
 async()=>{await service(stub().bridge,async a=>{assertLab(await request(a,baseRaw,{headers:withHeaders(a,{'Content-Encoding':'gzip'})}),400,'LAB_HTTP_HEADERS_DENIED');});},
 async()=>{await service(stub().bridge,async a=>{assertLab(await request(a,baseRaw,{headers:withHeaders(a,{'X-Debug-Tenant':'OTHER'})}),400,'LAB_HTTP_HEADERS_DENIED');});},
 async()=>{await service(stub().bridge,async a=>{const h=withHeaders(a);h['X-Hub-Signature-256']=[sig(baseRaw),sig(baseRaw)];assertLab(await request(a,baseRaw,{headers:h}),400,'LAB_HTTP_HEADERS_DENIED');});},
 async()=>{await service(stub().bridge,async a=>{const h=withHeaders(a);h['Content-Type']=['application/json','application/json'];assertLab(await request(a,baseRaw,{headers:h}),400,'LAB_HTTP_HEADERS_DENIED');});},
 async()=>{await service(stub().bridge,async a=>{const raw=[
  'POST '+a.route+' HTTP/1.1','Host: 127.0.0.1:__PORT__',
  'Content-Type: application/json','Content-Length: '+baseRaw.length,
  'Transfer-Encoding: chunked','X-Hub-Signature-256: '+sig(baseRaw),'Connection: close','',''].join('\r\n');
  const res=await rawRequest(a,raw);
  assert.match(res,/^HTTP\/1\.1 400 /);});},
 async()=>{await service(stub().bridge,async a=>{const raw=[
  'POST '+a.route+' HTTP/1.0','Host: 127.0.0.1:__PORT__',
  'Content-Type: application/json','Content-Length: 1',
  'X-Hub-Signature-256: '+sig(baseRaw),'Connection: close','','x'].join('\r\n');
  assert.match(await rawRequest(a,raw),/^HTTP\/1\.1 404 /);});},
 async()=>{await service(stub().bridge,async a=>{const raw=[
  'POST '+a.route+' HTTP/1.1','Host: 127.0.0.1:__PORT__',
  'Expect: 100-continue','Content-Type: application/json',
  'Content-Length: 1','X-Hub-Signature-256: '+sig(baseRaw),
  'Connection: close','','x'].join('\r\n');
  const res=await rawRequest(a,raw);assert.match(res,/^HTTP\/1\.1 417 /);assert.doesNotMatch(res,/100 Continue/);});},
 async()=>{const s=stub(async()=>({...VERDICT,ack_allowed:true}));await service(s.bridge,async a=>{assertLab(await request(a),403,'LAB_HTTP_FORENSIC_DENIED');});},
 async()=>{const s=stub(async()=>({...VERDICT,receipt:{entrypoint:'WA40',lab_only:true}}));await service(s.bridge,async a=>{assertLab(await request(a),403,'LAB_HTTP_FORENSIC_DENIED');});},
 async()=>{const s=stub(async()=>{throw Error('db unavailable');});await service(s.bridge,async a=>{assertLab(await request(a),503,'LAB_HTTP_UNAVAILABLE');});},
];

const DSN=process.env.PRUMO_TEST_DATABASE_URL;
const DBPASS=randomBytes(32).toString('hex'),DBKEY=randomUUID(),DBSECRET=randomBytes(48);
function db(sql,client=false){
 if(typeof DSN!=='string')throw Error('WA57 explicit local PG17 DSN required');
 const u=new URL(DSN);
 if(u.protocol!=='postgresql:'||u.hostname!=='127.0.0.1'||
    u.port!=='5432'||u.username!=='postgres'||
    u.pathname!=='/prumo_s0_test_ci'||u.search||u.hash)
  throw Error('WA57 refuses hosted database');
 for(const v of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER',
  'PGSERVICE','PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT','PGSSLKEY','PGSSLROOTCERT'])
  if(process.env[v])throw Error('WA57 PG override forbidden '+v);
 const dsn=client?'postgresql://prumo_s0_meta_wa48_client_lab@127.0.0.1:5432/prumo_s0_test_ci':DSN;
 const z=spawnSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose',dsn,'-c',sql],{
  encoding:'utf8',timeout:12000,
  env:{...process.env,PGPASSWORD:client?DBPASS:'postgres'}});
 if(z.error)throw z.error;
 if(z.status!==0)throw Error('WA57 PG17 SQL '+z.stderr.slice(-600));
 return z.stdout.trim();
}
const q=s=>"'"+String(s).replaceAll("'","''")+"'";
let physical,physicalAddress;
let writes=0;
function makePhysical(){
 db("alter role prumo_s0_meta_wa48_client_lab login password "+q(DBPASS));
 db("insert into prumo_private.meta_wa48_shadow_keys_fixture_s0"+
  "(key_id,app,secret,active,valid_from,valid_until) values("+
  q(DBKEY)+","+q(R.appTechnical)+",decode("+q(DBSECRET.toString('hex'))+
  ",'hex'),true,clock_timestamp()-interval '2 minutes',"+
  "clock_timestamp()+interval '1 hour')");
 const b=createWa45OfflineBoundary({getRegistry:async()=>R,
  lookupBinding:async()=>B,getInternalKey:async()=>Buffer.from(DBSECRET),
  newNonce:async()=>randomUUID(),nowSeconds:()=>NOW},DBKEY);
 const gate=createWa46OfflineMetaGate({getRegistry:async()=>REG,
  getMetaAppSecret:async()=>Buffer.from(APP_SECRET),nowSeconds:()=>NOW,
  wa45Boundary:b},ROUTE_REF);
 const bridge=createWa56OfflineArchiveBridge({rawGate:gate,
  getInternalKey:async()=>Buffer.from(DBSECRET),nowSeconds:()=>NOW,
  appendWa55:async ticket=>{
   writes++;
   const a=[...ticket.candidate,ticket.macSha256].map((v,i)=>i===13?String(Number(v)):q(v));
   return JSON.parse(db('select prumo_private.meta_wa55_single_entry_fixture_s0('+
    a.join(',')+')',true));
  }});
 physical=createWa57OfflineLoopback({bridge});
 assert.ok(physical);
}
checks.push(async()=>{makePhysical();physicalAddress=await physical.start();assert.equal(physicalAddress.host,'127.0.0.1');});
checks.push(async()=>{const r=await request(physicalAddress);assertLab(r,202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(writes,1);});
checks.push(async()=>{const r=await request(physicalAddress);assertLab(r,202,'LAB_HTTP_FORENSIC_STORED_ONLY');assert.equal(writes,2);});
checks.push(async()=>{const raw=rawStatus(),wrong='sha256='+'0'.repeat(64);
  const r=await request(physicalAddress,raw,{headers:withHeaders(physicalAddress,{'X-Hub-Signature-256':wrong})});
  assertLab(r,403,'LAB_HTTP_FORENSIC_DENIED');assert.equal(writes,2);});
checks.push(async()=>{const modified=rawStatus({id:'wamid.FORGED'});const r=await request(physicalAddress,modified);
  assertLab(r,403,'LAB_HTTP_FORENSIC_DENIED');assert.equal(writes,2);});
checks.push(async()=>{const event='WA46_'+createHash('sha256').update(JSON.stringify(
  [R.wabaTechnical,R.phoneTechnical,B.wamid,B.recipient,'delivered',String(NOW)])).digest('hex');
  assert.equal(db('select count(*) from prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(event)),'1');});
checks.push(async()=>{assert.equal(db('select count(*) from prumo_private.meta_wa48_shadow_receipts_fixture_s0 where key_id='+q(DBKEY)),'0');
  assert.equal(db("select has_function_privilege('prumo_s0_meta_wa48_client_lab',"+
   q('prumo_private.meta_wa52_locked_forensic_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)')+
   ",'EXECUTE')"),'f');});
checks.push(async()=>{await physical.stop();assert.equal(physical.address(),null);
  await assert.rejects(physical.stop(),/WA57_LIFECYCLE_DENIED/);
  await assert.rejects(physical.start(),/WA57_LIFECYCLE_DENIED/);});

assert.equal(checks.length,40);
for(let i=0;i<checks.length;i++){
 test('WA57-'+String(i+1).padStart(2,'0')+' loopback HTTP/WA55 PG17 proof',async()=>{
  await checks[i]();
  console.log('WA57-'+String(i+1).padStart(2,'0')+' PASS');
 });
}
