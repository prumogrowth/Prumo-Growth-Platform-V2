"""Disable only the disposable Functions service's default wildcard CORS.

The pinned CLI Kong template otherwise overwrites the handler's CORS header and
short-circuits OPTIONS. No Auth/REST/request-transformer configuration is changed.
Never print the declarative config: it contains synthetic bearer credentials.
"""
import os
import subprocess

CONTAINER='supabase_kong_prumo-s0-auth-ci'
CONFIG='/home/kong/kong.yml'


def _read():
    return subprocess.check_output(['docker','exec',CONTAINER,'cat',CONFIG])


def _load(content):
    result=subprocess.run(['docker','exec','-i',CONTAINER,'sh','-c',
        'cat > /home/kong/kong.yml && kong reload --nginx-conf /home/kong/custom_nginx.template'],
        input=content,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
    if result.returncode:raise RuntimeError('I82 own disposable gateway reload failed (configuration withheld)')


def configure():
    if os.environ.get('PRUMO_I82_DISPOSABLE_TEST')!='YES':raise RuntimeError('I82 gateway local opt-in required')
    before=_read()
    start=before.index(b'\n  - name: functions-v1\n')
    # Next service begins after the Functions block in the pinned CLI template.
    end=before.index(b'\n  - name: ',start+len(b'\n  - name: functions-v1\n'))
    block=before[start:end]
    cors=b'      - name: cors\n'
    if block.count(cors)!=1 or b'      - name: request-transformer\n' not in block:
        raise RuntimeError('I82 unexpected pinned Functions gateway template')
    after=before[:start]+block.replace(cors,b'',1)+before[end:]
    try:
        _load(after)
        if _read()!=after:raise RuntimeError('I82 disposable gateway readback mismatch')
    except BaseException:
        _load(before)
        raise
    def restore():
        _load(before)
        if _read()!=before:raise RuntimeError('I82 disposable gateway restoration mismatch')
    return restore
