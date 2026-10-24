/**
 * WA44 Node ↔ PG17 S0/044 contract parity. Synthetic only; no provider/Graph.
 * Runs in disposable GitHub Actions PG17 with an explicitly constrained DSN.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac,randomUUID} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {
 makeWa44CandidateFixture,wa44CanonicalBytes,signWa44Fixture,
 compareWa44FixtureSignature,WA44_AUDIENCE,WA44_WIRE_FIELDS,
} from './s0_wa_048_meta_handoff_adapter.mjs';

const key=Buffer.alloc(48,0x4b);
const registry=Object.freeze({
 appTechnical:'12346000002',wabaTechnical:'22346000002',
 phoneTechnical:'32346000002',appRef:'FIXTURE_WA40_B',
 tenantRef:'SHOP_WA40_B',channelRef:'f7300000-0000-4000-8000-000000000002',
});
const binding=Object.freeze({
 appRef:registry.appRef,tenantRef:registry.tenantRef,channelRef:registry.channelRef,
 intentRef:'f7400000-0000-4000-8000-000000000002',attemptRef:'ATTEMPT_B',
 correlationRef:'CORR_B',recipient:'5581900000000',
 wamid:'wamid.WA40.SHARED',bindingRevision:3,
});
const event=Object.freeze({eventRef:'EVT_WA44_ACCEPT',kind:'delivered',bodySha256:'e'.repeat(64)});
const KEY_ID='f7800000-0000-4000-8000-000000000001';
const at=Math.floor(Date.now()/1000);
const nonce=randomUUID();
const fixture=({r=registry,b=binding,e=event,rev=3,k=KEY_ID,n=nonce,issued=at}={})=>
 makeWa44CandidateFixture({registry:r,binding:b,event:e,keyId:k,nonce:n,issuedAtSeconds:issued,expectedRevision:rev});
const candidate=fixture();
const signed=signWa44Fixture(candidate,key);
function canonical(c=candidate){const v=wa44CanonicalBytes(c);assert.ok(Buffer.isBuffer(v));return v;}
function change(o,k,v){return {...o,[k]:v};}
const checks=[
 ()=>{assert.equal(WA44_WIRE_FIELDS.length,15);assert.equal(candidate.length,15);assert.ok(Object.isFrozen(candidate));},
 ()=>{assert.equal(canonical().toString('utf8').split('|').length,17);assert.ok(canonical().toString('utf8').startsWith('prumo-meta-handoff-lab-v1|FORENSIC_APPEND_ONLY|'));},
 ()=>{assert.equal(signed.macSha256,createHmac('sha256',key).update(canonical()).digest('hex'));assert.ok(compareWa44FixtureSignature(candidate,key,signed.macSha256));},
 ()=>{const json=JSON.stringify(candidate);const forged=createHmac('sha256',key).update(json).digest('hex');assert.notEqual(forged,signed.macSha256);assert.equal(compareWa44FixtureSignature(candidate,key,forged),false);},
 ()=>{for(let i=0;i<15;i++){const tmp=[...candidate];tmp[i]=i===11?'failed':i===12?'f'.repeat(64):i===13?String(at+1):i===14?randomUUID():i===10?'EVT_MUTATED':i===9?'wamid.WA44.OTHER':i===8?'5581999999999':i>=4&&i<=5?'f9999999-0000-4000-8000-000000000001':i===0?randomUUID():i>=1&&i<=3?'99999000009':'CHANGED';const v=wa44CanonicalBytes(Object.freeze(tmp));if(v)assert.notEqual(v.toString(),canonical().toString(),'field '+i);}},
 ()=>{assert.equal(fixture({r:change(registry,'appRef','FIXTURE_OTHER')}),null);},
 ()=>{assert.equal(fixture({r:change(registry,'tenantRef','OTHER_SHOP')}),null);},
 ()=>{assert.equal(fixture({r:change(registry,'channelRef',randomUUID())}),null);},
 ()=>{assert.equal(fixture({rev:4}),null);},
 ()=>{assert.equal(fixture({r:change(registry,'unexpected',true)}),null);assert.equal(fixture({b:change(binding,'trusted',true)}),null);},
 ()=>{const o={...event};Object.defineProperty(o,'kind',{get(){throw Error('unsafe getter')}});assert.equal(fixture({e:o}),null);},
 ()=>{const proxy=new Proxy(registry,{getPrototypeOf(){throw Error('untrusted proxy')}});assert.equal(fixture({r:proxy}),null);},
 ()=>{assert.equal(fixture({issued:Infinity}),null);assert.equal(fixture({issued:-3}),null);},
 ()=>{assert.equal(fixture({n:'CLIENT_NONCE'}),null);},
 ()=>{assert.equal(fixture({r:change(registry,'appTechnical','not_numeric')}),null);},
 ()=>{assert.equal(fixture({b:change(binding,'wamid','forged')}),null);},
 ()=>{assert.equal(fixture({e:change(event,'bodySha256','0000')}),null);},
 ()=>{assert.equal(fixture({e:change(event,'kind','GRAPH_SEND')}),null);},
 ()=>{assert.equal(signWa44Fixture(candidate,Buffer.alloc(10)),null);assert.equal(compareWa44FixtureSignature(candidate,key,'bad'),false);},
 ()=>{assert.equal(signed.audience,WA44_AUDIENCE);assert.equal(signed.contract,'WA40_PG17_LAB_ONLY');for(const k of ['ack_allowed','send_authorized','retry_external','production_authorized','service_authenticated'])assert.equal(signed[k],false);},
];
for(let i=0;i<checks.length;i++)test('WA44-'+String(i+1).padStart(2,'0')+' offline JS invariant',()=>{
 checks[i]();console.log('WA44-'+String(i+1).padStart(2,'0')+' PASS');
});
const dsn=process.env.PRUMO_TEST_DATABASE_URL;
function db(query){
 if(typeof dsn!=='string')throw Error('WA44 requires an explicitly provided PG17 test DSN');
 const u=new URL(dsn);
 if(u.protocol!=='postgresql:'||u.hostname!=='127.0.0.1'||u.port!=='5432'||
    u.username!=='postgres'||u.pathname!=='/prumo_s0_test_ci'||u.search||u.hash)
  throw Error('WA44 refuses any non-disposable database');
 for(const v of ['PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER',
   'PGSERVICE','PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT',
   'PGSSLKEY','PGSSLROOTCERT'])
  if(process.env[v])throw Error('WA44 refuses libpq overrides: '+v);
 const p=spawnSync('psql',['-X','-qAt','-v','ON_ERROR_STOP=1',
  '-v','VERBOSITY=verbose',dsn,'-c',query],{timeout:12000,encoding:'utf8'});
 if(p.error)throw p.error;
 return p;
}
const sqlQuote=s=>{assert.match(s,/^[A-Za-z0-9_.:-]{1,128}$/);return "'"+s+"'";};
const sqlArgs=c=>c.map(sqlQuote).join(',');
const queryGood=q=>{const x=db(q);assert.equal(x.status,0,x.stderr);return x.stdout.trim();};
const queryDenied=q=>{const x=db(q);assert.notEqual(x.status,0,'unexpected success');assert.match(x.stderr,/42501/);};
const SQLFN='prumo_private.meta_arquivar_handoff_assinado_fixture_s0';
function call(c,mac){return 'SET ROLE prumo_s0_meta_ingress_lab; SELECT '+SQLFN+'('+sqlArgs([...c,mac])+');';}
const phys=[
 ()=>{const actual=queryGood('SELECT prumo_private.meta_material_handoff_fixture_s0('+sqlArgs(candidate)+');');assert.equal(actual,canonical().toString('utf8'));},
 ()=>{const schema=queryGood("SELECT n.nspname FROM pg_extension e JOIN pg_namespace n ON e.extnamespace=n.oid WHERE e.extname='pgcrypto'");
 assert.match(schema,/^[a-z_][a-z0-9_]*$/);
 const actual=queryGood('SELECT encode("'+schema+'".hmac(convert_to(prumo_private.meta_material_handoff_fixture_s0('+sqlArgs(candidate)+"),'UTF8'),decode(repeat('4b',48),'hex'),'sha256'),'hex');");
 assert.equal(actual,signed.macSha256);},
 ()=>{queryGood("INSERT INTO prumo_private.meta_servico_chaves_fixture_s0(chave_id,app_technical_ref,segredo,valido_desde,valido_ate,ativo) VALUES("+
 sqlQuote(KEY_ID)+",'12346000002',decode(repeat('4b',48),'hex'),clock_timestamp()-interval '60 seconds',clock_timestamp()+interval '30 minutes',true)");
 const wire=JSON.parse(queryGood(call(candidate,signed.macSha256)));
 assert.equal(wire.outcome,'LAB_OBSERVED_UNVERIFIED');assert.equal(wire.service_authenticated,false);
 assert.equal(wire.ack_allowed,false);assert.equal(wire.send_authorized,false);},
 ()=>{const altered=Object.freeze([...candidate].map((x,i)=>i===10?'EVT_WA44_TAMPER':x));
 queryDenied(call(altered,signed.macSha256));
 assert.equal(queryGood("SELECT count(*) FROM prumo_private.meta_status_forense_fixture_s0 WHERE event_ref='EVT_WA44_TAMPER'"),'0');},
 ()=>{queryDenied(call(candidate,signed.macSha256));
 assert.equal(queryGood("SELECT count(*) FROM prumo_private.meta_servico_nonces_fixture_s0 WHERE nonce="+sqlQuote(nonce)),'1');},
 ()=>{const alt=fixture({n:randomUUID(),e:change(event,'eventRef','EVT_WA44_JSON')});
 const forged=createHmac('sha256',key).update(JSON.stringify(alt)).digest('hex');
 queryDenied(call(alt,forged));
 assert.equal(queryGood("SELECT count(*) FROM prumo_private.meta_status_forense_fixture_s0 WHERE event_ref='EVT_WA44_JSON'"),'0');},
 ()=>{assert.equal(queryGood("SELECT count(*) FROM prumo_private.meta_status_forense_fixture_s0 WHERE "+
 "ack_allowed OR send_authorized OR retry_external OR production_authorized OR "+
 "delivery_confirmed OR case_transition_authorized OR definitive_failure_count_increment"),'0');},
];
for(let i=0;i<phys.length;i++)test('WA44-'+String(i+21).padStart(2,'0')+' PG17 interoperability check',()=>{
 phys[i]();console.log('WA44-'+String(i+21).padStart(2,'0')+' PASS');
});
