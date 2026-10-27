# F02 → S0/F03 — mapa de produtores das quatro provas (H01)
**Data:** 27/10/2026. **Fonte:** retorno da auditoria S0 `aux/f02-s0-auditoria-integracao-20261027` `7c282df…`, G01–G06 parcialmente atendidos, G07 pendente.

## Finalidade
Identificar os **produtores de laboratório existentes**, evitando reconstruir código e evitando alegar que os quatro hashes `ClaimedS0Evidence` já são provas verificadas pela S0. Este mapa não é transporte, decisão de ratificação, implantação ou pedido enviado à F03; apenas prepara a resposta técnica H01 solicitada pela auditoria.

| Campo F02 | Produtor existente em E04 | Prova que continua faltando |
|---|---|---|
| `f03_receipt_sha256` | `S0F03LocalHistoryManifestBridge.inspect` e `S0F03LocalEvidenceReviewBridge.inspect`, apoiados em recibo CFI | Definir recibo F03 **final e canônico**, versões distintas de caso/ficha/atribuição/catálogo, fonte minimizada e cutoff |
| `c08_local_witness_sha256` | `S0F02LocalLegacyCancellationWitness.inspect_and_seal` | Releitura confiável da testemunha/HMAC na transação S0; provar apenas cancelamento **local**, não externo Meta |
| `origin_ledger_sha256` | `S0F02LegacyObservedOriginBridge.inspect` | Fonte, criação efetiva, versão e completude do AFTER ledger sob cutoff |
| `human_intent_sha256` | `S0F02LocalPostHumanIntentStore.record` | Ato gerencial real G04, com ator/escopo/validade/revogação, **separado da intenção sintética** |

**Passagem humana:** o laboratório oferece `S0LocalClosureStore.capture` e `S0CFI01F03ReceiptBridgeLocal.capture`. Isso não identifica sozinho o evento/handover físico completo F01/F03: é necessário ratificar causalidade, ordem e recibo final.

## Contrato de integração para futura avaliação

`docs/contracts/OAI_E04_F02_S0_MAPA_QUATRO_PROVAS_V1.json` registra para cada prova o arquivo, método e os campos ainda necessários. Ele não serializa texto de cliente, IDs reais, tokens nem credenciais. O mapeamento de produtores prova apenas presença de código; o futuro adapter S0 deverá revalidar **de fonte autorizada** identificador, versão, canonicalização, hash/HMAC, escopo, cutoff, completude, revisão e revogação. Em ausência de evidência, responder com recheck/negativa; nunca converter hash alegado em ratificação ou direito de envio.

**Pendência efetiva H01:** F01/F03/S0 devem escolher recibos/versões e contrato de passagem; F02 mantém a interface candidata `ClaimedS0Evidence` e pode adicionar testes de inconsistência, sem criar novo produtor. Estado de referência: G03 parcialmente atendido, G07 pendente; G01/G02/G04/G05/G06 também não ratificados.

A arquitetura-alvo de hospedagem foi decidida separadamente em `docs/decisoes/ADR_20261027_BACKEND_SUPABASE_OPENAI_DIRETO.md`. Isso não altera a natureza offline das provas E04 nem autoriza migração hospedada.
