# F02 E04 — preflight vinculada de solicitação de revisão V1

**Checkpoint:** 26/10/2026; branch experimental `feat/oai-s0-f03-history-port-20261023`; PR #1 Draft; sujeito à revisão Codex/S0. **Status: REVIEW ONLY, NO AUTHORITY**.

## Lacuna fechada no laboratório

A API original `evaluate_review_lifecycle(handoff, proposal, window, timeline)` aceitava um SHA-256 de formato válido sem recalcular se correspondia à **proposta** submetida naquele momento. Assim, o status `READY_FOR_S0_RECHECK_ONLY` poderia aparecer para uma proposta trocada após o handoff. Isso **não** permitia enviar, mas tornava imprecisa a alegação de coerência formal.

A nova entrada **preferencial para integração experimental** é `evaluate_bound_review_lifecycle(evidence, handoff, proposal, window, timeline)` em `backend/f02_reconciled_review_lifecycle.py`. Ela:
1. verifica os tipos estritos e versão `F02_S0_RECONCILED_HUMAN_HANDOFF_V1`;
2. recalcula o handoff **com a mesma evidência e proposta atuais** via `prepare_handoff`;
3. compara os SHA-256 determinísticos usando `compare_digest`; rejeita mudança de loja/lead/caso/fechamento, canal, template, versão de política, instante, chave e testemunhas sintéticas;
4. conserva as verificações anteriores de janela, replay, conflito e revogação do ciclo legado;
5. devolve **somente** `LifecycleResult.status` (`RECONCILIATION_RECHECK_REQUIRED` na divergência), sem criar token, permissão, agendamento, plano ou envio.

A API anterior continua disponível por compatibilidade para os testes/contratos já existentes, mas passa a rejeitar uma versão incorreta de `HandoffResult.contract_version`. **Não deve ser escolhida como única preflight de propostas futuras**; a recomputação depende da evidência original.

## Prova de regressão e limites

`backend/tests/test_f02_bound_review_preflight.py` adiciona **17 unitários** para o vínculo, troca de payload e SHA, versionamento, UTC, opt-in fictício, ratificação falsa, replay, expiração, revogação e inexistência de poder de execução. O teste da matriz de aceitação aponta para este contrato. Incluído **somente** no runner experimental `scripts/run-s0-f03-pg17-local.sh`.

Toda `ClaimedS0Evidence` continua **não autenticada**. Recalcular SHA-256 apenas comprova consistência *dentro de insumos controlados pelo chamador*: quem controlar evidência e proposta pode criar outro hash. **Não é HMAC, assinatura, prova S0, selo imutável, validade legal, opt-out real ou autorização humana**. `UntrustedTimeline` ainda é relato do chamador; faltam fonte imutável, transação, concorrência, relógio confiável, verificação Meta e revogação autoritativa.

**Dependências Codex/S0:** ratificar materialização de recibos F03, autenticação/sessão GoTrue, S1 gestor e escopo, cadeia C04/C08, estado remoto Meta, elegibilidade no instante da decisão, idempotência durável e eventual API S0 de revisão humana assinada. Nenhuma alteração no núcleo S0 oficial, na main, em workflows de outras frentes, no hosted Supabase ou APIs reais. **Sem merge/deploy.**

**Certificação:** este arquivo descreve código candidato. O commit só está certificado quando o CI da branch concluir com SUCCESS.
