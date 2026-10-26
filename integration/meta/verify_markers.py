#!/usr/bin/env python3
"""Verify every historical marker exactly once, not just a green last step."""
from collections import Counter
import json
from pathlib import Path
import re
import sys

manifest = json.loads(Path(__file__).with_name('source_manifest.json').read_text())
log = Path(sys.argv[1]).read_text()
# SQL RAISE NOTICE markers carry a psql filename/line prefix; Node 22 uses
# TAP '# ', while Node 24 prints raw console output. Count all three forms.
actual = Counter(re.findall(r'(?m)^(?:psql:[^\n]+?NOTICE:  |# )?(WA\d\d-(?:R)?\d\d) PASS[ \t]*$', log))
expected = {f'WA{wa}-{i:02}' for wa, count in enumerate(manifest['wa_counts'], 39)
            for i in range(1, count + 1)}
expected |= {f'WA42-R{i:02}' for i in range(1, 12)}
assert set(actual) == expected, (sorted(expected - set(actual)), sorted(set(actual) - expected))
assert all(value == 1 for value in actual.values()), actual
assert len(expected) == 823
print('META-REGRESSION: 823/823 individual WA39–WA68 markers exactly once')
