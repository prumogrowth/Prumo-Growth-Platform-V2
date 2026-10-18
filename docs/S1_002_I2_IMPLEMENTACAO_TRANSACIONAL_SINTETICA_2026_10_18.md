# S1-002/I2 — Implementação de redistribuição no sandbox | 18/10/2026

**Escopo:** protótipo SQL 039 da frente S1-002, sem API pública, frontend, OpenAI, Meta, Banco ou infraestrutura hospedada. Complementa [contrato I2](S1_002_I2_CONTRATO_REMANEJAMENTO_AUTOMATICO_CF_OP_02_v0_1.md), PR #5, PR #7 e issue #6.

**Mecanismo:** team state ativo→suspenso/desligado e última concessão operacional por loja revogada acionam remanejamento na mesma transação: guard nas novas atribuições, encerramento da atribuição antiga, nova atribuição exclusivamente a operador Prumo ativo com concessão válida para aquela concessionária, ou fila privada protegida sem destinatário; auditoria de cada caso. A heuristic provisória usa menor carteira ativa por loja com desempate por UUID. Gestão Prumo não é titular de canal Meta, gestor sem autoatribuição não é operador, e S0 continua proprietário dos status e do roteiro comercial. Caso terminal preserva histórico e não reaparece ao reativar a pessoa.

**Evidência exigida:** workflow PG17 S1-002 deve mostrar baseline S0, S1E-01..07 e S1R-01..08. Não confundir cobertura I1 com remanejamento; testes do cenário não provam corrida de duas transações ou integração com workers.

**Pendente:** contrato real de aprovador RH, escala/capacidade/feriados, trabalhador multiloja e casos sob remessa já avançada, cron de grants com validade futura, backfill de atribuições antigas, fila via API para gestores, GoTrue/REST depois de 039, funções legadas privileged e coordenação com C05/C08/Meta. Sem essas provas, **NO-GO produção, merge ou Supabase hospedado**.


## Evidência real de execução do incremento

[CI GitHub PostgreSQL 17 #39159483920 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39159483920) para o commit `2435264f56f36a572382b7e27d5c773e0e921453`; logs do job `117769573687` foram consultados. **S1R-01..08: 8/8 PASS**, mais S1E-01..07 e regressão S0 executadas antes da 039. Evidência limitada a transação sintética e RLS por role fake, não autenticação Supabase integrada ou race 2 sessões. Nenhuma migration no Supabase hospedado.


**Ampliação auditada:** [GitHub Actions PG17 #39159745461 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39159745461), SHA `47a9dd80b12ee874bd9cc4aeb680196f6acd1dc8`, **9/9 cenários S1R aprovados**. S1R-09 prova que atribuição a operador suspenso é negada mesmo para um caso sem titular ativo na fila protegida. Regressões S0 + testes I1 executados antes das migrations 039 e 038 respectivamente, não são regressão integrada pós-039. Nenhum login real, Supabase hospedado, Meta ou gasto externo.
