/**
 * OFFLINE CI policy canary: flag new runtime references to the WA-01B
 * shape-only ACK helper. No code alteration, network or production effect.
 *
 * This is a conservative source-text heuristic, NOT a whole-program proof.
 * It strips comments before looking for identifiers to avoid false alerts
 * on explanatory notes in historical fake transaction harnesses. Dynamic
 * imports/string-computed uses and deployed artifacts still need review.
 */
import {execFileSync} from 'node:child_process';
import {readFileSync} from 'node:fs';

const token='decide'+'BatchAck';
const identifier=new RegExp('\\b'+token+'\\b');
const script='integrations/whatsapp-meta/cloud-ack-runtime-guard.mjs';
const allowedDefinition='integrations/whatsapp-meta/durable-receipt.ts';
const isCode=(path)=>/\.(?:ts|tsx|js|jsx|mjs|cjs|py)$/.test(path);
const isTest=(path)=>/\.(?:test|spec)\.(?:ts|tsx|js|jsx|mjs|cjs|py)$/.test(path);
const stripComments=(s)=>
 s.replace(/\/\*[\s\S]*?\*\//g,'')
  .replace(/^[ \t]*\/\/[^\r\n]*$/gm,'')
  .replace(/[ \t]+\/\/[^\r\n]*$/gm,'')
  .replace(/^[ \t]*#[^\r\n]*$/gm,'');

const files=execFileSync('git',['ls-files','-z'],{encoding:'utf8'})
 .split('\0').filter(Boolean);
const failures=[];
for(const file of files){
 if(!isCode(file)||isTest(file)||file===allowedDefinition||file===script)
  continue;
 const content=readFileSync(file,'utf8');
 if(identifier.test(stripComments(content)))failures.push(file);
}
if(failures.length){
 for(const f of failures)process.stderr.write(
  'Unreviewed runtime reference to legacy shape-only ACK: '+f+'\n');
 process.exitCode=1;
}else{
 process.stdout.write(
  'PASS: no direct legacy ACK helper identifier in tracked runtime sources ('+
  files.length+' tracked files inspected; comment-only references ignored)\n');
}
