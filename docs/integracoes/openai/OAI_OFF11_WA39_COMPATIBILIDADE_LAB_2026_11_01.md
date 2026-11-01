# OAI OFF-11 — Compatibilidade de evidências WA-39 para a F02 (laboratório)

**Estado:** `CANDIDATO_OFFLINE_SEM_AUTORIDADE`. **Data:** 01/11/2026. **Solicitação existente:** [Issue #9 — OpenAI→Meta](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9) e, para autorização S0 do planejamento, [Issue #7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7). **Não criar demanda duplicada.**

## Base imutável

- Base auditada OpenAI OFF-02…OFF-08: commit `1f8157838c11a7b59456a3b178a8ade21a17b42b`; [CI dos 678/678 testes](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41268436358).
- [WA-39 v0.1 candidata](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/94338c3a36293f23dd88afe7773d5c1e622a1a8f/docs/integracoes/whatsapp-meta/WA39_CONTRATO_CANDIDATO_EVIDENCIA_OUTBOUND_F02_S0_v0_1.md) — proposta Meta, não contrato oficial de autorização nem endpoint.
- Componente F02 existente: `e04_offline_lab/f02-plan-boundary.mjs`, sem modificação. O OFF-11 **não** invoca `reviewF02Continuity` com uma flag `verified: true` inventada; uma projeção simulada não deve ser confundida com readback S0 autenticado.

## Entrega

- `e04_offline_lab/f02-wa39-consumer-lab.mjs`: função pura `previewWa39F02Projection`.
- `e04_offline_lab/tests/f02-wa39-consumer-lab.test.mjs`: matriz de 46 casos, incluindo cross-store/case/flow, versão stale, replay divergente, colisão de sequência, binding de tentativa+template, getters, ciclos, `131049`, inversão de `read/sent`, `API_ACCEPTED` e conflito entre `sent/failed`.
- `.github/workflows/oai-off11-wa39-lab.yml`: execução da suíte OFF-01 a OFF-11 na branch exclusiva; nenhuma alteração de `main`.

## Semântica conservadora

| Entrada candidata | Observação OFF-11 | NÃO significa |
|---|---|---|
| `API_ACCEPTED` | `API_ACCEPTED_NOT_SENT` | envio comprovado |
| `QUEUED`, `UNKNOWN` | espera/reconciliação | envio ou falha definitiva |
| `PENDING_CORRELATION` | aguarda vinculação | sucesso |
| `CORRELATED_SENT` | `SENT_CANDIDATE_UNVERIFIED` | readback autenticado S0 / início C09 |
| `CORRELATED_DELIVERED/READ` | `PROGRESS_WITHOUT_SENT_INFERENCE` | prova retroativa de `sent` |
| `CORRELATED_DEFINITIVE_FAILURE` | `FAILURE_CANDIDATE_UNVERIFIED` | `perdido`, WDC-13 ou desistência |
| `CONFLICT`, `QUARANTINED` | `REVIEW_REQUIRED` | plano contínuo automático |
| Erro `131049` | diagnóstico técnico | evidência comercial |
 
A entrada `prumo.openai.f02-wa39-consumer/0.1-lab` tem um escopo esperado e um snapshot **estritamente sintéticos**. `phase=GRAPH` admite apenas `API_ACCEPTED/QUEUED/UNKNOWN`; `phase=S0_RECONCILED` admite os estados de conciliação propostos WA-39. Referências, revisões, marcadores de template final, números de sequência e flags recebidas **não são prova criptográfica, identidade/autorização ou dado produtivo**. O código restringe esquema e cruza loja/caso/fluxo/revisões/tentativa/template, deduplica replay exato e devolve observações minimizadas, sem segredos de Meta.

Toda saída (positiva ou negada) preserva `sourceAuthenticated=false`, `metaProviderVerified=false`, `s0ReadbackVerified=false`, `sendAuthorized=false`, `schedulingAuthorized=false`, `c09Authorized=false`, `commercialTransitionAuthorized=false`, `productionAuthorized=false` e `requiresS0Recheck=true`. Não há Graph, API, SDK, SQL, credenciais, tempo real, envio ou efeitos comerciais.

## Lacunas que NÃO foram resolvidas

1. **#9 Meta/S0:** schema oficial de projeção assinada e readback persistido, autenticação de ocorrência, cursor/ordenação, idempotência transacional, resolução de `CONFLICT`, versão de recibo e origem confiável de `is_final_template`. A v0.1 WA-39 ainda é proposta.
2. **#7 S0/F02:** porta autorizativa, cadastro real de templates elegíveis, vínculo de cadeia/plano/campanha, propósito, consentimento por loja e versão, grants por principal e recheck antes de planejamento.
3. **#10 S0/Meta:** `PRE_DISPATCH` transacional, reserva/idempotência, consentimento, revogação, versão atual e readback na hora do envio. Código OFF-11 **não** chama essa porta.
4. **#5/#6 S0/F03** e **#11/#12 S0/F01** continuam pendentes; nenhuma competência foi transferida. O resumo compacto de IA para Frontend permanece **futuro** na #13, sem implementação nesta entrega.

## Critérios para evolução

Após ratificação S0/Meta, adaptar entradas ao contrato real, validar leitura autenticada/correlacionada e testar concorrência/replay/cutoff com fonte canônica — preservando idempotência, restrição de loja e autoridade única S0. Nenhuma observação do laboratório poderá virar `verified:true` por coerção ou simplesmente pela passagem em testes.

**Entrega de laboratório não equivale a integração aceita, deploy, merge ou produção.**
