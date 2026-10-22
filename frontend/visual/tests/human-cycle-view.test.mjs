import assert from 'node:assert/strict';
import test from 'node:test';
import {copyCFDemoFixtures} from '../cf-op-02.mjs';
import {projectMockHumanCycleHistory,projectMockClarificationScene,
  stageMockRepeatCompletion,projectMockCustomerDossier} from '../human-cycle-view.mjs';

const fixture=(id='A-108')=>copyCFDemoFixtures().find(row=>row.id===id);

test('FV-22-05 duas conclusões reais APENAS na fixture possuem requests, cutoffs e versões distintos',()=>{
  const view=projectMockHumanCycleHistory(fixture(),'rafael','aurora');
  assert.equal(view.visibility,'detail');
  assert.equal(view.events.length,2);
  assert.deepEqual(view.events.map(x=>x.requestId),['f03-a108-1','f03-a108-2']);
  assert.deepEqual(view.events.map(x=>x.cutoffMessageRef),['a108-1','a108-2']);
  assert.deepEqual(view.events.map(x=>x.resultVersionRef),['v0-ficticia','v1-ficticia']);
  assert.ok(view.events.every(x=>x.humanCompletionConfirmed && x.source==='s0_fixture'));
});

test('FV-22-05 cutoff anterior não muda quando mensagens posteriores aparecem',()=>{
  const record=fixture(),before=projectMockHumanCycleHistory(record,'rafael','aurora');
  record.messages.push({id:'new-later',side:'in',body:'Depois do corte',time:'Depois'});
  const after=projectMockHumanCycleHistory(record,'rafael','aurora');
  assert.deepEqual(after.events,before.events);
  assert.equal(after.events[0].cutoffMessageRef,'a108-1');
  assert.notEqual(after.events[0].cutoffMessageRef,'new-later');
});

test('FV-22-05 falha fechada para evento sem prova, cutoff sem mensagem e duplicado',()=>{
  for(const mutate of [
    x=>{x.events[0].humanCompletionConfirmed=false;},
    x=>{x.events[0].cutoffMessageRef='future-not-in-log';},
    x=>{x.events[1].cutoffMessageRef=x.events[0].cutoffMessageRef;},
    x=>{x.events[1].requestId=x.events[0].requestId;},
    x=>{x.events[1].origin='browser';},
    x=>{x.shopId='horizonte';}
  ]){
    const record=fixture();
    mutate(record.humanCycleProjection);
    assert.equal(projectMockHumanCycleHistory(record,'rafael','aurora').visibility,'forbidden');
  }
});

test('FV-22-06 cenário de esclarecimento não reabre no S0 e conserva projeção original',()=>{
  const record=fixture(),before=JSON.stringify(record);
  const alternative=projectMockClarificationScene(record,'rafael','aurora');
  assert.ok(alternative);
  assert.equal(record.humanCompletionProjection,'completed');
  assert.equal(alternative.humanCompletionProjection,'pending');
  assert.equal(alternative.messages.at(-1).id,'a108-3');
  assert.equal(alternative.reviewCutoffCandidateRef,'a108-3');
  assert.equal(JSON.stringify(record),before);
  assert.equal(alternative.registrationProjection.formVersionRef,'v1-ficticia');
});

test('FV-22-05 terceira solicitação candidata sem confirmação, F03 ou persistência',()=>{
  const preview=projectMockClarificationScene(fixture(),'rafael','aurora');
  const staged=stageMockRepeatCompletion(preview,'rafael','aurora');
  assert.equal(staged.kind,'accepted');
  assert.equal(staged.candidateCutoffRef,'a108-3');
  assert.equal(staged.confirmedByS0,false);
  assert.equal(staged.persisted,false);
  assert.equal(staged.source,'local_demo');
  assert.equal(stageMockRepeatCompletion(fixture(),'rafael','aurora'),null);
  preview.messages.push({id:'demo-unsent',side:'out',deliveryState:'local_demo_not_sent'});
  assert.equal(stageMockRepeatCompletion(preview,'rafael','aurora').candidateCutoffRef,'a108-3');
  preview.messages.push({id:'other-confirmed-message',side:'in'});
  assert.equal(stageMockRepeatCompletion(preview,'rafael','aurora'),null);
});

test('FV-22-06 só titular ativo da mesma loja acessa retorno; supervisor não',()=>{
  assert.equal(projectMockClarificationScene(fixture(),'marina','aurora'),null);
  assert.equal(projectMockClarificationScene(fixture(),'bianca','aurora'),null);
  assert.equal(projectMockClarificationScene(fixture(),'rafael','horizonte'),null);
  const invalid=fixture();invalid.clarificationProjection.confirmed=false;
  assert.equal(projectMockClarificationScene(invalid,'rafael','aurora'),null);
});

test('FV-22-07 ficha viva versionada A-108 preserva versões e não inventa banco',()=>{
  const d=projectMockCustomerDossier(fixture(),'rafael','aurora');
  assert.equal(d.visibility,'detail');
  assert.equal(d.liveFormVersionRef,'v1-ficticia');
  assert.deepEqual(d.formHistory.map(x=>x.versionRef),['v0-ficticia','v1-ficticia']);
  assert.deepEqual(d.bankSnapshots,[]);
});

test('FV-22-07 após remessa, ficha mais recente NÃO reescreve snapshot bancário antigo',()=>{
  const d=projectMockCustomerDossier(fixture('A-114'),'rafael','aurora');
  assert.equal(d.visibility,'detail');
  assert.equal(d.liveFormVersionRef,'live-form-v2-demo');
  assert.equal(d.bankSnapshots[0].submissionCaseRef,'A-105');
  assert.equal(d.bankSnapshots[0].bankSubmissionVersionRef,'bank-demo-v1');
  assert.equal(d.bankSnapshots[0].frozenSnapshot,true);
  assert.notEqual(d.liveFormVersionRef,d.bankSnapshots[0].bankSubmissionVersionRef);
});

test('FV-22-07 concessão entre lojas e supervisão não expondo dossiê',()=>{
  assert.equal(projectMockCustomerDossier(fixture(),'marina','aurora').visibility,'forbidden');
  assert.equal(projectMockCustomerDossier(fixture(),'rafael','horizonte').visibility,'forbidden');
  assert.equal(projectMockCustomerDossier(fixture(),'bianca','aurora').visibility,'forbidden');
  const cross=fixture('A-114');cross.customerDossierProjection.bankSnapshots[0].shopId='horizonte';
  assert.equal(projectMockCustomerDossier(cross,'rafael','aurora').visibility,'forbidden');
});

test('FV-22-07 dossiê falha fechado sem confirmação de identidade/versão/snapshot',()=>{
  for(const mutation of [
    p=>{p.identityConfirmed=false;},p=>{p.liveFormVersionRef='inexistente';},
    p=>{p.authorizedCaseRefs=['A-105'];},
    p=>{p.formHistory[0].confirmedPersisted=false;},
    p=>{p.bankSnapshots[0].frozenSnapshot=false;}
  ]){
    const record=fixture('A-114');mutation(record.customerDossierProjection);
    assert.equal(projectMockCustomerDossier(record,'rafael','aurora').visibility,'forbidden');
  }
});

test('fixtures reiniciadas não compartilham histórico, recortes ou snapshots',()=>{
  const a=fixture('A-114'),b=fixture('A-114');
  a.customerDossierProjection.bankSnapshots[0].bankSubmissionVersionRef='ALTERADO';
  assert.equal(b.customerDossierProjection.bankSnapshots[0].bankSubmissionVersionRef,'bank-demo-v1');
});
