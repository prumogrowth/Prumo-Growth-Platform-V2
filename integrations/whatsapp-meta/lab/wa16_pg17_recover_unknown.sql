\set ON_ERROR_STOP on
\ir wa15c_pg17_load_commands.sql
-- Fresh connection after the acknowledgement of the write was deliberately
-- discarded. Read-only recovery is the ONLY allowed external interaction.
begin;
do $wa16_recover$
declare r jsonb; n integer;
begin
 r:=pg_temp.wa15c_call('after_read');
 if r->>'outcome'<>'LAB_FOUND_EXACT' or (r->>'ack_allowed')::boolean
    or (r->>'production_authorized')::boolean or (r->>'retry_external')::boolean
 then raise exception 'WA16P_05_EXACT_POST_COMMIT_FAILED';end if;
 raise notice 'PASS WA16P-05: exact binding recovered after hidden commit reply';

 r:=pg_temp.wa15c_call('before_read');
 if r->>'outcome'<>'LAB_ABSENT' or (r->>'retry_external')::boolean
 then raise exception 'WA16P_06_NONCOMMITTED_SHOULD_BE_ABSENT';end if;
 raise notice 'PASS WA16P-06: rolled-back binding still absent; no resend evidence';

 r:=pg_temp.wa15c_call('after_conflict_read');
 if r->>'outcome'<>'LAB_CONFLICT' or (r->>'retry_external')::boolean
 then raise exception 'WA16P_07_CONFLICT_DISGUISED_AS_ABSENT';end if;
 raise notice 'PASS WA16P-07: conflicted exact recovery quarantined';

 r:=pg_temp.wa15c_call('after_replay');
 if r->>'outcome'<>'LAB_REPLAY' or (r->>'ack_allowed')::boolean
    or (r->>'retry_external')::boolean
 then raise exception 'WA16P_08_SQL_REPLAY_NOT_IDEMPOTENT';end if;
 raise notice 'PASS WA16P-08: DB-only replay did not duplicate Graph or ledger';

 begin
   perform pg_temp.wa15c_call('attempt_conflict');
   raise exception 'WA16P_09_SECOND_WAMID_ACCEPTED';
 exception when unique_violation then
   if sqlerrm<>'CONFLICT_TECHNICAL_BINDING' then raise;end if;
 end;
 raise notice 'PASS WA16P-09: second wamid rejected for same attempt';

 begin
   perform pg_temp.wa15c_call('wamid_conflict');
   raise exception 'WA16P_10_SECOND_ATTEMPT_ACCEPTED';
 exception when unique_violation then
   if sqlerrm<>'CONFLICT_TECHNICAL_BINDING' then raise;end if;
 end;
 raise notice 'PASS WA16P-10: second attempt rejected for same wamid';

 select count(*) into n from prumo_private.meta_vinculos_tentativa_fixture_s0
 where app_ref='FIXTURE_WA15C_APP_A' and attempt_ref like 'WA16_%';
 if n<>1 then raise exception 'WA16P_11_INVARIANT_LEDGER_COUNT';end if;
 if (select count(*) from prumo_private.outbox_intencoes_s0
     where id in ('f6400000-0000-4000-8000-000000000003',
                  'f6400000-0000-4000-8000-000000000004')
       and estado='BLOQUEADA_GATES')<>2
 then raise exception 'WA16P_11_OUTBOX_STATE_CHANGED';end if;
 raise notice 'PASS WA16P-11: one binding only; both S0 intents remain BLOCKED';
end $wa16_recover$;
commit;
