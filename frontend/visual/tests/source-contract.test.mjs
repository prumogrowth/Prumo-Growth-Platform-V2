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
  assert.match(registration, /actor\.role !== 'gestor' && record\.assignedTo !== actorId/);
  assert.match(bank, /actor\.role !== 'gestor' && record\.assignedTo !== actorId/);
});

test('auditoria: operação independente da autorização de leitura do caso anterior',()=>{
  assert.match(postmark, /export function mayMockOperateContinuation/);
  assert.match(postmark, /record\.assignedTo!==actorId/);
  assert.match(postmark, /relation\.kind!=='restricted'/);
  assert.match(postmark, /origin\.shopId!==record\.shopId/);
});
