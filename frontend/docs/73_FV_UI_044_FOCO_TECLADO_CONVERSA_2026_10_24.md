# FV-UI-044 — Foco de teclado, contorno visível e navegação da conversa

**Data:** 24/10/2026 · **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** `frontend/`.

## Evidência do problema

Em viewport compacta (320px), a barra operacional tem `overflow-y:auto` e um botão de ação ficava junto à borda interna esquerda do contêiner. O contorno existente usa **3px** com `outline-offset:2px`, podendo avançar **5px para fora da área rolável** e ser parcialmente recortado, apesar de o foco lógico do teclado permanecer correto. O teste local antes da correção encontrou botão em `x=14` e limite esquerdo da barra também em `x=14`. Não foi identificada alteração de ordem do Tab nem perda de foco lógico.

## Ajuste aplicado

- `.thread-pane .workflow-bar` ganha **6px de espaço interno horizontal e superior** e `scroll-padding:8px` para dar margem a comandos dentro da área com overflow.
- Ação operacional, botões do cabeçalho, campo de mensagem e botão de prévia usam `:focus-visible` com contorno **3px**, deslocamento **2px**, cor **#11685d** no claro e **#83dac9** no escuro.
- Mantidos foco apenas ao navegar por teclado, controles `disabled`, ordem do DOM, regras comerciais, ações e o comportamento da prévia que **não envia WhatsApp**.
- Nenhuma nova aba ou comando, nem desabilitação de rolagem, `tabindex` ou reestruturação do DOM.

## Testes executados

O ensaio direcionado de Chromium/Playwright foi executado em snapshot local derivado do FV-UI-036 com o CSS do FV-UI-043 e a mudança FV-UI-044 aplicada: **8/8 cenários PASS** em larguras 320, 390, 900, 1440px nos temas claro/escuro. O ensaio incluiu 520px de altura nas duas telas móveis para desafiar a área rolável e verificou: foco perceptível no cabeçalho, `Shift+Tab` do campo para `#request-completion` sem disparar comando, `Tab` de volta ao campo e em seguida ao botão de prévia, contorno 3px e cor adequada, folga ≥5px nas quatro bordas do comando dentro da barra, ausência de overflow horizontal ou erro JS.

Na mesma base derivada, **340/340 testes Node PASS** (excluído `offline-export-manifest.test.mjs` referente ao snapshot anterior). O último deles verifica os contratos estáticos FV-UI-044. Esses ensaios **não constituem execução de testes no checkout autenticado do HEAD oficial**; o gate nativo integral e a validação humana de acessibilidade permanecem pendentes.

## Fronteiras

Prova de conceito visual com dados fictícios. Nenhum comando operacional foi ativado nos ensaios. Nada de backend, persistência, Meta/WhatsApp, OpenAI, Supabase, alterações de permissões ou autorização, distribuição, S0/S1, cobrança, merge em `main` ou deploy. O comportamento de tela no navegador é verificado separadamente da integridade de Git blob.

**Anterior:** [FV-UI-043](./72_FV_UI_043_BARRA_OPERACIONAL_COMPOSITOR_2026_10_24.md).


## Auditoria remota após repin

- Implementação, teste de teclado e documentação: `d6f662182a8293aec2c0310eee71705e13527239`.
- Manifesto repinado: `c69fa194e376d4058f43effd28a091e0cbf98024`, com `source_head=d6f662182a8293aec2c0310eee71705e13527239` anterior à atualização do próprio manifesto.
- Comparação desde o FV-UI-043: **2 commits, 7 arquivos alterados**, todos em `frontend/`, nenhum arquivo fora do escopo.
- Conferência de árvore oficial e `verify_offline_export.py`: **58/58 hashes e tamanhos de blobs correspondentes**, sem entradas extras nem divergências. SHA Git do próprio verificador: `25ea72cdacb44d6fa4c8f8aaa4fd16bead474c77`.
- `main` verificada em `dace737ab7afb7ae3f5a3a6f5cb522e6def8b43a`, sem merge e sem deploy.
- Os arquivos publicados contêm CSS FV-UI-044, contrato estático e regressão em `browser.smoke.py`. O relatório local de Chromium **8/8 PASS** e Node **340/340 PASS** pertence a **snapshot derivado do FV-UI-036**, não ao HEAD autenticado. A comparação Git não deve ser apresentada como execução da suíte nativa desse HEAD.
- Gate de checkout autenticado, execução integral do navegador e revisão humana de acessibilidade **pendentes**.
