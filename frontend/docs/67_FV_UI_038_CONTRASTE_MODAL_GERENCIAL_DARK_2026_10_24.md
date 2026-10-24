# FV-UI-038 — Contraste do diálogo gerencial em tema escuro

**Data:** 24/10/2026 · **Repositório oficial:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** `frontend/`.

## Achado

A atualização do FV-UI-036 já sincroniza o tema do `body` com os diálogos nativos. No modo escuro, seletores antigos de **Lotes** ainda podiam definir fundo claro para `.team-batch-summary` enquanto o contêiner herdava texto quase branco, provocando baixo contraste. Rótulos em cartões de lotes, auxiliares de Monitoramento e o `summary` de ajuda também conservavam algumas cores de texto de tema claro.

## Correção

CSS estritamente condicionado ao tema escuro em `body[data-theme="dark"] .team-dialog`, sem afetar o tema claro:

- `team-batch-summary`: fundo escuro neutro, borda diferenciada e texto legível.
- Textos auxiliares em cartões de lotes, métricas, etapas, fila, membros e prévias de pausa: escala de cinza-azulado claro uniforme.
- Título da ajuda (`details > summary`) e das prévias de pausa: destaque verde-acinzentado acessível.
- Bordas das divisões do monitoramento e indicador de aba gerencial pressionada harmonizados com superfícies escuras.

## Testes e limites

- Regressão estática em `tests/source-contract.test.mjs`: seletores específicos, prevenção de desaparecimento dos estilos e presença do teste browser.
- Chromium real em ambiente de ensaio derivado do FV-UI-036, simulando a sincronização remota do tema em diálogos: **PASS** em 1366×800 e 390×800.
- No cenário de gestão da fixture Marina, o ensaio verificou contraste calculado de **pelo menos 4,5:1** em resumo e rótulos de lotes, ajuda, texto do monitoramento e fila. Não verifica todos os pixels, todos os estados ou a WCAG completa.
- Node nativo local **340/340 PASS** com exclusão deliberada da suíte de manifesto (os bytes locais FV-UI-036 e os do HEAD oficial FV-UI-037 não eram idênticos). Browser smoke da suíte local **PASS**.
- A integridade dos blobs finais é avaliada separadamente via árvore Git remota e manifesto repinado. A execução nativa completa sobre checkout Git autenticado desse HEAD ainda está pendente.
- Nenhum S0/S1, WhatsApp/Meta, Supabase, OpenAI ou banco acionado. Gestores não ganham acesso a mensagens privadas ou dados D3/D4; a solução não modifica equipes, permissões, concessões, fila, pausa ou status comercial. Nenhum merge/deploy autorizado.

**Anterior:** [FV-UI-037](./66_FV_UI_037_TEMA_SISTEMA_ESCOLHA_MANUAL_2026_10_24.md).


## Auditoria remota pós-publicação

- Commit de CSS, navegador, regressão e documentação: `17f442abc93755cff1f634fce5ce759ecb062b31`.
- Commit de repin do manifesto: `a25e0ff73eae1b9bc1c2836fe3a7f03080e4a3ac`.
- Comparação com FV-UI-037: **2 commits**, **7 arquivos alterados**, **todos sob `frontend/`**.
- Árvore do GitHub do novo repositório confrontada com `tests/verify_offline_export.py`: **58/58 hashes Git blob e tamanhos válidos**, nenhuma divergência; SHA do próprio verificador: `987ae824550211370ae82999af1479e137348287`.
- `source_head` do manifesto referencia o commit de conteúdo `17f442abc...`, anterior ao repin do próprio verificador, para evitar ciclo de hash.
- Branch `main` verificada sem alteração: `dace737ab7afb7ae3f5a3a6f5cb522e6def8b43a`.
- O resultado Chromium/Node acima foi obtido em snapshot **local derivado**, com as regras remotas de tema dos diálogos reproduzidas no ensaio. Não constitui checkout autenticado do HEAD publicado nem gate integral do ZIP final. Auditoria WCAG completa segue pendente.
