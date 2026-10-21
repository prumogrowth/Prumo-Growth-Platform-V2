# WA-06D — execução PostgreSQL 17 concluída e preparação do contrato Meta↔S0

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Data:** 20/10/2026 UTC. **Repositório:** `prumogrowth/Prumo-Growth---Platform`. **Branch:** `docs/whatsapp-meta-concessionária de demonstração-poc-20261017`, PR #2 **Draft**, sem merge/deploy ou serviços reais.

## 1. Evidência executada (GitHub Actions)

- **Execução definitiva validada:** [Prumo Meta, run #4](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39362852084), commit executado `98b78d10714211709494e1b58764d19edc62b217`.
- **Job `WA-06D PG17 descartavel`:** `118432785904`, `conclusion=success`.
- **Job `meta-offline`:** `118432786087`, `conclusion=success`.
- Banco: imagem oficial `postgres:17` em contêiner Docker temporário **`--network none`** e servidor com `listen_addresses=''`, sem publicação de portas, `wa06d_test_ephemeral`; container removido após os testes. O CI executa três `psql` separados com entrada interativa, garantindo que os arquivos SQL tenham sido realmente consumidos.
- **WA06D/A:** `wa06d_pg17_atomicity.sql` **14/14 PASS**, marcadores `WA06D-01..14` individuais.
- **WA06D/B:** `wa06d_pg17_postcommit_setup.sql` grava e faz `COMMIT`; `wa06d_pg17_postcommit_verify.sql` abre outro `psql`, **6/6 PASS**, marcadores `WA06D-B01..06` individuais.
- Uma guarda adicional no workflow exige **cada um dos 20 marcadores exatamente uma vez**, além de `ON_ERROR_STOP=1` e `pipefail`. Marcador final conferido: `PASS WA06D: all 20 SQL markers independently verified with 0 psql errors`.
- Testes Python do *runner* próprio `run-wa06d-ephemeral.sh`, com binários PostgreSQL simulados, **7/7 PASS**. **Importante:** o workflow definitivo executou as três SQL por `docker exec`, **não executou o script original `run-wa06d-ephemeral.sh` usando binários PostgreSQL reais**. O teste Python comprova contratos/guardas do runner com mocks, não seu caminho real no CI.
- No mesmo commit, Meta `run-offline-tests.sh --all` em Node.js 22: **467/467 PASS**, `# fail 0`, `# skipped 0`.

## 2. Falhas descobertas e reparadas

1. [Tentativa de CI #2](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39362379770): o Ubuntu do runner não encontrou o pacote `postgresql-17` em seus repositórios. Nenhuma SQL WA-06D foi executada ali. Substituído por PostgreSQL 17 do Docker, sem rede.
2. [Tentativa de CI #3](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39362544636): banco iniciado, **WA06D-01 PASS**, mas `WA06D_02_FAIL`. O teste chamava `wa06d_accept` (com efeito de escrita) e lia contagens em uma única expressão booleana SQL: a ordem de avaliação não é garantida, portanto o teste dependia de um detalhe não contratado. Corrigidas cinco verificações (WA06D-02, 07, 08, 12 e 14), separando explicitamente as chamadas de escrita de suas assertivas de contagem. Nenhuma regra comercial alterada.
3. [CI #4](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39362682957): ambos os jobs PASS, 20 marcadores SQL registrados; confirmação reforçada na [execução #5](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39362852084) com checagem dos 20 marcadores individuais.

## 3. Relação com S0-041, validade e lacuna de contrato

**Já comprovado em PostgreSQL real, de modo separado:**
- [CI S0 run #335](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39358441903): S0-041 vinculou tentativa↔wamid sintético com **WA14 18/18**, concorrência **WA14C 3/3**, S0-040 **5/5**, sempre em banco descartável.
- WA06D-A/B **20/20** confirma semântica isolada de transação, replay, rollback, posições de status e leitura de registros após `COMMIT`, não a chamada ao serviço S0-041.

**Lacuna observada na leitura das interfaces publicadas:**
- O laboratório Meta WA-13 (`s0-binding-bridge.ts`) recebe `CorrelationReference.scope` com `meta_app_ref`, `meta_waba_id`, `phone_number_id`, `canal_id` e `concessionaria_id`, e valida emissor com dígitos (`/^\d{5,25}$/`). Suas referências de loja/canal/intenção são strings opacas de fixture (ex.: `SHOP_A`, `CHANNEL_A`, `INTENT_A`).
- O cadastro PostgreSQL S0-030/040 usa **`FIXTURE_*`** para app, WABA e `phone_number_ref`; loja/canal/intenção são **UUIDs**. O método SQL `registrar_vinculo_meta_fixture_s0` resolve WABA/phone com base no App/canal/loja interno, sem receber diretamente o emissor numérico do envelope Meta.
- Assim, **não há ainda correspondência física 1:1 comprovada** entre a evidência técnica da WA-13 e a identidade do emissor persistida na S0-041. Não converter `phone_number_id` numérico em `FIXTURE_PHONE_*` por concatenação, nem tratar referências fictícias como atestados de produção. A tradução e validação devem vir de **um cadastro S0 confiável**, com checks do App/WABA/emissor/autorização na mesma transação.

**Próximo gate de engenharia WA-15 (proposto, não implementado):** contrato parametrizado e autenticado de gravação/consulta do ledger S0 a partir do adaptador Meta, com identidade de escopo conferida pelo S0, UUIDs internos reais de laboratório, ligação exata do intento bloqueado e dois modos de incerteza de confirmação do commit. Construir testes cross-branch reais em PostgreSQL antes de chamar a integração concluída. O status Graph `API_ACCEPTED` não implica `sent` ou venda.

## 4. Limites e autorização

**Nenhuma chamada real a Meta Graph, OpenAI, banco, webhook, API de produção ou Supabase hospedado.** Nenhum token, lead real, disparo, transição comercial, HTTP ACK, merge ou deploy. A aprovação das 20 SQL **não** homologa durabilidade após falha de energia, `COMMIT_UNKNOWN` fora do laboratório, identidade JWT/IAM, políticas LGPD, integração Meta↔S0, autorização comercial C03/C06/C12 ou operação definitiva. PRs permanecem Draft.
