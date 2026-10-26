-- Connect as the actual LOGIN, never postgres followed by SET ROLE.
begin;
do $$ begin
 if session_user<>'prumo_cfi01_pgtest_login' or current_user<>session_user then
  raise exception 'wrong session principal';end if;
 begin perform * from public.mensagens;
 raise exception 'restricted login sees messages';exception when insufficient_privilege then null;end;
 begin set local role prumo_cfi01_atomic_owner_local;
 raise exception 'restricted login assumed owner';exception when insufficient_privilege then null;end;
end $$;
\echo 'PASS PRIVATE-02: real SQL session_user CFI login cannot SELECT messages or assume owner role'
rollback;
