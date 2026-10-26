/** WA64 — 24 PG17 lab-only checks: two different signed event refs per
 * authoritative S0 intent under cancellation / per-key revocation.
 * This file never accesses a hosted DB, Meta Graph or the S1 product.
 */
import test,{after} from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import {spawn,spawnSync} from 'node:child_process';
import {createHash,createHmac,randomBytes,randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';

const DSN=process.env.PRUMO_TEST_DATABASE_URL??'',url=new URL(DSN);
if(url.protocol!=='postgresql:'||url.hostname!=='127.0.0.1'||url.port!=='5432'||
 url.username!=='postgres'||url.pathname!=='/prumo_s0_test_ci'||
 url.search||url.hash)throw Error('WA64_LOCAL_PG17_ONLY');
for(const k of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER','PGSERVICE',
 'PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT','PGSSLKEY','PGSSLROOTCERT'])
 if(process.env[k])throw Error('WA64_PG_ENV_OVERRIDE');

const PASS=randomBytes(32).toString('hex'),META=Buffer.alloc(48,0x4d);
const APP='12346000002',WABA='22346000002',PHONE='32346000002';
const SHOP='f7200000-0000-4000-8000-000000000002';
const CHANNEL='f7300000-0000-4000-8000-000000000002';
const RECIPIENT='5581900000000',TS=Array.from({length:8},(_,i)=>
 String(Math.floor(Date.now()/1000)-2600000-i*31));
const S=[
 {id:'f7400000-0000-4000-8000-000000000066',profile:'wa64-a',
  attempt:'ATTEMPT_WA64_A',corr:'CORR_WA64_A',wamid:'wamid.WA64.A'},
 {id:'f7400000-0000-4000-8000-000000000067',profile:'wa64-b',
  attempt:'ATTEMPT_WA64_B',corr:'CORR_WA64_B',wamid:'wamid.WA64.B'},
 {id:'f7400000-0000-4000-8000-000000000068',profile:'wa64-c',
  attempt:'ATTEMPT_WA64_C',corr:'CORR_WA64_C',wamid:'wamid.WA64.C'}
];
const q=v=>"'"+String(v).replaceAll("'","''")+"'";
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const children=[];
after(()=>{for(const a of children){
 const c=a.child??a;if(c.exitCode===null&&c.signalCode===null)c.kill('SIGKILL');
}});
function pg(sql){
 const x=spawnSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1','-v',
  'VERBOSITY=verbose',DSN,'-c',sql],{
  encoding:'utf8',timeout:12000,env:{...process.env,PGPASSWORD:'postgres'}});
 if(x.error||x.status!==0)throw Error('WA64_PSQL '+String(x.stderr).slice(-500));
 return x.stdout.trim();
}
const num=table=>Number(pg('select count(*) from '+table));
const state=s=>pg('select estado from prumo_private.outbox_intencoes_s0 where id='+q(s.id));
const active=k=>pg('select active::text from prumo_private.meta_wa48_shadow_keys_fixture_s0 where key_id='+q(k.id));
const nonce=k=>num('prumo_private.meta_wa48_shadow_nonces_fixture_s0 where key_id='+q(k.id));
const ev=(s,ts)=>'WA46_'+createHash('sha256').update(JSON.stringify([
 WABA,PHONE,s.wamid,RECIPIENT,'delivered',ts])).digest('hex');
const count=(s,ts)=>num('prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(ev(s,ts)));
const snapshot=(s,ts)=>pg("select id::text||'|'||body_sha256||'|'||provider_status "+
 'from prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(ev(s,ts)));
async function wait(fn,tag,ms=6500){
 const end=Date.now()+ms;
 while(Date.now()<end){const v=await fn();if(v)return v;await sleep(20);}
 assert.fail('WA64_WAIT_TIMEOUT '+tag);
}
function launchSQL(query){
 const c=spawn('psql',['-X','-qAt','-v','ON_ERROR_STOP=1','-v',
  'VERBOSITY=verbose',DSN,'-c',query],{
   env:{...process.env,PGPASSWORD:'postgres'},stdio:['ignore','pipe','pipe']});
 children.push(c);
 let out='',err='';
 c.stdout.on('data',d=>out+=String(d));
 c.stderr.on('data',d=>err+=String(d));
 const result=new Promise((resolve,reject)=>{
  c.on('error',reject);
  c.on('close',code=>resolve({code,out:out.trim(),err}));
 });
 return {child:c,result};
}
function cancel(s){return "update prumo_private.outbox_intencoes_s0 set estado='CANCELADA' "+
 'where id='+q(s.id)+" and estado='BLOQUEADA_GATES' returning estado";}
const revoke=k=>'select prumo_private.meta_wa48_shadow_revoke_fixture_s0('+q(k.id)+')';
function blockers(pids,queryPart){
 const statement="select pid::text from pg_catalog.pg_stat_activity "+
  "where datname='prumo_s0_test_ci' and wait_event_type='Lock' "+
  "and query like "+q('%'+queryPart+'%')+
  " and pg_catalog.array_length(pg_catalog.pg_blocking_pids(pid),1)>0 "+
  "and (pg_catalog.pg_blocking_pids(pid) && ARRAY["+
  pids.map(n=>String(Number(n))).join(',')+"]::integer[]) limit 1";
 const x=pg(statement);
 return /^\d+$/.test(x)?Number(x):null;
}
function key(){
 const k={id:randomUUID(),secret:randomBytes(48).toString('hex')};
 pg('insert into prumo_private.meta_wa48_shadow_keys_fixture_s0('+
  'key_id,app,secret,active,valid_from,valid_until) values('+
  q(k.id)+','+q(APP)+',decode('+q(k.secret)+
  ",'hex'),true,clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '2 hours')");
 return k;
}
const raw=(s,ts)=>Buffer.from(JSON.stringify({object:'whatsapp_business_account',
 entry:[{id:WABA,changes:[{field:'messages',value:{
  metadata:{phone_number_id:PHONE},statuses:[{
   id:s.wamid,status:'delivered',recipient_id:RECIPIENT,timestamp:ts
  }]}}]}]}));
async function worker(k,s,mode='normal'){
 const file=join(dirname(fileURLToPath(import.meta.url)),'s0_wa_064_pg17_restart_worker.mjs');
 const c=spawn(process.execPath,[file],{
  env:{...process.env,WA60_CLIENT_PASS:PASS,WA60_KEY_ID:k.id,
   WA60_KEY_SECRET:k.secret,WA60_CRASH_MODE:mode,
   WA61_BINDING_PROFILE:s.profile},stdio:['pipe','pipe','pipe']});
 children.push(c);
 const w={child:c,ready:null,held:null,receipts:[],err:''};
 let rest='';
 c.stdout.on('data',b=>{
  rest+=String(b);
  for(;;){
   const i=rest.indexOf('\n');if(i<0)break;
   const row=rest.slice(0,i);rest=rest.slice(i+1);
   try{const msg=JSON.parse(row);
    if(msg.type==='ready')w.ready=msg;
    if(msg.type==='wa62-held')w.held=msg;
    if(msg.type==='receipt')w.receipts.push(msg);
   }catch{w.err+='bad stdout '+row.slice(0,55);}
  }
 });
 c.stderr.on('data',b=>w.err+=String(b).slice(-200));
 await wait(()=>w.ready||c.exitCode!==null||c.signalCode!==null,'worker');
 assert.ok(w.ready,w.err);
 assert.equal(w.ready.host,'127.0.0.1');
 assert.equal(w.ready.lab_only,true);
 return w;
}
async function stop(w){
 assert.equal(w.child.exitCode,null,'worker exited unexpectedly '+w.err);
 w.child.stdin.write('STOP\n');
 await wait(()=>w.child.exitCode!==null||w.child.signalCode!==null,'worker stop');
 assert.equal(w.child.exitCode,0,w.err);
}
function send(w,s,ts){
 const bytes=raw(s,ts);
 return new Promise(resolve=>{
  const req=http.request({host:'127.0.0.1',port:w.ready.port,path:w.ready.route,
   method:'POST',agent:false,headers:{
    'Content-Type':'application/json','Content-Length':String(bytes.length),
    'X-Hub-Signature-256':'sha256='+createHmac('sha256',META).update(bytes).digest('hex')
   }},res=>{
    const parts=[];
    res.on('data',b=>parts.push(b));
    res.on('end',()=>{
     try{resolve({code:res.statusCode,body:JSON.parse(Buffer.concat(parts).toString())});}
     catch{resolve({code:res.statusCode,unreadable:true});}
    });
   });
  req.on('error',e=>resolve({broken:true,error:String(e.code??e.message)}));
  req.setTimeout(9000,()=>req.destroy(Error('WA64_HTTP_TIMEOUT')));
  req.end(bytes);
 });
}
function safe(v){
 assert.equal(v.body?.lab_only,true);assert.equal(v.body?.ack_allowed,false);
 assert.equal(v.body?.meta_ack_emitted,false);
 assert.equal(v.body?.send_authorized,false);
}
function accepted(v){assert.equal(v.code,202,JSON.stringify(v));safe(v);}
function denied(v){assert.equal(v.code,403,JSON.stringify(v));safe(v);}
async function requireReceipt(w,s,ts,result){
 await wait(()=>w.receipts.some(x=>x.event===ev(s,ts)&&x.outcome===result),
  'receipt '+result);
}
async function assertAdmin(call,expected){
 const r=await call.result;assert.equal(r.code,0,r.err);assert.equal(r.out,expected);
}

let baseline,ka1,ka2,ka3,kb1,kb2,kb3,kc1,kc2,kc3;
let A1,A2,A3,B1,B2,B3,B4,C1,C2,C3,C4;
let aP1,aP2,bP1,bP2,cP1,cP2,ha1,ha2,hb1,hb2,hcCancel;
let aCancel,ar1,ar2,bCancel,br1,br2,cr1;
let aOld1,aOld2,bOld2,cOld2,doneC1=false,doneC2=false;
const tests=[
 // Setup authentic synthetic S0 bind for all three independent intents.
 async()=>{
  assert.equal(pg('select current_database()'),'prumo_s0_test_ci');
  assert.equal(state({id:'f7400000-0000-4000-8000-000000000002'}),'CANCELADA');
  pg('alter role prumo_s0_meta_wa48_client_lab login password '+q(PASS));
  baseline=num('prumo_private.meta_status_forense_fixture_s0');
  for(let i=0;i<3;i++){
   const s=S[i];
   assert.equal(num('prumo_private.outbox_intencoes_s0 where id='+q(s.id)),0);
   pg('insert into prumo_private.outbox_intencoes_s0('+
    'id,concessionaria_id,canal_id,contrato,chave_idempotencia,versao_estado_sintetica) '+
    'values('+[s.id,SHOP,CHANNEL,'C03','WA64_DUAL_'+i,1].map(q).join(',')+')');
   const out=JSON.parse(pg('select prumo_private.registrar_vinculo_meta_tecnico_fixture_s0('+
    [APP,WABA,PHONE,CHANNEL,s.id,s.attempt,s.corr,RECIPIENT,s.wamid,200]
    .map((v,j)=>j===9?'200':q(v)).join(',')+')'));
   assert.equal(out.outcome,'LAB_BOUND');
   assert.equal(state(s),'BLOQUEADA_GATES');
  }
  for(const [s,ts] of [[S[0],TS[0]],[S[0],TS[1]],[S[1],TS[2]],
   [S[1],TS[3]],[S[2],TS[4]],[S[2],TS[5]]])assert.equal(count(s,ts),0);
 },
 // A: two distinct events, two independent keys and transaction holders.
 async()=>{
  ka1=key();ka2=key();
  A1=await worker(ka1,S[0],'holdcommit');
  A2=await worker(ka2,S[0],'holdcommit');
  aP1=send(A1,S[0],TS[0]);aP2=send(A2,S[0],TS[1]);
  ha1=await wait(()=>A1.held,'A event1 held');ha2=await wait(()=>A2.held,'A event2 held');
  assert.notEqual(ha1.db_pid,ha2.db_pid);
  assert.equal(ha1.outcome,'LAB_OBSERVED_UNVERIFIED');
  assert.equal(ha2.outcome,'LAB_OBSERVED_UNVERIFIED');
 },
 async()=>{
  assert.equal(state(S[0]),'BLOQUEADA_GATES');
  assert.equal(count(S[0],TS[0]),0);assert.equal(count(S[0],TS[1]),0);
  assert.equal(nonce(ka1),0);assert.equal(nonce(ka2),0);
 },
 async()=>{
  aCancel=launchSQL(cancel(S[0]));
  await wait(()=>blockers([ha1.db_pid,ha2.db_pid],'update prumo_private.outbox_intencoes_s0'),
   'A cancel waiting on event holders');
  ar1=launchSQL(revoke(ka1));ar2=launchSQL(revoke(ka2));
  await wait(()=>blockers([ha1.db_pid],'meta_wa48_shadow_revoke_fixture_s0'),
   'A revoke key1 waiting');
  await wait(()=>blockers([ha2.db_pid],'meta_wa48_shadow_revoke_fixture_s0'),
   'A revoke key2 waiting');
 },
 async()=>{
  assert.equal(state(S[0]),'BLOQUEADA_GATES');
  assert.equal(active(ka1),'true');assert.equal(active(ka2),'true');
  assert.equal(aCancel.child.exitCode,null);
  assert.equal(ar1.child.exitCode,null);assert.equal(ar2.child.exitCode,null);
 },
 async()=>{
  A1.child.stdin.write('COMMIT\n');
  accepted(await aP1);await requireReceipt(A1,S[0],TS[0],'LAB_OBSERVED_UNVERIFIED');
  await assertAdmin(ar1,'LAB_REVOKED');
  await wait(()=>blockers([ha2.db_pid],'update prumo_private.outbox_intencoes_s0'),
   'A second append still blocks cancellation');
  assert.equal(state(S[0]),'BLOQUEADA_GATES');
  assert.equal(count(S[0],TS[0]),1);assert.equal(count(S[0],TS[1]),0);
  assert.equal(nonce(ka1),1);assert.equal(nonce(ka2),0);
 },
 async()=>{
  A2.child.stdin.write('COMMIT\n');
  accepted(await aP2);await requireReceipt(A2,S[0],TS[1],'LAB_OBSERVED_UNVERIFIED');
  await assertAdmin(ar2,'LAB_REVOKED');await assertAdmin(aCancel,'CANCELADA');
  assert.equal(state(S[0]),'CANCELADA');
  assert.equal(active(ka1),'false');assert.equal(active(ka2),'false');
 },
 async()=>{
  aOld1=snapshot(S[0],TS[0]);aOld2=snapshot(S[0],TS[1]);
  assert.match(aOld1,/\|delivered$/);assert.match(aOld2,/\|delivered$/);
  assert.equal(count(S[0],TS[0]),1);assert.equal(count(S[0],TS[1]),1);
  assert.equal(nonce(ka1),1);assert.equal(nonce(ka2),1);
  await stop(A1);await stop(A2);
  A3=await worker(ka1,S[0]);
  denied(await send(A3,S[0],TS[0]));denied(await send(A3,S[0],TS[1]));
  await stop(A3);
 },
 // B: same intent, one committed event, a second rolled back.
 async()=>{
  kb1=key();kb2=key();
  B1=await worker(kb1,S[1],'holdrollback');
  B2=await worker(kb2,S[1],'holdcommit');
  bP1=send(B1,S[1],TS[2]);bP2=send(B2,S[1],TS[3]);
  hb1=await wait(()=>B1.held,'B rollback event held');
  hb2=await wait(()=>B2.held,'B commit event held');
  assert.notEqual(hb1.db_pid,hb2.db_pid);
  assert.equal(hb1.outcome,'LAB_OBSERVED_UNVERIFIED');
  assert.equal(hb2.outcome,'LAB_OBSERVED_UNVERIFIED');
 },
 async()=>{
  bCancel=launchSQL(cancel(S[1]));
  await wait(()=>blockers([hb1.db_pid,hb2.db_pid],'update prumo_private.outbox_intencoes_s0'),
   'B cancellation blocked');
  br1=launchSQL(revoke(kb1));br2=launchSQL(revoke(kb2));
  await wait(()=>blockers([hb1.db_pid],'meta_wa48_shadow_revoke_fixture_s0'),
   'B revoke rollback key blocked');
  await wait(()=>blockers([hb2.db_pid],'meta_wa48_shadow_revoke_fixture_s0'),
   'B revoke commit key blocked');
 },
 async()=>{
  assert.equal(state(S[1]),'BLOQUEADA_GATES');
  assert.equal(count(S[1],TS[2]),0);assert.equal(count(S[1],TS[3]),0);
  assert.equal(nonce(kb1),0);assert.equal(nonce(kb2),0);
 },
 async()=>{
  B1.child.stdin.write('ROLLBACK\n');denied(await bP1);
  await assertAdmin(br1,'LAB_REVOKED');
  await wait(()=>blockers([hb2.db_pid],'update prumo_private.outbox_intencoes_s0'),
   'B cancellation remains blocked by committed candidate');
  assert.equal(count(S[1],TS[2]),0);assert.equal(nonce(kb1),0);
  assert.equal(state(S[1]),'BLOQUEADA_GATES');
 },
 async()=>{
  B2.child.stdin.write('COMMIT\n');accepted(await bP2);
  await requireReceipt(B2,S[1],TS[3],'LAB_OBSERVED_UNVERIFIED');
  await assertAdmin(br2,'LAB_REVOKED');await assertAdmin(bCancel,'CANCELADA');
  assert.equal(state(S[1]),'CANCELADA');
 },
 async()=>{
  assert.equal(count(S[1],TS[2]),0);assert.equal(nonce(kb1),0);
  assert.equal(count(S[1],TS[3]),1);assert.equal(nonce(kb2),1);
  bOld2=snapshot(S[1],TS[3]);
  assert.match(bOld2,/\|delivered$/);
  assert.equal(active(kb1),'false');assert.equal(active(kb2),'false');
 },
 async()=>{
  await stop(B1);await stop(B2);
  B3=await worker(kb1,S[1]);B4=await worker(kb2,S[1]);
  denied(await send(B3,S[1],TS[2]));
  denied(await send(B4,S[1],TS[3]));
  assert.equal(count(S[1],TS[2]),0);assert.equal(count(S[1],TS[3]),1);
  await stop(B3);await stop(B4);
 },
 async()=>{
  kb3=key();const w=await worker(kb3,S[1]);
  accepted(await send(w,S[1],TS[3]));
  await requireReceipt(w,S[1],TS[3],'LAB_EXACT_BODY_REPLAY');
  accepted(await send(w,S[1],TS[2]));
  await requireReceipt(w,S[1],TS[2],'LAB_LATE_UNVERIFIED');
  assert.equal(count(S[1],TS[2]),1);assert.equal(count(S[1],TS[3]),1);
  assert.equal(nonce(kb3),2);
  assert.equal(snapshot(S[1],TS[3]),bOld2);
  await stop(w);
 },
 // C: committed cancellation BEFORE two different concurrent appends;
 // one key is revoked while blocked, the other remains valid.
 async()=>{
  kc1=key();kc2=key();
  C1=await worker(kc1,S[2]);C2=await worker(kc2,S[2]);
  const c=spawn('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
   '-v','VERBOSITY=verbose',DSN],{
   env:{...process.env,PGPASSWORD:'postgres'},stdio:['pipe','pipe','pipe']});
  children.push(c);let output='',err='';
  hcCancel={child:c,pid:null};
  c.stdout.on('data',d=>{output+=String(d);
   const m=/([0-9]+)\|WA64_CANCEL_HELD/.exec(output);
   if(m)hcCancel.pid=Number(m[1]);
  });
  c.stderr.on('data',d=>err+=String(d));
  c.stdin.write('BEGIN;\n'+cancel(S[2])+";\nselect pg_catalog.pg_backend_pid()::text||'|WA64_CANCEL_HELD';\n");
  await wait(()=>hcCancel.pid!==null||c.exitCode!==null,'C cancellation held');
  assert.ok(hcCancel.pid,'C holder failure '+err);
  assert.match(output,/CANCELADA/);
 },
 async()=>{
  cP1=send(C1,S[2],TS[4]).then(v=>{doneC1=true;return v;});
  cP2=send(C2,S[2],TS[5]).then(v=>{doneC2=true;return v;});
  await wait(()=>blockers([hcCancel.pid],'meta_wa55_single_entry_fixture_s0'),
   'C event append blocked by cancellation');
  assert.equal(state(S[2]),'BLOQUEADA_GATES');
  assert.equal(doneC1,false);assert.equal(doneC2,false);
 },
 async()=>{
  cr1=launchSQL(revoke(kc1));await assertAdmin(cr1,'LAB_REVOKED');
  assert.equal(active(kc1),'false');assert.equal(active(kc2),'true');
  assert.equal(nonce(kc1),0);assert.equal(nonce(kc2),0);
  assert.equal(count(S[2],TS[4]),0);assert.equal(count(S[2],TS[5]),0);
 },
 async()=>{
  hcCancel.child.stdin.write('COMMIT;\n\\q\n');
  await wait(()=>hcCancel.child.exitCode!==null||hcCancel.child.signalCode!==null,
   'C cancel commit');
  assert.equal(hcCancel.child.exitCode,0);
  denied(await cP1);accepted(await cP2);
  await requireReceipt(C2,S[2],TS[5],'LAB_LATE_UNVERIFIED');
  assert.equal(state(S[2]),'CANCELADA');
 },
 async()=>{
  assert.equal(count(S[2],TS[4]),0);assert.equal(count(S[2],TS[5]),1);
  assert.equal(nonce(kc1),0);assert.equal(nonce(kc2),1);
  cOld2=snapshot(S[2],TS[5]);
  assert.match(cOld2,/\|delivered$/);
 },
 async()=>{
  const rev=launchSQL(revoke(kc2));await assertAdmin(rev,'LAB_REVOKED');
  await stop(C1);await stop(C2);
  C3=await worker(kc1,S[2]);C4=await worker(kc2,S[2]);
  denied(await send(C3,S[2],TS[4]));denied(await send(C4,S[2],TS[5]));
  await stop(C3);await stop(C4);
  assert.equal(active(kc2),'false');
 },
 async()=>{
  kc3=key();const rotated=await worker(kc3,S[2]);
  accepted(await send(rotated,S[2],TS[5]));
  await requireReceipt(rotated,S[2],TS[5],'LAB_EXACT_BODY_REPLAY');
  accepted(await send(rotated,S[2],TS[4]));
  await requireReceipt(rotated,S[2],TS[4],'LAB_LATE_UNVERIFIED');
  await stop(rotated);
  assert.equal(nonce(kc3),2);
  assert.equal(count(S[2],TS[4]),1);assert.equal(count(S[2],TS[5]),1);
  assert.equal(snapshot(S[2],TS[5]),cOld2);
 },
 async()=>{
  assert.equal(num('prumo_private.meta_status_forense_fixture_s0'),baseline+6);
  for(const s of S)assert.equal(state(s),'CANCELADA');
  for(const k of [ka1,ka2,kb1,kb2,kc1,kc2])assert.equal(active(k),'false');
  for(const [scope,t] of [[S[0],TS[0]],[S[0],TS[1]],[S[1],TS[2]],
   [S[1],TS[3]],[S[2],TS[4]],[S[2],TS[5]]])assert.equal(count(scope,t),1);
  assert.equal(snapshot(S[0],TS[0]),aOld1);
  assert.equal(snapshot(S[0],TS[1]),aOld2);
  assert.equal(snapshot(S[1],TS[3]),bOld2);
  assert.equal(snapshot(S[2],TS[5]),cOld2);
  const ids=[ka1,ka2,kb1,kb2,kb3,kc1,kc2,kc3].map(k=>q(k.id)).join(',');
  assert.equal(num('prumo_private.meta_wa48_shadow_receipts_fixture_s0 where key_id in ('+ids+')'),0);
  assert.equal(num('prumo_private.meta_status_forense_fixture_s0 where ack_allowed or send_authorized or retry_external or production_authorized or delivery_confirmed or case_transition_authorized or definitive_failure_count_increment'),0);
  assert.equal(pg("select has_function_privilege('prumo_s0_meta_wa48_client_lab',"+
   q('prumo_private.meta_wa52_locked_forensic_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)')+
   ",'EXECUTE')"),'f');
 }
];
assert.equal(tests.length,24);
for(let i=0;i<tests.length;i++)
 test('WA64-'+String(i+1).padStart(2,'0')+' dual-event cancel/revoke PG17',async()=>{
  await tests[i]();
  console.log('WA64-'+String(i+1).padStart(2,'0')+' PASS');
 });
