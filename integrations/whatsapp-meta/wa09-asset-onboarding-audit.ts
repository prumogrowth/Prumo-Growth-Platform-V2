/**
 * WA-09 / M09 — OFFLINE, untrusted inventory reconciliation ONLY.
 *
 * Two independently supplied fixture manifests (S0 expectation + Meta assets)
 * are checked against an injected registry; matching claims are NEVER proof
 * of provider ownership, partner delegation, S0 M2M identity or activation.
 * No Meta Graph, secrets, database, HTTP ACK, SQL, login, or live onboarding.
 * Actual authorities must be obtained by S0/Infra independently (#8).
 */
import {selectMetaCredential, type TrustedMetaRegistry} from './credential-routing.ts';

export type Wa09AuditDecision = Readonly<{
  decision:'LAB_INVENTORY_MATCHED_UNVERIFIED'|'DENIED';
  reason:'MATCHED_FIXTURES'|'INVALID_FIXTURE'|'REGISTRY_DENIED'|
   'INVENTORY_INCOMPLETE'|'ASSET_MISMATCH'|'OWNERSHIP_OR_DELEGATION_MISMATCH'|
   'DUPLICATE_ASSET'|'STALE_OR_REVOKED';
  app_count:number;
  waba_count:number;
  channel_count:number;
  catalog_count:number;
  /** Never promote a synthetic equality check into authority. */
  provider_ownership_verified:false;
  delegation_verified:false;
  s0_principal_verified:false;
  onboarding_approved:false;
  production_authorized:false;
  send_authorized:false;
  ack_allowed:false;
  s0_write_authorized:false;
}>;
type Obj=Record<string,unknown>;
type Waba={waba_id:string;catalog_ref:string;phone_number_ids:string[]};
type App={app_ref:string;concessionaria_id:string;business_owner_ref:string;
  delegated_partner_ref:string;route_ref:string;revision:number;wabas:Waba[]};
type Manifest={contract_version:string;apps:App[]};

const flags=Object.freeze({
 provider_ownership_verified:false,delegation_verified:false,
 s0_principal_verified:false,onboarding_approved:false,
 production_authorized:false,send_authorized:false,ack_allowed:false,
 s0_write_authorized:false,
} as const);
const output=(decision:Wa09AuditDecision['decision'],
 reason:Wa09AuditDecision['reason'],apps=0,wabas=0,channels=0,catalogs=0
):Wa09AuditDecision=>Object.freeze({
 decision,reason,app_count:apps,waba_count:wabas,
 channel_count:channels,catalog_count:catalogs,...flags,
});
const id=(x:unknown):x is string=>typeof x==='string'&&
 /^[A-Za-z0-9_.:-]{1,128}$/.test(x);
const phone=(x:unknown):x is string=>typeof x==='string'&&/^\d{5,25}$/.test(x);
const revision=(x:unknown):x is number=>
 typeof x==='number'&&Number.isSafeInteger(x)&&x>0;
const exact=(raw:unknown,keys:readonly string[]):Obj|null=>{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const own=Reflect.ownKeys(raw);
  if(own.length!==keys.length||own.some(k=>typeof k!=='string'||!keys.includes(k)))return null;
  const descriptors=Object.getOwnPropertyDescriptors(raw);
  if(keys.some(k=>!Object.hasOwn(descriptors,k)||!Object.hasOwn(descriptors[k],'value')))return null;
  return Object.fromEntries(keys.map(k=>[k,descriptors[k].value]));
 }catch{return null;}
};
const manifestKeys=['contract_version','apps'];
const appKeys=['app_ref','concessionaria_id','business_owner_ref',
 'delegated_partner_ref','route_ref','revision','wabas'];
const wabaKeys=['waba_id','catalog_ref','phone_number_ids'];
function parseManifest(raw:unknown,version:string):Manifest|null{
 const m=exact(raw,manifestKeys);
 if(!m||m.contract_version!==version||!Array.isArray(m.apps)||
    m.apps.length<1||m.apps.length>100)return null;
 const apps:App[]=[];
 let n=0;
 try{
  for(const candidate of m.apps){
   const a=exact(candidate,appKeys);
   if(!a||!id(a.app_ref)||!id(a.concessionaria_id)||
      !id(a.business_owner_ref)||!id(a.delegated_partner_ref)||
      !id(a.route_ref)||!revision(a.revision)||
      !Array.isArray(a.wabas)||a.wabas.length<1||a.wabas.length>100)return null;
   const wabas:Waba[]=[];
   for(const record of a.wabas){
    const w=exact(record,wabaKeys);
    if(!w||!id(w.waba_id)||!id(w.catalog_ref)||
       !Array.isArray(w.phone_number_ids)||w.phone_number_ids.length<1||
       w.phone_number_ids.length>100||w.phone_number_ids.some(x=>!phone(x)))return null;
    n+=w.phone_number_ids.length;
    if(n>1000)return null;
    wabas.push({waba_id:w.waba_id as string,
      catalog_ref:w.catalog_ref as string,
      phone_number_ids:[...w.phone_number_ids] as string[]});
   }
   apps.push({app_ref:a.app_ref as string,
     concessionaria_id:a.concessionaria_id as string,
     business_owner_ref:a.business_owner_ref as string,
     delegated_partner_ref:a.delegated_partner_ref as string,
     route_ref:a.route_ref as string,revision:a.revision as number,wabas});
  }
 }catch{return null;}
 return {contract_version:version,apps};
}
function duplicate(m:Manifest):boolean{
 const apps=new Set<string>(),routes=new Set<string>(),
  wabas=new Set<string>(),phones=new Set<string>(),catalogOwners=new Map<string,string>();
 for(const a of m.apps){
  if(apps.has(a.app_ref)||routes.has(a.route_ref))return true;
  apps.add(a.app_ref);routes.add(a.route_ref);
  for(const w of a.wabas){
   if(wabas.has(w.waba_id))return true;
   wabas.add(w.waba_id);
   const owner=catalogOwners.get(w.catalog_ref);
   if(owner!==undefined&&owner!==a.concessionaria_id)return true;
   catalogOwners.set(w.catalog_ref,a.concessionaria_id);
   for(const p of w.phone_number_ids){
    if(phones.has(p))return true;
    phones.add(p);
   }
  }
 }
 return false;
}
const matchList=(a:readonly string[],b:readonly string[]):boolean=>
 a.length===b.length&&new Set(a).size===a.length&&
 new Set(b).size===b.length&&a.every(v=>b.includes(v));

/**
 * Do not accept either manifest as an authority, even if called "trusted".
 * expected must eventually be provided by an authenticated S0 principal,
 * observed from Meta asset records, both checked by a privileged host.
 * This function only inspects synthetic claims and returns safe counts.
 */
export function inspectWa09OfflineAssetInventory(
 registry:TrustedMetaRegistry,expectedFixture:unknown,observedFixture:unknown,
 atMs:number,
):Wa09AuditDecision{
 try{
  if(!Number.isSafeInteger(atMs)||atMs<0)return output('DENIED','INVALID_FIXTURE');
  const expected=parseManifest(expectedFixture,'wa09-s0-asset-expectation.fixture.v0.1');
  const observed=parseManifest(observedFixture,'wa09-meta-assets.fixture.v0.1');
  if(!expected||!observed)return output('DENIED','INVALID_FIXTURE');
  if(duplicate(expected)||duplicate(observed))
   return output('DENIED','DUPLICATE_ASSET');
  if(!registry||!Array.isArray(registry.apps)||
     registry.apps.length!==expected.apps.length||
     observed.apps.length!==expected.apps.length)
   return output('DENIED','INVENTORY_INCOMPLETE');
  let channels=0;
  const catalogSet=new Set<string>();
  for(const a of expected.apps){
   const obs=observed.apps.find(x=>x.app_ref===a.app_ref);
   const reg=registry.apps.find(x=>x.app_ref===a.app_ref);
   if(!obs||!reg)return output('DENIED','INVENTORY_INCOMPLETE');
   if(a.business_owner_ref!==obs.business_owner_ref||
      a.delegated_partner_ref!==obs.delegated_partner_ref||
      a.concessionaria_id!==obs.concessionaria_id)
    return output('DENIED','OWNERSHIP_OR_DELEGATION_MISMATCH');
   if(a.route_ref!==obs.route_ref||a.revision!==obs.revision||
      a.route_ref!==reg.route_ref||a.concessionaria_id!==reg.concessionaria_id)
    return output('DENIED','ASSET_MISMATCH');
   if(a.revision!==reg.revision)return output('DENIED','STALE_OR_REVOKED');
   const selected=selectMetaCredential(registry,{
    purpose:'POST_APP_SECRET',trusted_route_ref:a.route_ref,
    at_ms:atMs,expected_revision:a.revision,
   });
   if(!selected.ok||selected.app_ref!==a.app_ref)
    return output('DENIED','STALE_OR_REVOKED');
   if(a.wabas.length!==obs.wabas.length||!Array.isArray(reg.channels))
    return output('DENIED','INVENTORY_INCOMPLETE');
   for(const w of a.wabas){
    const ow=obs.wabas.find(x=>x.waba_id===w.waba_id);
    if(!ow)return output('DENIED','INVENTORY_INCOMPLETE');
    if(w.catalog_ref!==ow.catalog_ref||
       !matchList(w.phone_number_ids,ow.phone_number_ids))
     return output('DENIED','ASSET_MISMATCH');
    for(const p of w.phone_number_ids){
     const hits=reg.channels.filter(c=>c.waba_id===w.waba_id&&
       c.phone_number_id===p&&c.active);
     if(hits.length!==1)return output('DENIED','ASSET_MISMATCH');
     channels++;
    }
    catalogSet.add(w.catalog_ref);
   }
   if(channels>1000)return output('DENIED','INVALID_FIXTURE');
   // A registry channel not explicitly listed in the S0 expectation
   // (including an inactive, revoked channel) must not disappear from audit.
   const allExpected=a.wabas.flatMap(w=>w.phone_number_ids.map(p=>w.waba_id+':'+p));
   if(reg.channels.length!==allExpected.length||
     reg.channels.some(c=>!allExpected.includes(c.waba_id+':'+c.phone_number_id)))
    return output('DENIED','INVENTORY_INCOMPLETE');
  }
  return output('LAB_INVENTORY_MATCHED_UNVERIFIED','MATCHED_FIXTURES',
   expected.apps.length,expected.apps.reduce((n,a)=>n+a.wabas.length,0),
   channels,catalogSet.size);
 }catch{
  // No payload, token, business owner ref, or exception is surfaced.
  return output('DENIED','INVALID_FIXTURE');
 }
}
