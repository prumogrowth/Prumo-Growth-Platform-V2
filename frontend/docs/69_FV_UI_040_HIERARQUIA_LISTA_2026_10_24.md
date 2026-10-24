# FV-UI-040 — Hierarquia e legibilidade da fila de conversas

**Data:** 24/10/2026 · **Repositório oficial:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** somente `frontend/`.

## Problema observado

Na fila do demonstrador, o nome do atendimento (13 px) ficava visualmente muito próximo da prévia (11 px). Rótulos dos três indicadores e a etiqueta da conversa (`micro-tag`) usavam 9 px. Horários e descrições utilizavam tons claros em superfícies claras. A solução deve preservar a leitura simultânea de nome, prévia, horário, etiqueta e pendência, sem adicionar botões ou esconder informação operacional.

## Mudanças aplicadas

CSS localizado na lista de conversas, com estilo neutro:

- Nomes das conversas: **14 px**; mantido `min-width:0` e truncamento quando necessário.
- Prévia das mensagens: **12 px**, linha confortável e cor neutra mais contrastante.
- Horários, etiquetas de estado, contexto da fila e rótulos dos indicadores: **11 px**.
- Conversa selecionada: marcador interno sutil de 3 px, sem mudar o tamanho do botão e sem substituir as indicações existentes de leitura ou resposta pendente.
- Tema escuro: cor própria para rótulos dos indicadores e destaque interno da conversa selecionada.
- Nenhum ícone, texto, autorização, contagem, filtro ou estado comercial modificado.

## Evidências de execução local

**Chromium/Playwright PASS** em ambiente de ensaio baseado em snapshot local derivado do FV-UI-036. Novo teste de fonte, contraste e reflow em **oito cenários**: 320, 390, 900 e 1440 px × claro e escuro. Os cinco elementos auditados em cada cenário mantiveram fontes previstas e contraste calculado **≥ 4,5:1** na seleção e nos indicadores, com marca de seleção e sem overflow horizontal.

**Node local: 340/340 PASS**, excluindo `offline-export-manifest.test.mjs` intencionalmente, pois os arquivos do snapshot de ensaio anterior não constituem o checkout oficial da branch atual. O teste de regressão de origem está incluído nesse total. Não representar esta aferição como validação nativa completa do HEAD GitHub.

## Procedência e integridade remota

- Commit de implementação: `3a89b4b3e2f60887a6f680ad76458a20b56da84f`.
- Commit de repin: `04912d8a507ad28e13ccb25817ed54a8be4aadd9`.
- Manifesto `verify_offline_export.py` com `source_head` apontando para o commit da implementação, anterior à alteração do próprio verificador para evitar autopinagem.
- **58/58 hashes Git blob SHA-1 e tamanhos conferidos** contra a árvore oficial do novo repositório; nenhuma divergência. SHA do próprio verificador: `2003f941d224ea781475733474c5f9545de370e7`.
- Comparação FV-UI-039 → repin FV-UI-040: **2 commits, 5 arquivos alterados**, todos dentro de `frontend/`.
- `main` permanece em `dace737ab7afb7ae3f5a3a6f5cb522e6def8b43a`. Nenhum merge ou deploy realizado.

## Limitações e fronteiras

O teste Chromium foi executado em código de snapshot local derivado e com as novas regras de CSS, não em checkout autenticado do HEAD final. A conferência dos hashes remotos não equivale a execução dos testes remotos. Permanecem pendentes ensaios com leitor de tela, zoom real, auditoria WCAG integral e homologação funcional.

Sem backend, S0/S1, Meta/WhatsApp, OpenAI, Supabase ou banco. Nenhuma mudança em autorização por loja/equipe/caso, distribuição, estados comerciais, comprovação de envio, F03 ou dados privados.

**Anterior:** [FV-UI-039](./68_FV_UI_039_ALVOS_TOQUE_TEMAS_2026_10_24.md).
