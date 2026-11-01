# OFF-13 — Revisão conservadora da posse F01 / S0 (somente laboratório)

**Data:** 01/11/2026. **Status:** candidato offline e não ratificado. **Issue preexistente:** [#11 — F01/S0 posse IA, handoff definitivo e recheck](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/11).

## Base existente e limite

- [F01 OFF-05](./e04_offline_lab/f01-sales-boundary.mjs) já implementa turno/proposta, revisões sintéticas, bloqueios pós-handoff e journal, sem autorização de publicação.
- [Issue #11](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/11): a S0 confirma **apenas a divisão de responsabilidades** — leitura de posse inicial + recheck transacional posterior e handoff irreversível. **Não há endpoint ou contrato autenticado F01 de S0 ratificado**.
- [S0 I81, ownership administrativo restrito v1](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/6972c8011dc4b4a7855707a2050801470ec21165/docs/contratos/i81_ownership/CONTRATO_OWNERSHIP_V1.md) não é ownership da IA, não concede publicação de mensagens nem substitui handoff operacional. Não reutilizar grants administrativos.
- [#12](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/12): fontes comerciais por loja ainda sem fonte canônica/versão homologadas; o guarda de posse não resolve evidência semântica nem vigência de oferta.
- Baseline OFF-12: [774/774 testes no GitHub](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41293123872) em `cc2321735bf7609e6d03719562fbe28d6eea45cb`.

## Incremento OFF-13

Módulo `e04_offline_lab/f01-s0-ownership-review-lab.mjs`, função pura `reviewF01S0Ownership`, contrato de **fixture** `prumo.openai.f01-owner-recheck/0.1-lab`. `before` e `after` são descrições **não verificadas** de posse/loja/caso/pessoa, handoff, opt-out, elegibilidade, pós-remessa/venda, tempo e versões de caso/ciclo/atribuição/catálogo/conhecimento/política/rota/consentimento.

Todas as saídas, inclusive `LAB_CONSISTENT_UNVERIFIED`, carregam `principalAuthenticated=false`, `s0OwnerVerified=false`, `s0SnapshotAuthenticated=false`, `modelInvocationAuthorized=false`, `publishAuthorized=false`, `handoffAuthorized=false`, `consultantAssignmentAuthorized=false`, `f02RestartAuthorized=false`, `sent=false`, `commercialTransitionAuthorized=false`, `productionAuthorized=false` e `requiresS0TransactionalRecheck=true`.

Verificações determinísticas:

- **Escopo primeiro**: qualquer divergência de loja/caso/pessoa é `DENIED` sem expor identificação no resultado.
- **Handoff definitivo**: posse humana, `handoffDefinitive` ou `humanized` em qualquer um dos snapshots impedem retomada da F01; regressão de estado humano para IA gera revisão, não reativação. Novo inbound não é grant.
- **Opt-out, canal, pós-remessa e pós-venda**: negam continuidade, mesmo que a fixture alegue versão compatível.
- **Tempo e versão**: snapshot inicial anterior à requisição, relógio regressivo, deadline excedido e variação de versão exigem revisão, atraso ou `STALE`; sem corrigir a versão por inferência.
- **Hostilidade**: campos extras, propriedades accessor, ciclos, protótipos estranhos e tipos inconsistentes falham sem executar getters.
- **Sem dados pessoais ou efeitos**: a saída não contém IDs, conteúdo, tokens, nomes de Consultor, prompt, plano, recibo ou operação. A função não faz I/O, SQL, OpenAI/Meta, gravação ou autorização.

`e04_offline_lab/tests/f01-s0-ownership-review-lab.test.mjs` acrescenta **45 testes**. Alvo da regressão cumulativa: **819** (774 históricos verificados + 45 novos), apenas na mesma árvore da branch OFF-13, não soma de CI separados.

## O que ainda falta para integração real

1. **S0/S1, Issue #11:** contrato autenticado para leitura de posse e handoff, versão/ordem monotônica, estado durável irreversível, principal/loja/caso, idempotência, concorrência e CAS/recheck **na mesma transação de publicação**.
2. **S0/S1, Issue #12:** fonte canônica da base de conhecimento comercial, autorização por concessionária, cutoff, correções, validade, minimização e verificação semântica.
3. **Meta/S0:** publicação somente por porta autorizada, recheck da rota/canal/consentimento e transporte; saída da OpenAI é rascunho, não dispatch.
4. **Frontend, #13:** resumos curtos de F01/F02/F03 para aba Resumo continuam **futuros**; não implementar nesta etapa.

**Sem mudança de schema/RLS, S0, Meta, Frontend, banco, produção, merge, credenciais ou modelos operacionais.** Não confundir `LAB_CONSISTENT_UNVERIFIED` com autorização ou aceite de contrato.
