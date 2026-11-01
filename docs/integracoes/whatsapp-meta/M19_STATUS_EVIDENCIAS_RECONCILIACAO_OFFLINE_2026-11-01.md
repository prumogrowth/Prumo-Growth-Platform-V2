# M19 — Reconciliação de status e evidências Meta (somente laboratório)

**Data:** 01/11/2026. **Frente:** WhatsApp/Meta. **Status:** M19-A/B/C demonstrados offline; M19-D e marco principal **abertos**. Não houve Graph, assinatura de POST por fonte real, banco hospedado, efeito WDC-13/C09, HTTP ACK ou envio.

## Fonte de requisitos e separação de competências

[WA-39 — contrato candidato](WA39_CONTRATO_CANDIDATO_EVIDENCIA_OUTBOUND_F02_S0_v0_1.md) e [Issue #9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9) distinguem o retorno Graph `API_ACCEPTED`, callback `sent`, `delivered`, `read`, `failed`, status `UNKNOWN`, dedupe por ocorrência e correlação S0. São **propostas, não contratos autenticados**. S0/S1 tem autoridade para vínculo da tentativa, persistência, cursor e projeção F02; Meta produz proposta de observação técnica; Infra provê custódia de chave/rota e origem autenticada; OpenAI não transforma evidência sintática em decisão comercial.

A base existente **não foi substituída**: `status-evidence.ts` valida sintaxe; `technical-reconciliation.ts` faz correlação in-memory sintética; WA-31/32/38 distinguem evidência tardia, assinatura/ingresso e ambiguidade. M19 adiciona ensaios de consistência no limite da WA-39. A branch recebeu **dois módulos laboratoriais complementares**, criados em sequência durante o mesmo desenvolvimento; eles **não** formam automaticamente um pipeline nem uma única interface estável. Não somar as respectivas saídas como provas independentes da mesma observação.

## M19-A — dois ensaios complementares e limites de autoridade

**1. `integrations/whatsapp-meta/wa19-status-reconciliation-offline.ts`: vínculo S0 alegado e ocorrência.** Confronta concessionária, App, WABA, número emissor, canal, caso, intento/tentativa, `wamid` e digest do destinatário com uma alegação S0 `wa19-s0-binding-claim.lab.v0.1`. Recebe lista de ocorrências `wa19-status-occurrence.lab.v0.1` com posição, corpo/digest, timestamp, erro técnico e todas as provas de origem/persistência marcadas **false**. Deduplica observações idênticas por ID de ocorrência, conserva eventos distintos e coloca em quarentena IDs reutilizados com payload divergente, `failed` contraditório e observações em tentativa invalidada. `delivered` ou `read` isolados **não fabricam** `sent`. Recheck compara snapshot e revisão/tempo da alegação original.

**2. `integrations/whatsapp-meta/wa19-status-evidence-reconciliation-offline.ts`: Graph alegado e lote de callback.** Confere a mesma tentativa/template/versão, concessionária, App/WABA/número emissor, caso e `wamid` entre um pedido sintético, um `wa19-graph-claim.lab.v0.1` e um lote de `wa19-callback-event.lab.v0.1`. O Graph pode estar alegadamente `API_ACCEPTED`, `EXTERNAL_UNKNOWN` ou `PROVIDER_REJECTED`. Mesmo 2xx/`wamid` não torna `sent` verdadeiro. Há dedupe exato por ID de ocorrência **e posição física do item no lote**, preservando digest de bytes originais e timestamps; conflito entre IDs reutilizados, `sent` e `failed`, status após alegada revogação ou `PROVIDER_REJECTED` contraditório entra em `LAB_QUARANTINED_CONFLICT`. `read` sem `sent` explícito permanece só `READ_OBSERVED`, sem retropropagação. `131049` é diagnóstico técnico, não desistência ou falha WDC-13. O status `LAB_LATE_HISTORICAL_UNVERIFIED` é histórico, sem credencial.

**Contratos distintos, não intercambiáveis:** o ensaio de vínculo S0 mantém `wa19-status-request.lab.v0.1` / `wa19-status-snapshot.lab.v0.1`; o ensaio Graph usa `wa19-graph-status-request.lab.v0.1` / `wa19-graph-status-snapshot.lab.v0.1` após correção preventiva de colisão de nomes. **Não há conversão ratificada entre os dois contratos:** um recebe binding S0 simulado e outro recebe Graph/callback/revogação simulados. Ambos mantêm `source_authenticated=false`, `attempt_correlation_verified=false`, `sent_verified=false`, `delivered_verified=false`, `read_verified=false`, `definitive_failure_verified=false`, `retry_external=false`, `ack_allowed=false`, `case_transition_authorized=false`, `production_authorized=false` ou equivalentes. Hash SHA-256 é fotografia de alegações, não assinatura, HMAC, comprovante S0 nem identificador civil.

## M19-B — testes adversariais

- **57 testes** no módulo `wa19-status-reconciliation-offline.test.ts` de vínculo S0 fake, isolamento de WABA/loja/número/canal/intent/tentativa, dedupe e colisão de ocorrência, status fora de ordem e contraditórios, observação invalidada, fonte falsificada, getter, stale/future e recheck, sem efeito comercial.
- **58 testes** no módulo `wa19-status-evidence-reconciliation-offline.test.ts` de interação de Graph fake com callback, `API_ACCEPTED` versus `sent`, timeout/estado desconhecido, duplicata/reordenação por posição física, `read` isolado, conflito `failed`/progresso, revogação tardia, `131049`, tenant/canal/template cruzados, getters, lotes esparsos/excessivos e recheck.

**Evidência funcional atual:** [CI 41329194524](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41329194524), commit `343201aa92515139387feb046a2f5be6d30264b8`: **1.882/1.882 testes Meta offline** (=1.767 anteriores +115 M19), **18/18 verificações PG17** históricas de ingresso S0/Meta em job distinto, dois jobs `success`, scanner ACK lexical aprovado. Runs intermediários com regressões em fixtures não são evidência final. CI do último commit documental é verificado independentemente. Os 115 testes M19 não equivalem a qualquer cenário autenticado de operação real.

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


## Adendo de auditoria corretiva — 01/11/2026

A [auditoria M19](AUDITORIA_M19_RECONCILIACAO_STATUS_2026-11-01.md) corrigiu duas lacunas de integridade nos laboratórios complementares, **sem integrá-los**:

- No módulo de vínculo S0, o estado de quarentena antes registrava no hash somente o primeiro evento visto para um `occurrence_ref`; variantes conflitantes posteriores eram sinalizadas como conflito, mas podiam mudar de corpo, status, timestamp ou erro sem mudar a fotografia. Agora **todas as variantes distintas** entram no hash de forma canônica, com duplicatas exatas contabilizadas; `saw_*` inclui as variantes conflitantes, sem conferir `sent`.
- No módulo Graph/callback, a seleção da primeira ocorrência na posição/identificador poderia fazer o snapshot depender da ordem de chegada e omitir uma variante em conflito. Agora todas as variantes distintas são preservadas e ordenadas antes da detecção de colisão; **a quarentena continua obrigatória** e o hash cobre todos os campos de todas as variantes.

Por mudança semântica dos hashes, saídas de snapshot recebem versões distintas **`wa19-status-snapshot.lab.v0.2`** (vínculo S0) e **`wa19-graph-status-snapshot.lab.v0.2`** (Graph/callback); `v0.1` é recusada no recheck. As entradas dos dois ensaios conservam suas versões de laboratório anteriores e **não são convertíveis entre si**. A identificação do item físico pelo S0 continua insuficiente (falta identidade do lote/posição completa), e a origem Meta não está autenticada.

**Evidência funcional auditada:** SHA `3311caaa91034e93da533ce7748370e239538ecb`, [CI 41338646961](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41338646961), **1.902/1.902 Meta offline**: 67 testes S0 binding M19 (57 + 10 de auditoria), 68 testes Graph/callback M19 (58 + 10 de auditoria), total **135 M19**. Dois jobs `success`, scanner ACK lexical aprovado e **18/18 PG17 históricos independentes** de ingresso. Valores anteriores (115 M19/1.882 Meta) eram o estado antes da auditoria.

M19-D e marco principal continuam **[ ]**, sem serviço de status S0, HMAC real, prova `sent`, projeção F02, Graph, ACK, merge ou deploy.
