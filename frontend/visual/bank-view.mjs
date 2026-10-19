/** FV-UI-008 · O4 — PROJEÇÕES BANCÁRIAS APENAS FICTÍCIAS.
 * Não há comando de remessa, retorno/recusa/venda ou upload de prova no browser.
 * A S0 deve produzir projeções já minimizadas e autorizadas; filtragem JS não é segurança.
 */
import { getActor, visibleConversations } from './fixtures.mjs';

export const BANK_PHASES = Object.freeze([
  'not_submitted', 'submission_requested', 'submission_verified',
  'reply_pending', 'reply_verified', 'unverified', 'unavailable'
]);

const EMPTY_VIEW = Object.freeze({
  canViewDetails:false, submissionConfirmed:false, replyConfirmed:false,
  submissionSummary:null, replySummary:null
});

export function bankProjectionFor(record, actorId, shopId) {
  const actor = getActor(actorId);
  if (!record || !actor || actor.teamState !== 'active' ||
      !actor.shops.includes(shopId) || record.shopId !== shopId ||
      !visibleConversations([record],actorId,shopId).includes(record)) {
    return Object.freeze({ ...EMPTY_VIEW, visibility:'forbidden', phase:'unavailable' });
  }

  const raw = record.bankProjection;
  const phase = BANK_PHASES.includes(raw?.phase) ? raw.phase : 'unavailable';
  const canViewDetails = record.assignedTo === actorId;
  // Supervisor D2 recebe apenas estado operacional, nunca detalhes de prova bancária D4.
  if (!canViewDetails) return Object.freeze({
    ...EMPTY_VIEW, visibility:'summary', phase
  });

  const submissionConfirmed = Boolean(
    ['submission_verified','reply_pending','reply_verified'].includes(phase) &&
    raw?.submissionProofState === 'verified' &&
    raw?.submittedByAuthorizedHuman === true &&
    typeof raw?.submissionVersionRef === 'string' && raw.submissionVersionRef.trim()
  );
  const replyConfirmed = Boolean(
    submissionConfirmed && phase === 'reply_verified' &&
    raw?.replyProofState === 'verified' && raw?.replyRecordedByHuman === true &&
    typeof raw?.replyVersionRef === 'string' && raw.replyVersionRef.trim()
  );
  const submissionSummary = submissionConfirmed ? Object.freeze({
    label:'Remessa confirmada apenas na fixture',
    versionRef:raw.submissionVersionRef.trim(),
    proofLabel:'Verificação S0 sintética',
    operatorLabel:'Ação humana simulada'
  }) : null;
  const replySummary = replyConfirmed ? Object.freeze({
    label:'Retorno do banco confirmado apenas na fixture',
    versionRef:raw.replyVersionRef.trim(),
    proofLabel:'Verificação S0 sintética',
    operatorLabel:'Registro humano simulado'
  }) : null;
  return Object.freeze({
    visibility:'detail', phase, canViewDetails,
    submissionConfirmed, replyConfirmed, submissionSummary, replySummary
  });
}

export function bankPhaseCopy(projection) {
  if (!projection || projection.visibility === 'forbidden')
    return { title:'Acesso indisponível', description:'Nenhuma informação deste caso pode ser apresentada.' };
  if (projection.visibility === 'summary')
    return { title:'Acompanhamento bancário · resumo', description:'O gestor visualiza o marco operacional, sem documento, dados bancários nem conteúdo D4.' };
  if (projection.replyConfirmed)
    return { title:'Retorno comprovado · demonstração', description:'Evidência e ação humana verificadas na fixture. Não alterar status comercial na interface.' };
  if (projection.submissionConfirmed)
    return { title:'Remessa comprovada · demonstração', description:'Somente a remessa está ilustrada como comprovada; não há decisão bancária inferida.' };
  if (projection.phase === 'submission_requested')
    return { title:'Solicitação de remessa · não confirmada', description:'Pedido, transporte e remessa efetiva não são a mesma coisa.' };
  if (projection.phase === 'reply_pending')
    return { title:'Retorno ainda não comprovado', description:'Não confundir espera do banco com aprovação, recusa ou perda.' };
  return { title:'Evidência bancária não confirmada', description:'Não afirmar remessa, aprovação, recusa, venda ou prova sem retorno confiável da S0.' };
}

export function bankCanMockWrite() {
  // Sem catálogo de provas, C15-C18 físico, validação e autenticação reais.
  return false;
}
