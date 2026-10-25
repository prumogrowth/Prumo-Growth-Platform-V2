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
 !['normal','precommit','postcommit'].includes(mode))
 throw Error('WA60_WORKER_BAD_CONFIG');
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
 secretSlot:'WA60_TEST_SECRET_ONLY',enabled:true});
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
const q=x=>"'"+String(x).replaceAll("'","''")+"'";
const boundary=createWa45OfflineBoundary({
 getRegistry:async()=>R,lookupBinding:async()=>B,
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
  const receipt=JSON.parse(await sql(
   'select prumo_private.meta_wa55_single_entry_fixture_s0('+args+')'));
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
 if(data.trim()==='STOP'){
  await server.stop();
  process.exit(0);
 }
});
