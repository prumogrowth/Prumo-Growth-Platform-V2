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
