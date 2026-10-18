# S1-002/I2 — Implementação de redistribuição no sandbox | 18/10/2026

**Escopo:** protótipo SQL 039 da frente S1-002, sem API pública, frontend, OpenAI, Meta, Banco ou infraestrutura hospedada. Complementa [contrato I2](S1_002_I2_CONTRATO_REMANEJAMENTO_AUTOMATICO_CF_OP_02_v0_1.md), PR #5, PR #7 e issue #6.

**Mecanismo:** team state ativo→suspenso/desligado e última concessão operacional por loja revogada acionam remanejamento na mesma transação: guard nas novas atribuições, encerramento da atribuição antiga, nova atribuição exclusivamente a operador Prumo ativo com concessão válida para aquela concessionária, ou fila privada protegida sem destinatário; auditoria de cada caso. A heuristic provisória usa menor carteira ativa por loja com desempate por UUID. Gestão Prumo não é titular de canal Meta, gestor sem autoatribuição não é operador, e S0 continua proprietário dos status e do roteiro comercial. Caso terminal preserva histórico e não reaparece ao reativar a pessoa.

**Evidência exigida:** workflow PG17 S1-002 deve mostrar baseline S0, S1E-01..07 e S1R-01..08. Não confundir cobertura I1 com remanejamento; testes do cenário não provam corrida de duas transações ou integração com workers.

**Pendente:** contrato real de aprovador RH, escala/capacidade/feriados, trabalhador multiloja e casos sob remessa já avançada, cron de grants com validade futura, backfill de atribuições antigas, fila via API para gestores, GoTrue/REST depois de 039, funções legadas privileged e coordenação com C05/C08/Meta. Sem essas provas, **NO-GO produção, merge ou Supabase hospedado**.
