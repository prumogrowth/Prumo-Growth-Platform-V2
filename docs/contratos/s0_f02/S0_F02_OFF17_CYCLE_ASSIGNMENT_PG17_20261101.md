# S0/S1 F02 — OFF17-F02-VERSIONS-01, ciclo e atribuição independentes no PG17

**Data:** 01/11/2026  
**Issue:** [#7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7)  
**Classificação:** `F02_INDEPENDENT_VERSIONS_PG17_LAB_ONLY` — revisão candidata, **não homologada**.

## Achado reproduzido

A OpenAI identificou em OFF-17 que a função S0 `_sources` fazia duas comparações de `case['assignment_revision']`, uma contra `expected['cycle']` e outra contra `expected['assignment']`, embora OFF-04 declare as revisões como independentes. [Parecer OFF-17 na Issue #7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7#issuecomment-6560166682), [CI de reprodução OpenAI](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41322708635). A evidência anterior de F02 com ambos os valores `1` não demonstrava a separação.

**Decisão:** opção A solicitada pela OpenAI: separar fisicamente a origem do ciclo da revisão de atribuição, sem descartar `cycle` nem alegar equivalência. Não houve tentativa de ajustar o consumidor OFF-04 para aceitar dados incorretos.

## Implementação candidata

Base S0 consolidada `13a091aaa75afad45a5609bf3cd6bba8b0ebde0e`. Branch isolada `exp/s0s1-f02-independent-cycle-pg17-20261101`.

- `integration/s0s1_f02/pg17_schema.sql`: nova tabela `s0_f02_lab.case_cycles`, com FK para `s0_pre_dispatch_lab.cases(case_ref)`, `cycle_revision` e `flow_ref` independentes; nenhuma concessão ao papel runtime, RLS habilitada. A tabela `s0_f02_lab.requests` armazena **`cycle_revision` própria**, ao lado de `assignment_revision`. Este schema só instala no PostgreSQL 17 descartável e não representa origem hosted S0 autenticada.
- `integration/s0s1_f02/pg17_service.py`: solicita `flow_ref` explicitamente na requisição privada S0; bloqueia `s0_pre_dispatch_lab.cases` e `s0_f02_lab.case_cycles` e compara `case_revision`, `cycle_revision`, `assignment_revision` e `policy_revision` com **campos físicos distintos**. Registro/recuperação da solicitação preserva as revisões; `review_in_admin_transaction` relê as duas fontes antes de aceitar proposta, verifica novamente os valores persistidos e o fingerprint completo. Falta ou mudança do vínculo `flow_ref` nega. A origem do ciclo ainda é uma fixture S0/F02 local, não uma autoridade comercial ou operacional autenticada.
- `integration/s0s1_f02/test_pg17_service.py`: fixture cria `flow_A` e `cycle_revision=1` independente da atribuição inicial. Foram adicionados **12 testes físicos** direcionados: `cycle=2/assignment=7` com recheck positivo, `5/1`, `1/9`, stale de cada dimensão, mudanças após a proposta, fonte ausente, outro `flow_ref`, replay `4/8`, negação de acesso runtime e stale durante recheck com `3/5`.
- `integration/s0s1_f02/emit_off04_evidence.py`: gera evidência **diretamente do PG17 descartável** com `cycle=3` e `assignment=7`, verifica os dois valores persistidos e fornece envelope privado ao teste do OFF-04 original.
- `integration/s0s1_f02/test_off04_interop.mjs`: consumidor pinado aceita `cycle=3, assignment=7` como revisões independentes e rejeita mudança individual em `currentVersions.cycle` ou `currentVersions.assignment`; estado `STALE` pode omitir flags de autoridade, mas nunca é lido como grant.
- `.github/workflows/exp-s0s1-f02-independent-cycle-pg17.yml`: workflow isolado, com análise de delta exato, pin de OFF-04 original e do ingresso PG17, execução de testes com banco descartável, sanitização do artefato e regressões físicas PRE_DISPATCH anteriores.

## Evidência verificada e auditoria

[Execução física funcional após ajustes — 41327442027](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41327442027): 2/2 jobs success. **37/37 F02 físicos**, **11/11 interop OFF-04**, **71/71 testes originais OFF-04** e **24/24 regressões PRE_DISPATCH**; total **143 casos distintos**, não duplicando os nove testes de interop offline e os dois condicionados à fixture PG17. Os dois testes dependentes do artefato PG17 são omitidos apenas no job offline e passam no físico. Fonte OFF-04 original pinada `1f8157838c11a7b59456a3b178a8ade21a17b42b` e blob `4cff139912b9afed7a159d17ad68a894cdd0a5df`; S0 ingresso `01ffdb093013664b73b18d23f92aac2202578210`.

Tentativas CI anteriores não foram aprovadas: (a) checagem de escopo exigia um relatório ainda não criado; corrigida; (b) edição textual produziu DDL truncado; reconstruído a partir do original; (c) o teste de negação `STALE` exigia flags `false` explícitas não presentes no contrato OFF-04, em vez de somente exigir que não fossem `true`; corrigido sem alterar a OpenAI. A execução citada passou depois desses ajustes. O commit final com este relatório terá **uma CI adicional própria**.

Escopo esperado do diff contra a base: cinco arquivos F02 alterados, um workflow CI novo e este relatório; sem modificações no código OpenAI, Meta, Frontend, ingress técnico pinado, Supabase ou `main`.

## Segurança e limites operacionais

Toda saída S0 permanece `send_authorized=false`, `schedule_authorized=false`, `production_authorized=false`, `provider_approval_verified=false`, `consent_source_authenticated=false` e `m2m_operationally_verified=false`. O envelope OFF-04 privado **não é payload de modelo**: deve passar por `f02ProviderView` para minimizar identidade/refs do host. Não há chamada à OpenAI real, Graph, WhatsApp, agendamento, reserva, envio, segredos, dados pessoais, merge ou deploy. A fixture de fluxo não comprova que existe um controlador de ciclos durável e autenticado na S0 hospedada. Escritores operacionais precisam seguir o lock transacional do caso/ciclo ou passar por fonte controlada equivalente; a prova atual é apenas no PG17.

**Solicitação à frente OpenAI:** reavaliar OFF17-F02-VERSIONS-01 sobre o código da branch e resultados PG17 com duas revisões legitimamente diferentes; devolver parecer **ACEITE_TECNICO_CANDIDATO ou incompatibilidades específicas** na mesma Issue #7. Mesmo eventual aceite de contrato não significará autorização operacional sem fontes reais, identidade S0, meta-provider approval e gates #8/#9/#10.

**Próxima dependência independente:** contrato S0 verdadeiro para ciclo/cadência e atribuição com propriedade, revisão, autoria e revogação; responsabilidade da S0/Infra e das frentes de operação, sem substituir estados de fluxo por atribuição administrativa.
