"""Fast physical Supabase PG17 logging gate, before the full integration suite.

No operational key/login is created until existing installer privileges can
protect material from logging. All settings are LOCAL; no new grant/ACL/role
configuration, business guard or audit table is changed.
"""
import json
import os
from pathlib import Path
import subprocess
import psycopg
from psycopg import sql
from integration.i83.provision_local import Credential,guard,private_material_transaction
from scripts.test_s0_cfi01_auth_rest_local import local_env

NAMES=('log_statement','log_parameter_max_length','log_parameter_max_length_on_error','log_min_error_statement','pgaudit.log')

def settings(c):return {n:c.execute('select current_setting(%s,true)',(n,)).fetchone()[0] for n in NAMES}

if __name__=='__main__':
    db=local_env()['DB_URL'];guard(db);value=Credential();stage='LOGGING_GUARD'
    try:
        with psycopg.connect(db) as c:
            before=settings(c);private_material_transaction(c);during=settings(c)
            stage='NONLOGIN_PROBE'
            c.execute(sql.SQL('create role prumo_i83_logging_probe nologin noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls password {}').format(sql.Literal(value.verifier)))
            c.execute('create temporary table i83_logging_probe(secret bytea) on commit drop')
            c.execute('insert into i83_logging_probe(secret) values (%s)',(value.secret,))
            c.execute('alter role prumo_i83_logging_probe password null')
            c.execute('drop role prumo_i83_logging_probe')
        with psycopg.connect(db) as c:
            after=settings(c);assert before==after
            assert not c.execute("select exists(select 1 from pg_roles where rolname='prumo_i83_logging_probe')").fetchone()[0]
        stage='LOG_SCAN'
        result=subprocess.run(['docker','logs','supabase_db_prumo-s0-auth-ci'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
        if result.returncode:raise RuntimeError('own disposable DB log unavailable')
        for label,needle in zip(('PASSWORD','SCRAM','HMAC'),(value.password,value.verifier,value.secret.hex())):
            if needle.encode() in result.stdout+result.stderr:raise RuntimeError('I83 material log match kind='+label+' (value withheld)')
        proof={'status':'PASS','postgres_major':17,'settings_before':before,'settings_during_private_material_transaction':during,'settings_after':after,'no_parameter_grant_or_global_role_change':True,'nologin_probe_role_removed':True,'no_material_match_in_own_db_log':True}
        (Path(os.environ.get('RUNNER_TEMP','/tmp'))/'prumo_i83_logging_preflight.json').write_text(json.dumps(proof,indent=2)+'\n')
        print('I83-LOGGING-PREFLIGHT PASS: existing installer privilege, LOCAL settings restored, nonlogin SCRAM and binary material absent from DB log, probe role removed',flush=True)
    except Exception as error:
        code=getattr(error,'sqlstate',None)
        code=code if isinstance(code,str) and len(code)==5 and code.isascii() and code.isalnum() else 'UNCLASSIFIED'
        # Deliberately no server error/detail/configuration or credential output.
        raise SystemExit('I83-LOGGING-PREFLIGHT BLOCKED stage='+stage+' code='+code+' (values withheld)') from None
