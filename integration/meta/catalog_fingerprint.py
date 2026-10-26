"""Hash catalog/role/ACL state without exposing row contents or passwords."""
import hashlib
import subprocess


def fingerprint(dsn):
    queries = [
        "select row(oid,nspname,nspowner,nspacl)::text from pg_namespace order by oid",
        "select row(oid,relname,relnamespace,relowner,relacl,relrowsecurity)::text from pg_class order by oid",
        "select row(oid,proname,pronamespace,proowner,proacl,prosrc,proconfig,prosecdef)::text from pg_proc order by oid",
        "select row(oid,rolname,rolcanlogin,rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolinherit,rolreplication)::text from pg_roles order by oid",
        "select row(roleid,member,grantor,admin_option,inherit_option,set_option)::text from pg_auth_members order by roleid,member,grantor",
        "select row(oid,defaclrole,defaclnamespace,defaclobjtype,defaclacl)::text from pg_default_acl order by oid",
        "select row(oid,polname,polrelid,polroles,polqual,polwithcheck)::text from pg_policy order by oid",
        "select row(oid,tgrelid,tgname,tgfoid,tgtype,tgenabled,tgisinternal,tgqual)::text from pg_trigger order by oid",
        "select row(oid,conname,connamespace,contype,conrelid,conkey,confrelid,confkey)::text from pg_constraint order by oid",
    ]
    output = subprocess.check_output(['psql', '-XqAt', '-v', 'ON_ERROR_STOP=1',
                                      dsn, '-c', ';'.join(queries)])
    return hashlib.sha256(output).hexdigest()
