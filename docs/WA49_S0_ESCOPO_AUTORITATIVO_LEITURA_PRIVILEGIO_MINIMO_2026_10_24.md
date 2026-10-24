# WA-49 — Escopo S0 autoritativo de leitura + recibo sombra (PG17)

**24/10/2026. Exclusivamente repositório oficial, branch da frente Meta/S0, PR #2 Draft.**

## Avanço efetivo

A migration de laboratório `202610230048_s0_meta_scoped_non_superuser_fixture.sql` adiciona à função PG17 de proprietário limitado uma **consulta com JOIN dos vínculos S0/041-042 de verdade** (`meta_vinculos_tentativa_fixture_s0`, `meta_apps_fixture_s0`, `meta_canais_fixture_s0` e `outbox_intencoes_s0`). Exige correspondência exata de App técnico, WABA, phone, concessionária via JOIN, canal, intenção, tentativa, correlação, destinatário e `wamid`. Sem o vínculo, não executa assinatura, nonce nem recibo.

A execução autorizada continua chamando a prova HMAC/nonce da WA48 no **mesmo contexto transacional**, com papel NOLOGIN/NOSUPERUSER, função `SECURITY DEFINER`, grants de **SELECT de colunas** e políticas RLS apenas para o proprietário limitado. Não concede UPDATE/DELETE/INSERT nos quatro objetos autoritativos ao executor, nem SELECT/INSERT ao cliente. O registro vai **somente ao ledger-sombra da WA48**, não ao ledger forense S0/043. O lock `wa39:<binding>:<event>` é compartilhado com o arquivador S0/043; não bloqueia mudança de estado da outbox, portanto não é snapshot de autorização de negócio.

## Provas

`supabase/tests/s0_wa_053_assert_authoritative_scope_pg17.py` executa **34 verificações PG17** sobre login real de fixture, propriedade de função, negação de acesso direto, não-superusuário, correspondência/cross-shop, versão, nonce, replay, MAC adulterado, concorrência, rollback e revogação, inclusive mantendo invariantes sobre o ledger forense original. O workflow valida marcadores individuais e toda a regressão WA39–48.

## O que não está resolvido

**Não é a remoção de `postgres` do caminho WA40/S0/043.** O novo papel lê os registros de mapeamento S0 de laboratório sob política RLS ampla `using(true)` para executor NOLOGIN; a restrição de tenant ocorre na função por combinação exata. Não há escrita autoritativa, nem consulta de revisão do vínculo versionada, nem lock de cancelamento da S1. Também não há identidade M2M/IAM validada, assinatura Meta real, credencial Meta, Graph, ACK, Supabase hospedado ou autorização comercial. Não alterar S1 para cumprir teste.

Próxima etapa: projetar com a S0 mudança segura do dono do arquivo forense real, evitando conceder UPDATE nos objetos autoritativos apenas para `SELECT FOR SHARE`, e validar ordem de locks S0↔S1 antes de qualquer integração.
