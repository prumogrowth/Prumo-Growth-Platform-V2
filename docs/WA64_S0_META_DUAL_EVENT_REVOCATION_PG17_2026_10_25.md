# WA64 — Dois eventos independentes da mesma intenção: cancelamento e revogação

**25/10/2026 · Exclusivamente S0/Meta em PostgreSQL 17 descartável e loopback Node.**

## Hipótese e método

Cada uma de três intenções sintéticas S0 novas (WA64-A/B/C) recebe **um único vínculo técnico imutável**. Dois eventos de status `delivered` com **timestamps distintos**, identificadores de evento (WA46) distintos e chaves de laboratório distintas competem sobre o mesmo vínculo e a mesma outbox. As intenções anteriores da WA61–63 não são reabertas nem modificadas.

A suíte `supabase/tests/s0_wa_069_dual_event_revocation_pg17.test.mjs` implementa 24 verificações de laboratório:

- **A — dois COMMITs, cancelamento e duas revogações:** dois processos Node/HTTP independentes mantêm transações WA55 abertas, cada qual com sua chave/nonce. Uma sessão de cancelamento da outbox e duas revogações aguardam locks reais. O primeiro COMMIT preserva um evento e libera uma revogação, mas **não libera o cancelamento**, pois o segundo append segue aberto. Após o segundo COMMIT, a outbox cancela, a segunda chave é revogada, e ambos os eventos permanecem registrados individualmente, sem duplicação. Retransmissão com chave revogada é negada.
- **B — ROLLBACK seletivo, COMMIT e cancelamento:** dois eventos distintos concorrem sobre a mesma intenção, cada um com chave própria. O ROLLBACK de um deles não grava nem consome nonce; não impede que o outro COMMIT seja persistido. Revogações e cancelamento aguardam os respectivos locks até o fim das transações. Uma **terceira chave**, após o cancelamento, permite replay exato do evento persistido e uma observação tardia nova para o evento originalmente revertido.
- **C — cancelamento primeiro e revogação seletiva:** a transação de cancelamento retém o lock da outbox, enquanto dois PIDs HTTP tentam registrar eventos diferentes. Revoga-se somente a chave de um deles. Após COMMIT do cancelamento, a chave revogada falha sem gastar nonce; a chave ainda válida arquiva **uma única observação `LAB_LATE_UNVERIFIED`**. Após outra revogação, novas tentativas com as chaves antigas falham. A chave rotacionada permite replay exato e uma observação tardia separada.

A ordem transacional é verificada por `pg_stat_activity` (`wait_event_type='Lock'`) e `pg_blocking_pids`, sem usar pausas temporais como prova. A auditoria final confirma seis registros novos, hashes/IDs originais preservados, dois eventos por intenção, isolamento dos nonces, nenhuma gravação em shadow receipts, ACL antiga fechada e flags comerciais negativas.

## Escopo e certificação

Alterados apenas o worker de laboratório para três perfis WA64, a nova suíte, o runner S0 e o workflow S0. **Não foram alteradas funções de produção, permissões, regras S1, main ou migrations.** Sem Graph API, Meta ACK/webhook público/envio, IAM real, banco Supabase hospedado ou merge.

WA39–63: **703/703** provas certificadas; candidato WA64: **+24** verificações, total previsto **727/727**, dependente de **CI SUCCESS no SHA exato**. A implementação não será considerada certificada antes desse resultado.

**Próxima candidata WA65:** cruzamento de replays e variantes de corpo/status sob duas chaves e cancelamento, preservando classificação de conflitos por evento e nonce.
