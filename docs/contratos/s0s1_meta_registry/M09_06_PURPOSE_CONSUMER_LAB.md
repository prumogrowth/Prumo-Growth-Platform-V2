# S0/S1 M09-06 — consumidor de slot por finalidade, **apenas laboratório**

**01/11/2026 · Estado:** `S0S1_M09_06_PURPOSE_SLOT_LAB_UNVERIFIED`. Issue canônica: https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8. **Sem aceite de interface pela Meta, sem autorização produtiva.**

## Proveniência e arquivos

- Base S0 M09-05: `184753988addcc4c4df6a5a05ec688b8310438d3`. Fonte PG17 física pinada e separada `01ffdb093013664b73b18d23f92aac2202578210`; Meta WA04A/WA09 original em `745f54acd8255bea728c5ab7c87848d5018ad66b`. Nenhum arquivo dessas fontes foi editado.
- Branch `exp/s0s1-m09-purpose-consumer-20261101`. Arquivos novos: `integration/s0s1_m09_registry/purpose_slot_consumer.ts`, `test_purpose_slot_consumer.mjs`, `emit_purpose_slot_evidence.py`, workflow `.github/workflows/exp-s0s1-m09-purpose-consumer.yml` e este relatório. A CI verifica diff limitado contra o SHA M09-05.

## Mudança concreta

- Candidato TypeScript `inspectPurposeSlotLab` recebe: (a) saída M09-04 com revisões separadas e escopo de canal; (b) **testemunho de slot não confiável**, deliberadamente limitado a uma finalidade e um nome de slot; (c) solicitação de finalidade, escopo e cinco revisões esperadas independentes. Reaproveita a auditoria M09-05 `inspectM09ForMetaOffline` e confere igualdade completa de loja/App/rota/canal/WABA/número, cinco revisões, digest, App e finalidade específica. Recusa flags de autoridade, slots de formato inválido, proxi, getters, propriedades extras, alias de propósito, versões stale e incompatibilidade de fontes.
- Apenas retorno `LAB_SLOT_NAME_MATCHED_UNVERIFIED` ou `DENIED`; sucesso mostra **um único nome de slot** por requisição, sem os outros dois. Não devolve segredo, token, bearer, chave de assinatura ou acesso ao vault. Todas as flags `production_authorized/send_authorized/graph_authorized/ack_allowed/s0_write_authorized/m2m_operationally_verified` permanecem falsas.
- O testemunho `source_role=DISPOSABLE_PG17_INSTALLER_UNVERIFIED` é somente um rótulo de fixture e **não constitui atestado criptográfico ou credencial**. Um atacante pode forjar tanto a saída JSON quanto o testemunho e obter um pareamento **estrutural**; por isso este módulo não pode ser instalado como autorizador nem consumido por executor de credencial. O slot é metadado técnico de teste, não uma concessão de leitura de segredo.
- A consulta M09-04 existente assina e lê apenas `REGISTRY_READ`; ela **não autoriza** `GET_VERIFY_TOKEN`, `POST_APP_SECRET` ou `GRAPH_ACCESS_TOKEN`. O gerador de ensaio `emit_purpose_slot_evidence.py` usa o **instalador PG17 descartável**, após o read Ed25519, para buscar um único slot `POST_APP_SECRET` do App na tabela `s0_m09_lab.slots` e produzir JSON transitório com status não verificado. Esse privilégio de fixture **não** é atribuído ao runtime.
- Não houve alteração de funções WA-04A/WA-09 originais nem passagem de `TrustedMetaRegistry` fabricado. A saída não habilita envio, Graph, verificação Meta de HMAC, HTTP/ACK ou efeitos comerciais.

## Evidências de execução

- [GitHub Actions 41292544197](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41292544197), execução funcional no SHA `a07010a807479bb1bafd7b290cd4e4d80088e2d2`: **dois jobs aprovados**.
- Job offline: **22/22 casos M09-06 aprovados**, um cenário dependente de PG17 corretamente **skipped**; **63/63 testes Meta originais WA04A/WA09 aprovados**, em checkout pinado.
- Job PG17 isolado: **23/23 testes M09-06 aprovados sem skip**, incluindo caso de evidência PG17 assinada + slot do instalador e rejeição de propósito cruzado; **16/16 testes físicos M09-04 de Ed25519/antirreplay aprovados**. O PG17 original é descartado após o teste, sem mudança na árvore pinada.
- **23 novos cenários distintos**, não 22 + 23. As 63 regressões Meta e 16 físicas M09-04 são herdadas e não devem ser contadas como testes novos.
- O commit deste relatório é posterior ao SHA funcional acima e exige CI própria. Não usar evidências de SHA anterior para alegar CI de commit final.

## Dependências abertas

**Meta:** não há resposta ratificando o contrato scoped da M09-05. Solicita-se revisão específica do shape por finalidade, estratégia de slot único, cinco revisões e separação do contrato WA04A antigo, sem forçar registro com três slots. **S0/S1:** construir camada real autenticada de host/principal, contrato de resposta assinado/atestado e recheck de ponto de uso, com segurança de privilégio e retenção/revogação. **Infra/Proprietário:** titularidade/delegação de App, WABA e número, custódia de segredos/chaves, trust anchors e autorização para ambiente hospedado. No cenário atual, todas as evidências de posse/delegação seguem `UNVERIFIED`.

Sem Graph, banco hospedado, merge, deploy, secrets reais ou licença de comunicação externa. #2 (ingresso/recibo/ACK), #7 (F02) e #10 (PRE_DISPATCH) seguem distintas da M09.
