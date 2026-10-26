"""Issue #10: fixed Git snapshots -> disposable offline PG17, never hosted SQL.

Requires Docker local socket and the pinned image already present. No pull,
ports, volumes, DSN, tokens, providers or edits to other branches. Synthetic
auth.uid/session fixtures are NOT GoTrue/PostgREST authentication evidence.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'postgres@sha256:b8faeff7712663c2773a190181e1246e37e364b887611c04658c28b44e2408fe'
REFS = {
 's0': '060b472b03e9e7b89f5b3d7e19b72b98836f106d',
 's1': 'e868b5dbd98b107f4ebd3f9f7087e24ec8518dbe',
 'p9': 'ff623482fca0eb1857a64b51959e3716bc0216d7',
 'f03': 'a7ba0136ae7c7907cc5b7f9ad0ee6b6ae499125e',
}


def command(args, data=None):
    result=subprocess.run(args, input=data, text=True, capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError(f'local command failed ({result.returncode}): {result.stderr[-2500:]}')
    return result.stdout


def source(ref, path):
    return command(['git','-C',str(ROOT),'show',f'{ref}:{path}'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--profiles',nargs='+',choices=REFS,default=list(REFS))
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    # Prevent inherited Docker selectors from redirecting to a remote daemon.
    for key in ('DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH'):
        os.environ.pop(key,None)
    docker=['docker','--host=unix:///var/run/docker.sock']
    command(docker+['image','inspect',IMAGE,'--format','{{.Id}}'])
    summary={}
    for profile in args.profiles:
        ref=REFS[profile]
        name='prumo-issue10-'+uuid.uuid4().hex[:12]
        db='prumo_s0_test_cfi01' if profile in ('p9','f03') else 'prumo_s0_test_g3_'+profile
        applied=[]
        try:
            command(docker+['run','--detach','--name',name,'--network','none',
                '--label','prumo.task=issue10-g3','--tmpfs','/var/lib/postgresql/data:rw',
                '-e','POSTGRES_HOST_AUTH_METHOD=trust','-e','POSTGRES_DB='+db,IMAGE])
            for attempt in range(60):
                # Docker's temporary init server listens only on its Unix
                # socket; TCP loopback readiness identifies the final server.
                ready=subprocess.run(docker+['exec',name,'pg_isready','-h','127.0.0.1','-U','postgres','-d',db],capture_output=True)
                if ready.returncode==0: break
                time.sleep(.3)
            else: raise RuntimeError('local PG17 not ready')
            def sql(text,user='postgres'):
                return command(docker+['exec','-i',name,'psql','-X','-qAt','-v','ON_ERROR_STOP=1','-U',user,'-d',db],text)
            def load(path, from_ref=ref):
                sql(source(from_ref,path));applied.append({'ref':from_ref,'path':path})
            load('supabase/tests/bootstrap_fake_auth.sql')
            # Minimal synthetic auth.sessions, distinct from managed GoTrue.
            sql('create table auth.sessions(id uuid primary key,user_id uuid not null references auth.users(id),not_after timestamptz);')
            files=command(['git','-C',str(ROOT),'ls-tree','-r','--name-only',ref,'supabase/migrations']).splitlines()
            for path in sorted(files):
                if path.endswith('.sql'): load(path)
            if profile in ('p9','f03'):
                for path in ('s0_cfi01_s1_038_reference_local_only.sql','s0_cfi01_human_closure_table_local_only.sql',
                             's0_cfi01_signed_prerequisite_local_only.sql'):
                    load('supabase/tests/'+path)
                # Each session must explicitly opt in to the hardened installer.
                sql("set prumo.cfi01_disposable='YES';"+source(ref,'supabase/tests/s0_cfi01_atomic_owner_local_only.sql'))
                applied.append({'ref':ref,'path':'supabase/tests/s0_cfi01_atomic_owner_local_only.sql'})
            if profile=='f03':
                for part in ('message_modalities','history_seal','versions_reservation','version_source_triggers',
                             'operational_contracts','field_application','media_attestation'):
                    load('supabase/tests/s0_f03_'+part+'_local_only.sql')
            catalog=json.loads(sql((ROOT/'integration/g3/catalog.sql').read_text()))
            (args.output/(profile+'-catalog.json')).write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
            if profile=='s1':
                candidate_catalog=json.loads(sql('begin;'+source(ref,'supabase/tests/s1_087_rls_excecao_canonica_local_only.sql')+
                    (ROOT/'integration/g3/catalog.sql').read_text()+'rollback;'))
                (args.output/'s1-i63-candidate-catalog.json').write_text(json.dumps(candidate_catalog,ensure_ascii=False,indent=2)+'\n')
            if profile in ('s0','s1'):
                candidate=profile=='s1'
                probe=(ROOT/'integration/g3/negative_history.sql').read_text()
                probe=probe.replace('-- INSTALL_CANDIDATE_HERE',source(ref,'supabase/tests/s1_087_rls_excecao_canonica_local_only.sql') if candidate else '')
                probe=probe.replace('CANDIDATE_BOOLEAN','true' if candidate else 'false')
                if candidate:
                    probe=probe.replace('-- TEAM_SEED_HERE',
                      "insert into public.equipe_prumo_s1(ator_id,estado) select id,'ativo' from public.atores;\n"
                      "insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values\n"
                      "('a1000000-0000-4000-8000-000000000003','a1000000-0000-4000-8000-000000000001'),\n"
                      "('a1000000-0000-4000-8000-000000000004','a1000000-0000-4000-8000-000000000002');")
                result=sql(probe)
                (args.output/(profile+'-negative.log')).write_text(result)
                after=json.loads(sql((ROOT/'integration/g3/catalog.sql').read_text()))
                if after!=catalog: raise AssertionError('probe changed persistent catalog')
                if sql("select count(*) from public.concessionarias where id::text like 'a2%'").strip()!='0':
                    raise AssertionError('probe rows survived rollback')
                summary[profile]={'ref':ref,'markers':[x for x in result.splitlines() if x.startswith(('PASS','GAP'))],
                                  'catalog_unchanged_after_rollback':True,'synthetic_rows_removed':True}
            else:
                result=sql((ROOT/'integration/g3/negative_private.sql').read_text().replace('F03_BOOLEAN','true' if profile=='f03' else 'false'))
                result+=sql((ROOT/'integration/g3/negative_login.sql').read_text(),user='prumo_cfi01_pgtest_login')
                (args.output/(profile+'-negative.log')).write_text(result)
                summary[profile]={'ref':ref,'markers':[x for x in result.splitlines() if x.startswith('PASS')]}
            summary[profile]['applied_sources']=applied
            summary[profile]['server']=catalog['server']
            summary[profile]['markers']+=[]
            print(profile,summary[profile]['markers'],flush=True)
        finally:
            # Failure to remove the specific container is also an error.
            command(docker+['rm','--force',name])
    (args.output/'execution.json').write_text(json.dumps({'image':IMAGE,'authentication':'synthetic SQL; no GoTrue/PostgREST',
        'profiles':summary,'containers_removed':True},ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__': main()
