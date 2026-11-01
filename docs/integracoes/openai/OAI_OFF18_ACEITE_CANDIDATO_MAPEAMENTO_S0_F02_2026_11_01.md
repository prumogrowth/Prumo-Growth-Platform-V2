# OFF-18 — Verificação OpenAI da correção S0 F02 (cycle x assignment)

**Data:** 01/11/2026. **Issue:** [#7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7). **Classificação:** `AVALIACAO_CONTRATO_CANDIDATO_OFFLINE`; nenhum efeito operacional.

## Resposta S0 recebida

Após a descoberta OpenAI OFF-17 [reproduzida no CI 41322708635](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41322708635), S0 respondeu na [Issue #7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7) e publicou a **opção A**: duas fontes físicas independentes na branch `exp/s0s1-f02-independent-cycle-pg17-20261101`, commit `31e88ec2632e861d55c2e0ae4766f8a0a4362e22`.

- `s0_f02_lab.case_cycles(case_ref,flow_ref,cycle_revision)` — ciclo em PG17 descartável, com vínculo explícito de `flow_ref`.
- `s0_pre_dispatch_lab.cases.assignment_revision` — atribuição, separada do ciclo.
- `requests.cycle_revision` própria; `review_in_admin_transaction` volta a consultar ciclo/atribuição e verifica persistência/fingerprint, segundo código S0.
- [CI S0 41327577931](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41327577931) concluiu com 37 testes físicos F02, 11 interop OFF-04, 71 regressões OFF-04 e 24 regressões PRE_DISPATCH, **143 casos distintos de laboratório**, sem duplicação entre jobs.

## Verificação independente OpenAI

`e04_offline_lab/tests/off18_s0_f02_independent_cycle_review.py` compila **somente a AST da função `_sources` do arquivo Python S0 original** extraído com `git show` do SHA `31e88ec...`. O cursor de teste é uma *fixture* em memória: a verificação é **de função-fonte, não de PG17 verdadeiro**, e não altera a S0.

Entre os **24 casos**:
- aceita `cycle=3,assignment=7`, `5/1` e `1/9`, com escopo e versões de origem correspondentes;
- rejeita mudança unilateral do ciclo ou da atribuição;
- rejeita `flow_ref` trocado ou `case_cycles` ausente;
- mantém as negativas de caso/política/catálogo/grant/consentimento vencido, opt-out, template sem aprovação/mídia, cross-store, catálogo duplicado e campanha/grant inativo.

**Gate CI** exige dois resultados separados no mesmo HEAD da branch: **950/950 testes OpenAI Node acumulados**, **24/24 testes Python AST da fonte S0 pinada**. Nenhuma soma desses casos representa uma suite física OpenAI+PG; os 143 testes S0 permanecem uma evidência separada.

## Critério de decisão

Se a CI validar essa matriz, a OpenAI pode registrar **`ACEITE_TECNICO_CANDIDATO_DO_MAPEAMENTO_CYCLE_ASSIGNMENT`**, exclusivamente para a independência da revisão e compatibilidade estrutural com OFF-04, sem equivaler a aceite operacional. Esse parecer se limita ao mapeamento `case_cycles` e `assignment_revision`; não atesta revisão end-to-end da função de armazenamento nem autenticação.

**Não foram resolvidos:** fonte operacional/autenticada dos ciclos, controle de escritores/locks em hospedagem real, catálogo Meta, consentimento verificável, finalidade/campanha reais, event sourcing/outbound WA39, PRE_DISPATCH transacional de envio, recuperação multi-instância, chamada de modelo e credenciais/segredos. `send_authorized`, `schedule_authorized` e `production_authorized` continuam **false**.

**Sem API OpenAI, sem PostgreSQL nesta suíte OpenAI, sem Graph, merge, deploy ou operações com clientes.**