# E04 A38 — Recuperação conservadora de estados S0/F02 após indisponibilidade

**28/10/2026.** Base A37: `24d39a7`/GitHub Actions #40722180768 SUCCESS (1.373/1.373). Este incremento pertence apenas à frente OpenAI F01/F02/F03. **Nenhum código ou contrato físico da S0 foi modificado.**

## Contrato existente preservado

O schema de resultado da S0 `prumo.s0.f02.review.result/0.1-candidate` permanece **candidato**, fixado em `docs/contracts/upstream/OAI_S0_F02_REVIEW_RESULT_SCHEMA_0_1_PINNED.json`. A A37 valida o formato por `inspect_s0_lookup_alignment_candidate`, incluindo identidade de revisão declarada, digest S0 distinto do digest F02 e flags operacionais sempre falsas. O schema não transporta fisicamente loja/caso/sessão; nada aqui autentica a S0.

## Implementação

`backend/f02_s0_recovery_sequence_candidate.py` agrega uma sequência limitada de **até 32 projeções declaradas** e o tipo `ClaimedContext`:

- `SAME_CONTEXT_UNVERIFIED`: apenas alegação de que a sessão/contexto não mudou; **não** comprova autenticação.
- `LOST_CONTEXT`, `CHANGED_SESSION`, `UNKNOWN_CONTEXT`: bloquear sem tentar refazer credenciais ou criar nova chave, retornando `AUTH_CONTEXT_RECHECK_REQUIRED`.

A sequência chama **o próprio validador A37** para cada estado. Diante de `UNAVAILABLE`, não transforma erro de transporte em rollback, criação de novo pedido ou limpeza do histórico. Preserva o último registro de revisão declarado para comparar uma projeção posterior, com `review_ref`, revisão, UTC, prazo e digest consistentes. Um resultado reaparecido é somente `REAPPEARED_SHAPE_RECHECK_ONLY`; ainda precisa de S0 autenticada. Mesmo uma repetição de bytes após a falha não demonstra que a indisponibilidade foi resolvida fisicamente.

Terminais `WITHDRAWN_REVIEW_ONLY` e `EXPIRED_REVIEW_ONLY` não podem ser reabertos. Outros estados negativos, inclusive `DENIED`, `STALE`, `CLOCK_RECHECK_REQUIRED` e conflitos de idempotência, mantêm a revisão bloqueada; não há retry automático. Sem histórico (ou com um `UNAVAILABLE` anterior à primeira prova declarada) não é possível afirmar que o registro foi perdido. O limite de 32 é **técnico de laboratório**, não política de retenção.

**Esta camada não prova que o histórico é completo.** O chamador pode omitir, falsificar ou inverter snapshots. `BASELINE_SHAPE_RECHECK_ONLY`, `CONTINUITY_SHAPE_RECHECK_ONLY` e `REAPPEARED_SHAPE_RECHECK_ONLY` são rótulos de sanidade estrutural **não autenticada**, nunca autorização de envio/agenda, reconciliação física, consentimento, ratificação do Gestor ou transferência válida de sessão. Nenhum token, servidor, fonte externa, storage, migração, rede ou runtime comercial é acessado.

## Testes e pendências

`backend/tests/test_f02_s0_recovery_sequence_candidate.py` contém **39 novos casos**, cobrindo recuperação com e sem baseline, `UNAVAILABLE`, múltiplos estados S0, replay exato sem ação, estados terminais e falsos retornos de terminal, perda/troca de sessão, campo de autorização malicioso, mudança de SHA, escopo, revisão, referência, hora e fuso, contratos inválidos e limite de snapshots. Runner PG17 integra a suíte junto às anteriores; F02-A38 somente certificado após CI SUCCESS.

A dependência de integração S0 é **concreta, mas continua aberta**: lookup durável e autenticado por CFI/GoTrue, contexto server-owned, gestão de sessões D3/D4 e comparação transacional com histórico e revogações. Não cabe à F02 criar um broker paralelo nem pedir à S0 auditoria genérica. G01–G07 continuam bloqueados; PR #1 permanece Draft, sem merge ou deploy.