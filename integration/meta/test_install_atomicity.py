#!/usr/bin/env python3
"""Run an actual fixture install, fail AFTER DDL/grants, prove full rollback.

Called just before each normal installation, with its real dependencies ready.
Only the final COMMIT is prefixed by an injected division-by-zero statement.
"""
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

from catalog_fingerprint import fingerprint

dsn = os.environ['PRUMO_TEST_DATABASE_URL']
url = urlsplit(dsn)
assert url.scheme == 'postgresql' and url.hostname == '127.0.0.1' and url.port == 5432
assert url.path == '/prumo_s0_test_ci' and url.username == 'postgres'
assert not url.query and not url.fragment
for name in ('PGHOSTADDR', 'PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER',
             'PGSERVICE', 'PGSERVICEFILE', 'PGOPTIONS'):
    assert not os.environ.get(name), name
file = Path(sys.argv[1])
assert file.name.startswith('2026102300') and file.suffix == '.sql'
source = file.read_text()
assert source.startswith('begin;\n') and source.endswith('\ncommit;\n')
faulty = source[:-len('commit;\n')] + 'select 1/0;\ncommit;\n'
before = fingerprint(dsn)
result = subprocess.run(['psql', '-Xq', '-v', 'ON_ERROR_STOP=1', '-v',
                         'VERBOSITY=verbose', dsn], input=faulty,
                        capture_output=True, text=True)
assert result.returncode and '22012' in result.stderr, result.stderr[-600:]
assert fingerprint(dsn) == before, file.name
print('META-ATOMIC-' + file.name[10:12] + ' PASS: injected failure after DDL/grants rolled back', flush=True)
