import test from 'node:test';
import assert from 'node:assert/strict';
import {ATTENTION_PROPOSAL_VERSION,stageConversationAttention,
  canStageReadAcknowledgment} from '../conversation-attention.mjs';
const projection=(unread=0, read=false, pending=false)=>({
  schema_version:ATTENTION_PROPOSAL_VERSION,
  unread_inbound_count:unread, operator_read_confirmed:read,
  human_reply_pending:pending
});
test('indicador único numerado quando há mensagens recebidas não lidas',()=>{
  for(const n of [1,2,9,99,100]){
    const v=stageConversationAttention(projection(n,true,true));
    assert.equal(v.kind,'unread');
    assert.equal(v.count,Math.min(n,99));
    assert.equal(v.kind==='read_awaiting_reply',false);
  }
});
test('após leitura confirmada e sem resposta humana, indicador muda e perde número',()=>{
  const v=stageConversationAttention(projection(0,true,true));
  assert.equal(v.kind,'read_awaiting_reply');assert.equal(v.count,null);
  assert.match(v.label,/resposta humana pendente/);
});
test('após resposta, ou sem leitura comprovada, nenhum indicador',()=>{
  for(const [read,pending] of [[true,false],[false,true],[false,false]])
    assert.equal(stageConversationAttention(projection(0,read,pending)).kind,'none');
});
test('projeções inválidas ou versão desconhecida não geram alerta',()=>{
  for(const data of [
    null,[],{},'pending',{...projection(1),schema_version:'v0'},
    {...projection(1),unread_inbound_count:'1'},
    {...projection(1),unread_inbound_count:-1},
    {...projection(1),unread_inbound_count:1.5},
    {...projection(1),unread_inbound_count:Infinity},
    {...projection(1),operator_read_confirmed:'yes'},
    {...projection(1),human_reply_pending:1}
  ])assert.equal(stageConversationAttention(data).kind,'none');
});
test('supervisor nunca confirma leitura pelo operador nem reatribui caso',()=>{
  const base={role:'operador',account_active:true,actor_id:'op-a',
    assigned_actor_id:'op-a',case_ref:'case-1',case_version:'v3'};
  assert.equal(canStageReadAcknowledgment(base),true);
  assert.equal(canStageReadAcknowledgment({...base,role:'gestor',acting_as_assigned_operator:true}),true);
  for(const changed of [
    {role:'gestor'},{actor_id:'manager'},{assigned_actor_id:'op-b'},
    {account_active:false},{case_version:null},{case_ref:''}
  ])assert.equal(canStageReadAcknowledgment({...base,...changed}),false);
});
test('funções não alteram projeção original nem criam tempo de espera',()=>{
  const input=projection(2,true,true),before=structuredClone(input);
  const result=stageConversationAttention(input);
  assert.deepEqual(input,before);
  assert.equal('waiting_minutes' in result,false);
  assert.equal('sla' in result,false);
});

import { copyCFDemoFixtures } from '../cf-op-02.mjs';
import { confirmedDemoMessages, latestConfirmedDemoMessage, projectDemoAttention } from '../conversation-attention.mjs';
for(const body of ['', ' \n\t', null, undefined])test('COR07 I01: inbound sem corpo legível não confirma prévia/pendência '+String(body),()=>{
 const record=copyCFDemoFixtures().find(r=>r.id==='A-102');
 record.messages=[{id:'blank',side:'in',body,time:'T1'}];record.unread=0;
 record.demoReadByAssigned=true;record.demoReadProjection={source:'local_fixture',actorId:'rafael',caseId:record.id,shopId:'aurora'};
 assert.deepEqual(confirmedDemoMessages(record,'rafael','aurora'),[]);
 assert.equal(latestConfirmedDemoMessage(record,'rafael','aurora'),null);
 assert.equal(projectDemoAttention(record,'rafael','aurora').kind,'none');
});
test('COR07 I01: lista vazia, sistema e IA não criam pendência humana',()=>{
 const record=copyCFDemoFixtures().find(r=>r.id==='A-102');record.unread=0;
 record.demoReadByAssigned=true;record.demoReadProjection={source:'local_fixture',actorId:'rafael',caseId:record.id,shopId:'aurora'};
 for(const messages of [[],[{id:'system',side:'system',body:'Evento técnico'}],[{id:'ai',side:'ai',body:'Mensagem IA'}]]){
   record.messages=messages;assert.equal(projectDemoAttention(record,'rafael','aurora').kind,'none');
 }
});

test('COR07 I01: leitura referencia o último inbound legível; contador obsoleto não cria mensagens',()=>{
 const record=copyCFDemoFixtures().find(r=>r.id==='A-102');
 record.messages=[{id:'in-1',side:'in',body:'Olá',time:'T1'}];record.unread=0;
 record.demoReadByAssigned=true;record.demoReadProjection={source:'local_fixture',actorId:'rafael',caseId:record.id,shopId:'aurora',messageRef:'in-1'};
 assert.equal(projectDemoAttention(record,'marina','aurora').kind,'read_awaiting_reply');
 record.messages.push({id:'in-2',side:'in',body:'Outra mensagem',time:'T2'});
 assert.equal(projectDemoAttention(record,'rafael','aurora').kind,'none');
 record.messages=[];record.unread=8;
 assert.equal(projectDemoAttention(record,'rafael','aurora').kind,'none');
 record.messages=[{id:'local-audio',side:'out',body:'Áudio local (0:01)',localAudioId:'clip',deliveryState:'local_demo_not_sent'}];
 assert.equal(confirmedDemoMessages(record,'rafael','aurora').length,0);
});
