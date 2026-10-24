/** WA45 22 adversarial Node proofs + 5 physical PG17 handoff proofs. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac,randomUUID} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {createWa45OfflineBoundary} from './s0_wa_049_meta_trusted_boundary.mjs';
import {wa44CanonicalBytes,compareWa44FixtureSignature} from './s0_wa_048_meta_handoff_adapter.mjs';

const KEY_ID='f7900000-0000-4000-8000-000000000001';
const KEY=Buffer.alloc(48,0x61);
const R=Object.freeze({appTechnical:'12346000002',wabaTechnical:'22346000002',
 phoneTechnical:'32346000002',appRef:'FIXTURE_WA40_B',tenantRef:'SHOP_WA40_B',
 channelRef:'f7300000-0000-4000-8000-000000000002'});
const B=Object.freeze({appRef:R.appRef,tenantRef:R.tenantRef,channelRef:R.channelRef,
 intentRef:'f7400000-0000-4000-8000-000000000002',
 attemptRef:'ATTEMPT_B',correlationRef:'CORR_B',recipient:'5581900000000',
 wamid:'wamid.WA40.SHARED',bindingRevision:3});
const E=Object.freeze({eventRef:'EVT_WA45_PASS',kind:'delivered',
 bodySha256:'d'.repeat(64),wamid:B.wamid,recipient:B.recipient});
const now=Math.floor(Date.now()/1000);
function ports(overrides={}){
 return {getRegistry:async()=>R,lookupBinding:async()=>B,
  getInternalKey:async()=>Buffer.from(KEY),newNonce:async()=>randomUUID(),
  nowSeconds:()=>now,...overrides};
}
function issue(o={},e=E){const boundary=createWa45OfflineBoundary(ports(o),KEY_ID);assert.ok(boundary);return boundary.issue(e);}
function change(x,k,v){return {...x,[k]:v};}
const checks=[
 async()=>{const v=await issue();assert.equal(v.decision,'LAB_CANDIDATE_ONLY');assert.ok(v.ticket);},
 async()=>{const v=await issue();for(const k of ['ack_allowed','send_authorized','retry_external','production_authorized','service_authenticated','delivery_confirmed','case_transition_authorized'])assert.equal(v[k],false,k);},
 async()=>{assert.equal((await issue({},change(E,'tenantRef','ATTACKER'))).decision,'LAB_DENIED');},
 async()=>{assert.equal((await issue({},change(E,'wamid','wamid.FORGED'))).decision,'LAB_SCOPE_DENIED');},
 async()=>{assert.equal((await issue({},change(E,'recipient','5581999999999'))).decision,'LAB_SCOPE_DENIED');},
 async()=>{assert.equal((await issue({getRegistry:async()=>change(R,'tenantRef','FORGED')})).decision,'LAB_SCOPE_DENIED');},
 async()=>{assert.equal((await issue({getRegistry:async()=>change(R,'channelRef',randomUUID())})).decision,'LAB_SCOPE_DENIED');},
 async()=>{assert.equal((await issue({lookupBinding:async()=>change(B,'bindingRevision',0)})).decision,'LAB_SCOPE_DENIED');},
 async()=>{assert.equal((await issue({getRegistry:async()=>change(R,'unexpected',true)})).decision,'LAB_SCOPE_DENIED');},
 async()=>{const x={...R};Object.defineProperty(x,'appRef',{get(){throw Error('getter')}});assert.equal((await issue({getRegistry:async()=>x})).decision,'LAB_SCOPE_DENIED');},
 async()=>{const x=new Proxy(R,{getPrototypeOf(){throw Error('proxy')}});assert.equal((await issue({getRegistry:async()=>x})).decision,'LAB_SCOPE_DENIED');},
 async()=>{assert.equal((await issue({getInternalKey:async()=>Buffer.alloc(12)})).decision,'LAB_UNAVAILABLE');},
 async()=>{assert.equal((await issue({newNonce:async()=> 'CLIENT_NONCE'})).decision,'LAB_UNAVAILABLE');},
 async()=>{assert.equal((await issue({nowSeconds:()=>Infinity})).decision,'LAB_UNAVAILABLE');},
 async()=>{let i=0;assert.equal((await issue({nowSeconds:()=>++i===1?now:now-1})).decision,'LAB_STALE');},
 async()=>{let i=0;assert.equal((await issue({nowSeconds:()=>++i===1?now:now+22})).decision,'LAB_STALE');},
 async()=>{assert.equal((await issue({getRegistry:async()=>null})).decision,'LAB_SCOPE_DENIED');},
 async()=>{assert.equal((await issue({lookupBinding:async()=>null})).decision,'LAB_SCOPE_DENIED');},
 async()=>{assert.equal((await issue({getInternalKey:async()=>{throw Error('not available')}})).decision,'LAB_UNAVAILABLE');},
 async()=>{const x={...E};Object.defineProperty(x,'kind',{get(){throw Error('getter')}});assert.equal((await issue({},x)).decision,'LAB_DENIED');},
 async()=>{assert.equal((await issue({},Object.assign(Object.create(null),E,{other:1}))).decision,'LAB_DENIED');},
 async()=>{let n=0;const v=await issue({lookupBinding:async()=>++n===1?B:change(B,'attemptRef','STALE')});assert.equal(v.decision,'LAB_STALE');},
];
for(let i=0;i<checks.length;i++){
 test('WA45-'+String(i+1).padStart(2,'0')+' trusted-boundary lab check',async()=>{
  await checks[i]();console.log('WA45-'+String(i+1).padStart(2,'0')+' PASS');
 });
}

const dsn=process.env.PRUMO_TEST_DATABASE_URL;
function db(sql){
 if(typeof dsn!=='string')throw Error('WA45: explicit disposable DSN required');
 const u=new URL(dsn);
 if(u.protocol!=='postgresql:'||u.hostname!=='127.0.0.1'||u.port!=='5432'||
 u.username!=='postgres'||u.pathname!=='/prumo_s0_test_ci'||u.search||u.hash)
  throw Error('WA45 refuses hosted or non-local PG');
 for(const v of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER','PGSERVICE',
 'PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT','PGSSLKEY','PGSSLROOTCERT'])
  if(process.env[v])throw Error('WA45: libpq override '+v);
 const x=spawnSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose',dsn,'-c',sql],
  {timeout:15000,encoding:'utf8'});
 if(x.error)throw x.error;
 return x;
}
function good(sql){const x=db(sql);assert.equal(x.status,0,x.stderr);return x.stdout.trim();}
const q=x=>{assert.match(x,/^[A-Za-z0-9_.:-]{1,128}$/);return "'"+x+"'";};
const call=(c,mac)=>'SET ROLE prumo_s0_meta_ingress_lab; SELECT prumo_private.meta_arquivar_handoff_assinado_fixture_s0('+[...c,mac].map(q).join(',')+');';
const denied=s=>{const x=db(s);assert.notEqual(x.status,0,'Unexpected PG17 acceptance');assert.match(x.stderr,/42501/);};
let packet;
const physical=[
 async()=>{
  const res=await issue();
  assert.equal(res.decision,'LAB_CANDIDATE_ONLY');
  packet=res.ticket;
  assert.ok(compareWa44FixtureSignature(packet.candidate,KEY,packet.macSha256));
  assert.equal(packet.macSha256,createHmac('sha256',KEY).update(wa44CanonicalBytes(packet.candidate)).digest('hex'));
 },
 async()=>{
  const s=good("SELECT prumo_private.meta_material_handoff_fixture_s0("+packet.candidate.map(q).join(',')+");");
  assert.equal(s,wa44CanonicalBytes(packet.candidate).toString('utf8'));
 },
 async()=>{
  good("INSERT INTO prumo_private.meta_servico_chaves_fixture_s0(chave_id,app_technical_ref,segredo,valido_desde,valido_ate,ativo) VALUES("+q(KEY_ID)+",'12346000002',decode(repeat('61',48),'hex'),clock_timestamp()-interval '60 seconds',clock_timestamp()+interval '30 minutes',true)");
  const v=JSON.parse(good(call(packet.candidate,packet.macSha256)));
  assert.equal(v.outcome,'LAB_OBSERVED_UNVERIFIED');
  assert.equal(v.service_authenticated,false);
  assert.equal(v.ack_allowed,false);
 },
 async()=>{
  denied(call(packet.candidate,packet.macSha256));
  assert.equal(good("SELECT count(*) FROM prumo_private.meta_servico_nonces_fixture_s0 WHERE nonce="+q(packet.candidate[14])),'1');
 },
 async()=>{
  const altered=Object.freeze([...packet.candidate].map((v,i)=>i===10?'EVT_WA45_FORGED':v));
  denied(call(altered,packet.macSha256));
  assert.equal(good("SELECT count(*) FROM prumo_private.meta_status_forense_fixture_s0 WHERE event_ref='EVT_WA45_FORGED'"),'0');
  assert.equal(good("SELECT count(*) FROM prumo_private.meta_status_forense_fixture_s0 WHERE ack_allowed OR send_authorized OR production_authorized OR retry_external OR delivery_confirmed OR case_transition_authorized"),'0');
 },
];
for(let i=0;i<physical.length;i++)
 test('WA45-'+String(i+23).padStart(2,'0')+' PG17 trusted-boundary proof',async()=>{
  await physical[i]();console.log('WA45-'+String(i+23).padStart(2,'0')+' PASS');
 });
