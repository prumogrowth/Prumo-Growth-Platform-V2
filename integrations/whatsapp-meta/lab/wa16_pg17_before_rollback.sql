\set ON_ERROR_STOP on
\ir wa15c_pg17_load_commands.sql
-- Deliberate rollback simulates a failed write BEFORE durability, not a
-- power loss or truly unknown server result.
begin;
do $wa16_before$
declare r jsonb;
begin
 r:=pg_temp.wa15c_call('before_write');
 if r->>'outcome'<>'LAB_BOUND' or (r->>'retry_external')::boolean
 then raise exception 'WA16P_01_DID_NOT_PREPARE';end if;
 r:=pg_temp.wa15c_call('before_read');
 if r->>'outcome'<>'LAB_FOUND_EXACT'
 then raise exception 'WA16P_01_IN_TX_LOOKUP';end if;
end $wa16_before$;
rollback;
\echo PASS WA16P-01: a prepared binding was rolled back before COMMIT
