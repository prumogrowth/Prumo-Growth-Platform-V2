"""Physical private-material success/failure logging gate before full CI.

No operational key/login, no parameter GRANT, no persistent SQL helper. The
probe role remains NOLOGIN and disappears in the same transaction. A forced
password error and a CHECK error containing real synthetic bytes are caught and
sanitized before propagation; Docker logs and client errors must have no values.
"""
import json
import os
from pathlib import Path
import subprocess
import psycopg
from integration.i83.provision_local import Credential,guard,private_material_transaction,private_password,material_parameter
from scripts.test_s0_cfi01_auth_rest_local import local_env

NAMES=('log_statement','log_parameter_max_length','log_parameter_max_length_on_error','log_min_error_statement','pgaudit.log')

def settings(c):return {n:c.execute('select current_setting(%s,true)',(n,)).fetchone()[0] for n in NAMES}

if __name__=='__main__':
    db=local_env()['DB_URL'];guard(db);value=Credential();stage='LOGGING_GUARD'
    needles=(value.password,value.verifier,value.secret.hex())
    try:
        with psycopg.connect(db) as c:
            before=settings(c)
            (Path(os.environ.get('RUNNER_TEMP','/tmp'))/'prumo_i83_logging_preflight.json').write_text(json.dumps({'status':'CHECKING_EXISTING_PRIVILEGES','settings_before':before},indent=2)+'\n')
            private_material_transaction(c);during=settings(c)
            stage='NONLOGIN_PROBE'
            c.execute('create role prumo_i83_logging_probe nologin noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls')
            private_password(c,value.verifier,'2100-01-01 UTC',probe=True)
            stage='PASSWORD_ERROR_PROBE'
            caught=False
            try:
                with c.transaction():private_password(c,value.verifier,'I83-invalid-timestamp',probe=True)
            except psycopg.Error as error:
                caught=True
                if error.sqlstate!='22007' or any(n in str(error) for n in needles):raise RuntimeError('I83 password error sanitation refused') from None
            if not caught:raise RuntimeError('I83 password fault did not execute')
            stage='ROW_ERROR_PROBE'
            c.execute('create temporary table i83_logging_probe(secret bytea check(octet_length(secret)<0)) on commit drop')
            material_parameter(c,'hmac',value.secret.hex());caught=False
            try:
                with c.transaction():
                    c.execute("""do $row$ begin
                      begin
                        insert into pg_temp.i83_logging_probe(secret) values(decode(current_setting('prumo_i83.hmac'),'hex'));
                      exception when others then
                        raise exception 'I83_KEY_WRITE_FAILED' using errcode=sqlstate;
                      end;
                    end $row$;""")
            except psycopg.Error as error:
                caught=True
                if error.sqlstate!='23514' or any(n in str(error) for n in needles):raise RuntimeError('I83 row error sanitation refused') from None
            if not caught:raise RuntimeError('I83 row fault did not execute')
            c.execute('alter role prumo_i83_logging_probe password null');c.execute('drop role prumo_i83_logging_probe')
        with psycopg.connect(db) as c:
            after=settings(c);assert before==after
            assert not c.execute("select exists(select 1 from pg_roles where rolname='prumo_i83_logging_probe')").fetchone()[0]
            assert all(c.execute('select current_setting(%s,true)',('prumo_i83.'+n,)).fetchone()[0] in(None,'') for n in ('verifier','until','hmac'))
        stage='LOG_SCAN'
        result=subprocess.run(['docker','logs','supabase_db_prumo-s0-auth-ci'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
        if result.returncode:raise RuntimeError('own disposable DB log unavailable')
        for label,needle in zip(('PASSWORD','SCRAM','HMAC'),needles):
            if needle.encode() in result.stdout+result.stderr:raise RuntimeError('I83 material log match kind='+label+' (value withheld)')
        proof={'status':'PASS','postgres_major':17,'settings_before':before,'settings_during_private_material_transaction':during,'settings_after':after,'no_parameter_grant_or_global_role_change':True,'error_logging_threshold_unchanged':before['log_min_error_statement']==during['log_min_error_statement'],'forced_password_error_sanitized':True,'forced_secret_row_check_error_sanitized':True,'nologin_probe_role_removed':True,'no_material_match_in_own_db_log':True,'backend_local_parameters_absent_in_new_session':True}
        (Path(os.environ.get('RUNNER_TEMP','/tmp'))/'prumo_i83_logging_preflight.json').write_text(json.dumps(proof,indent=2)+'\n')
        print('I83-LOGGING-PREFLIGHT PASS: private SCRAM success and forced password/row errors contain no material; existing LOCAL settings restored, error logging threshold unchanged, no new grant, probe role removed',flush=True)
    except Exception as error:
        code=getattr(error,'sqlstate',None)
        code=code if isinstance(code,str) and len(code)==5 and code.isascii() and code.isalnum() else 'UNCLASSIFIED'
        raise SystemExit('I83-LOGGING-PREFLIGHT BLOCKED stage='+stage+' code='+code+' parameter='+getattr(error,'parameter','NONE')+' (values withheld)') from None
