"""Evidence for the experimental I29/I30 pair; no application behavior changes."""
import ast
from collections import Counter
import json
import re
from pathlib import Path
import sys
import unittest

UNITS = {
    'I29': ['test_s1_002_i23_http_policy.py', 'test_s1_002_i25_signer_process.py',
            'test_s1_002_i26_independent_auth.py', 'test_s1_002_i27_mtls.py'],
    'I30': ['test_s1_002_i28_cert_lifecycle.py', 'test_s1_002_i29_persistent_revocation.py',
            'test_s1_002_i30_authenticated_authority.py'],
}
E2E = {
    'I29': ('scripts/test_s1_002_i29_persistent_revocation_local.py',
            'S1-002/I29: 105/105 gates E2E GoTrue, HMAC, mTLS e revogacao persistente.'),
    'I30': ('scripts/test_s1_002_i30_signed_authority_local.py',
            'S1-002/I30: 120/120 E2E GoTrue HMAC mTLS com autoridade autenticada local.'),
}

def flatten(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from flatten(test)
        else:
            yield test.id()


def source_markers(source):
    # The first marker includes the number of migration files. Resolve that
    # expression from the same unchanged runners rather than ignoring scenario 01.
    paths = {'supabase/migrations/202610190052_s1_verificacao_sessao_gotrue.sql'}
    for runner in ['scripts/run-s0-local.sh', 'scripts/run-s1-002-local.sh',
                   'scripts/run-s1-002-i12-local.sh']:
        paths.update(re.findall(r'supabase/migrations/[A-Za-z0-9_.-]+\.sql', Path(runner).read_text()))
    def resolve(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return resolve(node.left) + resolve(node.right)
        if ast.unparse(node) == 'str(len(paths))':
            return str(len(paths))
        raise ValueError('Unknown dynamic marker expression; review required')
    markers = []
    for node in ast.walk(ast.parse(Path(source).read_text())):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == 'print' and node.args):
            text = resolve(node.args[0])
            if text.startswith('PASS '):
                markers.append(text)
    return sorted(markers)


def main():
    mode, gate, directory = sys.argv[1:]
    evidence = Path(directory)
    evidence.mkdir(parents=True, exist_ok=True)
    if mode == 'unit':
        all_ids = []
        for filename in UNITS[gate]:
            # A new interpreter per file preserves the controls' process isolation.
            import subprocess
            result = subprocess.run([sys.executable, __file__, 'unit-file', filename, directory])
            if result.returncode:
                raise SystemExit(result.returncode)
            all_ids.extend(json.loads((evidence / (filename + '.json')).read_text()))
        (evidence / 'unit-ids.json').write_text(json.dumps(all_ids, indent=2) + '\n')
        print(f'PASS EXP UNIT {gate}: {len(all_ids)} tests, {len(UNITS[gate])} files')
    elif mode == 'unit-file':
        loader = unittest.TestLoader()
        suite = loader.discover('tests', pattern=gate)
        ids = list(flatten(suite))
        if loader.errors or not ids:
            raise SystemExit('Discovery failed or empty suite')
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful() or result.skipped or result.testsRun != len(ids):
            raise SystemExit('Failed, skipped or missing unit tests')
        (evidence / (gate + '.json')).write_text(json.dumps(ids, indent=2) + '\n')
    elif mode == 'e2e':
        source, final_marker = E2E[gate]
        expected = source_markers(source)
        expected_count = {'I29': 105, 'I30': 120}[gate]
        if len(expected) != expected_count or len(set(expected)) != expected_count:
            raise SystemExit('Source scenario inventory changed; review required')
        log = (evidence.parent / (gate + '-e2e.log')).read_text()
        actual = [line for line in log.splitlines() if line.startswith('PASS ')]
        if Counter(actual) != Counter(expected) or log.splitlines().count(final_marker) != 1:
            raise SystemExit('Missing, duplicate or unexpected E2E scenario markers')
        # Publish only fixed scenario descriptions, never environment files or keys.
        (evidence / 'e2e-markers.json').write_text(json.dumps(expected, indent=2) + '\n')
        print(f'PASS EXP E2E {gate}: {len(expected)} exact scenario markers')
    else:
        raise SystemExit('Unknown evidence mode')


if __name__ == '__main__':
    main()
