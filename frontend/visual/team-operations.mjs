/** G2 — contratos VISUAIS de equipe e de pausa de entrada, apenas em memória.
 * Não altera Auth, estado global do operador, lojas elegíveis ou atribuições.
 * Projeções reais/identidades autorizadas deverão ser enviadas pelo núcleo S0/S1-002.
 */
import { getActor, managedOperators, visibleConversations } from './fixtures.mjs';

export function projectManagedTeam(managerId, records) {
  const manager=getActor(managerId);
  if(manager?.role!=='gestor' || manager.teamState!=='active')return [];
  return managedOperators(managerId).map(operator=>{
    // O número é somente demonstração e respeita a concessão A/B do próprio operador.
    const cases=manager.shops.flatMap(shop=>visibleConversations(records,managerId,shop)
      .filter(row=>row.assignedTo===operator.id));
    const available=operator.teamState==='active';
    const intake=available && operator.leadIntakeProjection==='paused_confirmed' ? 'paused_confirmed'
      : available && operator.leadIntakeProjection==='receiving' ? 'receiving' : 'unavailable';
    return Object.freeze({
      id:operator.id, name:operator.name,
      shops:Object.freeze([...operator.shops]), // informação somente leitura
      teamState:operator.teamState,
      intake, cases:cases.length
    });
  });
}

export function requestMockIntake(managerId, operatorId, action) {
  const manager=getActor(managerId),operator=getActor(operatorId);
  if(!manager || manager.role!=='gestor' || manager.teamState!=='active' ||
    !operator || operator.role!=='operador' || operator.managerId!==manager.id ||
    operator.teamState!=='active')throw Error('FORBIDDEN_TEAM');
  if(!['pause','resume'].includes(action))throw Error('INVALID_ACTION');
  const state=operator.leadIntakeProjection;
  if(action==='pause' && state!=='receiving')throw Error('INVALID_TRANSITION');
  if(action==='resume' && state!=='paused_confirmed')throw Error('INVALID_TRANSITION');
  // Nunca mutate operator/teamState/shops/assignedTo ou redistribua casos aqui.
  return Object.freeze({
    actorId:manager.id, operatorId:operator.id, action,
    state:'requested_demo', scope:'all_granted_shops',
    message:'Solicitação apenas local. Nenhuma pausa ou redistribuição efetivada.'
  });
}
