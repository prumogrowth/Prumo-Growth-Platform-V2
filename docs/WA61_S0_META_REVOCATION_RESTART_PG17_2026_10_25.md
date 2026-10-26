# WA-61 — Reconciliação forense após reinício: revogação, vínculo e cancelamento (PG17)

**25/10/2026 — Laboratório isolado PostgreSQL 17 e Node no loopback `127.0.0.1`, exclusivamente S0/Meta.**

## Escopo e provas

A WA61 acrescenta 24 provas em `supabase/tests/s0_wa_066_forensic_revocation_restart_pg17.test.mjs`, executadas após WA60 no mesmo banco descartável:

1. Evento forense original persistido, seguido de encerramento e retransmissão em novo PID com a **mesma chave** (replay sem duplicação).
2. Revogação administrativa da chave sintética pelo contrato WA48. Em um **terceiro processo**, a mesma chave revogada não pode arquivar nem repetir um evento anterior; a recusa não gasta nonce, não acrescenta forense e preserva a observação original.
3. Rotação para chave sintética nova: retransmissão permitida resulta apenas em `LAB_EXACT_BODY_REPLAY`; evento distinto produz uma única observação original.
4. O vínculo técnico S0 é imutável, não um registro livremente reassociável: UPDATE direto sofre bloqueio; novo processo com fotografia sintética divergente (`attempt_ref` incorreto) recebe 403 e não consome nonce nem grava ledger.
5. A desativação da rota injetada para um processo posterior provoca negação antes da persistência.
6. Cancelamento real do estado **sintético** da outbox S0: replay de evento anterior não duplica observação, enquanto evento distinto posterior vira `LAB_LATE_UNVERIFIED` (observação tardia sem concessão comercial). Reinício subsequente com chave nova mantém a idempotência.
7. Todas as observações antigas conservam identificador/hash/tipo; shadow receipts continuam ausentes, flags comerciais permanecem falsas e rota WA52 direta continua inacessível para o cliente sintético.

As diferenças de vínculo e de rota injetadas pelo worker simulam **fotografias divergentes entre PIDs**; não representam mutação real do vínculo, pois o banco a proíbe. O cancelamento, a revogação e o ledger são efetivamente persistidos em PG17.

## Integração e limites

`s0_wa_064_pg17_restart_worker.mjs` recebeu o parâmetro de fixture `WA61_BINDING_PROFILE` (padrão `current`; negativos `stale-attempt` e `disabled-route`). WA60 não mudou seu padrão. O runner e o workflow **exclusivos da S0** incluem e contam 24 marcadores novos, preservando todos os anteriores.

Não há webhook Meta público, Graph, Meta ACK, envio WhatsApp, IAM/M2M produtivo, Supabase hospedado, autorização comercial, mudanças S1, merge ou modificação da `main`. Revogação após COMMIT não apaga evidência prévia. A conclusão exige **CI SUCCESS no SHA exato** e 659/659 marcadores únicos (base 635 + 24); antes disso, registrar somente implementação pendente de certificação.

**Dependência da S1:** nenhuma. **Próxima candidata:** WA62, testes de corrida entre revogação e append transacional em processos distintos, preservando ordem dos locks e evidência histórica.
