# F02 E04 — ciclo de vida da solicitação pós-humana para revisão S0/Codex

**Checkpoint:** 2026-10-26. Branch experimental `feat/oai-s0-f03-history-port-20261023`; PR #1 Draft. **CÓDIGO certificado** `0963af1cb41c04e38547837a2c6074f8894da3cb` · [GitHub Actions #40297565619 — SUCCESS](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40297565619).

## Alterações isoladas da F02

- `backend/f02_reconciled_review_lifecycle.py`: pré-verificação **pura, in-memory**, com insumos tipados `ReviewWindow`, `UntrustedRecordedRequest`, `UntrustedRevocation`, `UntrustedTimeline` e `HandoffResult` do contrato anterior. **Nenhuma** importação S0, escrita em banco, rede, operação de envio, HMAC, autenticação, autorização operacional, cron, agendamento, integração ou evento persistido.
- `backend/tests/test_f02_reconciled_review_lifecycle.py`: **24 novos unitários** (expiração no limite, TTL excessiva, janela negativa, datas sem fuso, relógio anterior, replay idêntico, mudança de digest/chave/expiração, isolamento de escopo, duplicação de registros, revogação, revogação futura, entrada malformada e ausência de poder de execução).
- `scripts/run-s0-f03-pg17-local.sh`: adiciona somente a suíte Python deste módulo, preservando os testes físicos já existentes. Não mudou `.github/workflows`, bancos hospedados nem o núcleo S0.

## Estados do ciclo local, sem autoridade operacional

| Estado | Interpretação estrita |
|---|---|
| `READY_FOR_S0_RECHECK_ONLY` | Solicitação local formalmente coerente com histórico **alegado**, apta apenas para rechecagem independente pela S0 |
| `UNTRUSTED_EXACT_REPLAY_REVIEW_ONLY` | Mesmo hash, chave, escopo e janela temporal dos registros apresentados, ainda sem idempotência durável |
| `EXPIRED_REVIEW_REQUIRED` | `observed_at` é igual ou posterior à expiração alegada |
| `REVOKED_CLAIM_REVIEW_REQUIRED` | Há uma revogação declarada para aquela solicitação |
| `IDEMPOTENCY_CONFLICT_REVIEW_REQUIRED` | Mesmo fechamento com chave/hash/janela diferente ou múltiplos registros de histórico |
| `TIME_OR_HISTORY_INVALID` | Relógio, janela, registro ou revogação temporalmente inconsistente, ilegível ou fora do escopo |
| `RECONCILIATION_RECHECK_REQUIRED` / `DENIED_MALFORMED` | Handoff anterior ou insumos não permitem sequer preparar uma revisão |

**Janela máxima desta fixture: 48 horas.** É uma decisão de teste para a validade do *pedido de revisão*, independente da janela experimental de 24h–7d usada em minutas de horário de contato, e **não** é política comercial homologada.

## Limites e encargos do Codex/S0

- `UntrustedTimeline.observed_at`, os registros e as revogações são **fornecidos pelo chamador**; a F02 não prova que representam o relógio, os fatos completos ou os eventos reais. Uma ausência de revogação declarada nunca prova inexistência de revogação. Não há lock, ledger externo, assinatura, armazenamento ou garantia real de unicidade entre processos.
- `LifecycleResult` contém **somente um estado**, sem token, fila, booleano `approved` ou mandato. O estado positivo nunca substitui autenticação GoTrue/S1, autorização operacional assinada, prova de cancelamento externo Meta, opt-out, consentimento, template real ou revalidação de S0 no instante de envio.
- A S0 oficial, liderada pelo Codex, deverá definir eventos reais imutáveis com escopo e proveniência, transação e concorrência, expiração em relógio de servidor, revogação autorizada, política temporal homologada e ratificação humana independente; sem incorporar este módulo isolado sem coordenação.

## Resultado de CI e próximo gate

- **84/84 Python S0 + 561/561 Python F02/F03 = 645/645 Python; 269/269 Node S2 fixado.** Dos F02/F03, **330 testes físicos PG17** permanecem aprovados; nesta rodada foram adicionados **24 unitários** e **nenhum cenário PG17 novo**. São 914 verificações de suítes distintas, não 914 jornadas comerciais E2E e não homologação dos 70 oráculos E02 originais.
- **Próxima etapa da frente F02:** congelamento/redução de contratos redundantes após auditoria de dependências, matriz de aceitação funcional com critérios de pronto/não pronto, pacote de integração autorizado pelo Codex/S0. Sem implementação em hosted Supabase, sem Meta, sem clientes reais e sem merge para `main`.
