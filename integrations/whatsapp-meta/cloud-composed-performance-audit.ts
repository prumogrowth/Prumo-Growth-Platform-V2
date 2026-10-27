/**
 * Offline, synthetic, non-SLA benchmark of the full composed inspection
 * versus the one-HMAC generic inbound handoff. No calls to real services.
 *
 * Emits aggregate timings ONLY. Results vary by runner, JIT and CPU; do not
 * interpret as a production p95 or a promise of mobile/server throughput.
 */
import {performance} from 'node:perf_hooks';
import {createHmac} from 'node:crypto';
import {inspectCloudWebhookForHandoff}
 from './cloud-webhook-handoff.ts';
import {inspectSignedMetaComposedWebhook}
 from './cloud-composed-observation-handoff.ts';

const SECRET='SYNTHETIC_BENCHMARK_SECRET';
const ROUTE={waba_id:'123456789012',phone_number_id:'987654321098',revision:5};
const stamp='1761000000';
const msg=(n:number)=>({
 from:'5581888800000',id:'wamid.BENCH_'+n,timestamp:stamp,
 ...(
 n%6===0?{type:'button',button:{text:'Choose',payload:'BENCH_'+n}}:
 n%6===1?{type:'reaction',reaction:{message_id:'wamid.TARGET',emoji:'👍'}}:
 n%6===2?{type:'image',image:{id:'9999999999999'}}:
 n%6===3?{type:'unsupported',errors:[{code:131051}]}:
 n%6===4?{type:'text',text:{body:'Synthetic no real data'}}:
 {type:'interactive',interactive:{
  type:'list_reply',list_reply:{id:'MODEL_'+n,title:'Model'},
 }}
 ),
});
const status=(n:number)=>({
 id:'wamid.OUT_'+n,recipient_id:'5581888800000',timestamp:stamp,
 ...((n%2===0)?{status:'failed',errors:[{code:131026}]}:
 {status:'delivered'}),
});
function fixture(n:number){
 const nMessages=Math.ceil(n/2);
 const body={object:'whatsapp_business_account',
  entry:[{id:ROUTE.waba_id,changes:[{field:'messages',value:{
   messaging_product:'whatsapp',metadata:{phone_number_id:ROUTE.phone_number_id},
   messages:Array.from({length:nMessages},(_,i)=>msg(i)),
   statuses:Array.from({length:n-nMessages},(_,i)=>status(i)),
  }}]}]};
 const bytes=Buffer.from(JSON.stringify(body),'utf8');
 return {bytes,sig:'sha256='+createHmac('sha256',SECRET)
  .update(bytes).digest('hex')};
}
function quantile(a:readonly number[],fraction:number){
 const values=[...a].sort((x,y)=>x-y);
 return values[Math.ceil(fraction*values.length)-1];
}
async function profile(events:number){
 const {bytes,sig}=fixture(events);
 const one=()=>inspectCloudWebhookForHandoff(bytes,sig,SECRET,ROUTE);
 const composed=()=>inspectSignedMetaComposedWebhook(bytes,sig,SECRET,ROUTE);
 for(let i=0;i<12;i++){
  const a=await one(),b=await composed();
  if(a.outcome!=='AUTHENTICATED_NOT_DURABLE'||
     b.decision!=='SIGNED_COMPOSED_NOT_DURABLE'||
     b.occurrences.length!==events||a.observations.length!==events)
    throw Error('Benchmark fixture invalid');
 }
 const aTimes:number[]=[],bTimes:number[]=[];
 for(let i=0;i<40;i++){
  for(const [f,samples] of (i%2===0?
   [[one,aTimes],[composed,bTimes]]:
   [[composed,bTimes],[one,aTimes]]
  ) as Array<[typeof one|typeof composed,number[]]>){
   const start=performance.now();
   const result=await f();
   const elapsed=performance.now()-start;
   if(('outcome' in result&&result.outcome!=='AUTHENTICATED_NOT_DURABLE')||
      ('decision' in result&&result.decision!=='SIGNED_COMPOSED_NOT_DURABLE'))
    throw Error('Unexpected benchmark denial');
   samples.push(elapsed);
  }
 }
 const medianGeneric=quantile(aTimes,.5),medianComposed=quantile(bTimes,.5);
 const summary={
  events,body_bytes:bytes.byteLength,samples_per_mode:40,
  runtime:'Node 22 GitHub Actions runner',
  reference:'one-HMAC generic observation',composed:'six-HMAC full composition',
  generic_p50_ms:+medianGeneric.toFixed(3),
  generic_p95_ms:+quantile(aTimes,.95).toFixed(3),
  composed_p50_ms:+medianComposed.toFixed(3),
  composed_p95_ms:+quantile(bTimes,.95).toFixed(3),
  ratio_p50:+(medianComposed/medianGeneric).toFixed(2),
  diagnostic_only:true,
 };
 console.log('BENCHMARK_SUMMARY '+JSON.stringify(summary));
}
for(const n of [1,25,100])await profile(n);
