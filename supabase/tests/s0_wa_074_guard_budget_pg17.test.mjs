/** WA68: budget/complexity of WA67 strict JSON guard, signed HTTP
 * saturation and forensic atomicity under an OPEN PG17 transaction.
 * Lab-only; contract decisions and production integration belong to Codex.
 */
import test,{after} from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import net from 'node:net';
import {spawn,spawnSync} from 'node:child_process';
import {createHash,createHmac,randomBytes,randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';
import {wa67StrictJsonKeys} from './s0_wa_072_strict_json_keys.mjs';

const DSN=process.env.PRUMO_TEST_DATABASE_URL??'',U=new URL(DSN);
if(U.protocol!=='postgresql:'||U.hostname!=='127.0.0.1'||U.port!=='5432'||
 U.username!=='postgres'||U.pathname!=='/prumo_s0_test_ci'||U.search||U.hash)
 throw Error('WA68_DISPOSABLE_PG17_ONLY');
for(const k of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER','PGSERVICE',
 'PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT','PGSSLKEY','PGSSLROOTCERT'])
 if(process.env[k])throw Error('WA68_LIBPQ_OVERRIDE');
const PASS=randomBytes(32).toString('hex'),META=Buffer.alloc(48,0x4d);
const APP='12346000002',WABA='22346000002',PHONE='32346000002';
const SHOP='f7200000-0000-4000-8000-000000000002';
const CHANNEL='f7300000-0000-4000-8000-000000000002';
const RECIPIENT='5581900000000';
const S={id:'f7400000-0000-4000-8000-000000000074',profile:'wa68-a',
 attempt:'ATTEMPT_WA68_A',corr:'CORR_WA68_A',wamid:'wamid.WA68.A'};
const TS=Array.from({length:5},(_,i)=>String(Math.floor(Date.now()/1000)-4000000-i*41));
const q=x=>"'"+String(x).replaceAll("'","''")+"'";
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const children=[],sockets=[];
after(()=>{
 for(const c of children)if(c.exitCode===null&&c.signalCode===null)c.kill('SIGKILL');
 for(const s of sockets)if(!s.destroyed)s.destroy();
});
function pg(sql){
 const r=spawnSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
  '-v','VERBOSITY=verbose',DSN,'-c',sql],{
   encoding:'utf8',timeout:14000,env:{...process.env,PGPASSWORD:'postgres'}});
 if(r.error||r.status!==0)throw Error('WA68_SQL '+String(r.stderr).slice(-600));
 return r.stdout.trim();
}
const number=table=>Number(pg('select count(*) from '+table));
const state=()=>pg('select estado from prumo_private.outbox_intencoes_s0 where id='+q(S.id));
const nonce=k=>number('prumo_private.meta_wa48_shadow_nonces_fixture_s0 where key_id='+q(k.id));
const active=k=>pg('select active::text from prumo_private.meta_wa48_shadow_keys_fixture_s0 where key_id='+q(k.id));
const ev=ts=>'WA46_'+createHash('sha256').update(
 JSON.stringify([WABA,PHONE,S.wamid,RECIPIENT,'delivered',ts])).digest('hex');
const count=ts=>number('prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(ev(ts)));
const snapshot=ts=>pg("select id::text||'|'||body_sha256||'|'||provider_status "+
 'from prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(ev(ts))+
 ' order by body_sha256').split('\n').filter(Boolean);
function newKey(){
 const k={id:randomUUID(),secret:randomBytes(48).toString('hex')};
 pg('insert into prumo_private.meta_wa48_shadow_keys_fixture_s0('+
 'key_id,app,secret,active,valid_from,valid_until) values('+
 q(k.id)+','+q(APP)+',decode('+q(k.secret)+
 ",'hex'),true,clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '2 hours')");
 return k;
}
async function wait(fn,label,timeout=6500){
 const end=Date.now()+timeout;
 while(Date.now()<end){const v=fn();if(v)return v;await sleep(20);}
 assert.fail('WA68_WAIT '+label);
}
function pgAsync(query){
 const c=spawn('psql',['-X','-qAt','-v','ON_ERROR_STOP=1','-v',
  'VERBOSITY=verbose',DSN,'-c',query],{
   env:{...process.env,PGPASSWORD:'postgres'},stdio:['ignore','pipe','pipe']});
 children.push(c);let out='',err='';
 c.stdout.on('data',d=>out+=String(d));
 c.stderr.on('data',d=>err+=String(d));
 return {child:c,result:new Promise((resolve,reject)=>{
  c.on('error',reject);c.on('close',code=>resolve({code,out:out.trim(),err}));
 })};
}
function blocked(pid,fragment){
 return Number(pg("select count(*) from pg_catalog.pg_stat_activity "+
  "where datname='prumo_s0_test_ci' and wait_event_type='Lock' "+
  "and query like "+q('%'+fragment+'%')+
  " and "+Number(pid)+"=any(pg_catalog.pg_blocking_pids(pid))"))>0;
}
function raw(ts=TS[0]){
 return Buffer.from(JSON.stringify({object:'whatsapp_business_account',entry:[
  {id:WABA,changes:[{field:'messages',value:{metadata:{phone_number_id:PHONE},
   statuses:[{id:S.wamid,status:'delivered',recipient_id:RECIPIENT,timestamp:ts}]
  }}]}]}));
}
function fixedSize(ts,len){
 const start=raw(ts);
 assert.ok(start.length<=len);
 return Buffer.concat([start,Buffer.alloc(len-start.length,0x20)]);
}
function complexity(kind){
 if(kind==='names')return Buffer.from('{"extra":'+
  '{'+Array.from({length:2049},(_,i)=>'"key'+i+'":0').join(',')+'}}');
 if(kind==='nodes')return Buffer.from('{"extra":['+
  Array.from({length:4097},()=>0).join(',')+']}');
 if(kind==='depth')return Buffer.from('{"extra":'+
  '['.repeat(50)+'0'+']'.repeat(50)+'}');
 if(kind==='duplicate')return Buffer.from(raw().toString().replace(
  '"statuses":','"statuses":[],"statuses":'));
 throw Error('unknown');
}
async function worker(k,mode='normal'){
 const file=join(dirname(fileURLToPath(import.meta.url)),'s0_wa_064_pg17_restart_worker.mjs');
 const c=spawn(process.execPath,[file],{
  env:{...process.env,WA60_CLIENT_PASS:PASS,WA60_KEY_ID:k.id,
   WA60_KEY_SECRET:k.secret,WA60_CRASH_MODE:mode,
   WA61_BINDING_PROFILE:S.profile},stdio:['pipe','pipe','pipe']});
 children.push(c);
 const w={child:c,ready:null,held:null,receipts:[],err:''};let buffer='';
 c.stdout.on('data',d=>{
  buffer+=String(d);
  for(;;){
   const i=buffer.indexOf('\n');if(i<0)break;
   const line=buffer.slice(0,i);buffer=buffer.slice(i+1);
   try{const x=JSON.parse(line);
    if(x.type==='ready')w.ready=x;
    if(x.type==='wa62-held')w.held=x;
    if(x.type==='receipt')w.receipts.push(x);
   }catch{w.err+='BAD '+line.slice(0,60);}
  }
 });
 c.stderr.on('data',d=>w.err+=String(d).slice(-200));
 await wait(()=>w.ready||c.exitCode!==null||c.signalCode!==null,'worker');
 assert.ok(w.ready,w.err);
 assert.equal(w.ready.host,'127.0.0.1');
 assert.equal(w.ready.lab_only,true);
 return w;
}
async function stop(w){
 assert.equal(w.child.exitCode,null,w.err);
 w.child.stdin.write('STOP\n');
 await wait(()=>w.child.exitCode!==null||w.child.signalCode!==null,'worker stop');
 assert.equal(w.child.exitCode,0,w.err);
}
function send(w,bytes,options={}){
 const signature='sha256='+(options.badSig?'0'.repeat(64):
  createHmac('sha256',META).update(bytes).digest('hex'));
 return new Promise(resolve=>{
  const req=http.request({host:'127.0.0.1',port:w.ready.port,path:w.ready.route,
   method:'POST',agent:false,headers:{
    'Content-Type':'application/json','Content-Length':String(bytes.length),
    'X-Hub-Signature-256':signature
   }},res=>{
    const all=[];
    res.on('data',c=>all.push(c));res.on('end',()=>{
     try{resolve({status:res.statusCode,body:JSON.parse(Buffer.concat(all).toString())});}
     catch{resolve({status:res.statusCode,invalid:true});}
    });
   });
  req.on('error',e=>resolve({error:String(e.code??e.message)}));
  req.setTimeout(10000,()=>req.destroy(Error('WA68_HTTP_TIMEOUT')));
  req.end(bytes);
 });
}
function response(v,status,decision){
 assert.equal(v.status,status,JSON.stringify(v));
 assert.equal(v.body?.decision,decision,JSON.stringify(v));
 assert.equal(v.body?.lab_only,true);
 assert.equal(v.body?.meta_ack_emitted,false);
 assert.equal(v.body?.ack_allowed,false);
 assert.equal(v.body?.send_authorized,false);
}
const ok=v=>response(v,202,'LAB_HTTP_FORENSIC_STORED_ONLY');
const denied=v=>response(v,403,'LAB_HTTP_FORENSIC_DENIED');
const busy=v=>response(v,503,'LAB_HTTP_BUSY');
async function receipt(w,ts,outcome){
 await wait(()=>w.receipts.some(x=>x.event===ev(ts)&&x.outcome===outcome),
  'receipt '+outcome);
}
function slowSocket(w,ts){
 return new Promise((resolve,reject)=>{
  const socket=net.createConnection({host:'127.0.0.1',port:w.ready.port});
  sockets.push(socket);socket.on('error',()=>{});
  socket.once('connect',()=>{
   const data=raw(ts);
   socket.write(['POST '+w.ready.route+' HTTP/1.1',
    'Host: 127.0.0.1:'+w.ready.port,
    'Content-Type: application/json','Content-Length: '+data.length,
    'X-Hub-Signature-256: sha256='+
    createHmac('sha256',META).update(data).digest('hex'),
    'Connection: close','',''].join('\r\n'));
   socket.write(data.subarray(0,10));resolve(socket);
  });
  socket.once('error',reject);
 });
}
async function closeSlow(){
 for(const s of sockets)if(!s.destroyed)s.destroy();
 await sleep(100);
}
async function noWrite(bytes){
 const before=nonce(KEY),prev=W.receipts.length;
 denied(await send(W,bytes));
 assert.equal(nonce(KEY),before);
 assert.equal(W.receipts.length,prev);
 assert.deepEqual(snapshot(TS[0]),record0);
}
let baseline,KEY,W,W2,pending,hold,slow,cancel,record0,maxVariant,completed=false;
const tests=[
 async()=>{
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"x":1}')),true);
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"x":1,"x":2}')),false);
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"x":1,"\\u0078":2}')),false);
 },
 async()=>{
  const a=n=>Buffer.from('{'+Array.from({length:n},(_,i)=>'"k'+i+'":0').join(',')+'}');
  assert.equal(wa67StrictJsonKeys(a(2048)),true);
  assert.equal(wa67StrictJsonKeys(a(2049)),false);
 },
 async()=>{
  const a=n=>Buffer.from('['+Array.from({length:n},()=>0).join(',')+']');
  assert.equal(wa67StrictJsonKeys(a(4095)),true);
  assert.equal(wa67StrictJsonKeys(a(4096)),false);
 },
 async()=>{
  const a=n=>Buffer.from('['.repeat(n)+'0'+']'.repeat(n));
  assert.equal(wa67StrictJsonKeys(a(48)),true);
  assert.equal(wa67StrictJsonKeys(a(49)),false);
 },
 async()=>{
  assert.equal(wa67StrictJsonKeys(Buffer.concat([Buffer.from('{}'),
   Buffer.alloc(262142,0x20)])),true);
  assert.equal(wa67StrictJsonKeys(Buffer.concat([Buffer.from('{}'),
   Buffer.alloc(262143,0x20)])),false);
 },
 async()=>{
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"\\u00e9":1,"e\\u0301":2}')),true);
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"\\u00e9":1,"é":2}')),false);
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"x":"\\uD83D\\uDE80"}')),true);
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"x":"\\uDE80"}')),false);
 },
 async()=>{
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"x":"'+ 'a'.repeat(200000)+'"}')),true);
  assert.equal(wa67StrictJsonKeys(Buffer.from([0xef,0xbb,0xbf,0x7b,0x7d])),false);
  assert.equal(wa67StrictJsonKeys(Buffer.from([0x7b,0x22,0x61,0x22,0x3a,0xff,0x7d])),false);
 },
 async()=>{
  assert.equal(pg('select current_database()'),'prumo_s0_test_ci');
  assert.equal(number('prumo_private.outbox_intencoes_s0 where id='+q(S.id)),0);
  pg('alter role prumo_s0_meta_wa48_client_lab login password '+q(PASS));
  baseline=number('prumo_private.meta_status_forense_fixture_s0');
  pg('insert into prumo_private.outbox_intencoes_s0('+
   'id,concessionaria_id,canal_id,contrato,chave_idempotencia,versao_estado_sintetica) values('+
   [S.id,SHOP,CHANNEL,'C03','WA68_BUDGET',1].map(q).join(',')+')');
  const v=JSON.parse(pg('select prumo_private.registrar_vinculo_meta_tecnico_fixture_s0('+
   [APP,WABA,PHONE,CHANNEL,S.id,S.attempt,S.corr,RECIPIENT,S.wamid,200]
   .map((v,i)=>i===9?'200':q(v)).join(',')+')'));
  assert.equal(v.outcome,'LAB_BOUND');assert.equal(state(),'BLOQUEADA_GATES');
 },
 async()=>{
  KEY=newKey();W=await worker(KEY,'holdcommit');
  pending=send(W,raw()).then(v=>{completed=true;return v;});
  hold=await wait(()=>W.held,'hold PG17');
  assert.equal(hold.event,ev(TS[0]));
  assert.equal(hold.outcome,'LAB_OBSERVED_UNVERIFIED');
 },
 async()=>{
  assert.equal(completed,false);
  assert.equal(count(TS[0]),0);assert.equal(nonce(KEY),0);
  assert.equal(state(),'BLOQUEADA_GATES');
 },
 async()=>{
  slow=await Promise.all([slowSocket(W,TS[1]),slowSocket(W,TS[1]),slowSocket(W,TS[1])]);
  await sleep(90);assert.equal(slow.length,3);
  assert.equal(completed,false);
 },
 async()=>{
  busy(await send(W,raw(TS[1])));
  assert.equal(nonce(KEY),0);assert.equal(count(TS[1]),0);
 },
 async()=>{
  busy(await send(W,complexity('names')));
  assert.equal(W.receipts.length,0);assert.equal(count(TS[1]),0);
 },
 async()=>{
  cancel=pgAsync("update prumo_private.outbox_intencoes_s0 set estado='CANCELADA' "+
   'where id='+q(S.id)+" and estado='BLOQUEADA_GATES' returning estado");
  await wait(()=>blocked(hold.db_pid,'update prumo_private.outbox_intencoes_s0'),
   'cancel waiting');
  assert.equal(cancel.child.exitCode,null);
 },
 async()=>{
  await closeSlow();
  assert.equal(completed,false);
  assert.equal(count(TS[0]),0);assert.equal(nonce(KEY),0);
 },
 async()=>{
  W.child.stdin.write('COMMIT\n');
  ok(await pending);
  const c=await cancel.result;
  assert.equal(c.code,0,c.err);assert.equal(c.out,'CANCELADA');
  await receipt(W,TS[0],'LAB_OBSERVED_UNVERIFIED');
  assert.equal(state(),'CANCELADA');
 },
 async()=>{
  record0=snapshot(TS[0]);
  assert.equal(record0.length,1);assert.equal(nonce(KEY),1);
  assert.equal(count(TS[1]),0);
 },
 async()=>{
  await stop(W);W=await worker(KEY);
  await noWrite(complexity('names'));
  await noWrite(complexity('nodes'));
  await noWrite(complexity('depth'));
 },
 async()=>{
  await noWrite(complexity('duplicate'));
  await noWrite(Buffer.concat([Buffer.from([0xef,0xbb,0xbf]),raw()]));
  await noWrite(Buffer.from(raw().toString().replace('"statuses":',
   '"statuses":[{},{}],"statuses":')));
 },
 async()=>{
  const max=fixedSize(TS[0],262144);
  assert.equal(wa67StrictJsonKeys(max),true);
  ok(await send(W,max));
  await receipt(W,TS[0],'LAB_BODY_VARIANT_QUARANTINED');
  maxVariant=snapshot(TS[0]);assert.equal(maxVariant.length,2);
  assert.ok(maxVariant.includes(record0[0]));
  assert.equal(nonce(KEY),2);
 },
 async()=>{
  const before=nonce(KEY);
  response(await send(W,fixedSize(TS[0],262145)),400,'LAB_HTTP_HEADERS_DENIED');
  assert.equal(nonce(KEY),before);
  assert.deepEqual(snapshot(TS[0]),maxVariant);
 },
 async()=>{
  const results=await Promise.all(TS.slice(1).map(ts=>send(W,raw(ts))));
  for(const x of results)ok(x);
  for(const ts of TS.slice(1))await receipt(W,ts,'LAB_LATE_UNVERIFIED');
  for(const ts of TS.slice(1))assert.equal(count(ts),1);
  assert.equal(nonce(KEY),6);
 },
 async()=>{
  await stop(W);
  assert.equal(pg('select prumo_private.meta_wa48_shadow_revoke_fixture_s0('+q(KEY.id)+')'),'LAB_REVOKED');
  W2=await worker(KEY);
  response(await send(W2,raw()),403,'LAB_HTTP_FORENSIC_DENIED');
  await stop(W2);
  assert.equal(active(KEY),'false');
 },
 async()=>{
  assert.equal(number('prumo_private.meta_status_forense_fixture_s0'),baseline+6);
  assert.equal(count(TS[0]),2);
  for(const ts of TS.slice(1))assert.equal(count(ts),1);
  assert.deepEqual(snapshot(TS[0]),maxVariant);
  assert.equal(nonce(KEY),6);assert.equal(state(),'CANCELADA');
  assert.equal(number('prumo_private.meta_status_conflitos_fixture_s0 where event_ref in ('+
   TS.map(ev).map(q).join(',')+')'),0);
  assert.equal(number('prumo_private.meta_wa48_shadow_receipts_fixture_s0 where key_id='+q(KEY.id)),0);
  assert.equal(number('prumo_private.meta_status_forense_fixture_s0 where ack_allowed or send_authorized or retry_external or production_authorized or delivery_confirmed or case_transition_authorized or definitive_failure_count_increment'),0);
  assert.equal(pg("select has_function_privilege('prumo_s0_meta_wa48_client_lab',"+
   q('prumo_private.meta_wa52_locked_forensic_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)')+
   ",'EXECUTE')"),'f');
 }
];
assert.equal(tests.length,24);
for(let i=0;i<tests.length;i++)test('WA68-'+String(i+1).padStart(2,'0')+
 ' JSON budget and concurrent PG17 admission',async()=>{
 await tests[i]();console.log('WA68-'+String(i+1).padStart(2,'0')+' PASS');
});
