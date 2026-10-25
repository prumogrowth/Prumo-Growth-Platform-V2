#!/usr/bin/env bash
set -euo pipefail
: "${PRUMO_TEST_DATABASE_URL:?Defina URL LOCAL descartável com nome prumo_s0_test_*}"
command -v psql >/dev/null || { echo 'psql não instalado'; exit 2; }
python3 - <<'PY'
import os,re,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
name=unquote((u.path or '')[1:]) if (u.path or '').startswith('/') else ''
if (u.scheme not in ('postgres','postgresql')
    or u.hostname not in ('localhost','127.0.0.1','::1')
    or not re.fullmatch(r'prumo_s0_test_[a-z0-9_]{1,40}',name)
    or u.query or u.fragment or u.params):
 sys.exit('RECUSADO: PostgreSQL local descartável; URL sem query/hostaddr/service')
PY
# libpq PGHOSTADDR can silently override even a URI that says localhost.
# All child concurrency scripts inherit this scrubbed environment.
unset PGHOSTADDR PGHOST PGPORT PGDATABASE PGUSER PGSERVICE PGSERVICEFILE PGOPTIONS PGSSLMODE PGSSLCERT PGSSLKEY PGSSLROOTCERT
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Fail before applying any migration on wrong PostgreSQL version/database.
# Synthetic negative tests do not contact a database.
bash "$ROOT/scripts/test_s0_pg17_preflight.sh"
bash "$ROOT/scripts/check_s0_pg17.sh"
for file in supabase/tests/bootstrap_fake_auth.sql supabase/migrations/202610170001_s0_foundation.sql supabase/migrations/202610170002_s0_read_policies.sql supabase/migrations/202610170003_s0_domain.sql supabase/migrations/202610170004_s0_access.sql supabase/migrations/202610170005_s0_scope_integrity.sql supabase/migrations/202610170006_s0_transactional_simulation.sql supabase/migrations/202610170008_s0_lead_operador_caso.sql supabase/migrations/202610170009_s0_c02_inbound_synthetic.sql supabase/migrations/202610170010_s0_channel_validation.sql supabase/migrations/202610170011_s0_c02_ambiguous_inbox.sql supabase/migrations/202610170012_s0_recontatos_sinteticos.sql supabase/migrations/202610170013_s0_c02_cancelamento_atomico.sql supabase/migrations/202610170014_s0_cancelamento_gestor_versionado.sql supabase/migrations/202610170015_auditoria_recontatos.sql supabase/migrations/202610170016_c04_elegibilidade_optout_sintetico.sql supabase/migrations/202610170017_c04_estado_replay_plano.sql supabase/migrations/202610170018_c04_inbound_pos_optout_humano.sql supabase/migrations/202610170019_c07_callbacks_sinteticos.sql supabase/migrations/202610170020_c07_reconciliacao_falhas_sintetica.sql supabase/migrations/202610170021_c07_bloqueio_retry_incertos.sql supabase/migrations/202610170022_c07_auditoria_replay_eligibilidade.sql supabase/migrations/202610170023_s0_gateway_minimo_e_auditoria.sql supabase/migrations/202610170024_s0_auditoria_sessao_fingerprint.sql supabase/migrations/202610170025_s0_prova_dupla_gateway.sql supabase/migrations/202610180026_s0_ciclo_chaves_e_retencao_nonce.sql supabase/migrations/202610180027_s0_isolamento_verificador_hmac.sql supabase/migrations/202610180028_s0_identidade_aliases_sinteticos.sql supabase/migrations/202610180029_s0_inbox_outbox_sinteticos.sql supabase/migrations/202610180030_s0_replay_multicanal_fixture.sql supabase/migrations/202610180031_s0_c01_alias_importacao_sintetica.sql supabase/migrations/202610180032_s0_ciclo_tarefas_ingresso.sql supabase/migrations/202610180033_s0_inbox_aplicacao_c02_atomica.sql supabase/migrations/202610180034_s0_integridade_c02_e_pendencias.sql supabase/migrations/202610180036_s0_owner_gateway_assinado.sql supabase/migrations/202610180037_s0_036a_acl_audit_repair.sql supabase/migrations/202610190040_s0_meta_canal_emissor_unico_fixture.sql supabase/migrations/202610190041_s0_meta_vinculo_tentativa_fixture.sql supabase/migrations/202610200042_s0_wa15_meta_ids_tecnicos_fixture.sql supabase/migrations/202610230043_s0_meta_status_forense_fixture.sql supabase/migrations/202610230044_s0_meta_handoff_assinado_fixture.sql supabase/migrations/202610230045_s0_meta_isolar_verificador_fixture.sql supabase/migrations/202610230046_s0_meta_key_revocation_lock_fixture.sql supabase/migrations/202610230047_s0_meta_shadow_non_superuser_fixture.sql supabase/migrations/202610230048_s0_meta_scoped_non_superuser_fixture.sql supabase/migrations/202610230049_s0_meta_restricted_authoritative_forensic_fixture.sql supabase/migrations/202610230050_s0_meta_forensic_conflict_parity_fixture.sql supabase/migrations/202610230051_s0_meta_outbox_lock_cancel_race_fixture.sql supabase/migrations/202610230052_s0_meta_lock_order_repair_fixture.sql supabase/migrations/202610230053_s0_meta_wa40_lock_order_fixture.sql supabase/tests/s0_isolation.sql supabase/tests/s0_dorg01_multiloja_prumo.sql supabase/tests/s0_extended.sql supabase/tests/s0_transactional.sql supabase/tests/s0_c02_inbound.sql supabase/tests/s0_recontatos.sql supabase/tests/s0_recontatos_gestor.sql supabase/tests/s0_auditoria_recontatos.sql supabase/tests/s0_c04_elegibilidade_optout.sql supabase/tests/s0_c04_replay_plano.sql supabase/tests/s0_c07_callbacks.sql supabase/tests/s0_c07_reconciliacao.sql supabase/tests/s0_gateway_privilegios.sql supabase/tests/s0_gateway_rotacao_retencao.sql supabase/tests/s0_gateway_isolamento_verificador.sql supabase/tests/s0_owner_gateway_assinado.sql supabase/tests/s0_036a_auditoria_acl_completa.sql supabase/tests/s0_037a_gate_owner_comercial.sql supabase/tests/s0_037b_matriz_rls_escrita.sql supabase/tests/s0_037c_execucao_assinada_c07_c08.sql supabase/tests/s0_037d_capacidade_transacional.sql supabase/tests/s0_037f_emissor_assinado_mock.sql supabase/tests/s0_identidade_aliases.sql supabase/tests/s0_inbox_outbox.sql supabase/tests/s0_wa_030_auditoria.sql supabase/tests/s0_wa_040_meta_binding.sql supabase/tests/s0_wa_041_meta_tentativa_binding.sql supabase/tests/s0_wa_042_meta_ids_tecnicos_fixture.sql supabase/tests/s0_wa_043_status_forense_fixture.sql supabase/tests/s0_wa_045_meta_signer_privilegios.sql supabase/tests/s0_wa_046_meta_revocation_contract.sql supabase/tests/s0_wa_031_c01_identidade.sql supabase/tests/s0_wa_032_lifecycle.sql supabase/tests/s0_wa_033_aplicacao_c02.sql supabase/tests/s0_wa_034_integridade.sql supabase/tests/s0_wa_034b_c07_contrato.sql; do
 psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/$file"
done
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/supabase/tests/s0_wa_044_meta_handoff_setup.sql"
python3 "$ROOT/supabase/tests/s0_wa_044_assert_meta_handoff_pg17.py"
python3 "$ROOT/supabase/tests/s0_wa_046_assert_key_revocation_race_pg17.py"
python3 "$ROOT/supabase/tests/s0_wa_047_assert_handoff_canonical_pg17.py"
node --test "$ROOT/supabase/tests/s0_wa_048_meta_handoff_adapter.test.mjs"
node --test "$ROOT/supabase/tests/s0_wa_049_meta_trusted_boundary.test.mjs"
node --test "$ROOT/supabase/tests/s0_wa_050_meta_raw_hmac_gate.test.mjs"
node --test "$ROOT/supabase/tests/s0_wa_051_dual_wire_agreement.test.mjs"
python3 "$ROOT/supabase/tests/s0_wa_052_assert_non_superuser_pg17.py"
python3 "$ROOT/supabase/tests/s0_wa_053_assert_authoritative_scope_pg17.py"
python3 "$ROOT/supabase/tests/s0_wa_054_assert_restricted_forensic_pg17.py"
python3 "$ROOT/supabase/tests/s0_wa_055_assert_forensic_parity_pg17.py"
python3 "$ROOT/supabase/tests/s0_wa_056_assert_outbox_cancel_race_pg17.py"
python3 "$ROOT/supabase/tests/s0_wa_057_assert_lock_order_cross_routes_pg17.py"
python3 "$ROOT/supabase/tests/s0_wa_058_assert_legacy_handoff_lock_order_pg17.py"
bash "$ROOT/scripts/test_s0_concurrency.sh"
bash "$ROOT/scripts/test_s0_cross_shop.sh"
bash "$ROOT/scripts/test_s0_c02_concurrency.sh"
bash "$ROOT/scripts/test_s0_recontato_race.sh"
bash "$ROOT/scripts/test_s0_c04_optout_race.sh"
bash "$ROOT/scripts/test_s0_c07_recon_concurrency.sh"
bash "$ROOT/scripts/test_s0_wa_030_concurrency.sh"
bash "$ROOT/scripts/test_s0_wa_031_c01_concurrency.sh"
bash "$ROOT/scripts/test_s0_wa_032_lifecycle_concurrency.sh"
bash "$ROOT/scripts/test_s0_wa_033_concurrency.sh"
bash "$ROOT/scripts/test_s0_wa_041_concurrency.sh"
# WA55 is deliberately LATE: all previous historical WA40/48-54 regression
# fixtures must execute before direct client EXECUTE is revoked.
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/supabase/migrations/202610230054_s0_meta_single_entry_seal_fixture.sql"
python3 "$ROOT/supabase/tests/s0_wa_059_assert_single_entry_sealed_pg17.py"
node --test "$ROOT/supabase/tests/s0_wa_060_meta_raw_to_pg17_bridge.test.mjs"
echo 'Teste local concluído. Não houve escrita no Supabase.'
