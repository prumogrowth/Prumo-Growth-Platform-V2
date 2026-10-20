\set ON_ERROR_STOP on
\ir wa15c_pg17_load_commands.sql
-- Only a fixed allow-listed private read. One machine-readable JSON line;
-- no SQL is constructed from untrusted TypeScript labels or identifiers.
select jsonb_build_object(
 'found',pg_temp.wa15c_call('after_read'),
 'absent',pg_temp.wa15c_call('before_read'),
 'conflict',pg_temp.wa15c_call('after_conflict_read')
);
