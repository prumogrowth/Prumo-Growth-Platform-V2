# WA-52 — Bloqueio da outbox S0 e cancelamento concorrente

**25/10/2026. PostgreSQL 17 descartável `prumo_s0_test_ci`, branch experimental S0/Meta, PR #2 Draft. Nenhuma migração hospedada.**

## Mudança implantada no código de laboratório

`supabase/migrations/202610230051_s0_meta_outbox_lock_cancel_race_fixture.sql` adiciona um papel `prumo_s0_meta_wa52_outbox_guard_lab` sem LOGIN, superusuário nem BYPASSRLS. Somente esse papel possui o privilégio excepcional `UPDATE(id)` na tabela S0 de outbox, necessário para `SELECT ... FOR SHARE`. O papel de escrita forense NÃO recebe esse privilégio; o usuário de teste NÃO tem acesso direto ao guard, à tabela nem à troca de papel.

`meta_wa52_lock_outbox_fixture_s0(binding,intent,channel)` valida novamente a associação imutável entre vínculo e intenção, bloqueando a **linha real da outbox S0**. O bloqueio dura até `COMMIT` ou `ROLLBACK`; não libera envio nem aprova a operação.

`meta_wa52_locked_forensic_fixture_s0(...)` replica a rota experimental WA51, mas revalida `estado` pelo guard *após* a consulta preliminar e *antes* da assinatura e do arquivamento. Ordem: **outbox FOR SHARE → lock WA39 vínculo/evento → lock WA48 chave/HMAC/nonce → escrita S0**. Quando o cancelamento vence, o evento novo fica `LAB_LATE_UNVERIFIED`; quando o evento possui o lock primeiro, o cancelamento espera e o status é classificado usando o estado anterior. Nenhum retorno autoriza ACK, Graph, envio, retry ou alteração comercial.

## Provas programadas

`supabase/tests/s0_wa_056_assert_outbox_cancel_race_pg17.py` adiciona 28 provas incluindo: identidade e privilégios dos papéis, impossibilidade de escrita direta, vínculos sintéticos independentes, HMAC, replay, conflitos, negação cross-tenant, não consumo de nonce na falha de escopo e **dois processos PostgreSQL transacionais** controlados que demonstram ambas as ordens de cancelamento/status, com observação de espera por lock em `pg_stat_activity`. O CI completo preserva 347 testes anteriores; só certificar após `SUCCESS` no HEAD exato.

## Limites ainda abertos

O bloqueio utiliza `FOR SHARE` em cenário sintético da S0; não representa aprovação de mudança da S1 nem de um protocolo de cancelamento produtivo. O guard tem `UPDATE(id)` apenas por requisito de lock do PostgreSQL, o que merece nova auditoria de princípio do menor privilégio. Funções WA50 e WA51 continuam paralelas e **não foram substituídas**, e WA50 ainda tem ordenação de bloqueios distinta. Identidade IAM/M2M real, validade de webhook Meta original, trânsito entre S0/S1, mapeamento a rotinas reais de cancelamento, transições comerciais, integração HTTP, Graph, ACK e Supabase hospedado permanecem bloqueados. Nenhum merge.

**Próxima frente:** harmonizar ordem de locks das rotas históricas e ensaiar cancelamento simultâneo e eventos conflitantes em múltiplos vínculos, sem acionar a S1 real.
