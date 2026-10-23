# FV-UI-036 — Base visual limpa e alternância claro/escuro

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** somente `frontend/`.

## Direção do redesign

Os critérios do responsável são: interface limpa, cores neutras, opção entre modo claro e escuro, e familiaridade com ferramentas de mensageria modernas, sem copiar o WhatsApp. A referência é de **organização e uso**, não de logotipos ou identidade de terceiros.

## Implementação

- Duas opções explícitas **Claro / Escuro** junto ao título da lista, com `aria-pressed` e controle por teclado.
- Tema inicial conforme `prefers-color-scheme` do sistema/navegador. Seleção manual permanece apenas enquanto a demonstração está aberta; não grava preferências em API, cookie ou storage.
- Revisão neutra das cores da central, superfícies, fila e balões; contraste com foco visível em claro/escuro.
- Tema dos diálogos nativos sincronizado no `body` porque ficam fora de `#visual-app`.
- Área de conversa, detalhes, gestão e permissões mantêm semântica anterior. Nenhuma edição cadastral, autenticação, atualização comercial ou chamada S0/S1, Meta/WhatsApp, OpenAI, Supabase ou banco foi criada.
- Arquivos: `index.html`, `styles.css`, `app.mjs`, mocks, testes Node/Chromium, README e manifesto offline; índice documental também atualizado.

## Verificação e limites

Testes sintéticos de DOM verificam seleção do tema e caso preservado. Smoke Chromium verifica transição claro/escuro em quatro tamanhos (1440, 900, 390 e 320 px), aparência calculada dos balões e superfícies, e preferência nativa escura com diálogo da equipe. Os gates completos e contagens constam do relatório FV-UI-036.

A interface é uma primeira base visual, não um design system final; auditoria integral de contraste WCAG, zoom real, leitores de tela, identidade visual definitiva e checkout Git autenticado permanecem pendentes.

**Anterior:** [FV-UI-035](./63_FV_UI_035_GATE_NATIVO_SNAPSHOT_2026_10_23.md).
