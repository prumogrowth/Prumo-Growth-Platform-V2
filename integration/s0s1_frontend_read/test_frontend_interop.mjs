import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const pinned=process.env.S0_FRONTEND_PIN;
const ui=pinned?await import(pathToFileURL(resolve(pinned,
  'frontend/visual/conversation-attention.mjs')).href):null;
const enabled={skip:!ui};
const samples={
  before:{unread_inbound_count:1,operator_read_confirmed:false,
    human_reply_pending:'COUNT',historical_read_only:false,composer_enabled:true},
  after:{unread_inbound_count:0,operator_read_confirmed:true,
    human_reply_pending:'DOT',historical_read_only:false,composer_enabled:true},
  cleared:{unread_inbound_count:0,operator_read_confirmed:true,
    human_reply_pending:'NONE',historical_read_only:false,composer_enabled:true},
  historical:{unread_inbound_count:0,operator_read_confirmed:true,
    human_reply_pending:'DOT',historical_read_only:true,composer_enabled:false},
};
let evidence=null;
if(process.env.S0_FRONTEND_EVIDENCE){
  evidence=JSON.parse(await readFile(process.env.S0_FRONTEND_EVIDENCE,'utf8'));
  assert.equal(evidence.lab_only,true);
}
function stage(row){
  return ui.stageConversationAttention({
    schema_version:ui.ATTENTION_PROPOSAL_VERSION,
    unread_inbound_count:row.unread_inbound_count,
    operator_read_confirmed:row.operator_read_confirmed,
    human_reply_pending:row.human_reply_pending!=='NONE'
  });
}
test('S0-FE-01 S0 COUNT maps to one numbered Frontend badge',enabled,()=>{
  assert.equal(stage(samples.before).kind,'unread');
  assert.equal(stage(samples.before).count,1);
});
test('S0-FE-02 S0 DOT maps to read awaiting human reply',enabled,()=>{
  assert.equal(stage(samples.after).kind,'read_awaiting_reply');
  assert.equal(stage(samples.after).count,null);
});
test('S0-FE-03 published reply clears the attention badge',enabled,()=>{
  assert.equal(stage(samples.cleared).kind,'none');
});
test('S0-FE-04 historical case still read/pending without composer',enabled,()=>{
  const h=samples.historical;
  assert.equal(stage(h).kind,'read_awaiting_reply');
  assert.equal(h.historical_read_only,true);
  assert.equal(h.composer_enabled,false);
});
test('S0-FE-05 Frontend does not authorize supervisor read',enabled,()=>{
  const owner={role:'operador',actor_id:'seller_A',
    assigned_actor_id:'seller_A',case_ref:'case_A',case_version:'v1',
    account_active:true};
  assert.equal(ui.canStageReadAcknowledgment(owner),true);
  assert.equal(ui.canStageReadAcknowledgment({
    ...owner,role:'gestor',actor_id:'manager_A'}),false);
});
test('S0-FE-06 only S0 read after commit, not API ACK',enabled,()=>{
  assert.equal(samples.before.operator_read_confirmed,false);
  assert.equal(samples.after.operator_read_confirmed,true);
  assert.equal('transport_received' in samples.after,false);
  assert.equal('ack' in samples.after,false);
});
test('S0-FE-07 unknown source clock has no fabricated time',enabled,()=>{
  const a={...samples.after,last_activity_at:null,
    activity_time_state:'UNKNOWN',last_activity_cutoff_seq:null};
  assert.equal(a.last_activity_at,null);
  assert.equal(a.last_activity_cutoff_seq,null);
  assert.equal(stage(a).kind,'read_awaiting_reply');
});
test('S0-FE-08 exact PG17 open and supervisor result map to pinned UI',
 {skip:!ui||!evidence},()=>{
  assert.equal(stage(evidence.before).kind,'unread');
  assert.equal(evidence.supervisor.decision,'SUPERVISORY_VIEW_NO_READ');
  assert.equal(stage(evidence.after).kind,'read_awaiting_reply');
  assert.equal(evidence.recorded.decision,'LAB_READ_RECORDED_BEFORE_COMMIT');
  assert.equal(stage(evidence.historical).kind,'read_awaiting_reply');
  assert.equal(evidence.historical.composer_enabled,false);
  assert.equal(evidence.manager.decision,'LAB_MANAGER_MINIMIZED');
  assert.equal(JSON.stringify(evidence.manager).includes('seller_A'),false);
  assert.equal(JSON.stringify(evidence.manager).includes('case_A'),false);
  for(const r of evidence.queue){
    assert.equal(typeof r.last_activity_at,'string');
    assert.equal(r.activity_time_state,'VERIFIED_LAB_ONLY');
  }
});
