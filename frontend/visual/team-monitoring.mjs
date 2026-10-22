/** FV-UI-011 · G3 — Monitoramento por OPERADORES da equipe, exclusivamente sintético.
 * Não há relógio Meta/SLA, agregação de D3/D4, consulta direta de dados, mutação
 * de status, redistribuição ou autorização real. S0 deve entregar projeção minimizada.
 */
import { COMMERCIAL_STATUSES, getActor, hasMockCaseOnlyScope, managedOperators, visibleConversations } from './fixtures.mjs';
import { isInActiveInbox } from './cf-op-02.mjs';

export function projectTeamMonitoring(managerId, records) {
  const manager=getActor(managerId);
  if(!manager || manager.role!=='gestor' || manager.teamState!=='active')
    return Object.freeze({visibility:'forbidden', summary:null, operators:[]});
  const operators=managedOperators(managerId);
  const allowed=manager.shops.flatMap(shop=>visibleConversations(records,managerId,shop));
  // IDs do mesmo caso não podem inflar contagens caso a projeção venha repetida.
  const cases=[...new Map(allowed.map(record=>[record.id,record])).values()];
  const active=cases.filter(isInActiveInbox);
  const historical=cases.filter(record=>record.inboxProjection==='historical');
  const isWindowIssue=record=>isInActiveInbox(record) &&
    record.metaWindowProjection==='expired' &&
    record.humanCompletionProjection==='pending';
  const isProtected=record=>isInActiveInbox(record) &&
    record.reassignmentProjection==='protected_queue';
  const inTeamQueue=record=>isInActiveInbox(record) &&
    record.assignedTo==null && record.teamManagerId===managerId;
  const isBankPending=record=>isInActiveInbox(record) &&
    record.bankProjection?.phase==='reply_pending';
  const perOperator=operators.map(operator=>{
    const own=cases.filter(record=>record.assignedTo===operator.id &&
      (operator.shops.includes(record.shopId) ||
       hasMockCaseOnlyScope(record,operator.id,record.shopId)));
    const open=own.filter(isInActiveInbox);
    return Object.freeze({
      id:operator.id,name:operator.name,
      intake:operator.teamState!=='active'?'unavailable':
        operator.leadIntakeProjection==='paused_confirmed'?'paused_confirmed':
        operator.leadIntakeProjection==='receiving'?'receiving':'unknown',
      activeCount:open.length,
      historicalCount:own.filter(record=>record.inboxProjection==='historical').length,
      unreadCount:open.filter(record=>record.unread>0).length,
      windowAttentionCount:open.filter(isWindowIssue).length,
      shopsCount:operator.shops.length
    });
  });
  const summary=Object.freeze({
    operatorCount:operators.length,
    intakePausedCount:perOperator.filter(row=>row.intake==='paused_confirmed').length,
    intakeUnavailableCount:perOperator.filter(row=>row.intake==='unavailable').length,
    activeCases:active.length,
    historicalCases:historical.length,
    unreadCases:active.filter(record=>record.unread>0).length,
    windowAttentionCases:active.filter(isWindowIssue).length,
    protectedQueueCases:active.filter(isProtected).length,
    unassignedTeamCases:active.filter(inTeamQueue).length,
    bankReplyPendingCases:active.filter(isBankPending).length,
    managerOwnedCases:active.filter(record=>record.assignedTo===managerId).length
  });
  return Object.freeze({
    visibility:'team_summary',summary,
    // Status comerciais canônicos em quadro SEPARADO dos eventos técnicos G3.
    commercialStages:Object.freeze(COMMERCIAL_STATUSES.map(status=>Object.freeze({
      status,count:active.filter(record=>record.status===status).length
    }))),
    operators:Object.freeze(perOperator),
    timing:'unverified', // sem SLA, hora atual ou vencimento estimado pelo browser
    source:'synthetic_fixture'
  });
}

export function describeMonitoring(metric) {
  const labels={
    activeCases:'Atendimentos na lista ativa (projeção)',
    unreadCases:'Conversas com mensagens não lidas',
    windowAttentionCases:'Janela Meta expirada com etapa humana pendente (projeção)',
    protectedQueueCases:'Casos indicados como fila protegida',
    unassignedTeamCases:'Casos sem titular nesta projeção histórica (fila compartilhada ainda não modelada)',
    bankReplyPendingCases:'Retornos bancários pendentes de prova (projeção)'
  };
  return labels[metric]??'Indicador indisponível';
}
