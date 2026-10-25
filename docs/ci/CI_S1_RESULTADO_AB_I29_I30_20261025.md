# CI/S1 — A/B controlado I29/I30 em 25/10/2026

**Estado:** experimento aprovado no escopo de testes observado, sem autorização para mudança de CI oficial ou merge. Todas as verificações correram no mesmo commit `a31c5e935e1c53bd95ff27c5b61c612255cb6889` e no ramo isolado `exp/ci-s1-consolidacao-20261025`.

| Modo | Run GitHub | Jobs | Resultados | Somatório de execução dos jobs |
| --- | --- | ---: | --- | ---: |
| Controle I29 original copiado | [#40203852442](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40203852442) | 2 | PASS/PASS | 141 s E2E + 27 s unit = **168 s** |
| Controle I30 original copiado | [#40203852317](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40203852317) | 2 | PASS/PASS | 139 s E2E + 35 s unit = **174 s** |
| Agregado I29 + I30, isolamentos separados | [#40203852236](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40203852236) | 1 | PASS | **237 s** |

## Indicadores e trade-off
- Controle: 168 + 174 = **342 s**, equivalente a 5min42s de intervalos observados em runners.
- Agregado: **237 s** = 3min57s. Economia estimada em intervalo de jobs = **105 s**, aproximadamente **30,7%**. Esse número **não é a medição de cobrança do GitHub**.
- Controles paralelos: maior job E2E levou 141 s a partir do início do seu runner; agregado levou 237 s. Portanto feedback do agregado **96 s mais lento em tempo de job**, embora consuma menos tempo somado de runner. Há variação de fila e cache não medida.
- **Cobertura preservada no experimento:** 7 suítes unitárias distintas (I23=30, I25=10, I26=10, I27=13, I28=15, I29=15, I30=15), **108/108 casos** no agregado, frente a 93 testes unitários no controle I29 e 108 no controle I30 (suítes cumulativas e repetidas). E2E I29 **105/105** e I30 **120/120**, ambos observados em logs dos controles e do agregado.
- Isolamento preservado: `supabase init/start/stop --no-backup` repetido para cada E2E; bancos GoTrue/PostgREST descartáveis independentes. Tempo das stacks no agregado: I29 122 s, I30 63 s.
- **Nota de auditoria:** o texto do marcador informativo `PASS EXP UNIT` ainda cita apenas I23/I25/I26/I29/I30. O loop executa adicionalmente I27 e I28, e os logs comprovam 7 contagens `Ran` totalizando 108; corrigir o rótulo em qualquer revisão futura do workflow, sem alterar os testes.

## Conclusão limitada
O segundo par confirma que a consolidação preservando isolamento pode **economizar minutos de execução de runners**, ao custo de **demorar mais para devolver o feedback**. É uma opção de economia de franquia, não uma forma demonstrada de acelerar testes.

Esta é apenas **uma comparação isocommit do par I29/I30**. Não extrapolar para outras suítes sem novas medições, e não desligar workflows originais. O owner S1 deve avaliar custo vs tempo de feedback, cobertura, checks obrigatórios, recorrência e rollback antes de qualquer promoção. Branch `main`, S1 oficial, Meta, Frontend e OpenAI não foram alterados.
