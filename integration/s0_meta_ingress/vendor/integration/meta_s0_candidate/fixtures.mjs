// Synthetic fixtures ONLY. No environment credentials, JWTs, Graph tokens or DSN.
import {randomBytes,randomUUID,createHmac} from 'node:crypto';
import {CandidateLab,newFixtureState} from './candidate.mjs';
import {MemoryStore} from './lab-store.mjs';
import {VERSION,signFixture} from './protocol.mjs';

export function setup({storeFactory,hook}={}) {
  let now=10000;
  const secrets={dispatch:randomBytes(32),ingress:randomBytes(32),
    reviewer:randomBytes(32),other:randomBytes(32)};
  const appSecrets={route_A:randomBytes(32).toString('hex'),route_B:randomBytes(32).toString('hex')};
  const key=(operations,tenant_ref='tenant_A',channel_ref='channel_A',route_ref='route_A')=>({
    kind:'LAB_SERVICE',active:true,issuer:'LAB_META_SERVICE',audience:'LAB_S0_CANDIDATE',
    tenant_ref,channel_ref,route_ref,route_revision:'1',operations,
    not_before_ms:1,not_after_ms:100000,
  });
  const authority=(tenant_ref,channel_ref,route_ref,recipient_ref)=>({
    tenant_ref,channel_ref,route_ref,route_revision:'1',recipient_ref,
    revision:'1',purpose_ref:'purpose_synthetic',content_sha256:'a'.repeat(64),
    catalog_revision:'1',template_revision:'1',cancelled:false,opted_out:false,
    gates:Object.fromEntries(['s0','s1','assignment','consent','window','template',
      'catalog','purpose','destination'].map(x=>[x,true])),
  });
  const seed=newFixtureState({
    keys:{dispatch:key(['reserve','begin','observe','read']),
      ingress:key(['append_batch']),reviewer:key(['read','review']),
      other:key(['reserve','begin','observe','read','append_batch'],
        'tenant_B','channel_B','route_B')},
    routes:{route_A:{active:true,revision:'1',waba_id:'100001',phone_number_id:'200001'},
      route_B:{active:true,revision:'1',waba_id:'100002',phone_number_id:'200002'}},
    authorities:{
      intent_A:authority('tenant_A','channel_A','route_A','recipient_synthetic_A'),
      intent_A2:authority('tenant_A','channel_A','route_A','recipient_synthetic_A2'),
      intent_B:authority('tenant_B','channel_B','route_B','recipient_synthetic_B'),
    },
  });
  const store=storeFactory?storeFactory(seed):new MemoryStore(seed,{hook});
  const lab=new CandidateLab({optIn:'DISPOSABLE_META_S0_LAB_ONLY',store,
    keys:secrets,appSecrets,clock:()=>now});
  const packet=(operation,body,role='dispatch',extra={})=>signFixture(role,secrets[role],{
    version:VERSION,operation,request_id:randomUUID(),correlation_id:randomUUID(),
    nonce:randomUUID(),issued_at_ms:now,expires_at_ms:now+1000,body,...extra,
  });
  const call=async(operation,body,role='dispatch',extra={})=>{
    const p=packet(operation,body,role,extra);return lab.call(p.bytes,p.proof);
  };
  const batch=(statuses=['sent','delivered'],{variant=false,waba='100001',
    phone='200001',batch_ref='batch_A',route_revision='1'}={})=>{
    const payload={object:'whatsapp_business_account',entry:[{id:waba,changes:[
      {field:'messages',value:{metadata:{phone_number_id:phone},
        statuses:statuses.map(status=>({id:'wamid.SYNTHETIC_A',
          recipient_id:'5500000000000',status,timestamp:'1700000000'})),
        ...(variant?{synthetic_variant:true}:{})}},
    ]}]};
    const raw=Buffer.from(JSON.stringify(payload));
    return {batch_ref,route_revision,raw_base64:raw.toString('base64'),
      meta_signature:'sha256='+createHmac('sha256',appSecrets.route_A).update(raw).digest('hex')};
  };
  return {seed,store,lab,secrets,appSecrets,packet,call,batch,
    setNow:x=>{now=x;},getNow:()=>now};
}
export const reservation=(extra={})=>({
  intent_ref:'intent_A',idempotency_key:'logical_A',expected_revision:'1',...extra,
});
export const http=(status,body={messages:[{id:'wamid.SYNTHETIC_A'}]},headers={})=>({
  kind:'http_response',http_status:status,
  headers:{'content-type':'application/json',...headers},
  response_base64:Buffer.from(JSON.stringify(body)).toString('base64'),
});
export async function begun(h) {
  const r=await h.call('reserve',reservation());
  const b=await h.call('begin',{attempt_ref:r.attempt_ref,expected_revision:'1'});
  if(b.code!=='LAB_BEGIN_RECORDED_NO_SEND_RIGHTS')throw Error('FIXTURE_BEGIN_FAILED');
  return r.attempt_ref;
}
