# FV-UI-032 — Retorno de foco na extração fictícia e navegação O5

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** somente `frontend/` e fixtures. **Não homologado**.

## Problema e correções

1. Após selecionar um dos resultados técnicos fictícios na aba **Extração**, o botão de origem é recriado. Agora o foco retorna à nova aba Extração, e o aviso de contexto `role="status"` identifica o resultado **simulado**.
2. O botão **Visualizar retorno fictício de esclarecimento** desaparece depois de ativar o cenário alternativo. O foco é restaurado na aba Extração e o anúncio deixa explícito o contexto demonstrativo. Não há reabertura real, F03 executada, gravação ou remessa.
3. O botão O5 de vínculo entre dois casos já existentes também é descartado durante a navegação. No desktop/tablet o foco passa à região de conversa `#thread-pane` identificada pelo título e com `tabindex="-1"`; no celular, ao botão **Voltar** `#thread-back`. O destino é anunciado somente depois de ser confirmado pelos checks já existentes de autorização contextual e reciprocidade do vínculo.

Para restaurar o foco na Extração, o novo helper verifica **caso atual**, aba, ausência de modal aberto e painel visível no contexto de viewport. A lógica de permissões, documentos bancários, S0/S1, concessionárias e estados comerciais não foi modificada.

## Implementação e regressões

Arquivos: `frontend/visual/app.mjs`, `index.html`, `tests/app.dom.test.mjs`, `tests/app.mobile.dom.test.mjs`, `tests/browser.smoke.py`, `tests/source-contract.test.mjs`, `README.md` e o índice em `frontend/docs/`. O manifesto `tests/verify_offline_export.py` é repinado **após** as mudanças visuais.

Foram adicionados três testes DOM desktop, um móvel, um contrato estático e verificações Chromium para seleção de resultado, esclarecimento e navegação O5 desktop/móvel.

## Evidência e limites

A correção é local, sem mensagem enviada, acesso a dados reais, gravação bancária, OpenAI, Meta ou Supabase. A regressão V8, se realizada, deve ser identificada separadamente de Node nativo; nenhuma asserção Playwright é considerada aprovada apenas por existir no roteiro. A homologação autenticada de checkout e a revisão do redesign permanecem pendentes.

**Relatório anterior:** [FV-UI-031](./55_FV_UI_031_FOCO_APOS_NOTA_LOCAL_2026_10_23.md).
