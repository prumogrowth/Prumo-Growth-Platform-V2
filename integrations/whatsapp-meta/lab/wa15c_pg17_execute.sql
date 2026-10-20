\set ON_ERROR_STOP on
\ir wa15c_pg17_load_commands.sql
begin;
do $wa15c_execute$
declare r jsonb; n integer;
begin
 r:=pg_temp.wa15c_call('register');
 if r->>'outcome'<>'LAB_BOUND' or (r->>'retry_external')::boolean
   or (r->>'ack_allowed')::boolean then
   raise exception 'WA15C_01_REGISTRATION_INVALID';end if;
 if (select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0
     where app_ref='FIXTURE_WA15C_APP_A' and
       concessionaria_id='f6200000-0000-4000-8000-000000000001'
       and canal_id='f6300000-0000-4000-8000-000000000001'
       and waba_ref='FIXTURE_WA15C_WABA_A'
       and phone_number_ref='FIXTURE_WA15C_PHONE_A'
       and intencao_id='f6400000-0000-4000-8000-000000000001'
       and attempt_ref='WA15C_ATTEMPT'
       and provider_message_id='wamid.WA15C.CONTRACT')<>1
 then raise exception 'WA15C_01_WRONG_S0_OWNER';end if;
 raise notice 'PASS WA15C-01: TS arguments persisted under S0-authoritative owner';

 r:=pg_temp.wa15c_call('replay');
 if r->>'outcome'<>'LAB_REPLAY' then raise exception 'WA15C_02_REPLAY';end if;
 raise notice 'PASS WA15C-02: same TS command idempotent';

 r:=pg_temp.wa15c_call('recover');
 if r->>'outcome'<>'LAB_FOUND_EXACT' or
    (r->>'retry_external')::boolean then raise exception 'WA15C_03_IN_TX_RECOVERY';end if;
 raise notice 'PASS WA15C-03: exact recovery before COMMIT';

 begin
   perform pg_temp.wa15c_call('wrong_sender');
   raise exception 'WA15C_WRONG_SENDER_ACCEPTED';
 exception when insufficient_privilege then
   if sqlerrm<>'UNMAPPED_META_TECHNICAL_SCOPE' then raise;end if;
 end;
 raise notice 'PASS WA15C-04: wrong sender cross-shop rejected';

 begin
   perform pg_temp.wa15c_call('wrong_intent');
   raise exception 'WA15C_WRONG_INTENT_ACCEPTED';
 exception when insufficient_privilege then
   if sqlerrm<>'UNTRUSTED_OR_INACTIVE_FIXTURE_SCOPE' then raise;end if;
 end;
 raise notice 'PASS WA15C-05: another tenant intent rejected';

 begin
   perform pg_temp.wa15c_call('attempt_conflict');
   raise exception 'WA15C_ATTEMPT_CONFLICT_ACCEPTED';
 exception when unique_violation then
   if sqlerrm<>'CONFLICT_TECHNICAL_BINDING' then raise;end if;
 end;
 raise notice 'PASS WA15C-06: attempt cannot get second wamid';

 begin
   perform pg_temp.wa15c_call('wamid_conflict');
   raise exception 'WA15C_WAMID_CONFLICT_ACCEPTED';
 exception when unique_violation then
   if sqlerrm<>'CONFLICT_TECHNICAL_BINDING' then raise;end if;
 end;
 raise notice 'PASS WA15C-07: wamid cannot get second attempt';

 r:=pg_temp.wa15c_call('absent');
 if r->>'outcome'<>'LAB_ABSENT' or (r->>'retry_external')::boolean
   or (r->>'ack_allowed')::boolean or (r->>'production_authorized')::boolean
 then raise exception 'WA15C_08_ABSENCE_AUTHORIZED_RETRY';end if;
 select count(*) into n from prumo_private.meta_vinculos_tentativa_fixture_s0
    where app_ref='FIXTURE_WA15C_APP_A';
 if n<>1 then raise exception 'WA15C_08_CONFLICT_CHANGED_LEDGER';end if;
 raise notice 'PASS WA15C-08: ABSENT is read-only, without retry authority';
end $wa15c_execute$;
commit;
\echo PASS WA15C-09: one exact S0 ledger record COMMITTED in session two
