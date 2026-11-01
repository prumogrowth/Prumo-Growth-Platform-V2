# OFF-14 — F01: fontes comerciais por loja, vigência e fontes históricas

**Data:** 01/11/2026. **Estado:** LABORATÓRIO CANDIDATO, NÃO AUTORIZATIVO. **Dependência original:** [Issue #12](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/12) (S0/S1, sem contrato físico ratificado). [Issue #11](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/11) controla separadamente posse e recheck de publicação.

## Evidência anterior e base

- OFF-13 [commit `4efb643d8e6264caef55d21eeb4efb8b3f481a10`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/commit/4efb643d8e6264caef55d21eeb4efb8b3f481a10), [CI `41295797952`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41295797952): 819/819 PASS, zero falhas ou skips.
- A frente S0 [Issue #12](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/12) reconhece somente a divisão de competência: a S0 precisa identificar fonte canônica de conhecimento, aprovar seleção por concessionária, controlar versão/vigência, consentimento e minimização. **Não existe serviço de catálogo comercial F01 ratificado** no material revisado.
- `f01-sales-boundary.mjs` OFF-05 já aceita fontes atuais e históricas em **fixtures** e nega oferta vencida; OFF-14 é uma revisão independente e mais restrita de consistência **de metadados antes/depois**, sem duplicar a implementação da F01 nem alterar seu código.

## Arquivos publicados neste lote

- `e04_offline_lab/f01-commercial-source-review-lab.mjs` — função pura `reviewF01CommercialSources`.
- `e04_offline_lab/tests/f01-commercial-source-review-lab.test.mjs` — 45 testes adversariais, incluindo mudança não versionada de autorização, expiração e códigos, histórico como oferta, correções, escopo e vigência.
- `.github/workflows/oai-off14-f01-sources.yml` — regressão conjunta alvo **864 testes** (819 acumulados + 45 novos) no commit OpenAI isolado.
- `OAI_ROTEIRO_PROGRESSO_2026_11_01.md` — rastreio da etapa 08, sem declarar que a etapa operacional 09 está concluída.

## Entrada e saídas

Schema `prumo.openai.f01-source-review/0.1-lab`: identificadores sintéticos de pedido/loja/caso/pessoa/finalidade, instante de início/prazo, revisões `catalog/knowledge/policy/consent/grant`, lista mínima de claims tipadas e duas leituras simuladas contendo apenas metadados de fontes (`current/historical`, estado de aprovação, código permitido, versão, expiração, marcação de correção e loja).

**Sem texto comercial, PII, consulta de catálogo real ou login S0.** `LAB_ELIGIBLE_UNVERIFIED` significa apenas que as duas *fixtures* são estruturalmente consistentes. **Não equivale a oferta aprovada, conteúdo liberado para o provedor, garantia de semântica ou permissão de publicar.**

O resultado nunca revela identificadores, conteúdo, versões nem fontes e **sempre** fixa:
`s0SourceAuthenticated=false`, `s0CatalogVerified=false`,
`contentGrantVerified=false`, `provenanceAuthenticated=false`,
`semanticSupportVerified=false`, `commercialOfferAuthorized=false`,
`modelContentAuthorized=false`, `modelInvocationAuthorized=false`,
`publishAuthorized=false`, `sendAuthorized=false`,
`productionAuthorized=false`, `requiresS0TransactionalRecheck=true`.

## Negativas principais

- **Escopo:** loja, caso, pessoa, finalidade ou fonte de outra concessionária → `DENIED/SCOPE`, antes de expor detalhes.
- **Autorização sintética:** `LAB_DENIED` → negação; `LAB_UNKNOWN` → revisão; nenhuma serve como grant físico.
- **Atualização e corrida:** conhecimento, catálogo, política, consentimento ou grant alterado → `STALE`. Alteração de status/expiração/fonte/códigos mesmo sem revisão → `REVIEW_REQUIRED/SOURCES_CHANGED`. Isso **não prova** ausência de ABA ou garante transação.
- **Oferta atual:** exige estado `APPROVED_ACTIVE`, origem `current`, expiração estritamente posterior ao recheck e código do claim associado à fonte; um histórico nunca sustenta oferta atual.
- **Histórico interpretativo:** pode continuar apenas como contexto sintético; revogação, pausa, rascunho ou citação corrigida bloqueiam a fonte. Nenhuma correspondência semântica é inferida.
- **Hostilidade estrutural:** campo inesperado, getter, valores cíclicos ou tipo inválido geram negação sem I/O nem chamada de getter.

## Bloqueios para consumidor real

A S0 deve ratificar e implementar versão de contrato de fontes comerciais e conhecimento, responsável editor/aprovador, fonte canônica/versionada por loja e finalidade, correções atestadas, autorização de conteúdo/modelo (LGPD), prova de validade e seleção de fragmentos minimizados. A saída F01 exige revisão **semântica** e recheck da fonte *na transação de publicação* pela S0 (Issue #11). A eventual integração Meta também depende de roteamento, opt-out e grants de envio; não transportar um grant de leitura para envio.

**Nenhum arquivo S0/Meta/Frontend/banco foi alterado. Sem uso de modelos, serviço real, merge, deploy ou permissão produtiva.**
