/**
 * WA-15C: GitHub Actions-only synthetic fixture generator.
 * Imports the ACTUAL WA-15B TypeScript adapter; no database or HTTP access.
 * Its JSON output is passed as a psql VARIABLE and parsed as JSONB, never
 * interpolated as a SQL identifier, query or statement.
 */
import { prepareWa15FixtureCommand } from '../s0-technical-binding-contract.ts';
import type { CorrelationReference } from '../technical-reconciliation.ts';
import type { GraphSendOutcome } from '../graph-outbound.ts';

const base:CorrelationReference={
  app_ref:'12345678912',
  intent_id:'f6400000-0000-4000-8000-000000000001',
  recipient_verified:'5581900000000',
  scope:{
    concessionaria_id:'f6200000-0000-4000-8000-000000000001',
    canal_id:'f6300000-0000-4000-8000-000000000001',
    meta_app_ref:'12345678912',
    meta_waba_id:'33345678912',
    phone_number_id:'55545678912',
  },
};
const accepted:GraphSendOutcome={
  attempt_id:'WA15C_ATTEMPT',correlation_id:'WA15C_CORR',
  send_state:'API_ACCEPTED',api_accepted:true,http_status:200,
  provider_message_id:'wamid.WA15C.CONTRACT',
  meta_error_code:null,meta_error_subcode:null,retry_automatically:false,
};
type Action='REGISTER_FIXTURE'|'RECOVER_FIXTURE';
const command = (label:string,r:CorrelationReference,o:GraphSendOutcome,a:Action)=>{
  const result=prepareWa15FixtureCommand(r,o,a);
  if(!result||result.ack_allowed||result.retry_external||result.production_authorized)
    throw Error('WA15C_FIXTURE_PREPARATION_REJECTED');
  return Object.freeze({label,...result});
};
const commands=[
  command('register',base,accepted,'REGISTER_FIXTURE'),
  command('replay',base,accepted,'REGISTER_FIXTURE'),
  command('recover',base,accepted,'RECOVER_FIXTURE'),
  command('wrong_sender',{...base,scope:{...base.scope,phone_number_id:'77745678912'}},accepted,'REGISTER_FIXTURE'),
  command('wrong_intent',{...base,intent_id:'f6400000-0000-4000-8000-000000000002'},accepted,'REGISTER_FIXTURE'),
  command('attempt_conflict',base,{...accepted,provider_message_id:'wamid.WA15C.FORGED'},'REGISTER_FIXTURE'),
  command('wamid_conflict',base,{...accepted,attempt_id:'WA15C_OTHER'},'REGISTER_FIXTURE'),
  command('absent',base,{...accepted,attempt_id:'WA15C_ABSENT',correlation_id:'WA15C_ABSENT_CORR',
    provider_message_id:'wamid.WA15C.ABSENT'},'RECOVER_FIXTURE'),
] as const;
if(commands.length!==8||new Set(commands.map(x=>x.label)).size!==8)throw Error('WA15C_BAD_COMMAND_SET');
process.stdout.write(JSON.stringify(commands));
