# WA-62 — Corrida entre revogação e append forense (PostgreSQL 17)

**25/10/2026 · S0/Meta isolada, PostgreSQL 17 descartável, Node HTTP em 127.0.0.1.**

## Testes físicos

`supabase/tests/s0_wa_067_key_revoke_race_pg17.test.mjs` contém **20 verificações** organizadas em três sequências independentes. A ordenação de transações é provada mediante `pg_stat_activity.wait_event_type='Lock'` e `pg_blocking_pids()`, com PIDs reais do banco; não depende apenas de intervalos artificiais.

1. **Revogação precede append** — revogador PostgreSQL detém o advisory lock `wa48-key` e altera `active` numa transação aberta. Node/HTTP concorrente espera no bloqueio comprovado; quando a revogação confirma o COMMIT, a escrita WA55 é recusada, sem nonce nem forense. Novo PID com chave revogada continua recusado.
2. **Append precede revogação** — o cliente sintético da WA55 mantém aberta uma transação após a chamada SQL e antes do COMMIT. O revogador externo aguarda efetivamente o lock pertencente ao processo PostgreSQL do append. Nenhum nonce/registro é visível antes do COMMIT; após ele, a única observação fica preservada, HTTP devolve confirmação **somente de laboratório** e o revogador conclui. Retransmissão posterior com a chave revogada é recusada e não apaga a observação.
3. **ROLLBACK precede revogação** — uma segunda transação de append detém o lock, o revogador aguarda, e então ocorre ROLLBACK do append. Nenhuma observação/nonce é persistida nem é emitido HTTP 202; o revogador pode confirmar a revogação.

A barreira controlável `holdcommit/holdrollback` foi acrescentada **somente ao worker descartável WA60**, preservando seu default e os modos históricos. Sua sinalização `wa62-held` não concede autoridade, nem expõe segredos. O workflow exclusivo S0 exigirá 20 marcadores novos exatos; total candidato: **679** (659 anteriores + 20).

## Limites

Não há webhook público, Meta Graph, ACK real, envio, IAM/M2M verdadeiro, deploy Supabase hospedado, autorização comercial, integração S1/main ou merge. O PR segue Draft. A mudança da S0 é apenas test harness local; IAM real e persistência além do PG17 não foram provados.

**Certificação somente após CI SUCCESS no SHA exato.** Nenhuma ação necessária da S1.

**WA63 candidata:** concorrência tripla cancelamento de outbox × revogação × append com locks e resultado forense tardio.
