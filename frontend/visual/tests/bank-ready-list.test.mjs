import test from 'node:test';
import assert from 'node:assert/strict';
import {copyCFDemoFixtures} from '../cf-op-02.mjs';
import {withRevisionScenes} from '../revision-fixtures.mjs';
import {projectBankReadyList,bankReadyCaseForSelection,isBankReadyForRegistration}
  from '../bank-ready-list.mjs';

const sample=()=>withRevisionScenes(copyCFDemoFixtures());
const row=(rows,id)=>rows.find(r=>r.id===id);
/** Teste isolado: caso novo fictício sem remessa prévia.
 * Não cria autorização real, não muda as fixtures de produto nem é contrato S0.
 */
function isolatedNewSubmission(){
 const records=sample(),reference=row(records,'A-114'),caseId='A-118';
 const candidate={
   ...structuredClone(reference),id:caseId,name:'Cliente Exemplo Novo',
   postmarkProjection:undefined,customerDossierProjection:undefined,
   bankProjection:{phase:'not_submitted'},
   relationshipProjection:{...reference.relationshipProjection,caseId,
      customerRef:'cliente-novo-isolado-aurora'},
   bankReadinessProjection:{...reference.bankReadinessProjection,caseId}
 };
 return {records:[...records,candidate],candidate};
}

test('BANCO-02: cenário base pós-remessa não é implicitamente apto para reenvio',()=>{
 const records=sample(),list=projectBankReadyList(records,'rafael','aurora');
 assert.deepEqual(list,[]);
 assert.equal(bankReadyCaseForSelection(records,'rafael','aurora','A-114'),null);
 assert.equal(isBankReadyForRegistration(row(records,'A-114'),records,'rafael','aurora'),false);
});
test('BANCO-02: somente nome e chave interna, com confirmação explícita de não envio',()=>{
 const {records,candidate}=isolatedNewSubmission();
 const list=projectBankReadyList(records,'rafael','aurora');
 assert.deepEqual(list,[{id:'A-118',name:candidate.name}]);
 assert.deepEqual(Object.keys(list[0]).sort(),['id','name']);
 assert.equal(bankReadyCaseForSelection(records,'rafael','aurora','A-118'),candidate);
 assert.equal(projectBankReadyList(records,'marina','aurora').length,0);
 assert.equal(projectBankReadyList(records,'rafael','horizonte').length,0);
});
test('BANCO-02: estado desconhecido, remessa incerta, iniciada ou comprovada excluídos',()=>{
 const {records,candidate}=isolatedNewSubmission();
 for(const phase of ['unavailable','submission_requested','submission_verified','reply_pending','reply_verified','unverified']){
   const altered={...candidate,bankProjection:{phase}};
   const rows=records.map(x=>x.id===candidate.id?altered:x);
   assert.equal(isBankReadyForRegistration(altered,rows,'rafael','aurora'),false,phase);
 }
 const missing={...candidate,bankProjection:undefined};
 assert.equal(isBankReadyForRegistration(missing,records.map(x=>x.id===candidate.id?missing:x),'rafael','aurora'),false);
});
test('BANCO-02: ficha sem persistência ou contraditória não passa',()=>{
 const {records,candidate}=isolatedNewSubmission();
 for(const [title,mutation] of [
  ['readiness unconfirmed',{bankReadinessProjection:{...candidate.bankReadinessProjection,confirmed:false}}],
  ['readiness stale',{bankReadinessProjection:{...candidate.bankReadinessProjection,formVersionRef:'stale'}}],
  ['registration unconfirmed',{registrationProjection:{...candidate.registrationProjection,confirmedPersisted:false}}],
  ['registration processing',{registrationProjection:{...candidate.registrationProjection,state:'processing'}}],
  ['registration partial',{registrationProjection:{...candidate.registrationProjection,state:'partial'}}],
  ['missing field',{registrationProjection:{...candidate.registrationProjection,missing:['campo obrigatório em análise']}}],
  ['conflict',{registrationProjection:{...candidate.registrationProjection,conflicts:['informação em conflito']}}],
  ['no readiness',{bankReadinessProjection:null}],
  ['historical',{inboxProjection:'historical'}]
 ]){
   const altered={...candidate,...mutation},rows=records.map(x=>x.id===candidate.id?altered:x);
   assert.equal(isBankReadyForRegistration(altered,rows,'rafael','aurora'),false,title);
 }
});
test('BANCO-02: remessa anterior do próprio ciclo ou dossiê exige contrato S0 específico',()=>{
 const {records,candidate}=isolatedNewSubmission();
 for(const [title,mutation] of [
  ['postmark',{postmarkProjection:{direction:'continuation',source:'bank_submitted',originCaseRef:'A-105'}}],
  ['post-sale continuation',{postmarkProjection:{direction:'continuation',source:'sold',originCaseRef:'A-115'}}],
  ['snapshot',{customerDossierProjection:{bankSnapshots:[{bankSubmissionVersionRef:'remessa-anterior'}]}}]
 ]){
   const altered={...candidate,...mutation},rows=records.map(x=>x.id===candidate.id?altered:x);
   assert.equal(isBankReadyForRegistration(altered,rows,'rafael','aurora'),false,title);
 }
});
test('BANCO-02: acesso da ficha exige recheck de seleção na loja e perfil',()=>{
 const {records}=isolatedNewSubmission();
 for(const [actor,shop,caseId] of [
  ['marina','aurora','A-118'],['rafael','horizonte','A-118'],
  ['rafael','aurora','A-105'],['rafael','aurora','A-114'],
  ['daniel','aurora','A-118'],['rafael','aurora','A-999']
 ])assert.equal(bankReadyCaseForSelection(records,actor,shop,caseId),null);
});
