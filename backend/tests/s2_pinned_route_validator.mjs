// E04 synthetic route bridge: imports the EXACT S2 code checked out at pinned CI SHA.
// This CLI does not perform S0 verification, model generation, business actions or I/O
// beyond reading a single synthetic fixture from stdin and returning status labels.
import {validateF01,validateF02,prepareF03History,validateF03Proposal}
  from '../../.s2-e04-source/docs/integracoes/openai/e04_offline_lab/core.mjs';

let size=0;
const chunks=[];
for await (const chunk of process.stdin) {
  size+=chunk.length;
  if(size>65536) { process.stdout.write('{"error":"OVERSIZED"}'); process.exit(0); }
  chunks.push(chunk);
}
try {
  const obj=JSON.parse(Buffer.concat(chunks).toString('utf8'));
  if (!obj || typeof obj!=='object'||Array.isArray(obj)||
      Object.keys(obj).sort().join(',')!=='steps'||
      !Array.isArray(obj.steps)||obj.steps.length>64||obj.steps.length<1)
    throw new Error('INVALID_SHAPE');
  const results=[];
  for (const step of obj.steps) {
    if(!step||typeof step!=='object'||Array.isArray(step)||
       Object.keys(step).sort().join(',')!=='proposal,req,stage'||
       !['F01','F02','F03'].includes(step.stage))
      throw new Error('INVALID_STEP');
    let out;
    if(step.stage==='F01') {
      out=validateF01(step.req,step.proposal);
    } else if(step.stage==='F02') {
      out=validateF02(step.req,step.proposal);
    } else {
      const history=prepareF03History(step.req);
      out=(history.status==='READY')
        ?validateF03Proposal(step.req,history,step.proposal)
        :history;
    }
    if(!out||typeof out.status!=='string'||out.status.length>64)
      throw new Error('INVALID_RETURN');
    results.push({stage:step.stage,status:out.status});
  }
  process.stdout.write(JSON.stringify({results}));
} catch (_) {
  process.stdout.write('{"error":"INVALID_REVIEW_INPUT"}');
}
