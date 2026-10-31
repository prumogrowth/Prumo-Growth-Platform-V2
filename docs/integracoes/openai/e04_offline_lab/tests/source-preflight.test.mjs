import test, {before, after} from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {createRequire, syncBuiltinESMExports} from 'node:module';
import {fileURLToPath} from 'node:url';
import {verifySources, validateManifest, parseManifest, readManifest, parseArguments,
  SourcePreflightError} from '../source-preflight.mjs';

// Disposable local Git repositories only. These synthetic commits are not the
// official source pins and never stand in for the unavailable historical S2.
const require = createRequire(import.meta.url);
const cp = require('node:child_process');
const cfs = require('node:fs');
const net = require('node:net');
const http = require('node:http');
const https = require('node:https');
const cli = fileURLToPath(new URL('../source-preflight.mjs', import.meta.url));
const repo = 'synthetic/off01-fixture';
const historical = 'ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c';
const digest = (alg, bytes) => createHash(alg).update(bytes).digest('hex');
let templates, templateManifest;
function git(root, ...args) {
  const run = spawnSync('git', ['-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', ...args], {
    cwd: root, encoding: 'utf8', env: {PATH: process.env.PATH, LC_ALL: 'C',
      GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: '/dev/null',
      GIT_AUTHOR_NAME: 'Synthetic OFF01', GIT_AUTHOR_EMAIL: 'fixture@example.invalid',
      GIT_COMMITTER_NAME: 'Synthetic OFF01', GIT_COMMITTER_EMAIL: 'fixture@example.invalid',
      GIT_AUTHOR_DATE: '2026-10-01T00:00:00Z', GIT_COMMITTER_DATE: '2026-10-01T00:00:00Z'},
  });
  assert.equal(run.status, 0, run.stderr);
  return run.stdout.trim();
}
function commit(root, text) {
  fs.mkdirSync(path.join(root, 'docs'), {recursive: true});
  fs.writeFileSync(path.join(root, 'docs/shared.txt'), 'same synthetic bytes\n');
  fs.writeFileSync(path.join(root, 'docs/variant.txt'), text);
  git(root, 'add', '--all'); git(root, 'commit', '-m', 'synthetic source fixture');
}
function file(root, name) {
  const bytes = fs.readFileSync(path.join(root, name));
  return {path: name, mode: '100644', byte_length: bytes.length,
    sha256: digest('sha256', bytes), git_blob: git(root, 'rev-parse', `HEAD:${name}`)};
}
before(() => {
  templates = fs.mkdtempSync(path.join(os.tmpdir(), 'off01-templates-'));
  for (const id of ['i86', 's2', 'f03']) {
    const root = path.join(templates, id); fs.mkdirSync(root);
    git(root, 'init', '--object-format=sha1');
    git(root, 'remote', 'add', 'origin', `https://github.com/${repo}.git`);
    commit(root, 'old synthetic CFI\n');
  }
  fs.cpSync(path.join(templates, 'i86'), path.join(templates, 's0'), {recursive: true});
  commit(path.join(templates, 's0'), 'later synthetic CFI\n');
  const sources = ['s2', 'f03', 's0', 'i86'].map(id => {
    const root = path.join(templates, id);
    return {id, repository: repo, reference_branch: 'synthetic/fixture',
      commit: git(root, 'rev-parse', 'HEAD'), tree: git(root, 'rev-parse', 'HEAD^{tree}'),
      requirement: ['s2', 'f03'].includes(id) ? 'required' : 'optional',
      files: ['docs/shared.txt', 'docs/variant.txt'].map(name => file(root, name))};
  });
  templateManifest = {schema: 'prumo.openai.source-manifest/1.0', purpose: 'OFFLINE_SOURCE_INTEGRITY_ONLY',
    object_format: 'sha1', sources, comparisons: [
      {id: 'shared', left: {source: 'f03', path: 'docs/shared.txt'}, right: {source: 's0', path: 'docs/shared.txt'}, expected: 'IDENTICAL_BYTES'},
      {id: 'cfi', left: {source: 'f03', path: 'docs/variant.txt'}, right: {source: 's0', path: 'docs/variant.txt'}, expected: 'DIFFERENT_BYTES'},
    ], ancestry: [{id: 'i86-base', ancestor: 'i86', descendant: 's0'}], historical: [
      {id: 's2-a38-history', repository: repo, commit: historical,
        documentary_origin: [{source: 'f03', path: 'docs/variant.txt'}],
        recovery: 'NOT_RECOVERED_IN_OAI_RET_01', required_for: ['a38'], replacement: null,
        reason: 'Synthetic documentary reference; never an executed A38 fixture.'},
    ]};
});
after(() => fs.rmSync(templates, {recursive: true, force: true}));
function fixture(t) {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), 'off01-test-'));
  t.after(() => fs.rmSync(base, {recursive: true, force: true}));
  const roots = {};
  for (const id of ['s2', 'f03', 's0', 'i86']) {
    roots[id] = path.join(base, id); fs.cpSync(path.join(templates, id), roots[id], {recursive: true});
  }
  return {base, roots, manifest: structuredClone(templateManifest)};
}
const source = (x, id = 's2') => x.manifest.sources.find(s => s.id === id);
function fails(x, code, extra = {}) {
  const r = verifySources({manifest: x.manifest, roots: x.roots, ...extra});
  assert.equal(r.status, 'SOURCE_INTEGRITY_REJECTED');
  assert.ok(r.errors.some(e => e.code === code), JSON.stringify(r.errors));
  assert.ok(Object.values(r.assurance).every(v => v === false));
  return r;
}
function invalid(mutator, code = 'INVALID_MANIFEST') {
  const m = structuredClone(templateManifest); mutator(m);
  assert.throws(() => validateManifest(m), e => e instanceof SourcePreflightError && e.code === code);
}

test('OFF01 correct S2 F03 and explicitly required S0/I86 verify selected objects and bytes', t => {
  const x = fixture(t), r = verifySources({...x, base: undefined});
  assert.equal(r.status, 'SOURCE_INTEGRITY_REJECTED'); // API rejects unspecified knobs.
  const good = verifySources({manifest: x.manifest, roots: x.roots, requireSources: ['s0', 'i86']});
  assert.equal(good.status, 'SOURCE_INTEGRITY_VERIFIED');
  assert.equal(good.sources.length, 4);
  assert.ok(good.sources.every(s => s.files_verified === 2));
  assert.deepEqual(good.comparisons, [{id: 'cfi', state: 'DIFFERENT_BYTES'}, {id: 'shared', state: 'IDENTICAL_BYTES'}]);
  assert.equal(good.ancestry[0].state, 'ANCESTRY_VERIFIED');
});
test('OFF01 optional absent sources are classified and never counted as verified', t => {
  const x = fixture(t); delete x.roots.s0; delete x.roots.i86;
  const r = verifySources({manifest: x.manifest, roots: x.roots});
  assert.equal(r.status, 'SOURCE_INTEGRITY_VERIFIED');
  assert.equal(r.sources.find(s => s.id === 's0').state, 'OPTIONAL_NOT_PROVIDED');
  assert.ok(r.comparisons.every(c => c.state === 'NOT_EVALUATED_SOURCE_NOT_VERIFIED'));
});
test('OFF01 explicitly required optional S0 cannot be omitted', t => {
  const x = fixture(t); delete x.roots.s0; fails(x, 'CHECKOUT_REQUIRED', {requireSources: ['s0']});
});
test('OFF01 outputs are deterministic and independent of root argument order', t => {
  const x = fixture(t), opts = {manifest: x.manifest, roots: x.roots};
  const first = verifySources(opts), second = verifySources({...opts, roots: Object.fromEntries(Object.entries(x.roots).reverse())});
  assert.deepEqual(first, second); assert.ok(!JSON.stringify(first).includes(x.base));
});
test('OFF01 integrity success preserves historical absence and all authority denials', t => {
  const x = fixture(t), r = verifySources({manifest: x.manifest, roots: x.roots});
  assert.equal(r.status, 'SOURCE_INTEGRITY_VERIFIED');
  assert.equal(r.historical[0].commit, historical);
  assert.equal(r.historical[0].state, 'NOT_RECOVERED_IN_OAI_RET_01');
  assert.deepEqual(r.operations, [{id: 'a38', state: 'BLOCKED_HISTORICAL_SOURCE_UNRECOVERED', tests_executed: false}]);
  assert.ok(Object.values(r.assurance).every(v => v === false));
});
test('OFF01 A38 operation stays blocked without looking for a replacement', t => {
  const x = fixture(t); fails(x, 'HISTORICAL_SOURCE_UNRECOVERED', {operation: 'a38'});
});
test('OFF01 missing checkout argument is typed', t => {
  const x = fixture(t); delete x.roots.s2; fails(x, 'CHECKOUT_REQUIRED');
});
test('OFF01 nonexistent supplied checkout is rejected', t => {
  const x = fixture(t); x.roots.f03 = path.join(x.base, 'absent'); fails(x, 'CHECKOUT_ABSENT');
});
test('OFF01 different HEAD is rejected even when bytes are identical', t => {
  const x = fixture(t); source(x).commit = '1'.repeat(40); fails(x, 'COMMIT_MISMATCH');
});
test('OFF01 origin from another repository is rejected without echoing the URL', t => {
  const x = fixture(t); git(x.roots.s2, 'remote', 'set-url', 'origin', 'https://github.com/synthetic/wrong.git');
  const r = fails(x, 'REPOSITORY_MISMATCH'); assert.ok(!JSON.stringify(r).includes('synthetic/wrong'));
});
test('OFF01 unobservable origin fails closed', t => {
  const x = fixture(t); git(x.roots.s2, 'remote', 'remove', 'origin'); fails(x, 'REPOSITORY_UNOBSERVABLE');
});
test('OFF01 supported SSH origin is an observation of the same repository', t => {
  const x = fixture(t); git(x.roots.s2, 'remote', 'set-url', 'origin', `git@github.com:${repo}.git`);
  assert.equal(verifySources({manifest: x.manifest, roots: x.roots}).status, 'SOURCE_INTEGRITY_VERIFIED');
});
test('OFF01 origin containing credentials is rejected and never reflected', t => {
  const x = fixture(t); git(x.roots.s2, 'remote', 'set-url', 'origin', `https://CANARY_FAKE@github.com/${repo}.git`);
  const r = fails(x, 'REPOSITORY_MISMATCH'); assert.ok(!JSON.stringify(r).includes('CANARY_FAKE'));
});
test('OFF01 missing working file is rejected', t => {
  const x = fixture(t); fs.unlinkSync(path.join(x.roots.s2, 'docs/shared.txt')); fails(x, 'FILE_MISSING');
});
test('OFF01 adulterated working bytes are rejected despite unchanged HEAD', t => {
  const x = fixture(t); fs.appendFileSync(path.join(x.roots.s2, 'docs/shared.txt'), 'tampered'); fails(x, 'CONTENT_MISMATCH');
});
test('OFF01 manifest blob mismatch is distinct from SHA-256 mismatch', t => {
  const x = fixture(t); source(x).files[0].git_blob = '1'.repeat(40); fails(x, 'BLOB_MISMATCH');
});
test('OFF01 altered byte hash is rejected against immutable Git blob', t => {
  const x = fixture(t); source(x).files[0].sha256 = '1'.repeat(64); fails(x, 'HASH_MISMATCH');
});
test('OFF01 altered byte length is rejected', t => {
  const x = fixture(t); source(x).files[0].byte_length++; fails(x, 'HASH_MISMATCH');
});
test('OFF01 Git object identity cannot be replaced by raw SHA-256', () => {
  invalid(m => { m.sources[0].files[0].git_blob = m.sources[0].files[0].sha256; });
});
test('OFF01 pinned tree mismatch is rejected', t => {
  const x = fixture(t); source(x).tree = '1'.repeat(40); fails(x, 'TREE_MISMATCH');
});
test('OFF01 staged selected-file drift is rejected even if working bytes were restored', t => {
  const x = fixture(t), file = path.join(x.roots.s2, 'docs/shared.txt'), saved = fs.readFileSync(file);
  fs.writeFileSync(file, 'staged drift'); git(x.roots.s2, 'add', 'docs/shared.txt'); fs.writeFileSync(file, saved);
  fails(x, 'INDEX_MISMATCH');
});
test('OFF01 path not present in the pinned tree is rejected', t => {
  const x = fixture(t); source(x).files[0].path = 'docs/absent.txt'; fails(x, 'FILE_MISSING');
});
test('OFF01 source mode divergence is rejected', t => {
  const x = fixture(t); source(x).files[0].mode = '100755'; fails(x, 'MODE_MISMATCH');
});
test('OFF01 unexpected local executable mode is rejected', t => {
  const x = fixture(t); fs.chmodSync(path.join(x.roots.s2, 'docs/shared.txt'), 0o755); fails(x, 'MODE_MISMATCH');
});
for (const unsafe of ['../outside', '/etc/passwd', 'docs/../outside', 'docs//file', 'docs/./file',
  '.git/config', 'docs/.env', 'docs\\file', 'docs/*', 'docs/a\nfile']) {
  test(`OFF01 unsafe selected path ${JSON.stringify(unsafe)} is rejected before reading`, () => {
    invalid(m => { m.sources[0].files[0].path = unsafe; }, 'UNSAFE_PATH');
  });
}
test('OFF01 leaf symlink is refused even when target bytes match', t => {
  const x = fixture(t), file = path.join(x.roots.s2, 'docs/shared.txt'), outside = path.join(x.base, 'outside.txt');
  fs.renameSync(file, outside); fs.symlinkSync(outside, file); fails(x, 'SYMLINK_OR_ESCAPE');
});
test('OFF01 parent symlink cannot escape the checkout', t => {
  const x = fixture(t), dir = path.join(x.roots.s2, 'docs'), outside = path.join(x.base, 'outside');
  fs.renameSync(dir, outside); fs.symlinkSync(outside, dir); fails(x, 'SYMLINK_OR_ESCAPE');
});
test('OFF01 checkout root symlink is refused', t => {
  const x = fixture(t), link = path.join(x.base, 'root-link'); fs.symlinkSync(x.roots.s2, link);
  x.roots.s2 = link; fails(x, 'SYMLINK_OR_ESCAPE');
});
test('OFF01 symlink in a checkout root ancestor is refused', t => {
  const x = fixture(t), link = path.join(x.base, 'parent-link'); fs.symlinkSync(x.base, link);
  x.roots.s2 = path.join(link, 's2'); fails(x, 'SYMLINK_OR_ESCAPE');
});
test('OFF01 hardlinked selected file is refused', t => {
  const x = fixture(t); fs.linkSync(path.join(x.roots.s2, 'docs/shared.txt'), path.join(x.base, 'hardlink'));
  fails(x, 'NOT_REGULAR_FILE');
});
test('OFF01 directory in place of a file is refused', t => {
  const x = fixture(t), file = path.join(x.roots.s2, 'docs/shared.txt'); fs.unlinkSync(file); fs.mkdirSync(file);
  fails(x, 'NOT_REGULAR_FILE');
});
test('OFF01 FIFO is refused before opening it', t => {
  const x = fixture(t), file = path.join(x.roots.s2, 'docs/shared.txt'); fs.unlinkSync(file);
  assert.equal(spawnSync('mkfifo', [file]).status, 0); fails(x, 'NOT_REGULAR_FILE');
});
test('OFF01 incomplete source inventory is invalid', () => invalid(m => { m.sources.pop(); }));
test('OFF01 empty file selection is invalid', () => invalid(m => { m.sources[0].files = []; }));
test('OFF01 missing digest field is invalid', () => invalid(m => { delete m.sources[0].files[0].sha256; }));
test('OFF01 duplicate source is invalid', () => invalid(m => { m.sources[1] = structuredClone(m.sources[0]); }));
test('OFF01 duplicate path is invalid', () => invalid(m => { m.sources[0].files.push(m.sources[0].files[0]); }));
test('OFF01 unsupported schema version is rejected', () => invalid(m => { m.schema = 'prumo.openai.source-manifest/2.0'; }, 'MANIFEST_VERSION_UNSUPPORTED'));
for (const mutate of [m => { m.approved = true; }, m => { m.sources[0].approved = true; },
  m => { m.sources[0].files[0].allow_write = true; }, m => { m.comparisons[0].ratified = true; }]) {
  test('OFF01 unknown fields are rejected at their own nesting level', () => invalid(mutate, 'UNEXPECTED_FIELD'));
}
test('OFF01 malformed JSON is rejected', () => assert.throws(() => parseManifest('{'), {code: 'INVALID_MANIFEST'}));
test('OFF01 duplicate JSON keys are rejected including escaped aliases', () => {
  const text = JSON.stringify(templateManifest);
  assert.throws(() => parseManifest(text.replace('{', '{"schema":"bad",')), {code: 'INVALID_MANIFEST'});
  assert.throws(() => parseManifest(text.replace('{', '{"sch\\u0065ma":"bad",')), {code: 'INVALID_MANIFEST'});
});
test('OFF01 historical replacement is rejected without reading substitute checkout', () => invalid(m => {
  m.historical[0].replacement = {source: 's2'};
}, 'HISTORICAL_SUBSTITUTION_FORBIDDEN'));
test('OFF01 changing the historical commit to current S2 is refused', () => invalid(m => {
  m.historical[0].commit = m.sources[0].commit;
}, 'HISTORICAL_SUBSTITUTION_FORBIDDEN'));
test('OFF01 recovery assertion cannot approve A38', () => invalid(m => {
  m.historical[0].recovery = 'A38_APPROVED';
}, 'HISTORICAL_SUBSTITUTION_FORBIDDEN'));
test('OFF01 a manifest cannot claim integration homologation', () => invalid(m => {
  m.integration_homologated = true;
}, 'UNEXPECTED_FIELD'));
test('OFF01 undeclared checkout substitutes are refused', t => {
  const x = fixture(t); x.roots.historical = x.roots.s2; fails(x, 'INVALID_OPTIONS');
});
test('OFF01 optional checkout supplied incorrectly must fail rather than be skipped', t => {
  const x = fixture(t); x.roots.s0 = x.roots.i86; fails(x, 'COMMIT_MISMATCH');
});
test('OFF01 mismatching declared byte equivalence fails closed', t => {
  const x = fixture(t); x.manifest.comparisons[0].expected = 'DIFFERENT_BYTES'; fails(x, 'COMPARISON_MISMATCH');
});
test('OFF01 reversed ancestry is rejected', t => {
  const x = fixture(t); x.manifest.ancestry[0] = {id: 'reversed', ancestor: 's0', descendant: 'i86'};
  // Populate the later object in this disposable repo so merge-base can prove false.
  fs.cpSync(path.join(x.roots.s0, '.git/objects'), path.join(x.roots.i86, '.git/objects'), {recursive: true, force: false});
  fails(x, 'ANCESTRY_MISMATCH');
});
test('OFF01 partial/promisor repositories cannot initiate object hydration', t => {
  const x = fixture(t); git(x.roots.s2, 'config', 'remote.origin.promisor', 'true'); fails(x, 'PARTIAL_CLONE_UNSUPPORTED');
});
test('OFF01 subdirectory cannot masquerade as checkout root', t => {
  const x = fixture(t); x.roots.s2 = path.join(x.roots.s2, 'docs'); fails(x, 'CHECKOUT_ROOT_MISMATCH');
});
function snapshot(roots) {
  const rows = [];
  function visit(root, rel = '') {
    for (const name of fs.readdirSync(path.join(root, rel)).sort()) {
      const p = path.join(rel, name), stat = fs.lstatSync(path.join(root, p));
      if (stat.isDirectory()) visit(root, p);
      else rows.push([root, p, stat.mode, stat.size, digest('sha256', fs.readFileSync(path.join(root, p)))]);
    }
  }
  Object.values(roots).sort().forEach(root => visit(root)); return rows;
}
test('OFF01 preflight uses only read-only local Git, no network or writes; Git bytes remain unchanged', t => {
  const x = fixture(t), before = snapshot(x.roots), calls = [], saved = [];
  const originalSpawn = cp.spawnSync;
  function replace(object, key, value) { saved.push([object, key, object[key]]); object[key] = value; }
  replace(cp, 'spawnSync', (cmd, args, options) => {
    assert.equal(cmd, 'git'); assert.equal(options.shell, false);
    const at = args.indexOf('core.fsmonitor=false') + 1;
    assert.ok(['rev-parse', 'config', 'cat-file', 'ls-tree', 'ls-files', 'merge-base'].includes(args[at]));
    assert.ok(!args.includes('fetch') && !args.includes('pull') && !args.includes('clone'));
    assert.equal(options.env.GIT_NO_LAZY_FETCH, '1'); assert.equal(options.env.GIT_OPTIONAL_LOCKS, '0');
    assert.ok(!('GIT_DIR' in options.env) && !('GIT_CONFIG_COUNT' in options.env));
    calls.push(args[at]); return originalSpawn(cmd, args, options);
  });
  const forbidden = () => { throw new Error('forbidden capability'); };
  for (const [obj, names] of [[cfs, ['writeFileSync', 'appendFileSync', 'renameSync', 'unlinkSync', 'mkdirSync']],
    [net, ['connect', 'createConnection']], [http, ['request', 'get']], [https, ['request', 'get']],
    [cp, ['exec', 'execSync', 'execFile', 'execFileSync', 'spawn', 'fork']]]) {
    for (const name of names) replace(obj, name, forbidden);
  }
  replace(globalThis, 'fetch', forbidden); syncBuiltinESMExports();
  let r;
  try { r = verifySources({manifest: x.manifest, roots: x.roots}); }
  finally { for (const [obj, key, value] of saved.reverse()) obj[key] = value; syncBuiltinESMExports(); }
  assert.equal(r.status, 'SOURCE_INTEGRITY_VERIFIED'); assert.ok(calls.length > 0);
  assert.deepEqual(snapshot(x.roots), before);
});
test('OFF01 inherited Git selector/config variables cannot redirect inspection', t => {
  const x = fixture(t), saved = {};
  const injected = {GIT_DIR: '/absent/forged', GIT_WORK_TREE: '/absent', GIT_CONFIG_COUNT: '1',
    GIT_CONFIG_KEY_0: 'remote.origin.url', GIT_CONFIG_VALUE_0: 'https://github.com/forged/repo.git'};
  for (const [k, v] of Object.entries(injected)) { saved[k] = process.env[k]; process.env[k] = v; }
  let r;
  try { r = verifySources({manifest: x.manifest, roots: x.roots}); }
  finally { for (const [k, v] of Object.entries(saved)) { if (v === undefined) delete process.env[k]; else process.env[k] = v; } }
  assert.equal(r.status, 'SOURCE_INTEGRITY_VERIFIED');
});
test('OFF01 manifest and arguments are not mutated by verification', t => {
  const x = fixture(t), before = structuredClone(x.manifest), roots = {...x.roots};
  verifySources({manifest: x.manifest, roots: x.roots});
  assert.deepEqual(x.manifest, before); assert.deepEqual(x.roots, roots);
});
test('OFF01 strict CLI returns JSON and exit 0 for integrity only', t => {
  const x = fixture(t), name = path.join(x.base, 'manifest.json'); fs.writeFileSync(name, JSON.stringify(x.manifest));
  const args = Object.entries(x.roots).flatMap(([id, root]) => ['--source', `${id}=${root}`]);
  const r = spawnSync(process.execPath, [cli, '--manifest', name, ...args], {encoding: 'utf8'});
  assert.equal(r.status, 0, r.stderr); assert.equal(JSON.parse(r.stdout).status, 'SOURCE_INTEGRITY_VERIFIED');
});
test('OFF01 CLI returns typed failure and exit 2 for A38 dependency', t => {
  const x = fixture(t), name = path.join(x.base, 'manifest.json'); fs.writeFileSync(name, JSON.stringify(x.manifest));
  const args = Object.entries(x.roots).flatMap(([id, root]) => ['--source', `${id}=${root}`]);
  const r = spawnSync(process.execPath, [cli, '--manifest', name, '--operation', 'a38', ...args], {encoding: 'utf8'});
  assert.equal(r.status, 2); assert.equal(JSON.parse(r.stdout).errors.at(-1).code, 'HISTORICAL_SOURCE_UNRECOVERED');
});
test('OFF01 CLI unknown flags and duplicate source roots are refused', () => {
  assert.throws(() => parseArguments(['--fetch', 'yes']), {code: 'INVALID_OPTIONS'});
  assert.throws(() => parseArguments(['--source', 's2=/tmp/a', '--source', 's2=/tmp/b']), {code: 'INVALID_OPTIONS'});
  assert.throws(() => parseArguments(['--source']), {code: 'INVALID_OPTIONS'});
});
test('OFF01 manifest file symlink is refused', t => {
  const x = fixture(t), file = path.join(x.base, 'manifest.json'), link = path.join(x.base, 'manifest-link.json');
  fs.writeFileSync(file, JSON.stringify(x.manifest)); fs.symlinkSync(file, link);
  assert.throws(() => readManifest(link), {code: 'SYMLINK_OR_ESCAPE'});
});
test('OFF01 invalid UTF-8 manifest bytes are rejected rather than normalized', t => {
  const x = fixture(t), filename = path.join(x.base, 'invalid.json');
  fs.writeFileSync(filename, Buffer.concat([Buffer.from('{"reason":"'), Buffer.from([0xff]), Buffer.from('"}')]));
  assert.throws(() => readManifest(filename), {code: 'INVALID_MANIFEST'});
});
test('OFF01 observable source mutation during reading cannot return integrity success', t => {
  const x = fixture(t), original = cfs.readSync;
  const filename = path.join(x.roots.s2, 'docs/shared.txt');
  cfs.readSync = (...args) => {
    const n = original(...args);
    if (fs.readlinkSync(`/proc/self/fd/${args[0]}`) === filename) fs.appendFileSync(filename, 'changed during read');
    return n;
  };
  syncBuiltinESMExports();
  try { fails(x, 'SOURCE_CHANGED'); }
  finally { cfs.readSync = original; syncBuiltinESMExports(); }
});
test('OFF01 checked-in public manifest pins the four authorized sources and unavailable history', () => {
  const m = readManifest(fileURLToPath(new URL('../source-manifest.json', import.meta.url)));
  assert.deepEqual(Object.fromEntries(m.sources.map(s => [s.id, s.commit])), {
    s2: '1747cb0fee2a95322dc768044bafe9817d8cc540',
    f03: 'dc8554db2e625accbf95cf922fdff8446be56f00',
    s0: '7d3232f59aab35265c3aa7fb5ab5ab2f06d5d047',
    i86: 'a0c4eaf2720bd6cf2bd756544498f8f185f005fc',
  });
  assert.equal(m.sources.reduce((n, s) => n + s.files.length, 0), 60);
  assert.equal(m.comparisons.length, 12);
  assert.equal(m.historical[0].commit, historical);
  assert.equal(m.historical[0].replacement, null);
});
