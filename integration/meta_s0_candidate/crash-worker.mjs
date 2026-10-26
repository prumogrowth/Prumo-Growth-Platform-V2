// Invoked ONLY by durable.test.mjs, with synthetic data on stdin.
import {FileStore} from './lab-store.mjs';
import {CandidateLab} from './candidate.mjs';
let input='';for await(const c of process.stdin)input+=c;
const config=JSON.parse(input),phase=process.argv[3];
const store=new FileStore(process.argv[2],{hook:async current=>{
  if(current===phase)process.exit(23); // abrupt process loss, never an ACK
}});
const lab=new CandidateLab({optIn:'DISPOSABLE_META_S0_LAB_ONLY',store,
  keys:Object.fromEntries(Object.entries(config.keys).map(([id,hex])=>[id,Buffer.from(hex,'hex')])),
  appSecrets:config.appSecrets,clock:()=>config.now});
await lab.call(Buffer.from(config.bytes,'base64'),config.proof);
process.exit(99); // fail the test if the intended crash point was not reached
