/** FV-UI-016 — preview de pausa com casos SINTÉTICOS, exclusivamente leitura.
 * Não faz alterações em atribuições, conta, leads ou concessões.
 * S0/S1 é a única fonte futura de prova de contato e execução transacional.
 */
import { ACTORS, getActor, getShop, managedOperators, visibleConversations } from './fixtures.mjs';

export const PAUSE_PREVIEW_VERSION = 'fv-ui-016-demo/0.1';

/** Evidências de cenário fictício explicitamente fornecidas, nunca extraídas
 * de mensagens, status comercial, data ou abertura da conversa no browser.
 */
export const DEMO_PAUSE_EVIDENCE = Object.freeze([
  {caseId:'A-102',ownerId:'rafael',shopId:'aurora',version:'fx-a102-1',contactConfirmed:true},
  {caseId:'A-107',ownerId:'rafael',shopId:'aurora',version:'fx-a107-1',contactConfirmed:false},
  {caseId:'A-114',ownerId:'rafael',shopId:'aurora',version:'fx-a114-1',contactConfirmed:false},
  {caseId:'A-103',ownerId:'bianca',shopId:'aurora',version:'fx-a103-1',contactConfirmed:false},
  {caseId:'B-201',ownerId:'lia',shopId:'horizonte',version:'fx-b201-1',contactConfirmed:false},
  {caseId:'B-203',ownerId:'bianca',shopId:'horizonte',version:'fx-b203-1',contactConfirmed:true}
].map(item=>Object.freeze({...item,source:'s0_fixture'})));

const DENIED=Object.freeze({visibility:'forbidden',operatorId:null,summary:null,cases:Object.freeze([]),applied:false});
export const PAUSE_OUTCOMES=Object.freeze({
  retain_started:'Contato humano iniciado — manter atribuição',
  retain_no_recipient:'Sem substituto na equipe — manter atribuição',
  retain_unverified:'Sem prova suficiente — manter atribuição',
  retain_protected:'Ciclo bancário/terminal protegido — manter atribuição',
  proposed_same_team:'Candidato a redistribuição na equipe — não aplicado'
});
const active=row=>row?.inboxProjection==='active' && !['vendido','perdido'].includes(row.status);
const protectedCycle=row=>['cadastro enviado ao banco','vendido','perdido'].includes(row.status);

/** Escolha é só proposta de visualização; nunca gera um grant ou um comando. */
export function classifyPauseCase(row, proof, candidates, ownerId, managerId) {
  if(!row || !row.id || !row.shopId || row.assignedTo!==ownerId || !managerId ||
    !Array.isArray(candidates) || !active(row)) return 'retain_unverified';
  if(protectedCycle(row))return 'retain_protected';
  if(!proof || proof.source!=='s0_fixture' || proof.caseId!==row.id ||
    proof.ownerId!==ownerId || proof.shopId!==row.shopId ||
    typeof proof.version!=='string' || !proof.version.trim() ||
    typeof proof.contactConfirmed!=='boolean')return 'retain_unverified';
  if(proof.contactConfirmed)return 'retain_started';
  const eligible=candidates.some(person=>person && person.id!==ownerId &&
    person.role==='operador' && person.managerId===managerId &&
    person.teamState==='active' && person.leadIntakeProjection==='receiving' &&
    Array.isArray(person.shops) && person.shops.includes(row.shopId));
  return eligible?'proposed_same_team':'retain_no_recipient';
}

/** Envelope de prévia: só considera casos autorizados no frontend fictício;
 * escopo JS nunca constitui autorização real. Também não reproduz mensagens.
 */
export function projectManagerPausePreview(managerId,operatorId,records,evidence=DEMO_PAUSE_EVIDENCE){
  const manager=getActor(managerId),operator=getActor(operatorId);
  if(!manager || manager.role!=='gestor' || manager.teamState!=='active' ||
     !operator || operator.role!=='operador' || operator.managerId!==managerId ||
     operator.teamState!=='active' || !Array.isArray(records) || !Array.isArray(evidence))return DENIED;
  const team=managedOperators(managerId);
  const allowedCases=new Map();
  for(const shop of manager.shops){
    for(const row of visibleConversations(records,managerId,shop)){
      if(row.assignedTo===operatorId && active(row))allowedCases.set(row.id,row);
    }
  }
  const cases=[...allowedCases.values()].sort((a,b)=>a.id.localeCompare(b.id)).map(row=>{
    const matchingProof=evidence.find(proof=>proof?.caseId===row.id);
    const outcome=classifyPauseCase(row,matchingProof,team,operatorId,managerId);
    return Object.freeze({
      caseId:row.id,shopName:getShop(row.shopId)?.name??'Concessionária fictícia',
      outcome,label:PAUSE_OUTCOMES[outcome]
    });
  });
  const summary=Object.freeze({
    total:cases.length,
    started:cases.filter(row=>row.outcome==='retain_started').length,
    noRecipient:cases.filter(row=>row.outcome==='retain_no_recipient').length,
    unverified:cases.filter(row=>row.outcome==='retain_unverified').length,
    protected:cases.filter(row=>row.outcome==='retain_protected').length,
    candidates:cases.filter(row=>row.outcome==='proposed_same_team').length
  });
  return Object.freeze({visibility:'ready',operatorId,managerId,source:PAUSE_PREVIEW_VERSION,
    summary,cases:Object.freeze(cases),applied:false});
}
