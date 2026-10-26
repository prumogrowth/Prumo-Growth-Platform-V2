/** WA65: 24 PG17-only assertions for byte-variant replay, status-distinct
 * event IDs, key revocation and late cancellation. No Meta API or S1.
 */
import test,{after} from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import {spawn,spawnSync} from 'node:child_process';
import {createHmac,createHash,randomBytes,randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';

const DSN=process.env.PRUMO_TEST_DATABASE_URL??'',U=new URL(DSN);
if(U.protocol!=='postgresql:'||U.hostname!=='127.0.0.1'||U.port!=='5432'||
 U.username!=='postgres'||U.pathname!=='/prumo_s0_test_ci'||U.search||U.hash)
 throw Error('WA65_DISPOSABLE_PG17_ONLY');
for(const k of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER','PGSERVICE',
 'PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT','PGSSLKEY','PGSSLROOTCERT'])
 if(process.env[k])throw Error('WA65_LIBPQ_OVERRIDE');

const APP='12346000002',WABA='22346000002',PHONE='32346000002';
const SHOP='f7200000-0000-4000-8000-000000000002';
const CHANNEL='f7300000-0000-4000-8000-000000000002';
const RECIPIENT='5581900000000',PASS=randomBytes(32).toString('hex');
const META=Buffer.alloc(48,0x4d);
const S=[
 {id:'f7400000-0000-4000-8000-000000000069',profile:'wa65-a',
  attempt:'ATTEMPT_WA65_A',corr:'CORR_WA65_A',wamid:'wamid.WA65.A'},
 {id:'f7400000-0000-4000-8000-000000000070',profile:'wa65-b',
  attempt:'ATTEMPT_WA65_B',corr:'CORR_WA65_B',wamid:'wamid.WA65.B'}
];
const TS=[0,1,2,3].map(i=>String(Math.floor(Date.now()/1000)-3200000-i*37));
const q=v=>"'"+String(v).replaceAll("'","''")+"'";
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const children=[];
after(()=>{for(const c of children)
 if(c.exitCode===null&&c.signalCode===null)c.kill('SIGKILL');
});
function pg(sql){
 const x=spawnSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
  '-v','VERBOSITY=verbose',DSN,'-c',sql],{
  encoding:'utf8',timeout:15000,env:{...process.env,PGPASSWORD:'postgres'}});
 if(x.error||x.status!==0)throw Error('WA65_SQL '+String(x.stderr).slice(-500));
 return x.stdout.trim();
}
const num=expr=>Number(pg('select count(*) from '+expr));
const state=s=>pg('select estado from prumo_private.outbox_intencoes_s0 where id='+q(s.id));
const nonce=k=>num('prumo_private.meta_wa48_shadow_nonces_fixture_s0 where key_id='+q(k.id));
const active=k=>pg('select active::text from prumo_private.meta_wa48_shadow_keys_fixture_s0 where key_id='+q(k.id));
const event=(s,ts,kind='delivered')=>'WA46_'+createHash('sha256').update(
 JSON.stringify([WABA,PHONE,s.wamid,RECIPIENT,kind,ts])).digest('hex');
const eventCount=(s,ts,kind='delivered')=>num(
 'prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(event(s,ts,kind)));
const lines=(s,ts,kind='delivered')=>pg(
 "select id::text||'|'||body_sha256||'|'||provider_status "+
 'from prumo_private.meta_status_forense_fixture_s0 where event_ref='+
 q(event(s,ts,kind))+' order by body_sha256');
const snap=(s,ts,kind='delivered')=>lines(s,ts,kind).split('\n').filter(Boolean);
const conflictCount=()=>num('prumo_private.meta_status_conflitos_fixture_s0 where event_ref in ('+
 [event(S[0],TS[0]),event(S[0],TS[0],'read'),event(S[1],TS[2]),
 event(S[1],TS[2],'failed'),event(S[1],TS[2],'read')]
 .map(q).join(',')+')');
function key(){
 const k={id:randomUUID(),secret:randomBytes(48).toString('hex')};
 pg('insert into prumo_private.meta_wa48_shadow_keys_fixture_s0('+
 'key_id,app,secret,active,valid_from,valid_until) values ('+
 q(k.id)+','+q(APP)+',decode('+q(k.secret)+
 ",'hex'),true,clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '2 hours')");
 return k;
}
async function until(predicate,tag,ms=5000){
 const limit=Date.now()+ms;
 while(Date.now()<limit){
  const got=await predicate();if(got)return got;
  await sleep(15);
 }
 assert.fail('WA65_TIMEOUT '+tag);
}
async function worker(k,s,overrideSecret=null){
 const file=join(dirname(fileURLToPath(import.meta.url)),'s0_wa_064_pg17_restart_worker.mjs');
 const child=spawn(process.execPath,[file],{env:{
  ...process.env,WA60_CLIENT_PASS:PASS,WA60_KEY_ID:k.id,
  WA60_KEY_SECRET:overrideSecret??k.secret,WA60_CRASH_MODE:'normal',
  WA61_BINDING_PROFILE:s.profile
 },stdio:['pipe','pipe','pipe']});
 children.push(child);
 const x={child,ready:null,receipts:[],err:''};let buffer='';
 child.stdout.on('data',data=>{
  buffer+=String(data);
  for(;;){
   const idx=buffer.indexOf('\n');if(idx<0)break;
   const line=buffer.slice(0,idx);buffer=buffer.slice(idx+1);
   try{
    const msg=JSON.parse(line);
    if(msg.type==='ready')x.ready=msg;
    else if(msg.type==='receipt')x.receipts.push(msg);
   }catch{x.err+='BAD_STDOUT '+line.slice(0,80);}
  }
 });
 child.stderr.on('data',v=>x.err+=String(v).slice(-250));
 await until(()=>x.ready||child.exitCode!==null||child.signalCode!==null,'worker start');
 assert.ok(x.ready,'WA65 worker failed '+x.err.slice(-250));
 assert.equal(x.ready.host,'127.0.0.1');
 assert.equal(x.ready.lab_only,true);
 return x;
}
async function stop(x){
 assert.equal(x.child.exitCode,null,'unexpected child death '+x.err);
 x.child.stdin.write('STOP\n');
 await until(()=>x.child.exitCode!==null||x.child.signalCode!==null,'child stop');
 assert.equal(x.child.exitCode,0,x.err.slice(-250));
}
function body(s,ts,{kind='delivered',variant=false,extra=false}={}){
 const status=variant
  ?{timestamp:ts,recipient_id:RECIPIENT,status:kind,id:s.wamid}
  :{id:s.wamid,status:kind,recipient_id:RECIPIENT,timestamp:ts};
 if(extra)status.untrusted_extra='NO_S0_AUTHORITY';
 return Buffer.from(JSON.stringify({object:'whatsapp_business_account',
  entry:[{id:WABA,changes:[{field:'messages',value:{
   metadata:{phone_number_id:PHONE},statuses:[status]}}]}]}));
}
function send(w,s,ts,opts={}){
 const bytes=body(s,ts,opts);
 const sig=createHmac('sha256',META).update(bytes).digest('hex');
 return new Promise(resolve=>{
  const req=http.request({host:'127.0.0.1',port:w.ready.port,
   path:w.ready.route,method:'POST',agent:false,headers:{
   'Content-Type':'application/json','Content-Length':String(bytes.length),
   'X-Hub-Signature-256':'sha256='+(opts.badSig?'0'.repeat(64):sig)
  }},res=>{
   const chunks=[];res.on('data',chunk=>chunks.push(chunk));
   res.on('end',()=>{
    try{resolve({status:res.statusCode,body:JSON.parse(Buffer.concat(chunks).toString())});}
    catch{resolve({status:res.statusCode,unreadable:true});}
   });
  });
  req.on('error',e=>resolve({broken:true,error:String(e.code??e.message)}));
  req.setTimeout(6800,()=>req.destroy(Error('WA65_HTTP_TIMEOUT')));
  req.end(bytes);
 });
}
function noAuthority(x){
 assert.equal(x.body?.lab_only,true);
 assert.equal(x.body?.meta_ack_emitted,false);
 assert.equal(x.body?.ack_allowed,false);
 assert.equal(x.body?.send_authorized,false);
}
const accepted=x=>{assert.equal(x.status,202,JSON.stringify(x));noAuthority(x);};
const denied=x=>{assert.equal(x.status,403,JSON.stringify(x));noAuthority(x);};
async function receipt(w,s,ts,kind,outcome){
 await until(()=>w.receipts.some(v=>v.event===event(s,ts,kind)&&v.outcome===outcome),
  'receipt '+kind+' '+outcome);
}
const revoke=k=>pg('select prumo_private.meta_wa48_shadow_revoke_fixture_s0('+q(k.id)+')');

let base,kA1,kA2,kA3,kB1,kB2,kB3,W1,W2,W3,X1,X2,X3,WBad;
let originA,variantA,readA,lateA,originalB,variantB,failedB,readB,lateB;
const tests=[
 async()=>{
  assert.equal(pg('select current_database()'),'prumo_s0_test_ci');
  assert.equal(state({id:'f7400000-0000-4000-8000-000000000002'}),'CANCELADA');
  pg('alter role prumo_s0_meta_wa48_client_lab login password '+q(PASS));
  base=num('prumo_private.meta_status_forense_fixture_s0');
  for(let i=0;i<S.length;i++){
   const scope=S[i];
   assert.equal(num('prumo_private.outbox_intencoes_s0 where id='+q(scope.id)),0);
   pg('insert into prumo_private.outbox_intencoes_s0('+
    'id,concessionaria_id,canal_id,contrato,chave_idempotencia,versao_estado_sintetica) values('+
    [scope.id,SHOP,CHANNEL,'C03','WA65_'+i,1].map(q).join(',')+')');
   const result=JSON.parse(pg('select prumo_private.registrar_vinculo_meta_tecnico_fixture_s0('+
    [APP,WABA,PHONE,CHANNEL,scope.id,scope.attempt,scope.corr,
     RECIPIENT,scope.wamid,200].map((v,j)=>j===9?'200':q(v)).join(',')+')'));
   assert.equal(result.outcome,'LAB_BOUND',JSON.stringify(result));
   assert.equal(state(scope),'BLOQUEADA_GATES');
  }
  for(const ts of TS)assert.ok(/^[0-9]+$/.test(ts));
  assert.equal(eventCount(S[0],TS[0]),0);
  assert.equal(eventCount(S[1],TS[2]),0);
 },
 async()=>{kA1=key();kA2=key();kA3=key();W1=await worker(kA1,S[0]);W2=await worker(kA2,S[0]);},
 async()=>{
  accepted(await send(W1,S[0],TS[0]));
  await receipt(W1,S[0],TS[0],'delivered','LAB_OBSERVED_UNVERIFIED');
  originA=snap(S[0],TS[0]);assert.equal(originA.length,1);
  assert.equal(nonce(kA1),1);assert.equal(nonce(kA2),0);
 },
 async()=>{
  accepted(await send(W2,S[0],TS[0],{variant:true}));
  await receipt(W2,S[0],TS[0],'delivered','LAB_BODY_VARIANT_QUARANTINED');
  variantA=snap(S[0],TS[0]);
  assert.equal(variantA.length,2);
  assert.equal(new Set(variantA.map(v=>v.split('|')[1])).size,2);
  assert.ok(variantA.includes(originA[0]));
  assert.equal(nonce(kA1),1);assert.equal(nonce(kA2),1);
 },
 async()=>{
  accepted(await send(W2,S[0],TS[0],{variant:true}));
  await receipt(W2,S[0],TS[0],'delivered','LAB_EXACT_BODY_REPLAY');
  assert.deepEqual(snap(S[0],TS[0]),variantA);
  assert.equal(nonce(kA2),2);
 },
 async()=>{
  const other=event(S[0],TS[0],'read');
  assert.notEqual(other,event(S[0],TS[0]));
  accepted(await send(W2,S[0],TS[0],{kind:'read'}));
  await receipt(W2,S[0],TS[0],'read','LAB_OBSERVED_UNVERIFIED');
  readA=snap(S[0],TS[0],'read');
  assert.equal(readA.length,1);
  assert.equal(eventCount(S[0],TS[0]),2);
  assert.equal(conflictCount(),0);
 },
 async()=>{
  const n1=nonce(kA1),length=W1.receipts.length;
  denied(await send(W1,S[0],TS[0],{badSig:true}));
  assert.equal(nonce(kA1),n1);
  assert.equal(W1.receipts.length,length);
  assert.deepEqual(snap(S[0],TS[0]),variantA);
 },
 async()=>{
  const n2=nonce(kA2),length=W2.receipts.length;
  denied(await send(W2,S[0],TS[0],{extra:true}));
  assert.equal(nonce(kA2),n2);
  assert.equal(W2.receipts.length,length);
  assert.equal(conflictCount(),0);
 },
 async()=>{
  assert.equal(pg("update prumo_private.outbox_intencoes_s0 set estado='CANCELADA' where id="+
   q(S[0].id)+" and estado='BLOQUEADA_GATES' returning estado"),'CANCELADA');
  assert.deepEqual(snap(S[0],TS[0]),variantA);
  assert.deepEqual(snap(S[0],TS[0],'read'),readA);
 },
 async()=>{
  W3=await worker(kA3,S[0]);
  accepted(await send(W3,S[0],TS[1]));
  await receipt(W3,S[0],TS[1],'delivered','LAB_LATE_UNVERIFIED');
  lateA=snap(S[0],TS[1]);assert.equal(lateA.length,1);
  accepted(await send(W3,S[0],TS[0]));
  await receipt(W3,S[0],TS[0],'delivered','LAB_EXACT_BODY_REPLAY');
  assert.deepEqual(snap(S[0],TS[0]),variantA);
  assert.equal(nonce(kA3),2);
 },
 async()=>{
  assert.equal(revoke(kA1),'LAB_REVOKED');assert.equal(active(kA1),'false');
  const before=nonce(kA1);
  denied(await send(W1,S[0],TS[0]));
  assert.equal(nonce(kA1),before);
  accepted(await send(W2,S[0],TS[0],{kind:'read'}));
  await receipt(W2,S[0],TS[0],'read','LAB_EXACT_BODY_REPLAY');
  assert.deepEqual(snap(S[0],TS[0],'read'),readA);
 },
 async()=>{
  WBad=await worker(kA2,S[0],kA1.secret);
  const n=nonce(kA2);
  denied(await send(WBad,S[0],TS[0]));
  assert.equal(nonce(kA2),n);
  assert.deepEqual(snap(S[0],TS[0]),variantA);
  await stop(WBad);
 },
 async()=>{
  await stop(W1);await stop(W2);await stop(W3);
  assert.equal(state(S[0]),'CANCELADA');
  assert.equal(eventCount(S[0],TS[0]),2);
  assert.equal(eventCount(S[0],TS[0],'read'),1);
  assert.equal(eventCount(S[0],TS[1]),1);
  assert.equal(conflictCount(),0);
  assert.deepEqual(snap(S[0],TS[1]),lateA);
 },
 async()=>{
  assert.equal(pg("update prumo_private.outbox_intencoes_s0 set estado='CANCELADA' where id="+
   q(S[1].id)+" and estado='BLOQUEADA_GATES' returning estado"),'CANCELADA');
  kB1=key();kB2=key();kB3=key();
  X1=await worker(kB1,S[1]);X2=await worker(kB2,S[1]);
  assert.equal(eventCount(S[1],TS[2]),0);
 },
 async()=>{
  const [a,b]=await Promise.all([send(X1,S[1],TS[2]),send(X2,S[1],TS[2])]);
  accepted(a);accepted(b);
  await until(()=>X1.receipts.some(v=>v.event===event(S[1],TS[2]))&&
   X2.receipts.some(v=>v.event===event(S[1],TS[2])),'dual cross-key receipts');
  const outcomes=[...X1.receipts,...X2.receipts].filter(v=>v.event===event(S[1],TS[2])).map(v=>v.outcome);
  assert.deepEqual(outcomes.sort(),['LAB_EXACT_BODY_REPLAY','LAB_LATE_UNVERIFIED'].sort());
  originalB=snap(S[1],TS[2]);
  assert.equal(originalB.length,1);
  assert.equal(nonce(kB1),1);assert.equal(nonce(kB2),1);
 },
 async()=>{
  accepted(await send(X1,S[1],TS[2],{variant:true}));
  await receipt(X1,S[1],TS[2],'delivered','LAB_BODY_VARIANT_QUARANTINED');
  variantB=snap(S[1],TS[2]);
  assert.equal(variantB.length,2);
  assert.ok(variantB.includes(originalB[0]));
  assert.equal(nonce(kB1),2);
 },
 async()=>{
  assert.notEqual(event(S[1],TS[2],'failed'),event(S[1],TS[2]));
  accepted(await send(X2,S[1],TS[2],{kind:'failed'}));
  await receipt(X2,S[1],TS[2],'failed','LAB_LATE_UNVERIFIED');
  failedB=snap(S[1],TS[2],'failed');
  assert.equal(failedB.length,1);
  assert.equal(conflictCount(),0);
 },
 async()=>{
  accepted(await send(X2,S[1],TS[2],{kind:'failed'}));
  await receipt(X2,S[1],TS[2],'failed','LAB_EXACT_BODY_REPLAY');
  accepted(await send(X2,S[1],TS[2],{variant:true}));
  await receipt(X2,S[1],TS[2],'delivered','LAB_EXACT_BODY_REPLAY');
  assert.deepEqual(snap(S[1],TS[2]),variantB);
 },
 async()=>{
  assert.equal(revoke(kB1),'LAB_REVOKED');
  const n=nonce(kB1),len=X1.receipts.length;
  denied(await send(X1,S[1],TS[2],{variant:true}));
  denied(await send(X1,S[1],TS[2]));
  assert.equal(nonce(kB1),n);assert.equal(X1.receipts.length,len);
  assert.equal(active(kB2),'true');
 },
 async()=>{
  accepted(await send(X2,S[1],TS[2],{kind:'read'}));
  await receipt(X2,S[1],TS[2],'read','LAB_LATE_UNVERIFIED');
  readB=snap(S[1],TS[2],'read');
  assert.equal(readB.length,1);
  const n=nonce(kB2);
  denied(await send(X2,S[0],TS[0]));
  assert.equal(nonce(kB2),n);
 },
 async()=>{
  X3=await worker(kB3,S[1]);
  accepted(await send(X3,S[1],TS[2],{variant:true}));
  await receipt(X3,S[1],TS[2],'delivered','LAB_EXACT_BODY_REPLAY');
  accepted(await send(X3,S[1],TS[3]));
  await receipt(X3,S[1],TS[3],'delivered','LAB_LATE_UNVERIFIED');
  lateB=snap(S[1],TS[3]);assert.equal(lateB.length,1);
  assert.equal(nonce(kB3),2);
  assert.deepEqual(snap(S[1],TS[2]),variantB);
 },
 async()=>{
  const n=nonce(kB3),len=X3.receipts.length;
  denied(await send(X3,S[1],TS[3],{extra:true}));
  denied(await send(X3,S[1],TS[3],{badSig:true}));
  assert.equal(nonce(kB3),n);
  assert.equal(X3.receipts.length,len);
 },
 async()=>{
  assert.equal(revoke(kB2),'LAB_REVOKED');
  await stop(X1);await stop(X2);
  const restarted=await worker(kB2,S[1]);
  denied(await send(restarted,S[1],TS[2],{kind:'failed'}));
  assert.deepEqual(snap(S[1],TS[2],'failed'),failedB);
  await stop(restarted);await stop(X3);
  assert.equal(state(S[1]),'CANCELADA');
  assert.equal(conflictCount(),0);
 },
 async()=>{
  assert.equal(num('prumo_private.meta_status_forense_fixture_s0'),base+9);
  assert.equal(eventCount(S[0],TS[0]),2);
  assert.equal(eventCount(S[0],TS[0],'read'),1);
  assert.equal(eventCount(S[0],TS[1]),1);
  assert.equal(eventCount(S[1],TS[2]),2);
  assert.equal(eventCount(S[1],TS[2],'failed'),1);
  assert.equal(eventCount(S[1],TS[2],'read'),1);
  assert.equal(eventCount(S[1],TS[3]),1);
  assert.deepEqual(snap(S[0],TS[0]),variantA);
  assert.deepEqual(snap(S[0],TS[0],'read'),readA);
  assert.deepEqual(snap(S[0],TS[1]),lateA);
  assert.deepEqual(snap(S[1],TS[2]),variantB);
  assert.deepEqual(snap(S[1],TS[2],'failed'),failedB);
  assert.deepEqual(snap(S[1],TS[2],'read'),readB);
  assert.deepEqual(snap(S[1],TS[3]),lateB);
  assert.equal(nonce(kA1),1);assert.equal(nonce(kB1),2);
  assert.equal(nonce(kA3),2);assert.equal(nonce(kB3),2);
  assert.equal(active(kA1),'false');assert.equal(active(kB1),'false');assert.equal(active(kB2),'false');
  assert.equal(state(S[0]),'CANCELADA');assert.equal(state(S[1]),'CANCELADA');
  assert.equal(conflictCount(),0);
  const ids=[kA1,kA2,kA3,kB1,kB2,kB3].map(k=>q(k.id)).join(',');
  assert.equal(num('prumo_private.meta_wa48_shadow_receipts_fixture_s0 where key_id in ('+ids+')'),0);
  assert.equal(num('prumo_private.meta_status_forense_fixture_s0 where ack_allowed or send_authorized or retry_external or production_authorized or delivery_confirmed or case_transition_authorized or definitive_failure_count_increment'),0);
  assert.equal(pg("select has_function_privilege('prumo_s0_meta_wa48_client_lab',"+
   q('prumo_private.meta_wa52_locked_forensic_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)')+
   ",'EXECUTE')"),'f');
 }
];
assert.equal(tests.length,24);
for(let i=0;i<tests.length;i++)
 test('WA65-'+String(i+1).padStart(2,'0')+' cross-key byte variant and status arbitration PG17',async()=>{
  await tests[i]();console.log('WA65-'+String(i+1).padStart(2,'0')+' PASS');
 });
