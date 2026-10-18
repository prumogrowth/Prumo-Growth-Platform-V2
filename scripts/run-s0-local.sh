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
for file in supabase/tests/bootstrap_fake_auth.sql supabase/migrations/202610170001_s0_foundation.sql supabase/migrations/202610170002_s0_read_policies.sql supabase/migrations/202610170003_s0_domain.sql supabase/migrations/202610170004_s0_access.sql supabase/migrations/202610170005_s0_scope_integrity.sql supabase/migrations/202610170006_s0_transactional_simulation.sql supabase/migrations/202610170008_s0_lead_operador_caso.sql supabase/migrations/202610170009_s0_c02_inbound_synthetic.sql supabase/migrations/202610170010_s0_channel_validation.sql supabase/migrations/202610170011_s0_c02_ambiguous_inbox.sql supabase/migrations/202610170012_s0_recontatos_sinteticos.sql supabase/migrations/202610170013_s0_c02_cancelamento_atomico.sql supabase/migrations/202610170014_s0_cancelamento_gestor_versionado.sql supabase/migrations/202610170015_auditoria_recontatos.sql supabase/migrations/202610170016_c04_elegibilidade_optout_sintetico.sql supabase/migrations/202610170017_c04_estado_replay_plano.sql supabase/migrations/202610170018_c04_inbound_pos_optout_humano.sql supabase/migrations/202610170019_c07_callbacks_sinteticos.sql supabase/migrations/202610170020_c07_reconciliacao_falhas_sintetica.sql supabase/migrations/202610170021_c07_bloqueio_retry_incertos.sql supabase/migrations/202610170022_c07_auditoria_replay_eligibilidade.sql supabase/migrations/202610170023_s0_gateway_minimo_e_auditoria.sql supabase/tests/s0_isolation.sql supabase/tests/s0_extended.sql supabase/tests/s0_transactional.sql supabase/tests/s0_c02_inbound.sql supabase/tests/s0_recontatos.sql supabase/tests/s0_recontatos_gestor.sql supabase/tests/s0_auditoria_recontatos.sql supabase/tests/s0_c04_elegibilidade_optout.sql supabase/tests/s0_c04_replay_plano.sql supabase/tests/s0_c07_callbacks.sql supabase/tests/s0_c07_reconciliacao.sql supabase/tests/s0_gateway_privilegios.sql; do
 psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/$file"
done
bash "$ROOT/scripts/test_s0_concurrency.sh"
bash "$ROOT/scripts/test_s0_cross_shop.sh"
bash "$ROOT/scripts/test_s0_c02_concurrency.sh"
bash "$ROOT/scripts/test_s0_recontato_race.sh"
bash "$ROOT/scripts/test_s0_c04_optout_race.sh"
bash "$ROOT/scripts/test_s0_c07_recon_concurrency.sh"
echo 'Teste local concluído. Não houve escrita no Supabase.'
