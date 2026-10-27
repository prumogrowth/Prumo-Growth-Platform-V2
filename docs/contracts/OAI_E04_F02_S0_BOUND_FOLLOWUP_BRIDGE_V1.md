# F02 E04 — ponte vinculada de leitura de retorno S0 candidata V1

**Emissão:** 27/10/2026, apenas experimento F02, branch `feat/oai-s0-f03-history-port-20261023`, PR #1 Draft. S0 é proprietária do núcleo oficial.

## Lacuna fechada

O classificador `classify_s0_review_followup` interpreta corretamente os 13 estados do resultado S0 0.1-candidate e valida o hash com um `HandoffResult` fornecido ao chamador. Porém **não recebia as próprias `ClaimedS0Evidence` e `ReviewOnlyProposal`** para recomputar esse digest: uma cópia antiga ou declaração forjada de handoff podia gerar um status de análise coerente com uma proposta diferente. Mesmo sem privilégio comercial, é uma divergência relevante para a solicitação de revisão.

## Nova interface experimental

`classify_bound_s0_review_followup(evidence, proposal, handoff, window, projection, previous=None)`, implementada em `backend/f02_s0_review_followup_candidate.py`:

1. valida tipos exatos dos insumos;
2. executa `prepare_handoff(evidence, proposal)` com os campos da proposta atual, incluindo escopo, horário, template, política e quatro hashes alegados;
3. só continua com `HANDOFF_REVIEW_ONLY`, `contract_version` coincidente e SHA-256 recomputado idêntico, conferido por `compare_digest`;
4. delega ao validador e classificador existentes para conferir o schema S0, revogação/expiração de pedido técnico representadas, mudança de `review_ref`, versão, relógio e estados negativos;
5. devolve exclusivamente `FollowupResult(status)`; divergência → `BLOCK_AND_RECHECK_CONTRACT_ONLY`, sem fila, comando, operador, credencial, identificador, token ou capacidade operacional.

O contrato S0 `prumo.s0.f02.review.result/0.1-candidate` continua não ratificado. A execução real de `record/read/withdraw` exige CFI/GoTrue/SQL e pertence à S0, **não** à ponte F02. Os próprios dados de evidência e `projection` permanecem não autenticados no chamador; até que S0 disponibilize canal verificado, o resultado comprova somente consistência sintética. É impossível elevar esse status a aprovação, consulta viva ou autorização Meta.

**Políticas distintas:** a S0 admite prazo **voluntário e imutável** do pedido de revisão, sem aprovação de teto máximo; o TTL de 48h do módulo F02 `evaluate_bound_review_lifecycle` é uma experiência separada. Esta ponte **não importa os 48h**, nem transforma 24h–7d de proposta de contato em norma S0. Unicidade de revisão S0 permanece por `loja+ator+chave`, não por encerramento.

## Evidência e coordenação

`backend/tests/test_f02_s0_review_bound_bridge_candidate.py`: 25 novos unitários independentes cobrindo integridade de proposta, escopo, domínio Meta, falsa ratificação, fonte, replay, expiração, discrepância do hash, intervalo voluntário acima de 48h, UTC, terminal e `UNAVAILABLE`. Matriz `F02-A23`, runner experimental somente. O commit requer CI `SUCCESS` no próprio SHA; testes físicos PG17 existentes são uma suíte separada e **não** tornam esse contrato uma integração S0 real.

**Restante reservado Codex/S0:** autenticação de origem e sessão, ratificação oficial do schema/transporte/lookup, escopo de supervisor S1, validação da cadeia F03/C04/C08, fonte de opt-out, template, cancelamento externo Meta, concorrência comercial, agendamento e operação real. Nenhuma autorização, merge, main, deploy, production migration ou serviço real foi usado.
