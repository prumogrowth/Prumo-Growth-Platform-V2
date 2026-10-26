/** WA60 only: standalone disposable Node child, NEVER a hosted Meta service.
 * One process = one ephemeral localhost listener, no public bind, no ACK.
 * Env fixtures come exclusively from the parent PG17 integration test.
 */
import {createWa57OfflineLoopback} from './s0_wa_061_meta_http_loopback_transport.mjs';
import {createWa56OfflineArchiveBridge} from './s0_wa_060_meta_raw_to_pg17_bridge.mjs';
import {createWa46OfflineMetaGate} from './s0_wa_050_meta_raw_hmac_gate.mjs';
import {createWa45OfflineBoundary} from './s0_wa_049_meta_trusted_boundary.mjs';
import {spawn} from 'node:child_process';
import {randomUUID} from 'node:crypto';

const env=process.env,ds=env.PRUMO_TEST_DATABASE_URL??'';
const u=new URL(ds);
if(u.protocol!=='postgresql:'||u.hostname!=='127.0.0.1'||u.port!=='5432'||
 u.username!=='postgres'||u.pathname!=='/prumo_s0_test_ci'||u.search||u.hash)
 throw Error('WA60_WORKER_LOCAL_PG17_ONLY');
for(const key of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER','PGSERVICE',
 'PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT','PGSSLKEY','PGSSLROOTCERT'])
 if(env[key])throw Error('WA60_WORKER_LIBPQ_OVERRIDE');
const keyId=env.WA60_KEY_ID,secretHex=env.WA60_KEY_SECRET,
 password=env.WA60_CLIENT_PASS,mode=env.WA60_CRASH_MODE??'normal';
if(!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(keyId??'')||
 !/^[a-f0-9]{96}$/.test(secretHex??'')||
 !/^[a-f0-9]{64}$/.test(password??'')||
 !['normal','precommit','postcommit','holdcommit','holdrollback'].includes(mode))
 throw Error('WA60_WORKER_BAD_CONFIG');
// WA61 process-local fixture drift, never a real S0 binding update.
const profile=env.WA61_BINDING_PROFILE??'current';
if(!['current','stale-attempt','disabled-route','wa63-a','wa63-b','wa63-c','wa64-a','wa64-b','wa64-c','wa65-a','wa65-b'].includes(profile))
 throw Error('WA61_WORKER_PROFILE_DENIED');
const INTERNAL=Buffer.from(secretHex,'hex'),META=Buffer.alloc(48,0x4d);
const NOW=()=>Math.floor(Date.now()/1000);
const R=Object.freeze({appTechnical:'12346000002',wabaTechnical:'22346000002',
 phoneTechnical:'32346000002',appRef:'FIXTURE_WA40_B',tenantRef:'SHOP_WA40_B',
 channelRef:'f7300000-0000-4000-8000-000000000002'});
const B=Object.freeze({appRef:R.appRef,tenantRef:R.tenantRef,channelRef:R.channelRef,
 intentRef:'f7400000-0000-4000-8000-000000000002',attemptRef:'ATTEMPT_B',
 correlationRef:'CORR_B',recipient:'5581900000000',wamid:'wamid.WA40.SHARED',
 bindingRevision:3});
const REG=Object.freeze({routeRef:'WA60_LOOPBACK',revision:1,...R,
 secretSlot:'WA60_TEST_SECRET_ONLY',enabled:profile!=='disabled-route'});
// WA63: independent fresh synthetic S0 intent per triple-race ordering.
const WA63_BINDINGS=Object.freeze({
 'wa63-a':Object.freeze({...B,intentRef:'f7400000-0000-4000-8000-000000000063',
  attemptRef:'ATTEMPT_WA63_A',correlationRef:'CORR_WA63_A',wamid:'wamid.WA63.A'}),
 'wa63-b':Object.freeze({...B,intentRef:'f7400000-0000-4000-8000-000000000064',
  attemptRef:'ATTEMPT_WA63_B',correlationRef:'CORR_WA63_B',wamid:'wamid.WA63.B'}),
 'wa63-c':Object.freeze({...B,intentRef:'f7400000-0000-4000-8000-000000000065',
  attemptRef:'ATTEMPT_WA63_C',correlationRef:'CORR_WA63_C',wamid:'wamid.WA63.C'})
});
// WA64 synthetic fixtures: two independently signed events share each
// authoritative S0 intent, without remapping a historical binding.
const WA64_BINDINGS=Object.freeze({
 'wa64-a':Object.freeze({...B,intentRef:'f7400000-0000-4000-8000-000000000066',
  attemptRef:'ATTEMPT_WA64_A',correlationRef:'CORR_WA64_A',wamid:'wamid.WA64.A'}),
 'wa64-b':Object.freeze({...B,intentRef:'f7400000-0000-4000-8000-000000000067',
  attemptRef:'ATTEMPT_WA64_B',correlationRef:'CORR_WA64_B',wamid:'wamid.WA64.B'}),
 'wa64-c':Object.freeze({...B,intentRef:'f7400000-0000-4000-8000-000000000068',
  attemptRef:'ATTEMPT_WA64_C',correlationRef:'CORR_WA64_C',wamid:'wamid.WA64.C'})
});
// WA65 isolates cross-key replay, byte-different bodies and status IDs.
const WA65_BINDINGS=Object.freeze({
 'wa65-a':Object.freeze({...B,intentRef:'f7400000-0000-4000-8000-000000000069',
  attemptRef:'ATTEMPT_WA65_A',correlationRef:'CORR_WA65_A',wamid:'wamid.WA65.A'}),
 'wa65-b':Object.freeze({...B,intentRef:'f7400000-0000-4000-8000-000000000070',
  attemptRef:'ATTEMPT_WA65_B',correlationRef:'CORR_WA65_B',wamid:'wamid.WA65.B'})
});
const ACTIVE_BINDING=WA65_BINDINGS[profile]??WA64_BINDINGS[profile]??WA63_BINDINGS[profile]??(profile==='stale-attempt'
 ?Object.freeze({...B,attemptRef:'ATTEMPT_WA61_STALE'}):B);
function sql(q){
 return new Promise((resolve,reject)=>{
  const client='postgresql://prumo_s0_meta_wa48_client_lab@127.0.0.1:5432/prumo_s0_test_ci';
  const p=spawn('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
   '-v','VERBOSITY=verbose',client,'-c',q],
   {env:{...env,PGPASSWORD:password},stdio:['ignore','pipe','pipe']});
  let text='',err='';
  p.stdout.on('data',b=>text+=b);
  p.stderr.on('data',b=>err+=b);
  p.on('error',reject);
  p.on('close',status=>status===0?resolve(text.trim()):
   reject(Error('WA60_WORKER_PG_FAILED '+err.slice(-300))));
 });
}
// WA62 standalone PG17-only transaction barrier: no receipt/HTTP success
// until an explicit COMMIT; ROLLBACK rejects and rolls back the nonce/append.
let pendingWa62Release=null;
function sqlHeld(statement,eventRef){
 return new Promise((resolve,reject)=>{
  const client='postgresql://prumo_s0_meta_wa48_client_lab@127.0.0.1:5432/prumo_s0_test_ci';
  const p=spawn('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
   '-v','VERBOSITY=verbose',client],{
   env:{...env,PGPASSWORD:password},stdio:['pipe','pipe','pipe']});
  let output='',err='',receipt=null,held=false,decision=null,settled=false;
  const fail=reason=>{if(!settled){settled=true;reject(reason);}};
  p.stderr.on('data',b=>err+=String(b));
  p.stdout.on('data',chunk=>{
   output+=String(chunk);
   for(;;){
    const pos=output.indexOf('\n');if(pos<0)break;
    const line=output.slice(0,pos).trim();output=output.slice(pos+1);
    if(!receipt){
     try{const v=JSON.parse(line);
      if(v&&v.lab_only===true){receipt=v;continue;}
     }catch{}
    }
    const match=/^([0-9]+)\|WA62_HELD$/.exec(line);
    if(match&&receipt&&!held){
     held=true;
     pendingWa62Release=verb=>{
      if(decision||!['COMMIT','ROLLBACK'].includes(verb))return;
      decision=verb;
      p.stdin.write(verb+';\n\\q\n');
     };
     process.stdout.write(JSON.stringify({type:'wa62-held',pid:process.pid,
      db_pid:Number(match[1]),event:eventRef,outcome:receipt.outcome})+'\n');
    }
   }
  });
  p.on('error',fail);
  p.on('close',status=>{
   pendingWa62Release=null;
   if(status===0&&held&&decision==='COMMIT'&&receipt){
    if(!settled){settled=true;resolve(JSON.stringify(receipt));}
   }else fail(Error('WA62_HELD_SQL_ABORT '+status+' '+err.slice(-250)));
  });
  p.stdin.write('BEGIN;\n'+statement+';\n'+
   "SELECT pg_catalog.pg_backend_pid()::text||'|WA62_HELD';\n");
 });
}
const q=x=>"'"+String(x).replaceAll("'","''")+"'";
const boundary=createWa45OfflineBoundary({
 getRegistry:async()=>R,lookupBinding:async()=>ACTIVE_BINDING,
 getInternalKey:async()=>Buffer.from(INTERNAL),newNonce:async()=>randomUUID(),
 nowSeconds:NOW
},keyId);

const gate=createWa46OfflineMetaGate({
 getRegistry:async()=>REG,getMetaAppSecret:async()=>Buffer.from(META),
 nowSeconds:NOW,wa45Boundary:boundary
},REG.routeRef);
const bridge=createWa56OfflineArchiveBridge({
 rawGate:gate,getInternalKey:async()=>Buffer.from(INTERNAL),nowSeconds:NOW,
 appendWa55:async ticket=>{
  if(mode==='precommit')process.kill(process.pid,'SIGKILL');
  const args=[...ticket.candidate,ticket.macSha256]
   .map((v,i)=>i===13?String(Number(v)):q(v)).join(',');
  const statement='select prumo_private.meta_wa55_single_entry_fixture_s0('+args+')';
  const receipt=JSON.parse(await (
   mode==='holdcommit'||mode==='holdrollback'
    ?sqlHeld(statement,ticket.candidate[10]):sql(statement)));
  // Evidence only on the PRIVATE test process stdout; never in the HTTP reply.
  process.stdout.write(JSON.stringify({type:'receipt',pid:process.pid,
   event:ticket.candidate[10],outcome:receipt.outcome})+'\n');
  if(mode==='postcommit')process.kill(process.pid,'SIGKILL');
  return receipt;
 }
});
if(!boundary||!gate||!bridge)throw Error('WA60_WORKER_BAD_BRIDGE');
const server=createWa57OfflineLoopback({bridge});
if(!server)throw Error('WA60_WORKER_LISTENER_FAILED');
const addr=await server.start();
process.stdout.write(JSON.stringify({type:'ready',pid:process.pid,
 host:addr.host,port:addr.port,route:addr.route,lab_only:true})+'\n');
process.stdin.setEncoding('utf8');
process.stdin.on('data',async data=>{
 const command=data.trim();
 if(((command==='COMMIT'&&mode==='holdcommit')||
      (command==='ROLLBACK'&&mode==='holdrollback'))&&pendingWa62Release){
  pendingWa62Release(command);return;
 }
 if(command==='STOP'){
  await server.stop();
  process.exit(0);
 }
});
