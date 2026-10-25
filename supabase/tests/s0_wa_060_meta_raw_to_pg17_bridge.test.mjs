/** WA56: adversarial raw-Meta-to-WA55 bridge; synthetic only. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash,createHmac,randomBytes,randomUUID} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {createWa45OfflineBoundary} from './s0_wa_049_meta_trusted_boundary.mjs';
import {createWa46OfflineMetaGate} from './s0_wa_050_meta_raw_hmac_gate.mjs';
import {createWa56OfflineArchiveBridge} from './s0_wa_060_meta_raw_to_pg17_bridge.mjs';
const INTERNAL=Buffer.alloc(48,0x61),APP_SECRET=Buffer.alloc(48,0x4d);
const KEY=randomUUID(),ROUTE='WA56_ROUTE';
const R=Object.freeze({appTechnical:'12346000002',wabaTechnical:'22346000002',
 phoneTechnical:'32346000002',appRef:'FIXTURE_WA40_B',tenantRef:'SHOP_WA40_B',
 channelRef:'f7300000-0000-4000-8000-000000000002'});
const B=Object.freeze({appRef:R.appRef,tenantRef:R.tenantRef,channelRef:R.channelRef,
 intentRef:'f7400000-0000-4000-8000-000000000002',attemptRef:'ATTEMPT_B',
 correlationRef:'CORR_B',recipient:'5581900000000',wamid:'wamid.WA40.SHARED',
 bindingRevision:3});
const REG=Object.freeze({routeRef:ROUTE,revision:1,...R,secretSlot:'WA56_APP_SECRET',enabled:true});
const NOW=Math.floor(Date.now()/1000);
function rawMeta(overrides={}){
 const status={id:B.wamid,status:'delivered',recipient_id:B.recipient,timestamp:String(NOW),...overrides};
 return Buffer.from(JSON.stringify({object:'whatsapp_business_account',
  entry:[{id:R.wabaTechnical,changes:[{field:'messages',
   value:{metadata:{phone_number_id:R.phoneTechnical},statuses:[status]}}]}]}));
}
const header=raw=> 'sha256='+createHmac('sha256',APP_SECRET).update(raw).digest('hex');
const RECEIPT=Object.freeze({outcome:'LAB_OBSERVED_UNVERIFIED',lab_only:true,
 authoritative_lab_forensic_appended:true,original_wa39_owner_preserved:true,
 service_authenticated:false,production_authorized:false,ack_allowed:false,
 send_authorized:false,retry_external:false,delivery_confirmed:false,
 case_transition_authorized:false,definitive_failure_count_increment:false,
 entrypoint:'WA55_PG17_SINGLE_LAB_ONLY',legacy_paths_directly_executable:false,
 runtime_principal_authenticated:false});
function setup(override={}){
 const raw=rawMeta();
 const wa45=createWa45OfflineBoundary({
  getRegistry:async()=>R,lookupBinding:async()=>B,
  getInternalKey:async()=>Buffer.from(INTERNAL),
  newNonce:async()=>randomUUID(),nowSeconds:()=>NOW},KEY);
 const gate=createWa46OfflineMetaGate({
  getRegistry:async()=>REG,getMetaAppSecret:async()=>Buffer.from(APP_SECRET),
  nowSeconds:()=>NOW,wa45Boundary:wa45},ROUTE);
 assert.ok(gate);
 const write=override.appendWa55??(async()=>({...RECEIPT}));
 const bridge=createWa56OfflineArchiveBridge({
  rawGate:override.rawGate??gate,
  getInternalKey:override.getInternalKey??(async()=>Buffer.from(INTERNAL)),
  appendWa55:write,nowSeconds:override.nowSeconds??(()=>NOW)});
 assert.ok(bridge);
 return {raw,bridge,gate};
}
async function use(override={},raw=rawMeta(),sig=header(raw)){
 return setup(override).bridge.receive(raw,sig);
}
function fail(x){assert.equal(x.receipt,null);for(const k of
 ['service_authenticated','meta_provenance_production_proven','ack_allowed',
  'send_authorized','retry_external','production_authorized',
  'delivery_confirmed','case_transition_authorized'])assert.equal(x[k],false,k);}
function mutateGate(fn){
 const gate=setup().gate;
 return {receive:async(...args)=>fn(await gate.receive(...args))};
}
const checks=[
 async()=>{const r=await use();assert.equal(r.decision,'LAB_META_RAW_TO_WA55_FORENSIC_ONLY');assert.equal(r.receipt.entrypoint,'WA55_PG17_SINGLE_LAB_ONLY');},
 async()=>{const r=await use();for(const x of ['service_authenticated','meta_provenance_production_proven','ack_allowed','send_authorized','retry_external','production_authorized','delivery_confirmed','case_transition_authorized'])assert.equal(r[x],false,x);},
 async()=>{const raw=rawMeta();raw[raw.length-2]^=1;fail(await use({},raw,header(rawMeta())));},
 async()=>{const raw=rawMeta();fail(await use({},raw,'sha256='+'0'.repeat(64)));},
 async()=>{const raw=rawMeta();fail(await use({},raw,'sha1='+header(raw).slice(7)));},
 async()=>{fail(await use({},Buffer.from('invalid'),header(Buffer.from('invalid'))));},
 async()=>{fail(await use({},Buffer.alloc(262145),header(Buffer.alloc(262145))));},
 async()=>{fail(await use({},Buffer.from([255,254]),header(Buffer.from([255,254]))));},
 async()=>{const raw=rawMeta({id:'wamid.FORGED'});fail(await use({},raw));},
 async()=>{const raw=rawMeta({recipient_id:'5581999999999'});fail(await use({},raw));},
 async()=>{const raw=rawMeta({status:'unknown'});fail(await use({},raw));},
 async()=>{const raw=rawMeta({timestamp:'1'});const x=await use({},raw);assert.equal(x.receipt!==null,true);}, // fixture accepts legitimate old provider timestamps
 async()=>{const r=await use({getInternalKey:async()=>Buffer.alloc(48,0x3f)});assert.equal(r.decision,'LAB_TICKET_MAC_DENIED');fail(r);},
 async()=>{const r=await use({getInternalKey:async()=>Buffer.alloc(4)});assert.equal(r.decision,'LAB_KEY_UNAVAILABLE');},
 async()=>{const r=await use({getInternalKey:async()=>{throw Error('vault')}});assert.equal(r.decision,'LAB_UNAVAILABLE');},
 async()=>{const r=await use({appendWa55:async()=>{throw Error('PG unavailable')}});assert.equal(r.decision,'LAB_UNAVAILABLE');},
 async()=>{const r=await use({appendWa55:async()=>({...RECEIPT,ack_allowed:true})});assert.equal(r.decision,'LAB_RECEIPT_UNTRUSTED');},
 async()=>{const r=await use({appendWa55:async()=>({...RECEIPT,service_authenticated:true})});assert.equal(r.decision,'LAB_RECEIPT_UNTRUSTED');},
 async()=>{const r=await use({appendWa55:async()=>({...RECEIPT,entrypoint:'OLD'})});assert.equal(r.decision,'LAB_RECEIPT_UNTRUSTED');},
 async()=>{const r=await use({appendWa55:async()=>({...RECEIPT,outcome:'ACCEPTED'})});assert.equal(r.decision,'LAB_RECEIPT_UNTRUSTED');},
 async()=>{const r=await use({nowSeconds:()=>NOW+40});assert.equal(r.decision,'LAB_STALE');},
 async()=>{const r=await use({rawGate:mutateGate(x=>({...x,ack_allowed:true}))});assert.equal(r.decision,'LAB_META_GATE_DENIED');},
 async()=>{const r=await use({rawGate:mutateGate(x=>({...x,ticket:{...x.ticket,macSha256:'0'.repeat(64)}}))});assert.equal(r.decision,'LAB_TICKET_MAC_DENIED');},
 async()=>{const r=await use({rawGate:mutateGate(x=>({...x,ticket:{...x.ticket,candidate:Object.freeze(x.ticket.candidate.map((v,i)=>i===12?'0'.repeat(64):v))}}))});assert.equal(r.decision,'LAB_WIRE_MISMATCH');},
 async()=>{const r=await use({rawGate:mutateGate(x=>({...x,ticket:{...x.ticket,candidate:Object.freeze(x.ticket.candidate.map((v,i)=>i===5?randomUUID():v))}}))});assert.equal(r.decision,'LAB_TICKET_MAC_DENIED');},
 async()=>{const r=await use({rawGate:mutateGate(x=>({...x,ticket:{...x.ticket,contract:'WA34'}}))});assert.equal(r.decision,'LAB_TICKET_DENIED');},
 async()=>{const r=await use({rawGate:mutateGate(x=>({...x,ticket:{...x.ticket,extra:true}}))});assert.equal(r.decision,'LAB_TICKET_DENIED');},
 async()=>{let captured;const raw=rawMeta(),sig=header(raw);const p=setup({appendWa55:async t=>{captured=t;return {...RECEIPT};}});const work=p.bridge.receive(raw,sig);raw.fill(0);const result=await work;assert.equal(result.decision,'LAB_META_RAW_TO_WA55_FORENSIC_ONLY');assert.ok(Object.isFrozen(captured.candidate));},
 async()=>{const raw=rawMeta();let wrote=0;const p=setup({appendWa55:async t=>{wrote++;assert.equal(t.candidate[12],createHash('sha256').update(raw).digest('hex'));return {...RECEIPT};}});await p.bridge.receive(raw,header(raw));assert.equal(wrote,1);},
];

const DSN=process.env.PRUMO_TEST_DATABASE_URL;
function db(sql,client=false,password=null){
 if(typeof DSN!=='string')throw Error('WA56 disposable URL required');
 const u=new URL(DSN);
 if(u.protocol!=='postgresql:'||u.hostname!=='127.0.0.1'||u.port!=='5432'||
 u.username!=='postgres'||u.pathname!=='/prumo_s0_test_ci'||u.search||u.hash)
  throw Error('WA56 refuses non-disposable DB');
 for(const k of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER',
  'PGSERVICE','PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT','PGSSLKEY','PGSSLROOTCERT'])
  if(process.env[k])throw Error('WA56 libpq override '+k);
 const dsn=client?'postgresql://prumo_s0_meta_wa48_client_lab@127.0.0.1:5432/prumo_s0_test_ci':DSN;
 const proc=spawnSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
  '-v','VERBOSITY=verbose',dsn,'-c',sql],
  {encoding:'utf8',timeout:12000,env:{...process.env,PGPASSWORD:client?password:'postgres'}});
 if(proc.error)throw proc.error;
 if(proc.status!==0)throw Error('WA56 PG failure '+proc.stderr.slice(-650));
 return proc.stdout.trim();
}
const q=x=>"'"+String(x).replaceAll("'","''")+"'";
const DATABASE_PASSWORD=randomBytes(32).toString('hex');
const DB_KEY=randomUUID(),DB_INTERNAL=randomBytes(48);
let physicalGate;
let physicalRaw;
let physicalPass;
function setupPhysical(){
 db("alter role prumo_s0_meta_wa48_client_lab login password "+q(DATABASE_PASSWORD));
 db("insert into prumo_private.meta_wa48_shadow_keys_fixture_s0"+
  "(key_id,app,secret,active,valid_from,valid_until) values("+
  q(DB_KEY)+","+q(R.appTechnical)+",decode("+q(DB_INTERNAL.toString('hex'))+
  ",'hex'),true,clock_timestamp()-interval '2 minutes',"+
  "clock_timestamp()+interval '1 hour')");
 const wa45=createWa45OfflineBoundary({
  getRegistry:async()=>R,lookupBinding:async()=>B,
  getInternalKey:async()=>Buffer.from(DB_INTERNAL),newNonce:async()=>randomUUID(),
  nowSeconds:()=>NOW},DB_KEY);
 const gate=createWa46OfflineMetaGate({
  getRegistry:async()=>REG,getMetaAppSecret:async()=>Buffer.from(APP_SECRET),
  nowSeconds:()=>NOW,wa45Boundary:wa45},ROUTE);
 let writes=0;
 physicalGate=createWa56OfflineArchiveBridge({rawGate:gate,
  getInternalKey:async()=>Buffer.from(DB_INTERNAL),nowSeconds:()=>NOW,
  appendWa55:async ticket=>{
   writes++;
   const fields=[...ticket.candidate,ticket.macSha256];
   const arr=fields.map((v,i)=>i===13?String(Number(v)):q(v));
   return JSON.parse(db("select prumo_private.meta_wa55_single_entry_fixture_s0("+
     arr.join(',')+")",true,DATABASE_PASSWORD));
  }});
 physicalPass=()=>writes;
 physicalRaw=rawMeta();
}
checks.push(async()=>{setupPhysical();assert.ok(physicalGate);assert.equal(physicalPass(),0);});
checks.push(async()=>{const x=await physicalGate.receive(physicalRaw,header(physicalRaw));
 assert.equal(x.decision,'LAB_META_RAW_TO_WA55_FORENSIC_ONLY');assert.ok(
 ['LAB_OBSERVED_UNVERIFIED','LAB_LATE_UNVERIFIED'].includes(x.receipt.outcome));assert.equal(physicalPass(),1);});
checks.push(async()=>{const x=await physicalGate.receive(physicalRaw,header(physicalRaw));assert.equal(x.receipt?.outcome,'LAB_EXACT_BODY_REPLAY');assert.equal(physicalPass(),2);});
checks.push(async()=>{const bad=Buffer.from(physicalRaw);bad[bad.length-2]^=1;
 const before=physicalPass(),x=await physicalGate.receive(bad,header(physicalRaw));
 fail(x);assert.equal(physicalPass(),before);});
checks.push(async()=>{const eid='WA46_'+createHash('sha256').update(JSON.stringify(
 [R.wabaTechnical,R.phoneTechnical,B.wamid,B.recipient,'delivered',String(NOW)])).digest('hex');
 assert.equal(db('select count(*) from prumo_private.meta_status_forense_fixture_s0 where event_ref='+q(eid)),'1');});
checks.push(async()=>{assert.equal(db('select count(*) from prumo_private.meta_wa48_shadow_receipts_fixture_s0 where key_id='+q(DB_KEY)),'0');});
checks.push(async()=>{assert.equal(db("select has_function_privilege('prumo_s0_meta_wa48_client_lab',"+
 q('prumo_private.meta_wa52_locked_forensic_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)')+
 ",'EXECUTE')"),'f');});
for(let i=0;i<checks.length;i++){
 test('WA56-'+String(i+1).padStart(2,'0')+' signed raw to sealed PG17 boundary',async()=>{
  await checks[i]();
  console.log('WA56-'+String(i+1).padStart(2,'0')+' PASS');
 });
}
