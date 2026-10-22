/** O5: visualização de um NOVO ciclo humano já criado/projetado pelo S0.
 * Nunca cria ciclo, concede acesso, reativa IA Vendedora, muda status ou faz envio.
 * Casos e links são apenas fixtures fictícias; servidor decide a relação de verdade.
 */
import { getActor, hasMockCaseScope, visibleConversations } from './fixtures.mjs';
import { isInActiveInbox } from './cf-op-02.mjs';

export const POSTMARK_SOURCES = Object.freeze({
  bank_submitted: 'cadastro enviado ao banco',
  sold: 'vendido'
});

export function isValidContinuationProjection(record) {
  const p=record?.postmarkProjection;
  return Boolean(p && p.direction === 'continuation' && p.confirmedCreated === true &&
    p.sellerAiSilenced === true && p.linkedByS0 === true &&
    typeof p.linkVersionRef === 'string' &&
    p.linkVersionRef.trim() && typeof p.originCaseRef === 'string' && p.originCaseRef.trim() &&
    Object.hasOwn(POSTMARK_SOURCES,p.source) &&
    record.status === 'em atendimento pelo operador' && isInActiveInbox(record));
}

function validPair(origin, continuation) {
  const a=origin?.postmarkProjection, b=continuation?.postmarkProjection;
  return Boolean(a?.direction==='origin' && a.confirmedCreated===true &&
    a.sellerAiSilenced===true && a.continuationCaseRef===continuation.id &&
    b?.direction==='continuation' && b.originCaseRef===origin.id &&
    b.source===a.source && b.linkVersionRef===a.linkVersionRef &&
    a.linkVersionRef?.trim() && a.linkedByS0===true && b.linkedByS0===true &&
    origin.shopId===continuation.shopId &&
    origin.status===POSTMARK_SOURCES[a.source] && isValidContinuationProjection(continuation));
}

export function postmarkViewFor(record, records, actorId, shopId) {
  const actor=getActor(actorId);
  if(!actor || !hasMockCaseScope(record,actorId,shopId) ||
    !record || record.shopId!==shopId) {
    return {visibility:'forbidden',kind:'unavailable',relatedCaseId:null,linked:false};
  }
  const allowed=visibleConversations(records,actorId,shopId);
  if(!allowed.some(x=>x.id===record.id)) {
    return {visibility:'forbidden',kind:'unavailable',relatedCaseId:null,linked:false};
  }
  const p=record.postmarkProjection;
  if(!p) return {visibility:'available',kind:'none',relatedCaseId:null,linked:false};
  const direction=p.direction;
  if(direction!=='origin' && direction!=='continuation')
    return {visibility:'available',kind:'unverified',relatedCaseId:null,linked:false};
  const relatedId=direction==='origin'?p.continuationCaseRef:p.originCaseRef;
  const related=allowed.find(x=>x.id===relatedId);
  if(!related) return {visibility:'available',kind:'restricted',relatedCaseId:null,linked:false};
  const origin=direction==='origin'?record:related;
  const continuation=direction==='continuation'?record:related;
  if(!validPair(origin,continuation))
    return {visibility:'available',kind:'unverified',relatedCaseId:null,linked:false};
  return {
    visibility:'available',kind:direction,linked:true,relatedCaseId:related.id,
    source:p.source,sourceStatus:POSTMARK_SOURCES[p.source],
    sellerAiSilenced:true,canOperateCurrentCase:actor.id===record.assignedTo
  };
}

/** A operação de um novo caso não exige acesso D2 ao histórico de OUTRO operador.
 * Somente a navegação para o caso relacionado requer permissão sobre AMBOS os casos.
 * Demonstração client-side: S0 terá que fazer esse controle no servidor.
 */
export function mayMockOperateContinuation(record, records, actorId, shopId) {
  const actor=getActor(actorId);
  if(!actor || !hasMockCaseScope(record,actorId,shopId) ||
     record?.shopId!==shopId || record.assignedTo!==actorId ||
     !visibleConversations(records,actorId,shopId).some(x=>x===record) ||
     !isValidContinuationProjection(record)) return false;
  const relation=postmarkViewFor(record,records,actorId,shopId);
  // Vínculo incoerente VÍSIVEL é rejeitado; histórico sem acesso não impede
  // atendimento no novo caso se a própria projeção de S0 está confirmada.
  if(relation.kind==='continuation' && relation.linked===true)return true;
  if(relation.kind!=='restricted')return false;
  const origin=records.find(x=>x.id===record.postmarkProjection.originCaseRef);
  if(origin && (origin.shopId!==record.shopId ||
    origin.status!==POSTMARK_SOURCES[record.postmarkProjection.source] ||
    origin.postmarkProjection?.continuationCaseRef!==record.id ||
    origin.postmarkProjection?.linkVersionRef!==record.postmarkProjection.linkVersionRef ||
    origin.postmarkProjection?.linkedByS0!==true)) return false;
  return true;
}

export function postmarkCopy(view) {
  if(!view || view.visibility==='forbidden')
    return {title:'Acesso indisponível',description:'A relação não está autorizada neste contexto.'};
  if(view.kind==='origin' && view.linked)
    return {title:'Novo atendimento humano confirmado · simulação',
      description:'O marco comercial original foi preservado. Um OUTRO caso humano foi projetado pelo S0 fictício, sem reativar a IA Vendedora.'};
  if(view.kind==='continuation' && view.linked)
    return {title:'Continuidade humana em novo ciclo · simulação',
      description:'Atendimento independente após marco bancário, com histórico original preservado e IA Vendedora permanentemente silenciada.'};
  if(view.kind==='restricted')
    return {title:'Relação sem acesso neste contexto',
      description:'Não revelar nem abrir caso vinculado fora do escopo do profissional.'};
  return {title:'Nenhum novo ciclo confirmado',
    description:'Não criar ou presumir um contato a partir de status, mensagem inbound ou botão local.'};
}
