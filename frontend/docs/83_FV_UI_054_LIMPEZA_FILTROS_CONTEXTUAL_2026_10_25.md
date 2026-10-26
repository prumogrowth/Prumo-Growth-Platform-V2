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

## Certificação GitHub Actions — 25/10/2026

- Commit de conteúdo: `c805c53397e6774cbd3cf56784b33ca5d75c276b`.
- Manifesto repinado e **commit efetivamente testado**: `969d120883f0112882598dc723d96964ba1082f8`.
- [GitHub Actions run 40249445210](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40249445210): **completed / success** no SHA testado.
- Preflight nativo: **59 arquivos PASS**; segurança Python **25/25 PASS**; Node **361/361 PASS** e **0 falhas**; Chromium/Playwright **PASS**, inclusive `FV-UI-054 limpeza de filtros com escopo preservado em 8 cenarios: PASS`.
- Log final: `FULL LOCAL ACCEPTANCE: PASS`.
- Os resultados homologam apenas a consistência técnica do protótipo sintético. Sem API produtiva S0/S1, Meta/WhatsApp, autenticação, concessões, remessa bancária, leitor de tela humano ou deploy.
- O commit documental de certificação altera apenas este arquivo, preservando os 59 arquivos do checkout técnico aprovado e mantendo `main` intacta.
