# FV-UI-041 — Leitura e organização visual do painel de detalhes

**Data:** 24/10/2026 · **Repositório oficial:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** apenas `frontend/`.

## Problema e decisão visual

A lista de conversas foi refinada no FV-UI-040, mas o painel lateral de Detalhes ainda usava abas e títulos de seções em 10px, propriedades e avisos em 11px. Em tema escuro, alguns avisos e rótulos mantinham as cores próprias de superfícies claras. A direção escolhida é **melhorar a legibilidade sem introduzir novos campos, seções, botões ou camadas de permissão**.

## Correção de CSS

- Identidade da ficha: nome em 15px e legenda do caso em 12px.
- Títulos de seções: 11px, cor neutra contrastante.
- Propriedades: 12px, espaçamento de 8px por linha e quebra segura de textos longos em rótulos/valores; sem truncar informações de estado.
- Abas existentes: 12px com altura mínima de 44px, mantendo `role=tab`, `aria-selected`, teclado e o mesmo conjunto de abas.
- Avisos de contexto: 12px e cores revisadas em claro/escuro, inclusive variantes de alerta e sucesso.
- Tema escuro: cor de rótulos e valores, divisórias, foco visual da aba e superfícies dos avisos com regras condicionadas a `data-theme=dark`.

## Ensaios executados

Em snapshot local **derivado do FV-UI-036**, foi aplicada esta correção. O primeiro teste encontrou o texto de um aviso informativo claro com contraste **4,11:1**, abaixo da meta para texto normal; sua cor foi corrigida e o ensaio repetido.

Após a correção:

- **Chromium/Playwright PASS**, incluindo o roteiro de regressão anterior disponível no snapshot e 8 cenários novos (320, 390, 900, 1440 CSS px × claro/escuro).
- Verificados: painel visível, identidade, títulos, propriedades, aba selecionada, troca Notas→Resumo sem perda de `aria-selected`, tamanho da fonte, contraste calculado **≥4,5:1** nos rótulos/valores, aba ativa e callout de notas, sem overflow horizontal.
- **Node local 340/340 PASS**, excluindo `offline-export-manifest.test.mjs` porque o snapshot local não representa os arquivos do HEAD oficial após FV-UI-036. Inclui novo contrato fonte FV-UI-041.

Esses resultados **não equivalem ao gate nativo integral sobre checkout autenticado do HEAD novo**. A verificação da integridade dos arquivos publicados será realizada separadamente via GitHub após repin do manifesto.

## Fronteiras preservadas

Todos os clientes, vendedores, concessionárias e resultados são **fictícios**. Nenhuma visibilidade D3/D4 foi ampliada. Sem alteração de atores, escopos, notas, extração, F03, distribuição, envio de mensagens, Meta/WhatsApp, OpenAI, Supabase, autenticação, banco, S0/S1 ou ações reais. Nenhum merge na `main` ou deploy autorizado.

**Anterior:** [FV-UI-040](./69_FV_UI_040_HIERARQUIA_LISTA_2026_10_24.md).


## Auditoria no repositório oficial (pós-repin)

- Commit de conteúdo e testes: `99f004cde3f79462e31bd684b468e3db5429ff25`.
- Commit de repin do inventário: `9d6c363a40c803e7d82343871ed6d48f5943e441`.
- Comparação com FV-UI-040: **2 commits e 7 arquivos alterados**, todos sob `frontend/`.
- Manifesto repinado com `source_head=99f004cde3f79462e31bd684b468e3db5429ff25`: **58/58 hashes Git SHA-1 e tamanhos iguais aos blobs da árvore oficial**, zero divergências. Blob do próprio verificador: `dbed21f06d3fee5277ac6b7f2f8a59e80ed08b9d`.
- Branch `main` permanece em `dace737ab7afb7ae3f5a3a6f5cb522e6def8b43a`. Não houve merge/deploy.
- Evidência de Node e Chromium: **ensaios locais sobre base derivada**, com a mudança aplicada, não execução de testes em checkout autenticado do HEAD GitHub. A integridade de blobs conferida remotamente não equivale a esse gate nativo pendente.
