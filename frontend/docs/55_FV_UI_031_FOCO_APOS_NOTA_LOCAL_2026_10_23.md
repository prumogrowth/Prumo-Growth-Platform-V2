# FV-UI-031 — Retorno do foco após inclusão de nota fictícia

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** exclusivamente `frontend/`, comportamento visual sintético. **Sem homologação.**

## Origem e correção

O editor de notas da aba **Notas** em `renderDetails()` recria o formulário com `replaceChildren` ao aceitar uma nota fictícia. O campo ou botão que iniciou a inclusão deixa de integrar o DOM e, sem reposicionamento explícito do foco, o teclado perde a referência para a próxima anotação. É um risco de acessibilidade da mesma família encontrada no FV-UI-029, agora fora dos modais de equipe.

A rotina de sucesso conserva todas as condições anteriores (caso selecionado, elegibilidade de nota, escopo e lista ativa). **Somente após** atualizar o array local de notas e reconstruir o painel, move o foco para o novo `#note-text`. O novo campo permanece vazio e a mensagem de sucesso continua no toast com `role="status"`. O callback de um formulário obsoleto continua sem produzir nota, foco ou anúncio de sucesso. Nenhuma regra comercial, concessão, transferência ou preenchimento de cadastro mudou.

## Arquivos técnicos modificados

- `frontend/visual/app.mjs`: restauração do foco no campo recriado após inclusão elegível.
- `frontend/visual/tests/dom-fixture.mjs`: consulta local por ID no mock para refletir o novo elemento.
- `frontend/visual/tests/app.dom.test.mjs`: regressões para foco depois de nota e rejeição de callback obsoleto.
- `frontend/visual/tests/browser.smoke.py`: asserção `to_be_focused()` no fluxo existente de notas, em tamanhos percorridos pelo smoke.
- `frontend/visual/tests/source-contract.test.mjs`: guarda estática do comportamento e da cobertura.

O índice vigente, o README visual e este relatório foram atualizados. O manifesto de hashes é repinado separadamente **depois** da alteração final de `frontend/visual/`.

## Evidências e limitações

- Conferência estática de patch, presença das regressões e escopo `frontend/`: executada na preparação dos objetos Git.
- **Node, Python e Chromium da revisão FV-UI-031: não executados.** O checkout autenticado não está presente no ambiente local; `git ls-remote` não pôde acessar GitHub por falta de DNS, embora o conector GitHub funcione. Os resultados FV-UI-029 são apenas históricos.
- A prova de comportamento em DOM real, leitores de tela e zoom é **pendente**: a asserção Playwright foi registrada, não executada. Não equivale a homologação, release, merge nem aceite de FV-22.
- Para diagnóstico futuro: executar camadas `interaction` e `source`, depois Chromium; repetir todas as camadas se o redesign alterar DOM/fluxos. Checkout Git autenticado permanece gate formal separado.

**Referência anterior:** [FV-UI-030](./54_FV_UI_030_TESTES_POR_CAMADA_PREPARACAO_REDESIGN_2026_10_23.md). **Próxima prioridade:** auditoria de foco em demais ações que recriam conteúdo de abas (extração e novo contato), seguida de redesign visual pactuado e nova verificação de reflow/zoom.
