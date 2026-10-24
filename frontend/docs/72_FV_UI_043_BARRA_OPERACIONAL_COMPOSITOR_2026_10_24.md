# FV-UI-043 — Barra operacional e compositor em claro/escuro

**Data:** 24/10/2026 · **Repositório oficial:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual`. **Escopo:** `frontend/` exclusivamente.

## Achados reais no código

A barra operacional `#workflow-bar` é renderizada por `renderThread()` e traz estado comercial, texto explicativo, janela Meta projetada, etapa humana e ações autorizadas pelo contexto do caso fictício. No CSS original, a classe `.status-indicator.human` recebia fundo verde escuro por uma regra global posterior, mas mantinha texto verde; no Chromium local, o caso ilustrativo **"em atendimento pelo operador"** atingiu apenas **1,11:1** de contraste. A regra de fonte móvel da janela Meta era 9px. O botão de prévia da composição tinha **43px** de lado em dispositivos móveis.

## Modificações

- A barra mantém **todos os rótulos e ações originais** e sua rolagem em viewport curta; tipografia de etiquetas e notas auxiliares ≥11px, quebra segura e espaçamento regular.
- Diferenciação dos estados `human`, `ai`, `bank`, `success` e `danger` com cores de fundo/texto específicas para tema claro/escuro. O tom de texto da etiqueta `human` foi corrigido contra o conflito global anterior.
- Botões operacionais da barra: altura mínima 44px, sem alterar ordem, quantidade ou `disabled`.
- Campo e botão do compositor: altura/largura-alvo de 48px; campo 14px no desktop/tablet e 16px no celular; foco visível. A indisponibilidade da composição recebe estilo discreto diferenciado, sem alterar `canMockMessage()`, `projectedMetaWindow()` ou fluxo de confirmação por prévia.
- Os avisos `NÃO ENVIADA`, `ACK != entrega`, janela de 24h e restrições de template continuam com a mesma semântica e conteúdo. Nada foi ocultado para simplificar a tela.

## Testes executados e limites

O código CSS proposto foi aplicado a um **snapshot local derivado FV-UI-036** (não checkout autenticado do HEAD oficial). Em Chromium real foi aferido **8/8 cenários PASS**: 320, 390, 900 e 1440px × temas claro/escuro. Verificados: região de conversa visível, etiquetas e nota com fontes ≥11px, contraste ≥4,5:1 para estados efetivos e cinco variantes inseridas apenas para auditoria visual, campo e botão ≥48px, tamanho do texto móvel ≥16px, ações com alvo ≥44px, aparência de controles desabilitados e ausência de overflow horizontal. Nenhum envio foi efetuado.

No mesmo snapshot local, Node sem `offline-export-manifest.test.mjs` resultou em **339/339 PASS**, refletindo a suíte disponível naquela base (e não a suíte completa da versão publicada).

A verificação integral da árvore Git, inventário de blobs e repin de manifesto serão documentados depois da publicação. **Conferência remota de hashes não equivale a executar a suíte nativa em checkout oficial.** Permanecem pendentes gate integral autenticado, WCAG completo, zoom real e avaliação humana.

## Limites funcionais

Somente apresentação. Sem chamadas S0/S1, dados reais, Auth/RLS, Meta/WhatsApp, OpenAI, Supabase, banco, mudanças em papéis, lojas, permissões, distribuição, conclusão, estados comerciais ou transporte. Sem deploy e sem merge na `main`.

**Anterior:** [FV-UI-042](./71_FV_UI_042_LEGIBILIDADE_CONVERSA_2026_10_24.md).
