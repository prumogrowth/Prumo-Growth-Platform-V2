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

## Evidências e limitações

Durante desenvolvimento, o novo smoke completo Chromium retornou **PASS**, incluindo os testes originais. Testes Node focados (`app.dom`, `app.mobile.dom`, `attention-integration`, `source-contract`) retornaram **132/132 PASS**. A suíte Node completa depende de repin do manifesto do novo snapshot: antes do repin, falha **intencionalmente** na comparação de SHA/tamanho, pois os arquivos alterados já não correspondem à versão anterior.

Os tamanhos simulam **reflow por CSS pixels equivalentes a 200/400%**; o ensaio não estabelece sucesso em zoom real de interface do navegador, tecnologia assistiva humana ou WCAG completo. A execução sobre ZIP derivado e a integridade do SHA final precisam ser documentadas separadamente após o repin. Mesmo com gates nativos, **não equivale a checkout Git autenticado ou homologação FV-22**.

**Referência anterior:** [FV-UI-032](./57_FV_UI_032_VALIDACAO_NATIVA_ZIP_2026_10_23.md).
