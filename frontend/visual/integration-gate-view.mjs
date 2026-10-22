/** FV-UI-021 — composição CONSERVADORA das fronteiras candidatas S0/S1.
 * NÃO é um transporte nem camada de autenticação/autorizações.
 * Sem contexto autenticado/ratificado, não liberar registros, comandos,
 * repetição automática, efeito comercial, remessa ou mensagens.
 */
import {stageProposedS0ReadEnvelope} from './s0-read-contract.mjs';
import {stageCandidateCommandResult} from './s0-command-result.mjs';

export const INTEGRATION_GATE_PROPOSAL='fv-ui-integration-readiness/0.1';
const isContext=x=>x!==null && typeof x==='object' && !Array.isArray(x) &&
  Object.getPrototypeOf(x)===Object.prototype &&
  typeof x.actor_id==='string' && x.actor_id.trim()===x.actor_id && !!x.actor_id &&
  typeof x.scope_ref==='string' && x.scope_ref.trim()===x.scope_ref && !!x.scope_ref;
const safeInfo=Object.freeze({
  integrationReady:false,authenticatedByS0:false,canExposeRecords:false,
  canPerformCommand:false,hasVerifiedEffect:false,automaticRetry:false,
  canChangeCommercialStatus:false
});
const build=(readState,commandState)=>Object.freeze({
  proposal:INTEGRATION_GATE_PROPOSAL,
  readState,commandState,...safeInfo
});

/** Esses argumentos seriam enviados APENAS por um adaptador autenticado
 * que a frente S0/S1 vier a implementar e homologar. Este protótipo não
 * aceita o simples fornecimento de IDs no browser como prova de permissão.
 *
 * Mesmo se os envelopes candidatos forem estruturalmente válidos,
 * o retorno é somente diagnóstico e NUNCA inclui records/outcome.
 */
export function projectCandidateIntegrationGate({readResponse=null,readExpected=null,
    commandResponse=null,commandExpected=null}={}){
  const readAsked=readResponse!=null || readExpected!=null;
  const commandAsked=commandResponse!=null || commandExpected!=null;
  if(!readAsked && !commandAsked)return build('not_connected','not_connected');

  // Cruzamento entre dois envelopes candidatos deve manter ator e escopo.
  if(readAsked && commandAsked &&
     (!isContext(readExpected) || !isContext(commandExpected) ||
      readExpected.actor_id!==commandExpected.actor_id ||
      readExpected.scope_ref!==commandExpected.scope_ref))
    return build('context_mismatch','context_mismatch');

  let read='not_connected',command='not_connected';
  if(readAsked){
    const candidate=stageProposedS0ReadEnvelope(readResponse,readExpected);
    read=candidate.accepted?'structural_candidate_only':'untrusted';
  }
  if(commandAsked){
    const candidate=stageCandidateCommandResult(commandResponse,commandExpected);
    command=candidate.accepted?(
      candidate.displayState==='claimed_applied'?'claimed_applied_unverified':
      candidate.displayState==='pending'?'pending_unverified':
      candidate.displayState==='rejected'?'rejected_unverified':'untrusted'
    ):'untrusted';
  }
  return build(read,command);
}
