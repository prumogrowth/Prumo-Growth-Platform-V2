# Prumo — plataforma comercial (nome provisório)

Operação comercial do produto **LiberaCred**, da instituição financeira. As ideias iniciais foram superadas: implementar somente normas vigentes dos documentos **00A, 13A, 21–23 e 41**, com os projetos técnicos 25/26/30/38/39/42/43.

**S0 em desenvolvimento, dados exclusivamente sintéticos.** Nenhuma integração Meta, Banco, OpenAI ou n8n está conectada e não há liberação para produção.

Arquivos:
- `supabase/migrations/`: fundamento e RLS de leitura segura por concessionária.
- `supabase/tests/`: fixtures sintéticas, importação C01 e testes SQL de isolamento/transições.
- `supabase/migrations/202610170006_s0_transactional_simulation.sql`: serviços internos C01 e evento de inbound simulados; **não expostos à API**.
- `scripts/test_s0_concurrency.sh`: ensaio com duas conexões PostgreSQL concorrentes.
- `scripts/run-s0-local.sh`: runner restrito a Postgres LOCAL e base descartável.
- `docs/MAPA_MENTAL.md`: mapa mental simples.
- `docs/DECISOES_E_GATES.md`: regras, custos e próximos portões.
- `tests/S0_ACEITE.md`: status dos ensaios.

Decisão posterior: telefone de cliente exclusivo globalmente; canais emissores também exclusivos por loja. Veja `docs/DECISAO_POSTERIOR_EXCLUSIVIDADE_NUMEROS_2026_10_17.md`.

S0: gestores autenticados podem ler leads/ciclos **somente de lojas vinculadas**; operadores não recebem leitura geral até existirem casos/atribuições na S1. Nenhum cliente recebe escrita direta. Gestão D2, autoatribuição e D3/D4 exigem módulo de casos S1 e provas adicionais.

Teste futuro: crie um banco local descartável `prumo_s0_test_*`, exporte `PRUMO_TEST_DATABASE_URL` e rode `./scripts/run-s0-local.sh`. **Não apontar para Supabase remoto.**

Migrações versionadas 001–008 não estão implantadas no Supabase. Suíte SQL e teste concorrente executados em CI; veja `tests/S0_ACEITE.md`. Não gravar segredos nem dados pessoais reais no repositório.
