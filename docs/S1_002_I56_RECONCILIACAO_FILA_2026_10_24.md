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
