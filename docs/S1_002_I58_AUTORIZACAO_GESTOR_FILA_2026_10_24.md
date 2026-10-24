# S0/S1-002 I58 — autorização de Gestor em consultas e CAS

**24/10/2026 · Somente laboratório descartável.** Branch feat/s1-002-equipe-prumo.

A auditoria identificou que a operação I54 `s0_fila_assumir` retornava CONFLICT para fila já consumida **antes** de verificar a concessão do Gestor. Um Gestor cujo escopo fosse revogado podia continuar distinguindo o estado CAS de um ciclo da concessionária via gateway assinado. A consulta assinada I55 utilizava predicado com timestamp dentro do primeiro SELECT com lock, sem rechecagem explícita depois de uma espera longa.

**Correção**: migration incremental `202610190057_s0_fila_gestor_revalidacao.sql` introduz helper privado `s0_fila_exigir_gestor_i58`. Ele trava, nessa ordem, equipe do Gestor, loja e concessão com `FOR SHARE` sem filtro temporal, para depois executar uma nova leitura de elegibilidade em `clock_timestamp()`. Rejeita Gestor inativo, loja inativa, falta de concessão ou expiração. O comando S0 I54 preserva ordem lead→fila→autorizações, mas chama o helper **antes** de retornar CONFLICT/ALREADY_HAS_CASE. A projeção assinada I55 (fixture GoTrue local `s1_079`) usa o mesmo helper antes de consultar o conteúdo da fila.

**Teste**: `s1_082_fila_gestor_autorizacao_aceite.sql` exercita concessão positiva, replay autorizado, revogação de escopo antes do CAS, multi-loja, suspensão do Gestor e ACL. `test_s1_002_i58_fila_gestor_race.sh` comprova duas esperas reais PostgreSQL: grant revogado enquanto CLAIM aguarda; grant naturalmente expirado enquanto o helper de LIST aguarda. E2E GoTrue/HMAC `S1QUEUE-166..167` comprova que CAS de fila já consumida retorna 403 com grant revogado, depois 409 com grant restabelecido, e que LIST nega escopo naturalmente expirado.

**Restrições**: o helper é SECURITY INVOKER privado, executor `postgres` apenas, sem RPC ou grant do cliente. Não altera casos históricos, A2, estados comerciais ou acesso direto a mensagens. Os resultados dependem da verificação independente de sessão/assinatura no gateway I55. Não homologa produção nem todos os comandos e superfícies D2/D3/D4; não resolve o estado de fila inexistente anterior à leitura do lead em I54 e não substitui política RLS de histórico.

**Evidências de CI**: somente acrescentar após jobs concluídos e logs inspecionados.

## Evidências verificadas — 24/10/2026

- **PG17 SUCESSO**: [workflow #40132128199](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40132128199), job `s1-002-equipe` `120985884703`, commit `881218e21d309787110437ad3ebd75dab07ddff0`. Logs conferidos: `PASS I58-01..06` (6/6), `PASS I58-RACE-01..02` (2/2), ambos os waits confirmados em `pg_stat_activity`; regressões I57/anteriores preservadas. Runner: `PASS S0+S1 I52-I58 canonical stages after legacy regression`.
- **GoTrue/HMAC E2E SUCESSO**: [workflow #40132414081](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40132414081), commit `8bce4866248409ac709ae8145f4c6037a51451e7`, jobs `e2e-gerencia-local` `120986749725` e `http-policy-unit` `120986749496` ambos SUCCESS. Logs conferidos: `S1QUEUE-157..167` **11/11**, I53 `S1CANON-149..156` **8/8**; nonce HMAC, GoTrue e gateway em contêineres descartáveis.
- **Falha e reparo documentados**: [workflow #40132128031](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40132128031) apresentou erro de sintaxe no teste SQL `pg_catalog.position` (os testes S1QUEUE-157..165 passaram). Corrigido para `pg_catalog.strpos` em `8bce486`; **não** se alterou a migration I58, o helper ou o código de autorização. A execução #40132414081 é o aceite final.

**Estado:** I58 implementado e aprovado no laboratório descartável; sem deploy, sem merge, sem alteração na `main`, sem dados de clientes ou ação externa Meta/Banco. As próximas frentes são RLS de histórico e leitura D2/D3/D4, outras operações privilegiadas e interface operacional.
