# WA-51 — Paridade do conflito forense com HMAC/nonce e bloqueio ordenado

**25/10/2026 · PostgreSQL 17 descartável, PR #2 Draft, sem deploy.**

## Incremento

A WA50 escreve na tabela forense original S0, mas reutilizava WA48, que combina verificação HMAC/nonce com uma regra de recebimento do ledger-sombra: status divergente para mesmo evento/body resultava em rejeição antecipada, impedindo que WA39 registrasse a divergência.

A migration de laboratório S0/050 cria **verificador HMAC/nonce-only** sob `prumo_s0_meta_wa48_executor_lab` (NOLOGIN/NOSUPERUSER), com chave sintética, validade temporal, advisory lock compartilhado com a rotina de revogação WA48, assinatura HMAC SHA-256 sobre material S0/044 e nonce único. O verificador **não consulta o ledger-sombra**. O cliente de teste não recebe EXECUTE nessa função; apenas o escritor interno `prumo_s0_meta_wa50_writer_lab` a chama.

O arquivador paralelo `meta_wa51_parity_forensic_fixture_s0` utiliza vínculo exato da S0, bloqueia evento pela mesma chave WA39, só então valida HMAC/consome nonce, e arquiva observação, replay, variante de corpo ou divergência de tipo nos ledgers S0/043 originais — sempre na mesma transação. Em caso de exceção posterior, o nonce reverte. A **ordem de locks** evento → chave coincide com WA49; WA48 e WA50 históricas permanecem inalteradas.

## Verificação

`supabase/tests/s0_wa_055_assert_forensic_parity_pg17.py` inclui **36 marcadores** cobrindo assinatura adulterada, escopo cruzado, replay, variantes, conflito registrado, rollback, concorrência do nonce, revogação, ACL e imutabilidade dos contratos legados. A regressão WA39–50 continua no mesmo runner. Certificar somente após CI no HEAD exato.

## Limites

Não há origem HTTP Meta autenticada, IAM/M2M real, autorização de envio, ACK, Graph, Supabase hospedado nem escrita em estados comerciais. Não foi resolvida a **leitura concorrente da outbox sem FOR SHARE**; tampouco a ordem de bloqueios da rota experimental antiga WA50 (que continua como fixture separado). A alteração do proprietário do trigger de vínculo introduzida pela WA50 ainda precisa de auditoria formal fora do laboratório. S1 e `main` seguem intactas.

Próximo passo: ensaios concorrentes com atualização/cancelamento de outbox, prova de lock order e desenho de credenciais operacionais antes de cogitar substituição do caminho `postgres`.