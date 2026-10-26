# FV-UI-054 — Limpeza contextual de busca e filtros

**Data:** 25/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`.

## Motivação, escopo e implementação

Antes da FV-UI-054, o botão para limpar busca e filtros aparecia apenas com lista vazia. Após a alteração, **Limpar busca e filtros** aparece sempre que a busca, o chip ou a etapa comercial estiver refinada, mesmo quando alguns resultados continuam visíveis.

- O controle se oculta na seleção padrão, tem área de toque de 44 px e foco visível em claro/escuro.
- A função compartilhada `resetListRefinements()` é usada tanto pelo estado vazio quanto pelo novo controle. Redefine **somente** `query`, `filter` e `statusFilter`, preservando aba (Ativas / pendentes ou Histórico), profissional fictício, concessionária e casos.
- A busca recupera o foco após a limpeza. Nenhuma chamada externa ou efeito comercial.

## Regressões e certificação

- Node DOM: filtros combinados, busca vazia, foco, identidade, loja e aba histórica preservados.
- Contrato Node de fonte e Chromium: 320×640, 390×844, 900×780 e 1440×900, dois temas, toque, foco e ausência de overflow/erros.
- A frente pode assumir dependências S0 necessárias, mediante contratos e segurança; **não há dependência S0 nesta alteração**.

**Gate:** Python, Node, Chromium e `FULL LOCAL ACCEPTANCE: PASS` em GitHub Actions no manifesto repinado antes da certificação; não equivale a testes humanos por leitor de tela ou integração. Sem `main`, PR, merge, deploy, S0/S1, dados reais, autenticação ou WhatsApp.

**Anterior:** [FV-UI-053](./82_FV_UI_053_ATALHO_BUSCA_VISIVEL_2026_10_25.md).
