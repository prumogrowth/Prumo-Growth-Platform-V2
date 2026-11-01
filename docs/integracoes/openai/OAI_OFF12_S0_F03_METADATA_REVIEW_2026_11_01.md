# OFF-12 — Porta de inspeção F03 de metadados S0, SEM autorização

Data: 01/11/2026. Frente: OpenAI. Estado: **candidata offline**, sem serviço F03 operacional.

## Fontes canônicas consultadas

- S0 [`s0_f03_history_manifest_local.py` @ `dc8554db2e625accbf95cf922fdff8446be56f00`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/dc8554db2e625accbf95cf922fdff8446be56f00/backend/s0_f03_history_manifest_local.py): `HistoryState.REVIEW_ONLY_NOT_FROZEN`, `count`, `case_count`, `metadata_sha256`. Inspeção apenas de metadados em PG descartável, sem garantia de completude multicases ou autorização de conteúdo. Isto não é contrato operacional para a F03.
- S0 [`s0_cfi01_f03_receipt_bridge_local.py` @ `7d3232f59aab35265c3aa7fb5ab5ab2f06d5d047`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/7d3232f59aab35265c3aa7fb5ab5ab2f06d5d047/backend/s0_cfi01_f03_receipt_bridge_local.py): `VERIFIED_CONTRACT_PENDING` é recheck de recibo de fechamento CFI-01, **não** grant F03; não confundir versão de ciclo físico com versão da ficha/caso.
- S0 [`s0_f03_field_application_local.py` @ `dc8554db2e625accbf95cf922fdff8446be56f00`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/dc8554db2e625accbf95cf922fdff8446be56f00/backend/s0_f03_field_application_local.py): `APPLIED_SYNTHETIC_ONLY` e `ALREADY_APPLIED_AUDIT_ONLY` **não** comprovam atualização real de ficha.
- OpenAI base OFF-11 [`4714ca50a27b9953a5da7c0389926643fa3d5231`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/commit/4714ca50a27b9953a5da7c0389926643fa3d5231), **724/724 testes** no [CI `41268914799`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41268914799).

## Incremento

- `e04_offline_lab/f03-s0-metadata-review-lab.mjs`: `reviewF03S0Metadata(input)`, função pura e sem SDK, acesso físico, SQL ou modelo.
- `e04_offline_lab/tests/f03-s0-metadata-review-lab.test.mjs`: 50 testes negativos/positivos para escopo, versions/cutoff binding, getters, digests, replay de snapshot sintético e aplicações apenas sintéticas.
- Forma de entrada `prumo.openai.f03-s0-review/0.1-lab`: **fixture interna, não contrato S0 ratificado**. `request/before/after` guardam marcadores declarados pelo laboratório de `storeRef/caseRef/closureRef/cycleVersion/snapshotSha256`. Esses marcadores não provam autenticidade; `inspection` simula somente os **campos de resultado** da inspeção S0; `application` simula um estado de aplicação opcional.

## Invariantes

1. `VERIFIED_CONTRACT_PENDING` + `REVIEW_ONLY_NOT_FROZEN` pode gerar **`LAB_METADATA_REVIEW_ONLY`**, jamais `READY`, `HISTORY_COMPLETE`, autorização de gerar prompt F03 ou abrir a ficha.
2. `APPLIED_SYNTHETIC_ONLY` e `ALREADY_APPLIED_AUDIT_ONLY` retornam `LAB_REVIEW_ONLY_SYNTHETIC_APPLICATION`, jamais aplicação operacional.
3. Mudança de loja/caso/fechamento é `DENIED` antes de expor metadados; mudança de versão de ciclo/digest é `STALE`; indisponibilidade, histórico incompleto, ausência de fonte ou contradição levam a bloqueio/revisão.
4. Toda saída mantém `s0SourceAuthenticated=false`, `historyComplete=false`, `mediaCoverageAttested=false`, `crossCaseIdentityAttested=false`, `modelContentAuthorized=false`, `modelInvocationAuthorized=false`, `fieldApplicationAuthorized=false`, `commercialTransitionAuthorized=false`, `sendAuthorized=false`, `productionAuthorized=false`, `requiresCanonicalS0Contract=true`. Nada de PII, digest, `leadRef`, conteúdo, recibo ou prova técnica vaza na projeção.
5. Os testes não convertem fixture em assinatura/identidade real, não acessam provedor Meta/Banco/OpenAI, não criam tabela, não alteram roteamento ou permissão S0.

## Dependências externas ainda necessárias

**[#5](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/5):** S0 deve atestar identidade multicases, cutoff global, completude e conteúdo minimizado autorizado, incluídas mídias/ausências. **[#6](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/6):** catálogo canônico de campos, regras semânticas, versões distintas e aplicação atômica com recheck exclusivamente S0. Sem aceite S0 nem revisão independente de contrato não há consumidor produtivo da F03.

Não executar merge, deploy, dados reais, escrita de ficha ou chamada a modelos. A OFF-12 é um guarda negativo para impedir promoção indevida de evidência intermediária.

Acompanhar a sequência geral em [`OAI_ROTEIRO_PROGRESSO_2026_11_01.md`](./OAI_ROTEIRO_PROGRESSO_2026_11_01.md).
