// OFF-01: local selected-source integrity only. Never executes source modules.
import * as fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

export const MANIFEST_VERSION = 'prumo.openai.source-manifest/1.0';
const HISTORICAL_PIN = 'ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c';
const IDS = ['s2', 'f03', 's0', 'i86'];
const MAX_BYTES = 2 * 1024 * 1024;
const HEX40 = /^[0-9a-f]{40}$/;
const HEX64 = /^[0-9a-f]{64}$/;
const messages = {
  INVALID_MANIFEST: 'Manifesto incompleto ou malformado.',
  MANIFEST_VERSION_UNSUPPORTED: 'Versao de manifesto nao suportada.',
  UNEXPECTED_FIELD: 'Campo nao previsto no contrato de integridade.',
  UNSAFE_PATH: 'Caminho relativo inseguro ou fora do escopo.',
  INVALID_OPTIONS: 'Argumentos locais invalidos ou duplicados.',
  CHECKOUT_REQUIRED: 'Checkout obrigatorio nao informado.',
  CHECKOUT_ABSENT: 'Checkout local ausente.',
  SYMLINK_OR_ESCAPE: 'Symlink ou escape de diretorio recusado.',
  NOT_REGULAR_FILE: 'Somente arquivo regular de link unico e permitido.',
  CHECKOUT_ROOT_MISMATCH: 'A raiz fornecida deve ser a raiz real do checkout.',
  REPOSITORY_UNOBSERVABLE: 'Origem local nao observavel; integridade nao atestada.',
  REPOSITORY_MISMATCH: 'Origem local difere do repositorio declarado.',
  PARTIAL_CLONE_UNSUPPORTED: 'Repositorio promisor ou parcial nao e aceito offline.',
  COMMIT_MISMATCH: 'HEAD difere do commit fixado.',
  TREE_MISMATCH: 'Arvore difere da referencia fixada.',
  GIT_OBJECT_MISMATCH: 'Objeto Git difere do identificador esperado.',
  GIT_INSPECTION_FAILED: 'Inspecao Git local falhou; sem tentativa de recuperacao.',
  FILE_MISSING: 'Arquivo selecionado ausente.',
  INDEX_MISMATCH: 'Indice do arquivo difere do commit fixado.',
  BLOB_MISMATCH: 'Blob Git diverge do manifesto ou da arvore.',
  HASH_MISMATCH: 'SHA-256 dos bytes diverge do manifesto.',
  CONTENT_MISMATCH: 'Bytes locais diferem do blob fixado.',
  MODE_MISMATCH: 'Modo Git ou executabilidade local divergente.',
  SOURCE_CHANGED: 'Mudanca observavel durante a inspecao.',
  COMPARISON_MISMATCH: 'Relacao de bytes declarada nao foi comprovada.',
  ANCESTRY_MISMATCH: 'Ancestralidade declarada nao foi comprovada.',
  HISTORICAL_SUBSTITUTION_FORBIDDEN: 'Referencia historica nao pode ser substituida por esta verificacao.',
  HISTORICAL_SOURCE_UNRECOVERED: 'A38 bloqueada: fonte historica exata nao recuperada; nenhum teste A38 executado.',
};

export class SourcePreflightError extends Error {
  constructor(code, source = undefined, relativePath = undefined) {
    super(messages[code]);
    this.name = 'SourcePreflightError';
    this.code = code;
    if (source !== undefined) this.source = source;
    if (relativePath !== undefined) this.path = relativePath;
  }
}
const reject = (code, source, relativePath) => { throw new SourcePreflightError(code, source, relativePath); };
const record = x => x !== null && typeof x === 'object' && !Array.isArray(x);
function exact(x, keys) {
  if (!record(x)) reject('INVALID_MANIFEST');
  if (Object.keys(x).some(k => !keys.includes(k))) reject('UNEXPECTED_FIELD');
  if (keys.some(k => !Object.hasOwn(x, k))) reject('INVALID_MANIFEST');
}
function safePath(value) {
  if (typeof value !== 'string' || value.length > 512 ||
      !value.split('/').every(p => /^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$/.test(p)) ||
      value.split('/').length > 12) reject('UNSAFE_PATH');
  return value;
}
function repository(value) {
  if (typeof value !== 'string' || !/^[A-Za-z0-9_-]+\/[A-Za-z0-9_.-]+$/.test(value)) reject('INVALID_MANIFEST');
}
function endpoint(x, sources) {
  exact(x, ['source', 'path']); safePath(x.path);
  const source = sources.find(s => s.id === x.source);
  if (!source || !source.files.some(f => f.path === x.path)) reject('INVALID_MANIFEST');
}

export function validateManifest(input) {
  // Copy JSON data so the inspection never mutates the caller's manifest.
  let m;
  try { m = structuredClone(input); } catch { reject('INVALID_MANIFEST'); }
  exact(m, ['schema', 'purpose', 'object_format', 'sources', 'comparisons', 'ancestry', 'historical']);
  if (m.schema !== MANIFEST_VERSION) reject('MANIFEST_VERSION_UNSUPPORTED');
  if (m.purpose !== 'OFFLINE_SOURCE_INTEGRITY_ONLY' || m.object_format !== 'sha1') reject('INVALID_MANIFEST');
  if (!Array.isArray(m.sources) || m.sources.length !== IDS.length) reject('INVALID_MANIFEST');
  const seen = new Set();
  for (const s of m.sources) {
    exact(s, ['id', 'repository', 'reference_branch', 'commit', 'tree', 'requirement', 'files']);
    if (!IDS.includes(s.id) || seen.has(s.id)) reject('INVALID_MANIFEST');
    seen.add(s.id); repository(s.repository);
    if (typeof s.commit !== 'string' || typeof s.tree !== 'string' || !HEX40.test(s.commit) || !HEX40.test(s.tree) ||
        typeof s.reference_branch !== 'string' || !/^[A-Za-z0-9_./-]{1,160}$/.test(s.reference_branch) ||
        s.requirement !== (['s2', 'f03'].includes(s.id) ? 'required' : 'optional') ||
        !Array.isArray(s.files) || !s.files.length || s.files.length > 128) reject('INVALID_MANIFEST');
    const files = new Set();
    for (const f of s.files) {
      exact(f, ['path', 'mode', 'byte_length', 'sha256', 'git_blob']); safePath(f.path);
      if (files.has(f.path) || !['100644', '100755'].includes(f.mode) ||
          !Number.isSafeInteger(f.byte_length) || f.byte_length < 0 || f.byte_length > MAX_BYTES ||
          typeof f.sha256 !== 'string' || !HEX64.test(f.sha256) ||
          typeof f.git_blob !== 'string' || !HEX40.test(f.git_blob)) reject('INVALID_MANIFEST');
      files.add(f.path);
    }
  }
  for (const group of ['comparisons', 'ancestry']) {
    if (!Array.isArray(m[group]) || m[group].length > 128) reject('INVALID_MANIFEST');
    const names = new Set();
    for (const c of m[group]) {
      exact(c, group === 'comparisons' ? ['id', 'left', 'right', 'expected'] : ['id', 'ancestor', 'descendant']);
      if (typeof c.id !== 'string' || !/^[a-z0-9_-]{1,100}$/.test(c.id) || names.has(c.id)) reject('INVALID_MANIFEST');
      names.add(c.id);
      if (group === 'comparisons') {
        endpoint(c.left, m.sources); endpoint(c.right, m.sources);
        if (!['IDENTICAL_BYTES', 'DIFFERENT_BYTES'].includes(c.expected)) reject('INVALID_MANIFEST');
      } else if (!IDS.includes(c.ancestor) || !IDS.includes(c.descendant) || c.ancestor === c.descendant) reject('INVALID_MANIFEST');
    }
  }
  if (!Array.isArray(m.historical) || m.historical.length !== 1) reject('INVALID_MANIFEST');
  const h = m.historical[0];
  exact(h, ['id', 'repository', 'commit', 'documentary_origin', 'recovery', 'required_for', 'replacement', 'reason']);
  repository(h.repository);
  if (h.id !== 's2-a38-history' || h.commit !== HISTORICAL_PIN ||
      h.recovery !== 'NOT_RECOVERED_IN_OAI_RET_01' || h.replacement !== null ||
      !Array.isArray(h.required_for) || h.required_for.length !== 1 || h.required_for[0] !== 'a38')
    reject('HISTORICAL_SUBSTITUTION_FORBIDDEN');
  if (h.repository !== m.sources.find(s => s.id === 's2').repository ||
      typeof h.reason !== 'string' || h.reason.length < 1 || h.reason.length > 512 ||
      !Array.isArray(h.documentary_origin) || !h.documentary_origin.length || h.documentary_origin.length > 8) reject('INVALID_MANIFEST');
  for (const ref of h.documentary_origin) endpoint(ref, m.sources);
  return m;
}

// JSON.parse checks grammar; this second pass refuses duplicate decoded keys.
export function parseManifest(text) {
  if (typeof text !== 'string' || Buffer.byteLength(text) > MAX_BYTES) reject('INVALID_MANIFEST');
  let m;
  try { m = JSON.parse(text); } catch { reject('INVALID_MANIFEST'); }
  const stack = [];
  const tokens = /"(?:\\.|[^"\\])*"|[{}\[\]]/g;
  for (const token of text.matchAll(tokens)) {
    const value = token[0];
    if (value === '{' || value === '[') {
      stack.push(value === '{' ? new Set() : null);
      if (stack.length > 16) reject('INVALID_MANIFEST');
    } else if (value === '}' || value === ']') stack.pop();
    else if (/^\s*:/.test(text.slice(token.index + value.length))) {
      const key = JSON.parse(value), keys = stack.at(-1);
      if (!(keys instanceof Set) || keys.has(key)) reject('INVALID_MANIFEST');
      keys.add(key);
    }
  }
  return validateManifest(m);
}

function noSymlink(candidate, source, missingCode) {
  const resolved = path.resolve(candidate);
  let at = path.parse(resolved).root;
  for (const segment of resolved.slice(at.length).split(path.sep).filter(Boolean)) {
    at = path.join(at, segment);
    let stat;
    try { stat = fs.lstatSync(at); } catch { reject(missingCode, source); }
    if (stat.isSymbolicLink()) reject('SYMLINK_OR_ESCAPE', source);
  }
  if (fs.realpathSync(resolved) !== resolved) reject('SYMLINK_OR_ESCAPE', source);
  return resolved;
}
function bytes(root, relativePath, source) {
  const full = noSymlink(path.join(root, relativePath), source, 'FILE_MISSING');
  if (!full.startsWith(root + path.sep)) reject('SYMLINK_OR_ESCAPE', source, relativePath);
  const before = fs.lstatSync(full);
  if (!before.isFile() || before.nlink !== 1 || before.size > MAX_BYTES) reject('NOT_REGULAR_FILE', source, relativePath);
  let fd;
  try {
    fd = fs.openSync(full, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
    const opened = fs.fstatSync(fd);
    if (!opened.isFile() || opened.ino !== before.ino || opened.dev !== before.dev) reject('SOURCE_CHANGED', source, relativePath);
    const data = Buffer.alloc(opened.size + 1);
    const length = fs.readSync(fd, data, 0, data.length, 0);
    const after = fs.fstatSync(fd);
    if (length !== opened.size || after.size !== opened.size || after.mtimeMs !== opened.mtimeMs ||
        after.ctimeMs !== opened.ctimeMs || fs.realpathSync(full) !== full) reject('SOURCE_CHANGED', source, relativePath);
    return {data: data.subarray(0, length), mode: before.mode};
  } finally { if (fd !== undefined) fs.closeSync(fd); }
}
export function readManifest(filename) {
  if (typeof filename !== 'string') reject('INVALID_MANIFEST');
  const full = noSymlink(filename, undefined, 'INVALID_MANIFEST');
  let text;
  try { text = new TextDecoder('utf-8', {fatal: true}).decode(bytes(path.dirname(full), path.basename(full)).data); }
  catch (e) { if (e instanceof SourcePreflightError) throw e; reject('INVALID_MANIFEST'); }
  return parseManifest(text);
}

function git(root, args, source, allowed = [0]) {
  // No inherited Git selectors, injected config, lazy fetching or optional locks.
  const run = spawnSync('git', ['--no-pager', '--no-optional-locks', '--no-replace-objects',
    '--literal-pathspecs', '-c', 'core.fsmonitor=false', ...args], {
    cwd: root, shell: false, timeout: 5000, maxBuffer: MAX_BYTES * 2,
    env: {PATH: process.env.PATH || '/usr/bin:/bin', LC_ALL: 'C',
      GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_SYSTEM: '/dev/null', GIT_CONFIG_GLOBAL: '/dev/null',
      GIT_OPTIONAL_LOCKS: '0', GIT_NO_REPLACE_OBJECTS: '1', GIT_NO_LAZY_FETCH: '1', GIT_TERMINAL_PROMPT: '0'},
  });
  if (run.error || run.signal || !allowed.includes(run.status)) reject('GIT_INSPECTION_FAILED', source);
  return {data: run.stdout, status: run.status};
}
const digest = (algorithm, data) => createHash(algorithm).update(data).digest('hex');
function objectId(kind, data) {
  return digest('sha1', Buffer.concat([Buffer.from(`${kind} ${data.length}\0`), data]));
}
function originRepository(url) {
  const match = /^(?:https:\/\/github\.com\/|git@github\.com:|ssh:\/\/git@github\.com\/)([A-Za-z0-9_-]+\/[A-Za-z0-9_.-]+?)(?:\.git)?\/?$/.exec(url);
  return match ? match[1].toLowerCase() : null;
}
function inspectSource(s, suppliedRoot) {
  const root = noSymlink(suppliedRoot, s.id, 'CHECKOUT_ABSENT');
  const call = (args, allowed) => git(root, args, s.id, allowed);
  const text = args => call(args).data.toString('utf8').trim();
  if (text(['rev-parse', '--show-toplevel']) !== root) reject('CHECKOUT_ROOT_MISMATCH', s.id);
  // Reject partial/promisor clones before any object read could trigger hydration.
  const partial = call(['config', '--no-includes', '--get-regexp',
    '^(extensions\.partialclone|remote\..*\.promisor)$'], [0, 1]);
  if (partial.status === 0) reject('PARTIAL_CLONE_UNSUPPORTED', s.id);
  const origin = call(['config', '--no-includes', '--get', 'remote.origin.url'], [0, 1]);
  if (origin.status !== 0) reject('REPOSITORY_UNOBSERVABLE', s.id);
  if (originRepository(origin.data.toString('utf8').trim()) !== s.repository.toLowerCase()) reject('REPOSITORY_MISMATCH', s.id);
  if (text(['rev-parse', '--show-object-format']) !== 'sha1') reject('GIT_OBJECT_MISMATCH', s.id);
  if (text(['rev-parse', 'HEAD']) !== s.commit) reject('COMMIT_MISMATCH', s.id);
  const commit = call(['cat-file', 'commit', s.commit]).data;
  if (objectId('commit', commit) !== s.commit) reject('GIT_OBJECT_MISMATCH', s.id);
  const tree = /^tree ([0-9a-f]{40})\n/.exec(commit.toString('utf8'))?.[1];
  if (tree !== s.tree) reject('TREE_MISMATCH', s.id);
  if (objectId('tree', call(['cat-file', 'tree', tree]).data) !== tree) reject('GIT_OBJECT_MISMATCH', s.id);
  const contents = new Map();
  for (const f of [...s.files].sort((a, b) => a.path < b.path ? -1 : 1)) {
    const entry = call(['ls-tree', '-z', s.commit, '--', f.path]).data.toString('utf8');
    const parsed = /^([0-7]{6}) blob ([0-9a-f]{40})\t([^\0]+)\0$/.exec(entry);
    if (!parsed || parsed[3] !== f.path) reject('FILE_MISSING', s.id, f.path);
    if (parsed[1] !== f.mode) reject('MODE_MISMATCH', s.id, f.path);
    if (parsed[2] !== f.git_blob) reject('BLOB_MISMATCH', s.id, f.path);
    const blob = call(['cat-file', 'blob', f.git_blob]).data;
    if (objectId('blob', blob) !== f.git_blob) reject('BLOB_MISMATCH', s.id, f.path);
    if (digest('sha256', blob) !== f.sha256 || blob.length !== f.byte_length) reject('HASH_MISMATCH', s.id, f.path);
    const index = call(['ls-files', '--stage', '-z', '--', f.path]).data.toString('utf8');
    if (index !== `${f.mode} ${f.git_blob} 0\t${f.path}\0`) reject('INDEX_MISMATCH', s.id, f.path);
    const local = bytes(root, f.path, s.id);
    if (!local.data.equals(blob)) reject('CONTENT_MISMATCH', s.id, f.path);
    if ((local.mode & 0o111 ? '100755' : '100644') !== f.mode) reject('MODE_MISMATCH', s.id, f.path);
    contents.set(f.path, local.data);
  }
  if (text(['rev-parse', 'HEAD']) !== s.commit) reject('SOURCE_CHANGED', s.id);
  return {root, contents};
}

function errorView(error) {
  const e = error instanceof SourcePreflightError ? error : new SourcePreflightError('GIT_INSPECTION_FAILED');
  return {code: e.code, message: e.message, ...(e.source ? {source: e.source} : {}), ...(e.path ? {path: e.path} : {})};
}
const assurance = () => ({integration_homologated: false, s0_authorized: false,
  semantic_validation: false, e02_homologated: false, a38_recovered: false});

export function verifySources(options) {
  const result = {status: 'SOURCE_INTEGRITY_REJECTED', sources: [], comparisons: [], ancestry: [],
    historical: [], operations: [], assurance: assurance(), errors: []};
  try {
    if (!record(options) || Object.keys(options).some(k => !['manifest', 'roots', 'requireSources', 'operation'].includes(k))) reject('INVALID_OPTIONS');
    const m = validateManifest(options.manifest), roots = options.roots;
    const required = options.requireSources ?? [], operation = options.operation ?? 'sources';
    if (!record(roots) || Object.keys(roots).some(k => !IDS.includes(k)) ||
        Object.values(roots).some(v => typeof v !== 'string' || !path.isAbsolute(v) || v.includes('\0')) ||
        !Array.isArray(required) || required.some(id => !IDS.includes(id)) ||
        new Set(required).size !== required.length || !['sources', 'a38'].includes(operation)) reject('INVALID_OPTIONS');
    result.historical = m.historical.map(h => ({id: h.id, commit: h.commit, state: h.recovery, required_for: [...h.required_for]}));
    result.operations = [{id: 'a38', state: 'BLOCKED_HISTORICAL_SOURCE_UNRECOVERED', tests_executed: false}];
    const inspected = new Map();
    for (const s of [...m.sources].sort((a, b) => a.id < b.id ? -1 : 1)) {
      if (!Object.hasOwn(roots, s.id)) {
        if (s.requirement === 'required' || required.includes(s.id)) {
          result.errors.push(errorView(new SourcePreflightError('CHECKOUT_REQUIRED', s.id)));
          result.sources.push({id: s.id, state: 'REQUIRED_NOT_PROVIDED'});
        } else result.sources.push({id: s.id, state: 'OPTIONAL_NOT_PROVIDED'});
        continue;
      }
      try {
        inspected.set(s.id, inspectSource(s, roots[s.id]));
        result.sources.push({id: s.id, state: 'SOURCE_INTEGRITY_VERIFIED', commit: s.commit, tree: s.tree, files_verified: s.files.length});
      } catch (e) {
        result.errors.push(errorView(e)); result.sources.push({id: s.id, state: 'REJECTED'});
      }
    }
    for (const c of [...m.comparisons].sort((a, b) => a.id < b.id ? -1 : 1)) {
      const left = inspected.get(c.left.source), right = inspected.get(c.right.source);
      if (!left || !right) { result.comparisons.push({id: c.id, state: 'NOT_EVALUATED_SOURCE_NOT_VERIFIED'}); continue; }
      const actual = left.contents.get(c.left.path).equals(right.contents.get(c.right.path)) ? 'IDENTICAL_BYTES' : 'DIFFERENT_BYTES';
      result.comparisons.push({id: c.id, state: actual});
      if (actual !== c.expected) result.errors.push(errorView(new SourcePreflightError('COMPARISON_MISMATCH')));
    }
    for (const c of [...m.ancestry].sort((a, b) => a.id < b.id ? -1 : 1)) {
      if (!inspected.has(c.ancestor) || !inspected.has(c.descendant)) {
        result.ancestry.push({id: c.id, state: 'NOT_EVALUATED_SOURCE_NOT_VERIFIED'}); continue;
      }
      const a = m.sources.find(s => s.id === c.ancestor), b = m.sources.find(s => s.id === c.descendant);
      const check = git(inspected.get(c.descendant).root, ['merge-base', '--is-ancestor', a.commit, b.commit], c.descendant, [0, 1]);
      result.ancestry.push({id: c.id, state: check.status === 0 ? 'ANCESTRY_VERIFIED' : 'ANCESTRY_MISMATCH'});
      if (check.status !== 0) result.errors.push(errorView(new SourcePreflightError('ANCESTRY_MISMATCH')));
    }
    if (operation === 'a38') result.errors.push(errorView(new SourcePreflightError('HISTORICAL_SOURCE_UNRECOVERED')));
    if (!result.errors.length) result.status = 'SOURCE_INTEGRITY_VERIFIED';
  } catch (e) { result.errors.push(errorView(e)); }
  return result;
}

export function parseArguments(args) {
  const options = {roots: {}, requireSources: [], operation: 'sources'};
  const singleton = new Set();
  for (let i = 0; i < args.length; i += 2) {
    const flag = args[i], value = args[i + 1];
    if (typeof value !== 'string' || !value.length) reject('INVALID_OPTIONS');
    if (flag === '--source') {
      const match = /^(s2|f03|s0|i86)=(.+)$/.exec(value);
      if (!match || Object.hasOwn(options.roots, match[1])) reject('INVALID_OPTIONS');
      options.roots[match[1]] = match[2];
    } else if (flag === '--require') {
      if (!IDS.includes(value) || options.requireSources.includes(value)) reject('INVALID_OPTIONS');
      options.requireSources.push(value);
    } else if (['--manifest', '--operation'].includes(flag) && !singleton.has(flag)) {
      singleton.add(flag); options[flag === '--manifest' ? 'manifestPath' : 'operation'] = value;
    } else reject('INVALID_OPTIONS');
  }
  return options;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  let result;
  try {
    const {manifestPath, ...options} = parseArguments(process.argv.slice(2));
    const filename = manifestPath ?? fileURLToPath(new URL('./source-manifest.json', import.meta.url));
    result = verifySources({...options, manifest: readManifest(filename)});
  } catch (e) { result = {status: 'SOURCE_INTEGRITY_REJECTED', assurance: assurance(), errors: [errorView(e)]}; }
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
  process.exitCode = result.status === 'SOURCE_INTEGRITY_VERIFIED' ? 0 : 2;
}
