\set ON_ERROR_STOP on
\ir wa15c_pg17_load_commands.sql
-- Synthetic "response lost" is simulated in the CI shell by redirecting all
-- output into a private ephemeral file. The SQL transaction DOES commit.
begin;
do $wa16_after$
declare r jsonb; n integer;
begin
 r:=pg_temp.wa15c_call('before_read');
 if r->>'outcome'<>'LAB_ABSENT' or (r->>'retry_external')::boolean
 then raise exception 'WA16P_02_ROLLBACK_DID_NOT_REMOVE_BINDING';end if;
 select count(*) into n from prumo_private.meta_vinculos_tentativa_fixture_s0
 where app_ref='FIXTURE_WA15C_APP_A' and attempt_ref='WA16_BEFORE';
 if n<>0 then raise exception 'WA16P_02_PHANTOM_WRITE';end if;
 raise notice 'PASS WA16P-02: new session sees ABSENT after rollback, no Graph retry';

 r:=pg_temp.wa15c_call('after_write');
 if r->>'outcome'<>'LAB_BOUND' or (r->>'ack_allowed')::boolean or
    (r->>'production_authorized')::boolean or (r->>'retry_external')::boolean
 then raise exception 'WA16P_03_WRITE_NOT_REGISTERED';end if;
 raise notice 'PASS WA16P-03: fixture write done before deliberately lost reply';
end $wa16_after$;
commit;
\echo PASS WA16P-04: fixture COMMIT performed; output will not reach caller
