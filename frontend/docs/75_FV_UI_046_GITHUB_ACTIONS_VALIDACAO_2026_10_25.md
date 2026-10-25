# FV-UI-046 — Configuração do GitHub Actions para validação nativa

**Data:** 25/10/2026 · **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual`.

## Autorização e arquivo de infraestrutura

A pedido do responsável, este incremento adiciona **exclusivamente a exceção de infraestrutura necessária** `.github/workflows/frontend-visual-validation.yml` fora de `frontend/`. Não altera a branch `main` ou o repositório antigo, não cria um ambiente de produção e não publica a interface. Os demais arquivos alterados são documentação em `frontend/docs/`.

## Gatilho e controle de custos

O workflow é acionado apenas por **push** em `feat/frontend-plataforma-visual`, quando mudanças atingirem `frontend/visual/**` ou seu próprio YAML. Commits exclusivamente documentais em `frontend/docs/` não acionam o fluxo. Utiliza uma única máquina GitHub-hosted **Ubuntu 24.04 padrão**, **15 minutos máximos por execução**, `concurrency.cancel-in-progress=true` para evitar acúmulo de runs redundantes, `GITHUB_TOKEN` com somente `contents:read`, checkout sem persistir credenciais, sem secrets, sem permissões de escrita e sem deploy. O relatório JSON é retido por um dia. A franquia e a cobrança dependem das configurações reais do proprietário da conta; **não afirmar custo zero garantido ou execução ativa sem conferir o GitHub**.

## Execução do gate

1. Faz checkout do commit exato de `github.sha`, com `fetch-depth:0` para permitir `git merge-base --is-ancestor` exigido no FV-UI-045.
2. Prepara Python 3.11 e Node 22; instala Playwright 1.55.0 e Chromium com dependências.
3. Executa `python -B frontend/visual/tests/run_acceptance.py --expected-head "$GITHUB_SHA" --json-report fv-native-validation/report.json`. Essa rotina valida revisão/branch/working tree limpo, manifesto e hashes reais, adversários ZIP, testes Node e smoke completo do Chromium, em sequência bloqueante.
4. Em caso de erro, mantém a execução **vermelha**, produz um resumo de etapas quando possível e publica o relatório JSON de diagnóstico sem dados reais. Não converte falha de navegador em aprovação.

## Critérios de veracidade

A presença do workflow no Git **não comprova que ele rodou**. Só registrar `full_acceptance=true` quando o job concluir em sucesso e o relatório demonstrar todos os gates aprovados no HEAD exato. Repositório privado pode restringir GitHub Actions ou suspender uso após cota; verificar a aba Actions. `workflow_dispatch` não foi incluído porque a branch padrão `main` não pode ser modificada no momento; gatilho via push na branch experimental é suficiente.

## Escopo preservado

Somente interface fictícia e verificação. Nenhuma modificação S0/S1, WhatsApp/Meta, OpenAI, Supabase, cadastro real, pagamento, template ou permissão. Nenhuma interação com leads reais.

**Antecessor:** [FV-UI-045](./74_FV_UI_045_PREFLIGHT_NATIVO_HEAD_2026_10_25.md).
