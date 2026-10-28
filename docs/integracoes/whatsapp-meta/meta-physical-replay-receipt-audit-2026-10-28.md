# Meta Cloud — auditoria de repetição física, reordenação e recibo alegado

**Data:** 28/10/2026. **Base:** PR #45 (`2de0003a8031056d73da7477f94fc2c8fc398c48`). **Branch:** `audit/meta-physical-replay-receipt-20261028`. **Natureza:** somente testes offline e inspeção documental da S0, sem autorizar envio ou HTTP ACK.

## Escopo auditado e fontes

1. `cloud-batch-scope-preflight.ts` (PR #45) autentica o **POST físico inteiro**, já suportando uma App com vários canais, sem ratificar o ingresso produtivo multicanais.
2. `s0-handoff-contract.ts` (fixture WA-05C anterior) produz apenas um candidato, com `payload_sha256`, `scope_sha256` e contadores; `reviewS0ReceiptFixture()` só oferece `STRUCTURE_MATCHES_BUT_UNVERIFIED`, nunca ACK.
3. `durable-receipt.ts` (helper histórico WA-01B, frente Meta) produz uma estrutura `{status:200,action:'ACK'}` quando recebe objeto que **apenas aparenta** ser `COMMITTED` com contadores completos. Não há verificação de origem da alegação nem vínculo criptográfico. O próprio código documenta que deveria receber somente um recibo de uma **porta interna autenticada e durável**, que não foi implantada. **Não é endpoint público atual nem prova de falha operacional**, mas é um risco concreto de mau uso futuro.
4. O PR S0 [#14](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/14) (META-S0-ACK-03, contrato candidato não ratificado) já exige duas provas independentes (HMAC externo Meta e M2M interno), lote completo, commit durável, readback/replay e política HTTP. O [PR #19](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/19) continua sem fonte autenticada de catálogo em produção. Ambos foram consultados apenas em leitura; não foram modificados.

## Implementação nova, somente na frente Meta

`integrations/whatsapp-meta/cloud-physical-replay-receipt-audit.ts` fornece **dois caminhos somente diagnósticos**.

### A. `compareSignedMetaPhysicalDeliveries(previous,current,ports)`

- Copia **ambas** as solicitações e rotas **antes do primeiro await** e passa cada uma separadamente por `inspectSignedMetaBatchChannelScope()`. Cada callback recebe sua própria inspeção HMAC, rota/clock/registry e negação total se algum item não corresponder.
- `EXACT_SIGNED_RAW_BYTES_UNVERIFIED`: hashes físicos idênticos e matriz de canais/revisão/rota coincidente. **Não prova recepção duplicada, commit ou deduplicação durável**.
- `DIFFERENT_SIGNED_RAW_BYTES_UNVERIFIED`: corpo físico diferente sob a mesma distribuição de canais, **sem alegar que as mensagens lógicas são equivalentes**. A simples reordenação de `entry[]`, de `messages[]` ou de serialização JSON produz bytes distintos.
- `SIGNED_SCOPE_CHANGED_UNVERIFIED`: há diferença de escopo/revisão/rota/canais. Não fazer merge de proveniências ou sugerir replay entre clientes.
- `DENIED`: pelo menos um input/assinatura/escopo é inválido. Não vazar hash parcial da outra solicitação.
- Nenhum armazenamento, cursor, epoch ou estado idempotente é criado. A leitura é comparação de **duas evidências físicas**, não tentativa de recuperar recibo após queda.

### B. `reviewAllegedS0ReceiptWithoutAck(signed,candidate,allegedReceipt,trustedRoute)`

- Os três objetos de entrada permanecem **alegações não autenticadas**, mesmo quando tecnicamente bem-formados. A rota e a revisão explícitas devem coincidir com os dados apresentados na fixture S0; isso é conferência estrutural, não prova de origem.
- Compara `raw_sha256` ao `payload_sha256`, quantidade total, posições sem duplicação e **contadores por App/Concessionária/Canal/WABA/Phone e tipo (mensagem/status)**. Uma contagem total igual não mascara troca de canal.
- Reutiliza `reviewS0ReceiptFixture()` **sem modificá-la** para conferir campos do recibo alegado. Ausência de resposta não é interpretada como rollback; conflito, quarentena, recibo parcial, rota/revisão/digest incompatíveis falham fechados.
- Um recibo `COMMITTED` estruturalmente perfeito retorna **`CLAIMED_RECEIPT_SHAPE_ONLY_UNVERIFIED`**, e `durable_receipt_verified=false`, `commit_verified=false`, `ack_allowed=false`, `http_response_authorized=false`.
- O helper histórico `decideBatchAck()` **não é chamado pela função nova**. Sua dependência futura de um serviço privilegiado autenticado exige revisão específica antes de utilização em HTTP.

**Segurança:** nenhuma das duas funções concede reenvio automático, direito de envio, ACK parcial/integral, S0 write, ratificação multicanais, consentimento, confirmação de entrega ou efeito comercial. SHA de corpo é identificador técnico sensível; não exibir em frontend/telemetria pública.

## Evidência reproduzível

`cloud-physical-replay-receipt-audit.test.ts`: **29 testes novos**, cobrindo:

- Mesmo POST físico, reordenação de entries/messages, variação whitespace, conteúdo alterado com mesmos contadores, mudança de escopo, payload HMAC adulterado, revogação implícita por rota inválida, mutação de bytes e rota após chamada.
- Queda/perda de resposta (recibo ausente), recibo fabricado com `COMMITTED`, troca de canal sob contagens idênticas, índices duplicados, quarentena, batch_ref divergente, contadores conflitantes, `ALREADY_ACCEPTED`, 100 eventos e alteração de route_ref/revisão.
- Um teste documenta a **resposta sintética 200/ACK do helper legado mediante forma fabricada**, sem fazer qualquer requisição HTTP. É prova de insuficiência de autorização por forma, não ataque em endpoint real.

Workflow `.github/workflows/meta-physical-replay-receipt-offline.yml`: **29 novos + 310 regressões focadas anteriores = 339 testes**. Exigir `SUCCESS` no **HEAD final**, sem extrapolar para testes integrais S0/PG, hardware ou produção.

## Encaminhamentos para equipes e dependências

| Código | Proprietário | Natureza | Encaminhamento futuro |
|---|---|---|---|
| M-ACK-01 | Meta/Infra | Risco de uso indevido **confirmado** no helper antigo | Não conectar `decideBatchAck()` diretamente ao endpoint HTTP. Substituir ou enclausurar sob autenticação M2M, porta S0 durável e recibo verificável, sujeito à política autorizada |
| S0-ACK-03 | S0/Meta/Infra | **Pendente já documentado**, sem defeito novo provado na S0 | Ratificar porta M2M, replay/recibo pós-commit, tratamento de resposta perdida, política HTTP e restrição de chamadas à Meta |
| S0-A1 | S0/Meta | Divergência de contrato do PR #44/45 | Ratificar permitir/recusar lotes físicos multicanais com atomicidade do POST; preflight continua sem efeito operacional |
| S0-CATALOG-05 | S0/Meta | Pendente anterior, não relacionado ao ACK | Fonte autenticada/atual do catálogo Meta continua necessária para envio produtivo |

**Nenhuma intervenção imediata da S0 exigida para continuar a frente Meta offline.** Os PRs S0 #14/#19 e I85 permanecem livres de alterações desta tarefa.

**Escopo negativo:** nenhum commit, branch, PR, SQL, schema, migration, ACL, banco, S0/S1 ou fixture histórica alterado; somente artefatos novos em `integrations/whatsapp-meta/`, `.github/workflows/` e `docs/integracoes/whatsapp-meta/`. Nenhum Graph, segredo real, HTTP 200/ACK, fila real, envio, Supabase hospedado, merge ou deploy.
