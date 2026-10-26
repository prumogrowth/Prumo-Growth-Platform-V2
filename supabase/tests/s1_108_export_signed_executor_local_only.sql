-- Atomic lab-only installer: one DO statement also works within PG acceptance ROLLBACK.
-- Reuses CFI01's transient installer SET/CREATE mechanism, restoring preexisting
-- installer membership options rather than persisting operational membership.
do $i74_install$
declare
 installer_before jsonb;
 prior_admin boolean; prior_inherit boolean; prior_set boolean;
 prior_own_grant boolean;
begin
 select coalesce(jsonb_agg(jsonb_build_array(m.grantor,m.admin_option,m.inherit_option,m.set_option)
                         order by m.grantor),'[]'::jsonb)
 into installer_before from pg_catalog.pg_auth_members m
 where m.roleid='prumo_s1_export_executor'::regrole and m.member='postgres'::regrole;
 select m.admin_option,m.inherit_option,m.set_option
 into prior_admin,prior_inherit,prior_set from pg_catalog.pg_auth_members m
 where m.roleid='prumo_s1_export_executor'::regrole and m.member='postgres'::regrole
 and m.grantor='postgres'::regrole;
 prior_own_grant:=found;
-- I74 S1-only experimental PG17/GoTrue fixture. NEVER deploy to hosted DB.
do $q$begin
 if current_user<>'postgres' or to_regrole('prumo_s1_export_executor') is null
 or to_regnamespace('prumo_export_auth') is null or
 not exists(select 1 from pg_catalog.pg_extension where extname='pgcrypto')
 then raise exception 'I74_I73_REQUIRED' using errcode='42501';end if;
end $q$;
-- Cut I73's SET ROLE route; a signed login must never inherit executor.
do $q$begin
 if to_regrole('prumo_s1_export_login_ci') is not null then
  execute 'revoke prumo_s1_export_executor from prumo_s1_export_login_ci';
 end if;
end $q$;
create role prumo_s1_export_signed_login_ci nologin noinherit
 nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
grant usage on schema prumo_export_auth to prumo_s1_export_signed_login_ci;
create table prumo_export_auth.chaves_i74(
 id uuid primary key,secret bytea not null check(octet_length(secret)=32),
 valid_from timestamptz not null,valid_until timestamptz not null,
 active boolean not null default true,check(valid_until>valid_from));
create table prumo_export_auth.nonces_i74(
 nonce uuid primary key,key_id uuid not null
 references prumo_export_auth.chaves_i74(id),
 created_at timestamptz not null default clock_timestamp());
alter table prumo_export_auth.chaves_i74 enable row level security;
alter table prumo_export_auth.nonces_i74 enable row level security;
revoke all on prumo_export_auth.chaves_i74,prumo_export_auth.nonces_i74
 from public,anon,authenticated,service_role,prumo_s1_export_signed_login_ci;
grant select on prumo_export_auth.chaves_i74 to prumo_s1_export_executor;
-- FOR SHARE needs UPDATE ACL + an UPDATE visibility policy, even for reads.
-- Identity-column ACL only; WITH CHECK false forbids every actual row change.
grant update(id) on prumo_export_auth.chaves_i74 to prumo_s1_export_executor;
create policy i74_key_lock on prumo_export_auth.chaves_i74
 for update to prumo_s1_export_executor using (true) with check (false);
grant insert on prumo_export_auth.nonces_i74 to prumo_s1_export_executor;
create policy i74_keys on prumo_export_auth.chaves_i74
 for select to prumo_s1_export_executor using (true);
create policy i74_nonces on prumo_export_auth.nonces_i74
 for insert to prumo_s1_export_executor with check (true);
grant create on schema prumo_export_auth to prumo_s1_export_executor;
-- Only the trusted installer receives a transient, non-inheriting SET grant.
grant prumo_s1_export_executor to postgres with inherit false, set true;
set role prumo_s1_export_executor;
create function prumo_export_auth.exportar_assinado_i74(
 actor uuid,session uuid,kind text,shop uuid,cursor_id uuid,page_size integer,
 key_id uuid,issued bigint,nonce_id uuid,signature text
) returns jsonb language plpgsql volatile security definer set search_path=''
as $body$
declare now_s bigint;secret_key bytea;extension_schema text;material text;
 expected bytea;added integer;reply jsonb;
begin
 if actor is null or session is null or shop is null
  or kind is null or kind not in ('lotes','canais')
  or page_size is null or page_size not between 1 and 20
  or key_id is null or issued is null or nonce_id is null
  or signature is null or signature !~ '^[0-9a-f]{64}$'
 then raise exception 'I74_INVALID_FIELDS' using errcode='42501';end if;
 now_s:=extract(epoch from clock_timestamp())::bigint;
 if issued<now_s-30 or issued>now_s+5
 then raise exception 'I74_EXPIRED' using errcode='42501';end if;
 select k.secret into secret_key from prumo_export_auth.chaves_i74 k
 where k.id=key_id and k.active and k.valid_from<=to_timestamp(issued)
 and k.valid_until>clock_timestamp() for share of k;
 if not found then raise exception 'I74_INVALID_KEY' using errcode='42501';end if;
 select n.nspname into extension_schema from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace
 where e.extname='pgcrypto';
 if extension_schema is null
 then raise exception 'I74_NO_CRYPTO' using errcode='42501';end if;
 material:=concat_ws('|','prumo-s1-i20-v1','EXPORT74',
 actor::text,session::text,shop::text,coalesce(cursor_id::text,'-'),
 '-','-','-', 'E:'||(case when kind='lotes' then 'L' else 'C' end)
 ||':'||page_size::text,issued::text,nonce_id::text);
 execute pg_catalog.format('select %I.hmac($1,$2,''sha256'')',
 extension_schema) into expected using convert_to(material,'UTF8'),secret_key;
 if expected is distinct from decode(signature,'hex')
 then raise exception 'I74_INVALID_HMAC' using errcode='42501';end if;
 insert into prumo_export_auth.nonces_i74(nonce,key_id)
 values(nonce_id,key_id) on conflict do nothing;
 get diagnostics added=ROW_COUNT;
 if added<>1 then raise exception 'I74_REPLAY' using errcode='42501';end if;
 if not prumo_export_auth.sessao_ativa(actor,session)
 then raise exception 'I74_INACTIVE_SESSION' using errcode='42501';end if;
 perform set_config('request.jwt.claims',
 jsonb_build_object('role','authenticated','sub',actor::text,
 'session_id',session::text)::text,true);
 perform set_config('request.jwt.claim.sub',actor::text,true);
 perform set_config('request.jwt.claim.role','authenticated',true);
 reply:=public.s1_71_exportar_resumo(kind,shop,cursor_id,page_size);
 if jsonb_typeof(reply)<>'object'
 or reply->>'estado' not in ('OK','VAZIO','LIMITE_ATINGIDO')
 then raise exception 'I74_BAD_EXPORT_REPLY' using errcode='42501';end if;
 return reply;
end $body$;
revoke all on function prumo_export_auth.exportar_assinado_i74(
 uuid,uuid,text,uuid,uuid,integer,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s1_export_signed_login_ci;
grant execute on function prumo_export_auth.exportar_assinado_i74(
 uuid,uuid,text,uuid,uuid,integer,uuid,bigint,uuid,text)
 to prumo_s1_export_signed_login_ci;
reset role;
revoke create on schema prumo_export_auth from prumo_s1_export_executor;
do $audit$declare own text;begin
 select pg_catalog.pg_get_userbyid(proowner) into own from pg_catalog.pg_proc
 where oid='prumo_export_auth.exportar_assinado_i74(
 uuid,uuid,text,uuid,uuid,integer,uuid,bigint,uuid,text)'::regprocedure;
 if own<>'prumo_s1_export_executor' or
 pg_has_role('prumo_s1_export_signed_login_ci','prumo_s1_export_executor','MEMBER')
 or pg_has_role('prumo_s1_export_signed_login_ci','authenticated','MEMBER')
 or has_function_privilege('authenticated',
 'prumo_export_auth.exportar_assinado_i74(
 uuid,uuid,text,uuid,uuid,integer,uuid,bigint,uuid,text)','EXECUTE')
 or not has_function_privilege('prumo_s1_export_signed_login_ci',
 'prumo_export_auth.exportar_assinado_i74(
 uuid,uuid,text,uuid,uuid,integer,uuid,bigint,uuid,text)','EXECUTE')
 or has_function_privilege('prumo_s1_export_signed_login_ci',
 'public.s1_71_exportar_resumo(text,uuid,uuid,integer)','EXECUTE')
 or has_table_privilege('prumo_s1_export_signed_login_ci',
 'prumo_export_auth.chaves_i74','SELECT')
 or has_schema_privilege('prumo_s1_export_executor','prumo_export_auth','CREATE')
 then raise exception 'I74_ACL_FAILED' using errcode='42501';end if;
end $audit$;

-- Restore precisely the installer's own prior grant; other grantors untouched.
if prior_own_grant then
 execute pg_catalog.format('grant prumo_s1_export_executor to postgres with admin %s, inherit %s, set %s',
   prior_admin,prior_inherit,prior_set);
else
 revoke prumo_s1_export_executor from postgres granted by postgres;
end if;
if installer_before is distinct from (
 select coalesce(jsonb_agg(jsonb_build_array(m.grantor,m.admin_option,m.inherit_option,m.set_option)
                          order by m.grantor),'[]'::jsonb)
 from pg_catalog.pg_auth_members m
 where m.roleid='prumo_s1_export_executor'::regrole and m.member='postgres'::regrole)
then raise exception 'I74_INSTALLER_MEMBERSHIP_DRIFT' using errcode='42501';end if;
if not has_column_privilege('prumo_s1_export_executor','prumo_export_auth.chaves_i74','id','UPDATE')
 or has_column_privilege('prumo_s1_export_executor','prumo_export_auth.chaves_i74','secret','UPDATE')
 or has_column_privilege('prumo_s1_export_executor','prumo_export_auth.chaves_i74','active','UPDATE')
 or (select count(*) from pg_catalog.pg_policy where polrelid='prumo_export_auth.chaves_i74'::regclass
     and polcmd='w' and polname='i74_key_lock'
     and pg_catalog.pg_get_expr(polwithcheck,polrelid)='false')<>1
then raise exception 'I74_KEY_LOCK_ACL_UNSAFE' using errcode='42501';end if;
-- Enforce runtime isolation and RLS without giving the application SET ROLE.
if exists(select 1 from pg_catalog.pg_roles where rolname='prumo_s1_export_executor'
          and (rolcanlogin or rolsuper or rolbypassrls or rolcreaterole))
 or exists(select 1 from pg_catalog.pg_proc where oid=
 'prumo_export_auth.exportar_assinado_i74(uuid,uuid,text,uuid,uuid,integer,uuid,bigint,uuid,text)'::regprocedure
 and (not prosecdef or proconfig is distinct from array['search_path=""']::text[]))
then raise exception 'I74_OWNER_OR_PATH_UNSAFE' using errcode='42501';end if;
end $i74_install$;
