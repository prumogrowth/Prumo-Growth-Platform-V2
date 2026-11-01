// E04 Offline Lab / Prumo — *candidate* gate validators, no network, no business writes.
// Pure data functions. NOT the physical S0 contract or a generative model.

export function isRecord(x){return x!==null && typeof x==="object" && !Array.isArray(x);}

export function isId(x){return typeof x==="string" && x.length>0 && x.length<=160 && !/[\u0000-\u001f]/.test(x);}

export function onlyKeys(x,keys){return isRecord(x)&&Object.keys(x).every(k=>keys.includes(k));}

export function verdict(status){return Object.freeze({status});}

// OFF-19 corrective audit: reject inherited/alias keys and accessors on S0
// version fixtures. A caller-provided authentication claim is NOT a real grant.
export function versionGate(ctx){
  try{
    if(!isRecord(ctx))return verdict("DENIED");
    const value=(o,k)=>{
      if(!isRecord(o))return undefined;
      const d=Object.getOwnPropertyDescriptor(o,k);
      return d&&Object.prototype.hasOwnProperty.call(d,"value")?d.value:undefined;
    };
    if(value(ctx,"authenticated")!==true||value(ctx,"authorized")!==true||
       value(ctx,"tenantAllowed")!==true)return verdict("DENIED");
    const store=value(ctx,"storeId"),caseId=value(ctx,"caseId");
    const expected=value(ctx,"expected"),current=value(ctx,"current");
    if(!isId(store)||!isId(caseId)||!isRecord(expected)||!isRecord(current))
      return verdict("INVALID_INPUT");
    const protoOk=o=>Object.getPrototypeOf(o)===Object.prototype||Object.getPrototypeOf(o)===null;
    if(!protoOk(expected)||!protoOk(current))return verdict("INVALID_INPUT");
    const expectedKeys=Reflect.ownKeys(expected),currentKeys=Reflect.ownKeys(current);
    const allowed=["case","cycle","form","catalog","assignment","policy"];
    if(!expectedKeys.length||expectedKeys.length!==currentKeys.length||
       expectedKeys.some(k=>typeof k!=="string"||!allowed.includes(k)||!currentKeys.includes(k))||
       currentKeys.some(k=>typeof k!=="string"||!allowed.includes(k)||!expectedKeys.includes(k)))
      return verdict("INVALID_INPUT");
    for(const k of expectedKeys){
      const e=Object.getOwnPropertyDescriptor(expected,k),c=Object.getOwnPropertyDescriptor(current,k);
      if(!e||!c||!Object.prototype.hasOwnProperty.call(e,"value")||
         !Object.prototype.hasOwnProperty.call(c,"value")||
         !Number.isSafeInteger(e.value)||e.value<0||
         !Number.isSafeInteger(c.value)||c.value<0)return verdict("INVALID_INPUT");
      if(e.value!==c.value)return verdict("STALE");
    }
    return verdict("READY");
  }catch{return verdict("INVALID_INPUT");}
}

export function validateF01(req,proposal){
  const gate=versionGate(req?.scope);if(gate.status!=="READY")return gate;
  if(req.owner!=="ai"||req.handoff!==false||req.humanized!==false)return verdict("DENIED");
  if("staffRoster" in req || "consultantNames" in req || "staffAvailability" in req)return verdict("INVALID_INPUT");
  if(!Array.isArray(req.sources))return verdict("INVALID_INPUT");
  const seen=new Set();
  for(const s of req.sources){
    if(!onlyKeys(s,["id","storeId","approved","active","mode","validUntil"])||!isId(s.id)||seen.has(s.id)||s.storeId!==req.scope.storeId||s.approved!==true||!["current","historical"].includes(s.mode))return verdict("INVALID_INPUT");
    seen.add(s.id);
  }
  if(!onlyKeys(proposal,["text","sourceIds","commercial","handoffAdvisory","modality"])||typeof proposal.text!=="string"||proposal.text.trim()===""||!Array.isArray(proposal.sourceIds)||typeof proposal.commercial!=="boolean"||!["text","audio"].includes(proposal.modality))return verdict("SCHEMA_INVALID");
  if(proposal.sourceIds.some(id=>!seen.has(id)))return verdict("SOURCE_INVALID");
  if(proposal.commercial && proposal.sourceIds.length===0)return verdict("SOURCE_INVALID");
  // Never substitute the process clock for a missing S0 observation time.
  // Legacy direct callers must supply a deterministic clock for expiring offers.
  if(proposal.sourceIds.some(id=>req.sources.find(s=>s.id===id)?.validUntil!==undefined)&&
     (!Number.isSafeInteger(req.nowMs)||req.nowMs<0))return verdict("INVALID_INPUT");
  if(proposal.sourceIds.some(id=>{const s=req.sources.find(y=>y.id===id);return !s.active||s.mode!=="current"||(s.validUntil!==undefined&&(!Number.isFinite(Date.parse(s.validUntil))||Date.parse(s.validUntil)<=req.nowMs));}))return verdict("SOURCE_INVALID");
  return verdict("PROPOSED");
}

export function validTime(x){return typeof x==="string" && /(Z|[+-]\d{2}:\d{2})$/.test(x) && Number.isFinite(Date.parse(x));}

export function validateF02(req,proposal){
  const gate=versionGate(req?.scope);if(gate.status!=="READY")return gate;
  if(req.explicitS0Request!==true||req.optOut!==false||req.handoffPlanReuse===true||!["human","seller_ai"].includes(req.ownerRoute)||(req.purpose==="post_human"&&req.ownerRoute!=="human"))return verdict("DENIED");
  if(!isId(req.purpose)||!Array.isArray(req.allowedTemplates)||!Number.isSafeInteger(req.maxAttempts)||req.maxAttempts<0||!validTime(req.windowStart)||!validTime(req.windowEnd)||Date.parse(req.windowStart)>=Date.parse(req.windowEnd))return verdict("INVALID_INPUT");
  const templates=new Map();
  for(const t of req.allowedTemplates){
    if(!onlyKeys(t,["id","version","storeId","purpose","active"])||!isId(t.id)||!isId(t.version)||t.storeId!==req.scope.storeId||t.purpose!==req.purpose||t.active!==true)return verdict("INVALID_INPUT");
    if(templates.has(t.id+"@"+t.version))return verdict("INVALID_INPUT");
    templates.set(t.id+"@"+t.version,t);
  }
  if(!onlyKeys(proposal,["attempts","finalTemplate"])||!Array.isArray(proposal.attempts)||proposal.attempts.length>req.maxAttempts)return verdict("SCHEMA_INVALID");
  let prev=Date.parse(req.windowStart)-1;
  const all=[...proposal.attempts,...(proposal.finalTemplate===null?[]:[proposal.finalTemplate])];
  for(const p of all){
    if(!onlyKeys(p,["templateId","version","purpose","at"])||!isId(p.templateId)||!isId(p.version)||p.purpose!==req.purpose||!validTime(p.at))return verdict("SCHEMA_INVALID");
    const time=Date.parse(p.at);
    if(time<=prev||time<Date.parse(req.windowStart)||time>Date.parse(req.windowEnd))return verdict("SCHEMA_INVALID");
    if(!templates.has(p.templateId+"@"+p.version))return verdict("SOURCE_INVALID");
    prev=time;
  }
  return verdict("PROPOSED");
}

export function prepareF03History(req){
  const gate=versionGate(req?.scope);if(gate.status!=="READY")return gate;
  if(req.humanClosed!==true||req.closureAuthenticated!==true||!isId(req.closureId))return verdict("DENIED");
  if(["case","cycle","form","catalog","assignment"].some(k=>!(k in req.scope.expected)))return verdict("INVALID_INPUT");
  if(!isId(req.personId)||!Number.isSafeInteger(req.cutoffSequence)||req.cutoffSequence<0||!Array.isArray(req.records))return verdict("INVALID_INPUT");
  const ids=new Set(),snapshot=[];
  for(const r of req.records){
    if(!onlyKeys(r,["id","storeId","personId","caseId","sequence","author","kind","available","contentAuthorized","content"])||!isId(r.id)||ids.has(r.id)||!isId(r.caseId)||!isId(r.author)||!["text","media"].includes(r.kind)||!Number.isSafeInteger(r.sequence)||r.sequence<0||r.storeId!==req.scope.storeId||r.personId!==req.personId)return verdict("INVALID_INPUT");
    ids.add(r.id);
    if(r.sequence>req.cutoffSequence)continue;
    if(r.available===true&&r.contentAuthorized!==true)return verdict("DENIED");
    if(r.available!==true&&r.available!==false)return verdict("INVALID_INPUT");
    // Metadata only. Media/transcripts are never fabricated by this offline stub.
    snapshot.push({id:r.id,caseId:r.caseId,sequence:r.sequence,author:r.author,kind:r.kind,available:r.available});
  }
  snapshot.sort((a,b)=>a.sequence-b.sequence||a.id.localeCompare(b.id));
  return {status:"READY",closureId:req.closureId,storeId:req.scope.storeId,personId:req.personId,cutoffSequence:req.cutoffSequence,expectedVersions:{...req.scope.expected},sources:snapshot};
}

export function validateF03Proposal(req,snapshot,proposal){
  const gate=versionGate(req?.scope);if(gate.status!=="READY")return gate;
  if(!isRecord(snapshot)||snapshot.status!=="READY"||snapshot.closureId!==req.closureId||snapshot.storeId!==req.scope.storeId||snapshot.personId!==req.personId||snapshot.cutoffSequence!==req.cutoffSequence||JSON.stringify(snapshot.expectedVersions)!==JSON.stringify(req.scope.expected))return verdict("INVALID_INPUT");
  if(!Array.isArray(req.catalog)||!Array.isArray(snapshot.sources))return verdict("INVALID_INPUT");
  const catalog=new Map();for(const f of req.catalog){if(!onlyKeys(f,["code","essential"])||!isId(f.code)||typeof f.essential!=="boolean"||catalog.has(f.code))return verdict("INVALID_INPUT");catalog.set(f.code,f);}
  const sources=new Map(snapshot.sources.map(s=>[s.id,s]));
  if(!onlyKeys(proposal,["fields","conflicts","commercialAdvisory"])||!Array.isArray(proposal.fields)||!Array.isArray(proposal.conflicts))return verdict("SCHEMA_INVALID");
  const present=new Set();
  for(const f of proposal.fields){
    if(!onlyKeys(f,["code","value","sourceId"])||!isId(f.code)||!isId(f.sourceId)||!catalog.has(f.code)||present.has(f.code)||!["string","number","boolean"].includes(typeof f.value)||f.value===""||!sources.has(f.sourceId)||sources.get(f.sourceId).available!==true)return verdict("SOURCE_INVALID");
    present.add(f.code);
  }
  for(const c of proposal.conflicts){if(!onlyKeys(c,["code","sourceIds"])||!catalog.has(c.code)||!Array.isArray(c.sourceIds)||c.sourceIds.length<2||c.sourceIds.some(id=>!sources.has(id)||sources.get(id).available!==true))return verdict("SOURCE_INVALID");}
  const advisory=proposal.commercialAdvisory;
  if(advisory!==null){
    if(!onlyKeys(advisory,["kind","sourceIds"])||advisory.kind!=="perdido"||!Array.isArray(advisory.sourceIds)||advisory.sourceIds.length===0||!Array.isArray(req.verifiedWithdrawalSourceIds)||advisory.sourceIds.some(id=>!req.verifiedWithdrawalSourceIds.includes(id)||!sources.has(id)||sources.get(id).available!==true))return verdict("SOURCE_INVALID");
  }
  if([...catalog.values()].some(f=>f.essential&&!present.has(f.code))||proposal.conflicts.length>0)return verdict("REVIEW_REQUIRED");
  return verdict("PROPOSED");
}
