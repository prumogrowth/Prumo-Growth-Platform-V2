# CI/S1 — experimento controlado I27/I28 (25/10/2026)

**Resultado:** ensaio A/B concluído com sucesso nos três workflows executados sobre o **mesmo commit** `a9da6bd8549b039bee1ee7d902929966a23c8465`. Todo o ensaio permaneceu em `exp/ci-s1-consolidacao-20261025` e não alterou a S1 oficial.

## Execuções controladas e equivalência

| Modalidade | Run | Jobs | Resultado | Somatório observado de tempos dos jobs |
| --- | --- | --- | --- | --- |
| Controle oficial I27 copiado, somente trigger alterado | [#40200376294](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40200376294) | 2 | SUCCESS / SUCCESS | 151 s |
| Controle oficial I28 copiado, somente trigger alterado | [#40200376287](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40200376287) | 2 | SUCCESS / SUCCESS | 162 s |
| Workflow experimental serial, duas stacks independentes | [#40200376262](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40200376262) | 1 | SUCCESS | 197 s |

**Tempo observado em runner:** controle 313 s (5min13s) vs experimental 197 s (3min17s). **Redução de 116 s, cerca de 37,1%** no somatório dos intervalos started_at–completed_at dos jobs. Esses valores não são a contagem faturável oficial da plataforma, nem garantia de economia futura.

**Tempo até o resultado:** controles rodaram em paralelo e completaram o E2E mais lento em cerca de 143 s (além do overhead de disparo/encerramento); o candidato levou 197 s, portanto **o retorno consolidado ficou aproximadamente 54 s mais lento**, apesar de consumir menos runner-minutes. Este trade-off deve entrar na decisão.

## Cobertura comprovada

Workflow experimental:
- **78/78 testes unitários**: I23 30, I25 10, I26 10, I27 13, I28 15 (suítes cumulativas, executadas uma vez cada).
- **I27 E2E: 80/80 cenários** aprovados.
- **I28 E2E: 93/93 cenários** aprovados.
- Para cada E2E houve novo `supabase init/start/stop --no-backup`, ambiente GoTrue/PostgREST e banco PostgreSQL **isolados**. Não houve compartilhamento de identidade, migrations nem fixtures entre I27 e I28.
- Os controles executaram os comandos originais I27 e I28, modificando apenas o nome/gatilho/concurrency para alcançar a branch experimental. Sem código produtivo editado.

Repetibilidade parcial: candidato já teve três runs SUCCESS; #40199747311 (3m11s), #40200072455 (3m22s), #40200376262 (3m17s). Apenas a terceira é A/B isocommit com controles.

## Limites e decisão
- Esta conclusão cobre **somente** o par I27/I28. Não extrapolar a economia para S0, Frontend, Meta, OpenAI ou outros workflows S1.
- O ganho é de **consumo de runners**, e não de menor latência de feedback. Compartilhar banco sem reinicialização violaria isolamento e invalidaria a aprovação.
- O experimento não prova equivalência dos demais workflows: persistência, witness, revogação, intempestividade, concorrência, S1 I37 e autorização com casos ficam intactos.
- **Nenhum workflow oficial foi desativado ou modificado.** Sem merge, deploy ou alteração de `main`.
- **Recomendação:** submeter ao owner da S1 o uso opcional do workflow agregado I27/I28, mantendo todos os gates obrigatórios e checks atuais até revisão e aprovação explícita. Se a latência de feedback for prioritária, avaliar alternativa com unitários compartilhados e E2E paralelos, sem alegar a mesma economia.
