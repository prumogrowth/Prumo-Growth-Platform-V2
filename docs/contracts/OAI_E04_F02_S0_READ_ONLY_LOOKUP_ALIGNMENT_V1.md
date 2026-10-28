# E04 A37 — alinhamento de consulta S0 somente leitura, sem autenticação

**28/10/2026.** Base: F02 `8ed7d14` / GitHub Actions #40673052410 SUCCESS, 1.338 testes. Implementação exclusivamente no código F01/F02/F03. **Nenhuma mudança na S0.**

## Contratos efetivamente verificados

A S0 já fornece o **schema de resultado candidato** `prumo.s0.f02.review.result/0.1-candidate`, fixado byte a byte em `docs/contracts/upstream/OAI_S0_F02_REVIEW_RESULT_SCHEMA_0_1_PINNED.json`. A própria F02 já implementou `inspect_s0_review_projection` para validar forma e continuidade **do resultado declarado**. Não foi criado um segundo contrato de resposta S0.

O novo `backend/f02_s0_lookup_alignment_candidate.py` integra esse vocabulário de estados com o `ReplayObservation` do A36. A função `inspect_s0_lookup_alignment_candidate(observation,binding,result,expected_s0_request_sha256,previous_result)` compara o escopo declarado de loja/lead/caso/ciclo, canal, rota, fechamento, F03, F02 e chave de idempotência com a observação A36. Valida o conjunto estrito de campos e os 13 estados da resposta S0 pinada: resultados de registro ou leitura continuam **apenas revisão**; estados WITHDRAWN/EXPIRED e todos os negativos permanecem em **bloqueio**; flags de envio/agendamento/transição comercial devem ser sempre falsas; revision/instantes/identificador não podem regredir contraditoriamente.

### Decisão de fronteira: dois digests diferentes

O SHA-256 de A36 é um digest determinístico de **jornada/proposta sintética da F02**. O `request_sha256` da S0 é do documento interno de solicitação S0, que considera inclusive campos temporais e o binding físico. **Não são semanticamente intercambiáveis.** Por isso a função aceita um `expected_s0_request_sha256` separado, exigindo correspondência com a projeção S0 quando seu estado é persistido. Esse valor continua **fornecido pelo chamador**, não autenticado. Uma coincidência, ou um hash fabricado, não equivale a origem S0 verificada. A semântica temporal da S0 não adota os limites de 48h do laboratório F02.

A resposta S0 0.1 também **não inclui loja/lead/caso/rota/canal**, de modo que comparar o escopo de duas alegações F02 não demonstra que o registro consultado pertence àquele escopo. A interface física terá de obter contexto CFI/GoTrue server-owned e validar a origem da resposta. `LookupBindingClaim` NÃO é token, sessão, decisão de Gestor ou credencial S0; `F02_UNVERIFIED_READ_ONLY_S0_LOOKUP_CLAIM` é estado fixo de laboratório e qualquer falsa promoção é recusada.

### Resultado do incremento

O resultado positivo `PERSISTED_SHAPE_RECHECK_ONLY` significa somente **forma compatível de dados passados por um chamador**. Não houve consulta à S0, leitura autenticada, emissão de evidência, escrita, persistência, envio ou ratificação gerencial. Falta de histórico antigo não comprova completude; `UNAVAILABLE` não autoriza reconstruir ou duplicar pedido. Terminal não pode ser reaberto por snapshot posterior. O modo anterior `inspect_s0_review_projection` permanece inalterado; este verificador é um alinhamento read-only do contrato com o novo A36.

O arquivo `docs/contracts/OAI_E04_F02_S0_READ_ONLY_LOOKUP_PORT_CANDIDATE_V1.json` especifica **requisitos de futura fronteira S0**, não endpoint aprovado nem ordem para outra frente: contrato de resposta versionado, transporte autenticado, binding CFI server-owned, lookup auditável após perda do processo, fonte do hash interno, CAS/concorrência, identidade de capturador versus gestor distinto e preservação da política de privacidade.

### Testes e pendências

`backend/tests/test_f02_s0_lookup_alignment_candidate.py` adiciona **35 testes**: estados 13/13, flags falsas, projeções inválidas, divergência entre hashes, escopo cruzado, chave trocada, revisão regressiva, retrocesso temporal, terminal/negativo, expiração e instantes UTC equivalentes. O runner PG17 preserva todas as outras suítes. O critério F02-A37 ficará LAB_VERIFIED apenas após CI SUCCESS.

**G01–G07 permanecem abertos**; em especial G02 (consulta/retorno autenticado da S0), G03 (proveniência das quatro testemunhas) e G07 (ensaio físico F01/F03/F02) não avançam de status por mera simulação. Merge, deploy, Meta e OpenAI API real continuam fora de escopo; o PR #1 segue Draft. S0 só precisa atuar quando uma integração autorizada exigir alteração ou decisão de fonte de sua responsabilidade.
