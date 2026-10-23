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
# auth.sessions local é uma fixture sintética, NÃO a tabela gerenciada pelo GoTrue.
# Isolamento: só após a suíte I14, que comprova o contrato anterior.
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_015_fake_gotrue_bootstrap.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/migrations/202610190052_s1_verificacao_sessao_gotrue.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_015_verificacao_sessao.sql
# Auditoria I38: demonstra a divergencia S0 e ensaia policies candidatas
# sob BEGIN/ROLLBACK. Nenhuma alteracao persiste; nao e migration.
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_058_supervisao_equipes_rls_local_only.sql
# I39: distribui lead novo entre equipes, testa fila sem titular e disputa CAS.
# Inclui fixture de intake I53 dentro de BEGIN/ROLLBACK (nenhum dado persiste).
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_059_novos_leads_fila_cross_team_local_only.sql
# I41: S0/RLS supervisor ve equipe historica; Consultor le mesmo contato/loja.
# Prova candidato dentro de BEGIN/ROLLBACK; policies canônicas nao mudam.
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_061_historico_equipe_contato_rls_local_only.sql
# I42: excecao estrita por caso abre historico do mesmo contato/loja
# e perde leitura/envio ao revogar. I53/I54/I55 restritos ao rollback.
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_062_excecao_historico_contato_local_only.sql
# I43: executa policies I41 + I42 SIMULTANEAMENTE, reproduz bloqueio
# interpolicy e valida permissao unificada + revogacao. ROLLBACK total.
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_063_rls_unificada_equipe_excecao_local_only.sql
# I51/A2 decisao [D] 23/10: impedir qualquer transferencia manual para Consultor
# pausado, tanto caminho I12 normal quanto I35 por caso. BEGIN/ROLLBACK.
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_075_a2_transferencia_pausado_local_only.sql
# I40: somente banco local descartavel; funcoes I39 idênticas em 2 sessoes reais.
# Seed COMMITADO apenas nesse PG17; runner CI descarta banco apos a suite.
bash scripts/test_s1_002_queue_race.sh
# I52: genuine incremental S0 assignment boundary + versioned S1 intake state.
# Execute only after historical S0/S1 migrations and all legacy tests.
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/migrations/202610190053_s0_s1_intake_atribuicao_guard.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_076_integracao_intake_canonico_aceite.sql
# I52: serialize pause vs canonical insert, under two independent SQL sessions.
bash scripts/test_s1_002_i52_intake_race.sh
echo 'S1-002/I15: sessao fake ativa/revogada conferida; sem GoTrue/REST real.'
