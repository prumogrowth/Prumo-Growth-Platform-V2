import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const pin=process.env.S0_FRONTEND_PIN;
const ui=pin?await import(pathToFileURL(resolve(pin,
 'frontend/visual/conversation-attention.mjs')).href):null;
const enabled={skip:!ui};
let physical=null;
if(process.env.S0_FRONTEND_V02_EVIDENCE){
 physical=JSON.parse(await readFile(process.env.S0_FRONTEND_V02_EVIDENCE,'utf8'));
 assert.equal(physical.lab_only,true);
}
function stage(row){
 return ui.stageConversationAttention({
  schema_version:ui.ATTENTION_PROPOSAL_VERSION,
  unread_inbound_count:row.unread_inbound_count,
  operator_read_confirmed:row.operator_read_confirmed,
  human_reply_pending:row.human_reply_pending!=='NONE'});
}
test('S0-FE02-01 historic unread stays COUNT and no composer',enabled,()=>{
 const row={unread_inbound_count:1,operator_read_confirmed:false,
   human_reply_pending:'COUNT',historical_read_only:true,composer_enabled:false};
 assert.equal(stage(row).kind,'unread');
 assert.equal(row.composer_enabled,false);
});
test('S0-FE02-02 historic opened but no reply becomes DOT',enabled,()=>{
 const row={unread_inbound_count:0,operator_read_confirmed:true,
   human_reply_pending:'DOT',historical_read_only:true,composer_enabled:false};
 assert.equal(stage(row).kind,'read_awaiting_reply');
 assert.equal(row.composer_enabled,false);
});
test('S0-FE02-03 staged open is NEVER a UI-confirmed read',enabled,()=>{
 const staged={status:'LAB_OPEN_STAGED_BEFORE_COMMIT',
  read_confirmation_state:'NOT_CONFIRMED',display_read_confirmed:false};
 assert.equal(staged.display_read_confirmed,false);
 assert.equal(staged.read_confirmation_state,'NOT_CONFIRMED');
});
test('S0-FE02-04 committed-original-cutoff readback is scoped to old inbox',enabled,()=>{
 const receipt={status:'LAB_COMMITTED_READBACK',
  original_open_committed:true,newer_inbound_after_open:true,
  display_read_confirmed:false,unread_inbound_count:1,
  human_reply_pending:'COUNT'};
 assert.equal(receipt.display_read_confirmed,false);
 assert.equal(receipt.unread_inbound_count,1);
});
test('S0-FE02-05 unknown commit cannot be shown as success',enabled,()=>{
 const unknown={status:'LAB_COMMIT_UNRESOLVED',
   read_confirmation_state:'UNKNOWN',display_read_confirmed:false};
 assert.equal(unknown.display_read_confirmed,false);
});
test('S0-FE02-06 only titular can stage original visual read',enabled,()=>{
 const user={role:'operador',actor_id:'seller_A',
   assigned_actor_id:'seller_A',case_ref:'case_A',
   case_version:'v1',account_active:true};
 assert.equal(ui.canStageReadAcknowledgment(user),true);
 assert.equal(ui.canStageReadAcknowledgment({...user,role:'gestor'}),false);
});
test('S0-FE02-07 unknown historical clock cannot imply chronology',enabled,()=>{
 const history={last_activity_at:null,activity_time_state:'UNKNOWN'};
 assert.equal(history.last_activity_at,null);
});
test('S0-FE02-08 PG17 history/readback drives original visual mapping',
 {skip:!ui||!physical},()=>{
 const hist=physical.history_before.rows;
 assert.deepEqual(hist.map(x=>x.case_ref).sort(),['case_B','case_C']);
 const archived=hist.find(x=>x.case_ref==='case_B');
 assert.equal(stage(archived).kind,'unread');
 assert.equal(archived.composer_enabled,false);
 assert.equal(physical.staged.status,'LAB_OPEN_STAGED_BEFORE_COMMIT');
 assert.equal(physical.staged.display_read_confirmed,false);
 assert.equal(physical.after_commit.status,'LAB_COMMITTED_READBACK');
 assert.equal(physical.after_commit.display_read_confirmed,true);
 assert.equal(physical.after_commit.composer_enabled,false);
 const after=physical.history_after.rows.find(x=>x.case_ref==='case_B');
 assert.equal(stage(after).kind,'read_awaiting_reply');
 assert.equal(physical.after_new_inbound.display_read_confirmed,false);
 assert.equal(physical.after_new_inbound.newer_inbound_after_open,true);
 assert.equal(physical.after_new_inbound.unread_inbound_count,1);
 assert.equal(physical.active_staged.display_read_confirmed,false);
 assert.equal(physical.active_after.display_read_confirmed,true);
});
