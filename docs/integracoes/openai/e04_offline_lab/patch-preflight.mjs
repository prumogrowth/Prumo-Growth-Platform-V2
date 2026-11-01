// OFF-06: local candidate gate. Verifies the exact OFF-01 parent, preserves
// inherited source files, checks candidate byte digests and runs ALL Node tests.
// Zero SDK/API/SQL/Meta calls; never writes to Git or a production system.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';

const here=path.dirname(fileURLToPath(import.meta.url));
const repo=path.resolve(here, '../../../..');
const manifestFile=path.join(here,'patch-files.sha256.json');
const OFF01='394512327cd3756dfbe61ff970a6279c354b6565';
const OFF01_TREE='87a3ce85b2ead682038d4bee104ca47dd006c971';
const EXPECTED_MIN=678; // 342 inherited historically reported + 336 new (63/101/71/101). Target only: inherited suite still requires actual rerun.
function run(cmd,args){
  const p=spawnSync(cmd,args,{cwd:repo,encoding:'utf8',timeout:180000,maxBuffer:12*1024*1024,env:{...process.env,CI:'1'}});
  if(p.error)return {code:2,stdout:'',stderr:p.error.code||'SPAWN_ERROR'};
  return {code:p.status??2,stdout:p.stdout||'',stderr:p.stderr||''};
}
function fatal(code,info={}){
  console.log(JSON.stringify({status:'BLOCKED',code, ...info},null,2));process.exitCode=2;
}
function validEntry(p){
  return typeof p==='string' && p.startsWith('docs/integracoes/openai/') &&
    /^[A-Za-z0-9_./-]+$/.test(p) && !p.includes('/../') && !p.includes('/./') &&
    !p.startsWith('/') && !p.endsWith('/') && !p.includes('//') && path.posix.normalize(p)===p;
}
function checkSafePath(file){
  const relative=path.relative(repo,file);
  if(relative.startsWith('..') || path.isAbsolute(relative))throw Error('TRAVERSAL');
  let parent=repo;
  for(const part of relative.split(path.sep).slice(0,-1)){
    parent=path.join(parent,part);
    const d=fs.lstatSync(parent);
    if(!d.isDirectory()||d.isSymbolicLink())throw Error('PARENT_LINK_OR_NOT_DIRECTORY');
  }
  const f=fs.lstatSync(file);
  if(!f.isFile()||f.isSymbolicLink()||f.nlink!==1||f.size>1024*1024)throw Error('FILE_INVALID');
  return f;
}
function verifyPatch(){
  checkSafePath(manifestFile);
  const doc=JSON.parse(fs.readFileSync(manifestFile,'utf8'));
  if(doc.schema!=='prumo.openai.offline-patch-manifest/0.1-candidate'||
     doc.base_commit!==OFF01||doc.base_tree!==OFF01_TREE||
     doc.expected_full_tests!==EXPECTED_MIN||
     !Array.isArray(doc.files)||doc.files.length!==27)throw Error('MANIFEST_INVALID');
  const names=new Set();
  for(const entry of doc.files){
    if(!entry || !validEntry(entry.path)||names.has(entry.path)||
       typeof entry.sha256!=='string'||!/^[0-9a-f]{64}$/.test(entry.sha256))throw Error('ENTRY_INVALID');
    names.add(entry.path);
    const p=path.resolve(repo,entry.path);
    if(!p.startsWith(repo+path.sep))throw Error('TRAVERSAL');
    checkSafePath(p);
    const hash=createHash('sha256').update(fs.readFileSync(p)).digest('hex');
    if(hash!==entry.sha256)throw Error('PATCH_BYTES_CHANGED:'+entry.path);
  }
  return names;
}
function runTests(names,gateMode) {
  if(!fs.existsSync(path.join(here,'source-preflight.mjs'))||
     !fs.existsSync(path.join(here,'tests','source-preflight.test.mjs')))
    return fatal('OFF01_SOURCE_MISSING');
  const test=run('npm',['--prefix','docs/integracoes/openai/e04_offline_lab','test']);
  const output=test.stdout+'\n'+test.stderr;
  const tests=Number(output.match(/# tests (\d+)/)?.[1]);
  const passed=Number(output.match(/# pass (\d+)/)?.[1]);
  const failures=Number(output.match(/# fail (\d+)/)?.[1]);
  const skip=Number(output.match(/# skipped (\d+)/)?.[1]??0);
  if(test.code!==0||tests!==EXPECTED_MIN||passed!==EXPECTED_MIN||failures!==0||skip!==0)
    return fatal('FULL_REGRESSION_NOT_PASSED',{exit:test.code,tests,passed,failures,skip,logTail:output.slice(-3500)});
  console.log(JSON.stringify({status:'LOCAL_GATE_PASS_NOT_OPERATIONAL_HOMOLOGATION',mode:gateMode,base:OFF01,baseTree:OFF01_TREE,patchFiles:names.size,tests,passed,failures,skip,productionAuthorized:false}));
}

try{
  const names=verifyPatch();
  const gitHead=run('git',['rev-parse','HEAD']);
  if(gitHead.code!==0){fatal('OFF01_CHECKOUT_REQUIRED',{patchFilesValidated:names.size});}
  else {
    const head=gitHead.stdout.trim();
    const candidate=head===OFF01;
    const parents=run('git',['rev-list','--parents','-n1','HEAD']);
    const parentParts=parents.stdout.trim().split(/\s+/);
    const committed=!candidate && parents.code===0 && parentParts.length===2 && parentParts[1]===OFF01;
    if(!candidate&&!committed)fatal('BASE_COMMIT_MISMATCH',{actual:head});
    else{
      const srcRef=committed?'HEAD^':'HEAD';
      const tree=run('git',['rev-parse',srcRef+'^{tree}']);
      if(tree.code!==0||tree.stdout.trim()!==OFF01_TREE)fatal('BASE_TREE_MISMATCH');
      else{
        const allowed=new Set([...names,'docs/integracoes/openai/e04_offline_lab/patch-files.sha256.json']);
        const tracked=run('git',['diff','--name-only','HEAD','--']);
        const staged=run('git',['diff','--cached','--name-only']);
        const untracked=run('git',['ls-files','--others','--exclude-standard']);
        const unstaged=(tracked.stdout.trim()+'\n'+staged.stdout.trim()).trim();
        if(tracked.code!==0||staged.code!==0||untracked.code!==0||unstaged)
          fatal('WORKTREE_CHANGED');
        else if(candidate){
          const set=new Set(untracked.stdout.trim().split('\n').filter(Boolean));
          const missing=[...allowed].filter(p=>!set.has(p));
          const extra=[...set].filter(p=>!allowed.has(p));
          if(missing.length||extra.length)fatal('PATCH_TREE_NOT_ISOLATED',{missing:missing.length,unexpected:extra.length});
          else runTests(names,'PRE_COMMIT_CANDIDATE');
        }else{
          const paths=run('git',['diff','--name-status','HEAD^','HEAD','--']);
          const entries=paths.stdout.trim().split('\n').filter(Boolean);
          const added=new Set(entries.filter(s=>s.startsWith('A\t')).map(s=>s.slice(2)));
          const invalid=entries.filter(s=>!s.startsWith('A\t'));
          const extra=[...added].filter(p=>!allowed.has(p));
          const missing=[...allowed].filter(p=>!added.has(p));
          if(paths.code!==0||invalid.length||extra.length||missing.length||untracked.stdout.trim())
            fatal('COMMIT_SCOPE_INVALID',{changed:entries.length,missing:missing.length,unexpected:extra.length,modified:invalid.length});
          else runTests(names,'POST_COMMIT_CANDIDATE');
        }
      }
    }
  }
}catch(e){fatal('GATE_EXCEPTION',{kind:e instanceof Error?e.message:'UNKNOWN'});}
