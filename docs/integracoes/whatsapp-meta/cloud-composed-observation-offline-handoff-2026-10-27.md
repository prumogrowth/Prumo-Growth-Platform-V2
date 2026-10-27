# Meta Cloud — composição offline dos leitores de webhooks assinados

**Data:** 27/10/2026. **Base verificada:** PR #33, commit `998496c51012ac039d382d97889c49749f2c4e4e`. **Branch:** `feat/meta-cloud-composed-observation-20261027`.

## Lacuna real e fronteiras pré-existentes

Os leitores aditivos de PRs #25, #28, #29, #31 e #33 processavam formas específicas do mesmo callback: seleções de botão/lista, reações, referências de mídia, mensagens `unsupported` e erros de status `failed`. O verificador `cloud-webhook-handoff.ts` já inspecionava **o lote completo** e produzia observações genéricas. Faltava, porém, uma composição auditável que apresentasse cada ocorrência original **uma única vez**, sem somar múltiplas visões do mesmo item nem perder os itens genéricos.

Esta implementação **não substitui** os módulos estreitos, não cria endpoint, não modifica `inbound.ts` e não muda os contratos S0 existentes.

## Implementação

Arquivo `integrations/whatsapp-meta/cloud-composed-observation-handoff.ts`. Export `inspectSignedMetaComposedWebhook(rawBody,signature,appSecret,trustedRoute,limits?)`.

- O adaptador cria **uma cópia** de `Uint8Array` antes de qualquer operação assíncrona, limitada por `maxBodyBytes`; valida o envelope com `inspectCloudWebhookForHandoff()`, usando HMAC do próprio código, escopo WABA/phone confiável, tamanho e contagem de eventos.
- Em seguida invoca **cinco leitores estreitos existentes**, sobre o mesmo snapshot, sem pular validações: `inspectSignedMetaSelections()` (botão/lista), `inspectSignedMetaReactions()`, `inspectSignedMetaMediaMetadata()`, `inspectSignedMetaUnsupportedMessages()` e `inspectSignedMetaFailedStatusErrors()`. Cada leitor realiza independentemente sua própria HMAC e conferência de escopo. Isso custa **seis verificações HMAC no total**. Escolha deliberada de segurança: não introduzir interface para ignorar autenticação em leitores existentes.
- Confere o `raw_sha256` de cada leitor, os IDs de mensagem, participante, timestamp, WABA, phone e **posição original completa** (`entry_index`, `change_index`, `array_kind`, `item_index`). Exige no máximo uma evidência especializada para cada posição.
- Exige correspondência explícita para espécies que têm leitor especializado: `button`, `interactive`, `reaction`, cinco mídias (`image`, `audio`, `video`, `document`, `sticker`), `unsupported` e `status=failed`. Um evento esperado sem evidência não é transformado silenciosamente em genérico. Colisões, lacunas e qualquer negação dos leitores causam **negação do lote inteiro**.
- Mantém os demais eventos autenticados pela fronteira genérica como `uninterpreted_inbound` ou `uninterpreted_status`, sem alegar semântica reconhecida. A ordem das ocorrências é a da inspeção genérica: mensagens de cada change, seguidas pelos statuses; cada índice preserva seu endereço original.
- Duplicatas do **conteúdo** ou do `wamid` permanecem ocorrências distintas, localizadas em posições diferentes; não há dedupe durable, replay control, fila, `exactly_once` ou efeito de negócio.
- Retorna `SIGNED_COMPOSED_NOT_DURABLE`, `occurrences`, `route_revision` e hash bruto. A evidência especializada contém dados potencialmente sensíveis: **não registrar em logs** nem enviar ao front.
- Os indicadores `ack_allowed`, `send_authorized`, `s0_write_authorized`, `retry_external`, `production_authorized`, `delivery_confirmed`, `case_transition_authorized`, `commercial_effect_authorized`, `consent_verified`, `deduplicated`, `exactly_once_guaranteed`, `provider_failure_effect_confirmed`, `definitive_failure_count_increment` e `automatic_retry_authorized` permanecem **todos falsos**. O sucesso da HMAC jamais prova persistência nem autoriza HTTP 200.

## Testes e auditoria

`cloud-composed-observation-handoff.test.ts`: **20 novos cenários sintéticos**, incluindo mistura de mensagens e statuses, preservação de tipos não interpretados, posições entre changes, um registro por ocorrência, duplicatas sem dedupe, malformed siblings, subleitores negando formas inválidas, spoof de escopo WABA/phone, HMAC adulterada, limites de lote, UTF-8 e mutação dos bytes após invocação.

`.github/workflows/meta-cloud-composed-observation-offline.yml`: verifica **20 testes novos** e **154 regressões focadas**, sem reexecutar WA39–68, sem qualquer rede externa nos testes. **O status do CI e o SHA final devem ser verificados antes de certificação.**

## Governança e pendências

- Esta composição é **laboratório/offline**. Não implementa roteador de produção, ingress durable, storage, consentimento, autorização de envio, download de mídia, ACK, classificação comercial, mapeamento S0 ou retries.
- **Nenhuma dependência adicional imediata da S0** para verificar a composição, mas todos os passos operacionais dependem dos contratos autoritativos e permissões S0; PRs candidatos #14 e #19 permanecem sem ratificação.
- A verificação HMAC múltipla aumenta custo computacional. Se a integração real exigir otimização, somente uma API interna com tipo de snapshot autenticado e escopo confiável, revisada separadamente e aprovada, poderá remover redundância **sem pular proteções**.
- O formato de leitores especializados é intencionalmente conservador. Eventos futuros ou campos Meta incompatíveis podem causar negação; cobertura de todos os tipos e efeitos `exactly_once` **não são alegados**.

Sem merge/deploy, Graph API real, credenciais reais, endpoint público, Supabase produtiva ou alterações em S0/S1.