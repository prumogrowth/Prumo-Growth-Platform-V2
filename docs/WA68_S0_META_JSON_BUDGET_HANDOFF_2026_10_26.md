# WA68 — Orçamento de complexidade JSON e admissão concorrente no laboratório

**26/10/2026 — frente Meta S0 experimental isolada. Responsável pelo núcleo S0 oficial: Codex.**

## Objetivo e encerramento limitado

A WA68 confirma operacionalmente os limites introduzidos no parser estrito experimental da WA67 e os combina com o limite HTTP WA57, o append forense WA55 em PostgreSQL 17 e o cancelamento da outbox original. **Não representa entrega de integração WhatsApp de produção.**

## 24 provas

**Orçamento sintático determinístico** no módulo `s0_wa_072_strict_json_keys.mjs`: 2.048 nomes aceitos, 2.049 recusados; 4.096 nós totais aceitos, 4.097 recusados; 48 níveis de aninhamento aceitos, 49 recusados; corpos de 262.144 bytes permitidos, 262.145 recusados. Nomes Unicode NFC/NFD semanticamente distintos não são normalizados implicitamente; dois nomes que decodificam para o mesmo valor Unicode são considerados duplicados. Surrogate órfão, BOM e UTF-8 inválido seguem negados. Valores grandes mas sintaticamente válidos continuam válidos se dentro de todo orçamento. **Não há SLA absoluto de CPU/latência alegado**: a prova cobre os limites de trabalho e os efeitos de admissão, não benchmark entre dispositivos.

**Cenário integrado físico:** nova intenção S0 sintética `f7400000-0000-4000-8000-000000000074` com único vínculo WA68-A e chave shadow nova. Processo Node de loopback segura `holdcommit` enquanto três sockets TCP mantêm uploads incompletos, saturando os quatro slots existentes. Solicitações válidas e complexas excedentes devem retornar `503 LAB_HTTP_BUSY`, sem escrever nonce/forense. Cancelamento administrativo aguarda fisicamente o bloqueio `FOR SHARE` da outbox, comprovado com `pg_stat_activity` + `pg_blocking_pids`. Após liberação e COMMIT, persistência única do primeiro evento; depois, entradas caras/ambíguas são negadas antes do append, variantes de corpo com 262.144 bytes preservam hashes distintos, e quatro status com timestamps diferentes submetidos em paralelo geram quatro eventos próprios e `LAB_LATE_UNVERIFIED` depois de cancelamento. Revogação final bloqueia replay, preservando o histórico. Zero flags comerciais, zero shadow receipts e privilégio legado WA52 fechado.

## Arquivos e dependências para revisão Codex/S0

Alterações **somente na branch experimental**:
- `supabase/tests/s0_wa_064_pg17_restart_worker.mjs` — perfil explicitamente restrito `wa68-a`; não altera contrato real.
- `supabase/tests/s0_wa_074_guard_budget_pg17.test.mjs` — 24 testes em PG17 descartável + Node localhost.
- `scripts/run-s0-local.sh` e `.github/workflows/wa39-s0-meta-offline.yml` — execução e verificação dos 24 marcadores WA68.
- Este documento.

**Dependências:** módulos experimentais WA46/56/57/67, PostgreSQL 17 descartável, `prumo_private` S0 fixture com outbox/vínculo/chave shadow, Node/HTTP `127.0.0.1`; nenhuma alteração de migração ou de segurança S0 oficial.

**Para o Codex decidir:** manter/ajustar limites sintáticos e orçamentos de CPU, tratar entradas recusadas no serviço real, comparar diferenças na autenticação/ACL do núcleo S0 e decidir se a política WA67/68 deve ser integrada. Necessário comparar os PRs paralelos e executar testes no SHA exato na integração; **nenhum merge, cherry-pick, main, S1, Graph, webhook Meta real, IAM real, Supabase hospedado ou autorização comercial**.

**Marco anterior:** WA39–67 = 799/799 no commit `29da5b6d87ba01439253446c9cd1a6633e31c2d0`. **WA68 +24**: total candidato **823/823**, condicionado a CI **SUCCESS** no novo SHA.

**Proposta de fechamento:** após WA68, realizar auditoria final de escopo e matriz de integração/pendências no lugar de criar etapas indefinidas; qualquer nova WA exige lacuna concreta identificada.
