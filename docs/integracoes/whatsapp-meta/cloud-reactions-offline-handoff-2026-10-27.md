# Meta Cloud API — reação recebida, adição e retirada (laboratório offline)

**Data:** 27/10/2026. **Base:** PR #25, branch `feat/meta-cloud-list-replies-20261027`; nova branch independente `feat/meta-cloud-reaction-handoff-20261027`.

## Lacuna comprovada

`inbound.ts` já reconhece uma mensagem de tipo `reaction` como evento recebido genérico; `cloud-webhook-handoff.ts` verifica o corpo bruto com HMAC, valida a rota confiável WABA/phone e delimita posições. Os exports do PR #25 tratam botões e listas, **não** os campos `reaction.message_id` e `reaction.emoji`.

Referências públicas:
- Meta, coleção oficial da WhatsApp Business Platform: [Received Message with Reaction](https://www.postman.com/meta/whatsapp-business-platform/request/s9dccb2/received-message-with-reaction).
- Meta, [Webhooks](https://www.postman.com/meta/whatsapp-business-platform/folder/lboq68h/webhooks).
- Referência estrutural de `ReactionMessage`: [message_id e emoji](https://apis.io/json-structure/whatsapp/whatsapp-cloud-api-reaction-message-structure/), com string vazia usada como marcador de retirada.

## Entrega e semântica

`integrations/whatsapp-meta/cloud-reaction-handoff.ts` exporta `inspectSignedMetaReactions()`:

- Reusa **sem duplicação** `inspectCloudWebhookForHandoff()` para verificação HMAC, limite de bytes/eventos, escopo WABA/phone e verificação de todo o lote; não implementa endpoint ou novo mecanismo de autorização.
- Extrai `provider_message_id` **da mensagem de reação**, separado do `target_provider_message_id` reclamado pelo callback; preserva `participant_identifier`, timestamp, WABA, phone, índice e hash dos bytes brutos.
- `emoji!==''` é `add_candidate`; `emoji==='' ` é `remove_candidate`. Ambas são **observações**, não a prova de reação aplicada ou retirada anterior.
- Limita `reaction` a duas propriedades `message_id` e `emoji`; alvo precisa seguir a gramática conservadora de `wamid`; aceita uma string Unicode bem formada até 32 pontos de código, mas **não certifica** o suporte do emoji pela Meta.
- Falha sem retorno parcial se uma reação é malformada ou um outro item do lote causa negação pela verificação existente; não descarta duplicatas e não converte texto, botões ou status em reações.
- Resultado `SIGNED_REACTIONS_NOT_DURABLE` traz sempre `ack_allowed=false`, `send_authorized=false`, `s0_write_authorized=false`, `retry_external=false`, `production_authorized=false`, `delivery_confirmed=false`, `case_transition_authorized=false`, `commercial_effect_authorized=false`, `consent_verified=false`, `deduplicated=false`, `target_message_correlated=false` e `reaction_effect_confirmed=false`.

Os IDs, números e emojis observados são potencialmente sensíveis; **não expor em logs**. Assinatura íntegra não autoriza ACK HTTP 200, persistência ou ação comercial.

## Testes e restrições

`cloud-reaction-handoff.test.ts` inclui **16 cenários sintéticos** com HMAC, distinção entre identificador de evento e alvo, adição/remoção, Unicode, lote misto e parcialmente inválido, duplicação, limite de tamanho/eventos e mutação dos bytes após a invocação. CI em `.github/workflows/meta-cloud-reactions-offline.yml` executa os testes novos e apenas regressões focadas do PR #25, botão, HMAC e roteamento.

**Não faz:** integração Graph GET/POST, downloads, segredos reais, Supabase, ACK, merge, deploy, S0/S1, idempotência comercial ou conciliação de status.

## Dependências

Não surgiu contrato S0 novo para esta leitura estritamente técnica. Para refletir adição/retirada de reação numa interface futura, a S0 deverá primeiro reconhecer o alvo, canal/tenant, mensagem e tentativa e estabelecer idempotência/permissões. Isso não equivale a consentimento, escolha válida em lista ou ratificação dos contratos candidatos PRs #14/#19. Não iniciar nova solicitação de S0 sem necessidade operacional concreta.

**Certificação:** preencher exclusivamente após observar GitHub Actions SUCCESS associado ao SHA exato; nunca usar a existência do arquivo como prova.
