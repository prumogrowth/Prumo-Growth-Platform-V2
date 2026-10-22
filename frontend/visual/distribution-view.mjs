/** FV-UI-018 — projeções de DISTRIBUIÇÃO E FILA SINTÉTICAS (D-AL-02,05,06,07).
 * Não consome S0, não concede acesso, não faz claim/atribuição, não muta filas.
 * Cenários de fila são fotografia ALTERNATIVA T0, não se inferem do quadro
 * de disponibilidade atual em outras fixtures de atendimento.
 */
import { getActor, getShop, managedOperators } from './fixtures.mjs';

export const DEMO_SHARED_LEADS=Object.freeze([
  Object.freeze({id:'FILA-A-01',shopId:'aurora',name:'Lead fictício Aurora 01',
    origin:'s0_fixture',kind:'new_human_lead',queueState:'unassigned',
    versionRef:'queue-a01-v1',assignedTo:null,allowedActionsProjection:['claim','assign_team']}),
  Object.freeze({id:'FILA-H-01',shopId:'horizonte',name:'Lead fictício Horizonte 01',
    origin:'s0_fixture',kind:'new_human_lead',queueState:'unassigned',
    versionRef:'queue-h01-v1',assignedTo:null,allowedActionsProjection:['claim','assign_team']}),
  Object.freeze({id:'FILA-A-02',shopId:'aurora',name:'Lead assumido (prova fictícia)',
    origin:'s0_fixture',kind:'new_human_lead',queueState:'claimed',
    versionRef:'queue-a02-v2',assignedTo:'marina',allowedActionsProjection:[]}),
  Object.freeze({id:'FILA-A-03',shopId:'aurora',name:'Lead redistribuído (prova fictícia)',
    origin:'s0_fixture',kind:'new_human_lead',queueState:'redistributed',
    versionRef:'queue-a03-v3',assignedTo:'rafael',allowedActionsProjection:[]})
]);
const FORBIDDEN=Object.freeze({visibility:'forbidden',asOf:null,shopId:null,
  available:Object.freeze([]),summary:null});
function permittedManager(managerId,shopId){
  const a=getActor(managerId);
  return a?.role==='gestor' && a.teamState==='active' &&
    Array.isArray(a.shops) && a.shops.includes(shopId) && Boolean(getShop(shopId));
}
function trustedQueueRow(row,shopId){
  return row && row.shopId===shopId && row.origin==='s0_fixture' &&
    row.kind==='new_human_lead' && typeof row.id==='string' && row.id.trim() &&
    typeof row.versionRef==='string' && row.versionRef.trim() &&
    ['unassigned','claimed','redistributed'].includes(row.queueState) &&
    typeof row.name==='string' && row.name.trim() &&
    (row.queueState==='unassigned' ? row.assignedTo===null :
      typeof row.assignedTo==='string' && row.assignedTo.trim());
}
/** Só a fila SEM titular; estados já assumidos/redistribuídos são contagens,
 * nunca itens elegíveis para novo clique. Equipes distintas não filtram esta fila.
 */
export function projectSharedNewLeadQueue(managerId,shopId,rows=DEMO_SHARED_LEADS){
  if(!permittedManager(managerId,shopId) || !Array.isArray(rows))return FORBIDDEN;
  const relevant=rows.filter(row=>trustedQueueRow(row,shopId));
  const available=relevant.filter(row=>row.queueState==='unassigned').map(row=>
    Object.freeze({id:row.id,shopId:row.shopId,name:row.name,versionRef:row.versionRef,
      actions:Object.freeze(['claim','assign_team'].filter(action=>
        Array.isArray(row.allowedActionsProjection) && row.allowedActionsProjection.includes(action)))}));
  return Object.freeze({
    visibility:'shared_queue_demo',asOf:'Fotografia sintética alternativa T0',
    shopId,available:Object.freeze(available),
    summary:Object.freeze({
      unassigned:available.length,claimed:relevant.filter(x=>x.queueState==='claimed').length,
      redistributed:relevant.filter(x=>x.queueState==='redistributed').length
    })
  });
}
/** Monta SOMENTE uma intenção local. Claim e atribuição são transações S0/S1.
 * Duas intenções concorrentes NÃO geram dois titulares; não aplicamos nenhuma.
 */
export function requestMockQueueAction(managerId,shopId,caseId,versionRef,action,assigneeId=null,rows=DEMO_SHARED_LEADS){
  const view=projectSharedNewLeadQueue(managerId,shopId,rows);
  const target=view.available.find(row=>row.id===caseId && row.versionRef===versionRef);
  if(!target || !target.actions.includes(action))throw Error('QUEUE_NOT_ELIGIBLE');
  if(action==='claim'){
    if(assigneeId!==null)throw Error('QUEUE_CLAIM_TARGET_INVALID');
  }else if(action==='assign_team'){
    const operator=getActor(assigneeId);
    // Exceção de acesso por caso depende de S0/S1; seleção não altera grant.
    if(operator?.role!=='operador' || operator.teamState!=='active' ||
       operator.managerId!==managerId ||
       !managedOperators(managerId).some(row=>row.id===assigneeId))
      throw Error('QUEUE_ASSIGNEE_OUT_OF_TEAM');
  }else throw Error('QUEUE_ACTION_INVALID');
  return Object.freeze({
    state:'requested_demo',managerId,shopId,caseId,versionRef,action,
    assigneeId:action==='claim'?managerId:assigneeId,applied:false
  });
}
