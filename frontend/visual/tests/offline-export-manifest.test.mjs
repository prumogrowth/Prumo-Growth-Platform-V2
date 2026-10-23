/** FV-UI-023: prova nativa do snapshot GitHub ZIP, sem rede.
 * O verificador Python NÃO pode aceitar qualquer arquivo da branch atual
 * se o manifesto pinado não contiver todos os blobs e seus hashes Git.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {dirname,join,relative,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const here=dirname(fileURLToPath(import.meta.url));
const visual=join(here,'..');
const verifier=readFileSync(join(here,'verify_offline_export.py'),'utf8');
const encoded=verifier.match(/^MANIFEST = json\.loads\(("(?:(?:\\.)|[^"\\])*")\)$/m);
const manifest=encoded ? JSON.parse(JSON.parse(encoded[1])) : null;
const logical=path=>'frontend/visual/'+path.split(sep).join('/');
const blobs=()=>{
  const top=readdirSync(visual,{withFileTypes:true})
    .filter(v=>v.isFile()).map(v=>v.name);
  const tests=readdirSync(here,{withFileTypes:true})
    .filter(v=>v.isFile() && v.name!=='verify_offline_export.py')
    .map(v=>'tests/'+v.name);
  return [...top,...tests].map(logical).sort();
};
const shaGit=data=>createHash('sha1')
  .update(Buffer.from('blob '+data.length+'\0')).update(data).digest('hex');

test('FV-UI-023: manifesto oficial identifica branch e revisão pinadas',()=>{
  assert.ok(manifest,'Manifesto ZIP pinado não encontrado no verificador');
  assert.match(manifest.source_head,/^[0-9a-f]{40}$/);
  assert.equal(manifest.source_branch,'feat/frontend-plataforma-visual');
});

test('FV-UI-023: manifesto cobre cada fonte/teste e rejeita inventário antigo',()=>{
  assert.ok(manifest);
  assert.deepEqual(Object.keys(manifest.files).sort(),blobs());
  const tests=Object.keys(manifest.files).filter(name=>name.endsWith('.test.mjs'));
  assert.equal(tests.length,readdirSync(here).filter(name=>name.endsWith('.test.mjs')).length);
  assert.ok(tests.includes('frontend/visual/tests/offline-export-manifest.test.mjs'));
  assert.ok(!Object.hasOwn(manifest.files,'frontend/visual/tests/verify_offline_export.py'),
    'O verificador evita autopinagem recursiva');
});

test('FV-UI-023: tamanho e Git blob SHA-1 do manifesto coincidem com checkout',()=>{
  assert.ok(manifest);
  for(const [path,entry] of Object.entries(manifest.files)){
    assert.match(path,/^frontend\/visual\/[a-zA-Z0-9_./-]+$/);
    assert.ok(!path.includes('..') && !path.includes('\\'));
    assert.match(entry.sha,/^[a-f0-9]{40}$/);
    const data=readFileSync(join(visual,relative('frontend/visual',path)));
    assert.equal(data.length,entry.size,path+' size');
    assert.equal(shaGit(data),entry.sha,path+' blob');
  }
});
