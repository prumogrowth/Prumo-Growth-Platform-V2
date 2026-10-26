/** WA61: 24 PG17-only cross-process tests for revocation, immutable
 * binding and cancellation. No production Meta/S1 authorization or network.
 */
import test,{after} from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import {spawn,spawnSync} from 'node:child_process';
import {createHmac,createHash,randomBytes,randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';

const DSN=process.env.PRUMO_TEST_DATABASE_URL??'';
const url=new URL(DSN);
if(url.protocol!=='postgresql:'||url.hostname!=='127.0.0.1'||url.port!=='5432'||
 url.username!=='postgres'||url.pathname!=='/prumo_s0_test_ci'||
 url.search||url.hash)throw Error('WA61_DISPOSABLE_ONLY');
for(const k of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER','PGSERVICE',
 'PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT','PGSSLKEY','PGSSLROOTCERT'])
 if(process.env[k])throw Error('WA61_LIBPQ_OVERRIDE');
const PASS=randomBytes(32).toString('hex');
const META=Buffer.alloc(48,0x4d),NOW=Math.floor(Date.now()/1000);
const TS=[0,1,2,3].map(i=>String(NOW-1500000-i*13));
const INTENT='f7400000-0000-4000-8000-000000000002';
const WAMID='wamid.WA40.SHARED',RECIPIENT='5581900000000';
const WABA='22346000002',PHONE='32346000002',APP='12346000002';
const all=[],keys=[];
const q=v=>"'"+String(v).replaceAll("'","''")+"'";
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
after(()=>{for(const x of all)
 if(x.child.exitCode===null&&x.child.signalCode===null)x.child.kill('SIGKILL');});
function run(sql){
 return spawnSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
  '-v','VERBOSITY=verbose',DSN,'-c',sql],{encoding:'utf8',timeout:12000,
  env:{...process.env,PGPASSWORD:'postgres'}});
}
function pg(sql){
 const x=run(sql);
 if(x.error||x.status!==0)throw Error('WA61_PG '+String(x.stderr).slice(-600));
 return x.stdout.trim();
}
function num(sql){return Number(pg('select count(*) from '+sql));}
function deniedSql(sql){
 const x=run(sql);
 assert.equal(x.error,undefined);
 assert.notEqual(x.status,0,'Forbidden mutation succeeded');
 assert.match(x.stderr,/42501|IMMUTABLE_TECHNICAL_BINDING/);
}
const event=ts=>'WA46_'+createHash('sha256').update(JSON.stringify(
 [WABA,PHONE,WAMID,RECIPIENT,'delivered',ts])).digest('hex');
const raw=ts=>Buffer.from(JSON.stringify({object:'whatsapp_business_account',
 entry:[{id:WABA,changes:[{field:'messages',value:{
  metadata:{phone_number_id:PHONE},statuses:[{
   id:WAMID,status:'delivered',recipient_id:RECIPIENT,timestamp:ts
  }]}}]}]}));
const where=ts=>'prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(event(ts));
const count=ts=>num(where(ts));
const snapshot=ts=>pg('select id::text||\'|\'||body_sha256||\'|\'||provider_status from '+where(ts));
const nonces=k=>num('prumo_private.meta_wa48_shadow_nonces_fixture_s0 where key_id='+q(k.id));
function newKey(){
 const k={id:randomUUID(),secret:randomBytes(48).toString('hex')};
 pg('insert into prumo_private.meta_wa48_shadow_keys_fixture_s0('+
  'key_id,app,secret,active,valid_from,valid_until) values ('+
  q(k.id)+','+q(APP)+',decode('+q(k.secret)+
  ",'hex'),true,clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '2 hours')");
 keys.push(k);
 return k;
}
async function worker(k,profile='current'){
 const exe=join(dirname(fileURLToPath(import.meta.url)),'s0_wa_064_pg17_restart_worker.mjs');
 const child=spawn(process.execPath,[exe],{env:{
  ...process.env,WA60_CLIENT_PASS:PASS,WA60_KEY_ID:k.id,
  WA60_KEY_SECRET:k.secret,WA60_CRASH_MODE:'normal',
  WA61_BINDING_PROFILE:profile
 },stdio:['pipe','pipe','pipe']});
 const x={child,k,profile,ready:null,receipts:[],stderr:''};
 all.push(x);
 let buffer='';
 child.stdout.setEncoding('utf8');
 child.stdout.on('data',data=>{
  buffer+=data;
  for(;;){
   const pos=buffer.indexOf('\n');if(pos<0)break;
   const line=buffer.slice(0,pos);buffer=buffer.slice(pos+1);
   try{
    const obj=JSON.parse(line);
    if(obj.type==='ready')x.ready=obj;
    else if(obj.type==='receipt')x.receipts.push(obj);
   }catch{x.stderr+='BAD_STDOUT '+line.slice(0,50);}
  }
 });
 child.stderr.on('data',data=>x.stderr+=String(data).slice(-300));
 const until=Date.now()+3500;
 while(!x.ready&&child.exitCode===null&&child.signalCode===null&&Date.now()<until)
  await sleep(15);
 assert.ok(x.ready,'WA61 child did not start '+x.stderr.slice(-300));
 assert.equal(x.ready.host,'127.0.0.1');
 assert.equal(x.ready.lab_only,true);
 assert.equal(x.ready.pid,child.pid);
 return x;
}
async function stop(x){
 assert.equal(x.child.exitCode,null,'worker already exited '+x.stderr);
 x.child.stdin.write('STOP\n');
 const until=Date.now()+3500;
 while(x.child.exitCode===null&&x.child.signalCode===null&&Date.now()<until)
  await sleep(15);
 if(x.child.exitCode===null&&x.child.signalCode===null)x.child.kill('SIGKILL');
 assert.equal(x.child.exitCode,0,'WA61 child stop '+x.stderr.slice(-300));
}
async function send(x,ts){
 const bytes=raw(ts);
 return await new Promise(resolve=>{
  const req=http.request({host:'127.0.0.1',port:x.ready.port,
   path:x.ready.route,method:'POST',agent:false,headers:{
    'Content-Type':'application/json','Content-Length':String(bytes.length),
    'X-Hub-Signature-256':'sha256='+createHmac('sha256',META).update(bytes).digest('hex')
   }},res=>{
    const chunks=[];
    res.on('data',b=>chunks.push(b));
    res.on('end',()=>{
     try{resolve({status:res.statusCode,body:JSON.parse(Buffer.concat(chunks).toString())});}
     catch{resolve({status:res.statusCode,broken:true});}
    });
   });
  req.on('error',err=>resolve({broken:true,error:String(err.code??err.message)}));
  req.setTimeout(5500,()=>req.destroy(Error('WA61_HTTP_TIMEOUT')));
  req.end(bytes);
 });
}
function assertNoAuthority(r){
 assert.equal(r.body?.meta_ack_emitted,false);
 assert.equal(r.body?.ack_allowed,false);
 assert.equal(r.body?.send_authorized,false);
}
function accepted(r){assert.equal(r.status,202,JSON.stringify(r));assertNoAuthority(r);}
function refused(r){assert.equal(r.status,403,JSON.stringify(r));assertNoAuthority(r);}
async function receipt(x,ts,outcome){
 const until=Date.now()+1300;
 while(Date.now()<until){
  if(x.receipts.some(v=>v.event===event(ts)&&v.outcome===outcome))return;
  await sleep(12);
 }
 assert.fail('WA61 missing receipt '+outcome+' '+JSON.stringify(x.receipts));
}
let k1,k2,k3,k4,k5,k6,A,B,C,D,E,F,G,H,prior,nBefore,baselineTotal;
const checks=[
 async()=>{
  assert.equal(pg('select current_database()'),'prumo_s0_test_ci');
  assert.equal(pg('select estado from prumo_private.outbox_intencoes_s0 where id='+q(INTENT)),'BLOQUEADA_GATES');
  assert.equal(num('prumo_private.meta_vinculos_tentativa_fixture_s0 where app_ref=\'FIXTURE_WA40_B\' and attempt_ref=\'ATTEMPT_B\' and provider_message_id='+q(WAMID)),1);
  pg('alter role prumo_s0_meta_wa48_client_lab login password '+q(PASS));
  for(const ts of TS)assert.equal(count(ts),0);
  baselineTotal=num('prumo_private.meta_status_forense_fixture_s0');
 },
 async()=>{k1=newKey();A=await worker(k1);},
 async()=>{accepted(await send(A,TS[0]));await receipt(A,TS[0],'LAB_OBSERVED_UNVERIFIED');},
 async()=>{assert.equal(count(TS[0]),1);prior=snapshot(TS[0]);assert.ok(prior.includes('|delivered'));},
 async()=>{await stop(A);},
 async()=>{B=await worker(k1);assert.notEqual(A.child.pid,B.child.pid);},
 async()=>{accepted(await send(B,TS[0]));await receipt(B,TS[0],'LAB_EXACT_BODY_REPLAY');assert.equal(snapshot(TS[0]),prior);},
 async()=>{await stop(B);nBefore=nonces(k1);assert.equal(nBefore,2);},
 async()=>{assert.equal(pg('select prumo_private.meta_wa48_shadow_revoke_fixture_s0('+q(k1.id)+')'),'LAB_REVOKED');},
 async()=>{C=await worker(k1);refused(await send(C,TS[0]));},
 async()=>{refused(await send(C,TS[1]));assert.equal(nonces(k1),nBefore);assert.equal(count(TS[1]),0);assert.equal(snapshot(TS[0]),prior);},
 async()=>{assert.equal(C.receipts.length,0);await stop(C);},
 async()=>{k2=newKey();D=await worker(k2);assert.notEqual(D.child.pid,C.child.pid);},
 async()=>{accepted(await send(D,TS[0]));await receipt(D,TS[0],'LAB_EXACT_BODY_REPLAY');assert.equal(snapshot(TS[0]),prior);},
 async()=>{accepted(await send(D,TS[1]));await receipt(D,TS[1],'LAB_OBSERVED_UNVERIFIED');assert.equal(count(TS[1]),1);},
 async()=>{
  deniedSql("update prumo_private.meta_vinculos_tentativa_fixture_s0 set attempt_ref='WA61_MUTATION' where app_ref='FIXTURE_WA40_B' and attempt_ref='ATTEMPT_B' and provider_message_id="+q(WAMID));
  assert.equal(num("prumo_private.meta_vinculos_tentativa_fixture_s0 where app_ref='FIXTURE_WA40_B' and attempt_ref='ATTEMPT_B' and provider_message_id="+q(WAMID)),1);
  assert.equal(snapshot(TS[0]),prior);
 },
 async()=>{await stop(D);k3=newKey();E=await worker(k3,'stale-attempt');},
 async()=>{refused(await send(E,TS[0]));refused(await send(E,TS[2]));assert.equal(count(TS[2]),0);assert.equal(nonces(k3),0);},
 async()=>{assert.equal(E.receipts.length,0);await stop(E);},
 async()=>{k4=newKey();F=await worker(k4,'disabled-route');refused(await send(F,TS[0]));assert.equal(nonces(k4),0);await stop(F);},
 async()=>{
  assert.equal(pg("update prumo_private.outbox_intencoes_s0 set estado='CANCELADA' where id="+q(INTENT)+" and estado='BLOQUEADA_GATES' returning estado"),'CANCELADA');
  assert.equal(snapshot(TS[0]),prior);
 },
 async()=>{
  k5=newKey();G=await worker(k5);
  accepted(await send(G,TS[0]));await receipt(G,TS[0],'LAB_EXACT_BODY_REPLAY');
  accepted(await send(G,TS[2]));await receipt(G,TS[2],'LAB_LATE_UNVERIFIED');
  assert.equal(count(TS[2]),1);assert.equal(snapshot(TS[0]),prior);
 },
 async()=>{
  await stop(G);k6=newKey();H=await worker(k6);
  accepted(await send(H,TS[2]));await receipt(H,TS[2],'LAB_EXACT_BODY_REPLAY');
  assert.equal(count(TS[2]),1);await stop(H);
 },
 async()=>{
  assert.equal(count(TS[0]),1);assert.equal(count(TS[1]),1);
  assert.equal(count(TS[2]),1);assert.equal(count(TS[3]),0);
  assert.equal(num('prumo_private.meta_status_forense_fixture_s0'),baselineTotal+3);
  assert.equal(snapshot(TS[0]),prior);
  assert.equal(num('prumo_private.meta_wa48_shadow_receipts_fixture_s0 where key_id in ('+keys.map(x=>q(x.id)).join(',')+')'),0);
  assert.equal(num('prumo_private.meta_status_forense_fixture_s0 where ack_allowed or send_authorized or retry_external or production_authorized or delivery_confirmed or case_transition_authorized or definitive_failure_count_increment'),0);
  assert.equal(pg("select has_function_privilege('prumo_s0_meta_wa48_client_lab',"+
   q('prumo_private.meta_wa52_locked_forensic_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)')+
   ",'EXECUTE')"),'f');
 }
];
assert.equal(checks.length,24);
for(let i=0;i<checks.length;i++)
 test('WA61-'+String(i+1).padStart(2,'0')+' revocation/restart PG17',async()=>{
  await checks[i]();
  console.log('WA61-'+String(i+1).padStart(2,'0')+' PASS');
 });
