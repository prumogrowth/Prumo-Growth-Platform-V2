// FV-UI-013 — garante integridade do bootstrap de módulos no script Chromium local.
// Este teste roda nativamente em Node. Não é prova de execução no navegador.
import test from 'node:test';
import assert from 'node:assert/strict';
import {Script} from 'node:vm';
import {readFileSync, existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname, join} from 'node:path';

const visual = dirname(fileURLToPath(new URL('../app.mjs', import.meta.url)));
const read = name => readFileSync(join(visual, name), 'utf8');
const order = [
  'fixtures.mjs', 'view-model.mjs', 'cf-op-02.mjs',
  'registration-view.mjs', 'human-cycle-view.mjs', 'operation-feedback.mjs', 'bank-view.mjs', 'postmark-view.mjs',
  'team-operations.mjs', 'team-pause-preview.mjs', 'team-monitor.mjs', 'team-monitoring.mjs',
  'batch-monitor.mjs', 'distribution-view.mjs', 'transport-state-view.mjs', 'conversation-attention.mjs', 'local-audio.mjs', 'communication-composer.mjs', 'app.mjs'
];
const src = Object.fromEntries(order.map(name=>[name,read(name)]));
const smoke = read('tests/browser.smoke.py');
const html = read('index.html');

test('cada módulo local importado existe e aparece antes do consumidor no bundle de ensaio',()=>{
  for(const [name,contents] of Object.entries(src)){
    const dependencies=[...contents.matchAll(/from ['"]\.\/([^'"]+\.mjs)['"]/g)]
      .map(match=>match[1]);
    for(const dep of dependencies){
      assert.ok(existsSync(join(visual,dep)),name+' importa módulo ausente '+dep);
      assert.ok(order.indexOf(dep)!==-1 && order.indexOf(dep)<order.indexOf(name),
        name+' depende de módulo fora de ordem: '+dep);
    }
  }
});

test('roteiro Chromium lista exatamente os módulos usados pela demonstração na ordem correta',()=>{
  const tuple=smoke.match(/for name in \(([^)]+)\)\)/);
  assert.ok(tuple,'Lista de módulos ausente do ensaio Chromium');
  const actual=[...tuple[1].matchAll(/'([^']+\.mjs)'/g)].map(x=>x[1]);
  assert.deepEqual(actual,order);
});

test('HTML tem IDs únicos e um único CSS e módulo de entrada',()=>{
  const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);
  assert.equal(new Set(ids).size,ids.length,'ID duplicado no HTML');
  assert.equal((html.match(/<script type="module" src="\.\/app\.mjs"><\/script>/g)||[]).length,1);
  assert.equal((html.match(/<link rel="stylesheet" href="\.\/styles\.css">/g)||[]).length,1);
  for(const id of ['team-dialog','team-show-members','team-show-monitor',
                   'team-show-batches','team-monitor','team-batches']){
    assert.ok(ids.includes(id),'Controle visual não encontrado: '+id);
  }
});

test('ensaio real verifica erros no JS após interações e overflow em múltiplas larguras',()=>{
  assert.match(smoke,/for width, height in \(\(1440,900\),\(900,780\),\(390,844\),\(320,640\)\)/);
  assert.match(smoke,/errors_main/);
  assert.match(smoke,/errors_mobile/);
  assert.match(smoke,/scrollWidth > innerWidth/);
  assert.match(smoke,/CHROMIUM_EXECUTABLE/);
});

// browser.smoke.py injeta módulos concatenados como um único script clássico.
// Dependências e sintaxe individuais não detectam colisões léxicas entre módulos.
test('bundle de ensaio Chromium compila integralmente sem imports, exports ou colisões',()=>{
  const combined=order.map(name=>src[name]).join('\n');
  // Mesmo contrato de transformação usado pelo roteiro Python browser.smoke.py.
  const bundled=combined
    .replace(/^import \{.*?\} from ["']\.\/[^"']+["'];\s*/gms,'')
    .replace(/^export /gm,'');
  assert.doesNotMatch(bundled,/^import /m,'Import residual no bundle injetado');
  assert.doesNotMatch(bundled,/^export /m,'Export residual no bundle injetado');
  assert.doesNotThrow(()=>new Script(bundled,{filename:'fv-ui-013-chromium-bundle.js'}));
});


test('roteiro Chromium cobre G3 e G4 em viewport mobile e nega dados de outra equipe',()=>{
  const mobile=smoke.match(/mobile = browser\.new_page\([\s\S]*?browser\.close\(\)/);
  assert.ok(mobile,'Bloco de gestão mobile não encontrado');
  for(const marker of [
    "mobile.locator('#team-show-monitor').click()",
    "mobile.locator('#team-monitor').is_visible()",
    "mobile.locator('#team-show-batches').click()",
    "mobile.locator('#team-batches').is_visible()",
    "'L-G4-03' not in batches_mobile",
    "'Bianca Rocha' not in monitor_mobile",
    "'Bianca Rocha' not in mobile.locator('#team-list').inner_text()",
    "'Overflow mobile em G3/G4'"
  ]) assert.ok(mobile[0].includes(marker),'Cobertura mobile ausente: '+marker);
});


test('G2/G3/G4 no smoke mobile usam duas larguras mínimas reais',()=>{
  assert.match(smoke,/for mobile_width,mobile_height in \(\(390,844\),\(320,640\)\):/);
  assert.match(smoke,/mobile = browser\.new_page\(viewport=\{'width':mobile_width,'height':mobile_height\}\)/);
  assert.match(smoke,/mobile\.locator\('#team-show-monitor'\)\.click\(\)/);
  assert.match(smoke,/mobile\.locator\('#team-show-batches'\)\.click\(\)/);
  assert.match(smoke,/assert not mobile\.evaluate\('document\.documentElement\.scrollWidth > innerWidth'\)/);
});
