# OFF-23 — Auditoria independente do recibo de ciclo F02 entregue pela S0

**Data:** 01/11/2026. **Issue:** [#7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7). **Classificação:** REVISÃO DE CÓDIGO CANDIDATO COM CONTRAPROVAS SOURCE-LEVEL; **não** é PG17 físico nem atestado de serviço hospedado.

## Entrega revisada

A S0 entregou na Issue #7 o controlador adicional [`integration/s0s1_f02_cycle/pg17_service.py`, commit `054261b23b312421a6956b51ff5b37d36f10babb`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/054261b23b312421a6956b51ff5b37d36f10babb/integration/s0s1_f02_cycle/pg17_service.py), com [CI PG17 41337121331](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41337121331): **165 casos distintos aprovados**, incluindo 24 novos PG17, 37 F02, 24 PRE_DISPATCH, 71 OFF04 e 9 interop OFF04 efetivamente executados (2 skips offline excluídos). O estado é `LAB_ONLY/ENTREGUE_PARA_REVISAO`, com chave Ed25519 de fixture e nenhum mandato operacional real.

É uma entrega materialmente distinta do mapeamento independente `cycle/assignment` aceito pela OFF-18: agora a S0 inclui comandos assinados, CAS de revisão, estado `ACTIVE/PAUSED/REVOKED`, trilha em banco e um `readback` pós-COMMIT. A **OFF-18 não aprovou este controlador**.

## Dois achados da revisão da OpenAI

### AUD23-CYCLE-01 — Estado atual não confrontado com o estado do evento

Em `readback`, o código S0 confirma `auth.cycle_revision == event.after_revision` e `auth.last_command_ref == command_ref`, mas **não** exige `auth.state == event.after_state`. Se `state` for alterado sem revisão/last_command (escritor fora da disciplina de CAS, manutenção, corrupção ou outra violação de invariantes), o mesmo comando ainda devolve `LAB_COMMITTED_CYCLE_READBACK` **com `state` retirado do evento**, apesar de a autoridade atual alegar `PAUSED` ou `REVOKED`.

A função `readback` é genuinamente extraída por AST da fonte S0 pinada e executada sem alterações, contra `FakeCursor` determinístico. O teste positivo compara `ACTIVE/ACTIVE`; as contraprovas deixam **revisão=2 e last_command_ref intactos** e mudam `auth.state` para PAUSED/REVOKED. A saída continua `LAB_COMMITTED_CYCLE_READBACK` com state ACTIVE. **Uma CI verde desta auditoria confirma a reprodução do desvio, não sua correção.**

**Recomendação S0:** no readback, comparar explicitamente estado efetivo da autoridade com `event.after_state` e negar/reter se houver divergência; testar fisicamente alteração silenciosa em PostgreSQL 17 e publicar um novo SHA/CI. Se houver outro contrato de supersessão/estado, documentar a precedência. Não promover snapshot `readback` como fonte S0 de permissão com base apenas na revisão.

### AUD23-CYCLE-02 — Ator da linha do evento não confrontado com o solicitante do readback

O `readback` valida `auth.actor_ref == host.actor_ref`, mas não valida `event.actor_ref == host.actor_ref` nem `event.actor_key_revision` contra o registro apropriado do evento/ator. Uma alteração sintética de `event.actor_ref` para outra identidade passa com `LAB_COMMITTED_CYCLE_READBACK`, porque a autoridade corrente coincide com o host. **Isto é um problema potencial de proveniência do recibo em caso de escrita/journal fora da disciplina prevista**, não prova de que um cliente possa alterar a tabela real. A tabela `commands` é protegida no PG17 LAB; a severidade em produção depende de writers/ACL e da regra de rotação que a S0 definir.

**Recomendação S0:** exigir escopo e ator coerentes entre evento, host e autoridade (ou documentar política de rotação), cobrir adulteração com teste físico e preservar o conceito de recibo histórico sem tratá-lo como autorização presente.

## Evidência executável

`e04_offline_lab/tests/off23_s0_cycle_readback_source_audit.py` carrega **somente** a função `readback` exata da S0 por AST, do SHA `054261b...`. São **22 verificações Python** distintas: 1 cenário de correspondência, 4 contraprovas de estado/ator, ausência de evento, missing authority, falsos escopos, digest diferente, ciclo ausente/divergente, supersessão legítima, comando/host/hash inválidos e falha de dependência.

**Alvo CI desta branch:** **1068/1068 testes OpenAI Node herdados** (sem alterações de código funcional), **24/24 testes Python AST antigos** do mapeamento F02 e **22/22 novos** de `readback`. Esses três conjuntos são separados e não representam uma única integração autenticada S0/Meta. O workflow só obtém a fonte S0 com `git show` do commit pinado e a compila em memória, sem alterar o código externo ou chamar banco.

## Outros limites preservados

A S0 já documentou que `HostActor`/Ed25519 são fixtures, `prepare_guarded/review_guarded` não são a única entrada obrigatória do F02 LAB, identidade de host e KMS não existem de forma hospedada e todos os grants de modelo/agendamento/envio/Graph/produção permanecem `false`. A auditoria encontrou achados **no readback**; não analisou exaustivamente a simultaneidade multi-instância do PG, nem a integridade do journaling em serviço real.

A prioridade para a OpenAI é solicitar correção S0 **na Issue #7 existente**, não implementar regra concorrente dentro da OpenAI, nem editar módulo de outro responsável. Meta #10 e #9 continuam responsáveis por envio, PRE_DISPATCH e evidência WA39; suas correções recentes não criam mandato real.

**Decisão de integração:** `REVIEW_REQUIRED_SOURCE_READBACK_STATE_ACTOR_DRIFT`. Mapeamento `cycle/assignment` OFF-18 continua aceito somente em laboratório; **controlador/readback F02 aditivo NÃO está aceito** até S0 responder ao achado e publicar CI corrigida. Não fazer API paga, Graph, merge, deploy ou operação real.
