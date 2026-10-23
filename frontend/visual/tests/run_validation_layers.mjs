/** FV-UI-030: execução diagnóstica por camadas para facilitar redesign.
 * Não substitui tests/run_acceptance.py, não homologa produção.
 * Uso: node frontend/visual/tests/run_validation_layers.mjs interaction
 */
import {readFileSync,readdirSync,existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';
import {spawnSync} from 'node:child_process';

const here=dirname(fileURLToPath(import.meta.url));
const visual=dirname(here);
const names=['domain','interaction','source','browser'];
const chosen=process.argv[2];
if(chosen==='--help'||chosen==='-h'){
  console.log('Uso: node frontend/visual/tests/run_validation_layers.mjs <domain|interaction|source|browser>');
  console.log('Diagnóstico de snapshot; não equivale a homologação Git, de negócio ou de produto.');
  process.exit(0);
}
if(!names.includes(chosen) || process.argv.length!==3){
  console.error('Camada desconhecida. Selecione: '+names.join(', '));
  process.exit(2);
}
const manifest=JSON.parse(readFileSync(join(here,'validation-layers.json'),'utf8'));
if(manifest.schema!=='frontend-validation-layers/1'||manifest.full_acceptance!==false)
  throw new Error('Manifesto de diagnóstico inválido');
const nodeNames=names.filter(n=>n!=='browser').flatMap(n=>manifest.layers[n].node_tests);
const actual=readdirSync(here).filter(n=>n.endsWith('.test.mjs')).sort();
const expected=[...new Set(nodeNames)].sort();
if(new Set(nodeNames).size!==nodeNames.length ||
   JSON.stringify(actual)!==JSON.stringify(expected))
  throw new Error('Inventário de suítes alterado: classificar cada *.test.mjs antes de executar');
const layer=manifest.layers[chosen];
const binary=chosen==='browser'?(process.env.PYTHON||'python3'):process.execPath;
const args=chosen==='browser'?
  ['-B',join(here,layer.python_script)]:
  ['--test',...layer.node_tests.map(name=>join(here,name))];
if(chosen==='browser'&&!existsSync(join(here,layer.python_script)))
  throw new Error('Roteiro Chromium ausente do snapshot');
console.log('\nFV-UI-030 • diagnóstico por camada: '+chosen);
console.log('Não homologado: verificar novamente todas as camadas depois do redesign.');
const outcome=spawnSync(binary,args,{
  cwd:visual,stdio:'inherit',timeout:180_000,env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'}
});
if(outcome.error){
  console.error('Diagnóstico não executado: '+outcome.error.message);
  process.exit(1);
}
process.exit(outcome.status===0?0:1);
