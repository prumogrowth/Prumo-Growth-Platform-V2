# Auditoria corretiva M18 — anteparo de despacho Graph API (offline)

**Data:** 01/11/2026. **Frente:** WhatsApp/Meta. **Escopo:** `wa18-dispatch-boundary-offline.ts`, seus testes, classificador WA-02A e contratos S0 #10 / WA-39 #9. **NÃO é operação Graph homologada**; os dados são fixtures locais não autenticadas.

## Parecer

A implementação M18 anteriormente publicada não envia mensagens e manteve todos os flags de produção falsos. A auditoria identificou lacunas de **consistência temporal** e **semântica de correlação** em respostas positivas do laboratório. Elas não habilitavam um envio real, mas poderiam fazer a prévia lab parecer mais comprovada do que era.

### AUD-M18-01 — horários e janela ausentes do digest de recheck (corrigido)

O cálculo anterior de `candidate_sha256` incluía escopo, revisões e rate budget, mas **não** `intent.now_ms`, `intent.max_age_ms`, `binding.observed_at_ms` ou `rate.observed_at_ms`. Assim, novas alegações de reserva/política ou quota com timestamps distintos dentro do limite de idade podiam obter o mesmo `candidate_sha256` e o mesmo resultado `LAB_RECHECKED_NOT_AUTHORIZED`. Não detectava substituição de uma observação sintética por outra com a mesma revisão/capacidade.

**Correção:** o hash agora vincula os quatro campos temporais e usa domínio versionado `WA18_DISPATCH_NO_AUTH_V0_2` (e escopo `WA18_SCOPE_LAB_V0_2`). O contrato de **saída** passou para `wa18-dispatch-preview.lab.v0.2`. A entrada `wa18-dispatch-intent.lab.v0.1` permanece, e candidato legado v0.1 é recusado com `PREVIOUS_CANDIDATE_INVALID`. Mudança de observação, limite de idade ou relógio nega o recheck (`REVISION_OR_CONTEXT_CHANGED`), ainda que os contadores e estados aparentem ser os mesmos.

**Limite:** hashes SHA-256 de dados injetados **não autenticam** origem, não substituem revisão monotônica real nem eliminam ABA/concorrrência. Também não garantem estabilidade **depois** do recheck nem reserva para envio externo.

### AUD-M18-02 — correlação da tentativa Graph mock marcada como válida sem fonte S0 (corrigido)

O `classifyWa18GraphMockOffline` anterior retornava `attempt_correlation_valid:true` para observações sintéticas bem formadas e `transport_error`, embora **nenhuma** prova S0 de tentativa persistida, vínculo por App/WABA/phone/`wamid`, autenticação de origem ou readback fosse consumida nessa função. O rótulo era potencialmente enganoso, mesmo com `sent_verified=false`.

**Correção:** `attempt_correlation_valid:false` passa a ser invariante **em todos os resultados da função mock**, inclusive `LAB_API_ACCEPTED_NOT_SENT`, `LAB_PROVIDER_REJECTED_UNVERIFIED` e `LAB_EXTERNAL_UNCERTAIN`. Permanecem `provider_status_verified=false`, `sent_verified=false`, `retry_external=false` e todos os flags de Graph/produção/efeitos comerciais falsos. Nenhum evento de callback foi incorporado.

### AUD-M18-03 — observação contraditória transporte/HTTP (corrigido)

Antes, um mock com `kind:'transport_error'` e, simultaneamente, `http_status`/`response_json` era aceito como timeout sintético; as duas formas, embora contraditórias, tinham o mesmo caminho de entrada. A correção separa estritamente objetos `transport_error` (somente `kind`) e `http_response` (`kind,http_status,response_json` obrigatórios). Mistura ou forma parcial retorna `DENIED`.

### AUD-M18-04 — sucesso LAB S0 com motivo contraditório (corrigido)

O parser anterior aceitava `decision:'LAB_RESERVATION_RECORDED_NO_DISPATCH'` com qualquer `reason` tipado, por exemplo `POLICY_DENIED`, desde que as flags fossem falsas. A análise agora exige `reason:null` no suposto sucesso LAB. Respostas `DENIED/UNAVAILABLE` seguem negativas e **nunca** promovem permissão Graph.

## Evidências

- Base anterior: **44 testes M18**, **1.749 testes Meta offline**, [CI 41312483230](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41312483230) íntegro e dois jobs `success`.
- Após auditoria: **18 regressões AUD-M18-45..62**, total **62 testes M18** e **1.767/1.767 Meta offline**, no SHA de código/testes `0676f536182687fea6b35198142c39013baea23f`. [CI funcional 41322471887](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41322471887): **dois jobs `success`**, 0 fail: Meta offline + PG17 histórico independente, scanner ACK lexical aprovado.
- As **18/18 verificações PG17 físicas históricas** aprovadas pertencem exclusivamente à prova de ingresso S0/Meta, **não** ao novo anteparo M18 nem à integração Graph. A execução documental final é verificada separadamente.
- Os testes novos exercitam deriva de relógio/idade e timestamps da reserva e orçamento, S0 positivo incoerente, `attempt_correlation_valid:false` sob 200, 400 e timeout, shapes contraditórios de mocks, versão de saída antiga e negativas de grant/campos extra.

## Segurança mantida e bloqueios

- `LAB_DISPATCH_COHERENT_NOT_AUTHORIZED` e `LAB_RECHECKED_NOT_AUTHORIZED` são **diagnósticos de coerência**, não contratos de autorização real. `send_authorized=false`, `graph_dispatch_authorized=false`, `automatic_retry_authorized=false`, `reservation_committed_verified=false`, `s0_source_authenticated=false`, `credential_resolution_authorized=false`, `ack_allowed=false` em qualquer candidato.
- **S0 #10:** o PRE_DISPATCH PG17 corrente `prumo.s0.pre-dispatch.pg17/0.1-lab-only` é interno ao banco descartável e retorna antes do commit do chamador; mesmo após commit não fornece lease operacional Graph. Reserva e readback independentes, fonte autenticada, janela de envio, opt-out, CAS/serialização, idempotência/outbox e recuperação incerta requerem desenho/aceite S0/Infra.
- **Infra/#8:** inventário e concessão real App/WABA/número, credencial/vault, limitação de taxa operacional, prova da aprovação Meta de template e fonte de consentimento. O mock de quota **não reserva** slots nem impede corrida real.
- **WA-39/#9:** a classificação de HTTP 2xx com `wamid` é apenas API aceita; somente callback autenticado mais reconciliação por tentativa/loja/canal pela S0 pode sustentar status `sent`; 429/timeout/5xx e commit externo incerto não autorizam reenvio automático, efeito WDC-13/C09 ou inferência de desistência.
- **Auditoria não homologa Graph nem vínculo F02.** Não houve Graph, chamada HTTP, envio comercial, dados reais, credencial, SQL produtivo, merge ou deploy.

**Checklist:** M18-A/B/C [x] exclusivamente LAB e agora auditadas. **M18-D e M18 principal [ ]** até ratificação e prova E2E física expressamente autorizada entre S0/S1, Meta e Infra.
