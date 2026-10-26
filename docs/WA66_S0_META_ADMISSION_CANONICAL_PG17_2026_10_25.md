# WA66 — Limites de admissão sob transação PG17 e variantes brutas

**25/10/2026, S0/Meta offline. Exclusivamente PostgreSQL 17 descartável e localhost Node.**

## Escopo verificável

O listener WA57 aplica limites de **4 solicitações admitidas simultâneas**, **262.144 bytes por corpo**, header `Content-Length` obrigatório e estrutura raw WA46 estrita. Em WA66 esses limites são exercitados junto ao writer forense WA55, com duas intenções S0 sintéticas novas, sem reutilizar outboxes históricas.

A nova suíte `supabase/tests/s0_wa_071_admission_canonical_pg17.test.mjs` implementa **24 provas físicas**.

### Corrida A: capacidade reservada, cancelamento, COMMIT

Um processo Node `wa66-a` segura uma transação `holdcommit` real depois do append; a ausência de visibilidade do nonce e da observação é provada em conexão PG17 separada. Três clientes TCP mantêm corpos incompletos e ocupam os demais slots do listener. Duas solicitações excedentes (uma com evento válido, uma sintaticamente inválida) recebem `503 LAB_HTTP_BUSY` **antes da ponte**: zero nonces e zero observações extras. O cancelamento administrativo da outbox aguarda o PID PG17 do append, verificado por `pg_stat_activity.wait_event_type='Lock'` e `pg_blocking_pids`. Após liberar sockets e confirmar o append, a evidência fica única e o cancelamento conclui. Um novo processo com a mesma chave arquiva outro evento tardio; uma alteração apenas na ordem das propriedades de status cria **o mesmo event_ref**, mas novo hash bruto, recebendo `LAB_BODY_VARIANT_QUARANTINED`; retransmissão da variante retorna replay exato.

### Matriz B: canonização e limites de bytes

Um segundo vínculo `wa66-b` usa chave própria, preservada entre vários eventos no mesmo worker. Provas: corpo original; variante de ordem das propriedades; replay exato; JSON original seguido de whitespace até atingir **exatamente 262.144 bytes**, admitido como variante de hash, sem canonização de bytes; corpo com **262.145 bytes** recusado pelo cabeçalho antes de gastar nonce; objeto raiz com propriedade inesperada, status `DELIVERED` inválido, array de dois status e assinatura HMAC incorreta, todos negados sem recibos nem nonce. Após cancelamento, status distinto por timestamp é registrado como `LAB_LATE_UNVERIFIED`, e replay do corpo original preserva o registro.

## Contratos preservados

- Identidade do evento: `SHA256([waba,phone,wamid,recipient,status,timestamp])`, distinta do `SHA256(raw bytes)`. Não é feita canonização que apague variações forenses; nem toda variante de bytes representa novo evento.
- Nenhuma autorização comercial ou autenticação real; ACK externo inexistente, shadow receipts zerados, chamadas legado WA52 sem EXECUTE.
- Apenas worker de teste com dois perfis `wa66-a/b`, suíte PG17, runner e workflow de CI, além deste documento. **Nenhuma migration, produção, S1, main ou merge**.
- Última certificação WA39–65: 751/751; **candidato WA66 +24**, total **775/775** somente se GitHub Actions aprovar no SHA exato.

**Próxima candidata WA67:** reforçar/medir diferenciais de corpo ambíguo (chaves JSON duplicadas, encoding e Unicode) e sua admissão segura, distinguindo observação do contrato atual e mudança de política.
