# OFF-21 — Fronteira segura entre Responses e os avaliadores F01/F02/F03

Data: 01/11/2026. Estado: **LABORATÓRIO CANDIDATO**, sem serviço conectado ou publicação. Base: OFF-20, SHA `03b0ca7173dacdbe75eb1fc5d06f286dcb291f54`, [CI 41345516113](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41345516113), 990/990 Node e 24/24 Python AST separados.

## Qual problema resolve

A [auditoria OFF-19](./OAI_OFF19_AUDITORIA_GERAL_CORRETIVA_2026_11_01.md) identificou o risco de promover `candidateRaw` diretamente para ações. A OFF-20 removeu esse campo do relatório do [preflight Responses](./e04_offline_lab/responses-shape-preflight-lab.mjs), mas ainda **não havia um caminho que obrigasse o modelo a passar por um avaliador F0x**.

A OFF-21 acrescenta `response-domain-review-lab.mjs`, função pura `reviewResponseThroughDomain`. Ela recebe, para teste, o envelope normalizado Responses, **contexto privado de laboratório emitido pela função específica F0x** e **recheck sintético explícito**. O fluxo é:

1. `inspectResponsesShape` recusa erro, recusa do modelo, ferramenta, saída ambígua, payload incompleto, modelo ou JSON/schema/tag incompatíveis. Em caso de erro **não** extrai texto bruto.
2. Somente se o preflight classificar o JSON como `UNTRUSTED_JSON_CANDIDATE`, a ponte extrai temporariamente o único texto validado, **dentro da função**, sem registrar nem devolvê-lo.
3. Valida integralmente os metadados de recheck (sem getters, protótipo adversarial, ciclos, arrays esparsos); exige formatos distintos por função e escopo **explícito**, inclusive F03 (o avaliador antigo permitia fallback na ausência de recheck, agora a ponte não permite).
4. Faz chamada ao **avaliador existente, sem inventar um segundo schema**: `evaluateF01Model`, `evaluateF02Model` ou `reviewF03Extraction`. Cada função continua exigindo seu contexto previamente emitido (WeakSet), revisão de estado e limitações de modelo.
5. Destrói a referência de saída detalhada ao retornar e fornece **somente parecer congelado e sem identificação**: `LAB_DOMAIN_REVIEW_ONLY`, `LAB_DOMAIN_REVIEW_REQUIRED`, `LAB_DOMAIN_BLOCKED`, `PREFLIGHT_BLOCKED` ou `INVALID_INPUT`. Nenhum rascunho, campo de ficha, `privateReceipt`, alias, preço, endereço, prompt, texto gerado ou informação de cliente sai da ponte.

**Sempre false:** `s0Authenticated`, `providerAuthenticated`, `sourceAuthenticated`, `modelInvocationAuthorized`, `modelOutputTrusted`, `semanticVerified`, `publishAuthorized`, `sendAuthorized`, `schedulingAuthorized`, `fieldApplicationAuthorized`, `commercialTransitionAuthorized`, `productionAuthorized`, `modelCalled`, `liveApiCalled`, `rawModelOutputExposed`, `domainProposalExposed`; e sempre `requiresS0TransactionalRecheck=true`.

## Escopo da prova

A suíte `tests/response-domain-review-lab.test.mjs` contém **38 casos**: 3 positivos, um por F0x, **sem autorização**; negativas de handoff/opt-out, versão, cross-store/cross-person, fonte comercial, template, evidência/citação, recusa, JSON duplicado, tool call, modelo incorreto, timeout/incomplete, getter e ciclos. Permissões autodeclaradas não passam pelos validadores. Target CI: **1028 Node** = 990 já auditados + 38 da OFF-21, além das **24 verificações Python AST** já pinadas; **não** são 1052 testes físicos combinados.

## Limites que não devem ser omitidos

- A função opera sobre **fixture sintética** e handles locais. Não chama API OpenAI, Meta/Graph ou PostgreSQL, não contém segredo, não faz transação, não autentica S0 e não grava decisão de negócio.
- Um parecer `LAB_DOMAIN_REVIEW_ONLY` **NÃO** é aprovação de mensagem, financiamento, templates ou aplicação de ficha. Mesmo `PROPOSED` dos validadores F0x exige recheck/consentimento/autoridade S0 em instância hospedeira futura.
- Não certifica semântica nem ausência de alucinação. `modelOutputTrusted=false` e `semanticVerified=false` em toda saída; o teste real de qualidade de modelo depende de plano de teste, orçamento e autorização específicos.
- Não faz bypass de histórico F03: o campo `currentScope` é obrigatório e o contrato multicases/cutoff/commit continua pendente da S0.
- Não garante segurança contra Proxies JavaScript malignos no mesmo processo. A futura borda HTTP deverá fazer parsing/normalização em host confiável, autenticação e quotas.
- Não substitui OFF-11 WA39/F02, ofertas comerciais reais da F01, IA Analista/Otimizadora ou IA Gestora; não implementar resumo de Frontend da Issue #13 agora.

### Próximo checkpoint após CI

A etapa **12A (pré-homologação offline)** foi ampliada; **08B/08C** aguardam contratos e aceites operacionais S0/Meta; etapas 09–11 e 12B/12C continuam pendentes. A etapa 13 não está autorizada. Não fazer merge, deploy, uso de banco/cliente real ou chamadas pagas.

[Ver o roteiro mestre](./OAI_ROTEIRO_PROGRESSO_2026_11_01.md).
