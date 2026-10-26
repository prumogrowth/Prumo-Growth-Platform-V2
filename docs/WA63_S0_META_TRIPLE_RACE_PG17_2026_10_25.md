# WA63 — Concorrência tripla: cancelamento da outbox × revogação × append forense

**25/10/2026 — S0/Meta offline, PostgreSQL 17 descartável, Node loopback.**

## Objetivo e desenho da prova

Três tentativas de teste novas, vinculadas à estrutura S0 real no mesmo canal técnico sintético, usam outboxes independentes inicialmente `BLOQUEADA_GATES` (perfis de worker `wa63-a/b/c`). O processo não reabre a intenção cancelada na WA61. O teste `supabase/tests/s0_wa_068_triple_race_pg17.test.mjs` possui **24 provas** que consultam o PostgreSQL real para identificar `wait_event_type='Lock'` e `pg_blocking_pids`, sem decidir ordem de concorrência por `sleep`.

### Ordem A: cancelamento → revogação → append

O administrador mantém transação de cancelamento aberta e não confirmada; um processo Node distinto inicia o append e fica fisicamente bloqueado pelo lock da outbox; enquanto aguarda, outra sessão revoga e confirma a chave. Após COMMIT do cancelamento, a escrita não pode persistir status ou consumir nonce. Um novo processo com a chave revogada permanece negado.

### Ordem B: append → cancelamento e revogação

WA55 mantém o append transacional aberto através do modo `holdcommit` do worker WA62. Cancelamento aguarda o lock `FOR SHARE` da outbox e revogação aguarda o lock advisory da chave, ambos comprovadamente bloqueados pelo mesmo PID PostgreSQL. O recibo HTTP 202 é retido até o COMMIT. Após o COMMIT, uma única observação histórica permanece, cancelamento e revogação se confirmam e retransmissões com a chave revogada falham sem duplicação.

### Ordem C: revogação → append → cancelamento

Revogação mantém lock e atualização não confirmada; append inicia, obtém lock da outbox e aguarda a chave; cancelamento aguarda o lock da outbox do append. A cadeia de bloqueadores é verificada antes do COMMIT da revogação. O append falha sem nonce nem forense e libera o cancelamento. O processo seguinte também não pode arquivar usando a chave revogada.

A suíte exige imutabilidade dos vínculos sintéticos, conservação do ledger anterior, zero shadow receipts, ausência de novos privilégios SQL, todas as flags comerciais falsas e ausência de ACK/envio Meta. Nenhum evento de teste constitui evidência de entrega real.

## Alterações e contagem

Adições **somente na branch S0**: teste WA63; três perfis imutáveis no worker de laboratório; runner `scripts/run-s0-local.sh` e marcadores WA63 no workflow `.github/workflows/wa39-s0-meta-offline.yml`. Sem migrations nem modificação em S1. A base certificada WA39–62 possui 679 provas; WA63 acrescenta 24; total candidato **703/703**, exclusivamente após GitHub Actions SUCCESS no SHA exato.

**Limites:** sem servidor público, ACK real à Meta, Graph API, IAM/M2M verdadeiro, Supabase hospedado, envio, transições comerciais, merges ou alterações na main. Nenhuma dependência S1.

**Próxima candidata WA64:** concorrência cruzada envolvendo dois eventos distintos da mesma intenção e arbitragem forense após cancelamento e revogação, com isolamento de nonces.
