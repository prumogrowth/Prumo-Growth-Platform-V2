"""I79 delta; uses S0's original disposable-loopback environment guard."""
import os
from pathlib import Path
import psycopg
import hashlib
from scripts.test_s0_cfi01_auth_rest_local import local_env

def install_sql(source_repo=None):
    # Minimal, checked adaptation of the ORIGINAL I54 automatic selector.
    # New eligibility must skip unknown roles instead of failing on the first
    # legacy candidate and starving correctly registered consultants.
    path=Path(source_repo or os.environ['PRUMO_G1_SOURCE_REPO'])/'supabase/migrations/202610190054_s0_fila_humana_canonica.sql'
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!='52fb8ff13ae2c5508f2e80783fa27c7534f4ed23be3895a69abff99e4348443f':raise RuntimeError('I79_SOURCE_HASH_MISMATCH')
    fn=data.decode().split('create function prumo_private.s0_fila_distribuir(',1)[1].split('\nrevoke all on function',1)[0]
    fn='create or replace function prumo_private.s0_fila_distribuir('+fn
    needle="where e.estado='ativo' and coalesce(d.pausado,false)=false"
    if fn.count(needle)!=1:raise RuntimeError('I79_SELECTOR_MISMATCH')
    fn=fn.replace(needle,"where e.estado='ativo' and e.cargo='consultor' and chefe.cargo='gestor' and coalesce(d.pausado,false)=false")
    delta=Path('supabase/tests/s1_i79_profissionais_local_only.sql').read_text()
    if not delta.endswith('commit;\n'):raise RuntimeError('I79_TRANSACTION_MISMATCH')
    return delta[:-len('commit;\n')]+fn+'\ncommit;\n'

def main():
    if os.environ.get('PRUMO_I79_DISPOSABLE_TEST')!='YES':raise RuntimeError('I79 opt-in required')
    with psycopg.connect(local_env()['DB_URL'],autocommit=True) as c:
        c.execute("set prumo.i79_disposable='YES'")
        c.execute(install_sql())
    print('I79 installed in disposable PG17: authoritative cargo, deferred chefia and signed Director administration',flush=True)

if __name__=='__main__':main()
