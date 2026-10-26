// Test process only; does not start a server or call any provider.
import {parseCandidateCommand,requestFingerprint,compareRetry,stageCandidateResponse} from './reference_contract.mjs';
let text='';for await(const part of process.stdin)text+=part;
const cases=JSON.parse(text),results=[];
for(const c of cases){
 try{
  if(c.operation==='command'){
   const parsed=parseCandidateCommand(c.command);
   results.push({valid:true,command:parsed,fingerprint:await requestFingerprint(parsed)});
  }else if(c.operation==='retry')results.push({result:compareRetry(c.previous,c.current)});
  else if(c.operation==='response'){
   let calls=0;
   const getCurrentContext=()=>c.change_context_after_await&&++calls>1?c.changed_context:c.current_context;
   results.push(await stageCandidateResponse(c.response,c.command,{sentContext:c.sent_context,getCurrentContext}));
  }else throw Error('INVALID_OPERATION');
 }catch{results.push({valid:false});}
}
console.log(JSON.stringify(results));
