"""Install certified dependency bytes without running scenarios or creating people."""
import json
from pathlib import Path
from local_admin.boundary import ROOT,Blocked
from local_admin.environment import database,discover,checkout

STEPS=[
 ('cfi','supabase/tests/s0_cfi01_s1_038_reference_local_only.sql'),
 ('cfi','supabase/tests/s0_cfi01_human_closure_table_local_only.sql'),
 ('cfi','supabase/tests/s0_cfi01_signed_prerequisite_local_only.sql'),
 ('cfi','supabase/tests/s0_cfi01_atomic_owner_local_only.sql'),
 ('history','supabase/tests/s0_history_session_gate_local_only.sql'),
 ('f02','supabase/tests/s0_f02_review_registry_local_only.sql')]
END=[('g1','supabase/tests/s0_g1_manual_queue_local_only.sql'),
 ('i79',None),('i80','supabase/tests/s1_i80_regularizacao_local_only.sql'),
 ('i81','supabase/tests/s1_i81_admin_ownership_local_only.sql'),
 ('i82','supabase/tests/s1_i82_metadata_fence_local_only.sql')]
FLAGS={'cfi':'cfi01','history':'history','f02':'f02','g1':'g1','i79':'i79','i80':'i80','i81':'i81','i82':'i82'}


def apply(data,flag=None):
    from integration.i83.provision_local import private_material_transaction
    # Original files own BEGIN/COMMIT. Starting the privacy transaction first
    # protects the exact same DDL, including legacy published lab credentials.
    with database() as c:
        private_material_transaction(c)
        if flag:c.execute('select set_config(%s,%s,true)',('prumo.'+FLAGS[flag]+'_disposable','YES'))
        c.execute(data)


def quarantine():
    # Only in this new, owned disposable stack. No account/business-state change.
    with database() as c:
        c.execute("""do $q$ declare r record;begin
          for r in select rolname from pg_roles where rolcanlogin and rolname like 'prumo\\_%' escape '\\'
            and rolname<>'prumo_s1_admin_edge_local'
          loop execute format('alter role %I nologin password null',r.rolname);end loop;
        end $q$;""")
        c.execute('update prumo_private.cfi01_signing_keys_local set active=false')


def install(source_repo,on_step):
    from integration.history.prepare_s1_profile import verify_sources
    from integration.i79.install_local import install_sql
    from integration.i83.provision_local import install as i83_install
    from integration.i83.catalog import snapshot
    checkout();source_repo=Path(source_repo).resolve()
    manifest=json.loads((ROOT/'integration/g1/s1_sources.json').read_text())
    # Verify ALL sources before mutating the first dependency.
    sources=verify_sources(source_repo,manifest)
    with database() as c:
        if c.execute('select count(*) from auth.users').fetchone()[0]:raise Blocked('FRESH_AUTH_REQUIRED')
    for flag,path in STEPS:
        on_step(path);apply((ROOT/path).read_text(),flag)
    for item,data in zip(manifest['files'],sources):
        on_step(item['path']);apply(data.decode())
    for flag,path in END:
        on_step(path or 'I79_VERIFIED_SELECTOR')
        apply((ROOT/path).read_text() if path else install_sql(source_repo),flag)
    on_step('I83_DEDICATED_CUSTODY');i83_install(discover()['DB_URL'])
    on_step('QUARANTINE_SHARED_LAB_LOGINS');quarantine()
    with database() as c:return snapshot(c)
