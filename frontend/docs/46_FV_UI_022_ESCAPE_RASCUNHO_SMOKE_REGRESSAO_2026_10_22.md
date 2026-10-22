# FV-UI-022 — Escape, rascunho e integridade do smoke Chromium
**Data:** 22/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Situação:** correções implementadas em protótipo, **não homologadas em navegador nativo**.

**Precedência:** [FV-DOC-03](./38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md), [FV-UI-017](./41_FV_UI_017_INTEGRIDADE_CONTEXTO_MENSAGENS_2026_10_22.md) e [FV-UI-021](./45_FV_UI_021_PREPARACAO_S0_S1_ACESSIBILIDADE_2026_10_22.md). Continuam as decisões de nomenclatura pública Diretor/Gestor/Consultor e o escopo **estritamente frontend**.

## Alterações realizadas

| Área | Correção | Garantia/limite |
|---|---|---|
| Navegação móvel via Escape | `app.mjs` centraliza o retorno `detail → thread → list` na função `mobileBackNavigation()`, compartilhada por botões e Escape, transferindo o foco para `detail-toggle` ou `search-input` conforme a tela. | O Escape não faz navegação quando a digitação está em campo de entrada ou há diálogo modal aberto. Nenhum evento S0/S1, alteração de titular, atendimento ou leitura é emitido. |
| Cancelamento da prévia de mensagem | Ao cancelar/Escape na prévia de autoria, devolve o foco ao compositor **somente se ator, caso e loja ainda coincidirem e a ação permanecer elegível**. Confirmação válida adiciona apenas mensagem marcada `local_demo_not_sent`, com foco no compositor ainda acessível. | Não permite reutilizar confirmação após troca de contexto, não envia via Meta e não transforma rascunho em mensagem entregue. O texto cancelado permanece apenas no mesmo contexto válido e não migra de caso. |
| Mock de teste | `tests/dom-fixture.mjs` agora representa `search-input` e `message-input` como nós `INPUT`, além de `queue-assignee` como `SELECT`; anteriormente os campos eram `DIV`. | Correção importante para tornar realista a guarda por `document.activeElement.tagName`. O mock continua sem CSS/layout, leitor de tela ou ciclo nativo do `dialog`. |
| Smoke Chromium atualizado | `tests/browser.smoke.py` passa a exigir **12 casos** da supervisão de Marina (incluindo A-117 case-only), não os 11 anteriores à FV-UI-018. Incluído percurso de Escape/cancelamento/foco/rascunho e volta entre telas móveis. | O roteiro foi **alterado, mas não executado em Chromium nativo**. Expectativas ainda dependem da validação no checkout autorizado. |
| Contrato estático | `tests/source-contract.test.mjs` verifica a contagem atual da supervisão, o percurso FV-UI-022 no smoke, o retorno de Escape sem foco oculto e a tipagem correta dos inputs no mock. | Verificação de código-fonte, não substituto de experiência acessível em navegador real. |

## Evidência desta rodada

Fontes recuperadas pela conexão GitHub e avaliadas por V8 com o DOM sintético da própria frente:

- `app.dom.test.mjs`: **60/60** verificações aprovadas.
- `app.mobile.dom.test.mjs`: **13/13** verificações aprovadas (incluindo a nova proteção durante digitação/modal).
- `attention-integration.test.mjs`: **7/7** verificações aprovadas, preservando leitura e pendência do titular.
- `source-contract.test.mjs`: **35/35** verificações aprovadas (inclui smoke e mock).
- **115/115 verificações deste recorte**, sem afirmar que isso representa todos os testes do projeto. O runner de 25 suítes e a matriz de 16 critérios não mudaram e **não foram executados por inteiro nesta rodada**.

**Bloqueio material:** o ambiente de execução tem Node e Chromium instalados, mas não dispõe de checkout autenticado dos arquivos privados do Frontend. O único ZIP fornecido no contexto contém documentação histórica, não o código `frontend/visual`. Por isso não há prova de `node --test` nativo, Playwright/Chromium, acessibilidade por leitor de tela, RLS, S0/S1, Meta, OpenAI/F03, banco ou homologação FV-UI-013. A referência histórica `19F = 69/100` não foi recalculada.

## Gate de qualidade ainda necessário

Em um **checkout autenticado e limpo** de `feat/frontend-plataforma-visual`, executar o runner nativo com SHA completo do commit auditado, sem `--skip-browser`, incluindo todas as 25 suítes e o smoke Chromium:
```bash
python3 frontend/visual/tests/run_acceptance.py --expected-head <SHA_COMPLETO>
```
Depois validar 320/390/900/1440 px, altura reduzida, zoom, teclado e tecnologias assistivas reais. A aceitação depende da evidência nativa e de contratos ratificados; não iniciar merge, deploy ou integração produtiva com base nestes testes sintéticos.

**Não foram alterados** S0/S1, backend, DB, RLS, APIs, Meta, OpenAI, MCP, contratos de outra frente, branches alheias ou ambiente produtivo.
