import test from 'node:test';
import assert from 'node:assert/strict';
import { copyCFDemoFixtures } from '../cf-op-02.mjs';
import { bankProjectionFor, bankPhaseCopy, bankCanMockWrite } from '../bank-view.mjs';

const record=()=>copyCFDemoFixtures().find(x=>x.id==='A-105');

test('O4-01: remessa só confirmada com prova sintética, autor humano e versão',()=>{
  const p=bankProjectionFor(record(),'rafael','aurora');
  assert.equal(p.visibility,'detail');
  assert.equal(p.phase,'reply_pending');
  assert.equal(p.submissionConfirmed,true);
  assert.equal(p.replyConfirmed,false);
  assert.equal(p.submissionSummary.versionRef,'bank-demo-v1');
  assert.equal(p.replySummary,null);
  assert.match(bankPhaseCopy(p).description,/não há decisão bancária/i);
});

test('O4-02: gestora em supervisão só vê resumo, sem versões ou prova D4',()=>{
  const p=bankProjectionFor(record(),'marina','aurora');
  assert.equal(p.visibility,'summary');
  assert.equal(p.submissionConfirmed,false);
  assert.equal(p.replyConfirmed,false);
  assert.equal(p.submissionSummary,null);
  assert.equal(p.replySummary,null);
  assert.equal(p.phase,'reply_pending');
});

test('O4-03: loja não concedida e ator suspenso não enxergam o caso',()=>{
  for(const [actor,shop] of [['rafael','horizonte'],['otavio','aurora'],['inexistente','aurora']]){
    const p=bankProjectionFor(record(),actor,shop);
    assert.equal(p.visibility,'forbidden');
    assert.equal(p.submissionSummary,null);
    assert.equal(p.replySummary,null);
  }
});

test('O4-04: pedido, fila ou status comercial não são prova de remessa',()=>{
  const data=record();
  for(const phase of ['submission_requested','not_submitted','unverified','unavailable']){
    const p=bankProjectionFor({...data,bankProjection:{...data.bankProjection,phase}},'rafael','aurora');
    assert.equal(p.submissionConfirmed,false);
    assert.equal(p.replyConfirmed,false);
    assert.equal(p.submissionSummary,null);
  }
});

test('O4-05: versão vazia ou ação não humana impede remessa comprovada',()=>{
  const data=record();
  for(const mutation of [
    {submissionVersionRef:' '},{submittedByAuthorizedHuman:false},{submissionProofState:'pending'}
  ]){
    const p=bankProjectionFor({...data,bankProjection:{...data.bankProjection,...mutation}},'rafael','aurora');
    assert.equal(p.submissionConfirmed,false);
    assert.equal(p.replyConfirmed,false);
  }
});

test('O4-06: retorno só é confirmado com prova adicional e registro humano',()=>{
  const base=record();
  const projection={...base.bankProjection,phase:'reply_verified',replyVersionRef:'reply-demo-v1',
    replyProofState:'verified',replyRecordedByHuman:true};
  const confirmed=bankProjectionFor({...base,bankProjection:projection},'rafael','aurora');
  assert.equal(confirmed.replyConfirmed,true);
  assert.equal(confirmed.replySummary.versionRef,'reply-demo-v1');
  for(const mutation of [{replyProofState:'queued'},{replyRecordedByHuman:false},{replyVersionRef:''}]){
    const result=bankProjectionFor({...base,bankProjection:{...projection,...mutation}},'rafael','aurora');
    assert.equal(result.replyConfirmed,false);
    assert.equal(result.replySummary,null);
  }
});

test('O4-07: nenhuma transição comercial e nenhum comando bancário no browser',()=>{
  const data=record();
  const status=data.status;
  bankProjectionFor(data,'rafael','aurora');
  assert.equal(data.status,status);
  assert.equal(bankCanMockWrite(),false);
});

test('O4-08: resposta bancária desconhecida não pode virar aprovação/recusa',()=>{
  const data=record();
  const projection={...data.bankProjection,phase:'reply_verified',replyProofState:'verified',
    replyRecordedByHuman:false,replyVersionRef:'reply-demo-v1',outcome:'aprovado'};
  const result=bankProjectionFor({...data,bankProjection:projection},'rafael','aurora');
  assert.equal(result.replyConfirmed,false);
  assert.doesNotMatch(bankPhaseCopy(result).title,/aprova|recusa|vendid/i);
});

test('O4-09: caso sem projeção não afirma remessa ou retorno',()=>{
  const p=bankProjectionFor(copyCFDemoFixtures().find(x=>x.id==='A-108'),'rafael','aurora');
  assert.equal(p.phase,'unavailable');
  assert.equal(p.submissionConfirmed,false);
  assert.equal(p.replyConfirmed,false);
  assert.match(bankPhaseCopy(p).title,/não confirmada/i);
});

test('operador não designado não recebe nem resumo operacional de banco',()=>{
  const p=bankProjectionFor(record(),'bianca','aurora');
  assert.equal(p.visibility,'forbidden');
  assert.equal(p.submissionConfirmed,false);
  assert.equal(p.submissionSummary,null);
  assert.equal(p.replySummary,null);
});
