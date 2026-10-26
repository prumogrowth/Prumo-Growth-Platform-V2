# F02 E04 — guarda de retomada de revisão entre históricos declarados V1

**Data:** 26/10/2026. **Escopo:** branch experimental `feat/oai-s0-f03-history-port-20261023`; PR #1 Draft; somente laboratório, sem incorporação ao S0 oficial.

## Problema funcional coberto

A pré-validação vinculada existente avalia `UntrustedTimeline` de maneira independente, sem comparar o conjunto de eventos de uma consulta anterior. Se um chamador reapresenta um histórico sem um registro de idempotência ou revogação **antes declarado**, uma nova avaliação isolada pode voltar a `READY_FOR_S0_RECHECK_ONLY`. Nenhum status é autorização real, porém a perda de continuidade deve ser apontada para revisão.

## Contrato implementado

Arquivo `backend/f02_reconciled_review_recovery.py` — `evaluate_review_recovery(previous, current)`. Ambas as entradas são `UntrustedRecoverySnapshot` (evidência, handoff, proposta, janela e timeline anteriores/atuais). Função pura sem banco, IO, S0, SQL, autenticação, transporte, agenda ou escrita de plano.

- Revalida cada snapshot pela `evaluate_bound_review_lifecycle`, com recomputação do SHA-256 **não assinado** da proposta/evidência.
- Snapshot anterior inválido/expirado/revogado/conflitante retorna `PRIOR_RECHECK_REQUIRED`; não pode ser reabilitado apenas oferecendo timeline nova.
- Mudança em evidence, handoff, proposta, escopo, template, chave ou janela retorna `REQUEST_DRIFT_REVIEW_REQUIRED`, inclusive quando novo hash foi corretamente recalculado.
- Relógio apresentado retrocede: `CLOCK_REGRESSION_REVIEW_REQUIRED`.
- Desaparecimento de algum registro ou revogação previamente **declarados**, inclusive multiplicidade de linhas, retorna `CLAIMED_HISTORY_ERASURE_REVIEW_REQUIRED`.
- Novo conflito, expiração ou revogação na timeline atual: `CURRENT_RECHECK_REQUIRED`.
- Continuidade sintética coerente: `RESUME_FOR_S0_RECHECK_ONLY` ou `RESUME_EXACT_REPLAY_S0_RECHECK_ONLY`. **Ambos exigem nova revisão independente S0** e não emitem tokens nem autorização.

## Limitações de confiança e coordenação

Ambos os snapshots são fornecidos pelo chamador. A guarda **não detecta** fato nunca apresentado, omissão simultânea nos dois snapshots, exclusão do snapshot antigo, relógio falsificado, manipulador malicioso com controle dos registros, consentimento revogado fora do lote, nem unicidade concorrente. Não é reconciliação real, ledger durável, assinatura/HMAC, lock, status remoto Meta ou aprovação humana. A janela de 48h segue experimental.

**Pontos reservados ao Codex/S0:** armazenamento imutável de histórico versionado com cursor e cutoff autenticados, monotonicidade de relógio de servidor, lock/serialização, detecção de paginação incompleta, consulta de revogação/opt-out autoritativos, ratificação S1 e rechecagem de segurança antes de agendamento/transportes. F01/F03 deve garantir ordem do handoff humano.

Testes isolados: `backend/tests/test_f02_reconciled_review_recovery.py` (21 unitários de estado, perda de evidência, conflitos, relógio e exclusão de autoridade), incluídos apenas em `scripts/run-s0-f03-pg17-local.sh`. Matriz: novo critério `F02-A20`, status laboratório. **Não** representa jornada operacional ou aceite para produção.

**Certificação:** condicionada ao GitHub Actions do commit da própria branch com SUCCESS. Nenhum merge, deploy, hosted Supabase, Meta ou cliente real foi acionado.
