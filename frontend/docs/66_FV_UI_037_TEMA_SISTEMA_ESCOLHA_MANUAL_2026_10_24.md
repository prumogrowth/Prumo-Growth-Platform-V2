# FV-UI-037 — Atualização de tema do sistema com prioridade à escolha manual

**Data:** 24/10/2026 · **Repositório oficial:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** somente `frontend/`.

## Decisão

Preservar somente duas opções explícitas, Claro e Escuro, sem acrescentar controles desnecessários. Antes da primeira escolha manual, a interface segue a preferência do navegador (`prefers-color-scheme`) **inclusive quando ela muda com a página aberta**. Depois de clicar Claro ou Escuro, o tema escolhido prevalece até recarregar a página. Não há gravação em `localStorage`, cookie, conta, API ou servidor.

## Implementação

- `app.mjs`: `MediaQueryList` única e ouvinte de `change`; sinalizador `themeOverride` evita sobrescrever uma escolha manual. O `applyTheme` existente sincroniza tema no `#visual-app` e `body`, com `aria-pressed` dos botões.
- `tests/dom-fixture.mjs`: preferência simulada e disparo de evento de mudança do sistema; não finge ser motor de CSS.
- `tests/app.dom.test.mjs`: alternância automática claro→escuro→claro, escolha manual de Claro, mudança posterior do sistema ignorada, caso e lista preservados.
- `tests/browser.smoke.py`: Chromium em 390×844 com `emulate_media` alterada dinamicamente, tema do `body`, opção manual, `aria-pressed` e ausência de overflow.
- `tests/source-contract.test.mjs` e `README.md`: regressões e orientação.

## Escopo e segurança

Nenhuma nova identidade visual, estado comercial, mudança de permissões, alteração de distribuição, mensagem real ou chamada de API. A separação entre supervisor e titular, concessões por loja, contexto D3/D4, envio confirmado versus ACK e S0/S1 permanecem inalterados. O cenário é integralmente fictício.

## Evidência e limites

A implementação foi previamente ensaiada com fontes locais derivadas do FV-UI-036: **116/116** testes Node direcionados, **341/341** testes Node não relacionados à integridade do manifesto e **Chromium PASS**. Os arquivos remotos do FV-UI-036 não eram todos byte a byte idênticos ao ZIP local; portanto esses ensaios **não são rotulados como gate nativo de um snapshot remoto completo do FV-UI-037**. A integridade dos blobs finais deverá ser verificada diretamente no novo GitHub após o repin do manifesto.

Não é checkout Git autenticado, homologação, teste humano WCAG/leitor de tela ou aceite FV-22. Não há autorização para merge em `main` nem deploy.

**Anterior:** [FV-UI-036](./65_FV_UI_036_GATE_NATIVO_LOCAL_2026_10_23.md).

## Auditoria remota após repin

- Commit de código FV-UI-037: `3480921e42f1c71f2b2a54ce15c0d11a83fee87a`.
- Commit de documentação: `a9d27f2aa727ff02671f25481f71383030f8aa15`.
- Commit de manifesto: `2ac11a1507f9ec27b952c1050132d33710b85c6d`.
- Comparação desde FV-UI-036: **3 commits**, **9 arquivos alterados**, **zero arquivos fora de `frontend/`**.
- Árvore Git oficial: **58/58 Git blob SHA-1 e tamanhos conferidos** perante `verify_offline_export.py`; **zero divergências**.
- `source_head` do manifesto: commit de código `3480921...`, não o commit que atualizou o próprio manifesto; isso evita autopinagem circular.
- `main` não sofreu alteração pela nossa frente; sem merge, deploy ou integração produtiva.
- Fonte do diagnóstico de browser/Node: ambiente local derivado da base FV-UI-036, *não* ZIP oficial/checkout autenticado deste HEAD. Evidência remota é de integridade e presença dos contratos; a execução nativa integral sobre um checkout oficial permanece pendente.
