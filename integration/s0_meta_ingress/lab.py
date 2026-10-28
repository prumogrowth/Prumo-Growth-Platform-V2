"""Owns exactly one random container, volume, loopback port and ephemeral custody directory."""
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import tempfile
import time
import uuid
import psycopg
from psycopg.rows import dict_row
from psycopg import sql

IMAGE='postgres:17.6-bookworm@sha256:f3bd19c606e442c3d7bdfa8002e03fe260a1023351e0ea4598032022b68dd6e3'

class Laboratory:
    def __init__(self):
        self.name='s0-meta-ingress-01-'+uuid.uuid4().hex
        self.volume=self.name+'-wal'
        self.folder=Path(tempfile.mkdtemp(prefix='s0-meta-ingress-01-',dir=os.environ.get('S0_META_WORK','/tmp')))
        self.admin_password=secrets.token_urlsafe(32)
        self.runtime_password=secrets.token_urlsafe(32)
        self.started=False

    def docker(self,*args,check=True):
        env=os.environ.copy()
        for k in ('DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH'):
            env.pop(k,None)
        return subprocess.run(['docker','--host=unix:///var/run/docker.sock',*args],env=env,check=check,
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)

    def start(self):
        self.folder.chmod(0o700)
        envfile=self.folder/'postgres.env'
        envfile.write_text('POSTGRES_PASSWORD='+self.admin_password+'\nPOSTGRES_DB=s0_meta_ingress_lab\n')
        envfile.chmod(0o600)
        self.docker('volume','create','--label','prumo.lab=s0-meta-ingress-01',self.volume)
        with socket.socket() as reservation:
            reservation.bind(('127.0.0.1',0))
            self.port=reservation.getsockname()[1]
        self.docker('run','--detach','--name',self.name,'--label','prumo.lab=s0-meta-ingress-01',
                    '--publish',f'127.0.0.1:{self.port}:5432','--env-file',str(envfile),
                    '--mount','type=volume,source='+self.volume+',target=/var/lib/postgresql/data',
                    IMAGE,'-c','fsync=on','-c','full_page_writes=on','-c','synchronous_commit=on',
                    '-c','log_error_verbosity=terse','-c','log_statement=none','-c','log_min_error_statement=panic')
        self.started=True
        port=self.docker('port',self.name,'5432/tcp').stdout.strip().rsplit(':',1)[1]
        self.admin_dsn=f'host=127.0.0.1 port={port} dbname=s0_meta_ingress_lab user=postgres password={self.admin_password}'
        self.runtime_dsn=f'host=127.0.0.1 port={port} dbname=s0_meta_ingress_lab user=s0_meta_runtime password={self.runtime_password}'
        self.wait()
        with self.admin() as c:
            self.catalog_before=self.catalog(c)
            c.execute("SET s0_meta.disposable='YES'")
            c.execute(Path('integration/s0_meta_ingress/schema.sql').read_text())
            c.execute(sql.SQL('ALTER ROLE s0_meta_runtime PASSWORD {}').format(sql.Literal(self.runtime_password)))
            self.pg=c.execute("SELECT version() AS version,current_setting('fsync') AS fsync,current_setting('synchronous_commit') AS synchronous_commit,current_setting('full_page_writes') AS full_page_writes").fetchone()
        return self

    def admin(self):
        return psycopg.connect(self.admin_dsn,row_factory=dict_row,connect_timeout=3,
                               options='-c search_path=s0_meta_lab,pg_catalog')

    def wait(self):
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            try:
                with self.admin(): return
            except psycopg.OperationalError:time.sleep(.2)
        raise RuntimeError('laboratory PostgreSQL unavailable')

    @staticmethod
    def catalog(c):
        return c.execute("""SELECT n.nspname,c.relname,c.relkind,c.relacl::text FROM pg_class c
          JOIN pg_namespace n ON n.oid=c.relnamespace
          WHERE n.nspname <> 's0_meta_lab' AND n.nspname NOT LIKE 'pg_toast%' AND n.nspname NOT LIKE 'pg_temp%'
          ORDER BY n.nspname,c.relname""").fetchall()

    def crash_restart(self):
        if not self.name.startswith('s0-meta-ingress-01-'):
            raise RuntimeError('resource ownership')
        self.docker('kill','--signal=KILL',self.name)
        self.docker('start',self.name)
        self.wait()
        logs=self.docker('logs',self.name).stderr
        if 'database system was interrupted' not in logs or 'redo' not in logs:
            raise RuntimeError('WAL recovery not observed')

    def cleanup(self):
        report={'container_absent':False,'volume_absent':False,'custody_absent':False}
        if self.started:
            try:
                with self.admin() as c:
                    report['inherited_catalog_equal']=self.catalog_before==self.catalog(c)
            except Exception:
                report['inherited_catalog_equal']=False
            finally:
                self.docker('rm','--force','--volumes',self.name)
        self.docker('volume','rm',self.volume,check=False)
        report['container_absent']=self.docker('inspect',self.name,check=False).returncode!=0
        report['volume_absent']=self.docker('volume','inspect',self.volume,check=False).returncode!=0
        shutil.rmtree(self.folder)
        report['custody_absent']=not self.folder.exists()
        self.admin_password=self.runtime_password=None
        return report
