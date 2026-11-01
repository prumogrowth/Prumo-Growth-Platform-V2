# M19 — Reconciliação de ocorrências de status WhatsApp (somente LAB offline)

**Data:** 01/11/2026. **Frente:** WhatsApp/Meta. **Estado:** modelo técnico M19-A/B/C em laboratório; **M19-D e marco principal abertos**. Nenhuma operação real Graph, webhook/HTTP ACK, banco S0, token, credencial ou aplicação comercial.

## Marco e fronteiras que já existem

A M19 oficial exige **status e evidências reais reconciliados** por `wamid`, tentativa e concessionária, incluindo callbacks duplicados/fora de ordem, incerteza, `sent`, `delivered`, `read` e `failed`, sem inferência comercial. A origem formal é a [Issue #9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9) e o [contrato candidato WA-39](WA39_CONTRATO_CANDIDATO_EVIDENCIA_OUTBOUND_F02_S0_v0_1.md), ainda sem ratificação.

**Não duplicar bases existentes:** `routed-webhook.ts` valida HMAC do POST original conforme App/rota confiadas; `wa32-signed-status-s0-forensic-bridge.ts` ensaia vínculo exato com porta S0 falsa, sem transação; WA-35 emite ticket sintético para recheck S0; `wa38-callback-ambiguity-classifier.ts` impõe quarentena; `technical-reconciliation.ts` é um reconciliador de memória sem ingestão persistente nem ACK. A M19 proposta começa **depois dessas fronteiras**, com alegações de ocorrência e de vínculo S0 estritamente sintéticas.

## M19-A — Reconciliação sem inferência de autoridade

`integrations/whatsapp-meta/wa19-status-reconciliation-offline.ts` fornece apenas as funções puras:

- `reconcileWa19StatusOffline(scopeLab,bindingLab,occurrencesLab)`
- `recheckWa19StatusOffline(previousSnapshot,scopeLab,bindingLab,occurrencesLab)`

Entradas estritas:
- `wa19-status-request.lab.v0.1`: seleção, concessionária, App, WABA, emissor, canal, caso, intento, tentativa, `wamid`, digest do destinatário e janela de observação;
- `wa19-s0-binding-claim.lab.v0.1`: **alegação** S0 de vínculo exatamente correspondente, `binding_revision`, `LAB_CLAIMED` ou `LAB_INVALIDATED` e timestamp recente. Não é API S0 autenticada, reserva, commit nem readback durável;
- `wa19-status-occurrence.lab.v0.1`: uma ocorrência técnica individual com escopo App/WABA/número/concessionária/`wamid`, digest do corpo físico alegado, identificador de ocorrência **fornecido pela fixture**, posição, tipo (`sent`/`delivered`/`read`/`failed`), UTC, erro Meta opcional e as flags **`hmac_verified=false`, `s0_source_authenticated=false`, `durably_persisted=false`**.

O laboratório verifica tipos exatos, protótipos e descriptors de dados, impede getters, arrays esparsos, campos extras e lotes de mais de 100 ocorrências. O lote é **atômico na validação local**: um item incoerente nega todo o ensaio, sem aceitar subconjunto.

**Deduplicação LAB:** o mesmo `occurrence_ref` com os mesmos campos é contado uma vez, com `duplicate_count` separado. Se um mesmo identificador aparecer com conteúdo/status/timestamp/posição diferentes, o resultado é `LAB_CONFLICT_QUARANTINED`. A chave é uma **alegação da fixture**; não representa identificador de evento único emitido e autenticado pela Meta. Eventos diferentes de mesmo status são preservados, não fundidos apenas por `wamid`/timestamp.

**Ordenação:** as ocorrências são ordenadas canonicamente pelo identificador para compor um `snapshot_sha256` de escopo, versão de vínculo, relógio e eventos. Isso torna a comparação independente da ordem da lista e **não altera** a cronologia bruta. `read` ou `delivered` podem existir na fixture antes de `sent`; não se cria `sent` retroativamente. `sent` observado também **não é `sent_verified`**. `failed` concomitante a qualquer `sent`/`delivered`/`read` é conflito/quarentena, sem classificar definitividade.

**Revogação:** `LAB_INVALIDATED` com ocorrências retorna `LAB_INVALIDATED_OBSERVATION_HOLD`. Sem timestamp de revogação **não** se afirma que houve callback realmente tardio, apenas que o vínculo alegado está invalidado. `failed` e o erro 131049 são diagnósticos, não falha consecutiva na cadência WDC-13.

O resultado `wa19-status-snapshot.lab.v0.1` é um **agregado mínimo**: status técnico `LAB_*_UNVERIFIED`, quantidade de eventos únicos/duplicados, quais tipos foram observados, digest, flag de quarentena e `requires_s0_recheck:true`. Não retorna IDs, nomes, telefone, conteúdo, `wamid`, erro privado, segredos ou mensagens originais. Os estados de retorno positivo `LAB_STATUS_RECONCILED_UNVERIFIED` e `LAB_RECHECKED_UNVERIFIED` são **diagnósticos sintéticos**, não decisões S0.

**Invariantes em todas as saídas:** `s0_source_authenticated=false`, `callback_hmac_verified=false`, `attempt_correlation_verified=false`, `durable_persistence_verified=false`, `sent_verified=false`, `delivered_verified=false`, `read_verified=false`, `definitive_failure_verified=false`, `definitive_failure_count_increment=false`, `case_transition_authorized=false`, `commercial_transition_authorized=false`, `retry_external=false`, `ack_allowed=false`, `production_authorized=false`. **Não existe evidência para WDC-13, C09 ou F02**.

## M19-B — Testes adversariais e isolamento

`integrations/whatsapp-meta/wa19-status-reconciliation-offline.test.ts` acrescenta **57 cenários M19-01..57**: progressão não inferida, leitura/entrega sem sent, ordenação, ocorrência duplicada exata, colisão divergente, mesmo status em eventos diferentes, conflito sent↔failed, alegação invalidada, tempo inválido/futuro, erro 131049, escopo de loja/WABA/emissor/caso/attempt/intent/destinatário, snapshots stale/future, getters, array esparso, falsificação de HMAC/persistência, recheck e alterações de vínculo.

**Evidência CI:** anexar SHA funcional e execução dos dois jobs após validação; os 57 casos elevam a base de 1.767 para **1.824 testes Meta offline**. As 18 verificações PG17 são históricas **apenas do ingresso S0↔Meta** e não devem ser somadas à suíte M19 nem usadas como prova de callback/status real.

## M19-C — Dependências para WA-39/F02

- **Meta/Infra:** obter POST original pelo gateway autorizado, validar HMAC real com App Secret selecionado, rota/concessionária/WABA/phone, evento físico/posição/digest; persistência durável segura **antes** de ACK, segundo #2. Um `occurrence_ref` fabricado não permite deduplicação real e digest idêntico não substitui identidade de lote físico.
- **S0/S1:** vínculo efetivo e durável de `wamid`↔tentativa↔intent↔loja/canal/recipient, revisão monotônica, leitura consistente/lock, registros de eventos imutáveis, tombstones, rechecks pós-commit, divergência/replay/quarentena e readback atestado; não reescrever status com observações antigas. #8/#10 continuam dependências de fonte, autorização e identidade.
- **WA-39/#9:** S0 define `PENDING_CORRELATION`, `CORRELATED_SENT`, `CORRELATED_DELIVERED`, `CORRELATED_READ`, `CORRELATED_DEFINITIVE_FAILURE`, `UNCERTAIN`, `CONFLICT` e `QUARANTINED` sob fonte autenticada e política ratificada. A Meta **não** concede esses rótulos autoritativos a partir de um LAB.
- **WDC-13/C09:** apenas **S0** ordena tentativas consecutivas de uma cadência, contabiliza duas falhas definitivas correlacionadas, zera sequência por `sent` comprovado e determina janela de 24 h do **template final**. `API_ACCEPTED`, ACK, entrega, leitura e timeout não autorizam retroinferir `sent` nem efeitos comerciais.
- **OpenAI/F02:** receber somente a projeção mínima **ratificada e produzida pela S0**, nunca a lista bruta de callbacks, hashes de corpo ou mensagens privadas.

## M19-D — Não concluído

- [ ] Homologar contrato S0/Meta/Infra do callback, verificação HMAC e identidade do evento/ocorrência/posição física.
- [ ] Validar commit atômico e durável, dedupe/replay/cursor, ordenação, retorno perdido, ACK autorizado, recheck S0 com transação real e evidências efetivamente correlacionadas.
- [ ] Testar casos E2E reais isolados com autorização do proprietário, preservando ausência de efeito comercial automático pela Meta e isolamento tenant.
- [ ] Obter ratificação S0/S1/OpenAI da projeção WA-39 para a F02 e sem confundir M19 com M20.

**Estado:** M19-A/B/C são entregas sintéticas **somente offline**; M19-D e o marco principal continuam `[ ]`. Sem merge, deploy, Graph, webhook real, banco produtivo, tokens ou mensagens enviadas.
