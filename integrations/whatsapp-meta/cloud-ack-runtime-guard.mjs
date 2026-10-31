/**
 * Meta CI ACK canary — conservative source guard, NOT a program proof.
 * Prevents direct runtime use of the historical WA-01B helper, HTTP200
 * literals and positive authority flags before S0/Infra ratification.
 *
 * The old helper itself is fail-closed. Runtime HTTP transports are NOT
 * authorized by this scanner, tests, or a signed laboratory receipt.
 * Computed/dynamic aliases and built artifacts still require separate review.
 */
import {execFileSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const legacyIdentifier='decide'+'BatchAck';
const identifier=new RegExp('\\b'+legacyIdentifier+'\\b');
const script='integrations/whatsapp-meta/cloud-ack-runtime-guard.mjs';
const definition='integrations/whatsapp-meta/durable-receipt.ts';
const isCode=(p)=>/\.(?:ts|tsx|js|jsx|mjs|cjs|py)$/.test(p);
const isTest=(p)=>/\.(?:test|spec)\.(?:ts|tsx|js|jsx|mjs|cjs|py)$/.test(p);
const stripComments=(s)=>
 s.replace(/\/\*[\s\S]*?\*\//g,'')
  .replace(/^[ \t]*\/\/[^\r\n]*$/gm,'')
  .replace(/[ \t]+\/\/[^\r\n]*$/gm,'')
  .replace(/^[ \t]*#[^\r\n]*$/gm,'');

// Do not mistake provider status observations for an HTTP reply. These
// forbidden forms are deliberately narrow and limited to the Meta tree.
// http_status is the observed provider Graph HTTP result, not webhook ACK.
const statusLiteral=/\b(?:status|statusCode|httpStatus)\s*[:=]\s*(?:200|2e2|0xc8)\b/i;
const statusCall=/\b(?:sendStatus|writeHead|status)\s*\(\s*(?:200|2e2|0xc8)\s*[,)]/i;
const ackAction=/\baction\s*:\s*['"]ACK['"]/;
const positiveAuthority=/\b(?:ack_allowed|http_ack_allowed|http_response_authorized)\s*[:=]\s*true\b/;

// Only the two reviewed challenge shapes are exempt; other code in the
// same GET module remains subject to this conservative canary.
const getType=/readonly status:\s*200\s*;/g;
const getSuccess=/return matches\s*\?\s*\{\s*status:\s*200,\s*body:\s*challenge,\s*headers\s*\}\s*:\s*forbidden\(\)\s*;/g;
function suppressReviewedGet200(path,source){
 if(path!=='integrations/whatsapp-meta/verify-get.ts')return source;
 return source.replace(getType,'readonly status: VERIFIED_GET_CHALLENGE;')
  .replace(getSuccess,'return VERIFIED_GET_CHALLENGE_ONLY;');
}

/** No file IO: testable source-text inspection, conservative and fail-closed. */
export function scanRuntimeAckSource(path,source){
 if(typeof path!=='string'||typeof source!=='string')throw Error('INVALID_SCAN_INPUT');
 if(!isCode(path)||isTest(path)||path===script)return [];
 const code=suppressReviewedGet200(path,stripComments(source));
 const findings=[];
 if(path!==definition&&identifier.test(code))
  findings.push('LEGACY_SHAPE_ONLY_HELPER_REFERENCE');
 if(path.startsWith('integrations/whatsapp-meta/')){
  if(statusLiteral.test(code)||statusCall.test(code))
   findings.push('UNRATIFIED_HTTP_200_LITERAL');
  if(ackAction.test(code))findings.push('UNRATIFIED_ACK_ACTION');
  if(positiveAuthority.test(code))findings.push('UNRATIFIED_ACK_AUTHORITY_FLAG');
 }
 return findings;
}

/** Run only if directly invoked, never when imported by negative tests. */
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const files=execFileSync('git',['ls-files','-z'],{encoding:'utf8'})
  .split('\0').filter(Boolean);
 let violations=0;
 for(const path of files){
  if(!isCode(path)||isTest(path)||path===script)continue;
  let findings;
  try{findings=scanRuntimeAckSource(path,readFileSync(path,'utf8'));}
  catch(error){
   process.stderr.write('ACK_SCAN_FAILED '+path+' '+String(error)+'\n');
   violations++;continue;
  }
  for(const reason of findings){
   process.stderr.write('UNRATIFIED_META_ACK '+reason+' '+path+'\n');
   violations++;
  }
 }
 if(violations)process.exitCode=1;
 else process.stdout.write('PASS: no direct unratified ACK/HTTP200 authority in '+files.length+' tracked sources (static canary only)\n');
}
