/** CF-OP-02 / FV-03: somente projeções sintéticas recebidas como dados.
 * A janela Meta e os prazos C09 são autoritativos do S0, JAMAIS Date.now() no browser.
 */
import { getActor, visibleConversations, hasMockCaseScope, copyFixtures } from './fixtures.mjs';

export const DEMO_TEMPLATES = Object.freeze([
  { id: 'modelo_continuidade_demo', version: 'v1-demo', title: 'Retomar conversa', eligibility: 'Exemplo fictício' },
  { id: 'modelo_confirmacao_demo', version: 'v1-demo', title: 'Solicitar resposta', eligibility: 'Exemplo fictício' }
]);
export const FOLLOWUP_ACTIONS = Object.freeze(['single_template', 'request_chain']);

// Dados de S0 precisam ter o formato esperado: string com substring não é permissão.
export function hasProjectedAction(record, action) {
  return Array.isArray(record?.allowedActionsProjection) &&
    record.allowedActionsProjection.includes(action);
}

export function hasEligibleTemplateVersion(record, template) {
  return Array.isArray(record?.eligibleTemplatesProjection) &&
    typeof template?.id === 'string' && typeof template?.version === 'string' &&
    record.eligibleTemplatesProjection.includes(template.id + '@' + template.version);
}

export function isInActiveInbox(record) {
  // Fonte: projeção do servidor. Não usar expiração calculada no navegador.
  return record?.inboxProjection === 'active';
}

export function projectedMetaWindow(record) {
  return record?.metaWindowProjection ?? 'unknown';
}

export function humanCompletion(record, simulatedCompletion = false) {
  return simulatedCompletion ? 'requested_demo' : (record?.humanCompletionProjection ?? 'unknown');
}

function currentlyAssigned(record, actorId, shopId) {
  const actor = getActor(actorId);
  return Boolean(record && actor && hasMockCaseScope(record,actorId,shopId) &&
    record.assignedTo === actorId);
}

export function isPriorCycleLocked(record) {
  // Em retorno pós-banco, pós-venda ou pós-perda, o S0 deve projetar NOVO ciclo humano.
  // Não ativar a conversa comercial histórica por uma permissão de canal desatualizada.
  return ['cadastro enviado ao banco', 'vendido', 'perdido'].includes(record?.status);
}

export function mayMockFreeText(record, actorId, shopId, simulatedCompletion = false) {
  // Caso histórico, marco bancário/terminal, janela inválida e conclusão bloqueiam livre.
  return !isPriorCycleLocked(record) && currentlyAssigned(record, actorId, shopId) &&
    isInActiveInbox(record) && projectedMetaWindow(record) === 'open' &&
    humanCompletion(record, simulatedCompletion) === 'pending' &&
    hasProjectedAction(record,'free_text');
}

export function projectedFollowupActions(record, actorId, shopId, simulatedCompletion = false) {
  if (isPriorCycleLocked(record) || !currentlyAssigned(record, actorId, shopId) || !isInActiveInbox(record) ||
      humanCompletion(record, simulatedCompletion) !== 'pending' || projectedMetaWindow(record) !== 'expired') return [];
  return FOLLOWUP_ACTIONS.filter(action => hasProjectedAction(record,action) &&
    (action !== 'single_template' || DEMO_TEMPLATES.some(t => hasEligibleTemplateVersion(record,t))));
}

export function projectInbox(records, actorId, shopId, placement = 'active') {
  const allowed = visibleConversations(records, actorId, shopId);
  return allowed.filter(record => placement === 'history' ? record.inboxProjection === 'historical' : record.inboxProjection === 'active');
}

export function projectedFollowupState(record, localRequest = null) {
  const plan = record?.followupProjection ?? null;
  if (localRequest) return { ...localRequest, source: 'local_demo', confirmedSent: false };
  return plan ? { ...plan, source: 'fixture_projection' } : null;
}

export function applyLocalFollowupRequest(record, actorId, shopId, kind, template) {
  const actions = projectedFollowupActions(record, actorId, shopId);
  if (!actions.includes(kind)) throw new Error('ACAO_INELEGIVEL_NA_DEMONSTRACAO');
  if (kind === 'single_template') {
    if (!DEMO_TEMPLATES.some(t => t.id === template?.id && t.version === template.version &&
      hasEligibleTemplateVersion(record,t)))
      throw new Error('TEMPLATE_NAO_ELEGIVEL_NA_DEMONSTRACAO');
    return { kind, state: 'requested', template: { id: template.id, version: template.version }, confirmedSent: false };
  }
  return { kind, state: 'requested', confirmedSent: false };
}

export function isSyntheticBankProtected(record) {
  return ['cadastro enviado ao banco', 'vendido'].includes(record?.status);
}

/** Cenários visuais pré-projetados como se fossem vindos de S0; não são regras de S0. */
const SCENARIOS = Object.freeze([
  { id:'A-117',shopId:'aurora',name:'Cliente Exemplo 19',initials:'CE',
    assignedTo:'lia',status:'em atendimento pelo operador',unread:0,
    updatedAt:'Hoje · fictício',tag:'Transferência excepcional somente por caso',
    inboxProjection:'active',metaWindowProjection:'open',humanCompletionProjection:'pending',
    allowedActionsProjection:['free_text','complete'],
    caseOnlyAccessProjection:{origin:'s0_fixture',confirmed:true,scope:'case_only',
      reason:'manual_team_transfer',actorId:'lia',caseId:'A-117',shopId:'aurora',versionRef:'transfer-a117-v1'},
    messages:[{id:'a117-1',side:'system',body:'Transferência fictícia autorizada somente para este caso; nenhuma concessão geral de Aurora.',time:'Hoje'}]},
  { id:'A-114', shopId:'aurora', name:'Cliente Exemplo 15', initials:'CE', assignedTo:'rafael',
    status:'em atendimento pelo operador', unread:0, updatedAt:'Hoje · fictício',
    tag:'Novo ciclo pós-remessa',inboxProjection:'active',metaWindowProjection:'open',
    humanCompletionProjection:'pending',allowedActionsProjection:['free_text','complete'],
    postmarkProjection:{direction:'continuation',source:'bank_submitted',originCaseRef:'A-105',
      confirmedCreated:true,linkedByS0:true,linkVersionRef:'cycle-bank-demo-v1',
      sellerAiSilenced:true},
    customerDossierProjection:{
      origin:'s0_fixture',caseId:'A-114',shopId:'aurora',identityConfirmed:true,
      customerRef:'client15-aurora-only',liveFormVersionRef:'live-form-v2-demo',
      authorizedCaseRefs:['A-105','A-114'],
      formHistory:[
        {versionRef:'live-form-v1-demo',cutoffRef:'historical-cutoff-a105',confirmedPersisted:true},
        {versionRef:'live-form-v2-demo',cutoffRef:'historical-cutoff-a114',confirmedPersisted:true}
      ],
      bankSnapshots:[{origin:'s0_fixture',shopId:'aurora',
        submissionCaseRef:'A-105',bankSubmissionVersionRef:'bank-demo-v1',frozenSnapshot:true}]
    },
    messages:[{id:'a114-1',side:'system',body:'Novo ciclo humano fictício aberto pelo S0 após marco bancário, sem alterar o caso anterior.',time:'Hoje'},
      {id:'a114-2',side:'in',body:'Quero falar com a equipe sobre o andamento depois do envio ao banco.',time:'Hoje'}] },
  { id:'A-115', shopId:'aurora', name:'Cliente Exemplo 16', initials:'CE', assignedTo:'rafael',
    status:'vendido',unread:0,updatedAt:'Arquivo',
    tag:'Venda registrada · histórico',inboxProjection:'historical',metaWindowProjection:'expired',
    humanCompletionProjection:'completed',allowedActionsProjection:[],
    postmarkProjection:{direction:'origin',source:'sold',continuationCaseRef:'A-116',
      confirmedCreated:true,linkedByS0:true,linkVersionRef:'cycle-sold-demo-v1',
      sellerAiSilenced:true},
    messages:[{id:'a115-1',side:'system',body:'Venda humana confirmada somente neste cenário histórico fictício.',time:'Arquivo'}] },
  { id:'A-116', shopId:'aurora', name:'Cliente Exemplo 17',initials:'CE',assignedTo:'rafael',
    status:'em atendimento pelo operador',unread:0,updatedAt:'Hoje · fictício',
    tag:'Novo ciclo pós-venda',inboxProjection:'active',metaWindowProjection:'open',
    humanCompletionProjection:'pending',allowedActionsProjection:['free_text','complete'],
    postmarkProjection:{direction:'continuation',source:'sold',originCaseRef:'A-115',
      confirmedCreated:true,linkedByS0:true,linkVersionRef:'cycle-sold-demo-v1',
      sellerAiSilenced:true},
    messages:[{id:'a116-1',side:'system',body:'Atendimento humano fictício pós-venda em OUTRO ciclo. Não há nova IA Vendedora.',time:'Hoje'},
      {id:'a116-2',side:'in',body:'Gostaria de conversar com um profissional depois da compra.',time:'Hoje'}] },
  { id:'A-107', shopId:'aurora', name:'Cliente Exemplo 08', initials:'CE', assignedTo:'rafael',
    status:'em atendimento pelo operador', unread:1, updatedAt:'Ontem', tag:'Janela expirada · pendente',
    inboxProjection:'active', metaWindowProjection:'expired', humanCompletionProjection:'pending',
    allowedActionsProjection:['single_template','request_chain','complete'],
    eligibleTemplatesProjection:['modelo_continuidade_demo@v1-demo'],
    messages:[{id:'a107-1',side:'in',body:'Preciso pensar e retorno depois.',time:'Ontem'}] },
  { id:'A-108', shopId:'aurora', name:'Cliente Exemplo 09', initials:'CE', assignedTo:'rafael',
    status:'em atendimento pelo operador', unread:0, updatedAt:'10:50', tag:'Etapa humana concluída',
    inboxProjection:'active', metaWindowProjection:'open', humanCompletionProjection:'completed',
    allowedActionsProjection:[],
    humanCycleProjection:{origin:'s0_fixture',caseId:'A-108',shopId:'aurora',
      customerRef:'client09-aurora-only',events:[
        {origin:'s0_fixture',completionId:'concl-a108-1',requestId:'f03-a108-1',
         cutoffMessageRef:'a108-1',cutoffVersionRef:'case-v1-demo',
         resultVersionRef:'v0-ficticia',extractionState:'partial_confirmed',humanCompletionConfirmed:true},
        {origin:'s0_fixture',completionId:'concl-a108-2',requestId:'f03-a108-2',
         cutoffMessageRef:'a108-2',cutoffVersionRef:'case-v2-demo',
         resultVersionRef:'v1-ficticia',extractionState:'partial_confirmed',humanCompletionConfirmed:true}
      ]},
    clarificationProjection:{origin:'s0_fixture',confirmed:true,
      caseId:'A-108',shopId:'aurora',assignedTo:'rafael',
      state:'human_followup_authorized',versionRef:'review-a108-v3-demo',
      metaWindowProjection:'open',cutoffCandidateRef:'a108-3',
      inbound:{id:'a108-3',side:'in',
        body:'Posso esclarecer o dado que ainda está faltando?',time:'Cenário alternativo · fictício'}},
    customerDossierProjection:{origin:'s0_fixture',caseId:'A-108',
      shopId:'aurora',identityConfirmed:true,customerRef:'client09-aurora-only',
      liveFormVersionRef:'v1-ficticia',authorizedCaseRefs:['A-108'],
      formHistory:[{versionRef:'v0-ficticia',cutoffRef:'a108-1',confirmedPersisted:true},
        {versionRef:'v1-ficticia',cutoffRef:'a108-2',confirmedPersisted:true}],
      bankSnapshots:[]},
    registrationProjection:{
      state:'partial',confirmedPersisted:true,formVersionRef:'v1-ficticia',
      fields:[
        {key:'demonst_a',label:'Informação demonstrativa A',safeDisplayValue:'Valor fictício confirmado',
         sourceRef:'a108-1',sourceLabel:'Mensagem ilustrativa do cliente',validationState:'applied'},
        {key:'demonst_c',label:'Informação demonstrativa C',safeDisplayValue:'Somente proposta',
         sourceRef:'a108-1',sourceLabel:'Trecho ilustrativo',validationState:'proposed'}
      ],
      missing:['Informação demonstrativa B — ausente na conversa'],
      conflicts:['Informação demonstrativa D — fontes fictícias conflitantes']
    },
    messages:[{id:'a108-1',side:'in',body:'Obrigado pelo atendimento. Vou analisar.',time:'10:50'},
      {id:'a108-2',side:'in',body:'Retornei para esclarecer um ponto anterior.',time:'Outro momento · fictício'}] },
  { id:'A-109', shopId:'aurora', name:'Cliente Exemplo 10', initials:'CE', assignedTo:'rafael',
    status:'em atendimento pelo operador', unread:0, updatedAt:'Ontem', tag:'Histórico preservado',
    inboxProjection:'historical', metaWindowProjection:'expired', humanCompletionProjection:'completed',
    allowedActionsProjection:[],
    messages:[{id:'a109-1',side:'in',body:'Encerramos nossa conversa por hoje.',time:'Ontem'}] },
  { id:'A-110', shopId:'aurora', name:'Cliente Exemplo 11', initials:'CE', assignedTo:'rafael',
    status:'em atendimento pelo operador', unread:0, updatedAt:'Ontem', tag:'Cadeia em andamento',
    inboxProjection:'active', metaWindowProjection:'expired', humanCompletionProjection:'pending',
    allowedActionsProjection:[],
    followupProjection:{state:'scheduled',attempts:[
      {label:'Tentativa 1',state:'scheduled',template:'Modelo autorizado ilustrativo',time:'Horário fictício'},
      {label:'Tentativa 2',state:'pending',template:'Modelo autorizado ilustrativo',time:'A definir no S0'},
      {label:'Template final',state:'pending',template:'Encerramento fictício separado',time:'A definir no S0'}
    ],finalSentConfirmed:false,silenceResolution:'not_started'},
    messages:[{id:'a110-1',side:'in',body:'Estou avaliando as opções e retorno quando puder.',time:'Ontem'}] },
  { id:'A-111', shopId:'aurora', name:'Cliente Exemplo 12', initials:'CE', assignedTo:'rafael',
    status:'perdido', unread:0, updatedAt:'Arquivo', tag:'Perda confirmada em cenário',
    inboxProjection:'historical', metaWindowProjection:'expired', humanCompletionProjection:'completed',
    allowedActionsProjection:[],
    followupProjection:{state:'finished',attempts:[
      {label:'Template final',state:'sent_confirmed',template:'Encerramento ilustrativo',time:'Prova S0 fictícia'}
    ],finalSentConfirmed:true,silenceResolution:'confirmed_eligible'},
    messages:[{id:'a111-1',side:'system',body:'Estado perdido representado como projeção histórica fictícia do S0; não foi calculado aqui.',time:'Arquivo'}] },
  { id:'A-112', shopId:'aurora', name:'Cliente Exemplo 13', initials:'CE', assignedTo:null,
    status:'em atendimento pelo operador', unread:0, updatedAt:'Ontem', tag:'Fila protegida',
    inboxProjection:'active', metaWindowProjection:'unknown', humanCompletionProjection:'pending',
    reassignmentProjection:'protected_queue',teamManagerId:'marina',allowedActionsProjection:[],
    messages:[{id:'a112-1',side:'system',body:'Responsável fictício perdeu acesso; remanejamento cabe ao S1-002.',time:'Ontem'}] },
  { id:'A-113', shopId:'aurora', name:'Cliente Exemplo 14', initials:'CE', assignedTo:'rafael',
    status:'em atendimento pelo operador', unread:0, updatedAt:'Ontem', tag:'Envio final não confirmado',
    inboxProjection:'active', metaWindowProjection:'expired', humanCompletionProjection:'pending',
    allowedActionsProjection:[],
    followupProjection:{state:'awaiting_evidence',attempts:[
      {label:'Template final',state:'queued',template:'Encerramento ilustrativo',time:'Pendente de prova'}
    ],finalSentConfirmed:false,silenceResolution:'not_started'},
    messages:[{id:'a113-1',side:'in',body:'Vou verificar e responder.',time:'Ontem'}] },
]);

// G3: sinais operacionais explicitamente fornecidos pela fixture, sem Date.now,
 // sem extrapolar janelas Meta/C09 e sem criar status comerciais.
const G3_MONITOR_SCENARIOS = Object.freeze({
  'A-102':{code:'waiting_human',observedWaitMinutes:18},
  'A-103':{code:'waiting_human',observedWaitMinutes:27},
  'B-201':{code:'waiting_human',observedWaitMinutes:9},
  'B-203':{code:'waiting_human',observedWaitMinutes:12},
  'A-105':{code:'bank_pending'},
  'A-110':{code:'followup_scheduled'},
  'A-112':{code:'protected_queue'},
  'A-113':{code:'delivery_unverified'}
});
function demoMonitorProjection(id) {
  const signal=G3_MONITOR_SCENARIOS[id];
  return signal ? {...signal,origin:'s0_fixture',observedAt:'Corte fictício T0'} : undefined;
}

export function copyCFDemoFixtures() {
  const base = copyFixtures().map(record => {
    const windowState = { 'A-102':'open','A-105':'unknown','A-106':'open','B-201':'open' }[record.id] ?? 'unknown';
    return {
      ...record, inboxProjection:'active', metaWindowProjection:windowState,
      monitorProjection:demoMonitorProjection(record.id),
      humanCompletionProjection: ['A-102','A-106','B-201'].includes(record.id) ? 'pending' : 'unknown',
      postmarkProjection: record.id === 'A-105' ? {
        direction:'origin',source:'bank_submitted',continuationCaseRef:'A-114',
        confirmedCreated:true,linkedByS0:true,linkVersionRef:'cycle-bank-demo-v1',
        sellerAiSilenced:true
      } : undefined,
      bankProjection: record.id === 'A-105' ? {
        phase:'reply_pending', submissionProofState:'verified',
        submittedByAuthorizedHuman:true, submissionVersionRef:'bank-demo-v1',
        replyProofState:'not_received', replyRecordedByHuman:false
      } : undefined,
      allowedActionsProjection: ['A-102','A-106','B-201'].includes(record.id) ? ['free_text','complete'] : []
    };
  });
  return [...base,...SCENARIOS.map(record => ({
    ...record, notes:[], messages:record.messages.map(m=>({...m,
      transportProjection:m.transportProjection?{...m.transportProjection}:undefined})),
    monitorProjection:demoMonitorProjection(record.id),
    allowedActionsProjection:[...(record.allowedActionsProjection??[])],
    eligibleTemplatesProjection:[...(record.eligibleTemplatesProjection??[])],
    postmarkProjection:record.postmarkProjection ? {...record.postmarkProjection} : undefined,
    bankProjection:record.bankProjection ? {...record.bankProjection} : undefined,
    caseOnlyAccessProjection:record.caseOnlyAccessProjection ? {...record.caseOnlyAccessProjection} : undefined,
    humanCycleProjection:record.humanCycleProjection ? structuredClone(record.humanCycleProjection) : undefined,
    clarificationProjection:record.clarificationProjection ? structuredClone(record.clarificationProjection) : undefined,
    customerDossierProjection:record.customerDossierProjection ? structuredClone(record.customerDossierProjection) : undefined,
    registrationProjection:record.registrationProjection ? {
      ...record.registrationProjection,
      fields:(record.registrationProjection.fields??[]).map(field=>({...field})),
      missing:[...(record.registrationProjection.missing??[])],
      conflicts:[...(record.registrationProjection.conflicts??[])]
    } : undefined,
    followupProjection:record.followupProjection ? {
      ...record.followupProjection,attempts:record.followupProjection.attempts.map(a=>({...a}))
    } : undefined
  }))];
}
