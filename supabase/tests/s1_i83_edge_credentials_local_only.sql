-- I83: dedicated disposable admission and signing custody; no hosted migration.
begin;
set local lock_timeout='3s';
do $guard$
declare r record;p record;
begin
 if current_user<>'postgres' or session_user<>'postgres' or current_database()<>'postgres'
 or current_setting('server_version_num')::int/10000<>17
 or current_setting('prumo.i83_disposable',true) is distinct from 'YES'
 then raise exception 'I83_DISPOSABLE_ONLY' using errcode='42501';end if;
 for r in select * from(values
 ('prumo_private.s1_i79_admin_signed(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid,bigint,uuid,text)','8c07c152320c1861f8e71243b53d2636c9af8bb4d69e16facc6b940eaeb229e5','prumo_s0_g1_executor_local'),
 ('prumo_private.s1_i80_signed(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid,bigint,uuid,text)','3ef1812695b921683ef80df3b4eb4088e1ecdd350e9947585f383afdb2d13907','prumo_s0_g1_executor_local'),
 ('prumo_private.s1_i79_admin_bridge(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid)','1edc6b6016214adc9c6575f29b0fcbf1292e03ea9185b1a8edd36d1f7d36bdac','prumo_s1_admin_domain_local'),
 ('prumo_private.s1_i80_bridge(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid)','48ad4afe3303deb0c30f216326e64a10cc6fa05482f335d54ee3e5bc1f8d6a12','prumo_s1_admin_domain_local')
 ) v(signature,digest,owner)
 loop
  select prosrc,prosecdef,proconfig,pg_get_userbyid(proowner) as owner into p from pg_proc where oid=to_regprocedure(r.signature);
  if not found or not p.prosecdef or p.owner<>r.owner or p.proconfig is distinct from (case when r.signature like '%i80_bridge%' then array['search_path=""','TimeZone=UTC'] else array['search_path=""'] end) or encode(sha256(convert_to(p.prosrc,'UTF8')),'hex')<>r.digest
  then raise exception 'I83_I82_PREREQUISITE_DRIFT' using errcode='42501';end if;
 end loop;
 if exists(select 1 from pg_proc f cross join lateral aclexplode(coalesce(f.proacl,acldefault('f',f.proowner))) a
  where f.oid in ('prumo_private.s1_i79_admin_signed(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid,bigint,uuid,text)'::regprocedure,
   'prumo_private.s1_i80_signed(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid,bigint,uuid,text)'::regprocedure)
  and (a.grantee not in(f.proowner,'prumo_cfi01_pgtest_login'::regrole) or (a.is_grantable and a.grantee<>f.proowner)))
 then raise exception 'I83_SIGNED_ACL_DRIFT' using errcode='42501';end if;
 if exists(select 1 from pg_roles where rolname in('prumo_s0_g1_executor_local','prumo_s1_admin_domain_local','prumo_s1_professional_validator_local')
  and (rolcanlogin or rolinherit or rolsuper or rolcreatedb or rolcreaterole or rolreplication or rolbypassrls))
 then raise exception 'I83_OWNER_ROLE_DRIFT' using errcode='42501';end if;
end $guard$;

-- Starts disabled and passwordless. Explicit provisioning, not SQL in Git,
-- creates synthetic short-lived credentials after verifying the installation.
create role prumo_s1_admin_edge_local nologin noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls connection limit 4;
create role prumo_s1_edge_custodian_local nologin noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
grant connect on database postgres to prumo_s1_admin_edge_local;
grant usage on schema prumo_private to prumo_s1_admin_edge_local,prumo_s1_edge_custodian_local;

create table prumo_private.s1_i83_edge_credentials(
 key_id uuid primary key references prumo_private.cfi01_signing_keys_local(key_id),
 secret bytea,
 enabled boolean not null default true,
 not_before timestamptz not null,
 expires_at timestamptz not null,
 created_at timestamptz not null default clock_timestamp(),
 revoked_at timestamptz,
 check(expires_at>not_before),
 check((enabled and secret is not null and octet_length(secret)>=32 and revoked_at is null)
    or (not enabled and secret is null and revoked_at is not null))
);
alter table prumo_private.s1_i83_edge_credentials enable row level security;
revoke all on prumo_private.s1_i83_edge_credentials from public,anon,authenticated,service_role,
 prumo_cfi01_pgtest_login,prumo_s1_admin_edge_local,prumo_s1_admin_domain_local,prumo_s1_professional_validator_local;
grant select(key_id,secret,enabled,not_before,expires_at),update(key_id)
 on prumo_private.s1_i83_edge_credentials to prumo_s0_g1_executor_local;
create policy i83_edge_key_read on prumo_private.s1_i83_edge_credentials for select to prumo_s0_g1_executor_local
 using(session_user='prumo_s1_admin_edge_local');
create policy i83_edge_key_lock on prumo_private.s1_i83_edge_credentials for update to prumo_s0_g1_executor_local
 using(session_user='prumo_s1_admin_edge_local') with check(false);

grant create on schema prumo_private to prumo_s1_edge_custodian_local;
grant prumo_s1_edge_custodian_local to postgres with inherit false,set true;
alter table prumo_private.s1_i83_edge_credentials owner to prumo_s1_edge_custodian_local;
revoke prumo_s1_edge_custodian_local from postgres;
revoke create on schema prumo_private from prumo_s1_edge_custodian_local;

-- Same two functions, proof format, nonce FK, HMAC executor and business bodies.
-- Only admission and dedicated key source/expiry validation change.
grant create on schema prumo_private to prumo_s0_g1_executor_local;
grant prumo_s0_g1_executor_local to postgres with inherit false,set true;
set local role prumo_s0_g1_executor_local;
do $signed$
declare sig text;d text;old_lookup text;variable text;
begin
 foreach sig in array array[
 'prumo_private.s1_i79_admin_signed(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid,bigint,uuid,text)',
 'prumo_private.s1_i80_signed(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid,bigint,uuid,text)']
 loop
  d:=pg_get_functiondef(to_regprocedure(sig));
  d:=replace(d,'session_user<>''prumo_cfi01_pgtest_login''','session_user not in(''prumo_cfi01_pgtest_login'',''prumo_s1_admin_edge_local'')');
  variable:=case when sig like '%i79_%' then 'v_secret' else 'secret_value' end;
  old_lookup:='select secret into '||variable||' from prumo_private.cfi01_signing_keys_local where key_id=p_key and active for share;';
  if strpos(d,old_lookup)=0 then raise exception 'I83_LOOKUP_DRIFT' using errcode='42501';end if;
  d:=replace(d,old_lookup,
   'if session_user=''prumo_s1_admin_edge_local'' then'||chr(10)||
   '  select secret into '||variable||' from prumo_private.s1_i83_edge_credentials'||
   ' where key_id=p_key and enabled and not_before<=clock_timestamp() and expires_at>clock_timestamp() for share;'||chr(10)||
   ' else '||old_lookup||' end if;');
  d:=replace(d,' return ',
   ' if session_user=''prumo_s1_admin_edge_local'' and not exists(select 1 from prumo_private.s1_i83_edge_credentials'||
   ' where key_id=p_key and enabled and not_before<=clock_timestamp() and expires_at>clock_timestamp())'||
   ' then raise exception ''I83_KEY_EXPIRED_AFTER_WAIT'' using errcode=''42501'';end if;'||chr(10)||' return ');
  execute d;
 end loop;
end $signed$;
grant execute on function prumo_private.s1_i79_admin_signed(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid,bigint,uuid,text),
 prumo_private.s1_i80_signed(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid,bigint,uuid,text)
 to prumo_s1_admin_edge_local;
reset role;
revoke prumo_s0_g1_executor_local from postgres;
revoke create on schema prumo_private from prumo_s0_g1_executor_local;

grant create on schema prumo_private to prumo_s1_admin_domain_local;
grant prumo_s1_admin_domain_local to postgres with inherit false,set true;
set local role prumo_s1_admin_domain_local;
do $bridge$
declare sig text;d text;
begin
 foreach sig in array array[
 'prumo_private.s1_i79_admin_bridge(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid)',
 'prumo_private.s1_i80_bridge(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid)']
 loop
  d:=pg_get_functiondef(to_regprocedure(sig));
  execute replace(d,'session_user<>''prumo_cfi01_pgtest_login''','session_user not in(''prumo_cfi01_pgtest_login'',''prumo_s1_admin_edge_local'')');
 end loop;
end $bridge$;
reset role;
revoke prumo_s1_admin_domain_local from postgres;
revoke create on schema prumo_private from prumo_s1_admin_domain_local;

do $accept$
begin
 if (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname in('public','prumo_private') and has_function_privilege('prumo_s1_admin_edge_local',p.oid,'EXECUTE'))<>2
 then raise exception 'I83_UNEXPECTED_FUNCTION_EXPOSURE' using errcode='42501';end if;
 if current_setting('prumo.i83_fail_before_commit',true)='YES' then raise exception 'I83_INSTALL_FAULT' using errcode='23514';end if;
end $accept$;
commit;
