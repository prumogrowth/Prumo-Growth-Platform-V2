-- OPS-03 metadata-only diagnostic. Future hosted execution needs authorization.
-- No identity rows, tokens, credentials, PII, commercial data or function bodies.
-- Execute the complete read-only transaction as one SQL Editor submission.
begin read only;
with expected(schema_name,table_name,columns_required) as (values
 ('auth','users',array['id','deleted_at','banned_until']::text[]),
 ('auth','sessions',array['id','user_id','created_at','not_after']::text[]),
 ('public','atores',array['id']::text[]),
 ('public','equipe_prumo_s1',array['ator_id','cargo','estado']::text[]),
 ('prumo_private','s1_responsaveis_plataforma',array['ator_id','ativo']::text[])
), objects as (
 select e.*,c.oid,c.relkind,c.relrowsecurity,c.relforcerowsecurity,
  (select array_agg(a.attname::text order by a.attname) from pg_catalog.pg_attribute a
   where a.attrelid=c.oid and a.attnum>0 and not a.attisdropped) columns_present
 from expected e
 left join pg_catalog.pg_namespace n on n.nspname=e.schema_name
 left join pg_catalog.pg_class c on c.relnamespace=n.oid and c.relname=e.table_name
)
select pg_catalog.jsonb_build_object(
 'version','prumo.s0s1.ops03.diagnostic.v1',
 'authorizes_action',false,'hosted_homologated',false,
 'transaction_read_only',pg_catalog.current_setting('transaction_read_only'),
 'server_version_num',pg_catalog.current_setting('server_version_num'),
 'session_principal',session_user,'effective_principal',current_user,
 'principal_flags',(select pg_catalog.jsonb_build_object(
   'superuser',r.rolsuper,'bypass_rls',r.rolbypassrls,'create_role',r.rolcreaterole,
   'create_database',r.rolcreatedb) from pg_catalog.pg_roles r where r.rolname=current_user),
 'objects',(select pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
   'schema',schema_name,'relation',table_name,'exists',oid is not null,
   'kind',relkind,'required_columns_present',coalesce(columns_required<@columns_present,false),
   'rls',relrowsecurity,'force_rls',relforcerowsecurity,
   'effective_select',case when oid is not null then pg_catalog.has_table_privilege(oid,'SELECT') else false end,
   'effective_insert',case when oid is not null then pg_catalog.has_table_privilege(oid,'INSERT') else false end,
   'effective_update',case when oid is not null then pg_catalog.has_table_privilege(oid,'UPDATE') else false end,
   'effective_delete',case when oid is not null then pg_catalog.has_table_privilege(oid,'DELETE') else false end
   ) order by schema_name,table_name) from objects),
 'constraints',(select coalesce(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
   'schema',n.nspname,'relation',t.relname,'name',c.conname,'type',c.contype,
   'validated',c.convalidated,'deferrable',c.condeferrable,'initially_deferred',c.condeferred
   ) order by n.nspname,t.relname,c.conname),'[]'::jsonb)
   from pg_catalog.pg_constraint c join pg_catalog.pg_class t on t.oid=c.conrelid
   join pg_catalog.pg_namespace n on n.oid=t.relnamespace where t.oid in(select oid from objects)),
 'essential_professional_constraint',(select count(*)=1 from pg_catalog.pg_trigger
   where tgrelid=pg_catalog.to_regclass('public.equipe_prumo_s1')
   and tgname='s1_i79_professional_commit' and tgenabled<>'D' and tgdeferrable),
 'role_memberships',(select coalesce(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
   'member',m.rolname,'role',r.rolname,'admin_option',a.admin_option)
   order by m.rolname,r.rolname),'[]'::jsonb)
   from pg_catalog.pg_auth_members a join pg_catalog.pg_roles m on m.oid=a.member
   join pg_catalog.pg_roles r on r.oid=a.roleid where m.rolname in
   ('anon','authenticated','service_role','prumo_s1_admin_edge_local','prumo_cfi01_pgtest_login')),
 'private_routines',(select coalesce(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
   'schema',n.nspname,'name',p.proname,'security_definer',p.prosecdef,
   'owner',pg_catalog.pg_get_userbyid(p.proowner),
   'effective_execute',pg_catalog.has_function_privilege(p.oid,'EXECUTE'),
   'public_execute',exists(select 1 from pg_catalog.aclexplode(
     coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a
     where a.grantee=0 and a.privilege_type='EXECUTE'),
   'anon_execute',pg_catalog.has_function_privilege('anon',p.oid,'EXECUTE'),
   'authenticated_execute',pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE'),
   'service_role_execute',pg_catalog.has_function_privilege('service_role',p.oid,'EXECUTE'))
   order by n.nspname,p.proname),'[]'::jsonb)
   from pg_catalog.pg_proc p join pg_catalog.pg_namespace n on n.oid=p.pronamespace
   where n.nspname in('prumo_i86_manual','prumo_ops03_manual')),
 'not_verified',pg_catalog.jsonb_build_array('nominal human identity','organizational authorization',
   'API exposed schemas','Auth service version and supported session mutation',
   'Dashboard SQL connection identity mapping','MFA PAT OAuth custody','hosted installation support')
);
commit;
