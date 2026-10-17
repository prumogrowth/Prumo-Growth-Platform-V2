# Aceite S0 — não confundir código com teste PASS

| Cenário | Situação |
|---|---|
| Mesmo telefone sintético gera leads A/B independentes | NOT_RUN |
| FK composta impede ligação entre lojas | NOT_RUN |
| Estado `ganho` é rejeitado | NOT_RUN |
| Gestor A/B só lê registros da própria loja | NOT_RUN |
| Operador sem caso não obtém leitura geral | NOT_RUN |
| Usuário sem vínculo ou anon não lê dados de loja | NOT_RUN |
| authenticated não altera status diretamente | NOT_RUN |
| Importações e inbound idempotentes | A IMPLEMENTAR |
| D2 gestor, autoatribuição, D3/D4 do S1 | A IMPLEMENTAR |

Execução requer PostgreSQL real isolado, aplicação ordenada de migrações e registro do ambiente/commit/resultado. Scripts presentes não comprovam PASS.
