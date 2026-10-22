/** FV-UI-020 — estado de transporte de mensagem, projeção SINTÉTICA.
 * D-AL-04 / FV-DOC-03 §5. Não autentica S0/Meta, não faz polling nem envio.
 * O navegador não promove ACK a SENT nem marca resposta humana comprovada.
 */
import {hasMockCaseScope} from './fixtures.mjs';

export const TRANSPORT_PRESENTATION_STATES=Object.freeze([
  'requested','api_accepted','uncertain',
  'sent_confirmed','delivered','read','failed_confirmed'
]);
const PROVEN_STATES=new Set(['sent_confirmed','delivered','read','failed_confirmed']);
const labelByState=Object.freeze({
  requested:'Solicitado · envio não comprovado',
  api_accepted:'API aceitou · envio NÃO comprovado',
  uncertain:'Resultado incerto · verificar no serviço',
  sent_confirmed:'Envio comprovado · fixture',
  delivered:'Entrega comprovada · fixture',
  read:'Leitura comprovada · fixture',
  failed_confirmed:'Falha definitiva comprovada · fixture'
});
const noProjection=Object.freeze({
  visibility:'unavailable',state:'unknown',label:null,
  provedSent:false,provedDelivery:false,provedRead:false,
  failedConfirmed:false,needsRefresh:false
});
const isRef=v=>typeof v==='string' && v.trim()===v && v.length>0 && v.length<=160;
const isTransportProjection=o=>o && typeof o==='object' && !Array.isArray(o) &&
  (Object.getPrototypeOf(o)===Object.prototype || Object.getPrototypeOf(o)===null);

/** Só mostra o estado da mensagem identificada, por mesma concessionária.
 * Para estados avançados, prova específica e bandeira explicitamente
 * confirmada na fixture são obrigatórias; proveniência real seria S0/Meta.
 * Uma mensagem criada localmente nunca recebe prova de transporte.
 */
export function stageMockMessageTransport(record,message,actorId,shopId) {
  if(!isTransportProjection(record) || !isTransportProjection(message) || message.side!=='out' ||
    message.deliveryState==='local_demo_not_sent' ||
    record.shopId!==shopId || record.assignedTo!==actorId ||
    !hasMockCaseScope(record,actorId,shopId) ||
    !Array.isArray(record.messages) || !record.messages.includes(message))return noProjection;
  const p=message.transportProjection;
  if(!isTransportProjection(p) || p.source!=='s0_fixture' ||
    p.caseRef!==record.id || p.shopRef!==shopId || p.messageRef!==message.id ||
    !isRef(p.versionRef) || !TRANSPORT_PRESENTATION_STATES.includes(p.state))
    return noProjection;
  const proven=PROVEN_STATES.has(p.state);
  if(proven ? (p.confirmed!==true || !isRef(p.proofRef)) :
      (p.confirmed!==false || p.proofRef!=null))return noProjection;
  if(p.state==='api_accepted' && !isRef(p.apiAckRef))return noProjection;
  if(p.state!=='api_accepted' && p.apiAckRef!=null)return noProjection;
  const result={
    visibility:'synthetic',state:p.state,label:labelByState[p.state],
    provedSent:['sent_confirmed','delivered','read'].includes(p.state),
    provedDelivery:['delivered','read'].includes(p.state),
    provedRead:p.state==='read',
    failedConfirmed:p.state==='failed_confirmed',
    needsRefresh:!proven
  };
  return Object.freeze(result);
}
