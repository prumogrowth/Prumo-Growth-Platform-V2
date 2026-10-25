# FV-UI-047 — Legibilidade, foco e alvos dos filtros da fila

**Data:** 25/10/2026 · **Projeto:** LiberaCred / Prumo Growth · **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual`.

## Estado anterior comprovado no GitHub

Após o FV-UI-046, o GitHub Actions realizou [run 40180965490](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40180965490), com 25/25 Python, 352/352 Node e Chromium completo PASS no commit `f6f10b53329fecfa000699df37bdb1b509626714`. A alteração posterior em `frontend/docs/` não modificou os 59 blobs auditados.

Os filtros na lista mantinham áreas inferiores ao alvo de toque de 44px: caixa de busca de 42px, abas Ativas/Histórico com padding vertical de 9px, chips de filtros com 8px e seletor avançado com fonte de 10px. Alguns textos secundários claros tinham contraste insuficiente; o seletor avançado não possuía superfície correspondente ao tema escuro.

## Implementação restrita à interface

CSS aditivo escopado em `.list-pane`, sem alterar HTML, JS, permissões nem estados de negócio:

- Busca: altura mínima 44px, fonte 14px no desktop e 16px até 760px, foco de 3px e placeholder contrastante.
- Abas e chips: altura mínima 44px e fontes 12px; tons de texto ajustados sem ocultar selecionado/inativo.
- Etapa comercial: rótulo 11px contrastante; seletor com 12px e altura mínima 44px, incluindo superfície escura.
- Roteiro Chromium: 320/390/900/1440px × claro/escuro, alvos ≥44px, contraste calculado ≥4,5:1 em quatro textos amostrados, foco com Tab após a busca, seleção e restauração de abas/chips e ausência de overflow horizontal.
- Contrato estático Node valida presença das novas regras e do roteiro de browser.

Nenhuma alteração em `app.mjs`, dados fictícios, filtros reais, envio de mensagem, gestão, F03, papéis, autenticação, Meta/WhatsApp, Supabase, integrações, pagamentos ou `main`.

## Aprovação

**Condicionada ao GitHub Actions no commit efetivamente publicado**: não considerar executado ou aprovado apenas pela presença dos testes. O manifesto de blobs deve ser repinado após o commit de conteúdo; comparar logs do runner para Python/Node/Chromium e `full_acceptance`. Aceite visual humano não substituído.

**Anterior:** [FV-UI-046](./75_FV_UI_046_GITHUB_ACTIONS_VALIDACAO_2026_10_25.md).


## Execução real aprovada — GitHub Actions

- Commit de conteúdo e testes: `28d16d0c64119a561126b6c08a1d54789e1ce814`.
- Commit de repin do manifesto: `4c2e56e3d06d92a5337c2f9ac874f62bc55ae6f5`, com `source_head=28d16d0c64119a561126b6c08a1d54789e1ce814`.
- [GitHub Actions run 40188680770](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40188680770) executado sobre o SHA repinado exato, **completed / success**.
- Preflight confirmou **59 arquivos** do checkout Git (58 pinados + o próprio verificador). SHA e tamanhos consistentes.
- Regressão Python **25/25 PASS**; Node **353/353 PASS**, **0 falhas**.
- Chromium real executado, roteiro completo **PASS**, incluindo `FV-UI-047 filtros da fila em oito cenarios, foco e contraste: PASS`. Também passaram os blocos anteriores FV-UI-040 até FV-UI-044.
- Log do executor registra `FULL LOCAL ACCEPTANCE: PASS`. O relatório JSON foi publicado no Actions com retenção de um dia.
- Ao preparar a publicação, o commit de conteúdo permaneceu sem atualização de branch até a criação do manifesto, produzindo **uma única atualização final da branch** e evitando execuções CI duplicadas.
- **Nenhuma alteração em `main`, nenhuma integração externa, merge ou deploy**. Esse aceite técnico é do frontend sintético e não implica homologação comercial/produtiva ou análise humana completa de acessibilidade.
