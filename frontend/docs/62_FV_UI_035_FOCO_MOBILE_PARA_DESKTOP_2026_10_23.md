# FV-UI-035 — Foco preservado na ampliação de mobile para tablet/desktop

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** exclusivamente `frontend/` e interações sintéticas.

## Falha reproduzida

Com Chromium real na viewport **390×844**, o usuário pode abrir uma conversa fictícia e manter foco no controle móvel **Voltar** (`#thread-back`). Ao ampliar para **1440×900**, o botão deixa de ser exibido e o navegador transfere o foco para o `BODY`. A mesma perda ocorria com `#detail-back` quando a aba **Detalhes** estava aberta. A versão de FV-UI-033 já corrigia a abertura do painel na expansão, mas não garantia foco visível para controles de navegação que desapareciam com a mudança de CSS.

## Correção

A transição `max-width:760px` móvel→tablet/desktop, no `resize` já existente de `app.mjs`, identifica qual botão **Voltar** móvel havia sido focado. Se o último controle for `thread-back` e o caso selecionado continuar válido, o foco passa para a região nomeada **`#thread-pane`** (já existente com `tabindex="-1"`). Se for `detail-back`, a aba ativa do novo painel **Detalhes** recebe foco, com `#detail-toggle` como fallback seguro; a lateral permanece aberta e sincronizada com `aria-expanded`.

O retorno não roda quando há um diálogo aberto; não muda o caso selecionado, identidade de loja, ator, permissões, conteúdo do atendimento, rascunhos, dados comerciais, envio ou registro. O tratamento de foco em outros controles persistentes continua com as regras anteriores de FV-UI-033 e FV-UI-034.

## Arquivos da implementação

- `frontend/visual/app.mjs`: restauração de foco específica para os dois botões móveis que deixam de ser visíveis.
- `frontend/visual/tests/browser.smoke.py`: quatro caminhos em Chromium real (Conversa/Detalhes × larguras destino 900px e 1440px); asserções de foco visível, caso correto, ausência de overflow e erro JS.
- `frontend/visual/tests/source-contract.test.mjs`: regressão estática do ramo defensivo e das jornadas do navegador.
- `frontend/visual/README.md`: orientação de operação e limites.
- `frontend/visual/tests/verify_offline_export.py`: repin do inventário após código/testes, preservando `source_head` da revisão de conteúdo.

## Evidência e gates

O erro foi reproduzido em Chromium antes da correção. Após o patch, os testes Node focados passaram em **131/131**; o smoke Chromium completo passou. O teste Node integral anterior ao repin apresentou **uma falha esperada de integridade** porque ainda comparava os novos bytes ao manifesto do FV-UI-034; **não** se confundiu essa falha com comportamento do produto. O manifesto foi então atualizado, e o gate sequencial completo passou (ver relatório complementar).

**[FV-UI-035 — registro de validação nativa](./63_FV_UI_035_GATE_NATIVO_SNAPSHOT_2026_10_23.md)**.

## Limites

Esses testes cobrem a interface local fictícia; não incluem leitor de tela humano, zoom real de navegador 200/400%, autenticação, S0/S1, integração Meta/WhatsApp, OpenAI, instituição financeira ou Supabase. Reflow em pixels CSS não equivale a aceite WCAG, liberação de frontend, merge, deploy ou homologação de checkout Git. A matriz de papéis e as restrições de acesso preexistentes continuam vigentes.

**Incremento anterior:** [FV-UI-034](./61_FV_UI_034_GATE_NATIVO_SNAPSHOT_2026_10_23.md).
