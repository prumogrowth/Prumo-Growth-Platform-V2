/** WA66: 24 physical checks combining WA57 bounded admission (4 slots /
 * 262144-byte raw bodies) with WA55 PG17 transaction and forensic variants.
 * All actors are disposable local loopback or PG17 sessions; never S1/Meta.
 */
import test,{after} from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import net from 'node:net';
import {spawn,spawnSync} from 'node:child_process';
import {createHmac,createHash,randomBytes,randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';

const DSN=process.env.PRUMO_TEST_DATABASE_URL??'',U=new URL(DSN);
if(U.protocol!=='postgresql:'||U.hostname!=='127.0.0.1'||U.port!=='5432'||
 U.username!=='postgres'||U.pathname!=='/prumo_s0_test_ci'||U.search||U.hash)
 throw Error('WA66_LOCAL_DISPOSABLE_PG17_ONLY');
for(const k of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER',
 'PGSERVICE','PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT',
 'PGSSLKEY','PGSSLROOTCERT'])if(process.env[k])throw Error('WA66_LIBPQ_OVERRIDE');

const PASS=randomBytes(32).toString('hex'),META=Buffer.alloc(48,0x4d);
const APP='12346000002',WABA='22346000002',PHONE='32346000002';
const SHOP='f7200000-0000-4000-8000-000000000002';
const CHANNEL='f7300000-0000-4000-8000-000000000002';
const RECIPIENT='5581900000000',MAX_BYTES=262144;
const S=[
 {id:'f7400000-0000-4000-8000-000000000071',profile:'wa66-a',
  attempt:'ATTEMPT_WA66_A',corr:'CORR_WA66_A',wamid:'wamid.WA66.A'},
 {id:'f7400000-0000-4000-8000-000000000072',profile:'wa66-b',
  attempt:'ATTEMPT_WA66_B',corr:'CORR_WA66_B',wamid:'wamid.WA66.B'}
];
const TS=[0,1,2,3].map(i=>String(Math.floor(Date.now()/1000)-3500000-i*47));
const q=x=>"'"+String(x).replaceAll("'","''")+"'";
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const children=[],sockets=[];
after(()=>{
 for(const c of children)if(c.exitCode===null&&c.signalCode===null)c.kill('SIGKILL');
 for(const s of sockets)if(!s.destroyed)s.destroy();
});
function pg(sql){
 const a=spawnSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
  '-v','VERBOSITY=verbose',DSN,'-c',sql],{
  encoding:'utf8',timeout:12000,env:{...process.env,PGPASSWORD:'postgres'}});
 if(a.error||a.status!==0)throw Error('WA66_SQL '+String(a.stderr).slice(-530));
 return a.stdout.trim();
}
const num=expr=>Number(pg('select count(*) from '+expr));
const state=s=>pg('select estado from prumo_private.outbox_intencoes_s0 where id='+q(s.id));
const active=k=>pg('select active::text from prumo_private.meta_wa48_shadow_keys_fixture_s0 where key_id='+q(k.id));
const nonce=k=>num('prumo_private.meta_wa48_shadow_nonces_fixture_s0 where key_id='+q(k.id));
const event=(s,ts)=>'WA46_'+createHash('sha256').update(
 JSON.stringify([WABA,PHONE,s.wamid,RECIPIENT,'delivered',ts])).digest('hex');
const count=(s,ts)=>num('prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(event(s,ts)));
const lines=(s,ts)=>pg("select id::text||'|'||body_sha256||'|'||provider_status "+
 'from prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(event(s,ts))+
 ' order by body_sha256').split('\n').filter(Boolean);
function key(){
 const k={id:randomUUID(),secret:randomBytes(48).toString('hex')};
 pg('insert into prumo_private.meta_wa48_shadow_keys_fixture_s0('+
 'key_id,app,secret,active,valid_from,valid_until) values('+
 q(k.id)+','+q(APP)+',decode('+q(k.secret)+
 ",'hex'),true,clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '2 hours')");
 return k;
}
async function wait(fn,tag,ms=6200){
 const until=Date.now()+ms;
 while(Date.now()<until){const v=await fn();if(v)return v;await delay(20);}
 assert.fail('WA66_TIMEOUT '+tag);
}
function launchSQL(sql){
 const child=spawn('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
 '-v','VERBOSITY=verbose',DSN,'-c',sql],{
  env:{...process.env,PGPASSWORD:'postgres'},stdio:['ignore','pipe','pipe']});
 children.push(child);
 let stdout='',stderr='';
 child.stdout.on('data',b=>stdout+=String(b));
 child.stderr.on('data',b=>stderr+=String(b));
 const result=new Promise((resolve,reject)=>{
  child.on('error',reject);
  child.on('close',code=>resolve({code,stdout:stdout.trim(),stderr}));
 });
 return {child,result};
}
const cancel=s=>"update prumo_private.outbox_intencoes_s0 set estado='CANCELADA' "+
 'where id='+q(s.id)+" and estado='BLOQUEADA_GATES' returning estado";
function blocked(blocker,part){
 return Number(pg("select count(*) from pg_catalog.pg_stat_activity "+
 "where datname='prumo_s0_test_ci' and wait_event_type='Lock' and "+
 "query like "+q('%'+part+'%')+" and "+Number(blocker)+
 "=any(pg_catalog.pg_blocking_pids(pid))"))>0;
}
function raw(s,ts,option='normal'){
 const status=option==='reorder'
  ?{timestamp:ts,recipient_id:RECIPIENT,status:'delivered',id:s.wamid}
  :{id:s.wamid,status:option==='bad-status'?'DELIVERED':'delivered',
    recipient_id:RECIPIENT,timestamp:ts};
 const root={object:'whatsapp_business_account',entry:[
  {id:WABA,changes:[{field:'messages',value:{
   metadata:{phone_number_id:PHONE},statuses:option==='two-statuses'?[status,status]:[status]
  }}]}]};
 if(option==='extra-root')root.extra='UNTRUSTED';
 return Buffer.from(JSON.stringify(root));
}
function padded(s,ts,length){
 const body=raw(s,ts),extra=length-body.length;
 assert.ok(extra>=0);
 return Buffer.concat([body,Buffer.alloc(extra,0x20)]);
}
async function worker(k,s,mode='normal'){
 const file=join(dirname(fileURLToPath(import.meta.url)),'s0_wa_064_pg17_restart_worker.mjs');
 const c=spawn(process.execPath,[file],{
  env:{...process.env,WA60_CLIENT_PASS:PASS,WA60_KEY_ID:k.id,
   WA60_KEY_SECRET:k.secret,WA60_CRASH_MODE:mode,
   WA61_BINDING_PROFILE:s.profile},stdio:['pipe','pipe','pipe']});
 children.push(c);
 const w={child:c,ready:null,held:null,receipts:[],err:''};let buffer='';
 c.stdout.on('data',d=>{
  buffer+=String(d);
  for(;;){
   const i=buffer.indexOf('\n');if(i<0)break;
   const line=buffer.slice(0,i);buffer=buffer.slice(i+1);
   try{const msg=JSON.parse(line);
    if(msg.type==='ready')w.ready=msg;
    else if(msg.type==='wa62-held')w.held=msg;
    else if(msg.type==='receipt')w.receipts.push(msg);
   }catch{w.err+='BAD_STDOUT '+line.slice(0,60);}
  }
 });
 c.stderr.on('data',d=>w.err+=String(d).slice(-280));
 await wait(()=>w.ready||c.exitCode!==null||c.signalCode!==null,'worker start');
 assert.ok(w.ready,'WA66_WORKER_FAILED '+w.err);
 assert.equal(w.ready.host,'127.0.0.1');
 assert.equal(w.ready.lab_only,true);
 return w;
}
async function stop(w){
 assert.equal(w.child.exitCode,null,'worker already stopped '+w.err);
 w.child.stdin.write('STOP\n');
 await wait(()=>w.child.exitCode!==null||w.child.signalCode!==null,'worker stop');
 assert.equal(w.child.exitCode,0,w.err);
}
function send(w,body,{badSig=false}={}){
 const signature='sha256='+(badSig?'0'.repeat(64):
  createHmac('sha256',META).update(body).digest('hex'));
 return new Promise(resolve=>{
  const req=http.request({host:'127.0.0.1',port:w.ready.port,
   path:w.ready.route,method:'POST',agent:false,headers:{
    'Content-Type':'application/json','Content-Length':String(body.length),
    'X-Hub-Signature-256':signature
   }},res=>{
    const data=[];res.on('data',d=>data.push(d));
    res.on('end',()=>{
     try{resolve({status:res.statusCode,body:JSON.parse(Buffer.concat(data).toString())});}
     catch{resolve({status:res.statusCode,unreadable:true});}
    });
   });
  req.on('error',e=>resolve({broken:true,error:String(e.code??e.message)}));
  req.setTimeout(9000,()=>req.destroy(Error('WA66_HTTP_TIMEOUT')));
  req.end(body);
 });
}
function assertResponse(v,status,decision){
 assert.equal(v.status,status,JSON.stringify(v));
 assert.equal(v.body?.decision,decision,JSON.stringify(v));
 assert.equal(v.body?.lab_only,true);
 assert.equal(v.body?.meta_ack_emitted,false);
 assert.equal(v.body?.ack_allowed,false);
 assert.equal(v.body?.send_authorized,false);
}
const accepted=v=>assertResponse(v,202,'LAB_HTTP_FORENSIC_STORED_ONLY');
const denied=v=>assertResponse(v,403,'LAB_HTTP_FORENSIC_DENIED');
const busy=v=>assertResponse(v,503,'LAB_HTTP_BUSY');
async function receipt(w,s,ts,outcome){
 await wait(()=>w.receipts.some(r=>r.event===event(s,ts)&&r.outcome===outcome),
  'forensic receipt '+outcome);
}
function slowSocket(w,s,ts){
 return new Promise((resolve,reject)=>{
  const socket=net.createConnection({host:'127.0.0.1',port:w.ready.port});
  sockets.push(socket);
  socket.on('error',()=>{});
  socket.once('connect',()=>{
   const body=raw(s,ts);
   const h=['POST '+w.ready.route+' HTTP/1.1',
    'Host: 127.0.0.1:'+w.ready.port,
    'Content-Type: application/json','Content-Length: '+body.length,
    'X-Hub-Signature-256: sha256='+
      createHmac('sha256',META).update(body).digest('hex'),
    'Connection: close','',''].join('\r\n');
   socket.write(h);socket.write(body.subarray(0,9));resolve(socket);
  });
  socket.once('error',reject);
 });
}
async function releaseSockets(){
 for(const s of sockets)if(!s.destroyed)s.destroy();
 await delay(100); // only cleanup; assertions prove busy via HTTP and SQL
}

let base,ka,kb,A,A2,B,held,pending,finished=false,cancelA,origA,variantA,lateA;
let baseB,reorderB,maxB,lateB;
const tests=[
 async()=>{
  assert.equal(pg('select current_database()'),'prumo_s0_test_ci');
  assert.equal(state({id:'f7400000-0000-4000-8000-000000000002'}),'CANCELADA');
  pg('alter role prumo_s0_meta_wa48_client_lab login password '+q(PASS));
  base=num('prumo_private.meta_status_forense_fixture_s0');
  for(let i=0;i<2;i++){
   const s=S[i];
   assert.equal(num('prumo_private.outbox_intencoes_s0 where id='+q(s.id)),0);
   pg('insert into prumo_private.outbox_intencoes_s0('+
    'id,concessionaria_id,canal_id,contrato,chave_idempotencia,versao_estado_sintetica) values('+
    [s.id,SHOP,CHANNEL,'C03','WA66_'+i,1].map(q).join(',')+')');
   const out=JSON.parse(pg('select prumo_private.registrar_vinculo_meta_tecnico_fixture_s0('+
    [APP,WABA,PHONE,CHANNEL,s.id,s.attempt,s.corr,
     RECIPIENT,s.wamid,200].map((v,j)=>j===9?'200':q(v)).join(',')+')'));
   assert.equal(out.outcome,'LAB_BOUND');
   assert.equal(state(s),'BLOQUEADA_GATES');
  }
  assert.equal(count(S[0],TS[0]),0);
  assert.equal(count(S[1],TS[2]),0);
 },
 async()=>{
  ka=key();A=await worker(ka,S[0],'holdcommit');
  pending=send(A,raw(S[0],TS[0])).then(r=>{finished=true;return r;});
  held=await wait(()=>A.held,'held forensic event');
  assert.equal(held.event,event(S[0],TS[0]));
  assert.equal(held.outcome,'LAB_OBSERVED_UNVERIFIED');
 },
 async()=>{
  assert.equal(finished,false);
  assert.equal(count(S[0],TS[0]),0);assert.equal(nonce(ka),0);
  assert.equal(state(S[0]),'BLOQUEADA_GATES');
 },
 async()=>{
  await Promise.all([slowSocket(A,S[0],TS[1]),
   slowSocket(A,S[0],TS[1]),slowSocket(A,S[0],TS[1])]);
  await delay(95); // allow Node to enter its 3 body-read reservations
  assert.equal(finished,false);
 },
 async()=>{
  busy(await send(A,raw(S[0],TS[1])));
  assert.equal(count(S[0],TS[1]),0);
  assert.equal(nonce(ka),0);
 },
 async()=>{
  busy(await send(A,raw(S[0],TS[1],'bad-status')));
  assert.equal(count(S[0],TS[1]),0);
  assert.equal(A.receipts.length,0);
 },
 async()=>{
  cancelA=launchSQL(cancel(S[0]));
  await wait(()=>blocked(held.db_pid,'update prumo_private.outbox_intencoes_s0'),
   'cancel blocked by live WA55 transaction');
  assert.equal(cancelA.child.exitCode,null);
  assert.equal(state(S[0]),'BLOQUEADA_GATES');
 },
 async()=>{
  await releaseSockets();
  assert.equal(finished,false);
  assert.equal(count(S[0],TS[0]),0);
  assert.equal(nonce(ka),0);
 },
 async()=>{
  A.child.stdin.write('COMMIT\n');
  accepted(await pending);
  const canceled=await cancelA.result;
  assert.equal(canceled.code,0,canceled.stderr);
  assert.equal(canceled.stdout,'CANCELADA');
  await receipt(A,S[0],TS[0],'LAB_OBSERVED_UNVERIFIED');
 },
 async()=>{
  assert.equal(state(S[0]),'CANCELADA');
  assert.equal(count(S[0],TS[0]),1);
  origA=lines(S[0],TS[0]);assert.equal(origA.length,1);
  assert.equal(nonce(ka),1);
  assert.equal(count(S[0],TS[1]),0);
 },
 async()=>{
  await stop(A);A2=await worker(ka,S[0]);
  accepted(await send(A2,raw(S[0],TS[1])));
  await receipt(A2,S[0],TS[1],'LAB_LATE_UNVERIFIED');
  lateA=lines(S[0],TS[1]);assert.equal(lateA.length,1);
  assert.equal(nonce(ka),2);
 },
 async()=>{
  accepted(await send(A2,raw(S[0],TS[0],'reorder')));
  await receipt(A2,S[0],TS[0],'LAB_BODY_VARIANT_QUARANTINED');
  variantA=lines(S[0],TS[0]);assert.equal(variantA.length,2);
  assert.ok(variantA.includes(origA[0]));
  accepted(await send(A2,raw(S[0],TS[0],'reorder')));
  await receipt(A2,S[0],TS[0],'LAB_EXACT_BODY_REPLAY');
  assert.deepEqual(lines(S[0],TS[0]),variantA);
  assert.equal(nonce(ka),4);
 },
 async()=>{
  await stop(A2);
  assert.equal(count(S[0],TS[0]),2);
  assert.equal(count(S[0],TS[1]),1);
  assert.deepEqual(lines(S[0],TS[1]),lateA);
  assert.equal(num('prumo_private.meta_status_forense_fixture_s0'),base+3);
 },
 async()=>{
  kb=key();B=await worker(kb,S[1]);
  accepted(await send(B,raw(S[1],TS[2])));
  await receipt(B,S[1],TS[2],'LAB_OBSERVED_UNVERIFIED');
  baseB=lines(S[1],TS[2]);assert.equal(baseB.length,1);
  assert.equal(nonce(kb),1);
 },
 async()=>{
  accepted(await send(B,raw(S[1],TS[2],'reorder')));
  await receipt(B,S[1],TS[2],'LAB_BODY_VARIANT_QUARANTINED');
  reorderB=lines(S[1],TS[2]);assert.equal(reorderB.length,2);
  assert.ok(reorderB.includes(baseB[0]));
  assert.equal(nonce(kb),2);
 },
 async()=>{
  accepted(await send(B,raw(S[1],TS[2],'reorder')));
  await receipt(B,S[1],TS[2],'LAB_EXACT_BODY_REPLAY');
  assert.deepEqual(lines(S[1],TS[2]),reorderB);
  assert.equal(nonce(kb),3);
 },
 async()=>{
  const atMax=padded(S[1],TS[2],MAX_BYTES);
  assert.equal(atMax.length,MAX_BYTES);
  accepted(await send(B,atMax));
  await receipt(B,S[1],TS[2],'LAB_BODY_VARIANT_QUARANTINED');
  maxB=lines(S[1],TS[2]);assert.equal(maxB.length,3);
  assert.ok(maxB.includes(baseB[0]));
  assert.equal(nonce(kb),4);
 },
 async()=>{
  const oversized=padded(S[1],TS[2],MAX_BYTES+1),before=nonce(kb);
  const r=await send(B,oversized);
  assertResponse(r,400,'LAB_HTTP_HEADERS_DENIED');
  assert.equal(nonce(kb),before);
  assert.deepEqual(lines(S[1],TS[2]),maxB);
 },
 async()=>{
  const before=nonce(kb),n=B.receipts.length;
  denied(await send(B,raw(S[1],TS[2],'extra-root')));
  assert.equal(nonce(kb),before);assert.equal(B.receipts.length,n);
  assert.deepEqual(lines(S[1],TS[2]),maxB);
 },
 async()=>{
  const before=nonce(kb),n=B.receipts.length;
  denied(await send(B,raw(S[1],TS[2],'bad-status')));
  assert.equal(nonce(kb),before);assert.equal(B.receipts.length,n);
 },
 async()=>{
  const before=nonce(kb),n=B.receipts.length;
  denied(await send(B,raw(S[1],TS[2],'two-statuses')));
  assert.equal(nonce(kb),before);assert.equal(B.receipts.length,n);
 },
 async()=>{
  const before=nonce(kb),n=B.receipts.length;
  denied(await send(B,raw(S[1],TS[2]),{badSig:true}));
  assert.equal(nonce(kb),before);assert.equal(B.receipts.length,n);
 },
 async()=>{
  assert.equal(pg(cancel(S[1])),'CANCELADA');
  accepted(await send(B,raw(S[1],TS[3])));
  await receipt(B,S[1],TS[3],'LAB_LATE_UNVERIFIED');
  lateB=lines(S[1],TS[3]);assert.equal(lateB.length,1);
  accepted(await send(B,raw(S[1],TS[2])));
  await receipt(B,S[1],TS[2],'LAB_EXACT_BODY_REPLAY');
  assert.deepEqual(lines(S[1],TS[2]),maxB);
  assert.equal(nonce(kb),6);
 },
 async()=>{
  await stop(B);
  assert.equal(num('prumo_private.meta_status_forense_fixture_s0'),base+7);
  assert.equal(count(S[0],TS[0]),2);assert.equal(count(S[0],TS[1]),1);
  assert.equal(count(S[1],TS[2]),3);assert.equal(count(S[1],TS[3]),1);
  assert.deepEqual(lines(S[0],TS[0]),variantA);
  assert.deepEqual(lines(S[0],TS[1]),lateA);
  assert.deepEqual(lines(S[1],TS[2]),maxB);
  assert.deepEqual(lines(S[1],TS[3]),lateB);
  assert.equal(nonce(ka),4);assert.equal(nonce(kb),6);
  assert.equal(active(ka),'true');assert.equal(active(kb),'true');
  assert.equal(state(S[0]),'CANCELADA');assert.equal(state(S[1]),'CANCELADA');
  assert.equal(num('prumo_private.meta_status_conflitos_fixture_s0 where event_ref in ('+
   [event(S[0],TS[0]),event(S[0],TS[1]),event(S[1],TS[2]),event(S[1],TS[3])]
    .map(q).join(',')+')'),0);
  assert.equal(num('prumo_private.meta_wa48_shadow_receipts_fixture_s0 where key_id in ('+
   [ka,kb].map(k=>q(k.id)).join(',')+')'),0);
  assert.equal(num('prumo_private.meta_status_forense_fixture_s0 where ack_allowed or send_authorized or retry_external or production_authorized or delivery_confirmed or case_transition_authorized or definitive_failure_count_increment'),0);
  assert.equal(pg("select has_function_privilege('prumo_s0_meta_wa48_client_lab',"+
   q('prumo_private.meta_wa52_locked_forensic_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)')+
   ",'EXECUTE')"),'f');
 }
];
assert.equal(tests.length,24);
for(let i=0;i<tests.length;i++)
 test('WA66-'+String(i+1).padStart(2,'0')+' bounded-admission and raw variant PG17',async()=>{
  await tests[i]();console.log('WA66-'+String(i+1).padStart(2,'0')+' PASS');
 });
