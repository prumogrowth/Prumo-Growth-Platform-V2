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

A correção é local, sem mensagem enviada, acesso a dados reais, gravação bancária, OpenAI, Meta ou Supabase.

- **V8 sintético executado** sobre os 17 módulos extraídos do GitHub e `dom-fixture.mjs`: **67/67 testes** de `app.dom.test.mjs` e **15/15 testes** de `app.mobile.dom.test.mjs` aprovados. O executor adaptado executou as funções do arquivo de testes com asserções equivalentes, substituindo `structuredClone` e timers. **Não é execução do Node nativo**.
- **Verificação estática V8 de FV-UI-032:** **8/8 expressões** do novo contrato de origem foram exercitadas e aprovadas após ajuste da expressão de esclarecimento.
- **Node, Python e Chromium/Playwright nativos não executados nesta revisão.** O checkout autenticado e a revisão visual com tecnologia assistiva/zoom permanecem pendentes. As asserções novas em `browser.smoke.py` foram escritas, não executadas em navegador real nesta rodada.
- O repositório foi acessado pelo conector GitHub; `git ls-remote` falhou por resolução DNS no ambiente de execução. Um ZIP do SHA final da branch permitirá validação nativa de snapshot, **sem convertê-la em homologação de checkout Git**.

Nenhuma nota 19F/FV-22 foi reclassificada. A homologação autenticada de checkout e a revisão do redesign permanecem pendentes.

## Atualização posterior — execução nativa do ZIP recebido

O diagnóstico sobre ZIP integral do commit `138bf641` foi **executado e aprovado**: **57/57 hashes**, **20/20 testes Python**, **334/334 testes Node nativos** e **Chromium/Playwright PASS**. Os resultados anteriores de V8 acima são históricos da fase de implementação; o registro de execução nativa, junto à distinção entre commit do manifesto e commit exportado, está no **[relatório complementar FV-UI-032](./57_FV_UI_032_VALIDACAO_NATIVA_ZIP_2026_10_23.md)**. Permanecem pendentes a homologação do checkout Git, a auditoria manual de tecnologia assistiva e as integrações.

**Relatório anterior:** [FV-UI-031](./55_FV_UI_031_FOCO_APOS_NOTA_LOCAL_2026_10_23.md).
