/** FV-BANCO-01: lista de entrada para cadastro no banco, exclusivamente sintética.
 * Não é lista geral de clientes, acompanhamento pós-remessa ou autorização bancária.
 * O S0 deve entregar apenas dados e aptidão autorizados; a filtragem JS não é RLS.
 */
import { visibleConversations } from './fixtures.mjs';
import { registrationProjectionFor } from './registration-view.mjs';
import { bankProjectionFor } from './bank-view.mjs';
import { bankReadinessFor } from './relationship-view.mjs';

const TERMINAL_OR_ALREADY_SENT = new Set(['cadastro enviado ao banco','vendido','perdido']);
// Desconhecido não é prova de que a remessa ainda não ocorreu.
const EXPLICIT_NOT_SUBMITTED = 'not_submitted';

export function isBankReadyForRegistration(record, records, actorId, shopId) {
  if (!record || !Array.isArray(records) || record.shopId!==shopId ||
      record.inboxProjection!=='active' || TERMINAL_OR_ALREADY_SENT.has(record.status)) return false;

  // Ficha persistida e autorização para ver os dados são necessárias, mas não
  // bastam: a aptidão é uma prova independente, vinculada à versão da ficha.
  const registration=registrationProjectionFor(record,actorId,shopId);
  if (registration.visibility!=='detail' || registration.confirmedPersisted!==true ||
      registration.state!=='persisted' || registration.missing.length!==0 ||
      registration.conflicts.length!==0) return false;
  // Até a S0 tipar operação e autorização de reenvio, o novo ciclo após
  // remessa ou dossiê com snapshot bancário prévio não pode entrar nesta fila.
  if (record.postmarkProjection?.source==='bank_submitted' ||
      (Array.isArray(record.customerDossierProjection?.bankSnapshots) &&
       record.customerDossierProjection.bankSnapshots.length>0)) return false;
  const bank=bankProjectionFor(record,actorId,shopId);
  if (bank.visibility!=='detail' || bank.submissionConfirmed || bank.replyConfirmed ||
      bank.phase!==EXPLICIT_NOT_SUBMITTED) return false;

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
