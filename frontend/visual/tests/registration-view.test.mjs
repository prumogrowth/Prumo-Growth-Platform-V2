import test from 'node:test';
import assert from 'node:assert/strict';
import { copyCFDemoFixtures } from '../cf-op-02.mjs';
import { mayViewMockRegistrationDetail, registrationProjectionFor, registrationStateCopy } from '../registration-view.mjs';

const sample=()=>copyCFDemoFixtures().find(x=>x.id==='A-108');

test('operador atribuído vê só campo fictício aplicado, versão e proveniência',()=>{
  const detail=registrationProjectionFor(sample(),'rafael','aurora');
  assert.equal(detail.visibility,'detail');
  assert.equal(detail.confirmedPersisted,true);
  assert.equal(detail.formVersionRef,'v1-ficticia');
  assert.equal(detail.fields.length,1);
  assert.equal(detail.fields[0].safeDisplayValue,'Valor fictício confirmado');
  assert.equal(detail.fields[0].sourceRef,'a108-1');
  assert.equal(detail.fields[0].validationState,'applied');
  assert.equal(detail.missing.length,1);
  assert.equal(detail.conflicts.length,1);
});

test('supervisora não autoatribuída recebe somente resumo, sem D3 ou fontes',()=>{
  const summary=registrationProjectionFor(sample(),'marina','aurora');
  assert.equal(summary.visibility,'summary');
  assert.equal(summary.state,'partial');
  assert.equal(summary.formVersionRef,null);
  assert.deepEqual(summary.fields,[]);
  assert.deepEqual(summary.missing,[]);
  assert.deepEqual(summary.conflicts,[]);
  assert.equal(summary.confirmedPersisted,true);
  assert.equal(mayViewMockRegistrationDetail(sample(),'marina','aurora'),false);
});

test('gestor autoatribuído pode atuar como operador apenas no caso ativo',()=>{
  const assigned={...sample(),assignedTo:'marina'};
  assert.equal(registrationProjectionFor(assigned,'marina','aurora').visibility,'detail');
  assert.equal(registrationProjectionFor({...assigned,inboxProjection:'historical'},'marina','aurora').visibility,'summary');
});

test('perfis suspensos e lojas não concedidas não recebem nem resumo da ficha',()=>{
  for (const [actor,shop] of [['otavio','aurora'],['rafael','horizonte'],['inexistente','aurora']]){
    const result=registrationProjectionFor(sample(),actor,shop);
    assert.equal(result.visibility,'forbidden');
    assert.equal(result.confirmedPersisted,false);
    assert.deepEqual(result.fields,[]);
  }
});

test('sem versão persistida, modelo não promove proposta para valor salvo',()=>{
  const record=sample();
  record.registrationProjection={...record.registrationProjection,formVersionRef:null};
  const result=registrationProjectionFor(record,'rafael','aurora');
  assert.equal(result.confirmedPersisted,false);
  assert.deepEqual(result.fields,[]);
  assert.equal(result.formVersionRef,null);
});

test('campo sem fonte ou apenas proposto não é exibido como valor validado',()=>{
  const record=sample();
  record.registrationProjection.fields.push(
    {key:'bad',label:'Sem fonte',safeDisplayValue:'Não permitido',validationState:'applied'});
  const result=registrationProjectionFor(record,'rafael','aurora');
  assert.equal(result.fields.length,1);
  assert.ok(result.fields.every(x=>x.sourceRef==='a108-1'));
});

test('estado desconhecido não afirma cadastro ou persistência',()=>{
  const record=sample();
  record.registrationProjection={state:'INVALID',confirmedPersisted:true,formVersionRef:'v5',
    fields:[{key:'a',label:'A',safeDisplayValue:'X',sourceRef:'m',validationState:'applied'}]};
  const result=registrationProjectionFor(record,'rafael','aurora');
  assert.equal(result.state,'unavailable');
  assert.equal(result.confirmedPersisted,false);
  assert.deepEqual(result.fields,[]);
  assert.match(registrationStateCopy(result).title,/não confirmado/);
});

test('processamento e falha não equivalem a ficha preenchida',()=>{
  for(const state of ['processing','failed','stale']){
    const record=sample();
    record.registrationProjection={...record.registrationProjection,state};
    const result=registrationProjectionFor(record,'rafael','aurora');
    assert.equal(result.confirmedPersisted,false);
    assert.deepEqual(result.fields,[]);
    assert.ok(registrationStateCopy(result).title.length>0);
  }
});
