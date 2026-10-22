# WA-24 — Auditoria técnica inicial do PR #2 e reparos controlados (22/10/2026)

> **Tipo de registro: T (técnico), D (decisões apenas referenciadas), R (dependência interfrentes), V (homologação externa).** A documentação vigente [README](./README.md), [00 WDC](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md), [01 funcional](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md), [02 conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md), [WA-22](./wa22-revisao-cruzada-outras-frentes-contratos-2026-10-22.md), [WA-23](./wa23-auditoria-final-documentacao-propria-2026-10-22.md) tem precedência. Esta auditoria de código **não altera decisão de negócio**. **Não equivale a homologação**.

## 1. Escopo, proveniência e corte

- Repositório: `prumogrowth/Prumo-Growth---Platform`, [PR #2](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2), branch `docs/whatsapp-meta-concessionária de demonstração-poc-20261017`, base `main`. Antes dos reparos: HEAD `c0a767b9d8b1484743b0cbe425676dbc16dcce48`, **Draft**, aberto, não merged, 396 commits e 146 arquivos alterados. Fontes acessadas pela conexão GitHub.
- Foram recuperados os seis documentos obrigatórios na ordem de referência e cruzados com índice técnico, código, suítes, SQLs, workflow, evidências de CI e metadados dos PRs #1/#3/#5/#7/#8/#12. A auditoria é **estática de código e contrato**, complementada com evidência histórica de CI; não representa cobertura dinâmica de todos os caminhos nem execução em Meta/Supabase.
- Inventário inicial de arquivos: **63** docs Markdown da frente, **25** módulos TS, **33** suítes `*.test.ts`, **19** arquivos em `lab/`, **4** auxiliares (`README` técnico, contrato JSON MCP, runner bash e referência Python), **2** itens de apoio PR (workflow próprio e README raiz): **146**. Este WA-24 acrescenta um Markdown, elevando os docs para **64** e os arquivos do PR para **147** (caso nenhuma alteração simultânea).
- Contagem textual das 33 suítes: **519 ocorrências estáticas de `test(`**. Não usar como total de execuções, sucessos nem prova de runners atuais. Gate focado WA-16/17: **10+18+16 = 44 definições** preservadas após os reparos.

## 2. Inventário exato dos componentes

### 2.1 Módulos TypeScript (25)

- [`attempt-binding.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/attempt-binding.ts)
- [`attempt-commit-simulation.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/attempt-commit-simulation.ts)
- [`credential-lifecycle.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/credential-lifecycle.ts)
- [`credential-routing.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/credential-routing.ts)
- [`durable-receipt.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/durable-receipt.ts)
- [`graph-outbound.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/graph-outbound.ts)
- [`graph-template.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/graph-template.ts)
- [`inbound.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/inbound.ts)
- [`internal-proof-wire-v1.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/internal-proof-wire-v1.ts)
- [`lifecycle-simulation.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lifecycle-simulation.ts)
- [`offline-dispatch.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/offline-dispatch.ts)
- [`recovery-journal.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/recovery-journal.ts)
- [`routed-webhook.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/routed-webhook.ts)
- [`s0-binding-bridge.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/s0-binding-bridge.ts)
- [`s0-handoff-contract.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/s0-handoff-contract.ts)
- [`s0-ingress-gateway.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/s0-ingress-gateway.ts)
- [`s0-technical-binding-contract.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/s0-technical-binding-contract.ts)
- [`s0-unknown-commit-recovery.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/s0-unknown-commit-recovery.ts)
- [`status-evidence.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/status-evidence.ts)
- [`technical-keys.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/technical-keys.ts)
- [`technical-reconciliation.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/technical-reconciliation.ts)
- [`template-catalog-control.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/template-catalog-control.ts)
- [`template-mcp-multiformat.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/template-mcp-multiformat.ts)
- [`transactional-ingress.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/transactional-ingress.ts)
- [`verify-get.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/verify-get.ts)

**Cobertura funcional por família:** entrada/HMAC/GET/roteamento e ciclo de segredo (WA-01/04); descrição de requisições Graph texto/templates e despacho falso (WA-02); recepção/recibo/handoff S0 e provas internas (WA-05/06); chaves/status/escopo/índice bidirecional/commit incerto e recuperação (WA-08 a WA-16); catálogo BODY e rascunhos multimídia/catálogo MCP documental (WA-17). Predominam **funções puras e simulações em memória**; `Fake*`, `ack_allowed:false`, `production_authorized:false` não constituem conexão produtiva.

### 2.2 Suítes de testes TypeScript (33)

- [`attempt-binding.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/attempt-binding.test.ts)
- [`attempt-commit-simulation.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/attempt-commit-simulation.test.ts)
- [`credential-lifecycle.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/credential-lifecycle.test.ts)
- [`credential-routing.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/credential-routing.test.ts)
- [`cross-contract.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/cross-contract.test.ts)
- [`durable-receipt.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/durable-receipt.test.ts)
- [`graph-outbound.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/graph-outbound.test.ts)
- [`graph-template.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/graph-template.test.ts)
- [`inbound.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/inbound.test.ts)
- [`internal-proof-wire-audit.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/internal-proof-wire-audit.test.ts)
- [`internal-proof-wire-v1.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/internal-proof-wire-v1.test.ts)
- [`lifecycle-simulation.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lifecycle-simulation.test.ts)
- [`offline-dispatch.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/offline-dispatch.test.ts)
- [`preaudit-gaps.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/preaudit-gaps.test.ts)
- [`recovery-audit.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/recovery-audit.test.ts)
- [`recovery-journal.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/recovery-journal.test.ts)
- [`routed-webhook.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/routed-webhook.test.ts)
- [`s0-binding-bridge.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/s0-binding-bridge.test.ts)
- [`s0-handoff-contract.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/s0-handoff-contract.test.ts)
- [`s0-ingress-gateway.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/s0-ingress-gateway.test.ts)
- [`s0-technical-binding-contract.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/s0-technical-binding-contract.test.ts)
- [`s0-unknown-commit-recovery.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/s0-unknown-commit-recovery.test.ts)
- [`scope-isolation.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/scope-isolation.test.ts)
- [`status-evidence.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/status-evidence.test.ts)
- [`technical-keys.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/technical-keys.test.ts)
- [`technical-reconciliation.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/technical-reconciliation.test.ts)
- [`template-catalog-control.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/template-catalog-control.test.ts)
- [`template-mcp-multiformat.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/template-mcp-multiformat.test.ts)
- [`transactional-ingress.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/transactional-ingress.test.ts)
- [`verify-get.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/verify-get.test.ts)
- [`wa01-audit.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/wa01-audit.test.ts)
- [`wa04-audit.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/wa04-audit.test.ts)
- [`wa06c-crossruntime.test.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/wa06c-crossruntime.test.ts)

### 2.3 Laboratório PG17, shell e Python (19)

- [`run-wa06d-ephemeral.sh`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/run-wa06d-ephemeral.sh)
- [`run-wa06d-local.sh`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/run-wa06d-local.sh)
- [`test_wa06d_ephemeral_runner.py`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/test_wa06d_ephemeral_runner.py)
- [`test_wa06d_runner.py`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/test_wa06d_runner.py)
- [`wa06d_pg17_atomicity.sql`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa06d_pg17_atomicity.sql)
- [`wa06d_pg17_postcommit_setup.sql`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa06d_pg17_postcommit_setup.sql)
- [`wa06d_pg17_postcommit_verify.sql`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa06d_pg17_postcommit_verify.sql)
- [`wa15c-produce-s0-commands.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa15c-produce-s0-commands.ts)
- [`wa15c_pg17_execute.sql`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa15c_pg17_execute.sql)
- [`wa15c_pg17_load_commands.sql`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa15c_pg17_load_commands.sql)
- [`wa15c_pg17_recover.sql`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa15c_pg17_recover.sql)
- [`wa15c_pg17_setup.sql`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa15c_pg17_setup.sql)
- [`wa16-assert-db-recovery.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa16-assert-db-recovery.ts)
- [`wa16-produce-unknown-commit-commands.ts`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa16-produce-unknown-commit-commands.ts)
- [`wa16_pg17_after_commit.sql`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa16_pg17_after_commit.sql)
- [`wa16_pg17_before_rollback.sql`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa16_pg17_before_rollback.sql)
- [`wa16_pg17_read_recovery_json.sql`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa16_pg17_read_recovery_json.sql)
- [`wa16_pg17_recover_unknown.sql`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa16_pg17_recover_unknown.sql)
- [`wa16_pg17_setup.sql`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/lab/wa16_pg17_setup.sql)

### 2.4 Apoio e integração (4 + 2 externos ao diretório)

- [`README.md`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/README.md)
- [`mcp-template-tools.v0.json`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/mcp-template-tools.v0.json)
- [`run-offline-tests.sh`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/run-offline-tests.sh)
- [`wa06c_reference.py`](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/integrations/whatsapp-meta/wa06c_reference.py)
- [Workflow WhatsApp/Meta offline](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/.github/workflows/whatsapp-meta-offline.yml).
- [README da raiz (contexto somente; não alterado nesta auditoria)](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/README.md).
- Os **63 documentos históricos/editoriais** da frente no corte inicial estão indexados nominalmente no [README WhatsApp/Meta](./README.md). Preservados; o presente relatório é o 64º.
- `mcp-template-tools.v0.json` especifica **12 interfaces passivas** e NÃO fornece MCP Server, identidade delegada, ferramentas instaladas ou autorização.

## 3. Matriz de conformidade às 22 decisões WDC — estado em 22/10

| Regra | Evidência atual de código/documento | Classificação / lacuna |
|---|---|---|
| WDC-01 | README/WA-23: plataforma sem marca; LiberaCred é crédita instituição financeira | **Conforme no texto normativo**; nomenclatura legada não define marca |
| WDC-02/03 | `credential-routing.ts`, `routed-webhook.ts`: escopo App/WABA/emissor/loja, HMAC e rotas de fixture | **Parcial offline [T]**; sem prova de propriedade real, delegações e números [V] |
| WDC-04 | `technical-reconciliation.ts`, `attempt-binding.ts`, `template-catalog-control.ts` | **Parcial em memória [T]**; sem persistência operacional separada `mensagens` / `envios_template` / `catalogo_templates` homologada |
| WDC-05/06 | `template-mcp-multiformat.ts` e JSON de 12 tools | **Contrato somente [T/R]**; sem MCP executável, ACL/dupla confirmação/auditoria protegida reais |
| WDC-07 | WA-17B monta rascunhos BODY/HEADER mídia ou texto/FOOTER/BUTTONS com validação restrita | **Parcial offline**; nenhuma aprovação Graph nem mídia real comprovada |
| WDC-08 | `createEditedContentVersion` preserva versão anterior em WA-17A | **Parcial**; não há edição autorizada/reatestado Meta real nem trilha persistida |
| WDC-09 | WA-17A antes permitia `configureVariableSources(APPROVED,...)`; teste WA17-06 exigia esse comportamento | **INCORRETO no corte inicial; corrigido defensivamente neste ciclo**, sem execução nativa comprovada |
| WDC-10 | `TemplateCategory` e `MultiFormatInput.category` representam categoria Meta, sem conjunto múltiplo de finalidades/grants | **Ausente** o filtro finalidades N:N e a matriz por finalidade |
| WDC-11/12 | Não localizado orquestrador de catálogo elegível/F02 com replanejamento por suspensão Meta | **Ausente**; separar de erro normal de entrega e respeitar outro PR |
| WDC-13 | Conciliação técnica `sent/delivered/read/failed` existe como fixture; não agrega duas tentativas finais consecutivas nem aplica `perdido` S0 | **Ausente a transição comercial operacional**; precisa guarda S0 e contador atômico |
| WDC-14/15/16 | Opt-out da outra frente S0 foi descrito como sintético na 01/WA-22; nenhum gate Meta real atribuído a este PR | **Dependente S0 [R]**; A não contamina B; botões negativos não são transições automáticas Meta |
| WDC-17 | Nenhum agregador de saúde/eficácia Meta real no adaptador | **Pendente**; não adicionar teto monetário automático |
| WDC-18 | Mídias/PII em contrato; não houve autenticação Meta real, processamento de documentos ou parecer LGPD/Banco | **Validação externa [V]** |
| WDC-19 | Workflow com Node/PG17, mas código novo sem corrida nativa confirmada | **Pendente [T]**; não chamar testes escritos de aprovados |
| WDC-20 | `GraphSendOutcome` distingue `API_ACCEPTED` de `sent`; conciliação preserva dimensões técnicas | **Parcial**; transições comerciais, fechamento humano, janela e C09 dependem de S0/CF-OP |
| WDC-21/22 | Assinatura humana `Consultor Nome:\nMensagem`, `Gestor Nome:\nMensagem`, `Diretor Nome:\nMensagem` definida na 01/WA-21 | **Ausente no emissor atual**; `graph-outbound.ts` recebe texto já composto, sem identidade humana autenticada/cargo snapshot |

**Aviso:** ausente no módulo Meta NÃO prova ausente em todos os PRs. Integrações de S0/OpenAI/S1 exigem contrato cruzado e aceite dos donos, não implementação unilateral.

## 4. Segurança, robustez e provas

- **HMAC:** `inbound.ts` autentica assinatura SHA-256 do corpo bruto antes de parse; `routed-webhook.ts` resolve App Secret por rota confiável e revalida configuração após awaits. Resultado **candidato offline**; não existe webhook produtivo validado.
- **Isolamento:** `credential-routing.ts` e `routed-webhook.ts` recusam cruzamento App/WABA/phone/canal por fixture. Ainda faltam vínculos reais, privilégio de serviço, RLS/persistência S0, vínculo cliente+concessionária, políticas de mídia e retenção [R/V].
- **Correlações:** `technical-keys.ts` marca hash como hint não dedupe; `attempt-binding.ts`, `technical-reconciliation.ts` e bridge usam escopo de App/WABA/número/`wamid`, tentativas e eventos por posição; falta fluxo durável/replay operacional.
- **Idempotência/commit incerto:** `transactional-ingress.ts`, `recovery-journal.ts` e `s0-unknown-commit-recovery.ts` são simulações fail-closed; não há permissão de ACK ou repetição Graph. O `ACK` só poderá ocorrer após persistência durável e recheck atomizado S0, nunca só por HMAC.
- **Entrega/falhas:** `classifyGraphSendResult` pode apontar `API_ACCEPTED` ou `PROVIDER_REJECTED`; isso não prova `sent`, elegibilidade comercial, nem aplica `perdido`. Callbacks fora de ordem, duplicados, incertos, tentativas concorrentes e reinício continuam assuntos de gate real.
- **Autorização de texto humano:** não confiar em prefixo fornecido pela IA/cliente. Autor, nome, cargo, controle do caso, janela 24h, integridade do texto final e evidência Meta `sent` precisam ser conferidos pelo backend [R].
- **Meta/Graph/segredos:** nenhum POST real, token, WABA real ou conta comercial foi acessado; qualquer relatório de sucesso offline não remove bloqueios [V].

## 5. Interfaces com outras frentes — observadas, NÃO editadas

Metadados GitHub revisados em 22/10: PR #1 **S0** `feat/s0-fundacao-prumo`; #3 **OpenAI** `feat/s2-openai-adapter-sintetico`; #5 **S1/pessoas** `feat/s1-002-equipe-prumo`; #7 **CF-OP** `docs/cf-op-02-cadeias-contextuais-20261018`; #8 **S0/OpenAI/F03** `coord/s0-openai-cfi01-c09-20261019`; #12 **CFI-01/S0** `feat/s0-cfi01-f03-auth-preflight-20261020`. Todos estavam Draft.

A [WA-22](./wa22-revisao-cruzada-outras-frentes-contratos-2026-10-22.md) traz **XWA-01..12**. Contratos a harmonizar sem editar terceiros:
1. **S0/S1:** prova `human_message_sent` autenticada/correlacionada e propriedade do caso; `intake_paused` não impede resposta em caso mantido. Indicador `COUNT/DOT/NONE` de leitura humana é diferente do `read` de destino Meta.
2. **OpenAI F01/F02/F03:** F02 recebe catálogo filtrado e não cria template; F03 só é acionada por `explicit_human_close`, com histórico autorizado do mesmo cliente+loja até cutoff imutável e lock/recheck. Nenhuma IA atesta venda ou status bancário.
3. **CF-OP/CFI-01:** `last_inbound +24h`, conclusão humana e `final_template_sent +24h` C09 são marcos diferentes. Matriz C09 pós-humano, concorrência de cadeia vs template individual e consentimento exigem contrato ratificado.
4. **Campanhas/mídias:** origem oficial da oferta e elegibilidade antes de disponibilizar finalidade CAMPANHA; referência, política de retenção e autorização para mídia documental ainda [R/V].
5. **MCP:** protocolo, identidade do Diretor, auditoria protegida e confirmação são responsabilidade de outra frente. Aqui cabem apenas serviços internos de domínio autorizados.

## 6. Reparos efetivamente gravados na branch

| Ordem | Arquivo próprio | Divergência reparada | Evidência |
|---|---|---|---|
| R1 | `template-catalog-control.ts` | Bloqueia `configureVariableSources` fora de DRAFT/IN_REVIEW; exige mapeamento completo e ordenado antes de registrar `APPROVED`; valida a ordem no preparo de parâmetros | Commit `afb353cecbc080351e8e8a9db5288922d80c48` |
| R2 | `template-catalog-control.test.ts` | WA17-05/06/07/08/09/10/12/16 passam a distinguir edição anterior à aprovação, congelamento após aprovação e reprovação de versão sem bindings | Commit `df5398a8a5ea90007d61233058fa2444262b9b20`; **18 definições mantidas** |
| R3 | `template-mcp-multiformat.ts` | Prévia WA-17B carrega snapshot imutável de origem posicional e revisão, incluindo indicador de completude; recusa objetos com getters/protótipos impróprios e mapeamento em estado declarado aprovado | Commit `300079bb5a7d04cad0198399561b4c4c7ebb5da8` |
| R4 | `template-mcp-multiformat.test.ts` | WA17B-05/06 cobrem snapshot e getter hostil; **16 definições mantidas** | Commit `1ec841c596e3b915a5c50d3a4d63b200d87ffa21` |
| R5 | `.github/workflows/whatsapp-meta-offline.yml` | Corrige sintaxe YAML inválida de `name: WA-16B: ...` (segundo `:` sem aspas), causa concreta de workflow sem jobs; prefixo da etapa colocado entre aspas | Commit `f0d42245a377cef5ef788207f5cd566f2a836a3f`; GitHub voltou a iniciar jobs |

**Limite fundamental:** a WA-17B segue apenas preparadora de rascunho/prévia, sem estado persistido de aprovação, submissão ou serviço MCP real. O snapshot preparado deve ser revisto/comparado pelo serviço autenticado quando este for implementado. As mudanças **não concedem** licença de Graph nem realizam efeito comercial.

## 7. Validação e CI — classificação inequívoca

| Prova | Fonte verificável | Estado |
|---|---|---|
| Inspeção de assinatura de funções/guarda em TS WA17A/B e testes após commits | Releitura dos 4 arquivos com SHAs novos; presença de guards, mesmas 18+16 definições de testes | **PASS em verificação estática limitada**, não é teste funcional |
| Testes WA-16/17 `node --experimental-strip-types --test` (44) após os reparos | [Run 39775076366](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39775076366), job `meta-offline`, commit `f0d42245...`, 22/10 | **PASS 44/44, fail 0 — Node 22 nativo** |
| Regressão das 33 suítes atuais | [Run 39775076366](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39775076366), job `meta-offline`, logs do runner | **PASS 523/523, fail 0 — Node 22 nativo** (519 chamadas textuais de `test(` não eram contador confiável de casos dinâmicos) |
| WA-16 PG17 11 verificações + JSON→TS | [Run 39775076366](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39775076366), job `WA-15C contratos Meta TS + S0 PG17` | **PASS 11/11 WA16P + WA16C JSONB→TS**, com sessões PostgreSQL 17 distintas. Também **WA-15C 12/12 PASS** |
| CI prévio verde | GitHub Actions run [39401664926](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39401664926), commit `96c16ef24e6d1a263cd2657c4ca567c0a55916bc`, 20/10; três jobs PASS (regressão offline, WA-15C S0/PG17, WA-06D PG17) | **APROVADO HISTORICAMENTE**, código anterior ao gate 44 |
| Runs anteriores sem jobs | Ex.: [39504828861](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39504828861), [39774140443](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39774140443). Localizada linha 186 com `name: WA-16B: ...` sem aspas; PyYAML reproduziu `ScannerError`. | **Falha de sintaxe YAML corrigida em R5.** O run novo [39775076366](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39775076366) executou **3 jobs PASS**, conclusão global **success** |
| WA-06D PostgreSQL 17 descartável | [Run 39775076366](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39775076366), job `WA-06D PG17 descartavel` | **PASS 20/20 marcadores SQL, sem erros psql; 14 de atomicidade + 6 pós-COMMIT** |
| Homologação Meta/Graph/credenciais, banco hospedado, LGPD/instituição financeira | Nenhuma execução real autorizada/atestada | **NÃO HOMOLOGADO** |

Na sessão local não foi possível clonar o repositório privado por indisponibilidade de rede. **O GitHub Actions fez o checkout e EXECUTOU os testes nativos da branch com sucesso** no commit `f0d42245a377cef5ef788207f5cd566f2a836a3f`: Node WA16/17 44/44; regressão 523/523; PG17 WA06D 20/20, WA15C 12/12, WA16P 11/11 e classificação DB→TS. São testes **offline/em PG17 descartável e S0 Draft de laboratório**, não prova de API Meta, Banco, LGPD nem deploy. Eventos de erro PostgreSQL intencionais em cenários negativos não foram contados como falha do job, que terminou verde.

## 8. Plano priorizado após os reparos

| Prioridade | Trabalho e dono | Critério objetivo de aceite |
|---|---|---|
| **P0** | WA-17A/B e contrato do catálogo de bindings, **frente Meta** (R1–R4 já aplicados) | Revisão/versão imutável de origem aprovada; testes nativos + teste de concorrência; snapshots históricos sem remapeamento; falha segura |
| **P0 (CI concluído em laboratório)** | Manter workflow válido, execução automática e rastreio dos gates, **frente Meta** | **Cumprido no run 39775076366: 3 jobs success**; qualquer mudança posterior de código precisa de nova rodada; não confundir CI com homologação externa |
| **P0** | Segregação, HMAC, vínculo ativo e autorização operacional; **Meta + S0** | Ingestão durável/ACK por commit; replay sem duplicação; revogação concorrente; App/WABA/phone/loja validados; nenhum segredo exposto |
| **P1** | Registro versionado de finalidades múltiplas e grants por ator/fluxo, **domínio Meta; auth S0** | F02 só vê templates autorizados por finalidade/campanha; Meta category independente; isolamento entre concessionárias; versão/ACL não mutável por modelo |
| **P1** | Reconciliador de falhas definitivas por fluxo, **Meta como evidência + S0 comercial** | Uma falha=1; `sent` comprovado reseta; segunda falha consecutiva=cancelar fluxo e `perdido` técnico pela S0; duplicação/incerteza não contam |
| **P1** | Texto humano com assinatura, **S0/S1 identidade e Meta transporte** | `Cargo Nome:\nMensagem` automático, cargo/nome autenticados, preview=texto realmente enviado, prova humana e janela corretas; templates não recebem prefixo livre |
| **P1** | Relógios Meta / C09 / fechamento F03, **S0/CF-OP/OpenAI** | Eventos correlacionados e imutáveis; cutoff, concorrência e elegibilidade formal ratificados, sem C09 disparado por `API_ACCEPTED` |
| **P2** | Catálogo multimídia/revisão Meta e serviços domínio MCP, **Meta + futura MCP** | Prévia e confirmação de Diretor com auditoria; checagem de capacidades/estado Meta; sem enviar mídia ou dados antes de [V] |
| **P2** | Saúde dos templates, evidências e métricas, **Meta/gestão** | Métricas por template+versão+finalidade e denominadores distintos; nenhum bloqueio monetário automático; validações externas [V] |

**Sem merge, deploy, Meta Graph real, Supabase produtivo, alterações de outros PRs ou credenciais.** WA-24 registra reparos iniciados e lacunas objetivas, **NÃO** encerramento da auditoria técnica integral ou da frente. Prosseguir na ordem de P0 e só então novos recursos.
