# M19 — Reconciliação de status e evidências Meta (somente laboratório)

**Data:** 01/11/2026. **Frente:** WhatsApp/Meta. **Status:** M19-A/B/C demonstrados offline; M19-D e marco principal **abertos**. Não houve Graph, assinatura de POST por fonte real, banco hospedado, efeito WDC-13/C09, HTTP ACK ou envio.

## Fonte de requisitos e separação de competências

[WA-39 — contrato candidato](WA39_CONTRATO_CANDIDATO_EVIDENCIA_OUTBOUND_F02_S0_v0_1.md) e [Issue #9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9) distinguem o retorno Graph `API_ACCEPTED`, callback `sent`, `delivered`, `read`, `failed`, status `UNKNOWN`, dedupe por ocorrência e correlação S0. São **propostas, não contratos autenticados**. S0/S1 tem autoridade para vínculo da tentativa, persistência, cursor e projeção F02; Meta produz proposta de observação técnica; Infra provê custódia de chave/rota e origem autenticada; OpenAI não transforma evidência sintática em decisão comercial.

A base existente **não foi substituída**: `status-evidence.ts` valida sintaxe; `technical-reconciliation.ts` faz correlação in-memory sintética; WA-31/32/38 distinguem evidência tardia, assinatura/ingresso e ambiguidade. M19 adiciona ensaios de consistência no limite da WA-39. A branch recebeu **dois módulos laboratoriais complementares**, criados em sequência durante o mesmo desenvolvimento; eles **não** formam automaticamente um pipeline nem uma única interface estável. Não somar as respectivas saídas como provas independentes da mesma observação.

## M19-A — dois ensaios complementares e limites de autoridade

**1. `integrations/whatsapp-meta/wa19-status-reconciliation-offline.ts`: vínculo S0 alegado e ocorrência.** Confronta concessionária, App, WABA, número emissor, canal, caso, intento/tentativa, `wamid` e digest do destinatário com uma alegação S0 `wa19-s0-binding-claim.lab.v0.1`. Recebe lista de ocorrências `wa19-status-occurrence.lab.v0.1` com posição, corpo/digest, timestamp, erro técnico e todas as provas de origem/persistência marcadas **false**. Deduplica observações idênticas por ID de ocorrência, conserva eventos distintos e coloca em quarentena IDs reutilizados com payload divergente, `failed` contraditório e observações em tentativa invalidada. `delivered` ou `read` isolados **não fabricam** `sent`. Recheck compara snapshot e revisão/tempo da alegação original.

**2. `integrations/whatsapp-meta/wa19-status-evidence-reconciliation-offline.ts`: Graph alegado e lote de callback.** Confere a mesma tentativa/template/versão, concessionária, App/WABA/número emissor, caso e `wamid` entre um pedido sintético, um `wa19-graph-claim.lab.v0.1` e um lote de `wa19-callback-event.lab.v0.1`. O Graph pode estar alegadamente `API_ACCEPTED`, `EXTERNAL_UNKNOWN` ou `PROVIDER_REJECTED`. Mesmo 2xx/`wamid` não torna `sent` verdadeiro. Há dedupe exato por ID de ocorrência **e posição física do item no lote**, preservando digest de bytes originais e timestamps; conflito entre IDs reutilizados, `sent` e `failed`, status após alegada revogação ou `PROVIDER_REJECTED` contraditório entra em `LAB_QUARANTINED_CONFLICT`. `read` sem `sent` explícito permanece só `READ_OBSERVED`, sem retropropagação. `131049` é diagnóstico técnico, não desistência ou falha WDC-13. O status `LAB_LATE_HISTORICAL_UNVERIFIED` é histórico, sem credencial.

**Não há conversão ratificada entre os dois contratos:** um recebe binding S0 simulado e outro recebe Graph/callback/revogação simulados. Ambos mantêm `source_authenticated=false`, `attempt_correlation_verified=false`, `sent_verified=false`, `delivered_verified=false`, `read_verified=false`, `definitive_failure_verified=false`, `retry_external=false`, `ack_allowed=false`, `case_transition_authorized=false`, `production_authorized=false` ou equivalentes. Hash SHA-256 é fotografia de alegações, não assinatura, HMAC, comprovante S0 nem identificador civil.

## M19-B — testes adversariais

- **52 testes** no módulo `wa19-status-reconciliation-offline.test.ts` de vínculo S0 fake, isolamento de WABA/loja/número/canal/intent/tentativa, dedupe e colisão de ocorrência, status fora de ordem e contraditórios, observação invalidada, fonte falsificada, getter, stale/future e recheck, sem efeito comercial.
- **56 testes** no módulo `wa19-status-evidence-reconciliation-offline.test.ts` de interação de Graph fake com callback, `API_ACCEPTED` versus `sent`, timeout/estado desconhecido, duplicata/reordenação por posição física, `read` isolado, conflito `failed`/progresso, revogação tardia, `131049`, tenant/canal/template cruzados, getters, lotes esparsos/excessivos e recheck.

**Resultado de referência conjunto:** [CI 41328742682](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41328742682), commit `49b157ad4f39494e0b1cc3f0fe2d22d033376f95`: **1.875/1.875 testes Meta offline** (=1.767 anteriores +108 M19), **18/18 verificações PG17** históricas de ingresso S0/Meta em job distinto, dois jobs `success`, scanner ACK lexical aprovado. Runs intermediários com regressões em fixtures não são evidência final. CI do último commit documental é verificado independentemente. Esses 108 testes não equivalem a 108 cenários autenticados de operação real.

## M19-C — invariantes de WA-39 e contrato pendente

1. **Origem e vínculo:** callback só será útil quando o HMAC do POST original for validado com segredo App confiável, WABA/phone/loja/canal resolvidos de registry S0, digest e ocorrência preservados em recibo durável e `wamid` correlacionado ao `attempt_ref` persistido por S0. Ambos os módulos atuais recebem essas alegações por fixture, sem autenticá-las.
2. **Idempotência/ordem:** dedupe de **ocorrência** com batch/posição/digest/identidade; retransmissão HTTP não duplica evento, mas ocorrências distintas do mesmo `wamid` não são reduzidas a uma. Reprocessamento/ordenação, cursor durável, compensação, quarentena e leitura posterior exigem S0/Infra. Testes in-memory não são política durável.
3. **Sem inferência:** HTTP 2xx/`API_ACCEPTED` não prova `sent`; `read` e `delivered` não inventam `sent`; `failed` não prova falha definitiva; timeout/429/5xx não autorizam retry; código `131049` não determina abandono, venda ou regras de janela.
4. **WDC-13/C09 somente S0:** apenas S0 verifica `sent` técnico autenticado e falha definitiva de tentativa da cadência, conta **duas falhas consecutivas** ou reset, e avalia janela pós-humano de template final. A Meta não executa transição, não autoriza reenvio e não informa decisão comercial à F02.
5. **F02:** somente projeção interna versionada, autorizada, sem PII/segredos, depois de readback S0. Nenhuma das duas estruturas LAB é payload homologado para fornecedor OpenAI.
6. **Convergência entre ensaios:** requer contrato versionado comum, consenso interfrentes de fonte (binding e Graph), tratamento de eventos contestados/órfãos, identidade da ocorrência e resultados de agregação. Não aceitar ambos como duas confirmações independentes de envio.

## M19-D — pendências

- [ ] **S0/S1:** fonte hospedada/autenticada de tentativa e status, ingestão/receipt/replay com atomicidade e revisão monotônica, vínculo App/WABA/phone/template final, HMAC e readback; isolamento por tenant e idempotência/ordem (Issues [#2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2) e [#9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9)).
- [ ] **Meta/Infra:** callbacks reais e validação HMAC no limite de ingresso autorizado, canal/vault e testes de ambiguidade de bytes/assinatura, sem prover `HTTP ACK` por este classificador.
- [ ] **S0/OpenAI:** ratificação WA-39 de `PENDING_CORRELATION/CORRELATED_*/UNCERTAIN/CONFLICT/QUARANTINED` e projeção F02 (versão, tentativas, efeitos), com prova de `sent`/falha definitiva e separação de WDC-13/C09.
- [ ] **Homologação E2E:** casos de late/out-of-order, retries de webhook, duplicata de bytes, conflito de escopo, commit incerto e tampering, antes de merge/deploy/Graph. A autorização de envio real do M18-D segue pendente na #10.

**Situação:** M19-A/B/C exercitados somente **offline**, nenhum status real homologado; **M19-D e M19 principal abertos**. Nenhum Graph, credencial, dado real, mensagem, banco produtivo, HTTP ACK, merge ou deploy.
