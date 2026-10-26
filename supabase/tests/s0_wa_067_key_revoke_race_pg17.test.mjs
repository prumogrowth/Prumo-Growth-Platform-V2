/** WA62: 20 physical PG17 checks of revoke-vs-append across Node/PID.
 * No public transport, S1, hosted database, commercial or Meta actions.
 */
import test,{after} from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import {spawn,spawnSync} from 'node:child_process';
import {createHash,createHmac,randomBytes,randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';
const DSN=process.env.PRUMO_TEST_DATABASE_URL??'',u=new URL(DSN);
if(u.protocol!=='postgresql:'||u.hostname!=='127.0.0.1'||u.port!=='5432'||
 u.username!=='postgres'||u.pathname!=='/prumo_s0_test_ci'||u.search||u.hash)
 throw Error('WA62_DISPOSABLE_ONLY');
for(const k of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER',
 'PGSERVICE','PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT','PGSSLKEY','PGSSLROOTCERT'])
 if(process.env[k])throw Error('WA62_LIBPQ_OVERRIDE');
const PASS=randomBytes(32).toString('hex'),META=Buffer.alloc(48,0x4d);
const APP='12346000002',WABA='22346000002',PHONE='32346000002';
const WAMID='wamid.WA40.SHARED',RECIPIENT='5581900000000';
const TS=[0,1,2,3].map(i=>String(Math.floor(Date.now()/1000)-1800000-i*19));
const q=v=>"'"+String(v).replaceAll("'","''")+"'";
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const actors=[];
after(()=>{for(const x of actors){
 const c=x.child??x;if(c.exitCode===null&&c.signalCode===null)c.kill('SIGKILL');
}});
function spawnPG(query){
 return spawn('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
  '-v','VERBOSITY=verbose',DSN,'-c',query],{
  env:{...process.env,PGPASSWORD:'postgres'},stdio:['ignore','pipe','pipe']});
}
function pg(sql){
 const x=spawnSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
  '-v','VERBOSITY=verbose',DSN,'-c',sql],{
  encoding:'utf8',timeout:12000,env:{...process.env,PGPASSWORD:'postgres'}});
 if(x.error||x.status!==0)throw Error('WA62_SQL '+String(x.stderr).slice(-650));
 return x.stdout.trim();
}
const event=ts=>'WA46_'+createHash('sha256').update(JSON.stringify(
 [WABA,PHONE,WAMID,RECIPIENT,'delivered',ts])).digest('hex');
const count=ts=>Number(pg('select count(*) from prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(event(ts))));
const nonce=k=>Number(pg('select count(*) from prumo_private.meta_wa48_shadow_nonces_fixture_s0 where key_id='+q(k.id)));
const snapshot=ts=>pg("select id::text||'|'||body_sha256||'|'||provider_status "+
 'from prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(event(ts)));
const raw=ts=>Buffer.from(JSON.stringify({object:'whatsapp_business_account',
 entry:[{id:WABA,changes:[{field:'messages',value:{
 metadata:{phone_number_id:PHONE},statuses:[{
 id:WAMID,status:'delivered',recipient_id:RECIPIENT,timestamp:ts
 }]}}]}]}));
function newKey(){
 const k={id:randomUUID(),secret:randomBytes(48).toString('hex')};
 pg('insert into prumo_private.meta_wa48_shadow_keys_fixture_s0('+
 'key_id,app,secret,active,valid_from,valid_until) values('+
 q(k.id)+','+q(APP)+',decode('+q(k.secret)+
 ",'hex'),true,clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '2 hours')");
 return k;
}
async function wait(check,what){
 const until=Date.now()+4500;
 while(Date.now()<until){const v=await check();if(v)return v;await sleep(20);}
 assert.fail('WA62_WAIT_TIMEOUT '+what);
}
async function worker(k,mode='normal'){
 const exe=join(dirname(fileURLToPath(import.meta.url)),'s0_wa_064_pg17_restart_worker.mjs');
 const child=spawn(process.execPath,[exe],{
  env:{...process.env,WA60_CLIENT_PASS:PASS,WA60_KEY_ID:k.id,
   WA60_KEY_SECRET:k.secret,WA60_CRASH_MODE:mode,WA61_BINDING_PROFILE:'current'},
  stdio:['pipe','pipe','pipe']});
 const x={child,key:k,ready:null,held:null,receipts:[],stderr:''};
 actors.push(x);
 let buffer='';
 child.stdout.on('data',d=>{
  buffer+=String(d);
  for(;;){
   const at=buffer.indexOf('\n');if(at<0)break;
   const line=buffer.slice(0,at);buffer=buffer.slice(at+1);
   try{const msg=JSON.parse(line);
    if(msg.type==='ready')x.ready=msg;
    else if(msg.type==='wa62-held')x.held=msg;
    else if(msg.type==='receipt')x.receipts.push(msg);
   }catch{x.stderr+='BAD_STDOUT '+line.slice(0,60);}
  }
 });
 child.stderr.on('data',d=>x.stderr+=String(d).slice(-250));
 await wait(()=>x.ready||child.exitCode!==null||child.signalCode!==null,'worker start');
 assert.ok(x.ready,x.stderr);assert.equal(x.ready.host,'127.0.0.1');
 assert.equal(x.ready.lab_only,true);
 return x;
}
async function stop(x){
 assert.equal(x.child.exitCode,null);
 x.child.stdin.write('STOP\n');
 await wait(()=>x.child.exitCode!==null||x.child.signalCode!==null,'worker stop');
 assert.equal(x.child.exitCode,0,x.stderr);
}
function send(x,ts){
 const bytes=raw(ts);
 return new Promise(resolve=>{
  const req=http.request({host:'127.0.0.1',port:x.ready.port,path:x.ready.route,
   method:'POST',agent:false,headers:{
    'Content-Type':'application/json','Content-Length':String(bytes.length),
    'X-Hub-Signature-256':'sha256='+createHmac('sha256',META).update(bytes).digest('hex')
   }},res=>{
    const chunks=[];
    res.on('data',d=>chunks.push(d));
    res.on('end',()=>{
     try{resolve({status:res.statusCode,body:JSON.parse(Buffer.concat(chunks).toString())});}
     catch{resolve({status:res.statusCode,broken:true});}
    });
   });
  req.on('error',e=>resolve({broken:true,error:String(e.code??e.message)}));
  req.setTimeout(6800,()=>req.destroy(Error('WA62_HTTP_TIMEOUT')));
  req.end(bytes);
 });
}
const safety=r=>{
 assert.equal(r.body?.meta_ack_emitted,false);
 assert.equal(r.body?.ack_allowed,false);
 assert.equal(r.body?.send_authorized,false);
};
const accepted=r=>{assert.equal(r.status,202,JSON.stringify(r));safety(r);};
const denied=r=>{assert.equal(r.status,403,JSON.stringify(r));safety(r);};
const revoke=k=>'select prumo_private.meta_wa48_shadow_revoke_fixture_s0('+q(k.id)+')';
function revokeAsync(k){
 const child=spawnPG(revoke(k));actors.push(child);
 let stdout='',stderr='';
 child.stdout.on('data',d=>stdout+=d);
 child.stderr.on('data',d=>stderr+=d);
 const result=new Promise((resolve,reject)=>{
  child.on('error',reject);child.on('close',code=>resolve({code,stdout:stdout.trim(),stderr}));
 });
 return {child,result};
}
async function holdAdminRevoke(k){
 const child=spawn('psql',['-X','-qAt','-v','ON_ERROR_STOP=1','-v',
  'VERBOSITY=verbose',DSN],{
   env:{...process.env,PGPASSWORD:'postgres'},stdio:['pipe','pipe','pipe']});
 actors.push(child);
 const x={child,pid:null,output:'',stderr:''};
 child.stdout.on('data',d=>{
  x.output+=d;
  const m=/([0-9]+)\|WA62_ADMIN_HELD/.exec(x.output);
  if(m)x.pid=Number(m[1]);
 });
 child.stderr.on('data',d=>x.stderr+=d);
 const lock="pg_catalog.hashtextextended('wa48-key:'||"+q(k.id)+"::text,48)";
 child.stdin.write('BEGIN;\nSELECT pg_catalog.pg_advisory_xact_lock('+lock+');\n'+
  revoke(k)+";\nSELECT pg_catalog.pg_backend_pid()::text||'|WA62_ADMIN_HELD';\n");
 await wait(()=>x.pid!==null||child.exitCode!==null,'admin hold');
 assert.ok(x.pid,'admin hold failed: '+x.stderr);
 assert.match(x.output,/LAB_REVOKED/);
 return x;
}
async function adminCommit(x){
 x.child.stdin.write('COMMIT;\n\\q\n');
 await wait(()=>x.child.exitCode!==null||x.child.signalCode!==null,'admin commit');
 assert.equal(x.child.exitCode,0,x.stderr);
}
function blockedBy(blocker,needle){
 const query="select count(*) from pg_catalog.pg_stat_activity where "+
  "datname='prumo_s0_test_ci' and wait_event_type='Lock' and "+
  "query like "+q('%'+needle+'%')+
  " and "+Number(blocker)+"=any(pg_catalog.pg_blocking_pids(pid))";
 return Number(pg(query))>0;
}
let k1,k2,k3,A,B,C,D,E,h,r2,r3,p1,p2,p3,held2,held3;
let finished1=false,finished2=false,finished3=false,baseline,prior;
const cases=[
 async()=>{
  assert.equal(pg('select current_database()'),'prumo_s0_test_ci');
  // WA61 runs immediately before WA62 and deliberately persists cancellation.
  assert.equal(pg("select estado from prumo_private.outbox_intencoes_s0 where id='f7400000-0000-4000-8000-000000000002'"),'CANCELADA');
  pg('alter role prumo_s0_meta_wa48_client_lab login password '+q(PASS));
  for(const ts of TS)assert.equal(count(ts),0);
  baseline=Number(pg('select count(*) from prumo_private.meta_status_forense_fixture_s0'));
 },
 async()=>{k1=newKey();A=await worker(k1);h=await holdAdminRevoke(k1);},
 async()=>{
  p1=send(A,TS[0]).then(v=>{finished1=true;return v;});
  await wait(()=>blockedBy(h.pid,'meta_wa55_single_entry_fixture_s0'),'append blocked by revocation');
 },
 async()=>{
  assert.equal(finished1,false);assert.equal(count(TS[0]),0);assert.equal(nonce(k1),0);
  assert.equal(pg('select active::text from prumo_private.meta_wa48_shadow_keys_fixture_s0 where key_id='+q(k1.id)),'true');
 },
 async()=>{await adminCommit(h);assert.equal(pg('select active::text from prumo_private.meta_wa48_shadow_keys_fixture_s0 where key_id='+q(k1.id)),'false');},
 async()=>{denied(await p1);assert.equal(count(TS[0]),0);assert.equal(nonce(k1),0);},
 async()=>{await stop(A);B=await worker(k1);denied(await send(B,TS[0]));await stop(B);assert.equal(count(TS[0]),0);},
 async()=>{k2=newKey();C=await worker(k2,'holdcommit');p2=send(C,TS[1]).then(v=>{finished2=true;return v;});},
 async()=>{
  held2=await wait(()=>C.held,'append held before COMMIT');
  assert.equal(held2.event,event(TS[1]));
  assert.equal(held2.outcome,'LAB_LATE_UNVERIFIED');
  assert.ok(Number.isInteger(held2.db_pid));
 },
 async()=>{assert.equal(count(TS[1]),0);assert.equal(nonce(k2),0);assert.equal(finished2,false);},
 async()=>{r2=revokeAsync(k2);await wait(()=>blockedBy(held2.db_pid,'meta_wa48_shadow_revoke_fixture_s0'),'revoke blocked by append');},
 async()=>{
  assert.equal(r2.child.exitCode,null);assert.equal(finished2,false);
  assert.equal(count(TS[1]),0);
  assert.equal(pg('select active::text from prumo_private.meta_wa48_shadow_keys_fixture_s0 where key_id='+q(k2.id)),'true');
 },
 async()=>{C.child.stdin.write('COMMIT\n');accepted(await p2);assert.equal(count(TS[1]),1);prior=snapshot(TS[1]);assert.ok(prior.includes('|delivered'));},
 async()=>{
  const x=await r2.result;assert.equal(x.code,0,x.stderr);assert.equal(x.stdout,'LAB_REVOKED');
  assert.equal(pg('select active::text from prumo_private.meta_wa48_shadow_keys_fixture_s0 where key_id='+q(k2.id)),'false');
 },
 async()=>{await stop(C);D=await worker(k2);denied(await send(D,TS[1]));assert.equal(snapshot(TS[1]),prior);assert.equal(nonce(k2),1);await stop(D);},
 async()=>{k3=newKey();E=await worker(k3,'holdrollback');p3=send(E,TS[2]).then(v=>{finished3=true;return v;});},
 async()=>{
  held3=await wait(()=>E.held,'append held before ROLLBACK');
  assert.equal(held3.event,event(TS[2]));assert.equal(count(TS[2]),0);assert.equal(nonce(k3),0);
 },
 async()=>{r3=revokeAsync(k3);await wait(()=>blockedBy(held3.db_pid,'meta_wa48_shadow_revoke_fixture_s0'),'revoke blocked until rollback');assert.equal(finished3,false);},
 async()=>{
  E.child.stdin.write('ROLLBACK\n');denied(await p3);
  const x=await r3.result;assert.equal(x.code,0,x.stderr);assert.equal(x.stdout,'LAB_REVOKED');
  assert.equal(count(TS[2]),0);assert.equal(nonce(k3),0);
 },
 async()=>{
  await stop(E);
  assert.equal(Number(pg('select count(*) from prumo_private.meta_status_forense_fixture_s0')),baseline+1);
  assert.equal(snapshot(TS[1]),prior);
  for(const k of [k1,k2,k3])assert.equal(pg('select active::text from prumo_private.meta_wa48_shadow_keys_fixture_s0 where key_id='+q(k.id)),'false');
  assert.equal(Number(pg('select count(*) from prumo_private.meta_wa48_shadow_receipts_fixture_s0 where key_id in ('+[k1,k2,k3].map(k=>q(k.id)).join(',')+')')),0);
  assert.equal(Number(pg('select count(*) from prumo_private.meta_status_forense_fixture_s0 where ack_allowed or send_authorized or retry_external or production_authorized or delivery_confirmed or case_transition_authorized or definitive_failure_count_increment')),0);
  assert.equal(pg("select has_function_privilege('prumo_s0_meta_wa48_client_lab',"+
   q('prumo_private.meta_wa52_locked_forensic_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)')+
   ",'EXECUTE')"),'f');
 }
];
assert.equal(cases.length,20);
for(let i=0;i<cases.length;i++)
 test('WA62-'+String(i+1).padStart(2,'0')+' key/revoke PG17 race',async()=>{
  await cases[i]();console.log('WA62-'+String(i+1).padStart(2,'0')+' PASS');
 });
