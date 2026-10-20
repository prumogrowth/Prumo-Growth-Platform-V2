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
const bank = get('bank-view.mjs');
const postmark = get('postmark-view.mjs');
const teamOps = get('team-operations.mjs');
const teamMonitoring = get('team-monitoring.mjs');
const teamMonitor = get('team-monitor.mjs');
const batchMonitor = get('batch-monitor.mjs');
const fixtureTeam = get('fixtures.mjs');
const browserSmoke = get('tests/browser.smoke.py');

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
  assert.match(browserSmoke, /'team-monitor\.mjs','team-monitoring\.mjs','batch-monitor\.mjs','app\.mjs'/);
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
  assert.match(browserSmoke, /'batch-monitor\.mjs','app\.mjs'/);
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
