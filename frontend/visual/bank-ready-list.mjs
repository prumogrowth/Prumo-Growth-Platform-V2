/** FV-BANCO-01: lista de entrada para cadastro no banco, exclusivamente sintética.
 * Não é lista geral de clientes, acompanhamento pós-remessa ou autorização bancária.
 * O S0 deve entregar apenas dados e aptidão autorizados; a filtragem JS não é RLS.
 */
import { visibleConversations } from './fixtures.mjs';
import { registrationProjectionFor } from './registration-view.mjs';
import { bankProjectionFor } from './bank-view.mjs';
import { bankReadinessFor } from './relationship-view.mjs';

const TERMINAL_OR_ALREADY_SENT = new Set(['cadastro enviado ao banco','vendido','perdido']);
const NOT_YET_SUBMITTED = new Set(['not_submitted','unavailable']);

export function isBankReadyForRegistration(record, records, actorId, shopId) {
  if (!record || !Array.isArray(records) || record.shopId!==shopId ||
      record.inboxProjection!=='active' || TERMINAL_OR_ALREADY_SENT.has(record.status)) return false;

  // Ficha persistida e autorização para ver os dados são necessárias, mas não
  // bastam: a aptidão é uma prova independente, vinculada à versão da ficha.
  const registration=registrationProjectionFor(record,actorId,shopId);
  if (registration.visibility!=='detail' || registration.confirmedPersisted!==true) return false;
  const bank=bankProjectionFor(record,actorId,shopId);
  if (bank.visibility!=='detail' || bank.submissionConfirmed || bank.replyConfirmed ||
      !NOT_YET_SUBMITTED.has(bank.phase)) return false;

  // Não usar rótulos como "pronto", nome do cliente, campos preenchidos ou
  // ausência aparente de lacunas para inferir elegibilidade bancária.
  return bankReadinessFor(record,records,actorId,shopId);
}

/** O card só expõe o nome. O id é uma chave interna para abrir a ficha autorizada.
 * Os dados cadastrais não fazem parte da projeção da lista.
 */
export function projectBankReadyList(records,actorId,shopId) {
  if (!Array.isArray(records)) return Object.freeze([]);
  const rows=visibleConversations(records,actorId,shopId).filter(row=>
    isBankReadyForRegistration(row,records,actorId,shopId));
  return Object.freeze(rows.map(row=>Object.freeze({id:row.id,name:row.name})));
}

export function bankReadyCaseForSelection(records,actorId,shopId,caseId) {
  if (typeof caseId!=='string' || !caseId) return null;
  const allowed=visibleConversations(records,actorId,shopId).find(row=>row.id===caseId);
  return allowed && isBankReadyForRegistration(allowed,records,actorId,shopId) ? allowed : null;
}
