"""Publish bounded runtime diagnostics only, never env files or credentials."""
import os,re
from pathlib import Path

root=Path(os.environ.get('RUNNER_TEMP','/tmp'))
file=root/'prumo_i82_runtime.log'
if file.exists():
    lines=[]
    for line in file.read_text(errors='replace').splitlines():
        if not re.search('error|fail|boot|Listening|Serving|Using|worker|version|shutdown',line,re.I):continue
        line=re.sub(r'postgres(?:ql)?://\S+','[SQL_URL_REDACTED]',line)
        line=re.sub(r'[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}','[JWT_REDACTED]',line)
        line=re.sub(r'\b[0-9a-f]{64,}\b','[HEX_REDACTED]',line)
        lines.append(line[:500])
    (root/'prumo_i82_runtime_sanitized.txt').write_text('\n'.join(lines[-40:])+'\n')
    print('\n'.join(lines[-12:]),flush=True)
