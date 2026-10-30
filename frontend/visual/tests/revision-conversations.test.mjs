/** FV-REV-01 v0.4 Etapa 1. Synthetic scope only, no business transport. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {copyCFDemoFixtures,projectedFollowupActions,mayMockFreeText} from '../cf-op-02.mjs';
import {visibleConversations,COMMERCIAL_STATUSES} from '../fixtures.mjs';
import {latestConfirmedDemoMessage,projectDemoAttention} from '../conversation-attention.mjs';
import {installMockDOM} from './dom-fixture.mjs';

const records=copyCFDemoFixtures();
const find=id=>structuredClone(records.find(row=>row.id===id));

test('REV-009: preview follows last confirmed authorized record, independent of author',()=>{
  const record=find('A-102');
  const inbound=record.messages.at(-1);
  assert.equal(latestConfirmedDemoMessage(record,'rafael','aurora').id,inbound.id);
  for(const state of ['requested','api_accepted','uncertain','failed_confirmed','sent_confirmed','delivered','read']){
    const message={id:'out-'+state,side:'out',body:'Resposta '+state,time:'11:00',
      transportProjection:{source:'s0_fixture',caseRef:record.id,shopRef:'aurora',messageRef:'out-'+state,
        versionRef:'v1',state,confirmed:!['requested','api_accepted','uncertain'].includes(state),
        ...(['requested','api_accepted','uncertain'].includes(state)?{}:{proofRef:'proof-v1'}),
        ...(state==='api_accepted'?{apiAckRef:'ack-v1'}:{})}};
    record.messages.push(message);
    const latest=latestConfirmedDemoMessage(record,'rafael','aurora');
    assert.equal(latest.id,['sent_confirmed','delivered','read'].includes(state)?message.id:inbound.id);
    record.messages.pop();
  }
  for(const side of ['in','ai','system']){
    const message={id:'fixture-'+side,side,body:'Registro autorizado',time:'11:01'};
    record.messages.push(message);
    assert.equal(latestConfirmedDemoMessage(record,'rafael','aurora').id,message.id);
  }
  record.messages.push({id:'local',side:'out',body:'NÃO ENVIADA',deliveryState:'local_demo_not_sent'});
  assert.equal(latestConfirmedDemoMessage(record,'rafael','aurora').id,'fixture-system');
  assert.equal(latestConfirmedDemoMessage(record,'daniel','aurora'),null);
  assert.equal(latestConfirmedDemoMessage(record,'rafael','horizonte'),null);
  record.messages=[];
  assert.equal(latestConfirmedDemoMessage(record,'rafael','aurora'),null);
});

test('REV-010: supervisor sees assignee projection without changing reading or reply evidence',()=>{
  const record=find('A-102');
  assert.equal(projectDemoAttention(record,'marina','aurora').kind,'unread');
  assert.equal(record.unread,2);
  record.unread=0;
  assert.equal(projectDemoAttention(record,'marina','aurora').kind,'none');
  record.demoReadByAssigned=true;
  assert.equal(projectDemoAttention(record,'marina','aurora').kind,'none');
  record.demoReadProjection={source:'local_fixture',actorId:record.assignedTo,caseId:record.id,shopId:record.shopId};
  assert.equal(projectDemoAttention(record,'marina','aurora').kind,'read_awaiting_reply');
  assert.equal(projectDemoAttention(record,'daniel','aurora').kind,'none');
  // Confirmed human reply is independent of who is supervising the conversation.
  const sent=find('A-105');sent.demoReadByAssigned=true;
  assert.equal(projectDemoAttention(sent,'marina','aurora').kind,'none');
  assert.equal(projectDemoAttention(sent,'rafael','aurora').kind,'none');
});

test('REV-015/016: expired composer presents zero, one or two eligible capabilities conservatively',()=>{
  const record=find('A-107');
  assert.deepEqual(projectedFollowupActions(record,'rafael','aurora'),['single_template','request_chain']);
  for(const action of ['single_template','request_chain']){
    record.allowedActionsProjection=[action];
    assert.deepEqual(projectedFollowupActions(record,'rafael','aurora'),[action]);
  }
  record.allowedActionsProjection=[];
  assert.deepEqual(projectedFollowupActions(record,'rafael','aurora'),[]);
  record.allowedActionsProjection=['single_template','request_chain'];
  for(const window of ['open','unknown','blocked']){
    record.metaWindowProjection=window;
    assert.deepEqual(projectedFollowupActions(record,'rafael','aurora'),[]);
  }
  record.metaWindowProjection='expired';
  assert.deepEqual(projectedFollowupActions(record,'marina','aurora'),[]);
  record.eligibleTemplatesProjection=[];
  assert.deepEqual(projectedFollowupActions(record,'rafael','aurora'),['request_chain']);
  record.inboxProjection='historical';
  assert.deepEqual(projectedFollowupActions(record,'rafael','aurora'),[]);
  assert.equal(mayMockFreeText(record,'rafael','aurora'),false);
  assert.equal(COMMERCIAL_STATUSES.length,8);
});

const env=installMockDOM();
await import('../app.mjs');
const get=id=>env.get(id);
const reset=()=>get('reset-app').click();

test('REV-001/003/007: shared continuous list starts active then history; role filters stay scoped',()=>{
  reset();assert.equal(env.cards().length,11);
  const names=env.cards().map(card=>card.textContent);
  assert.match(names.at(-1),/Exemplo 12/);
  assert.ok(env.cards().every(card=>!env.descendants(card).some(n=>n.classList.contains('avatar'))));
  assert.equal(get('commercial-filter').hidden,true);
  assert.equal(env.filters.find(n=>n.dataset.filter==='mine').hidden,true);
  env.selectActor('marina');assert.equal(env.cards().length,15);
  assert.equal(get('commercial-filter').hidden,false);
  assert.equal(env.filters.find(n=>n.dataset.filter==='mine').hidden,false);
  env.selectShop('horizonte');assert.equal(env.cards().length,2);
  env.selectShop('not-authorized');assert.equal(env.cards().length,2);
  env.selectActor('otavio');assert.equal(env.cards().length,0);
});

test('REV-007/010: direct history, unread and assignee-read-without-reply filters',()=>{
  reset();
  env.filters.find(n=>n.dataset.filter==='pending').click();assert.equal(env.cards().length,0);
  env.filters[0].click();env.openCase('Exemplo 02');
  env.filters.find(n=>n.dataset.filter==='pending').click();assert.equal(env.cards().length,1);
  env.selectActor('marina');
  env.filters.find(n=>n.dataset.filter==='pending').click();assert.equal(env.cards().length,1);
  reset();env.selectActor('marina');env.openCase('Exemplo 02');
  env.filters.find(n=>n.dataset.filter==='pending').click();assert.equal(env.cards().length,0);
  reset();env.inbox[1].click();assert.equal(env.cards().length,3);
  env.filters.find(n=>n.dataset.filter==='unread').click();assert.equal(env.cards().length,0);
});

test('REV-012/013/037: desktop X and name control preserve case, note draft, text and focus',()=>{
  reset();env.openCase('Exemplo 02');
  get('message-input').value='Rascunho 🙂';
  get('thread-title').click();
  const notes=env.descendants(get('detail-content')).find(n=>n.textContent==='Notas');notes.click();
  const textarea=get('detail-content').querySelector('#note-text');textarea.value='Nota não submetida';
  get('detail-close').click();
  assert.equal(get('visual-app').classList.contains('details-hidden'),true);
  assert.equal(env.document.activeElement,get('thread-title'));
  assert.equal(get('thread-title').getAttribute('aria-expanded'),'false');
  get('thread-title').click();
  assert.equal(textarea.value,'Nota não submetida');
  assert.equal(get('message-input').value,'Rascunho 🙂');
  assert.match(get('thread-meta').textContent,/A-102/);
  assert.ok(env.descendants(get('thread-actions')).some(n=>n.id==='request-completion'));
  assert.ok(!env.descendants(get('workflow-bar')).some(n=>n.id==='request-completion'));
});

test('REV-017: sold/lost compact strip is separate from Meta and human completion',()=>{
  for(const [name,outcome] of [['Exemplo 16','vendido'],['Exemplo 12','perdido']]){
    reset();env.openCase(name);
    assert.equal(get('terminal-banner').hidden,false);
    assert.equal(get('terminal-banner').dataset.outcome,outcome);
    assert.equal(get('message-input').disabled,true);
    assert.equal(get('thread-actions').children.length,0);
  }
  reset();env.openCase('Exemplo 09');
  assert.equal(get('terminal-banner').hidden,true);
  assert.equal(get('message-input').disabled,true);
});


test('REV-008: explicit demo loading hides rows and recovers within the authorized scope',()=>{
  reset();get('demo-list-state').value='loading';get('demo-list-state').fire('change');
  assert.equal(env.cards().length,0);
  assert.equal(get('conversation-items').getAttribute('aria-busy'),'true');
  assert.match(get('conversation-items').textContent,/Carregando/);
  env.selectActor('marina');
  assert.equal(get('conversation-items').getAttribute('aria-busy'),'false');
  assert.equal(env.cards().length,15);
});
