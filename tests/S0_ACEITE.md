# Prumo — evidências de aceite S0 parcial

**Testes efetivamente executados em 17/10/2026** no GitHub Actions, PostgreSQL 17 em contêiner descartável e dados sintéticos. Commit verificado: `2e5fec57b454127b062f09411156505f49c1af2e`.

[Execução e logs (PASS)](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39059980947)

| Cenário | Resultado |
|---|---|
| Migrações criam 5 tabelas e 5 policies | PASS (CI) |
| Mesmo telefone: leads independentes em A/B | PASS (CI) |
| FK composta rejeita ligação de loja cruzada | PASS (CI) |
| Estado `ganho` é rejeitado | PASS (CI) |
| Gestor A/B só consulta dados da própria loja | PASS (CI) |
| Operador sem caso não recebe leitura geral | PASS (CI) |
| Usuário sem vínculo/anon não lê dados de loja | PASS (CI) |
| authenticated não altera status diretamente | PASS (CI) |
| Reimportação e histórico idempotentes | A IMPLEMENTAR |
| Inbound duplicado | A IMPLEMENTAR |
| Gestor D2, autoatribuição, OP atribuído, D3/D4 | A IMPLEMENTAR NA S1 |
| Políticas de retenção e recuperação | NÃO VALIDADO |

**Não confundir PASS parcial de CI com conclusão de S0 ou liberação comercial.** Não houve migração no Supabase remoto nem aprovação Meta, Banco ou LGPD. Há cenários AP41, importações, eventos e revisões humanas ainda pendentes.
