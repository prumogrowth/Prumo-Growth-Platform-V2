// Invokes pinned front modules; no transport, listeners or dependencies.
import {evaluateF03CommitCandidate} from './compat_sources/s2_f03.mjs';
import {stageCandidateCommandResult} from './compat_sources/fv_command.mjs';
let data='';
for await (const chunk of process.stdin) data+=chunk;
const {operation,payload,expected}=JSON.parse(data);
if (operation==='s2') console.log(JSON.stringify(evaluateF03CommitCandidate(payload)));
else if (operation==='fv') console.log(JSON.stringify(stageCandidateCommandResult(payload,expected)));
else throw new Error('Unknown probe');
