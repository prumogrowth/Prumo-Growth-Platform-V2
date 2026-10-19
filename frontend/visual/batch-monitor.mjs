/** FV-UI-012 / G4 — apenas PROJEÇÕES SINTÉTICAS de lotes já conhecidos do S0.
 * Não recebe arquivos, linhas CSV, contatos, cadastro ou ordem de distribuição.
 * A S0 precisa entregar lotes minimizados e já autorizados por equipe+loja.
 */
import { getActor, managedOperators, getShop } from './fixtures.mjs';

export const DEMO_BATCHES=Object.freeze([
  Object.freeze({id:'L-G4-01',managerId:'marina',shopId:'aurora',
    phase:'validated_partial',dataVersion:'batch-demo-v1',
    countsConfirmed:true,received:12,eligible:10,quarantined:2,
    qualityNote:'Duas linhas com pendência de qualidade (fictícias).'}),
  Object.freeze({id:'L-G4-02',managerId:'marina',shopId:'horizonte',
    phase:'under_review',countsConfirmed:false,
    qualityNote:'Conferência da origem pendente. Nenhum número validado.'}),
  Object.freeze({id:'L-G4-03',managerId:'daniel',shopId:'aurora',
    phase:'distribution_blocked',dataVersion:'batch-demo-v2',
    countsConfirmed:true,received:4,eligible:4,quarantined:0,
    qualityNote:'Distribuição indisponível na projeção, sem operador elegível confirmado.'}),
  Object.freeze({id:'L-G4-04',managerId:'daniel',shopId:'horizonte',
    phase:'received',countsConfirmed:false,
    qualityNote:'Recebimento ilustrativo; processamento ainda não confirmado.'})
]);

export const BATCH_PHASES=Object.freeze([
  'received','under_review','validated_partial','distribution_blocked','unavailable'
]);
export function batchPhaseCopy(phase){
  const labels={
    received:'Lote recebido · ilustração',
    under_review:'Conferência pendente · ilustração',
    validated_partial:'Validação parcial confirmada na fixture',
    distribution_blocked:'Distribuição bloqueada na fixture',
    unavailable:'Projeção sem confirmação'
  };
  return labels[phase]??labels.unavailable;
}

function validCounts(batch){
  const n=x=>Number.isSafeInteger(x)&&x>=0;
  return batch.countsConfirmed===true && typeof batch.dataVersion==='string' &&
    batch.dataVersion.trim().length>0 &&
    n(batch.received)&&n(batch.eligible)&&n(batch.quarantined)&&
    batch.eligible+batch.quarantined===batch.received;
}

export function projectManagerBatches(managerId,batches=DEMO_BATCHES){
  const manager=getActor(managerId);
  if(manager?.role!=='gestor' || manager.teamState!=='active')
    return Object.freeze({visibility:'forbidden',batches:Object.freeze([]),totals:null});
  const operators=managedOperators(managerId);
  const permitted=[];
  for(const row of batches){
    // Não herdar todos os lotes de uma concessionária compartilhada.
    if(!row || row.managerId!==managerId ||
      !manager.shops.includes(row.shopId) ||
      !operators.some(operator=>operator.shops.includes(row.shopId)))continue;
    const phase=BATCH_PHASES.includes(row.phase)?row.phase:'unavailable';
    const confirmed=validCounts(row) &&
      ['validated_partial','distribution_blocked'].includes(phase);
    permitted.push(Object.freeze({
      id:String(row.id??''),shopId:row.shopId,
      shopName:getShop(row.shopId)?.name??'Concessionária fictícia',
      phase,label:batchPhaseCopy(phase),countsConfirmed:confirmed,
      versionRef:confirmed?row.dataVersion.trim():null,
      received:confirmed?row.received:null,
      eligible:confirmed?row.eligible:null,
      quarantined:confirmed?row.quarantined:null,
      qualityNote:typeof row.qualityNote==='string'?row.qualityNote:'Sem observação confirmada.',
      actionAvailable:false
    }));
  }
  return Object.freeze({visibility:'ready',
    batches:Object.freeze(permitted),
    totals:Object.freeze({
      visibleBatches:permitted.length,
      confirmedBatches:permitted.filter(x=>x.countsConfirmed).length,
      distributionBlocked:permitted.filter(x=>x.phase==='distribution_blocked').length,
      pendingReview:permitted.filter(x=>x.phase==='under_review').length
    })
  });
}
