\set ON_ERROR_STOP on
\ir wa15c_pg17_load_commands.sql
begin;
do $wa15c_recover$
declare r jsonb; n integer;
begin
 select count(*) into n from prumo_private.meta_vinculos_tentativa_fixture_s0
  where app_ref='FIXTURE_WA15C_APP_A';
 if n<>1 then raise exception 'WA15C_10_NOT_DURABLE_POST_COMMIT';end if;
 r:=pg_temp.wa15c_call('recover');
 if r->>'outcome'<>'LAB_FOUND_EXACT' or (r->>'ack_allowed')::boolean
   or (r->>'retry_external')::boolean or (r->>'production_authorized')::boolean
 then raise exception 'WA15C_10_FRESH_CONNECTION_REJECT';end if;
 raise notice 'PASS WA15C-10: fresh PostgreSQL session recovers real committed binding';

 -- Technical exact lookup remains possible after an outbox cancellation.
 update prumo_private.outbox_intencoes_s0 set estado='CANCELADA'
   where id='f6400000-0000-4000-8000-000000000001';
 r:=pg_temp.wa15c_call('recover');
 if r->>'outcome'<>'LAB_FOUND_EXACT' or (r->>'retry_external')::boolean
 then raise exception 'WA15C_11_CANCELLED_HISTORY';end if;
 raise notice 'PASS WA15C-11: cancelled intent keeps exact historical read';

 begin
   perform pg_temp.wa15c_call('register');
   raise exception 'WA15C_12_CANCELLED_WRITE_ACCEPTED';
 exception when insufficient_privilege then
   if sqlerrm<>'UNTRUSTED_OR_INACTIVE_FIXTURE_SCOPE' then raise;end if;
 end;
 if (select count(*) from prumo_private.meta_vinculos_tentativa_fixture_s0
   where app_ref='FIXTURE_WA15C_APP_A')<>1
 then raise exception 'WA15C_12_POST_CANCEL_CHANGED_LEDGER';end if;
 raise notice 'PASS WA15C-12: cancelled intent prevents new registration/replay';
end $wa15c_recover$;
commit;
