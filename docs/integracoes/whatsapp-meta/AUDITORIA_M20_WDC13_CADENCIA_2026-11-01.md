# Auditoria corretiva M20 — WDC-13 e sequência de falhas (LAB offline)

**Data:** 01/11/2026. **Frente:** Meta/WhatsApp. **Escopo:** `integrations/whatsapp-meta/wa20-wdc13-cadence-preflight-offline.ts`, sua suíte de testes e as regras da [WA-39 candidata](WA39_CONTRATO_CANDIDATO_EVIDENCIA_OUTBOUND_F02_S0_v0_1.md). **Nenhum contador comercial, transação S0, efeito WDC-13, janela C09, Graph ou callback real.** Este módulo não pode consumir prova M19 como evidência autorizada.

## Regra preservada e limite de autoridade

A WA-39 define **duas falhas definitivas, correlacionadas e consecutivas em tentativas distintas da mesma cadência** como condição para que **somente S0** avalie o efeito WDC-13. Um `sent` verdadeiro da tentativa posterior zera a sequência, sem exigir resposta de cliente. `API_ACCEPTED`, HTTP ACK, timeout, erro `131049`, `UNKNOWN/PENDING/CONFLICT`, `delivered` ou `read` não comprovam por si status `sent` ou falha definitiva. C09 tem outra regra e janela: somente `sent` do **template final** comprovado por S0 pode subsidiar seu cálculo, não esta simulação.

O laboratório recebe `LAB_DEFINITIVE_FAILURE_CLAIM` e `LAB_SENT_CLAIM` como **alegações não autenticadas**. Um diagnóstico `LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED` jamais gera `wdc13_increment_authorized:true`, `wdc13_transition_authorized:true`, `case_transition_authorized:true`, envio, C09, replanejamento F02 ou retry. A interface S0 real e a política de evidência tardia permanecem sob a [Issue #9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9).

## Achados e correções

**AUD-M20-01 — referência de evento reutilizável em tentativas distintas (corrigido).** A primeira implementação exigia `attempt_ref`, `intent_ref` e índice de tentativa distintos, mas aceitava o **mesmo** `event_ref` em dois itens da sequência. Um dado injetado poderia, portanto, montar um falso cenário de duas falhas a partir de uma única referência de ocorrência. A auditoria acrescentou `seenEvents`, recusando qualquer `event_ref` repetido, mesmo quando o corpo ou o status alegado mudam. Os digests iguais em referências distintas continuam permitidos porque o SHA-256 não é prova de identidade da ocorrência; a regra é somente uma barreira de coerência no LAB, não dedupe durável S0.

**AUD-M20-02 — observações posteriores ao snapshot S0 alegado (corrigido).** O validador anterior exigia que `attempt.observed_at_ms` não fosse futuro para `context.now_ms` e estivesse dentro da idade máxima, mas aceitava observação **posterior** a `context.observed_at_ms`, apesar de o contexto declarar uma revisão de evidência. A correção exige `attempt.observed_at_ms <= context.observed_at_ms` para todos os itens; igualdade ou idade anterior são aceitas dentro da janela. O recheck também falha com `ATTEMPT_SCOPE_DENIED` quando o novo item aparece como posterior ao próprio snapshot, sem inventar revisão S0.

**AUD-M20-03 — contador de resets registrava qualquer alegação de envio (corrigido).** O laboratório incrementava `claimed_sent_reset_count` até em um `LAB_SENT_CLAIM` isolado ou em dois `sent` consecutivos sem falha pendente. A contagem agora é incrementada **somente** quando um `sent` alegado efetivamente zera `consecutive > 0` ou resolve um `hold` anterior. O reset provisório continua incapaz de autenticar envio real. Dois ciclos independentes falha→sent produzem dois resets diagnósticos; sent inicial antes das duas falhas não adiciona reset e mantém o limiar subsequente puramente hipotético.

**AUD-M20-04 — versão de snapshot alterada por mudança de semântica (corrigido).** O retorno passa de `wa20-wdc13-snapshot.lab.v0.1` para **`wa20-wdc13-snapshot.lab.v0.2`**, com domínio `WA20_WDC13_LAB_V0_2`. O recheck nega snapshots antigos e detecta alteração de referência de evento. **Entradas** `wa20-cadence-claim.lab.v0.1` e `wa20-attempt-claim.lab.v0.1` permanecem LAB, com verificação adicional de coerência, sem declaração de API interoperável.

## Testes e prova funcional

- **60 testes M20-01..60** da implementação inicial preservados: duas falhas, reset por `sent`, incerteza, timeout/ACK não contabilizados, `131049` não autoritativo, sequência sem saltos, escopo por concessionária/App/WABA/phone/caso/plano/cadência, tempo, getters, status alegado e ausência de privilégios.
- **20 testes AUD-M20-61..80** adicionais: reutilização de `event_ref` em duas falhas ou falha+sent/unknown+sent, divergência de digest com mesma referência, ausência de prova em hashes coincidentes, observação posterior ao snapshot, causalidade na rechecagem, reset sem sequência anterior, múltiplos resets verdadeiramente condicionados, snapshot `v0.2` e rejeição de `v0.1`.
- **CI funcional:** commit `d314d7bd1f1c87b366544c1eb6afc88c3080ecb3`, [Actions 41351099767](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41351099767): **80/80 M20 e 1.982/1.982 Meta offline**, job de regressões `success`, scanner estático ACK aprovado. Os **18 PG17 históricos de ingresso S0/Meta** são verificados separadamente no segundo job e não provam WDC-13 nem fonte de evidência. O CI do HEAD documental final requer conferência própria.

## Riscos remanescentes e decisão

1. **O input inteiro é injetado e não autenticado**, inclusive `event_ref`, `status_claim`, revisões e os relógios; SHA-256 é checksum local sem chave, **não** assinatura, vínculo `wamid` ou integridade de ledger S0. O módulo nem sequer recebe a trilha de ocorrências físicas de M19 como fonte autenticada.
2. **S0/S1** deve ratificar vínculo único de `attempt_ref` e `intent_ref` à cadência e a eventos duráveis `sent/failed` verificados, classificação definitiva por tentativa, numeração/ordem estáveis e regras de retrocorreção após sent, cancelamento, pausa, revogação, concorrência, reprocessamento e outbox. O LAB não pode incrementar WDC-13.
3. **Infra/Meta** devem entregar ingresso HMAC/recibo real e correlação S0 de App/WABA/phone, `wamid` e ocorrência física com readback/cursor; a [Issue #9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9) permanece a demanda interfrentes. O PG17 histórico é outro fluxo.
4. **F02/OpenAI** só pode ler projeções ratificadas e minimizadas **após** S0, nunca instrução para perda, interrupção ou replanejamento derivada da simulação. **C09** é distinta e não pode ser iniciada por `is_final_template:true` sem `sent` real e elegibilidade S0.
5. **M20-D** precisa integração ratificada, prova física e teste de concorrência/replay/late evidence. A entrega offline não supre os bloqueios de M18-D/M19-D.

**Parecer:** **M20-A/B/C concluídas e auditadas somente em LAB**. **M20-D e marco M20 principal permanecem [ ]**. Nenhum Graph, envio, SQL/HTTP ACK produtivo, credencial, merge, deploy ou efeito comercial.
