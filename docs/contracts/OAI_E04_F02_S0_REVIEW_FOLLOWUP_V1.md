# F02 E04 — continuação segura após a projeção S0 (0.1-candidate)

**Data:** 26/10/2026. Branch experimental `feat/oai-s0-f03-history-port-20261023`, PR #1 Draft. Fonte S0 sob coordenação Codex: `exp/s0-f02-revisao-autoritativa-20261026`, HEAD `88af4aea3aeb2c403bab4c078fdc04d560f2cba0`, CI de código `40414847271` SUCCESS.

## Nova funcionalidade efetiva

`backend/f02_s0_review_followup_candidate.py` fornece `classify_s0_review_followup(projection, handoff, window, previous=None)`. Ela reusa **sem substituir** o validador de contratos `inspect_s0_review_projection`. Emite apenas um `FollowupResult(status)`, com orientação *não executável*, sem ID, token, chave, função de rede, persistência, aprovação, agenda ou envio.

Os 13 estados da S0 são mapeados de modo exaustivo:
- `RECORDED_REVIEW_ONLY`, `REPLAY_REVIEW_ONLY`, `CURRENT_REVIEW_ONLY` → `AWAIT_S0_EVIDENCE_RECHECK_ONLY`. São registros de pedidos, não autorização.
- `WITHDRAWN_REVIEW_ONLY`, `EXPIRED_REVIEW_ONLY` → `STOP_TECHNICAL_REVIEW_REQUEST_ONLY`. **Interrompe a análise do pedido técnico, não afirma cancelamento Meta nem do atendimento.**
- `INPUT_REJECTED` → `OFFLINE_INPUT_CORRECTION_ONLY`; não repete operação inválida.
- `DENIED`, `STALE` → `REFRESH_AUTHENTICATED_S0_CONTEXT_ONLY`; não forja sessão/ator nem reaproveita recibo obsoleto.
- `IDEMPOTENCY_CONFLICT` → `MANUAL_S0_IDEMPOTENCY_REVIEW_ONLY`; não inventa chave alternativa.
- `REQUEST_EXPIRED` → `EXPIRED_REQUEST_NO_AUTO_RENEWAL_ONLY`; não estende janela.
- `REVIEW_REQUEST_NOT_FOUND`, `UNAVAILABLE` → `S0_READ_ORIGINAL_REQUEST_ONLY`; consulta futura *sob autoridade S0*, sem reenvio automático. Não implica que leitura realmente tenha sido realizada.
- `CLOCK_RECHECK_REQUIRED` → `S0_CLOCK_RECHECK_ONLY`; não usa relógio do cliente como prova.

Envelope inválido, hash/expiração incompatíveis, alteração de `review_ref`, regressão de revisão ou horário, retorno negativo após estado persistido, ou tentativa de reabrir `WITHDRAWN`/`EXPIRED` → `BLOCK_AND_RECHECK_CONTRACT_ONLY`. **Nada executa ação automaticamente.**

## Segurança e escopo

A API classifica apenas cópias locais **não autenticadas** do resultado candidato; não valida o canal nem a identidade de serviço S0. A S0 é a única fonte autorizada a reler documento/chave e confirmar estado durável. Não foi incorporado `S0F02ReviewRegistryLocal`, feita operação no PostgreSQL/GoTrue ou desenvolvida uma UI real. O estado `PENDING_EVIDENCE` **não é** ratificação humana, consentimento ou cancelamento externo.

Preserva as diferenças intencionais dos contratos: única chave técnica S0 por `loja + ator + chave`, não unicidade comercial por encerramento; janela S0 voluntária distinta dos 48h experimentais da lifecycle F02 e dos 24h–7d sintéticos do contato; C04/C08 local não comprova Meta. F01/F03, S1 gerente, C04/C08/Meta e Frontend continuam gates de integração.

`backend/tests/test_f02_s0_review_followup_candidate.py` acrescenta 26 testes isolados, cobrindo todos os 13 códigos S0, conflitos de continuidade, envelope forjado, exclusão de execução e compatibilidade com o manifesto pinado. `scripts/run-s0-f03-pg17-local.sh` os inclui no runner experimental; a matriz de aceitação passa a cobrir `F02-A22`. Esta entrega só é certificada quando o GitHub Actions do próprio commit retornar SUCCESS.

**Nenhum merge, deploy, envio Meta, hosted Supabase, migration de produção ou alteração da S0 oficial.**
