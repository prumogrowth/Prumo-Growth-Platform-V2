# WA-04-AUD1 — Auditoria retroativa completa dos candidatos WhatsApp/Meta (18/10/2026)

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Escopo e decisão:** auditoria **sintética local** de todo o conjunto de módulos de laboratório da frente Meta ainda sem teste conjunto completo, com atenção especial às etapas **WA-04A/B/C** e à pendência de execução dos **quatro testes originais WA-01A/B/C/D**. Um defeito reproduzível foi reparado e sua regressão publicada. **GO somente para evolução sintética; NO-GO para integração ou envio real.**

A verificação do token definitivo continua **dependente de terceiro**. Não foi solicitada, usada, inspecionada ou alterada nenhuma credencial no Supabase, Meta ou GitHub.

## 1. Material auditado

Reproduzimos os arquivos reais do PR #2 na branch `docs/whatsapp-meta-concessionária de demonstração-poc-20261017` e conferimos hashes Git entre os arquivos do GitHub e os executados localmente:

- **11 módulos:** `inbound.ts`, `durable-receipt.ts`, `technical-keys.ts`, `verify-get.ts`, `graph-outbound.ts`, `graph-template.ts`, `offline-dispatch.ts`, `technical-reconciliation.ts`, `credential-routing.ts`, `routed-webhook.ts` e `credential-lifecycle.ts`.
- **16 arquivos de testes:** os 4 `*.test.ts` originais da WA-01, as suítes de Graph/outbound, template, dispatch, reconciliação, segurança e os testes WA-04, inclusive **`wa04-audit.test.ts`** adicionado nesta auditoria.
- **27/27 hashes Git coincidentes** no momento da revisão, incluindo `credential-lifecycle.ts` `80494e5f56924e61fd81ab1a9c7ccc648e6529a0` e `wa04-audit.test.ts` `da4a62eef3fed34dada919bfee7f290e5982ae89`.
- Projeto/branch S0: consultado o `docs/MAPA_MENTAL.md` para conferir a arquitetura e os gates. Não auditamos nesta rodada o código SQL/Postgres/S0 do PR #1, que segue sua própria frente, testes e bloqueios.

## 2. Defeito encontrado e reparado (WA-04C)

**Achado AUD-WA04-01 — gravidade moderada em código não operacional:** `planMetaLifecycleTransition` assumia que `registry.apps` sempre era um array. Com `apps` malformado, um valor com `.find` não chamável produzia **exceção**, em vez de um resultado sanitizado de negativa. Também era possível receber exceção de `structuredClone` ao processar um registro contendo campo adicional não clonável.

**Evidência antes:** o ensaio adversarial de `registry.apps = {}` falhou com `registry?.apps?.find is not a function`. Não houve impacto operacional, pois o módulo não está implantado.

**Correção:** exigir `Array.isArray(registry.apps)` antes de percorrer Apps; capturar erro da cópia estruturada e devolver `REGISTRY_OR_APP_DENIED` sem refletir o conteúdo. Sem autorizar, ativar, revogar ou modificar Apps reais.

**Evidência após:** `WA-AUD-01/02` e 8 outros cenários novos passaram. Revisado também o comportamento da revogação de App/canal e do staging de rotação quando aplicado **apenas à cópia fictícia do registro**: GET e POST bloqueados conforme o vínculo, outra concessionária preservada, ausência de ativação implícita. As etapas WA-04A/B permaneceram sem outros defeitos reproduzíveis nesta rodada.

## 3. Resultado reproduzido localmente

Ambiente: **Node.js v22.16.0**, **TypeScript v5.8.3**, tipos Node disponíveis localmente.

- **235/235 PASS**, sem falhas: 180 testes de regressão reunidos anteriormente + **10 casos adversariais WA-04** novos + **45 testes legados WA-01 originais** finalmente reexecutados (11 inbound, 10 receipt, 12 technical keys, 12 GET).
- `tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --allowImportingTsExtensions --skipLibCheck --esModuleInterop --types node` sobre todos os **27 arquivos** = **PASS**.
- Execução de testes: `node --experimental-strip-types --test <16 arquivos .test.ts>` — apenas arquivos do PR, sem conectar APIs. A suíte temporária de exploração `audit-probes.test.ts` (não publicada) **não** entra na contagem 235; a regressão permanente e publicada é `wa04-audit.test.ts`.
- A reprodução dos quatro testes originais WA-01 foi verificada **arquivo por arquivo com o hash Git atual**. O mapa mental foi atualizado para retirar a antiga ressalva de que esses quatro arquivos não teriam sido reexecutados.

**O significado do PASS é estritamente técnico e local:** confere somente os cenários projetados e a compatibilidade dos módulos candidatos; **não** é comprovação de HMAC real recebido da Meta, entrega de WhatsApp, confirmação de consentimento, segurança operacional de Secrets, coerência de um registry hospedado, capacidade de recuperar crash distribuído, prova transacional do ACK, idempotência externa ou comportamento com tráfego real.

## 4. Mapa mental — diagrama principal

Por solicitação do responsável, o **primeiro diagrama Mermaid**, e não apenas as notas inferiores, passou a mostrar **cinco vínculos estruturais relevantes** na ramificação WhatsApp:

1. **[D]** App/WABA/número emissor exclusivos por concessionária.
2. **[P offline]** GET verify e POST HMAC por App/rota confiável.
3. **[R S0]** inbox durável **antes** do ACK.
4. **[R]** token Meta depende de validação por terceira pessoa.
5. **[P offline]** saídas C03/C06/C12 pela outbox/Graph.

Não incluí no desenho cada função, teste, número de commit ou política interna: isso tornaria o mapa menos útil. Histórico técnico, evidência e gates permanecem no corpo de `docs/MAPA_MENTAL.md`. Futuras atualizações desse diagrama devem ocorrer **quando surgir um componente ou relacionamento arquitetural significativo**, não em toda alteração de testes ou detalhe de implementação.

Fonte visual: [MAPA_MENTAL.md, branch S0](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-fundacao-prumo/docs/MAPA_MENTAL.md).

## 5. Gates preservados

**Sem** CI remoto GitHub Actions nesta rodada, integração com Supabase hospedado, token Meta real, Graph API real, webhook comercial, número operacional concessionária de demonstração, migração, merge ou deploy. Os dois PRs seguem em Draft.

**Pendências impeditivas de operação:** verificação externa do token, decisão DEC-WA-04 sobre ambiente definitivo, DEC-WA-06 sobre credenciais/retensão/ACK/recuperação, mapeamento autenticado App/WABA/emissor→loja/canal, transação e prova de commit para cada ocorrência e autorização S0 atual C03/C06/C12. O fato de uma simulação permitir revogação não garante que um segredo já emitido foi revogado na Meta.

**Resultado:** código isolado revisado com sucesso após reparo. Próximo incremento técnico pode prosseguir **sem credenciais**, apenas com testes sintéticos, e o mapa mental deve crescer de forma seletiva.
