/** Projeções conservadoras EXCLUSIVAMENTE SINTÉTICAS para FV-REV-01/2.
 * Não é API, autorização real, relógio de agenda, auditoria S0 ou motor de casos.
 */
import { visibleConversations } from './fixtures.mjs';
import { projectMockHumanCycleHistory, projectMockClarificationScene } from './human-cycle-view.mjs';
import { registrationProjectionFor } from './registration-view.mjs';
import { postmarkViewFor } from './postmark-view.mjs';

const relationshipAllowed = (record, records, actorId, shopId) => {
  if(!record)return false;
  const base=visibleConversations(records,actorId,shopId).find(row=>row.id===record.id);
  if(!base)return false;
  if(base===record)return true;
  // Alternativa já autorizada na fixture, sem copiar publicações/eventos de outro caso.
  const scene=projectMockClarificationScene(base,actorId,shopId);
  return Boolean(scene && record.shopId===base.shopId && record.assignedTo===base.assignedTo &&
    record.reviewSceneVersion===scene.reviewSceneVersion &&
    record.reviewCutoffCandidateRef===scene.reviewCutoffCandidateRef &&
    record.relationshipProjection===base.relationshipProjection &&
    record.aiCommunicationsProjection===base.aiCommunicationsProjection);
};
const relationshipText = value => typeof value==='string' && value.trim() ? value.trim() : null;
export const ATTEMPT_STATES = Object.freeze({
  scheduled:'Agendada (projeção)', pending:'Ainda não agendada · horário pendente', requested:'Solicitada',
  queued:'Solicitada · aguardando execução', executing:'Em execução',
  sent_confirmed:'Envio confirmado na fixture', failed:'Falha', uncertain:'Incerta',
  cancelled:'Cancelada', canceled:'Cancelada'
});

export function aiCommunicationsFor(record, records, actorId, shopId) {
  if(!relationshipAllowed(record,records,actorId,shopId))return [];
  const projection=record.aiCommunicationsProjection;
  const entries=[];
  const registration=registrationProjectionFor(record,actorId,shopId);
  const seen=new Set();
  if(projection?.origin==='s0_fixture' && projection.caseId===record.id &&
     projection.shopId===shopId && relationshipText(projection.versionRef)) {
    for(const entry of Array.isArray(projection.entries)?projection.entries:[]) {
      if(!entry || !['F01','F02','F03'].includes(entry.source) || entry.published!==true ||
         !relationshipText(entry.id) || seen.has(entry.id) || !relationshipText(entry.versionRef) ||
         !relationshipText(entry.content) || !['case','assignee'].includes(entry.audience) ||
         (entry.audience==='assignee' && record.assignedTo!==actorId))continue;
      if(entry.source==='F03' && (entry.audience!=='assignee' || entry.resultConfirmed!==true ||
        registration.visibility!=='detail' || !registration.confirmedPersisted ||
        entry.formVersionRef!==registration.formVersionRef))continue;
      seen.add(entry.id);
      entries.push(Object.freeze({id:entry.id,source:entry.source,content:entry.content,
        time:relationshipText(entry.time)??'Horário não informado',synthetic:true}));
    }
  }
  // F03 não conversa com o cliente. Só resultados já confirmados e autorizados.
  const cycles=projectMockHumanCycleHistory(record,actorId,shopId);
  for(const event of cycles.events) entries.push(Object.freeze({
    id:event.completionId,source:'F03',time:'Conclusão fictícia '+event.completionId,
    content:'Resultado '+event.extractionState+' · versão '+event.resultVersionRef+
      '. Projeção autorizada; nenhum diálogo da F03 com o cliente.',synthetic:true}));
  // Persisted form alone proves neither authorship nor a published F03 result.
  return entries;
}

export function operationalHistoryFor(record, records, actorId, shopId, processing=null, localRequest=null) {
  if(!relationshipAllowed(record,records,actorId,shopId))return {events:[],future:[],related:null};
  const projection=record.relationshipProjection;
  const events=[], future=[], seen=new Set();
  const kinds=['lead','f01_started','handoff','assignment','transfer','redistribution',
    'human_completion','registration','bank_submission','bank_reply','sold','lost','customer_return','human_cycle'];
  const projectionValid=projection?.origin==='s0_fixture' && projection.confirmed===true &&
     projection.caseId===record.id && projection.shopId===shopId &&
     relationshipText(projection.versionRef) && relationshipText(projection.customerRef);
  if(projectionValid){
    for(const event of Array.isArray(projection.events)?projection.events:[]){
      if(!event || event.origin!=='s0_fixture' || event.confirmed!==true || event.state!=='confirmed' ||
         !kinds.includes(event.kind) || !relationshipText(event.id) || seen.has(event.id) ||
         !relationshipText(event.label) || !relationshipText(event.versionRef) || !Number.isFinite(event.order))continue;
      if(['sold','lost'].includes(event.kind) && (event.resultConfirmed!==true ||
         record.status!==(event.kind==='sold'?'vendido':'perdido')))continue;
      if(event.kind==='registration'){
        const registration=registrationProjectionFor(record,actorId,shopId);
        if(event.audience!=='assignee' || event.resultConfirmed!==true || event.source!=='F03' ||
          registration.visibility!=='detail' || !registration.confirmedPersisted ||
          event.formVersionRef!==registration.formVersionRef)continue;
      }
      seen.add(event.id);
      events.push({id:event.id,label:event.label,time:relationshipText(event.time)??'Horário não informado',
        order:event.order,sequenceConfirmed:true,state:'confirmed',statusLabel:'Confirmado na fixture',kind:event.kind});
    }
  }
  for(const event of projectMockHumanCycleHistory(record,actorId,shopId).events) {
    events.push({id:event.completionId,label:'Conclusão humana '+event.completionId+
      ' · atualização F03 '+event.extractionState+' · versão '+event.resultVersionRef,
      time:'Recorte confirmado na fixture '+event.cutoffMessageRef,state:'confirmed',
      statusLabel:'Confirmado na fixture',kind:'registration'});
  }
  // Manter evidências do plano anterior mesmo quando há um novo pedido LOCAL.
  for(const [index,attempt] of (record.followupProjection?.attempts??[]).entries()){
    if(!attempt || !relationshipText(attempt.label))continue;
    const planCancelled=['cancelled','canceled'].includes(record.followupProjection?.state);
    const rawState=planCancelled && ['scheduled','pending','queued','requested'].includes(attempt.state)?'cancelled':attempt.state;
    const state=Object.hasOwn(ATTEMPT_STATES,rawState)?rawState:'uncertain';
    const entry={id:'followup-'+record.id+'-'+index,kind:'followup',state,
      statusLabel:ATTEMPT_STATES[state],label:attempt.label+' · '+(relationshipText(attempt.template)??'Template não informado'),
      time:relationshipText(attempt.time)??'Horário não informado'};
    if(['scheduled','pending'].includes(state))future.push(entry);else events.push(entry);
  }
  if(localRequest)events.push({id:'local-followup-'+record.id,kind:'request',state:'requested',
    label:localRequest.kind==='request_chain'?'Solicitação de cadeia fictícia':'Solicitação de template individual fictícia',
    time:'Somente neste navegador',statusLabel:'SOLICITADO (demo), não agendado, não transmitido e nunca ENVIADO'});
  if(processing)events.push({id:'local-extraction-'+record.id,kind:'extraction',state:
    ['failed','uncertain'].includes(processing.kind)?processing.kind:'requested',
    label:'Extração pós-atendimento · cenário '+processing.kind+' (simulado)',
    time:'Somente neste navegador',statusLabel:'Solicitação local · sem confirmação S0/F03'});
  // The synthetic sequence is explicit and bound to the same case/shop/version.
  // Never parse display labels ('Hoje', 'Arquivo', 'Prova') as timestamps or infer
  // cross-source causality from concatenation. Unsequenced records get their own group.
  const sequence=projectionValid && projection.sequence;
  const ids=new Set(events.map(event=>event.id));
  const validSequence=Array.isArray(sequence) && sequence.length>0 &&
    sequence.every(id=>relationshipText(id) && ids.has(id)) && new Set(sequence).size===sequence.length;
  const positions=new Map(validSequence ? sequence.map((id,index)=>[id,index]) : []);
  for(const entry of events){
    entry.sequenceConfirmed=positions.has(entry.id) || (entry.sequenceConfirmed===true && !validSequence);
    if(positions.has(entry.id))entry.order=positions.get(entry.id);
  }
  events.sort((a,b)=>Number(b.sequenceConfirmed)-Number(a.sequenceConfirmed) ||
    (a.sequenceConfirmed && b.sequenceConfirmed ? a.order-b.order : 0));
  const related=postmarkViewFor(record,records,actorId,shopId);
  return {events,future,related};
}

/** Aptidão é uma evidência sintética versionada; não é capacidade de remessa. */
export function bankReadinessFor(record, records, actorId, shopId){
  if(!relationshipAllowed(record,records,actorId,shopId))return false;
  const registration=registrationProjectionFor(record,actorId,shopId),ready=record.bankReadinessProjection;
  return Boolean(registration.visibility==='detail' && registration.confirmedPersisted &&
    ready?.origin==='s0_fixture' && ready.caseId===record.id && ready.shopId===shopId &&
    ready.confirmed===true && relationshipText(ready.versionRef) &&
    ready.formVersionRef===registration.formVersionRef);
}
