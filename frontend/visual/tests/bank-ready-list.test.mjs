import test from 'node:test';
import assert from 'node:assert/strict';
import {copyCFDemoFixtures} from '../cf-op-02.mjs';
import {withRevisionScenes} from '../revision-fixtures.mjs';
import {projectBankReadyList,bankReadyCaseForSelection,isBankReadyForRegistration}
  from '../bank-ready-list.mjs';

const sample=()=>withRevisionScenes(copyCFDemoFixtures());
const row=(rows,id)=>rows.find(r=>r.id===id);

test('BANCO-01: fila exibe somente nomes de cadastros com aptidão S0 confirmada',()=>{
 const records=sample(),list=projectBankReadyList(records,'rafael','aurora');
 assert.deepEqual(list,[{id:'A-114',name:row(records,'A-114').name}]);
 assert.deepEqual(Object.keys(list[0]).sort(),['id','name']);
 assert.equal(list.some(item=>/pronto|pendente|retorno/i.test(item.name)),false);
 assert.equal(projectBankReadyList(records,'marina','aurora').length,0);
 assert.equal(projectBankReadyList(records,'rafael','horizonte').length,0);
});
test('BANCO-01: ficha parcial, incompleta ou sem aptidão não entra na fila',()=>{
 const records=sample(),ready=row(records,'A-114');
 for(const mutation of [
   {bankReadinessProjection:{...ready.bankReadinessProjection,confirmed:false}},
   {bankReadinessProjection:{...ready.bankReadinessProjection,formVersionRef:'stale'}},
   {registrationProjection:{...ready.registrationProjection,confirmedPersisted:false}},
   {registrationProjection:{...ready.registrationProjection,state:'processing'}},
   {bankReadinessProjection:null},
   {inboxProjection:'historical'}
 ]){
   const candidate={...ready,...mutation};
   const staged=records.map(x=>x.id===ready.id?candidate:x);
   assert.equal(isBankReadyForRegistration(candidate,staged,'rafael','aurora'),false,
      Object.keys(mutation)[0]);
 }
 assert.equal(isBankReadyForRegistration(row(records,'A-108'),records,'rafael','aurora'),false);
});
test('BANCO-01: já enviado, em espera, em registro incerto ou vendido não entra',()=>{
 const records=sample(),ready=row(records,'A-114');
 for(const status of ['cadastro enviado ao banco','vendido','perdido']){
   const altered={...ready,status};
   assert.equal(isBankReadyForRegistration(altered,records.map(x=>x.id===ready.id?altered:x),'rafael','aurora'),false);
 }
 for(const phase of ['submission_requested','submission_verified','reply_pending','reply_verified','unverified']){
   const altered={...ready,bankProjection:{phase}};
   assert.equal(isBankReadyForRegistration(altered,records.map(x=>x.id===ready.id?altered:x),'rafael','aurora'),false,phase);
 }
});
test('BANCO-01: seleção não revela ficha fora da fila ou a supervisor',()=>{
 const records=sample();
 assert.equal(bankReadyCaseForSelection(records,'rafael','aurora','A-114')?.id,'A-114');
 for(const [actor,shop,caseId] of [
   ['marina','aurora','A-114'],['rafael','horizonte','A-114'],
   ['rafael','aurora','A-105'],['rafael','aurora','A-108'],
   ['daniel','aurora','A-114'],['rafael','aurora','A-999']
 ])assert.equal(bankReadyCaseForSelection(records,actor,shop,caseId),null);
});
