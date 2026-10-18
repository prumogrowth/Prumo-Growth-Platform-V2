# S1-002/I4 — Corridas de redistribuição e reconciliação (18/10/2026)

Frente exclusiva: S1-002. Run: `scripts/test_s1_002_concurrency.sh` no PG17 descartável, depois das migrations 038–040. PR #5/issue #6.

Contratos exercitados: equipe ativa e grants de loja são necessários para atribuição; suspensão/última concessão inválida retiram operador; nunca haverá dois responsáveis ativos para mesmo caso; mudança de status comercial e mensagens são propriedade S0, não S1.

**Cenários propostos:** S1C-01 fixture A+B; S1C-02 tenta atribuir caso sem dono durante suspensão e verifica rejeição após bloqueio de linha; S1C-03 duas transições (ativo→suspenso→desligado) simultâneas do mesmo operador; S1C-04 duas reconciliações simultâneas de concessão vencida, uma única história, novo dono só da loja B; S1C-05 privilégio interno negado a authenticated. O runner PG17 usa duas sessões independentes e temporalização controlada, nunca dados reais.

Critério para aceite: GitHub Actions SUCCESS e marcadores PASS S1C-01..05 no log. **Não confundir com prova de GoTrue/REST real, envio ou cron em produção.** Não modifica S0, Meta, OpenAI, Frontend ou main, e não aumenta porcentagem geral sem critérios globais concluídos.


## I4 — Primeira evidência de concorrência entre sessões

[GitHub Actions PG17 #39163239631 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39163239631), SHA `b0b5b5509107b15b4b42b7adeacc1695ff11c11d`, job `117780772360`: logs verificados **S1C-01..05, 5/5 PASS**. Suspensão versus nova atribuição, dupla mudança do mesmo profissional, reconciliação simultânea de concessão B, escopo privado negado a authenticated. A linha ERROR PROFISSIONAL_PRUMO_INELEGIVEL é **erro esperado e validado do teste negativo**; o job terminou SUCCESS. Não foi simulada suspensão simultânea de **dois** profissionais distintos neste ensaio.
