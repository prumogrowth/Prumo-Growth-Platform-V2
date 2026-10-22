/** FV-UI-019 — timeline de conclusões, F03 e ficha viva: PROJEÇÕES FICTÍCIAS.
 * Nenhum cutoff é calculado ou certificado no navegador. A S0 autentica ator,
 * versão física/lógica, autoriza acesso e sela cada evento de conclusão.
 */
import {getActor,hasMockCaseScope} from './fixtures.mjs';
import {isInActiveInbox} from './cf-op-02.mjs';
const empty=Object.freeze([]);
const deny=Object.freeze({visibility:'forbidden',events:empty,customer:null});
const str=x=>typeof x==='string' && x.trim()===x && x.length>0;
const activeAssigned=(record,actorId,shopId)=>{
  const actor=getActor(actorId);
  return Boolean(actor && hasMockCaseScope(record,actorId,shopId) &&
    record?.assignedTo===actorId && isInActiveInbox(record));
};

/** Os recortes são referências OPACAS fornecidas por uma fixture que simula S0.
 * Nem a posição de mensagens nem o relógio JS são usados como fonte de verdade.
 * O teste de ordem local é apenas consistência do cenário, não validação S0.
 */
export function projectMockHumanCycleHistory(record,actorId,shopId) {
  if(!activeAssigned(record,actorId,shopId))return deny;
  const p=record?.humanCycleProjection;
  if(!p || p.origin!=='s0_fixture' || p.caseId!==record.id ||
     p.shopId!==shopId || !str(p.customerRef) || !Array.isArray(p.events))return deny;
  const messageIds=(record.messages??[]).map(m=>m?.id);
  let prior=-1;
  const seen=new Set();
  const events=[];
  for(const event of p.events){
    if(!event || event.origin!=='s0_fixture' || !str(event.completionId) ||
       !str(event.requestId) || !str(event.cutoffMessageRef) ||
       !str(event.cutoffVersionRef) || !str(event.resultVersionRef) ||
       event.humanCompletionConfirmed!==true ||
       !['partial_confirmed','persisted_confirmed'].includes(event.extractionState) ||
       seen.has(event.completionId) || seen.has(event.requestId))return deny;
    const index=messageIds.indexOf(event.cutoffMessageRef);
    if(index<0 || index<=prior)return deny;
    prior=index;seen.add(event.completionId);seen.add(event.requestId);
    events.push(Object.freeze({
      completionId:event.completionId,requestId:event.requestId,
      cutoffMessageRef:event.cutoffMessageRef,cutoffVersionRef:event.cutoffVersionRef,
      resultVersionRef:event.resultVersionRef,extractionState:event.extractionState,
      humanCompletionConfirmed:true,source:'s0_fixture'
    }));
  }
  return Object.freeze({visibility:'detail',customer:p.customerRef,
    events:Object.freeze(events)});
}

/** Um retrato ALTERNATIVO já autorizado na fixture demonstra esclarecimento.
 * Não reabre realmente o atendimento nem altera a ficha ou o caso de origem.
 */
export function projectMockClarificationScene(record,actorId,shopId){
  if(!activeAssigned(record,actorId,shopId))return null;
  const p=record?.clarificationProjection;
  if(!p || p.origin!=='s0_fixture' || p.confirmed!==true ||
     p.caseId!==record.id || p.shopId!==shopId || p.assignedTo!==actorId ||
     p.state!=='human_followup_authorized' || !str(p.versionRef) ||
     !str(p.cutoffCandidateRef) || p.metaWindowProjection!=='open' ||
     !p.inbound || p.inbound.id!==p.cutoffCandidateRef ||
     p.inbound.side!=='in' || !str(p.inbound.body) ||
     (record.messages??[]).some(m=>m.id===p.inbound.id))return null;
  return {
    ...record, messages:[...record.messages.map(m=>({...m})),{...p.inbound}],
    // Alternativa DEMO; não escrever estes valores em record nem em S0.
    humanCompletionProjection:'pending',
    allowedActionsProjection:['free_text','complete'],
    reviewSceneVersion:p.versionRef,
    reviewCutoffCandidateRef:p.cutoffCandidateRef
  };
}

/** Solicitação CANDIDATA da nova conclusão; não dispara F03, não persiste.
 * Somente quando o último evento confirmado DA CENA foi fornecido pela fixture.
 */
export function stageMockRepeatCompletion(record,actorId,shopId){
  if(!activeAssigned(record,actorId,shopId) ||
     record.humanCompletionProjection!=='pending' ||
     !str(record.reviewSceneVersion) || !str(record.reviewCutoffCandidateRef))return null;
  const last=(record.messages??[]).filter(m=>m.deliveryState!=='local_demo_not_sent').at(-1);
  if(last?.id!==record.reviewCutoffCandidateRef)return null;
  return Object.freeze({kind:'accepted',requestId:'local-review-'+record.id+'-'+record.reviewSceneVersion,
    candidateCutoffRef:record.reviewCutoffCandidateRef,sceneVersion:record.reviewSceneVersion,
    confirmedByS0:false,source:'local_demo',persisted:false});
}

/** Dossiê de versão VIVA e snapshots preexistentes, exclusivamente projetados.
 * NUNCA recompor ficha pelo CPF/telefone, pelo nome, ou lendo casos de outra loja.
 * Dossiê só aparece ao titular autorizado do caso atual; resumo do supervisor
 * continua na função registrationProjectionFor sem dados D3/D4.
 */
export function projectMockCustomerDossier(record,actorId,shopId){
  if(!activeAssigned(record,actorId,shopId))return deny;
  const p=record?.customerDossierProjection;
  if(!p || p.origin!=='s0_fixture' || p.caseId!==record.id ||
     p.shopId!==shopId || p.identityConfirmed!==true ||
     !str(p.customerRef) || !str(p.liveFormVersionRef) ||
     !Array.isArray(p.formHistory) || !Array.isArray(p.bankSnapshots) ||
     !Array.isArray(p.authorizedCaseRefs))return deny;
  const seen=new Set();
  const versions=[];
  for(const v of p.formHistory){
    if(!v || !str(v.versionRef) || seen.has(v.versionRef) ||
       !str(v.cutoffRef) || v.confirmedPersisted!==true)return deny;
    seen.add(v.versionRef);
    versions.push(Object.freeze({versionRef:v.versionRef,cutoffRef:v.cutoffRef}));
  }
  if(!seen.has(p.liveFormVersionRef) ||
     !p.authorizedCaseRefs.includes(record.id) ||
     !p.authorizedCaseRefs.every(str))return deny;
  const bank=[];
  for(const snapshot of p.bankSnapshots){
    if(!snapshot || snapshot.origin!=='s0_fixture' ||
       snapshot.shopId!==shopId || !str(snapshot.submissionCaseRef) ||
       !str(snapshot.bankSubmissionVersionRef) ||
       snapshot.frozenSnapshot!==true ||
       !p.authorizedCaseRefs.includes(snapshot.submissionCaseRef))return deny;
    bank.push(Object.freeze({
      submissionCaseRef:snapshot.submissionCaseRef,
      bankSubmissionVersionRef:snapshot.bankSubmissionVersionRef,
      frozenSnapshot:true
    }));
  }
  return Object.freeze({visibility:'detail',customer:p.customerRef,
    liveFormVersionRef:p.liveFormVersionRef,
    formHistory:Object.freeze(versions),bankSnapshots:Object.freeze(bank),
    authorizedCaseRefs:Object.freeze([...p.authorizedCaseRefs])});
}
