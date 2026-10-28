# Meta Cloud — pré-validação técnica de distribuição por canais (offline)

**Data:** 28/10/2026. **Base:** PR #44 (auditoria somente leitura S0), SHA `21bf598a58163f9343785ded1b2c16ee8d17b55d`. **Branch:** `feat/meta-cloud-batch-scope-preflight-20261028`.

## Motivação

O PR #44 comprovou uma **diferença de contrato**, não uma falha operacional: o handoff sintético S0 aceita, sob a mesma App/assinatura, um POST com duas WABAs distintas resolvidas individualmente pelo registry; o compositor novo opera com `trustedRoute` singular WABA/phone e nega o lote misto. Os contratos S0 META-S0-ACK-03 e DISPATCH-01/02 do PR #14 **não estão ratificados**. Dividir um POST em vários ACKs ou selecionar silenciosamente uma WABA seria erro.

Entretanto, `inspectRoutedMetaPost()` (WA-04B), já existente na frente Meta, consegue autenticar o corpo completo sob a rota da App e verificar cada entrada contra o registry privilegiado. Aproveitamos essa implementação, em vez de criar parser HMAC ou roteador concorrente.

## Escopo implementado

Arquivo novo `integrations/whatsapp-meta/cloud-batch-scope-preflight.ts`, export `inspectSignedMetaBatchChannelScope(request,ports)`.

- Snapshot de bytes, assinatura e rota de App antes do primeiro await, tamanho de corpo 256 KiB; funções confiadas de registry, segredo e relógio preservadas na invocação.
- Reuso direto de `inspectRoutedMetaPost()`, incluindo HMAC do corpo inteiro com segredo resolvido pela **App selecionada pela rota confiada**, verificação de escopo entre App/Concessionária/Canal/WABA/Phone, revisão/expiração/revogação e recheck final.
- Exige 1–100 ocorrências autênticas; rejeita inteiro se existe uma posição repetida, endereço inválido, campo de escopo incongruente ou canal sem vínculo. **Nenhum** evento é descartado para produzir uma análise parcial.
- Agrupa somente contagens de mensagens e status por `(app_ref,concessionaria_id,canal_id,waba_id,phone_number_id)`, na ordem de primeira ocorrência. **Não retorna** wamids, números de clientes, conteúdo, assinaturas ou tokens. O `raw_sha256` representa o POST físico completo, não recibo S0 nem fonte autorizativa.
- Distinção exclusivamente diagnóstica:
  - `SIGNED_SINGLE_CHANNEL_TECHNICAL`: um único canal foi autenticado tecnicamente; **não** prova elegibilidade de S0/produção.
  - `SIGNED_MULTI_CHANNEL_UNRATIFIED`: várias ligações técnicas de canais de uma App passaram na inspeção; **não** ratifica processamento, particionamento, ingestão durável, ACK ou consentimento.
  - `DENIED`: entrada, assinatura/roteamento ou integridade insuficientes; contagens zero, nenhum canal e hash nulo.
- Flags fixas `false`: `ack_allowed`, `partial_ack_allowed`, `send_authorized`, `s0_write_authorized`, `production_authorized`, `service_identity_verified`, `m2m_verified`, `persisted`, `durable_receipt_verified`, `batch_partition_authorized`, `channel_policy_ratified`, `automatic_retry_authorized`, `commercial_effect_authorized`, `delivery_confirmed`, `consent_verified`, `deduplicated`.

Essa leitura não é o compositor de mensagem do PR #43. **Não amplia** o contrato vigente de `inspectSignedMetaComposedWebhook()` para múltiplas WABAs. Qualquer futura composição multicanais precisará de autorização formal da unidade de ingress/ACK, identidade técnica S0, garantias de retenção e validação de cobertura dos leitores de eventos.

## Provas offline

`cloud-batch-scope-preflight.test.ts`: **24 novos cenários** com dados sintéticos para um canal, duas WABAs da mesma App, dois phones da mesma WABA, contagem de mensagens/status, posicionamento sem dedupe, hash do POST, HMAC errada/ausente, cross-App, canal/phone inexistente, revogação de App e canal, revisão obsoleta, segredo ausente, sibling malformado, isolamento dos bytes/rota sob mutação, limites de body/eventos, privacidade da saída e revogação durante rechecks.

Workflow `.github/workflows/meta-cloud-batch-scope-preflight-offline.yml`: 24 novos + **286 regressões preexistentes**, abrangendo 14 testes cruzados S0, 24 handoff S0 antigo e 248 Meta prévios. **Total esperado 310**. Exigir CI **SUCCESS no HEAD final**; não alegar benchmark de latência ou certificação de PostgreSQL real.

## Registro para S0 (somente leitura)

**Nenhum arquivo S0/S1 foi modificado ou deve ser modificado por este PR.**

- **A1 — decisão contratual ainda pendente:** admitir ou recusar lote físico multicanais sob uma única App. Se admitido, a S0 deverá definir execução/registro atômico de todas as ocorrências, revalidação transacional do registry e ACK condicionado a commit íntegro do **lote físico**. Um `SIGNED_MULTI_CHANNEL_UNRATIFIED` não é autorização.
- **A2 — se decidir por ingress de canal único:** manter rejeição integral de lotes heterogêneos em qualquer caminho que possa dar ACK; não converter esse preflight em repartição/ACK por canal.
- **A3 — decisões já registradas:** C1–C7 do PR #14 (reserva, M2M, ACK, locks e recibos); T1–T6 do PR #19 (fonte real de template, política e vínculo). Não há nova solicitação imediata à S0.

### Escopo negativo

Sem alteração na S0, S1, schemas, migrations, IAM, Supabase, backend, PRs anteriores, branches de terceiros, HTTP, webhook público, Meta Graph, autorização de envio, retry, ACK, execução assíncrona, persistência ou deploy. Todos os dados de teste são artificiais.
