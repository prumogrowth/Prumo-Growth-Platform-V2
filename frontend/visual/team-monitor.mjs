/** FV-UI-011 / G3 — projeção visual de monitoramento gerencial.
 * Apenas dados fictícios fornecidos como projeção S0; nunca inferir SLA,
 * relógio Meta/C09, aprovação bancária, elegibilidade ou ação sobre operadores.
 * Filtro JS NÃO substitui autorização/anonimização no servidor.
 */
import { getActor, getShop, visibleConversations } from './fixtures.mjs';
import { isInActiveInbox } from './cf-op-02.mjs';
import { projectManagedTeam } from './team-operations.mjs';

export const G3_SIGNALS=Object.freeze({
  waiting_human:'Aguardando retorno humano',
  bank_pending:'Retorno bancário pendente',
  followup_scheduled:'Plano de recontato projetado',
  protected_queue:'Fila protegida — sem titular',
  delivery_unverified:'Entrega ainda não comprovada'
});

export function projectManagerMonitor(managerId,records,localRequests={}) {
  const manager=getActor(managerId);
  if(!manager || manager.role!=='gestor' || manager.teamState!=='active')
    return Object.freeze({visibility:'forbidden',indicators:null,operators:[],signals:[],asOf:null});
  const team=projectManagedTeam(managerId,records);
  // Somente casos já autorizados pela interseção equipe+concessão em cada loja.
  const authorized=new Map();
  for(const shopId of manager.shops)
    for(const row of visibleConversations(records,managerId,shopId))
      authorized.set(row.id,row);
  const scope=[...authorized.values()];
  const active=scope.filter(isInActiveInbox);
  const historical=scope.filter(row=>row.inboxProjection==='historical');
  const signals=[];
  for(const row of active) {
    const p=row.monitorProjection;
    if(!p || p.origin!=='s0_fixture' || typeof p.observedAt!=='string' ||
       !p.observedAt.trim() || !Object.hasOwn(G3_SIGNALS,p.code))continue;
    // Guarda: o alerta de fila protegida NÃO pode referir outra equipe.
    if(p.code==='protected_queue' && (row.assignedTo!==null ||
      row.reassignmentProjection!=='protected_queue' || row.teamManagerId!==managerId))continue;
    const wait=p.code==='waiting_human' && Number.isFinite(p.observedWaitMinutes) &&
      p.observedWaitMinutes>=0 ? p.observedWaitMinutes : null;
    signals.push(Object.freeze({
      caseId:row.id,shopId:row.shopId,shopName:getShop(row.shopId)?.name??'Loja fictícia',
      code:p.code,label:G3_SIGNALS[p.code],observedWaitMinutes:wait,
      observedAt:p.observedAt,commercialStatus:row.status
    }));
  }
  const pendingRequests=team.filter(member=>localRequests[member.id]?.actorId===managerId &&
    localRequests[member.id]?.operatorId===member.id &&
    localRequests[member.id]?.state==='requested_demo').length;
  const result={
    visibility:'ready',
    asOf:'Corte fictício T0 — sem relógio do navegador',
    indicators:Object.freeze({
      teamMembers:team.length,
      intakePaused:team.filter(member=>member.intake==='paused_confirmed').length,
      operationalActive:active.length,
      historical:historical.length,
      protectedQueue:signals.filter(x=>x.code==='protected_queue').length,
      pendingLocalRequests:pendingRequests,
      observedWaits:signals.filter(x=>x.observedWaitMinutes!==null).length
    }),
    operators:Object.freeze(team.map(x=>Object.freeze({
      id:x.id,name:x.name,intake:x.intake,teamState:x.teamState,cases:x.cases
    }))),
    signals:Object.freeze(signals)
  };
  return Object.freeze(result);
}
