#!/bin/bash
set -euo pipefail
bash scripts/run-s1-002-local.sh
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/migrations/202610190049_s1_movimento_manual_por_equipe.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_012_movimento_manual_equipe.sql
# O teste de duas sessoes cria dados persistentes: executar APENAS apos 050.
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/migrations/202610190050_s1_movimento_manual_bloqueio_chefia.sql
# A nova versao precisa manter as invariantes e corridas I12 ja comprovadas.
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_012_movimento_manual_equipe.sql
bash scripts/test_s1_002_manual_race.sh
bash scripts/test_s1_002_authority_race.sh
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/migrations/202610190051_s1_sessao_autorizacao_privada.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_014_sessao_privada_fake_auth.sql
echo 'S1-002/I14: interface privada de sessão fake-auth, sem GoTrue/REST.'
