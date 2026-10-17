#!/usr/bin/env bash
set -euo pipefail
: "${PRUMO_TEST_DATABASE_URL:?Defina URL LOCAL descartável com nome prumo_s0_test_*}"
command -v psql >/dev/null || { echo 'psql não instalado'; exit 2; }
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
name=unquote((u.path or '').strip('/'))
if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1','::1') or not name.startswith('prumo_s0_test_'):
 sys.exit('RECUSADO: apenas PostgreSQL LOCAL descartável prumo_s0_test_*')
PY
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for file in supabase/tests/bootstrap_fake_auth.sql supabase/migrations/202610170001_s0_foundation.sql supabase/migrations/202610170002_s0_read_policies.sql supabase/migrations/202610170003_s0_domain.sql supabase/migrations/202610170004_s0_access.sql supabase/migrations/202610170005_s0_scope_integrity.sql supabase/migrations/202610170006_s0_transactional_simulation.sql supabase/migrations/202610170007_s0_exclusividade_telefone.sql supabase/migrations/202610170008_s0_lead_operador_caso.sql supabase/tests/s0_isolation.sql supabase/tests/s0_extended.sql supabase/tests/s0_transactional.sql; do
 psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/$file"
done
bash "$ROOT/scripts/test_s0_concurrency.sh"
echo 'Teste local concluído. Não houve escrita no Supabase.'
