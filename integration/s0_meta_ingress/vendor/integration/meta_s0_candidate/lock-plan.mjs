/**
 * Candidate total order, NOT a DB lock manager. Global ratification is pending.
 * Rank 50..70 preserves final WA55 -> WA52 outbox -> event -> key order.
 * Every NEW S1/registry/revocation writer must participate before adoption.
 */
export const RANK=Object.freeze({
  S1_AUTHORITY_FENCE:10, S0_SCOPE_FENCE:20, REGISTRY:30,
  INTENT:40, OUTBOX:50, EVENT:60, TECHNICAL_KEY:70, NONCE:80, RECEIPT:90,
});
export function planLocks(resources) {
  const seen=new Set();
  return resources.map(x=>{
    if(!Object.hasOwn(RANK,x.kind)||typeof x.key!=='string'
      || !/^[A-Za-z0-9_.:-]{1,128}$/.test(x.key)) throw Error('INVALID_RESOURCE');
    const id=x.kind+':'+x.key;
    if(seen.has(id))throw Error('DUPLICATE_RESOURCE');
    seen.add(id);return {...x,rank:RANK[x.kind]};
  }).sort((a,b)=>a.rank-b.rank || (a.key<b.key?-1:a.key>b.key?1:0));
}
export function assertAcquisitionOrder(resources) {
  const plan=planLocks(resources);
  if(plan.some((x,i)=>x.kind!==resources[i].kind||x.key!==resources[i].key))
    throw Error('LOCK_ORDER_INVERSION');
  return true;
}
