// FV-UI-004 — verificações estáticas executáveis sobre as fontes reais.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const root = new URL('../', import.meta.url);
const get = path => readFileSync(new URL(path, root), 'utf8');
const app = get('app.mjs');
const markup = get('index.html');
const styles = get('styles.css');
const contract = get('cf-op-02.mjs');
const registration = get('registration-view.mjs');
const humanCycles = get('human-cycle-view.mjs');
const integrationGate = get('integration-gate-view.mjs');
const transport = get('transport-state-view.mjs');
const feedback = get('operation-feedback.mjs');
const command = get('s0-command-result.mjs');

const bank = get('bank-view.mjs');
const postmark = get('postmark-view.mjs');
const teamOps = get('team-operations.mjs');
const teamMonitoring = get('team-monitoring.mjs');
const teamMonitor = get('team-monitor.mjs');
const batchMonitor = get('batch-monitor.mjs');
const fixtureTeam = get('fixtures.mjs');
const browserSmoke = get('tests/browser.smoke.py');
const domMock = get('tests/dom-fixture.mjs');
const offlineExport = get('tests/verify_offline_export.py');
const offlineRunner = get('tests/run_acceptance.py');
const offlineAdversarial = get('tests/test_offline_export.py');

test('três áreas adaptativas e controle de histórico existem', () => {
  for (const fragment of ['id="conversation-items"', 'id="thread-pane"', 'id="detail-pane"',
    'data-inbox="active"', 'data-inbox="history"']) assert.ok(markup.includes(fragment), fragment);
  assert.match(styles, /max-width:760px/);
  assert.match(styles, /max-width:400px/);
  assert.match(styles, /prefers-reduced-motion:reduce/);
});

test('ações de templates e de cadeia permanecem distintas', () => {
  assert.match(markup, /id="template-dialog"/);
  assert.match(app, /Solicitar cadeia de tentativas à IA/);
  assert.match(app, /Selecionar e solicitar template aprovado/);
  assert.match(contract, /eligibleTemplatesProjection/);
  assert.match(contract, /record\.allowedActionsProjection/);
});

test('diálogos limpam confirmação antiga, evitando execução ao fechar com Escape', () => {
  assert.match(app, /dialog\.returnValue='';dialog\.showModal\(\)/);
  assert.match(app, /completion-dialog'\)\.returnValue='';/);
  assert.match(app, /template-dialog'\)\.returnValue='';/);
});

test('controles de gestão exigem perfil gestorial ativo, inclusive no celular', () => {
  assert.match(app, /const showTeam=actor\.role==='gestor' && actor\.teamState==='active'/);
  assert.match(app, /team-nav-mobile'\)\.hidden=!showTeam/);
  assert.match(styles, /\.rail-icon\[hidden\]/);
});

test('abas de detalhe têm foco e relacionamento acessível com o painel', () => {
  assert.match(app, /button\.setAttribute\('aria-controls','case-tab-panel'\)/);
  assert.match(app, /content\.setAttribute\('aria-labelledby','case-tab-'\+state\.detailTab\)/);
  assert.match(app, /target\.querySelector\('\.detail-tab\.active'\)\?\.focus\(\)/);
});

test('frontend não executa redes, persiste segredo ou mede prazos de domínio', () => {
  const code = [app, contract].join('\n').replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/^\s*\/\/.*$/gm, '');
  assert.doesNotMatch(code, /\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\b/);
  assert.doesNotMatch(code, /\blocalStorage\b|\bsessionStorage\b/);
  assert.doesNotMatch(code, /\bDate\.now\s*\(|\bnew\s+Date\s*\(/);
  assert.doesNotMatch(code, /\.innerHTML\s*=/);
});

test('O3 depende de confirmação S0 e não oferece formulário cadastral habitual', () => {
  assert.match(app, /registrationProjectionFor\(item,state\.actorId,state\.shopId\)/);
  assert.match(app, /Detalhes restritos ao responsável do caso/);
  assert.match(registration, /mayViewMockRegistrationDetail/);
  assert.match(registration, /confirmedPersisted/);
  assert.match(registration, /field\.validationState === 'applied'/);
  assert.doesNotMatch(registration, /\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\b/);
});

test('roteiro de Chromium carrega visualizador O3 para ensaios futuros', () => {
  assert.match(browserSmoke, /registration-view\.mjs/);
  assert.match(browserSmoke, /Valor fictício confirmado/);
  assert.match(browserSmoke, /Detalhes restritos ao responsável/);
});

test('O4 não contém edição, chamada bancária nem mutação de estado comercial', () => {
  assert.match(app, /bankProjectionFor\(item,state\.actorId,state\.shopId\)/);
  assert.match(app, /Registros C15–C18 exigem profissional autorizado/);
  assert.match(bank, /bankCanMockWrite/);
  assert.match(bank, /submittedByAuthorizedHuman === true/);
  assert.match(bank, /replyRecordedByHuman === true/);
  assert.doesNotMatch(bank, /\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\b/);
  assert.doesNotMatch(bank, /record\.status\s*=/);
});

test('roteiro Chromium inclui O4 e separação de prova bancária D4', () => {
  assert.match(browserSmoke, /bank-view\.mjs/);
  assert.match(browserSmoke, /bank-demo-v1/);
  assert.match(browserSmoke, /Acompanhamento bancário · resumo/);
  assert.match(browserSmoke, /Decisão bancária não confirmada/);
});

test('O5 abre ciclo projetado separado; não cria caso, muda estado ou reativa IA', () => {
  assert.match(app, /postmarkViewFor\(item,state\.cases,state\.actorId,state\.shopId\)/);
  assert.match(app, /Novo atendimento humano independente/);
  assert.match(app, /closeTransientDialogs\(\)/);
  assert.match(postmark, /sellerAiSilenced===true/);
  assert.match(postmark, /a\.linkedByS0===true && b\.linkedByS0===true/);
  assert.doesNotMatch(postmark, /\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\b/);
  assert.doesNotMatch(postmark, /\.status\s*=(?!=)/);
});

test('roteiro de Chromium contém navegação entre casos O5 no mesmo escopo', () => {
  assert.match(browserSmoke, /postmark-view\.mjs/);
  assert.match(browserSmoke, /Caso A-114/);
  assert.match(browserSmoke, /Caso A-105/);
  assert.match(browserSmoke, /Caso A-116/);
});

test('auditoria: recontatos negados se a continuidade pós-marco não tiver vínculo válido', () => {
  assert.match(app, /const fActions=postmarkContextValid\(item\) \? projectedFollowupActions/);
  assert.match(app, /current\.id!==item\.id \|\| !postmarkContextValid\(current\)/);
  assert.match(app, /selectedCase\(\)\?\.id!==item\.id \|\| !postmarkContextValid\(item\)/);
  assert.match(app, /if\(!item \|\| !postmarkContextValid\(item\)\)return;/);
  assert.match(app, /mayMockOperateContinuation\(record,state\.cases,state\.actorId,state\.shopId\)/);
});

test('auditoria: leituras D3/D4 negadas a operador não atribuído', () => {
  assert.match(registration, /visibleConversations\(\[record\],actorId,shopId\)\.includes\(record\)/);
  assert.match(bank, /visibleConversations\(\[record\],actorId,shopId\)\.includes\(record\)/);
});

test('auditoria: operação independente da autorização de leitura do caso anterior',()=>{
  assert.match(postmark, /export function mayMockOperateContinuation/);
  assert.match(postmark, /record\.assignedTo!==actorId/);
  assert.match(postmark, /relation\.kind!=='restricted'/);
  assert.match(postmark, /origin\.shopId!==record\.shopId/);
});

test('G2 tem equipes de operadores e a loja do gestor é somente filtro', () => {
  assert.match(fixtureTeam, /export function managedOperators/);
  assert.match(fixtureTeam, /operator\.managerId===managerId/);
  assert.match(fixtureTeam, /record\.teamManagerId===actorId/);
  assert.match(app, /projectManagedTeam\(state\.actorId,state\.cases\)/);
  assert.match(markup, /Concessionária \(filtro de conversas, não altera concessões\)/);
  assert.match(markup, /Solicitar pausa ou retomada de novos leads alcança TODAS as lojas/);
});

test('G2 exige pertencimento à equipe e pausa global só é solicitada, nunca aplicada no navegador', () => {
  assert.match(teamOps, /operator\.managerId!==manager\.id/);
  assert.match(teamOps, /scope:'all_granted_shops'/);
  assert.match(teamOps, /state:'requested_demo'/);
  assert.match(teamOps, /Nenhuma pausa ou redistribuição efetivada/);
  assert.match(app, /SOLICITADO LOCALMENTE/);
  assert.doesNotMatch(teamOps, /\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\b/);
  assert.doesNotMatch(teamOps, /operator\.shops\s*=/);
  assert.doesNotMatch(teamOps, /record\.assignedTo\s*=/);
});

test('Chromium smoke inclui a implementação visual G2', () => {
  assert.match(browserSmoke, /team-operations\.mjs/);
  assert.match(browserSmoke, /Solicitar pausa de novos leads/);
});

test('G3 projeta monitoramento da equipe sem relógio, D3, D4 ou acesso de loja inteira', () => {
  assert.match(app, /projectTeamMonitoring\(state\.actorId,state\.cases\)/);
  assert.match(app, /Prazos de espera e atrasos reais: NÃO VERIFICADOS/);
  assert.match(teamMonitoring, /visibleConversations\(records,managerId,shop\)/);
  assert.match(teamMonitoring, /record\.metaWindowProjection==='expired'/);
  assert.match(teamMonitoring, /record\.reassignmentProjection==='protected_queue'/);
  assert.match(teamMonitoring, /COMMERCIAL_STATUSES\.map\(status/);
  assert.doesNotMatch(teamMonitoring, /\bDate\.now\s*\(|\bnew Date\s*\(|\bfetch\s*\(/);
  assert.doesNotMatch(teamMonitoring, /\.registrationProjection\?\.fields|\.bankProjection\?\.submissionVersionRef/);
  assert.match(markup, /id="team-monitor"/);
});

test('G3 tem roteiro visual integrado em Chromium para Desktop',()=>{
  assert.match(browserSmoke, /team-monitoring\.mjs/);
  assert.match(browserSmoke, /Monitoramento operacional da equipe/);
});

test('G3 reconciliado reúne indicadores agregados e alertas técnicos em aba única',()=>{
  assert.match(app, /renderTeamMonitoring\(\);[\s\S]*?target\.replaceChildren\(title,note,indicators,workload,signals/);
  assert.match(app, /commercialSummary=target\.children\[0\]/);
  assert.match(app, /switchTeamPanel\('members'\)/);
  assert.match(app, /projectManagerMonitor\(state\.actorId,state\.cases,state\.teamRequests\)/);
  assert.match(markup, /id="team-show-monitor"/);
  assert.match(markup, /id="team-show-members"/);
  assert.equal((markup.match(/id="team-monitor"/g)||[]).length,1);
});

test('G3 alertas S0 só aceitam projeção de fonte e espera observada sem cronômetro local',()=>{
  assert.match(teamMonitor, /p\.origin!=='s0_fixture'/);
  assert.match(teamMonitor, /Number\.isFinite\(p\.observedWaitMinutes\)/);
  assert.match(teamMonitor, /visibleConversations\(records,managerId,shopId\)/);
  assert.match(teamMonitor, /row\.teamManagerId!==managerId/);
  assert.doesNotMatch(teamMonitor, /\bDate\.now\s*\(|\bnew Date\s*\(|\bfetch\s*\(|\bXMLHttpRequest\b/);
  assert.doesNotMatch(teamMonitor, /registrationProjection|submissionVersionRef|safeDisplayValue/);
});

test('Chromium smoke usa ambos módulos G3 e só lê painel depois de ativá-lo',()=>{
  assert.match(browserSmoke, /'team-monitor\.mjs','team-monitoring\.mjs','batch-monitor\.mjs','distribution-view\.mjs','transport-state-view\.mjs','conversation-attention\.mjs','app\.mjs'/);
  assert.match(browserSmoke, /page\.locator\('#team-show-monitor'\)\.click\(\)/);
  assert.match(browserSmoke, /page\.locator\('#team-show-members'\)\.click\(\)/);
});

test('G4 mostra somente lotes fictícios autorizados por equipe e loja',()=>{
  assert.match(app, /projectManagerBatches\(state\.actorId\)/);
  assert.match(app, /switchTeamPanel\('batches'\)/);
  assert.match(batchMonitor, /row\.managerId!==managerId/);
  assert.match(batchMonitor, /operators\.some\(operator=>operator\.shops\.includes\(row\.shopId\)\)/);
  assert.match(batchMonitor, /countsConfirmed===true/);
  assert.match(batchMonitor, /eligible\+batch\.quarantined===batch\.received/);
  assert.equal((markup.match(/id="team-batches"/g)||[]).length,1);
});

test('G4 não executa uploads, edição de concessão ou mudança de status comercial',()=>{
  assert.doesNotMatch(batchMonitor, /\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\b|\bFileReader\b/);
  assert.doesNotMatch(batchMonitor, /\.assignedTo\s*=(?!=)|\.shops\s*=(?!=)|\.status\s*=(?!=)/);
  assert.match(app, /Somente leitura\. Upload, aceitação de linhas, roteamento/);
  assert.match(browserSmoke, /'batch-monitor\.mjs','distribution-view\.mjs','transport-state-view\.mjs','conversation-attention\.mjs','app\.mjs'/);
  assert.match(browserSmoke, /page\.locator\('#team-show-batches'\)\.click\(\)/);
});

test('FV-UI-013 UX: intro detalhável, contraste e toque, indicadores gerenciais priorizados',()=>{
  assert.match(markup, /<details class="team-help"><summary>Entenda o alcance e os limites<\/summary>/);
  assert.match(markup, /Solicitar pausa ou retomada de novos leads alcança TODAS as lojas/);
  assert.match(styles, /\.team-mode \.btn\{min-height:44px/);
  assert.match(styles, /\.team-dialog \.icon-button\{width:44px;height:44px/);
  assert.match(styles, /\.team-dialog \.team-monitor-metric span\{color:#536d75;font-size:11px/);
  assert.match(app, /target\.replaceChildren\(title,note,indicators,workload,signals/);
});


test('FV-UI-013 funcional: ações do aplicativo exigem listas de permissão e template tipadas',()=>{
  assert.match(contract, /export function hasProjectedAction\(record, action\)/);
  assert.match(contract, /Array\.isArray\(record\?\.allowedActionsProjection\)/);
  assert.match(contract, /Array\.isArray\(record\?\.eligibleTemplatesProjection\)/);
  assert.match(app, /hasProjectedAction\(record,'complete'\)/);
  assert.match(app, /DEMO_TEMPLATES\.filter\(t=>hasEligibleTemplateVersion\(current,t\)\)/);
  assert.doesNotMatch(app, /allowedActionsProjection\?\.includes\('complete'\)/);
});

test('FV-UI-016: prévia de carteira G2 não executa redistribuições',()=>{
  assert.match(app,/projectManagerPausePreview\(state\.actorId,member\.id,state\.cases\)/);
  assert.match(app,/Somente prévia fictícia\. Nenhuma atribuição, conta ou concessão é alterada/);
  assert.match(browserSmoke,/'team-pause-preview\.mjs','team-monitor\.mjs'/);
  assert.match(browserSmoke,/page\.locator\('\.team-pause-preview summary'\)\.first\.click\(\)/);
});


test('FV-UI-017: prévia humana, assinatura legível e nenhuma confirmação Meta inventada',()=>{
  assert.match(markup,/id="message-preview-dialog"/);
  assert.match(markup,/id="message-preview-body"/);
  assert.match(app,/operador:'Consultor', gestor:'Gestor', responsavel:'Diretor'/);
  assert.match(app,/stageHumanMessagePreview\(getActor\(state\.actorId\),input\.value\)/);
  assert.match(app,/deliveryState:'local_demo_not_sent'/);
  assert.match(app,/clearComposerContext\(\)/);
  assert.match(styles,/\.message p\{white-space:pre-wrap\}/);
  assert.match(styles,/\.message-preview-body\{white-space:pre-wrap/);
  assert.doesNotMatch(app,/deliveryState:'sent_confirmed'/);
  assert.doesNotMatch(app,/\bfetch\s*\(|\bXMLHttpRequest\b/);
});


test('FV-UI-019: recortes históricos S0 fictícios e nova conclusão não promovem persistência',()=>{
  assert.match(app,/projectMockHumanCycleHistory\(item,state\.actorId,state\.shopId\)/);
  assert.match(app,/projectMockClarificationScene\(current,state\.actorId,state\.shopId\)/);
  assert.match(app,/stageMockRepeatCompletion\(item,state\.actorId,state\.shopId\)/);
  assert.match(app,/candidateCutoffRef/);
  assert.match(humanCycles,/confirmedByS0:false/);
  assert.match(humanCycles,/persisted:false/);
  assert.match(humanCycles,/bankSnapshots/);
  assert.match(browserSmoke,/FV-UI-019 histórico F03/);
  assert.doesNotMatch(humanCycles,/\bfetch\s*\(|\bXMLHttpRequest\b/);
});

test('FV-UI-020: ACK e estado incerto nunca viram envio provado no navegador',()=>{
  assert.match(app,/stageMockMessageTransport\(item,m,state\.actorId,state\.shopId\)/);
  assert.match(app,/stageMockMessageTransport\(item,message,item\.assignedTo,item\.shopId\)\.provedSent/);
  assert.doesNotMatch(app,/!message\.transportProjection\s*\|\|\s*stageMockMessageTransport/);
  assert.match(transport,/hasMockCaseScope\(record,actorId,shopId\)/);
  assert.match(transport,/api_accepted/);
  assert.match(transport,/failed_confirmed/);
  assert.match(transport,/message\.deliveryState==='local_demo_not_sent'/);
  assert.match(styles,/\.message-transport-state/);
  assert.match(browserSmoke,/FV-UI-020 fronteira de transporte/);
  assert.doesNotMatch(transport,/fetch\s*\(|XMLHttpRequest/);
});


test('FV-UI-020: resultado técnico conservador e C13 fora das ações candidatas da UI',()=>{
  assert.match(feedback,/automaticRetryAllowed:false/);
  assert.match(feedback,/effectConfirmed:false/);
  assert.match(feedback,/commercialTransition:false/);
  assert.match(app,/projectDemoOperationFeedback\(proc\.kind\)/);
  assert.match(app,/não há correção manual ou retentativa automática/);
  assert.doesNotMatch(command,/\['C11', 'C12', 'C13'/);
  assert.match(command,/C13 is historical/);
  assert.doesNotMatch(feedback,/\bfetch\s*\(|\bXMLHttpRequest\b/);
});

test('FV-UI-021: foco e contexto acessíveis, sem tocar dados ou integrações reais',()=>{
  assert.match(markup,/id="context-announcement"/);
  assert.match(markup,/class="sr-only" role="status" aria-live="polite"/);
  assert.match(markup,/id="conversation-list"[^>]*tabindex="-1"/);
  assert.match(app,/function announceCurrentContext\(detail=''/);
  assert.match(app,/announceCurrentContext\('Perfil alterado'\)/);
  assert.match(app,/announceCurrentContext\('Concessionária alterada'\)/);
  assert.match(app,/\['ArrowLeft','ArrowRight','Home','End'\]/);
  assert.match(styles,/\.sr-only\{/);
  assert.match(styles,/\.detail-tab\{min-height:44px\}/);
  assert.match(styles,/max-height:550px/);
});

test('FV-UI-021: gate não aciona rede e nunca autoriza efeito ou dados',()=>{
  assert.match(integrationGate,/stageProposedS0ReadEnvelope/);
  assert.match(integrationGate,/stageCandidateCommandResult/);
  assert.match(integrationGate,/canExposeRecords:false/);
  assert.match(integrationGate,/canPerformCommand:false/);
  assert.match(integrationGate,/hasVerifiedEffect:false/);
  assert.match(integrationGate,/automaticRetry:false/);
  assert.match(integrationGate,/canChangeCommercialStatus:false/);
  assert.match(browserSmoke,/FV-UI-021 foco móvel/);
  assert.doesNotMatch(integrationGate,/\bfetch\s*\(|XMLHttpRequest|WebSocket/);
});

test('FV-UI-022: smoke tem carteira atual, retorno de Escape e mock de campo real',()=>{
  assert.match(browserSmoke,/conversation-card'\)\.count\(\) == 12\s+# A-117/);
  assert.doesNotMatch(browserSmoke,/conversation-card'\)\.count\(\) == 11/);
  assert.match(browserSmoke,/FV-UI-022 Escape mobile/);
  assert.match(browserSmoke,/Rascunho de teste não enviado/);
  assert.match(app,/function mobileBackNavigation\(\)/);
  assert.match(app,/event\.preventDefault\(\);\s*mobileBackNavigation\(\)/);
  assert.match(app,/if\(validDraft && !document\.querySelector\('dialog\[open\]'\)\)input\.focus\(\)/);
  assert.match(domMock,/\['search-input','message-input'\]\.includes\(id\) \? 'input'/);
});

test('FV-UI-023: verificador de ZIP usa somente fontes pinadas e rejeita script diferente',()=>{
  assert.match(offlineExport,/exported_paths!=expected_paths/);
  assert.match(offlineExport,/archived_verifier!=Path\(__file__\)\.read_bytes\(\)/);
  assert.match(offlineExport,/len\(names\)!=len\(set\(names\)\)/);
  assert.match(offlineExport,/stat\.S_ISLNK\(mode\)/);
  assert.match(offlineExport,/blob_sha\(raw\)!=info\["sha"\]/);
  assert.match(offlineExport,/\["node","--test",\*tests\]/);
  assert.match(offlineExport,/\["chromium"\]/);
  assert.match(offlineExport,/full_acceptance":False/);
  assert.doesNotMatch(offlineExport,/git clone|curl|urllib|requests\.get/);
});

test('FV-UI-025: falha de segurança bloqueia efetivamente execução nativa posterior',()=>{
  assert.match(offlineExport,/if security\["executed"\] and security\["passed"\]:/);
  assert.match(offlineExport,/blocked by ZIP verifier security regression/);
  assert.match(offlineExport,/for gate in \("node","chromium"\)/);
  assert.match(offlineExport,/\[sys\.executable,"-B","-m","unittest"/);
  assert.match(offlineRunner,/security_ok=security_step\["passed"\] and security_step\["executed"\]/);
  assert.match(offlineRunner,/not inventory_ok or not node or not revision_ok or not security_ok/);
  assert.match(offlineRunner,/elif not inventory_ok or not revision_ok or not security_ok or not node_ok/);
  assert.match(offlineRunner,/node_ok=node_step\["passed"\] and node_step\["executed"\]/);
  assert.match(offlineExport,/if node_step\["executed"\] and node_step\["passed"\]:/);
  assert.match(offlineExport,/blocked by Node ESM regression/);
  assert.match(offlineRunner,/\[sys\.executable,"-B","-m","unittest"/);
  for(const name of [
    'test_native_gates_block_after_security_failure',
    'test_native_gates_block_if_python_security_not_executed',
    'test_native_gates_run_only_after_python_security_passes',
    'test_native_gates_block_chromium_after_node_failure',
    'test_native_gates_block_chromium_if_node_not_executed'
  ])assert.ok(offlineAdversarial.includes('def '+name+'('),name);
});

test('FV-UI-027: lista rola em viewport baixo e teste real mede reflow',()=>{
  assert.match(styles,/@media\(max-width:760px\) and \(max-height:700px\)/);
  assert.match(styles,/\.list-pane\{overflow-y:auto;overscroll-behavior-y:contain\}/);
  assert.match(styles,/\.conversation-items\{flex:0 0 auto;min-height:170px;overflow:visible\}/);
  assert.match(styles,/@media\(prefers-reduced-motion:reduce\)/);
  assert.match(browserSmoke,/FV-UI-027 reflow responsivo/);
  assert.match(browserSmoke,/reduced_motion='reduce'/);
  assert.match(browserSmoke,/zoom_height<=700/);
  assert.match(browserSmoke,/scroll_into_view_if_needed\(\)/);
});


test('FV-UI-028: aria-expanded móvel e foco contrastante têm contrato de origem',()=>{
  assert.match(app,/String\(view==='detail'\)/);
  assert.match(app,/if\(window\.matchMedia\('\(max-width:760px\)'\)\.matches\)/);
  assert.match(styles,/\.workspace :is\(button,input,select,textarea,summary\):focus-visible/);
  assert.match(styles,/outline:3px solid #11685d/);
  assert.match(browserSmoke,/FV-UI-028 acessibilidade teclado/);
});


test('FV-UI-029: confirmação de modais aninhados anuncia sem perder foco',()=>{
  assert.match(markup,/id="team-action-announcement"[^>]*role="status" aria-live="polite"/);
  assert.match(domMock,/'team-action-announcement'/);
  assert.match(app,/function announceTeamActionAndRestoreFocus\(tabId,announcement\)/);
  assert.match(app,/announceTeamActionAndRestoreFocus\('team-show-members'/);
  assert.match(app,/announceTeamActionAndRestoreFocus\('team-show-queue'/);
  assert.match(app,/if\(!\$\('team-dialog'\)\.open \|\| !canSeeTeamSummary/);
  assert.match(browserSmoke,/FV-UI-029 confirmação, anúncio e retorno do foco/);
});

test('FV-UI-031: nota fictícia não perde foco após recriar formulário',()=>{
  assert.match(app,/renderDetails\(\);target\.querySelector\('#note-text'\)\?\.focus\(\)/);
  assert.match(browserSmoke,/FV-UI-031: foco não deve cair no BODY/);
  assert.match(domMock,/selector\.startsWith\('#'\)/);
});

test('FV-UI-032: foco de extração e navegação O5 têm contratos de origem',()=>{
  assert.match(app,/function focusExtractionAfterRerender\(caseId,notice\)/);
  assert.match(app,/focusExtractionAfterRerender\(item\.id,'Resultado técnico fictício '/);
  assert.match(app,/focusExtractionAfterRerender\(item\.id,'Cenário de esclarecimento fictício do caso '/);
  assert.match(app,/document\.querySelector\('dialog\[open\]'\)/);
  assert.match(app,/else \$\('thread-pane'\)\.focus\(\)/);
  assert.match(markup,/id="thread-pane" aria-labelledby="thread-title" tabindex="-1"/);
  assert.match(browserSmoke,/FV-UI-032: resultado recria o DOM/);
  assert.match(browserSmoke,/FV-UI-032: a navegação O5 móvel/);
});

test('FV-UI-033: foco não desaparece ao atravessar breakpoint no zoom',()=>{
  assert.match(app,/let wasMobileViewport=window\.matchMedia/);
  assert.match(app,/document\.addEventListener\('focusin'/);
  assert.match(app,/window\.addEventListener\('resize'/);
  assert.match(app,/const canShowDetail=region==='detail' && selectedCase\(\)/);
  assert.match(app,/lastResponsiveFocus\.region===targetView/);
  assert.match(browserSmoke,/FV-UI-033 foco e reflow na transição de breakpoints: PASS/);
  assert.match(browserSmoke,/set_viewport_size\(\{'width':360,'height':500\}\)/);
  assert.match(browserSmoke,/set_viewport_size\(\{'width':1440,'height':900\}\)/);
});


test('FV-UI-034: fechamento do painel tablet não perde foco ou fecha modal',()=>{
  assert.match(app,/function closeFloatingDetails\(\)/);
  assert.match(app,/document\.querySelector\('dialog\[open\]'\)\)return false/);
  assert.match(app,/\$\('detail-toggle'\)\.focus\(\)/);
  assert.match(app,/\$\('detail-pane'\)\.contains\(document\.activeElement\)/);
  assert.match(domMock,/tablet = false/);
  assert.match(browserSmoke,/FV-UI-034 Escape tablet e foco ao fechar detalhes: PASS/);
});


test('FV-UI-035: retorno do foco dos controles mobile após ampliar viewport',()=>{
  assert.match(app,/const lastMobileBack=lastResponsiveFocus\.node\?\.id/);
  assert.match(app,/lastMobileBack==='detail-back'/);
  assert.match(app,/lastMobileBack==='thread-back'/);
  assert.match(app,/\$\('detail-content'\)\.querySelector\('\.detail-tab\.active'\)/);
  assert.match(app,/\$\('thread-pane'\)\.focus\(\)/);
  assert.match(browserSmoke,/FV-UI-035 retorno de foco ao ampliar mobile para desktop\/tablet: PASS/);
  assert.match(browserSmoke,/for destination_width in \(900,1440\)/);
});


test('FV-UI-036: temas claro e escuro têm contrato visual e de controle',()=>{
  assert.match(markup,/id="theme-light"/);
  assert.match(markup,/id="theme-dark"/);
  assert.match(app,/theme: systemColorScheme\.matches \? 'dark' : 'light'/);
  assert.match(app,/function applyTheme\(theme\)/);
  assert.match(app,/document\.body\) document\.body\.dataset\.theme = theme/);
  assert.match(styles,/body\[data-theme=\"dark\"\] dialog/);
  assert.match(app,/\$\('theme-light'\)\.addEventListener\('click'/);
  assert.match(app,/\$\('theme-dark'\)\.addEventListener\('click'/);
  assert.match(styles,/\.theme-switch/);
  assert.match(styles,/\.visual-app\[data-theme="dark"\]/);
  assert.match(browserSmoke,/FV-UI-036 tema claro\/escuro e superfícies neutras: PASS/);
});


test('FV-UI-037: preferência dinâmica só antes da escolha manual',()=>{
  assert.match(app,/systemColorScheme\.addEventListener\('change'/);
  assert.match(app,/if\(!state\.themeOverride\) applyTheme/);
  assert.match(app,/state\.themeOverride=true;applyTheme\('dark'\)/);
  assert.match(app,/state\.themeOverride=true;applyTheme\('light'\)/);
  assert.match(domMock,/setSystemDark\(dark\)/);
  assert.match(browserSmoke,/FV-UI-037 sistema e escolha manual: PASS/);
});


test('FV-UI-038: contraste do modal gerencial no tema escuro é verificado no navegador',()=>{
  assert.match(styles,/body\[data-theme="dark"\] \.team-dialog \.team-batch-summary/);
  assert.match(styles,/body\[data-theme="dark"\] \.team-dialog :is\(/);
  assert.match(styles,/\.team-help summary/);
  assert.match(styles,/outline-color:#8ad6c5/);
  assert.match(browserSmoke,/FV-UI-038 contraste de painel gerencial em dark desktop e mobile: PASS/);
  assert.match(browserSmoke,/ratio>=4\.5/);
});


test('FV-UI-039: temas têm alvos de toque legíveis e reflow de cabeçalho',()=>{
  assert.match(styles,/\.theme-option\{min-height:44px;min-width:44px/);
  assert.match(styles,/@media\(max-width:400px\)/);
  assert.match(styles,/\.list-topline\{align-items:flex-start;flex-wrap:wrap\}/);
  assert.match(browserSmoke,/FV-UI-039 botoes de tema 44px e reflow em quatro larguras: PASS/);
  assert.match(browserSmoke,/theme_width in \(320,390,900,1440\)/);
});


test('FV-UI-040: informações da fila ganham hierarquia nos dois temas',()=>{
  assert.match(styles,/\.list-pane \.item-title\{font-size:14px/);
  assert.match(styles,/\.list-pane \.item-preview\{font-size:12px/);
  assert.match(styles,/\.list-pane \.item-time\{font-size:11px/);
  assert.match(styles,/\.list-pane \.micro-tag\{font-size:11px/);
  assert.match(styles,/\.list-pane \.summary-tile span\{font-size:11px/);
  assert.match(styles,/\.visual-app\[data-theme="dark"\] \.list-pane \.summary-tile span/);
  assert.match(browserSmoke,/FV-UI-040 hierarquia legivel da fila em 8 cenarios: PASS/);
  assert.match(browserSmoke,/ratio>=4\.5/);
});


test('FV-UI-041: detalhes mantem texto legivel e abas sem mudar contratos',()=>{
  assert.match(styles,/\.detail-pane \.property\{font-size:12px/);
  assert.match(styles,/\.detail-pane \.detail-label\{font-size:11px/);
  assert.match(styles,/\.detail-pane \.detail-tab\{font-size:12px;min-height:44px/);
  assert.match(styles,/\.visual-app\[data-theme="dark"\] \.detail-pane \.detail-callout\.warning/);
  assert.match(browserSmoke,/FV-UI-041 detalhes legiveis em oito cenarios e abas preservadas: PASS/);
  assert.match(browserSmoke,/ratio>=4\.5/);
});
