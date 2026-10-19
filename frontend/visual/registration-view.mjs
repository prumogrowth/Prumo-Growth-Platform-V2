/** FV-UI-007 / O3: apresentação de PROJEÇÕES SINTÉTICAS de ficha.
 * O S0 deverá filtrar e autorizar tudo no servidor; este filtro local NÃO é segurança.
 * Nenhum rótulo de campo de exemplo define o catálogo oficial do cadastro.
 */
import { getActor } from './fixtures.mjs';
import { isInActiveInbox } from './cf-op-02.mjs';

export const REGISTRATION_OUTCOMES = Object.freeze([
  'persisted', 'partial', 'processing', 'failed', 'stale', 'unavailable'
]);
const EMPTY = Object.freeze([]);

export function mayViewMockRegistrationDetail(record, actorId, shopId) {
  const actor = getActor(actorId);
  return Boolean(actor && actor.teamState === 'active' &&
    record && record.shopId === shopId && actor.shops.includes(shopId) &&
    record.assignedTo === actorId && isInActiveInbox(record));
}

export function registrationProjectionFor(record, actorId, shopId) {
  const actor = getActor(actorId);
  if (!record || !actor || actor.teamState !== 'active' ||
      !actor.shops.includes(shopId) || record.shopId !== shopId ||
      (actor.role !== 'gestor' && record.assignedTo !== actorId)) {
    return Object.freeze({ visibility: 'forbidden', state: 'unavailable', confirmedPersisted: false,
      fields: EMPTY, missing: EMPTY, conflicts: EMPTY });
  }

  const projection = record.registrationProjection;
  const state = REGISTRATION_OUTCOMES.includes(projection?.state) ? projection.state : 'unavailable';
  const version = typeof projection?.formVersionRef === 'string' && projection.formVersionRef.trim()
    ? projection.formVersionRef.trim() : null;
  const confirmedPersisted = Boolean(projection?.confirmedPersisted === true &&
    version && (state === 'persisted' || state === 'partial'));

  // Supervisão D2 NÃO confere permissão a conteúdo D3/D4. Nem resumo de campo.
  if (!mayViewMockRegistrationDetail(record, actorId, shopId)) {
    return Object.freeze({
      visibility: 'summary', state, confirmedPersisted, formVersionRef: null,
      fields: EMPTY, missing: EMPTY, conflicts: EMPTY
    });
  }

  // Somente campos projetados como CONFIRMADOS e persistidos pelo servidor
  // poderiam ser exibidos. Proposta OAI não é valor cadastral persistido.
  const rawFields = confirmedPersisted && Array.isArray(projection?.fields)
    ? projection.fields : EMPTY;
  const fields = rawFields.filter(field =>
    field && field.validationState === 'applied' && field.sourceRef &&
    typeof field.label === 'string' && typeof field.safeDisplayValue === 'string')
    .map(field => Object.freeze({
      key: String(field.key ?? ''),
      label: field.label,
      safeDisplayValue: field.safeDisplayValue,
      sourceRef: String(field.sourceRef),
      sourceLabel: String(field.sourceLabel ?? 'Origem não identificada'),
      validationState: 'applied'
    }));

  return Object.freeze({
    visibility: 'detail', state, confirmedPersisted,
    formVersionRef: confirmedPersisted ? version : null,
    fields,
    // Pendências de um processamento falho/obsoleto não são afirmações atuais.
    missing: confirmedPersisted && Array.isArray(projection?.missing)
      ? projection.missing.filter(x => typeof x === 'string' && x.trim()) : EMPTY,
    conflicts: confirmedPersisted && Array.isArray(projection?.conflicts)
      ? projection.conflicts.filter(x => typeof x === 'string' && x.trim()) : EMPTY
  });
}

export function registrationStateCopy(result) {
  // "persisted/partial" isolado não é prova de commit: exige versão + confirmação.
  if ((result?.state === 'persisted' || result?.state === 'partial') &&
      result?.confirmedPersisted !== true) {
    return { title: 'Persistência não confirmada', note: 'Sem confirmação de nova versão válida, nenhum cadastro pode ser considerado gravado.' };
  }
  switch(result?.state) {
    case 'processing': return { title: 'Processamento em andamento', note: 'Nenhum campo novo pode ser considerado salvo.' };
    case 'persisted': return { title: 'Versão persistida (demonstração)', note: 'Somente campos com fonte e confirmação de gravação são mostrados.' };
    case 'partial': return { title: 'Versão parcial persistida (demonstração)', note: 'Dados confirmados, lacunas e conflitos são apresentados separadamente.' };
    case 'failed': return { title: 'Falha de processamento (demonstração)', note: 'Nenhum resultado novo foi considerado persistido.' };
    case 'stale': return { title: 'Resultado desatualizado (demonstração)', note: 'Não aplicar valores de uma versão anterior da conversa.' };
    default: return { title: 'Resultado não confirmado', note: 'Não inferir cadastro preenchido ou etapa de extração concluída.' };
  }
}
