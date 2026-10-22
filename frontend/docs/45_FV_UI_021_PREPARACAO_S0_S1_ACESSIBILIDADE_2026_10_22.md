# FV-UI-021 — Contratos candidatos S0/S1 e acessibilidade de navegação
**Data:** 22/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Estado:** protótipo visual sintético, **não homologado**.

**Precedência:** [FV-DOC-03](./38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md), decisões D-AL-01..10 e D-NOM-01; continuidade dos incrementos [FV-UI-019](./43_FV_UI_019_CONCLUSOES_F03_FICHA_VIVA_2026_10_22.md) e [FV-UI-020](./44_FV_UI_020_ERROS_TRANSPORTE_E_MATRIZ_ACEITACAO_2026_10_22.md).

## Mudanças concretas

| Área | Implementação | Restrição deliberada |
|---|---|---|
| Fronteira candidata S0/S1 | Novo `frontend/visual/integration-gate-view.mjs` compõe `stageProposedS0ReadEnvelope` e `stageCandidateCommandResult`. Distingue leitura estrutural, comando pendente/alegadamente aplicado/negado, envelope sem confiança e contexto cruzado divergente. | **Nenhuma** resposta tipada concede autenticação, acesso D3/D4, verificação de efeito, repetição automática ou mudança comercial. O resultado **não contém registros, PII, IDs da operação ou detalhes externos**. Não há `fetch`, conexão, chamada ou retry. |
| Isolamento por ator/loja | Quando envelopes candidatos de leitura e comando são fornecidos juntos, seus `actor_id` e `scope_ref` devem coincidir. Entrada inválida falha fechada. | Igualdade entre strings nunca substitui sessão GoTrue, grants/RLS, proteção de escopo por caso, auditoria ou prova emitida pelo S0. Camada **não conectada** à UI demonstrativa até contrato autenticado existir. |
| Acessibilidade de contexto | `index.html` cria região `#context-announcement` com `role=status`, `aria-live=polite`, sem dados bancários; atualizada no `app.mjs` após troca de ator fictício, loja, lista ativa/histórica ou caso. Link “Ir para conversas” passa a ter alvo focável via `tabindex=-1`. | Não comprova leitura por leitor de tela; apenas estabelece semântica e comportamento em mock. A região usa classe visualmente oculta mas acessível (`.sr-only`). |
| Teclado e mobile | Abas de detalhes aceitam **ArrowLeft/ArrowRight/Home/End**, mantêm apenas uma aba no tab order e reatribuem foco à ativa. Transições móveis lista → conversa → detalhes → volta agora posicionam foco no controle de retorno/entrada apropriado. | Foco verificado em mock, **não** em leitor de tela real ou browser nesta rodada. Evita colocar foco no compositor ou em controles ocultos após trocar tela. |
| Responsividade de altura e toque | Abas de detalhes com área mínima de 44 px, botões icônicos com alvos mínimos, e `min-height:0` em viewports com altura até 550 px. Smoke Chromium acrescentado para 390×844 e 900×480, transições de foco e ausência de overflow horizontal. | Smoke **alterado, não executado nativamente**. A avaliação visual de zoom, orientação, contraste e navegação por leitor de tela segue pendente. |

**Arquivos de código:** `integration-gate-view.mjs` (novo), `app.mjs`, `index.html`, `styles.css`.
**Testes:** `integration-gate-view.test.mjs` (novo), `app.dom.test.mjs`, `app.mobile.dom.test.mjs`, `dom-fixture.mjs`, `source-contract.test.mjs`, `browser.smoke.py`, `run_acceptance.py` e `acceptance-matrix.json`.

## Evidências da rodada

- **Executadas em avaliador V8 isolado**, a partir de arquivos recuperados na própria branch GitHub: `integration-gate-view.test.mjs` **8/8**, `app.dom.test.mjs` **58/58**, `app.mobile.dom.test.mjs` **11/11** e `source-contract.test.mjs` **34/34** — **111/111 cenários e verificações deste recorte**. O avaliador usa substitutos de `node:test`/`assert` e mock DOM: **não equivale a execução Node/Chromium/CI nativa ou a testes de segurança reais**.
- Inventário estático conectado: **25/25** suítes `*.test.mjs` existentes incluídas em `run_acceptance.py`; `integration-gate-view.test.mjs` aparece nos critérios FV-22-03 e FV-22-10 da matriz. **16/16** critérios continuam registrados: 13 `prototype_only`, 2 `partial`, 1 `external_blocked`. Categorias de cobertura **não** são percentuais de entrega.
- **Não executados:** `node --test` nativo, Playwright/Chromium, testes reais de teclado/zoom/leitor de tela, S0/S1, Supabase/GoTrue/RLS, Meta/WhatsApp, OpenAI/F03, bancos e deploy. Checkout Git privado não disponível no ambiente de execução. FV-UI-013 segue **não homologada** e referência histórica `19F=69/100` inalterada.

## Gatilhos de integração / próximos gates

1. **S0/S1** precisam fornecer sessão autenticada e projection minimizada por ator/loja/caso, grants e RLS, versões confiáveis e idempotência; só então pode existir transporte de leitura ou comando com proveniência verificável. A presente camada tipada é **somente preparação**, não implementação dessa integração.
2. **Meta e F03** exigem recibos e eventos confiáveis, cutoff imutável e estados de falha/reprocessamento autorizados. ACK/timeout não comprovam `SENT`, conclusão ou alteração cadastral; C13 não é editor acessível ao Consultor.
3. **Qualidade:** executar o runner nativo no checkout autorizado com HEAD completo, incluindo Chromium; verificar 320/390/900/1440 px, altura reduzida, zoom 200%/400%, ordem de foco, leitura por tecnologia assistiva e sensibilidade a redução de movimento. Documentar correções antes de declarar aceite.

**Proteções:** sem alteração das demais branches, APIs, esquemas, migrações, dados reais, automações, permissões, contratos de backend, merge, deploy ou produção.
