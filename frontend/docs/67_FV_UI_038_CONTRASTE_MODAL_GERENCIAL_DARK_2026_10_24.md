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
