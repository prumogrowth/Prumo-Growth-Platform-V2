# Gate de regressão offline WA / Meta e S0 — evidência de GitHub Actions

**Atualização:** 20/10/2026 UTC (19/10/2026 à noite em Recife). **PR #2:** branch `docs/whatsapp-meta-concessionária de demonstração-poc-20261017`, permanece **Draft**, sem merge ou deploy. Esta evidência confirma execução de testes com fixtures, não valida operação Meta/Graph.

## 1. Regressão integral Meta no checkout completo

- GitHub Actions: [Prumo Meta — regressão offline integral, run #1](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39358830368).
- `run_id=39358830368`, `job_id=118419912485`, commit Meta executado `3f40565b3a13d72801f81aff122d46647b0b2fa2`.
- Workflow novo `.github/workflows/whatsapp-meta-offline.yml`: executa a cada atualização elegível do PR Draft contra `main`; `ubuntu-latest`, `actions/checkout@v4`, `actions/setup-node@v4` com `node-version: '22'`, comando `bash integrations/whatsapp-meta/run-offline-tests.sh --all`, sem `npm install`, sem segredos e sem conexões Graph/Meta.
- `run-offline-tests.sh --all` verifica que existem **ao menos 29 arquivos `*.test.ts`** e que os casos essenciais (ponte S0, binding, commit incerto, evidência, reconciliação, inbound, outbound, webhook roteado, gateway ingresso) estão presentes; então executa `node --experimental-strip-types --test --test-concurrency=1` no checkout completo.
- **Log TAP auditado pela API do GitHub**: `# tests 467`, `# pass 467`, `# fail 0`, `# cancelled 0`, `# skipped 0`, `# duration_ms 6714.216399`. O job `meta-offline` e o workflow terminaram com `conclusion=success`.
- Esta execução **não** mede taxa de sucesso em produção, não prova autenticação real da Meta, envio de templates, disponibilidade de tokens, callback com webhook HTTP ou ACK S0 durável. Não existe `fetch` operacional para Graph neste laboratório.

## 2. S0 — prova PostgreSQL 17 isolada, já publicada no PR #1

- Workflow [Prumo S0 — PostgreSQL isolado, run #335](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39358441903).
- `run_id=39358441903`, `job_id=118418652947`, commit S0 executado `364adfc741246832a5f33989162bc70b3bc5d4ec`.
- Contêiner `postgres:17` temporário, banco fictício `prumo_s0_test_ci`, encerrado e removido ao final.
- Logs verificados: **WA14-01..18 = 18/18 PASS**, **WA14C-01..03 = 3/3 PASS** (sessões concorrentes), S0-040 WA40-01..05 **5/5 PASS**, pré-requisito PG17 real **PASS**, suíte mock de pré-requisito **10/10 PASS**, Python **24 PASS**, executor das migrations/SQL S0 exit 0.
- Arquivo de auditoria no PR #1: `docs/S0_041_WA14_VINCULO_TENTATIVA_META_AUDITORIA_2026_10_19.md`.

## 3. Conclusão e limites do gate

**Validado em execução real de CI:**
- O adaptador Meta passa a regressão offline integral em Node 22: **467/467**.
- O ledger S0-041 passa os testes sintéticos PostgreSQL 17 e concorrência: **21/21** WA-14.
- O vínculo App/WABA/emissor S0-040 foi novamente provado no PostgreSQL isolado: **5/5**.

**Não validado:** ligação de um serviço real Meta à persistência S0, autenticação/segredos operacionais, Graph, recebimento de webhooks reais, provas de commit desconhecido sob falha de infraestrutura externa, decisão comercial da S0 em produção, autorização de C03/C06/C12, deploy, instituição financeira e custos de serviços. A regressão PostgreSQL especializada **WA-06D (20 casos)** não aparece nos logs S0 deste gate e não deve ser incluída como aprovada.

**Decisão:** manter PR #1 e #2 em Draft; prosseguir para desenhar/testar o adaptador técnico WA-13 ↔ S0-041 sob escopo estrito, antes de discutir qualquer integração/ativação operacional. Nenhum merge/deploy autorizado.
