# M18 — Anteparo de despacho Graph API, exclusivamente offline

**Data:** 01/11/2026. **Frente:** WhatsApp/Meta. **Estado:** M18-A/B/C técnicos de laboratório; **M18-D e marco principal [ ]**. Este artefato NÃO envia mensagens, NÃO autoriza Graph, NÃO acessa credenciais/vault, NÃO recebe consentimento real e NÃO integra uma porta de produção S0.

## Decisões e fontes vigentes

O marco original M18 exige **despacho Graph real homologado com autorização específica, política de janela, revalidação, idempotência, rate limit e recuperação**. Esse marco **não** foi cumprido: somente modelagem e regressões sem efeitos externos estão autorizadas.

A [Issue #10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10) tem contrato S0 **`prumo.s0.pre-dispatch.pg17/0.1-lab-only`**, implementado em PostgreSQL 17 descartável no commit `078ba2c4dbd17adfb89355067e3cc656b4ba6b72`. Essa porta confere caso, consentimento, supressão, template, grant, revisões M09 e registra uma reserva/reatribuição na mesma transação de fixture. **A função devolve resultado ANTES do COMMIT do chamador; mesmo `LAB_RESERVATION_RECORDED_NO_DISPATCH` não é lease para Graph.** Não há validação de fonte hospedada, ativo real ou prova de janela Meta operacional. O consumidor Meta não pode converter a resposta em `send_authorized:true`.

A [Issue #8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8) contém cadastro/rota/App/WABA/grants por loja e depende de validação Infra. A [WA-39](WA39_CONTRATO_CANDIDATO_EVIDENCIA_OUTBOUND_F02_S0_v0_1.md) e [Issue #9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9) diferenciam `API_ACCEPTED`, `sent`, `delivered/read`, `failed`, timeout e contradição; a Meta apenas propõe observação, a S0 reconcilia efeitos. O ingresso HTTP ACK da [#2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2) é uma fronteira diferente.

## M18-A — Módulo de análise de fronteira

`integrations/whatsapp-meta/wa18-dispatch-boundary-offline.ts` oferece somente funções puras:

- `inspectWa18DispatchOffline(intent,s0Lab,bindingLab,rateLab)`;
- `recheckWa18DispatchOffline(previousCandidate,freshIntent,freshS0,freshBinding,freshRate)`;
- `classifyWa18GraphMockOffline(intent,observationMock)`.

**Entradas estritamente LAB**, não autenticadas:

1. `wa18-dispatch-intent.lab.v0.1`: seleção, `intent_ref`, `attempt_ref`, loja, App, WABA, `phone_number_id`, caso, serviço, template/versão, finalidade do template e do consentimento, campanha e revisão de plano, **oito revisões** S0 de caso/atribuição/política/supressão/consentimento/template/campanha/grant, revisão de registry, hash de conteúdo, hash de destinatário, relógio e freshness. Hash de destinatário é dado injetado, **não** prova de telefone validado.
2. Resposta **exata** `prumo.s0.pre-dispatch.pg17/0.1-lab-only`: aceita apenas `LAB_RESERVATION_RECORDED_NO_DISPATCH` para análise de coerência e exige **todas** flags de autoridade iguais a `false`. A saída `DENIED` ou `UNAVAILABLE` é recusada; qualquer `send_authorized:true` forjado também é recusado.
3. `wa18-s0-binding-claim.lab.v0.1`: alega a identidade exata de reserva (incluindo escopo completo, conteúdo e revisões), observação de readback, `LAB_HELD_NO_DISPATCH` e `LAB_COMMIT_CLAIMED`. **Não há obtenção de readback real:** as alegações são injetadas e podem ser mentirosas; o contrato S0 original não oferece esses campos no retorno, motivo pelo qual estão explicitamente separados como uma **proposta de handoff** a ratificar, jamais considerados autoridade.
4. `wa18-rate-budget.lab.v0.1`: alegação de orçamento por concessionária/App/emissor, revisão e idade, slots disponíveis e janela de throttle. Valor desconhecido, zero slots, throttle ativo ou leitura stale/future **negam**. **Não consome quota real**, nem implementa backoff, filas ou circuit breaker.

O resultado positivo do anteparo é `LAB_DISPATCH_COHERENT_NOT_AUTHORIZED` ou `LAB_RECHECKED_NOT_AUTHORIZED` e inclui apenas uma impressão digital técnica de escopo/tentativa e um objeto congelado mínimo. Não revela telefone, destinatário, conteúdo, caso ou token. `reservation_committed_verified`, `s0_source_authenticated`, `credential_resolution_authorized`, `graph_dispatch_authorized`, `send_authorized`, `production_authorized`, `automatic_retry_authorized`, `ack_allowed` permanecem **sempre false**. `requires_independent_commit_readback=true` indica lacuna, NÃO cumprimento.

O recheck confronta todos os campos, revisões e hash de contexto; mudança na intenção, tentativa, template, conteúdo ou orçamento de taxa nega continuidade. **Duas leituras de fixture não impedem ABA ou mudanças após o último check**, nem criam posse de idempotência/lock.

## M18-B — Resultado Graph fictício, sem envio

A função `classifyWa18GraphMockOffline` somente recebe um objeto `observationMock` construído no laboratório, faz cópia de dados própria e segura de getters maliciosos e utiliza a classificação já existente `classifyGraphSendResult` da WA-02A. Não existe endpoint, `fetch`, `POST`, transport ou token no módulo M18.

| Observação injetada | Resultado LAB | Nunca inferir |
|---|---|---|
| HTTP 2xx com `wamid` sintático | `LAB_API_ACCEPTED_NOT_SENT` | `sent`, entrega, leitura ou efeito C09 |
| HTTP 2xx sem `wamid`, timeout, 429, 5xx | `LAB_EXTERNAL_UNCERTAIN` | Falha definitiva, reenviar automaticamente |
| 4xx definitivo segundo o classificador existente | `LAB_PROVIDER_REJECTED_UNVERIFIED` | Falha comercial, sequência WDC-13, desistência |
| Objeto malformado, getter hostil, campo extra, ciclo | `DENIED` | Fonte Meta autenticada, HTTP ACK ou retry |

O resultado da classificação tem `sent_verified=false`, `delivered_verified=false`, `read_verified=false`, `provider_status_verified=false`, `retry_external=false`, `graph_dispatch_authorized=false`, `commercial_transition_authorized=false` e `production_authorized=false`, para **todos** os casos.

## M18-C — Testes e evidência de segurança

`integrations/whatsapp-meta/wa18-dispatch-boundary-offline.test.ts` inclui **44 testes M18-01..44** para reserva candidata S0, leitura sem autorização, integridade cross-loja/App/WABA/phone/caso/intenção/tentativa, isolamento de finalidade e campanha, digest de conteúdo/destinatário, revisões estáveis, rate limit e observações stale/future, recheck em mutações, adulteração de flags e getters, interpretação de Graph fictícia (200, 400, 429, 503, timeout e resposta incompleta) e **nenhuma autorização/retry/efeito comercial**.

**Evidência funcional de testes Meta:** commit `18cdcf60aa81914bafa94dd1c7d0c1400087e78e`, [GitHub Actions 41312270140](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41312270140): **1.749/1.749 Meta offline**, incluindo 44 M18, scanner lexical ACK aprovado no job `s0-receipt-interop`. As 18 verificações físicas PG17 são históricas **exclusivamente do ingresso S0/Meta**, não provam reserva M18, Graph real ou status `sent`. Conferir separadamente o job `s0-physical-meta-consumer` e o CI do HEAD documental final.

## M18-D — Bloqueios e responsáveis antes do despacho real

- [ ] **S0/S1:** contrato ratificado de PRE_DISPATCH operacional e recurso de "reserva utilizável" depois de COMMIT durável confirmado, identidade do serviço e concessão de escopo, readback independente, CAS, prevenção de concorrência/revogação, idempotência por `attempt_ref`/`intent_ref`, estado de tentativa e **sem retry ao haver ambiguidade**. Uma reserva LAB S0 não pode ser "redeemed".
- [ ] **Infra/Proprietário:** fonte confiável App/WABA/número/ativos, autenticação M2M e custódia de tokens, política rate limit/retention, ambiente E2E permitido. Não abrir credencial nem Graph sem autorização separada.
- [ ] **Meta:** materialização do corpo real protegido sob autorização S0, cliente HTTP/Graph versionado, erros sanitarizados, tratamento de token expiry/429/5xx e backoff controlado pela S0, readback/correlação WAMID ↔ tentativa por canal e transporte separado de status. **Não criar esse transporte agora** porque esse escopo não foi autorizado.
- [ ] **S0/Meta/OpenAI:** projeção versionada WA-39 e callbacks autenticados, eventos ordenados, conflito/replay, status `sent` verdadeiro antes de qualquer efeito F02/C09/WDC-13; #9. Nenhum retorno `API_ACCEPTED` prova envio.
- [ ] **Aceite:** revisão interfrentes documentada, prova E2E isolada com autorização expressa, auditoria de concorrência/timeout/commit incerto e homologação; sem merge/deploy/produção até decisões de proprietário/Infra.

**Conclusão:** M18-A/B/C no **laboratório sintético e sem autoridade**; **M18-D e o marco principal [ ]**. Este incremento não envia mensagens, não autentica origem S0, não chama Graph e não modifica a S0, a OpenAI ou qualquer ambiente produtivo.
