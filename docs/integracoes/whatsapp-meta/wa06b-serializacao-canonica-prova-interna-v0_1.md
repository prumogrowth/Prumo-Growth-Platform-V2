# WA-06B — bytes canônicos candidatos para prova interna Meta → S0

**Data:** 18/10/2026. **Estado: [P/V local].** Engenharia de interface: bytes determinísticos e testes unitários locais. **Não** é autenticação de serviço, esquema de banco, implementação ACID, serviço hospedado, credencial, assinatura real, autorização de ACK ou aprovação de DEC-WA-06.

## 1. Incremento efetivamente realizado

Depois da [WA-06A](wa06a-contrato-identidade-servico-replay-s0-v0_1.md), um dos riscos concretos era construir uma prova de integridade com serialização ambígua ou campos esquecidos. Na WA-05D-AUD1, `scope_sha256` público recalculável não autenticava a origem do envelope. A MAC fictícia posterior usa `JSON.stringify` sem protocolo de bytes versionado, e não tem `purpose/audience/request_ref/nonce_ref/key_epoch`.

Dois arquivos novos no PR #2:
- `integrations/whatsapp-meta/internal-proof-wire-v1.ts`: `canonicalizeInternalProofV1(claims,candidate)`, função **pura e síncrona**, produz bytes iguais para entradas válidas idênticas; rejeita formatos inesperados, campos extras, getters, arrays com buracos, versões erradas, IDs e posições malformados. Não assina nem verifica MAC e não chama serviços.
- `integrations/whatsapp-meta/internal-proof-wire-v1.test.ts`: `WIRE-01..15`, testes de campo vinculado, comprimento-prefixo, scope, array, payload hash, posições de callbacks, HMAC de **laboratório apenas no teste**, rejeição e erro sanitizado.

**Importante:** este encoder é um **candidato independente** da assinatura fictícia WA-05D; não modifica `FakePrivilegedS0Ingress`, não autoriza adaptar `createFakeS0ServiceProof` para produção, não transforma `S0ReceiptFixture` em recibo de commit, não toca C02/C07 e não altera o contador da suíte anterior.

## 2. Protocolo candidato [P], sem interoperabilidade homologada

Versões:
- `proof_version = prumo.meta-s0.proof.v1-candidate`
- `canonicalization_version = prumo.meta-s0.binlen.v1-candidate`
- `candidate.contract_version = meta-s0-handoff.v0.1-proposed`

Serialização binária: prefixo literal ASCII **`PRUMO:WA06B:PROOF:V1\0`**, seguido de **um campo por vez**, cada campo representado por `uint32` big-endian de comprimento em bytes e o valor convertido para texto UTF-8. Não usa concatenação simples de strings, propriedade de objeto em ordem dinâmica nem `JSON.stringify` do envelope. Números são inteiros JavaScript seguros escritos em decimal; flags são literais `false`. Referências técnicas aceitas são ASCII estrito para bloquear confusão Unicode; identificador `wamid` mantém `=` e caracteres opacos permitidos no contrato anterior.

Ordem fixa dos **21 campos de cabeçalho**: `proof_version`, `canonicalization_version`, `service_ref`, `request_ref`, `nonce_ref`, `key_epoch`, `purpose`, `audience`, `issued_at_ms`, `expires_at_ms`, `contract_version`, `batch_ref`, `route_ref`, `route_revision`, `app_ref`, `protected_payload_ref`, `payload_sha256`, `scope_sha256`, `event_count`, `ack_allowed`, `production_authorized`.

Após essa sequência, para cada ocorrência na **ordem original do lote**: `entry_index`, `change_index`, `array_kind`, `item_index`, `event_kind`, `app_ref`, `concessionaria_id`, `canal_id`, `waba_id`, `phone_number_id`, `provider_message_id`, `provider_timestamp`, `provider_kind`. Rejeitar posições duplicadas; `statuses[].id` permanece referência da mensagem, **nunca** identidade de ocorrência. Vários canais da mesma App são preservados e depois exigem vinculação/ACL real na S0.

`purpose` aceito: `meta_s0.ingest`. `audience` aceita: `s0_internal_ingress`. `issued_at_ms < expires_at_ms`, sem declarar frescor ou proteção contra replay real. `nonce_ref` é apenas campo serializado: consumo único em banco e revalidação temporal da identidade ainda dependem do serviço S0.

### Vetor de referência auditável

A fixture `fixture()` do teste `WIRE-01` define **exatamente** os campos (incluindo o único callback `delivered`, `wamid.ID=`, hashes sintéticos de 64 `a` e 64 `b`, números `1000/2000`). Com a codificação acima, o SHA-256 dos bytes produzidos é:

`c94993710cfc4a90d41314c89026385e7cbd446753b2fa7d0ec0cc7f65083209`.

**Este hash é vetor de consistência, não assinatura, token ou prova de origem.** Antes de eventual uso no gateway S0 real, exigir teste independente de interoperabilidade em outro runtime; aprovar versão/canonicidade, algoritmo de assinatura e origem do principal sob DEC-WA-06.

## 3. Evidências locais verificadas

Ambiente descartável local: Node.js **22.16.0**, TypeScript **5.8.3**.

- `node --experimental-strip-types --test internal-proof-wire-v1.test.ts` executado: **15/15 PASS**, WIRE-01..15.
- `tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --allowImportingTsExtensions --skipLibCheck --esModuleInterop --types node internal-proof-wire-v1.ts internal-proof-wire-v1.test.ts`: **PASS**. Para resolver o import de tipo, usou-se espelho **local temporário** da interface `S0HandoffCandidate` de WA-05C, sem importar os demais módulos. **Não é typecheck global da branch inteira.**
- Comparação do hash de blob Git do código efetivamente testado com a branch remota: encoder `1dc5fddd1893d69151043a1a5ea70fcc03a0c34f`; testes `773f1ccc950497ea787d04ab26b789d2403aef54`. **Coincidem.**
- **Nenhum CI remoto, Supabase local gerenciado, PostgreSQL ou Meta real executado nesta WA-06B.** Os 358 testes anteriores são histórico da WA-05D-AUD1, não foram reexecutados e **não** devem ser somados como suíte integrada validada no HEAD atual.

## 4. O que ainda deve ser comprovado antes de confiar nos bytes

A S0 precisa autenticar principal de workload **fora do JSON** e conferir se `service_ref` corresponde a essa identidade; gerenciar chave e rotação/negação; validar propósito e audiência, clock e nonce persistente; autenticar e revalidar todos os vínculos App→WABA/emissor/canal/loja **na mesma transação ACID** que armazena corpo integral protegido, batch, ocorrência própria e tarefa; publicar recibo autoritativo recuperável em `COMMIT_UNKNOWN`.

O encoder **não confere** que o `payload_sha256` informado de fato corresponde aos bytes Meta, nem recalcula `scope_sha256`; deve ocorrer em outras camadas confiáveis. `status` duplicado por `wamid` não é dedupe autorizada. A prova HMAC válida de laboratório **não** comprova identidade de produção. DEC-WA-06 define segredo, replay, recuperação, retenção, continuidade e política 200/503/quarentena; DEC-WA-04 define ambiente definitivo. A titularidade Meta por loja DEC-WA-05 e organização Prumo D-ORG-01 não se confundem com o gate humano S1-002/I1 do PR #5 Draft.

**Próximo gate WA-06C candidato:** revisão cruzada S0 dos bytes e 1 vetor independente em outro runtime, depois planejamento de teste **transacional PostgreSQL descartável** do nonce/escopo/commit/recibo com owner mínimo — sem converter o protótipo S0-037F em serviço real ou criar novo simulador `Map`.

**Restrições:** PR #1/#2/#5 permanecem Draft; sem merge, deploy, DDL Supabase hospedado, substituição da POC `whatsapp-webhook-sandbox` de concessionária de demonstração, token comercial, Graph, número real, custos, recursos pagos ou ACK HTTP 200. Aprovação específica ainda exigida para qualquer execução real.
