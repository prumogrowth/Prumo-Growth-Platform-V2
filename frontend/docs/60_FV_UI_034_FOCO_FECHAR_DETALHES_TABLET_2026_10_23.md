# FV-UI-034 — Fechar painel de Detalhes em tablet sem perder o foco

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** exclusivamente `frontend/`, protótipo fictício. **Não homologado**.

## Achado reproduzido em Chromium

Nas larguras de **900 e 1024 CSS pixels**, abrir o caso fictício A-102 e a lateral Detalhes e, em seguida, ativar **Fechar detalhes** deixava `document.activeElement` em `#detail-close` **depois** de ocultar seu contêiner. O controle permanecia invisível ao teclado. Um **Escape** com foco na aba Detalhes não fechava a lateral (esse atalho antes era apenas móvel).

## Implementação

- `app.mjs`: helper `closeFloatingDetails()` recusa ação fora de 761–1040px, com painel já oculto ou com diálogo nativo aberto; oculta o painel, atualiza `aria-expanded=false` e foca o botão visível `#detail-toggle`. Botão **Fechar detalhes** passa a chamá-lo.
- Um **Escape** é aceito somente quando foco está **dentro** da lateral flutuante e não está em campo de edição, e nenhum diálogo está aberto; assim o rascunho de nota não some ao pressionar Escape no textarea. O Escape móvel anterior é preservado.
- `tests/dom-fixture.mjs`: suporte a `tablet:true` e `contains()` com relação pai–filho mínima entre região e conteúdo; mock de viewport continua **não** emulando CSS.
- `tests/app.tablet.dom.test.mjs`: quatro regressões dedicadas — botão Fechar, Escape no painel, Escape no compositor e diálogo modal protegido. Nenhuma alteração de casos, permissões ou notas.
- `tests/validation-layers.json` e `validation-layers.test.mjs`: inclusão explícita da nova suíte em **interaction** (obrigatório pelo FV-UI-030).
- `tests/source-contract.test.mjs` e `tests/browser.smoke.py`: contrato estático e Chromium real com Enter/Escape, foco restaurado, `aria-expanded`, não perda de nota e ausência de overflow nas duas larguras.
- `README.md` e índice de decisões atualizados; manifesto offline repinado **após** as últimas alterações visuais.

## Evidências e limites

- Antes da correção, Chromium confirmou foco oculto e Escape sem ação em **900/1024px**.
- Após correção, smoke completo Chromium local: **PASS**, inclusive as novas jornadas.
- Node nativo direcionado: **130/130 PASS** em `app.dom`, `app.mobile.dom`, `app.tablet.dom` e `source-contract`.
- Node nativo, excluindo somente a suíte offline ainda não repinada: **336/336 PASS** após atualizar a taxonomia de camadas. A validação integral sobre snapshot final é uma etapa separada posterior ao repin.
- A persistência do estado `details-hidden` entre testes do mock exigiu abrir condicionalmente o painel em cada caso da nova suíte; isso é isolamento de regressão, não mudança comercial.
- Nenhum S0/S1, banco, Meta, WhatsApp, OpenAI, Supabase, autorização real, envio ou remessa foi executado. Snapshot ZIP derivado e checkout Git autenticado têm procedências diferentes. Sem aceite FV-22, deploy ou merge.

**Anterior:** [FV-UI-033](./59_FV_UI_033_GATE_NATIVO_SNAPSHOT_2026_10_23.md).
