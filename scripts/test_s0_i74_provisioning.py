"""I74 provisioning probes on I73 ephemeral GoTrue stack; called before I74."""
from pathlib import Path
import psycopg

assert os.environ.get('CI')=='true' and os.environ.get('PRUMO_S1_I37_EPHEMERAL')=='YES'
_snapshot="""select jsonb_build_object(
 'memberships',(select coalesce(jsonb_agg(jsonb_build_array(m.member,m.grantor,m.admin_option,m.inherit_option,m.set_option) order by m.member,m.grantor),'[]') from pg_auth_members m where m.roleid='prumo_s1_export_executor'::regrole),
 'signed_role',to_regrole('prumo_s1_export_signed_login_ci')::text,
 'function',to_regprocedure('prumo_export_auth.exportar_assinado_i74(uuid,uuid,text,uuid,uuid,integer,uuid,bigint,uuid,text)')::text,
 'keys',to_regclass('prumo_export_auth.chaves_i74')::text,
 'nonces',to_regclass('prumo_export_auth.nonces_i74')::text,
 'create',has_schema_privilege('prumo_s1_export_executor','prumo_export_auth','CREATE'))"""
with psycopg.connect(db,autocommit=True) as probe:
 before=probe.execute(_snapshot).fetchone()[0]
 superuser=probe.execute("select rolsuper from pg_roles where rolname=current_user").fetchone()[0]
 # Confirm root cause without leaving SET ROLE or partial original installation.
 if not superuser:
  try:
   with probe.transaction():
    probe.execute('set local role prumo_s1_export_executor')
    raise AssertionError('I74_UNEXPECTED_PREINSTALL_SET')
  except psycopg.errors.InsufficientPrivilege:
   pass
  print('PASS I74-PROV-01: non-superuser installer initially cannot SET executor')
 else:
  print('PASS I74-PROV-01: superuser PG control; restrictive precondition only applies to Supabase')
 source=Path('supabase/tests/s1_108_export_signed_executor_local_only.sql').read_text()
 assert source.count('set role prumo_s1_export_executor;')==1
 faulty=source.replace('set role prumo_s1_export_executor;',
                        'set role prumo_s1_export_executor;\nperform 1/0;',1)
 try:
  # Autocommit is essential: rollback must come from the installer's one atomic
  # statement, not a test transaction masking grants left by failed statements.
  probe.execute(faulty)
  raise AssertionError('I74_INSTALL_FAILURE_NOT_INJECTED')
 except psycopg.errors.DivisionByZero:
  pass
 assert probe.execute(_snapshot).fetchone()[0]==before
 assert probe.execute('select current_user').fetchone()[0]=='postgres'
 print('PASS I74-PROV-02: injected failure restores roles/grants/schema in autocommit')
# Save only catalog-derived initial membership for post-install exact comparison.
_i74_installer_before=before['memberships']
