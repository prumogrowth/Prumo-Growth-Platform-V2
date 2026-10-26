-- Actual private fixtures only; absence is never counted as D3/D4 denial.
begin;
set local role authenticated;
do $$ begin
 begin perform * from prumo_private.cfi01_human_closure_events_local;
 raise exception 'receipt exposed';exception when insufficient_privilege then null;end;
 if F03_BOOLEAN then
  begin perform * from prumo_private.cfi01_f03_form_fields_local;
  raise exception 'form exposed';exception when insufficient_privilege then null;end;
  begin perform * from prumo_private.cfi01_f03_media_attestations_local;
  raise exception 'media attestation exposed';exception when insufficient_privilege then null;end;
 end if;
end $$;
\echo 'PASS PRIVATE-01: authenticated cannot SELECT existing private receipt or selected F03 fixtures (when installed)'
reset role;
-- Synthetic helper proof only, does not execute authenticated CFI capture.
insert into auth.users(id) values('bb000000-0000-4000-8000-000000000001');
insert into auth.sessions(id,user_id) values('bb000000-0000-4000-8000-000000000002','bb000000-0000-4000-8000-000000000001');
do $$ begin
 if not prumo_private.cfi01_session_valid_local('bb000000-0000-4000-8000-000000000001','bb000000-0000-4000-8000-000000000002')
 then raise exception 'positive session helper control failed';end if;
end $$;
delete from auth.sessions where id='bb000000-0000-4000-8000-000000000002';
do $$ begin
 if prumo_private.cfi01_session_valid_local('bb000000-0000-4000-8000-000000000001','bb000000-0000-4000-8000-000000000002')
 then raise exception 'revoked session helper accepted';end if;
end $$;
\echo 'PASS PRIVATE-03: actual CFI session helper accepts live and denies deleted synthetic session'
rollback;
