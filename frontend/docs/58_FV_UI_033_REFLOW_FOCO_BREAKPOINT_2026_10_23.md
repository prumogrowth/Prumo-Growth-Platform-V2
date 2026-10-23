# FV-UI-033 — Preservação de foco sob reflow e mudança de breakpoint

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** somente `frontend/`, fluxos sintéticos e testes.

## Achado reproduzido

Em Chromium, iniciar em **1440×900**, abrir o caso fictício A-102 e manter foco na aba **Resumo** de Detalhes; ao mudar para **360×500**, o estado móvel permanecia **Conversa**, a região **Detalhes** desaparecia por CSS e o navegador transferia `document.activeElement` da aba para fora do controle. A mudança de viewport difere do fluxo anterior de clicar numa conversa já em layout móvel.

Na direção inversa, uma aba aberta no celular podia tornar-se invisível no desktop porque `details-hidden` persistia do estado inicial de tela estreita.

## Correção visual

- Registrar o último foco em **Lista**, **Conversa** ou **Detalhes** somente fora de diálogos nativos.
- Agir **apenas** quando o breakpoint `max-width:760px` muda; resize dentro de um mesmo modo não rouba foco.
- Na passagem desktop→móvel, selecionar o painel que continha o foco. Se o browser redefinir o foco durante o reflow, restaurar o elemento ainda conectado ao painel ou um controle de retorno/busca seguro.
- Na passagem móvel→desktop, conservar aberta uma aba Detalhes que estava ativa e sincronizar `aria-expanded`. Diálogos preservam o próprio foco, ajustando somente o painel subjacente.
- Não enviar mensagem, concluir atendimento, atribuir usuário, modificar dados de domínio, invocar F03, Meta, OpenAI, Banco ou Supabase.

## Testes

- `frontend/visual/tests/browser.smoke.py`: novas viagens **1440→360→1440** e **320→1440**, com asserts de aba visível, foco, `aria-expanded` e teclado Home/End; mais Lista/Conversa **1440→320** sem salto arbitrário ou overflow horizontal.
- `frontend/visual/tests/source-contract.test.mjs`: novo teste estrutural das salvaguardas e do roteiro Chromium.
- `frontend/visual/tests/dom-fixture.mjs`: suporte mínimo a assinatura de evento resize; a fixture **não simula CSS/viewport** e a prova de reflow depende de Chromium.
- `frontend/visual/app.mjs`: tratamento de transição de breakpoint sem atualização de regras ou integrações.

## Evidências nativas posteriores ao repin

O diagnóstico definitivo foi executado sobre **ZIP derivado da exportação entregue anteriormente**, contendo os 58 arquivos de `frontend/visual/` com bytes correspondentes aos blobs publicados, inclusive o verificador atualizado. **Não foi checkout Git autenticado nem foi exportado um novo ZIP oficial pelo GitHub.**

- Inventário do manifesto: **57/57 blobs válidos**; o 58º arquivo é o próprio verificador, confrontado byte a byte e não autopinado.
- `source_head` pinado: `6eb2df3433e88375317e682cdbdc279b6f4f5c38`; commit com repin: `ebd7f60e34ca9a786d156985a08ec813c92ba4b9`.
- Gate Python de testes adversariais do ZIP: **20/20 PASS**.
- Gate Node nativo: **335/335 PASS**, incluindo o contrato estático de FV-UI-033.
- Gate Playwright/Chromium real: **PASS**, incluindo as transições entre breakpoints e navegação por teclado.
- `native_snapshot_pass = true`, mas `git_checkout_verified = false` e `full_acceptance = false`.

Uma primeira execução sequencial havia identificado uma asserção imediata antes da entrega do evento `resize`, corrigida com espera por estado no Playwright. A repetição revelou ainda foco perdido na transição inversa móvel→desktop; a implementação e o teste foram corrigidos e **o gate completo foi repetido e aprovado**. Não foi ocultado resultado negativo ou classificado como sucesso antes do segundo ajuste.

A simulação de viewport de **360/320 pixels** representa reflow compatível com larguras efetivas reduzidas por zoom, **não teste manual de zoom do navegador, tecnologia assistiva ou WCAG integral**. Não testa S0/S1, Meta/WhatsApp, OpenAI, banco, persistência ou autenticação.

**[Registro detalhado do diagnóstico FV-UI-033](./59_FV_UI_033_GATE_NATIVO_SNAPSHOT_2026_10_23.md)**.

**Referência anterior:** [FV-UI-032](./57_FV_UI_032_VALIDACAO_NATIVA_ZIP_2026_10_23.md).
