/** WA67 S0-only ambiguity proposal: decoded duplicate keys, malformed UTF-8,
 * lone surrogates and safe escaped ASCII variants. PG17 disposable + loopback.
 * No official core changes, Meta Graph, external ACK, service IAM or S1.
 */
import test,{after} from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import {spawn,spawnSync} from 'node:child_process';
import {createHmac,createHash,randomBytes,randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';
import {wa67StrictJsonKeys} from './s0_wa_072_strict_json_keys.mjs';

const DSN=process.env.PRUMO_TEST_DATABASE_URL??'',url=new URL(DSN);
if(url.protocol!=='postgresql:'||url.hostname!=='127.0.0.1'||url.port!=='5432'||
 url.username!=='postgres'||url.pathname!=='/prumo_s0_test_ci'||url.search||url.hash)
 throw Error('WA67_DISPOSABLE_PG17_ONLY');
for(const k of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER','PGSERVICE',
 'PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT','PGSSLKEY','PGSSLROOTCERT'])
 if(process.env[k])throw Error('WA67_LIBPQ_OVERRIDE');

const PASS=randomBytes(32).toString('hex'),META=Buffer.alloc(48,0x4d);
const APP='12346000002',WABA='22346000002',PHONE='32346000002';
const SHOP='f7200000-0000-4000-8000-000000000002';
const CHANNEL='f7300000-0000-4000-8000-000000000002';
const RECIPIENT='5581900000000';
const S={id:'f7400000-0000-4000-8000-000000000073',profile:'wa67-a',
 attempt:'ATTEMPT_WA67_A',corr:'CORR_WA67_A',wamid:'wamid.WA67.A'};
const T0=String(Math.floor(Date.now()/1000)-3700000);
const T1=String(Number(T0)+1);
const q=x=>"'"+String(x).replaceAll("'","''")+"'";
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const children=[];
after(()=>{for(const c of children)if(c.exitCode===null&&c.signalCode===null)c.kill('SIGKILL');});
function pg(sql){
 const r=spawnSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
  '-v','VERBOSITY=verbose',DSN,'-c',sql],{
  encoding:'utf8',timeout:15000,env:{...process.env,PGPASSWORD:'postgres'}});
 if(r.error||r.status!==0)throw Error('WA67_PSQL '+String(r.stderr).slice(-500));
 return r.stdout.trim();
}
const num=t=>Number(pg('select count(*) from '+t));
const nonce=k=>num('prumo_private.meta_wa48_shadow_nonces_fixture_s0 where key_id='+q(k.id));
const active=k=>pg('select active::text from prumo_private.meta_wa48_shadow_keys_fixture_s0 where key_id='+q(k.id));
const state=()=>pg('select estado from prumo_private.outbox_intencoes_s0 where id='+q(S.id));
const event=t=>'WA46_'+createHash('sha256').update(JSON.stringify([
 WABA,PHONE,S.wamid,RECIPIENT,'delivered',t])).digest('hex');
const count=t=>num('prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(event(t)));
const snapshot=t=>pg("select id::text||'|'||body_sha256||'|'||provider_status "+
 'from prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(event(t))+
 ' order by body_sha256').split('\n').filter(Boolean);
const body=t=>Buffer.from(JSON.stringify({object:'whatsapp_business_account',entry:[
 {id:WABA,changes:[{field:'messages',value:{
  metadata:{phone_number_id:PHONE},statuses:[
   {id:S.wamid,status:'delivered',recipient_id:RECIPIENT,timestamp:t}]
 }}]}]}));
const altered=(t,from,to)=>Buffer.from(body(t).toString('utf8').replace(from,to));
function shadowKey(){
 const k={id:randomUUID(),secret:randomBytes(48).toString('hex')};
 pg('insert into prumo_private.meta_wa48_shadow_keys_fixture_s0('+
 'key_id,app,secret,active,valid_from,valid_until) values('+
 q(k.id)+','+q(APP)+',decode('+q(k.secret)+
 ",'hex'),true,clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '2 hours')");
 return k;
}
async function wait(check,name,ms=6500){
 const until=Date.now()+ms;
 while(Date.now()<until){const hit=check();if(hit)return hit;await delay(20);}
 assert.fail('WA67_WAIT_TIMEOUT '+name);
}
async function worker(k){
 const file=join(dirname(fileURLToPath(import.meta.url)),'s0_wa_064_pg17_restart_worker.mjs');
 const child=spawn(process.execPath,[file],{env:{...process.env,
  WA60_CLIENT_PASS:PASS,WA60_KEY_ID:k.id,WA60_KEY_SECRET:k.secret,
  WA60_CRASH_MODE:'normal',WA61_BINDING_PROFILE:S.profile},
  stdio:['pipe','pipe','pipe']});
 children.push(child);
 const w={child,ready:null,receipts:[],err:''};let buffer='';
 child.stdout.on('data',v=>{
  buffer+=String(v);
  for(;;){
   const end=buffer.indexOf('\n');if(end<0)break;
   const line=buffer.slice(0,end);buffer=buffer.slice(end+1);
   try{
    const row=JSON.parse(line);
    if(row.type==='ready')w.ready=row;
    if(row.type==='receipt')w.receipts.push(row);
   }catch{w.err+='BAD_OUT '+line.slice(0,50);}
  }
 });
 child.stderr.on('data',v=>w.err+=String(v).slice(-200));
 await wait(()=>w.ready||child.exitCode!==null||child.signalCode!==null,'worker ready');
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
function post(w,bytes,{badSig=false}={}){
 const signature='sha256='+(badSig?'0'.repeat(64):
  createHmac('sha256',META).update(bytes).digest('hex'));
 return new Promise(resolve=>{
  const req=http.request({host:'127.0.0.1',port:w.ready.port,path:w.ready.route,
   method:'POST',agent:false,headers:{
    'Content-Type':'application/json','Content-Length':String(bytes.length),
    'X-Hub-Signature-256':signature
   }},res=>{
    const chunks=[];res.on('data',x=>chunks.push(x));
    res.on('end',()=>{
     try{resolve({status:res.statusCode,body:JSON.parse(Buffer.concat(chunks).toString())});}
     catch{resolve({status:res.statusCode,unreadable:true});}
    });
   });
  req.on('error',e=>resolve({broken:true,error:String(e.code??e.message)}));
  req.setTimeout(8500,()=>req.destroy(Error('WA67_HTTP_TIMEOUT')));
  req.end(bytes);
 });
}
function decision(v,status,code){
 assert.equal(v.status,status,JSON.stringify(v));
 assert.equal(v.body?.decision,code,JSON.stringify(v));
 assert.equal(v.body?.lab_only,true);
 assert.equal(v.body?.meta_ack_emitted,false);
 assert.equal(v.body?.ack_allowed,false);
 assert.equal(v.body?.send_authorized,false);
}
const accepted=v=>decision(v,202,'LAB_HTTP_FORENSIC_STORED_ONLY');
const denied=v=>decision(v,403,'LAB_HTTP_FORENSIC_DENIED');
async function noImpact(bytes){
 const n=nonce(K),prev=W.receipts.length;
 assert.equal(wa67StrictJsonKeys(bytes),false);
 denied(await post(W,bytes));
 assert.equal(nonce(K),n);
 assert.equal(W.receipts.length,prev);
 assert.deepEqual(snapshot(T0),stored);
}
let K,K2,W,W2,baseline,stored,afterAlias,afterScalar,afterReorder,lateSnapshot;
const tests=[
 async()=>{
  assert.equal(wa67StrictJsonKeys(body(T0)),true);
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"key":1,"other":{"key":2}}')),true);
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"a":"\\uD83D\\uDE80"}')),true);
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"a":"A","b":"\\u0041"}')),true);
 },
 async()=>{
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"a":1,"a":2}')),false);
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"a":1,"\\u0061":2}')),false);
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"nested":{"x":1,"x":2}}')),false);
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"nested":[{"x":1},{"x":2}]}')),true);
 },
 async()=>{
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"a":"\\uD800"}')),false);
  assert.equal(wa67StrictJsonKeys(Buffer.from('{"\\uDC00":1}')),false);
  assert.equal(wa67StrictJsonKeys(Buffer.from([0xef,0xbb,0xbf,0x7b,0x7d])),false);
  assert.equal(wa67StrictJsonKeys(Buffer.from([0x7b,0x22,0x61,0x22,0x3a,0x22,0xff,0x22,0x7d])),false);
 },
 async()=>{
  assert.equal(pg('select current_database()'),'prumo_s0_test_ci');
  assert.equal(state(),'', 'WA67 scope must not preexist');
 },
 async()=>{
  pg('alter role prumo_s0_meta_wa48_client_lab login password '+q(PASS));
  baseline=num('prumo_private.meta_status_forense_fixture_s0');
  pg('insert into prumo_private.outbox_intencoes_s0('+
   'id,concessionaria_id,canal_id,contrato,chave_idempotencia,versao_estado_sintetica) values('+
   [S.id,SHOP,CHANNEL,'C03','WA67_AMBIGUOUS_KEYS',1].map(q).join(',')+')');
  const b=JSON.parse(pg('select prumo_private.registrar_vinculo_meta_tecnico_fixture_s0('+
   [APP,WABA,PHONE,CHANNEL,S.id,S.attempt,S.corr,RECIPIENT,S.wamid,200]
    .map((v,i)=>i===9?'200':q(v)).join(',')+')'));
  assert.equal(b.outcome,'LAB_BOUND');
  assert.equal(state(),'BLOQUEADA_GATES');
 },
 async()=>{
  K=shadowKey();W=await worker(K);
  accepted(await post(W,body(T0)));
  await wait(()=>W.receipts.some(v=>v.event===event(T0)&&v.outcome==='LAB_OBSERVED_UNVERIFIED'),
   'original observation');
  stored=snapshot(T0);
  assert.equal(stored.length,1);
  assert.equal(nonce(K),1);
 },
 async()=>{
  const x=altered(T0,'"entry":','"object":"whatsapp_business_account","entry":');
  await noImpact(x); // exact duplicate root key, otherwise same values
 },
 async()=>{
  const x=altered(T0,'"entry":','"ob\\u006aect":"whatsapp_business_account","entry":');
  await noImpact(x); // escape alias to 'object'
 },
 async()=>{
  const x=altered(T0,'"changes":','"id":"'+WABA+'","changes":');
  await noImpact(x); // duplicate entry-level id
 },
 async()=>{
  const x=altered(T0,'"statuses":','"metadata":{"phone_number_id":"'+PHONE+'"},"statuses":');
  await noImpact(x); // duplicate nested metadata
 },
 async()=>{
  const x=altered(T0,'"recipient_id":','"status":"delivered","recipient_id":');
  await noImpact(x); // duplicate status key, same value
 },
 async()=>{
  const x=altered(T0,'"recipient_id":','"st\\u0061tus":"delivered","recipient_id":');
  await noImpact(x); // escaped status alias
 },
 async()=>{
  const x=altered(T0,'"statuses":','"statuses":[],"statuses":');
  await noImpact(x); // array-valued key repeated
 },
 async()=>{
  const x=altered(T0,'"wamid.WA67.A"','"wamid.WA67.\\ud800"');
  await noImpact(x); // escaped lone surrogate scalar
 },
 async()=>{
  const raw=body(T0),idx=raw.indexOf(Buffer.from('wamid.WA67.A'));
  assert.ok(idx>0);
  const x=Buffer.from(raw);x[idx+6]=0xff;
  await noImpact(x); // invalid UTF-8 with valid HMAC
 },
 async()=>{
  const x=Buffer.concat([Buffer.from([0xef,0xbb,0xbf]),body(T0)]);
  await noImpact(x); // signed UTF-8 BOM is prohibited
 },
 async()=>{
  const x=altered(T0,'"status":','"sta\\u200btus":');
  const before=nonce(K),prev=W.receipts.length;
  // Unicode confusable is an *unknown property*, not a duplicate.
  assert.equal(wa67StrictJsonKeys(x),true);
  denied(await post(W,x));
  assert.equal(nonce(K),before);assert.equal(W.receipts.length,prev);
  assert.deepEqual(snapshot(T0),stored);
 },
 async()=>{
  const x=altered(T0,'"object":','"ob\\u006aect":');
  assert.equal(wa67StrictJsonKeys(x),true);
  accepted(await post(W,x));
  afterAlias=snapshot(T0);
  assert.equal(afterAlias.length,2);assert.ok(afterAlias.includes(stored[0]));
  assert.equal(nonce(K),2);
 },
 async()=>{
  const x=altered(T0,'"delivered"','"\\u0064elivered"');
  assert.equal(wa67StrictJsonKeys(x),true);
  accepted(await post(W,x));
  afterScalar=snapshot(T0);
  assert.equal(afterScalar.length,3);
  assert.ok(afterScalar.includes(stored[0]));
  assert.equal(nonce(K),3);
 },
 async()=>{
  const x=altered(T0,'"id":"'+S.wamid+'","status":"delivered","recipient_id":"'+RECIPIENT+'","timestamp":"'+T0+'"',
   '"timestamp":"'+T0+'","recipient_id":"'+RECIPIENT+'","status":"delivered","id":"'+S.wamid+'"');
  assert.equal(wa67StrictJsonKeys(x),true);
  accepted(await post(W,x));
  afterReorder=snapshot(T0);
  assert.equal(afterReorder.length,4);
  assert.equal(nonce(K),4);
 },
 async()=>{
  accepted(await post(W,body(T0)));
  assert.deepEqual(snapshot(T0),afterReorder);
  assert.equal(nonce(K),5);
 },
 async()=>{
  assert.equal(pg("update prumo_private.outbox_intencoes_s0 set estado='CANCELADA' "+
   'where id='+q(S.id)+" and estado='BLOQUEADA_GATES' returning estado"),'CANCELADA');
  assert.equal(pg('select prumo_private.meta_wa48_shadow_revoke_fixture_s0('+q(K.id)+')'),'LAB_REVOKED');
  const before=nonce(K);
  denied(await post(W,body(T0)));
  assert.equal(nonce(K),before);assert.equal(active(K),'false');
  assert.deepEqual(snapshot(T0),afterReorder);
 },
 async()=>{
  await stop(W);
  K2=shadowKey();W2=await worker(K2);
  accepted(await post(W2,body(T0)));
  await wait(()=>W2.receipts.some(v=>v.event===event(T0)&&v.outcome==='LAB_EXACT_BODY_REPLAY'),
   'rotated replay');
  accepted(await post(W2,body(T1)));
  await wait(()=>W2.receipts.some(v=>v.event===event(T1)&&v.outcome==='LAB_LATE_UNVERIFIED'),
   'late observation');
  lateSnapshot=snapshot(T1);
  assert.equal(lateSnapshot.length,1);assert.equal(nonce(K2),2);
 },
 async()=>{
  await stop(W2);
  assert.equal(state(),'CANCELADA');
  assert.equal(num('prumo_private.meta_status_forense_fixture_s0'),baseline+5);
  assert.equal(count(T0),4);assert.equal(count(T1),1);
  assert.deepEqual(snapshot(T0),afterReorder);
  assert.deepEqual(snapshot(T1),lateSnapshot);
  assert.equal(nonce(K),5);assert.equal(nonce(K2),2);
  assert.equal(num('prumo_private.meta_status_conflitos_fixture_s0 where event_ref in ('+
   [event(T0),event(T1)].map(q).join(',')+')'),0);
  assert.equal(num('prumo_private.meta_wa48_shadow_receipts_fixture_s0 where key_id in ('+
   [K,K2].map(k=>q(k.id)).join(',')+')'),0);
  assert.equal(num('prumo_private.meta_status_forense_fixture_s0 where ack_allowed or send_authorized or retry_external or production_authorized or delivery_confirmed or case_transition_authorized or definitive_failure_count_increment'),0);
  assert.equal(pg("select has_function_privilege('prumo_s0_meta_wa48_client_lab',"+
   q('prumo_private.meta_wa52_locked_forensic_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)')+
   ",'EXECUTE')"),'f');
 }
];
assert.equal(tests.length,24);
for(let i=0;i<tests.length;i++)
 test('WA67-'+String(i+1).padStart(2,'0')+' strict JSON key ambiguity PG17',async()=>{
  await tests[i]();
  console.log('WA67-'+String(i+1).padStart(2,'0')+' PASS');
 });
