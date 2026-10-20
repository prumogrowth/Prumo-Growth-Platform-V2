/**
 * WA-16B: synthetic Graph-accepted observations fed to the REAL WA15B
 * preparer. Emit exactly eight commands. This is NOT the real Graph API.
 * The "before" attempt is rolled back; the "after" attempt commits while
 * its local confirmation output is deliberately hidden from the caller.
 */
import { prepareWa15FixtureCommand } from '../s0-technical-binding-contract.ts';
import type { CorrelationReference } from '../technical-reconciliation.ts';
import type { GraphSendOutcome } from '../graph-outbound.ts';

const base:CorrelationReference={
 app_ref:'12345678912',intent_id:'f6400000-0000-4000-8000-000000000003',
 recipient_verified:'5581900000000',
 scope:{
  concessionaria_id:'f6200000-0000-4000-8000-000000000001',
  canal_id:'f6300000-0000-4000-8000-000000000001',
  meta_app_ref:'12345678912',meta_waba_id:'33345678912',phone_number_id:'55545678912',
 },
};
const accepted:GraphSendOutcome={
 attempt_id:'WA16_BEFORE',correlation_id:'WA16_CORR_BEFORE',
 send_state:'API_ACCEPTED',api_accepted:true,http_status:200,
 provider_message_id:'wamid.WA16.BEFORE',meta_error_code:null,
 meta_error_subcode:null,retry_automatically:false,
};
type Action='REGISTER_FIXTURE'|'RECOVER_FIXTURE';
const afterRef={...base,intent_id:'f6400000-0000-4000-8000-000000000004'};
const afterGraph={...accepted,attempt_id:'WA16_AFTER',correlation_id:'WA16_CORR_AFTER',
 provider_message_id:'wamid.WA16.AFTER'};
function make(label:string,ref:CorrelationReference,evidence:GraphSendOutcome,action:Action){
 const r=prepareWa15FixtureCommand(ref,evidence,action);
 if(!r||r.ack_allowed||r.retry_external||r.production_authorized)
   throw Error('WA16_BAD_CONTRACT');
 return {label,...r};
}
const cmds=[
 make('before_write',base,accepted,'REGISTER_FIXTURE'),
 make('before_read',base,accepted,'RECOVER_FIXTURE'),
 make('after_write',afterRef,afterGraph,'REGISTER_FIXTURE'),
 make('after_read',afterRef,afterGraph,'RECOVER_FIXTURE'),
 make('after_replay',afterRef,afterGraph,'REGISTER_FIXTURE'),
 make('attempt_conflict',afterRef,{...afterGraph,provider_message_id:'wamid.WA16.FORGED'},'REGISTER_FIXTURE'),
 make('wamid_conflict',afterRef,{...afterGraph,attempt_id:'WA16_OTHER'},'REGISTER_FIXTURE'),
 make('after_conflict_read',afterRef,{...afterGraph,provider_message_id:'wamid.WA16.FORGED'},'RECOVER_FIXTURE'),
] as const;
if(cmds.length!==8||new Set(cmds.map(x=>x.label)).size!==8)
 throw Error('WA16_DUPLICATE_LABEL');
process.stdout.write(JSON.stringify(cmds));
