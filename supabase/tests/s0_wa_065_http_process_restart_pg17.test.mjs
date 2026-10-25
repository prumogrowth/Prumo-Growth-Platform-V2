/** WA60: 24 proofs of cross-PID persistence, clean restart and crash windows.
 * Separate Node processes, one shared disposable PG17, NO public network.
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
 url.search||url.hash)throw Error('WA60_TEST_DISPOSABLE_ONLY');
for(const k of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER',
 'PGSERVICE','PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT','PGSSLKEY','PGSSLROOTCERT'])
 if(process.env[k])throw Error('WA60_TEST_LIBPQ_OVERRIDE');
const PASSWORD=randomBytes(32).toString('hex');
const R={app:'12346000002',waba:'22346000002',phone:'32346000002',
 wamid:'wamid.WA40.SHARED',recipient:'5581900000000'};
const META=Buffer.alloc(48,0x4d);
const NOW=Math.floor(Date.now()/1000);
const TS=[1,2,3,4,5].map(i=>String(NOW-720000-i));
const event=ts=>'WA46_'+createHash('sha256').update(JSON.stringify([
 R.waba,R.phone,R.wamid,R.recipient,'delivered',ts])).digest('hex');
const body=ts=>Buffer.from(JSON.stringify({object:'whatsapp_business_account',
 entry:[{id:R.waba,changes:[{field:'messages',value:{
  metadata:{phone_number_id:R.phone},statuses:[{
   id:R.wamid,status:'delivered',recipient_id:R.recipient,timestamp:ts
  }]}}]}]}));
const q=v=>"'"+String(v).replaceAll("'","''")+"'";
const all=[];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
after(()=>{for(const v of all){if(v.child.exitCode===null&&v.child.signalCode===null)v.child.kill('SIGKILL');}});
function pg(statement){
 const p=spawnSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1','-v',
 'VERBOSITY=verbose',DSN,'-c',statement],{encoding:'utf8',timeout:12000,
 env:{...process.env,PGPASSWORD:'postgres'}});
 if(p.error||p.status!==0)throw Error('WA60_PG '+String(p.stderr).slice(-650));
 return p.stdout.trim();
}
function count(ts){return Number(pg('select count(*) from prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(event(ts))));}
async function worker(mode='normal'){
 const id=randomUUID(),secret=randomBytes(48);
 pg('insert into prumo_private.meta_wa48_shadow_keys_fixture_s0('+
  'key_id,app,secret,active,valid_from,valid_until) values ('+
  q(id)+','+q(R.app)+',decode('+q(secret.toString('hex'))+
  ",'hex'),true,clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '2 hours')");
 const exe=join(dirname(fileURLToPath(import.meta.url)),'s0_wa_064_pg17_restart_worker.mjs');
 const child=spawn(process.execPath,[exe],{env:{
  ...process.env,WA60_CLIENT_PASS:PASSWORD,WA60_KEY_ID:id,
  WA60_KEY_SECRET:secret.toString('hex'),WA60_CRASH_MODE:mode
 },stdio:['pipe','pipe','pipe']});
 const obj={child,mode,keyId:id,receipts:[],address:null,stderr:''};
 all.push(obj);
 let raw='';
 child.stdout.setEncoding('utf8');
 child.stdout.on('data',data=>{
  raw+=data;
  for(;;){
   const i=raw.indexOf('\n');if(i<0)break;
   const line=raw.slice(0,i);raw=raw.slice(i+1);
   try{
    const msg=JSON.parse(line);
    if(msg.type==='receipt')obj.receipts.push(msg);
    else if(msg.type==='ready')obj.address=msg;
   }catch{obj.stderr+='BAD_STDOUT:'+line.slice(0,70);}
  }
 });
 child.stderr.on('data',buf=>obj.stderr+=String(buf).slice(-300));
 const start=Date.now();
 while(!obj.address&&child.exitCode===null&&child.signalCode===null&&Date.now()-start<3000)await sleep(15);
 if(!obj.address){child.kill('SIGKILL');throw Error('WA60_START_FAILED '+obj.stderr.slice(-500));}
 assert.equal(obj.address.host,'127.0.0.1');
 assert.equal(obj.address.pid,child.pid);
 assert.equal(obj.address.lab_only,true);
 return obj;
}
async function waitExit(obj){
 const c=obj.child;
 const until=Date.now()+3500;
 while(c.exitCode===null&&c.signalCode===null&&Date.now()<until)await sleep(15);
 if(c.exitCode===null&&c.signalCode===null){c.kill('SIGKILL');throw Error('WA60_WORKER_EXIT_TIMEOUT');}
 return {code:c.exitCode,signal:c.signalCode};
}
async function stop(obj){
 assert.equal(obj.child.exitCode,null);
 obj.child.stdin.write('STOP\n');
 const res=await waitExit(obj);
 assert.equal(res.code,0,'WA60 nonzero stop '+obj.stderr.slice(-220));
}
async function send(obj,ts,badMac=false){
 const raw=body(ts);
 const sig='sha256='+(badMac?'0'.repeat(64):
  createHmac('sha256',META).update(raw).digest('hex'));
 return new Promise(resolve=>{
  const req=http.request({host:'127.0.0.1',port:obj.address.port,
   path:obj.address.route,method:'POST',agent:false,headers:{
    'Content-Type':'application/json','Content-Length':String(raw.length),
    'X-Hub-Signature-256':sig}},res=>{
     const out=[];
     res.on('data',b=>out.push(b));
     res.on('end',()=>{
      try{resolve({status:res.statusCode,body:JSON.parse(Buffer.concat(out).toString('utf8'))});}
      catch{resolve({broken:true,code:'BODY_INVALID'});}
     });
   });
  req.on('error',e=>resolve({broken:true,code:e.code??e.message}));
  req.setTimeout(5500,()=>req.destroy(Error('WA60_HTTP_TIMEOUT')));
  req.end(raw);
 });
}
function good(result){
 assert.equal(result.status,202,JSON.stringify(result));
 assert.equal(result.body?.decision,'LAB_HTTP_FORENSIC_STORED_ONLY');
 assert.equal(result.body?.lab_only,true);
 assert.equal(result.body?.meta_ack_emitted,false);
 assert.equal(result.body?.ack_allowed,false);
 assert.equal(result.body?.send_authorized,false);
}
async function waitReceipt(obj,ts,outcome){
 const end=Date.now()+1300;
 while(Date.now()<end){
  if(obj.receipts.some(x=>x.event===event(ts)&&x.outcome===outcome))return;
  await sleep(12);
 }
 assert.fail('WA60 missing receipt '+outcome+' '+JSON.stringify(obj.receipts));
}

let A,B,C,D,E,F,G,H;
const cases=[
 async()=>{assert.equal(pg('select current_database()'),'prumo_s0_test_ci');
  pg('alter role prumo_s0_meta_wa48_client_lab login password '+q(PASSWORD));
  for(const ts of TS)assert.equal(count(ts),0);},
 async()=>{A=await worker();assert.equal(A.mode,'normal');},
 async()=>{good(await send(A,TS[0]));await waitReceipt(A,TS[0],'LAB_OBSERVED_UNVERIFIED');},
 async()=>{assert.equal(count(TS[0]),1);},
 async()=>{good(await send(A,TS[0]));await waitReceipt(A,TS[0],'LAB_EXACT_BODY_REPLAY');},
 async()=>{assert.equal(count(TS[0]),1);},
 async()=>{await stop(A);assert.equal(A.child.exitCode,0);},
 async()=>{B=await worker();assert.notEqual(B.child.pid,A.child.pid);assert.notEqual(B.keyId,A.keyId);},
 async()=>{good(await send(B,TS[0]));await waitReceipt(B,TS[0],'LAB_EXACT_BODY_REPLAY');},
 async()=>{assert.equal(count(TS[0]),1);},
 async()=>{good(await send(B,TS[1]));await waitReceipt(B,TS[1],'LAB_OBSERVED_UNVERIFIED');},
 async()=>{assert.equal(count(TS[1]),1);await stop(B);},
 async()=>{C=await worker('precommit');const x=await send(C,TS[2]);
  assert.equal(x.broken,true);const e=await waitExit(C);assert.equal(e.signal,'SIGKILL');},
 async()=>{assert.equal(count(TS[2]),0);},
 async()=>{D=await worker();good(await send(D,TS[2]));await waitReceipt(D,TS[2],'LAB_OBSERVED_UNVERIFIED');},
 async()=>{assert.equal(count(TS[2]),1);await stop(D);},
 async()=>{E=await worker('postcommit');const x=await send(E,TS[3]);
  assert.equal(x.broken,true);const e=await waitExit(E);assert.equal(e.signal,'SIGKILL');},
 async()=>{assert.equal(count(TS[3]),1);},
 async()=>{F=await worker();good(await send(F,TS[3]));await waitReceipt(F,TS[3],'LAB_EXACT_BODY_REPLAY');},
 async()=>{assert.equal(count(TS[3]),1);},
 async()=>{G=await worker();H=await worker();assert.notEqual(G.child.pid,H.child.pid);
  assert.notEqual(G.keyId,H.keyId);},
 async()=>{const replies=await Promise.all([send(G,TS[4]),send(H,TS[4])]);replies.forEach(good);
  assert.equal(count(TS[4]),1);},
 async()=>{await sleep(45);const a=[...G.receipts,...H.receipts].filter(x=>x.event===event(TS[4]))
   .map(x=>x.outcome).sort();
  assert.deepEqual(a,['LAB_EXACT_BODY_REPLAY','LAB_OBSERVED_UNVERIFIED'].sort());},
 async()=>{const before=count(TS[4]),fail=await send(F,TS[4],true);
  assert.equal(fail.status,403);assert.equal(fail.body?.meta_ack_emitted,false);
  assert.equal(count(TS[4]),before);
  assert.equal(pg('select count(*) from prumo_private.meta_wa48_shadow_receipts_fixture_s0 where key_id in ('+all.map(x=>q(x.keyId)).join(',')+')'), '0');
  assert.equal(pg("select has_function_privilege('prumo_s0_meta_wa48_client_lab',"+
   q('prumo_private.meta_wa52_locked_forensic_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)')+
   ",'EXECUTE')"),'f');
  await Promise.all([stop(F),stop(G),stop(H)]);
  assert.equal(pg('select count(*) from prumo_private.meta_status_forense_fixture_s0 where ack_allowed or send_authorized or retry_external or production_authorized or delivery_confirmed or case_transition_authorized'),'0');}
];
assert.equal(cases.length,24);
for(let i=0;i<cases.length;i++)
 test('WA60-'+String(i+1).padStart(2,'0')+' restart/durable PG17 replay',async()=>{
  await cases[i]();
  console.log('WA60-'+String(i+1).padStart(2,'0')+' PASS');
 });
