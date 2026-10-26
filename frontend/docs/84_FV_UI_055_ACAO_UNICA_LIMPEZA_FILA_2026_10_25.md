# FV-UI-055 — Ação única para limpar filtros na fila

**Data:** 25/10/2026 · **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual`.

## Problema detectado após a FV-UI-054

Quando filtros causavam zero resultados, o controle fixo `#clear-list-filters` coexistia com `.empty-reset` no aviso de lista vazia. Dois botões com mesmo texto e ação confundiam navegação por teclado e tecnologia assistiva. Não havia efeito comercial, mas havia redundância real de interface.

## Correção

- Com **resultados filtrados**, mostrar o botão de limpeza superior, introduzido na FV-UI-054.
- Com **zero resultados e possibilidade de restaurar a lista**, ocultar o botão superior e manter **somente** a ação contextual no aviso vazio.
- Com escopo sem atendimentos ou perfil suspenso, preservar o botão superior para limpar qualquer refinamento, sem sugerir que o reset concede acesso.
- Os dois fluxos reutilizam `resetListRefinements()`, preservando identidade fictícia, concessionária, aba, detalhes e regras existentes. Foco retorna à busca.
- Nenhum ajuste de S0/S1, autenticação, canais, dados reais ou permissões.

## Testes e critérios de aceite

- Node DOM: com resultados, ação superior única; com lista vazia, somente botão contextual, identidade e foco preservados.
- Node contrato: condicional de visibilidade consistente com o estado vazio e com a função compartilhada.
- Chromium/Playwright: 320×640, 390×844, 900×780, 1440×900 nos dois temas, contando botões visíveis pelo papel acessível, limpando filtros em ambos estados, sem overflow ou erros.
- GitHub Actions deve verificar o SHA repinado, testes Python, Node, Chromium e `FULL LOCAL ACCEPTANCE: PASS` antes da certificação. Não é homologação produtiva nem teste humano assistivo.

**Anterior:** [FV-UI-054](./83_FV_UI_054_LIMPEZA_FILTROS_CONTEXTUAL_2026_10_25.md).

## Certificação remota — GitHub Actions

- **Conteúdo visual:** `a5e748c52712f2f39bb110edc42491e0aa4b3c42`, com o manifesto inicial em `8025a463b2965a66e65cc1557e289e6baf22b8b2`.
- **Primeira tentativa:** [run 40251427648](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40251427648) falhou (Node **362 PASS / 1 FAIL**); o teste FV-UI-054 antigo ainda esperava o botão superior com zero resultados. Chromium foi corretamente bloqueado.
- **Reparo de regressão:** `f9e9958fb4419ce235390fb1dda76428fd5b4fbc`; o próximo teste foi refinado para evitar declaração local duplicada em `9bb885801b057a6300613e9c8ee38f991b5cb3bf`. Cada reparo foi repinado em manifesto antes da validação.
- **Commit efetivamente testado e aprovado:** `3740ba5bcb2848fae957918ee8b1f8c09242c198`.
- **[GitHub Actions run 40251736131](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40251736131):** `completed / success`. Preflight **59 arquivos PASS**; Python **25/25 PASS**; Node **363/363 PASS**, zero falhas; Chromium/Playwright **PASS**, inclusive FV-UI-054 e `FV-UI-055 limpeza unica por estado em 8 cenarios: PASS`.
- Log final: **`FULL LOCAL ACCEPTANCE: PASS`**. A certificação aplica-se apenas à interface demonstrativa e sintética; não homologa leitor de tela humano, autorização produtiva, S0/S1/Meta/IA/Banco.
- Este commit de certificação é exclusivamente documental, sem modificação dos arquivos visuais já testados. Nenhum merge, PR ou deploy; `main` preservada.
