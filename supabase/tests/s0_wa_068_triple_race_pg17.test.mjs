/** WA63 — 24 physical triple races: outbox cancellation, key revoke,
 * signed forensic append. Disposable PG17 + loopback Node only.
 */
import test,{after} from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import {spawn,spawnSync} from 'node:child_process';
import {createHash,createHmac,randomBytes,randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';

const DSN=process.env.PRUMO_TEST_DATABASE_URL??'';
const u=new URL(DSN);
if(u.protocol!=='postgresql:'||u.hostname!=='127.0.0.1'||u.port!=='5432'||
 u.username!=='postgres'||u.pathname!=='/prumo_s0_test_ci'||u.search||u.hash)
 throw Error('WA63_DISPOSABLE_PG17_ONLY');
for(const k of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER','PGSERVICE',
 'PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT','PGSSLKEY','PGSSLROOTCERT'])
 if(process.env[k])throw Error('WA63_LIBPQ_OVERRIDE');

const PASS=randomBytes(32).toString('hex');
const META=Buffer.alloc(48,0x4d);
const APP='12346000002',WABA='22346000002',PHONE='32346000002';
const SHOP='f7200000-0000-4000-8000-000000000002';
const CHANNEL='f7300000-0000-4000-8000-000000000002';
const RECIPIENT='5581900000000';
const S=[
 {id:'f7400000-0000-4000-8000-000000000063',profile:'wa63-a',
  attempt:'ATTEMPT_WA63_A',corr:'CORR_WA63_A',wamid:'wamid.WA63.A'},
 {id:'f7400000-0000-4000-8000-000000000064',profile:'wa63-b',
  attempt:'ATTEMPT_WA63_B',corr:'CORR_WA63_B',wamid:'wamid.WA63.B'},
 {id:'f7400000-0000-4000-8000-000000000065',profile:'wa63-c',
  attempt:'ATTEMPT_WA63_C',corr:'CORR_WA63_C',wamid:'wamid.WA63.C'}
];
const TS=[0,1,2].map(i=>String(Math.floor(Date.now()/1000)-2200000-i*29));
const q=x=>"'"+String(x).replaceAll("'","''")+"'";
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const children=[];
after(()=>{
 for(const item of children){
  const c=item.child??item;
  if(c.exitCode===null&&c.signalCode===null)c.kill('SIGKILL');
 }
});
function processPG(script,interactive=false){
 const args=['-X','-qAt','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose',DSN];
 if(!interactive)args.push('-c',script);
 const c=spawn('psql',args,{
  env:{...process.env,PGPASSWORD:'postgres'},stdio:[interactive?'pipe':'ignore','pipe','pipe']});
 children.push(c);
 return c;
}
function pg(sql){
 const r=spawnSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
  '-v','VERBOSITY=verbose',DSN,'-c',sql],{
   encoding:'utf8',timeout:15000,env:{...process.env,PGPASSWORD:'postgres'}});
 if(r.error||r.status!==0)throw Error('WA63_SQL '+String(r.stderr).slice(-550));
 return r.stdout.trim();
}
const num=sql=>Number(pg('select count(*) from '+sql));
const state=s=>pg('select estado from prumo_private.outbox_intencoes_s0 where id='+q(s.id));
const status=k=>pg('select active::text from prumo_private.meta_wa48_shadow_keys_fixture_s0 where key_id='+q(k.id));
const nonces=k=>num('prumo_private.meta_wa48_shadow_nonces_fixture_s0 where key_id='+q(k.id));
const event=(s,ts)=>'WA46_'+createHash('sha256').update(JSON.stringify([
 WABA,PHONE,s.wamid,RECIPIENT,'delivered',ts])).digest('hex');
const count=(s,ts)=>num('prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(event(s,ts)));
const snapshot=(s,ts)=>pg("select id::text||'|'||body_sha256||'|'||provider_status "+
 'from prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(event(s,ts)));
function newKey(){
 const k={id:randomUUID(),secret:randomBytes(48).toString('hex')};
 pg('insert into prumo_private.meta_wa48_shadow_keys_fixture_s0('+
  'key_id,app,secret,active,valid_from,valid_until) values('+
  q(k.id)+','+q(APP)+',decode('+q(k.secret)+
  ",'hex'),true,clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '2 hours')");
 return k;
}
async function wait(check,description,ms=6000){
 const deadline=Date.now()+ms;
 while(Date.now()<deadline){
  const v=await check();if(v)return v;
  await sleep(25);
 }
 assert.fail('WA63_TIMEOUT '+description);
}
function waiterPid(blocker,needle){
 const sql="select pid::text from pg_catalog.pg_stat_activity where "+
  "datname='prumo_s0_test_ci' and wait_event_type='Lock' and "+
  "query like "+q('%'+needle+'%')+
  " and "+Number(blocker)+"=any(pg_catalog.pg_blocking_pids(pid)) order by pid limit 1";
 const v=pg(sql);
 return v&&/^[0-9]+$/.test(v)?Number(v):null;
}
function spawnQuery(sql){
 const child=processPG(sql);
 let out='',err='';
 child.stdout.on('data',b=>out+=String(b));
 child.stderr.on('data',b=>err+=String(b));
 const result=new Promise((resolve,reject)=>{
  child.on('error',reject);
  child.on('close',code=>resolve({code,out:out.trim(),err}));
 });
 return {child,result};
}
function cancelSql(s){
 return "update prumo_private.outbox_intencoes_s0 set estado='CANCELADA' "+
  'where id='+q(s.id)+" and estado='BLOQUEADA_GATES' returning estado";
}
function revokeSql(k){
 return 'select prumo_private.meta_wa48_shadow_revoke_fixture_s0('+q(k.id)+')';
}
function holdTx(script,marker){
 const c=processPG(null,true);
 const h={child:c,pid:null,out:'',err:''};
 c.stdout.on('data',b=>{
  h.out+=String(b);
  const m=new RegExp('([0-9]+)\\|'+marker).exec(h.out);
  if(m)h.pid=Number(m[1]);
 });
 c.stderr.on('data',b=>h.err+=String(b));
 c.stdin.write('BEGIN;\n'+script+';\n'+
   "select pg_catalog.pg_backend_pid()::text||'|"+marker+"';\n");
 return wait(()=>h.pid!==null||c.exitCode!==null,'hold '+marker).then(()=>{
  assert.ok(h.pid,'WA63_HOLD_FAILED '+h.err);
  return h;
 });
}
async function release(h,verb='COMMIT'){
 assert.ok(['COMMIT','ROLLBACK'].includes(verb));
 h.child.stdin.write(verb+';\n\\q\n');
 await wait(()=>h.child.exitCode!==null||h.child.signalCode!==null,'release '+verb);
 assert.equal(h.child.exitCode,0,h.err.slice(-300));
}
const raw=(s,ts)=>Buffer.from(JSON.stringify({object:'whatsapp_business_account',
 entry:[{id:WABA,changes:[{field:'messages',value:{
  metadata:{phone_number_id:PHONE},statuses:[{
   id:s.wamid,status:'delivered',recipient_id:RECIPIENT,timestamp:ts
  }]}}]}]}));
async function worker(k,s,mode='normal'){
 const file=join(dirname(fileURLToPath(import.meta.url)),'s0_wa_064_pg17_restart_worker.mjs');
 const c=spawn(process.execPath,[file],{env:{
  ...process.env,WA60_CLIENT_PASS:PASS,WA60_KEY_ID:k.id,
  WA60_KEY_SECRET:k.secret,WA60_CRASH_MODE:mode,
  WA61_BINDING_PROFILE:s.profile
 },stdio:['pipe','pipe','pipe']});
 children.push(c);
 const w={child:c,ready:null,held:null,receipts:[],err:''};
 let text='';
 c.stdout.on('data',b=>{
  text+=String(b);
  for(;;){
   const i=text.indexOf('\n');if(i<0)break;
   const line=text.slice(0,i);text=text.slice(i+1);
   try{
    const m=JSON.parse(line);
    if(m.type==='ready')w.ready=m;
    else if(m.type==='wa62-held')w.held=m;
    else if(m.type==='receipt')w.receipts.push(m);
   }catch{w.err+='BAD_STDOUT '+line.slice(0,50);}
  }
 });
 c.stderr.on('data',b=>w.err+=String(b).slice(-200));
 await wait(()=>w.ready||c.exitCode!==null||c.signalCode!==null,'worker ready');
 assert.ok(w.ready,'WA63_WORKER_FAILED '+w.err);
 assert.equal(w.ready.host,'127.0.0.1');
 assert.equal(w.ready.lab_only,true);
 assert.equal(w.ready.pid,c.pid);
 return w;
}
async function stop(w){
 assert.equal(w.child.exitCode,null,'already stopped');
 w.child.stdin.write('STOP\n');
 await wait(()=>w.child.exitCode!==null||w.child.signalCode!==null,'worker stop');
 assert.equal(w.child.exitCode,0,w.err.slice(-350));
}
function send(w,s,ts){
 const b=raw(s,ts);
 return new Promise(resolve=>{
  const request=http.request({host:'127.0.0.1',port:w.ready.port,path:w.ready.route,
   method:'POST',agent:false,headers:{
   'Content-Type':'application/json','Content-Length':String(b.length),
   'X-Hub-Signature-256':'sha256='+createHmac('sha256',META).update(b).digest('hex')
  }},response=>{
   const chunks=[];
   response.on('data',chunk=>chunks.push(chunk));
   response.on('end',()=>{
    try{resolve({code:response.statusCode,body:JSON.parse(Buffer.concat(chunks).toString())});}
    catch{resolve({code:response.statusCode,unreadable:true});}
   });
  });
  request.on('error',e=>resolve({broken:true,error:String(e.code??e.message)}));
  request.setTimeout(9000,()=>request.destroy(Error('WA63_HTTP_TIMEOUT')));
  request.end(b);
 });
}
function assertSafety(v){
 assert.equal(v.body?.lab_only,true);
 assert.equal(v.body?.meta_ack_emitted,false);
 assert.equal(v.body?.ack_allowed,false);
 assert.equal(v.body?.send_authorized,false);
}
function success(v){assert.equal(v.code,202,JSON.stringify(v));assertSafety(v);}
function denied(v){assert.equal(v.code,403,JSON.stringify(v));assertSafety(v);}

let baseline,keyA,keyB,keyC,A,B,C,D,E,F,heldCancelA,heldAppendB;
let revokedA,cancelledB,revokedB,heldRevokeC,cancelledC;
let pa,pb,pc,pidC,originalB,completedA=false,completedB=false,completedC=false;
const checks=[
 async()=>{
  assert.equal(pg('select current_database()'),'prumo_s0_test_ci');
  assert.equal(state({id:'f7400000-0000-4000-8000-000000000002'}),'CANCELADA');
  pg('alter role prumo_s0_meta_wa48_client_lab login password '+q(PASS));
  baseline=num('prumo_private.meta_status_forense_fixture_s0');
  for(let i=0;i<S.length;i++){
   const s=S[i];
   assert.equal(num('prumo_private.outbox_intencoes_s0 where id='+q(s.id)),0);
   pg('insert into prumo_private.outbox_intencoes_s0('+
    'id,concessionaria_id,canal_id,contrato,chave_idempotencia,versao_estado_sintetica) '+
    'values('+[s.id,SHOP,CHANNEL,'C03','WA63_TRIPLE_'+String(i),1].map(q).join(',')+')');
   const r=JSON.parse(pg('select prumo_private.registrar_vinculo_meta_tecnico_fixture_s0('+
    [APP,WABA,PHONE,CHANNEL,s.id,s.attempt,s.corr,RECIPIENT,s.wamid,200]
      .map((x,j)=>j===9?'200':q(x)).join(',')+')'));
   assert.equal(r.outcome,'LAB_BOUND',JSON.stringify(r));
   assert.equal(state(s),'BLOQUEADA_GATES');
   assert.equal(count(s,TS[i]),0);
  }
 },
 async()=>{
  keyA=newKey();A=await worker(keyA,S[0]);
  heldCancelA=await holdTx(cancelSql(S[0]),'WA63_CANCEL_A_HELD');
  assert.match(heldCancelA.out,/CANCELADA/);
 },
 async()=>{
  pa=send(A,S[0],TS[0]).then(v=>{completedA=true;return v;});
  await wait(()=>waiterPid(heldCancelA.pid,'meta_wa55_single_entry_fixture_s0'),
   'append waiting for cancellation A');
 },
 async()=>{
  assert.equal(state(S[0]),'BLOQUEADA_GATES');
  assert.equal(count(S[0],TS[0]),0);
  assert.equal(nonces(keyA),0);
  assert.equal(completedA,false);
 },
 async()=>{
  revokedA=spawnQuery(revokeSql(keyA));
  const x=await revokedA.result;
  assert.equal(x.code,0,x.err);
  assert.equal(x.out,'LAB_REVOKED');
  assert.equal(status(keyA),'false');
  assert.equal(completedA,false);
 },
 async()=>{
  await release(heldCancelA);
  denied(await pa);
  assert.equal(state(S[0]),'CANCELADA');
  assert.equal(count(S[0],TS[0]),0);
  assert.equal(nonces(keyA),0);
 },
 async()=>{
  await stop(A);
  B=await worker(keyA,S[0]);assert.notEqual(B.child.pid,A.child.pid);
  denied(await send(B,S[0],TS[0]));
  assert.equal(count(S[0],TS[0]),0);
  await stop(B);
 },
 async()=>{
  keyB=newKey();
  C=await worker(keyB,S[1],'holdcommit');
  pb=send(C,S[1],TS[1]).then(v=>{completedB=true;return v;});
 },
 async()=>{
  heldAppendB=await wait(()=>C.held,'WA55 held before COMMIT B');
  assert.equal(heldAppendB.event,event(S[1],TS[1]));
  assert.equal(heldAppendB.outcome,'LAB_OBSERVED_UNVERIFIED');
  assert.ok(Number.isInteger(heldAppendB.db_pid));
 },
 async()=>{
  assert.equal(state(S[1]),'BLOQUEADA_GATES');
  assert.equal(count(S[1],TS[1]),0);
  assert.equal(nonces(keyB),0);
  assert.equal(completedB,false);
 },
 async()=>{
  cancelledB=spawnQuery(cancelSql(S[1]));
  await wait(()=>waiterPid(heldAppendB.db_pid,'update prumo_private.outbox_intencoes_s0'),
   'cancel B waiting behind WA55 FOR SHARE');
 },
 async()=>{
  revokedB=spawnQuery(revokeSql(keyB));
  await wait(()=>waiterPid(heldAppendB.db_pid,'meta_wa48_shadow_revoke_fixture_s0'),
   'revoke B waiting behind WA55 key lock');
 },
 async()=>{
  assert.equal(completedB,false);
  assert.equal(cancelledB.child.exitCode,null);
  assert.equal(revokedB.child.exitCode,null);
  assert.equal(status(keyB),'true');
  assert.equal(state(S[1]),'BLOQUEADA_GATES');
  assert.equal(count(S[1],TS[1]),0);
 },
 async()=>{
  C.child.stdin.write('COMMIT\n');
  success(await pb);
  const [cancelResult,revokeResult]=await Promise.all([cancelledB.result,revokedB.result]);
  assert.equal(cancelResult.code,0,cancelResult.err);
  assert.equal(cancelResult.out,'CANCELADA');
  assert.equal(revokeResult.code,0,revokeResult.err);
  assert.equal(revokeResult.out,'LAB_REVOKED');
 },
 async()=>{
  assert.equal(count(S[1],TS[1]),1);
  originalB=snapshot(S[1],TS[1]);
  assert.match(originalB,/\|delivered$/);
  assert.equal(nonces(keyB),1);
  assert.equal(state(S[1]),'CANCELADA');
  assert.equal(status(keyB),'false');
 },
 async()=>{
  await stop(C);
  D=await worker(keyB,S[1]);denied(await send(D,S[1],TS[1]));
  assert.equal(snapshot(S[1],TS[1]),originalB);
  assert.equal(count(S[1],TS[1]),1);
  await stop(D);
 },
 async()=>{
  keyC=newKey();
  E=await worker(keyC,S[2]);
  const lock="pg_catalog.hashtextextended('wa48-key:'||"+q(keyC.id)+"::text,48)";
  heldRevokeC=await holdTx('SELECT pg_catalog.pg_advisory_xact_lock('+lock+');\n'+
   revokeSql(keyC),'WA63_REVOKE_C_HELD');
  assert.match(heldRevokeC.out,/LAB_REVOKED/);
 },
 async()=>{
  pc=send(E,S[2],TS[2]).then(v=>{completedC=true;return v;});
  pidC=await wait(()=>waiterPid(heldRevokeC.pid,'meta_wa55_single_entry_fixture_s0'),
   'append C awaiting revocation key lock');
  assert.ok(pidC>0);
 },
 async()=>{
  cancelledC=spawnQuery(cancelSql(S[2]));
  await wait(()=>waiterPid(pidC,'update prumo_private.outbox_intencoes_s0'),
   'cancel C blocked behind append C');
 },
 async()=>{
  assert.equal(completedC,false);
  assert.equal(cancelledC.child.exitCode,null);
  assert.equal(state(S[2]),'BLOQUEADA_GATES');
  assert.equal(status(keyC),'true');
  assert.equal(count(S[2],TS[2]),0);
  assert.equal(nonces(keyC),0);
 },
 async()=>{
  await release(heldRevokeC);
  denied(await pc);
  const c=await cancelledC.result;
  assert.equal(c.code,0,c.err);
  assert.equal(c.out,'CANCELADA');
  assert.equal(state(S[2]),'CANCELADA');
  assert.equal(status(keyC),'false');
 },
 async()=>{
  assert.equal(count(S[2],TS[2]),0);
  assert.equal(nonces(keyC),0);
  await stop(E);
  F=await worker(keyC,S[2]);denied(await send(F,S[2],TS[2]));
  assert.equal(count(S[2],TS[2]),0);
  await stop(F);
 },
 async()=>{
  assert.notEqual(A.child.pid,B.child.pid);
  assert.notEqual(C.child.pid,D.child.pid);
  assert.notEqual(E.child.pid,F.child.pid);
  assert.equal(num('prumo_private.meta_status_forense_fixture_s0'),baseline+1);
  assert.equal(snapshot(S[1],TS[1]),originalB);
  for(const scope of S)assert.equal(state(scope),'CANCELADA');
  for(const key of [keyA,keyB,keyC])assert.equal(status(key),'false');
 },
 async()=>{
  const ids=[keyA,keyB,keyC].map(k=>q(k.id)).join(',');
  assert.equal(num('prumo_private.meta_wa48_shadow_receipts_fixture_s0 where key_id in ('+ids+')'),0);
  assert.equal(num('prumo_private.meta_status_conflitos_fixture_s0 where event_ref in ('+
    S.map((scope,i)=>q(event(scope,TS[i]))).join(',')+')'),0);
  assert.equal(num('prumo_private.meta_status_forense_fixture_s0 where ack_allowed or send_authorized or retry_external or production_authorized or delivery_confirmed or case_transition_authorized or definitive_failure_count_increment'),0);
  assert.equal(pg("select has_function_privilege('prumo_s0_meta_wa48_client_lab',"+
   q('prumo_private.meta_wa52_locked_forensic_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)')+
   ",'EXECUTE')"),'f');
  assert.equal(num('prumo_private.meta_vinculos_tentativa_fixture_s0 where provider_message_id in ('+
    S.map(s=>q(s.wamid)).join(',')+')'),3);
 }
];
assert.equal(checks.length,24);
for(let i=0;i<checks.length;i++)
 test('WA63-'+String(i+1).padStart(2,'0')+' cancellation/revocation/forensics PG17',async()=>{
  await checks[i]();
  console.log('WA63-'+String(i+1).padStart(2,'0')+' PASS');
 });
