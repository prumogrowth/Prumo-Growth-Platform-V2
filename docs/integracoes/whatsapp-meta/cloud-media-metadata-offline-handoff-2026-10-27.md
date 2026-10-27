# WhatsApp/Meta — mídia recebida: apenas referências técnicas, sem download

**Data:** 27/10/2026. **Branch:** `feat/meta-cloud-media-metadata-20261027`. **Base:** PR #28 (`feat/meta-cloud-reaction-handoff-20261027`, SHA `5e7e08925949444600790b656cd63818bd75b050`). Escopo estritamente offline e aditivo.

## Lacuna e fontes

`inbound.ts` e `cloud-webhook-handoff.ts` autenticam HMAC, validam a rota WABA/phone e identificam mensagens recebidas, mas não extraem referência de mídia. As extensões anteriores cobrem seleção interativa (PR #25) e reações (PR #28), não mídia.

A coleção oficial Meta/WhatsApp Business Platform descreve `Media Object` com `id`, `mime_type`, `sha256`, `caption` e `filename` (para documentos):
- [Meta — Media Object](https://www.postman.com/meta/whatsapp-business-platform/folder/t8iajsk/media-object)
- [Exemplo complementar — Messages Object (coleção comunitária, não oficial)](https://www.postman.com/postman/brewing-postman-flows/folder/il0b0ts/messages-object)
- [Meta — webhook Received Media Message with Sticker](https://www.postman.com/meta/whatsapp-business-platform/request/g1ktufl/received-media-message-with-sticker)

Essas referências orientam apenas o shape experimental, sem certificar entrega operacional, versões da Graph API ou suporte universal a todos os formatos.

## Implementação

`integrations/whatsapp-meta/cloud-media-metadata-handoff.ts` exporta `inspectSignedMetaMediaMetadata()`.

- Reusa **sem duplicação** `inspectCloudWebhookForHandoff()` para HMAC do corpo bruto, limites de lote e autenticação de escopo WABA/phone; não faz nova verificação HMAC. Extrai dados somente do mesmo snapshot imutável validado.
- Identifica `image`, `audio`, `video`, `document` e `sticker`. Preserva posição exata, identificador da mensagem recebida, participante, timestamp, WABA/phone e o identificador opaco de mídia.
- Capta metadados **declarados**, não verificados: MIME, SHA-256, legenda de imagem/vídeo/documento, nome de arquivo de documento, indicador de voice em áudio e animated em figurinha.
- Metadados opcionais ausentes ficam **`null`**, nunca são inventados. Mídia observada **não contém download URL, bytes, tamanho do arquivo, conteúdo analisado ou hash recalculado**.
- Usa gramáticas conservadoras para ID de mídia, MIME e representação textual de checksum. A mera adequação à gramática **não valida conteúdo, tipo real, integridade ou segurança do arquivo**.
- Restringe campos do objeto de mídia aos previstos para cada tipo. URLs, bytes, flags de autorização e propriedades inesperadas provocam negativa integral, sem tentativas de download. Outras espécies de mensagem não são transformadas em mídias. Um evento inválido pode negar o lote inteiro.
- Devolve `SIGNED_MEDIA_REFERENCES_NOT_DURABLE`, com indicadores invariavelmente falsos: `ack_allowed`, `send_authorized`, `s0_write_authorized`, `retry_external`, `production_authorized`, `delivery_confirmed`, `case_transition_authorized`, `commercial_effect_authorized`, `consent_verified`, `deduplicated`, `media_download_authorized`, `media_downloaded`, `media_content_verified`, `mime_verified`, `checksum_verified` e `malware_scanned`.

Dados de mídia, hashes, títulos, legendas e números de participantes podem ser sensíveis. **Não armazenar em logs nem usar para tomar decisões comerciais.**

## Testes e certificação

`integrations/whatsapp-meta/cloud-media-metadata-handoff.test.ts`: 20 cenários novos, inteiramente fictícios, cobrindo cinco tipos, campos opcionais, falsificação, assinatura errada, escopo cruzado, limites, duplicatas, bytes alterados após invocação e negação atômica.

`.github/workflows/meta-cloud-media-metadata-offline.yml`: Node 22 `--experimental-strip-types`, 20 provas novas e 100 regressões focadas (`cloud-reaction`, `cloud-list`, `cloud-button`, `cloud-webhook`, `inbound`, `routed-webhook`). Não recria WA39–68, nem PRs #14/#19.

**Estado do CI:** resultado e SHA devem ser confirmados nas Actions e PR correspondentes. Não atribuir certificação ao mero commit ou escrita desta documentação.

## Governança / integração futura

Nenhuma solicitação S0 nova imediata. A interpretação de arquivos reais, download, retenção, acesso, antivírus, política de dados, consentimento e associação a cliente/concessionária exigirá arquitetura e permissão autoritativas da S0, mais a política de privacidade e homologação aplicáveis. A HMAC válida não autoriza ACK 200 nem GET da Graph API.

Sem token real, GET/POST Graph, mídia real, endpoint, Supabase, S0/S1, fila produtiva, merge, deploy ou autorização de processamento comercial.
