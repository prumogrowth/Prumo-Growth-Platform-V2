# Prumo — plataforma comercial (nome provisório)

Operação comercial do produto **LiberaCred**, da instituição financeira. As ideias iniciais foram superadas: implementar somente normas vigentes dos documentos **00A, 13A, 21–23 e 41**, com os projetos técnicos 25/26/30/38/39/42/43.

**S0 em desenvolvimento, dados exclusivamente sintéticos.** Nenhuma integração Meta, Banco, OpenAI ou n8n está conectada e não há liberação para produção.

Arquivos:
- `supabase/migrations/`: fundamento e RLS de leitura segura por concessionária.
- `supabase/tests/`: fixtures sintéticas, importação C01 e testes SQL de isolamento/transições.
- `supabase/migrations/202610170006_s0_transactional_simulation.sql`: serviços internos C01 e evento de inbound simulados; **não expostos à API**.
- `scripts/test_s0_concurrency.sh`: ensaio com duas conexões PostgreSQL concorrentes.
- `supabase/migrations/202610170009_s0_c02_inbound_synthetic.sql`: recebimento fictício de mensagens e roteamento pendente, **sem Meta**.
- `scripts/test_s0_c02_concurrency.sh`: duplicidade de webhook fictício e eventos paralelos.
- `docs/C02_RECEBIMENTO_SIMULADO_S0.md`: ingresso simulado e relação com cancelamento local.
- `docs/RECONTATOS_C05_C08_SIMULACAO_2026_10_17.md`: catálogo, planos, reservas, cancelamento e limites (sem transmissão Meta).
- `scripts/test_s0_recontato_race.sh`: concorrência entre inbound e reserva em duas conexões PostgreSQL.
- `scripts/run-s0-local.sh`: runner restrito a Postgres LOCAL e base descartável.
- `docs/MAPA_MENTAL.md`: mapa mental simples.
- `docs/DECISOES_E_GATES.md`: regras, custos e próximos portões.
- `supabase/config.toml`, `scripts/test_s0_auth_rest_local.py`, `.github/workflows/s0-auth-rest.yml`: testes locais de GoTrue e PostgREST com JWTs reais de sandbox, sem usar Supabase hospedado.
- `docs/AUTH_REST_S0_VALIDACAO_LOCAL.md`: evidências e limitações da integração de autenticação.
- `docs/C04_ELEGIBILIDADE_OPTOUT_SIMULADO_2026_10_17.md`: evidência fictícia, supressão por emissor/finalidade e bloqueios C05/C06.
- `docs/C07_CALLBACKS_SIMULADOS_2026_10_17.md`: eventos técnicos correlacionados, duplicados, tardios e pendências de reconciliação; sem prova externa.
- `docs/CONTROLE_CUSTOS_GITHUB_ACTIONS_2026_10_17.md`: workflows enxutos, timeouts, cancelamento de execuções obsoletas e Auth/REST opt-in.
- `tests/S0_ACEITE.md`: status dos ensaios.

**Regra vigente:** um cliente pode atender-se em A, B e C com o mesmo telefone, com leads/históricos isolados por loja; número **emissor de atendimento da Prumo** é exclusivo de uma loja. Veja `docs/REGRA_NUMEROS_ATENDIMENTO_CLIENTE_2026_10_17.md`.

S0: gestores autenticados leem dados somente das lojas vinculadas; operadores leem leads/conversas apenas de casos atualmente atribuídos. A escrita direta em leads, ciclos e remessas continua bloqueada ao cliente. D3/D4 e fluxos bancários ainda não foram construídos.

Teste futuro: crie um banco local descartável `prumo_s0_test_*`, exporte `PRUMO_TEST_DATABASE_URL` e rode `./scripts/run-s0-local.sh`. **Não apontar para Supabase remoto.**

Migrações versionadas 001–006 e 008–019 (007 indevida retirada antes de deploy) não estão implantadas no Supabase. Suíte SQL e teste concorrente executados em CI; veja `tests/S0_ACEITE.md`. Não gravar segredos nem dados pessoais reais no repositório.
