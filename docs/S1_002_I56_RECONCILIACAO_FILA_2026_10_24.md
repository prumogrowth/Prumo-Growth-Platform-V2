# S0 + S1-002 / I56 — reconciliação canônica da fila (24/10/2026)

## Implementação

- Migration incremental 202610190055_s0_fila_reconciliacao_casos.sql (S0, sem mock).
- Todo INSERT de casos_humanos usa o mesmo lock por lead que I54; segundo caso do mesmo ciclo recebe 23505.
- Gatilho diferido no caso reconcilia a(s) pendência(s) ainda sem titular, com estado reconciliado, caso_id real, incremento de versão e evento RECONCILIADO. Casos legítimos gerados pela fila I54 chegam ao commit já atribuidos; não devem ser reconciliados.
- O gatilho de sinal comercial I54 também adquire lock por lead ANTES de verificar existência de casos, para não reintroduzir fila obsoleta.
- Backfill transacional de filas antigas com caso existente, sem atribuição artificial.
- Nenhuma permissão direta nova ao usuário autenticado. Nenhuma função externa, Meta, banco ou deploy envolvidos.

## Evidência e testes

- s1_080_fila_reconciliacao_aceite.sql: seis verificações de estado, versão, evento, claim I54 e privilégio PostgreSQL em transação descartável.
- test_s1_002_i56_reconciliacao_race.sh: dois cenários em sessões PostgreSQL independentes, com bloqueio observado e ambos os possíveis vencedores.
- Regressões I54 e I55 precisam permanecer verdes. **Não classificar I56 como aprovado até consultar os logs GitHub Actions das novas execuções.**
- Código de infraestrutura local e esquema da S0; não constitui homologação produtiva, operação real ou merge.

## Próximo gap

Verificação de todos os caminhos de criação de caso, permissões em voo, integração UI da fila e fluxo de primeiro contato humano/delivery. A2 continua obrigatória sem suspensão global de conta.

## Prova assinada complementar

A suíte GoTrue local I55 foi estendida com S1QUEUE-165, exigindo que a criação de caso externo reconciliada pelo I56 seja excluída da consulta assinada, retorne 409 ao tentar assunção CAS com versão antiga e mantenha um caso e um evento de reconciliação. O estado da execução será registrado somente após inspeção de logs reais.

## Evidências reais — 24/10/2026

**PG17 canônico I56: APROVADO em banco descartável**, em [GitHub Actions #40089537969](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40089537969), commit de implementação [fe767034](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/commit/fe767034a7545d5e3de70a06f8d238480a032374), job s1-002-equipe id 120859214026: SUCCESS. Logs conferidos: PASS I56-01..06 (6/6); PASS I56-RACE-01..02 (2/2) em duas sessões PostgreSQL e espera Lock observada. Regrediram também PASS I54-01..08 (8/8) e PASS I54-RACE-01..02 (2/2), incluindo concessão revogada durante lock.

**Gateway assinado I55+I56: APROVADO em GoTrue/HMAC descartáveis**, em [GitHub Actions #40089738334](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40089738334), código [640ba119](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/commit/640ba119f3a37c60d50e70bb336a932a0a4ae919). Jobs http-policy-unit 120859829766 e e2e-gerencia-local 120859829884: ambos SUCCESS. Logs conferidos: TestQueueV55 11/11, PASS S1QUEUE-157..165 9/9, regressão S1CANON-149..156 8/8 e isolamento do SQL privado; S1QUEUE-165 confirma reconciliação externa, exclusão da listagem assinada, HTTP 409 no claim obsoleto e um único caso.

Os outros workflows de regressão disparados por fe767034 concluíram 15 SUCCESS; o workflow I37 dessa revisão foi CANCELLED pela execução posterior de 640ba119 (que concluiu SUCCESS), **não é falha funcional**. A evidência relevante I37 final é #40089738334.

**Status de homologação:** testes unitários e integração local descartável aprovados. Não homologado para produção, sem deploy, merge, dados reais, WhatsApp, Meta ou Banco. Frontend, observabilidade e escala operacional permanecem pendentes.
