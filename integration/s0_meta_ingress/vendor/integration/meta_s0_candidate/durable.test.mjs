import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {FileStore} from './lab-store.mjs';
import {CandidateLab} from './candidate.mjs';
import {setup,reservation} from './fixtures.mjs';

async function fixture(t,hook=async()=>{}) {
  const directory=await mkdtemp(join(tmpdir(),'meta-s0-lab-'));
  t.after(()=>rm(directory,{recursive:true,force:true}));
  let enabled=false;
  const h=setup({storeFactory:()=>new FileStore(directory,{
    hook:(...args)=>enabled?hook(...args):undefined,
  })});
  await h.store.initialize(h.seed);enabled=true;
  return {...h,directory};
}
function reopen(h) {
  const store=new FileStore(h.directory);
  const lab=new CandidateLab({optIn:'DISPOSABLE_META_S0_LAB_ONLY',store,
    keys:h.secrets,appSecrets:h.appSecrets,clock:h.getNow});
  return {store,lab};
}
async function crash(h,phase,packet) {
  const child=spawn(process.execPath,['--experimental-strip-types',
    fileURLToPath(new URL('./crash-worker.mjs',import.meta.url)),h.directory,phase],
    {env:{PATH:process.env.PATH},stdio:['pipe','pipe','pipe']});
  let stderr='';child.stderr.on('data',c=>{stderr+=c;});
  child.stdout.resume();
  const done=new Promise((resolve,reject)=>{
    child.on('error',reject);child.on('exit',(code,signal)=>resolve({code,signal}));
  });
  child.stdin.end(JSON.stringify({
    keys:Object.fromEntries(Object.entries(h.secrets).map(([id,k])=>[id,k.toString('hex')])),
    appSecrets:h.appSecrets,now:h.getNow(),bytes:packet.bytes.toString('base64'),proof:packet.proof,
  }));
  const result=await done;
  assert.equal(result.code,23,stderr);assert.equal(result.signal,null);
}
test('file receipt follows file sync, atomic rename and directory sync; restart sees whole lot',async t=>{
  const phases=[],h=await fixture(t,async p=>{phases.push(p);});
  const r=await h.call('append_batch',h.batch(),'ingress');
  assert.equal(r.lab_ack_ready,true);assert.equal(r.ack_allowed,false);
  assert.deepEqual(phases,['before_write','before_file_sync','before_rename',
    'after_rename','after_directory_sync','after_commit_before_return']);
  const {store}=reopen(h),s=await store.snapshot();
  assert.equal(Object.keys(s.raw_receipts).length,1);
  assert.equal(Object.values(s.raw_receipts)[0].observations.length,2);
  assert.equal(Object.keys(s.nonces).length,1);assert.equal(s.audit.length,1);
});
test('ACK candidate stays pending while persistence is blocked before fsync',async t=>{
  let entered,release;
  const atSync=new Promise(r=>{entered=r;}),gate=new Promise(r=>{release=r;});
  const h=await fixture(t,async p=>{if(p==='before_file_sync'){entered();await gate;}});
  let settled=false;
  const result=h.call('append_batch',h.batch(),'ingress').then(r=>{settled=true;return r;});
  await atSync;assert.equal(settled,false);
  const old=await h.store.snapshot();assert.equal(Object.keys(old.batches).length,0);
  release();assert.equal((await result).lab_ack_ready,true);
});
test('failure before rename leaves no batch, nonce or audit; retry is fresh and complete',async t=>{
  let inject=true;
  const h=await fixture(t,async p=>{if(p==='before_rename'&&inject){inject=false;throw Error('INJECTED');}});
  const r=await h.call('append_batch',h.batch(),'ingress');
  assert.equal(r.code,'COMMIT_OR_RESULT_UNKNOWN');assert.equal(r.lab_ack_ready,false);
  const s=await h.store.snapshot();assert.equal(Object.keys(s.batches).length,0);
  assert.equal(Object.keys(s.nonces).length,0);assert.equal(s.audit.length,0);
  assert.equal((await h.call('append_batch',h.batch(),'ingress')).lab_ack_ready,true);
});
test('failure after rename is uncertain and readback reuses the persisted receipt',async t=>{
  let inject=true;
  const h=await fixture(t,async p=>{if(p==='after_rename'&&inject){inject=false;throw Error('LOST_SYNC');}});
  const r=await h.call('append_batch',h.batch(),'ingress');
  assert.equal(r.code,'COMMIT_OR_RESULT_UNKNOWN');assert.equal(r.lab_ack_ready,false);
  const s=await h.store.snapshot(),receipt=Object.values(s.raw_receipts)[0].receipt_ref;
  const opened=reopen(h),p=h.packet('append_batch',h.batch(),'ingress');
  const retry=await opened.lab.call(p.bytes,p.proof);
  assert.equal(retry.lab_ack_ready,true);assert.equal(retry.receipt_ref,receipt);
  assert.equal(retry.code,'BATCH_ALREADY_DURABLE_CANDIDATE');
});
test('lost durable result: old nonce cannot yield ACK and fresh proof recovers exact receipt',async t=>{
  let inject=true;
  const h=await fixture(t,async p=>{if(p==='after_commit_before_return'&&inject){inject=false;throw Error('LOST');}});
  const packet=h.packet('append_batch',h.batch(),'ingress');
  const r=await h.lab.call(packet.bytes,packet.proof);
  assert.equal(r.code,'COMMIT_OR_RESULT_UNKNOWN');assert.equal(r.lab_ack_ready,false);
  const opened=reopen(h);
  const replay=await opened.lab.call(packet.bytes,packet.proof);
  assert.equal(replay.code,'NONCE_REPLAY_NO_EXECUTION');assert.equal(replay.lab_ack_ready,false);
  const p2=h.packet('append_batch',h.batch(),'ingress');
  const recovered=await opened.lab.call(p2.bytes,p2.proof);
  assert.equal(recovered.lab_ack_ready,true);
  assert.equal(Object.keys((await opened.store.snapshot()).raw_receipts).length,1);
});
test('actual child process loss after fsync+commit and before response recovers all items',async t=>{
  const h=await fixture(t),p=h.packet('append_batch',h.batch(),'ingress');
  await crash(h,'after_commit_before_return',p);
  const {store,lab}=reopen(h),s=await store.snapshot();
  assert.equal(Object.keys(s.nonces).length,1);
  assert.equal(Object.values(s.raw_receipts)[0].observations.length,2);
  const fresh=h.packet('append_batch',h.batch(),'ingress');
  const r=await lab.call(fresh.bytes,fresh.proof);
  assert.equal(r.code,'BATCH_ALREADY_DURABLE_CANDIDATE');assert.equal(r.lab_ack_ready,true);
  assert.equal(r.receipt_ref,Object.values(s.raw_receipts)[0].receipt_ref);
});
test('actual process loss before rename leaves original state and no partial ACK',async t=>{
  const h=await fixture(t),p=h.packet('append_batch',h.batch(),'ingress');
  await crash(h,'before_rename',p);
  const {store,lab}=reopen(h),s=await store.snapshot();
  assert.equal(Object.keys(s.nonces).length,0);assert.equal(Object.keys(s.batches).length,0);
  const fresh=h.packet('append_batch',h.batch(),'ingress');
  const r=await lab.call(fresh.bytes,fresh.proof);
  assert.equal(r.lab_ack_ready,true);assert.equal(r.items.length,2);
});
test('restart after begin with no observation remains unknown, occupied and never reusable',async t=>{
  const h=await fixture(t),r=await h.call('reserve',reservation());
  await h.call('begin',{attempt_ref:r.attempt_ref,expected_revision:'1'});
  const {lab}=reopen(h),read=h.packet('read',{attempt_ref:r.attempt_ref});
  assert.equal((await lab.call(read.bytes,read.proof)).state,'EXTERNAL_UNCERTAIN');
  const p=h.packet('begin',{attempt_ref:r.attempt_ref,expected_revision:'1'});
  assert.equal((await lab.call(p.bytes,p.proof)).code,'BEGIN_ALREADY_CONSUMED_NO_RETRY');
  const reserve=h.packet('reserve',reservation({idempotency_key:'after_restart'}));
  assert.equal((await lab.call(reserve.bytes,reserve.proof)).code,'INTENT_OCCUPIED_NO_RETRY');
});
test('reinitialization cannot erase existing durable state',async t=>{
  const h=await fixture(t);await h.call('reserve',reservation());
  await assert.rejects(h.store.initialize(h.seed),/ALREADY_INITIALIZED/);
  assert.equal(Object.keys((await h.store.snapshot()).attempts).length,1);
});
test('proof and raw envelope are snapshotted before awaiting a transaction',async t=>{
  const h=await fixture(t),p=h.packet('reserve',reservation());
  const result=h.lab.call(p.bytes,p.proof);
  p.bytes.fill(0);p.proof.mac_sha256='0'.repeat(64);
  assert.equal((await result).code,'LAB_RESERVED_NO_SEND_RIGHTS');
});
