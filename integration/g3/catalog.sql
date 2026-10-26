-- Metadata only. No business rows or secret values are read.
with relations as (
 select c.*,n.nspname from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where (n.nspname in ('public','prumo_private','prumo_s1_interface')
        or n.nspname like 'prumo_s1_i%') and c.relkind in ('r','p','v','m')
), roles as (
 select rolname from pg_roles where rolname in ('anon','authenticated','service_role',
 'prumo_s0_gateway','prumo_s0_signed_executor','prumo_cfi01_pgtest_login','prumo_cfi01_atomic_owner_local')
)
select jsonb_build_object(
 'server',current_setting('server_version'),
 'storage_objects',to_regclass('storage.objects') is not null,
 'storage_buckets',to_regclass('storage.buckets') is not null,
 'relations',(select jsonb_agg(jsonb_build_object(
  'schema',r.nspname,'name',r.relname,'kind',r.relkind,'owner',pg_get_userbyid(r.relowner),
  'rls',r.relrowsecurity,'force_rls',r.relforcerowsecurity,'options',r.reloptions,
  'acl',r.relacl,
  'columns',(select jsonb_agg(jsonb_build_object('name',a.attname,
   'type',format_type(a.atttypid,a.atttypmod),'not_null',a.attnotnull,'acl',a.attacl,
   'privileges',(select jsonb_object_agg(rolname,jsonb_build_object(
     'select',has_column_privilege(rolname,r.oid,a.attnum,'SELECT'),
     'insert',has_column_privilege(rolname,r.oid,a.attnum,'INSERT'),
     'update',has_column_privilege(rolname,r.oid,a.attnum,'UPDATE'))) from roles)
  ) order by a.attnum) from pg_attribute a where a.attrelid=r.oid and a.attnum>0 and not a.attisdropped),
  'constraints',(select jsonb_agg(jsonb_build_object('name',c.conname,'definition',pg_get_constraintdef(c.oid)) order by c.conname)
   from pg_constraint c where c.conrelid=r.oid),
  'policies',(select jsonb_agg(jsonb_build_object('name',p.policyname,'roles',p.roles,'permissive',p.permissive,
   'command',p.cmd,'using',p.qual,'check',p.with_check) order by p.policyname)
   from pg_policies p where p.schemaname=r.nspname and p.tablename=r.relname)
 ) order by r.nspname,r.relname) from relations r),
 'functions',(select jsonb_agg(jsonb_build_object('schema',n.nspname,'name',p.proname,
  'arguments',pg_get_function_identity_arguments(p.oid),'owner',pg_get_userbyid(p.proowner),
  'security_definer',p.prosecdef,'config',p.proconfig,'acl',p.proacl)
  order by n.nspname,p.proname,p.oid)
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname in ('prumo_private','prumo_s1_interface') or n.nspname like 'prumo_s1_i%')
)::text;
