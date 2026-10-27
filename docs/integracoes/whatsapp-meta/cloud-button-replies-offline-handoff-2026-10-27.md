# WhatsApp/Meta — respostas técnicas a botões: handoff offline

**27/10/2026.** Frente independente Cloud API, branch `feat/meta-cloud-button-replies-20261027`, derivada da PR #22. **Não altera S0, S1, PRs #14/#19 nem outras branches.** Sem tokens produtivos, Graph, webhook público, ACK, Supabase, merge ou deploy.

## Lacuna concreta

A frente possui o builder de templates com QUICK_REPLY (PR #15), leitor de webhook com HMAC bruto e validação por rota (PR #8), e utilitários de templates (PRs #21/22). Entretanto, `inbound.ts` e `cloud-webhook-handoff.ts` devolvem apenas a identidade/tipo das mensagens recebidas, **sem extrair a escolha feita ao clicar num botão**. Isso impede testes realistas de entrega do evento técnico para o futuro sistema S0.

A Meta diferencia envio de templates com botões QUICK_REPLY e mensagens interativas com botões. Fontes de referência:
- [Meta/Postman — Send Message Template Interactive](https://www.postman.com/meta/whatsapp-business-platform/request/lwtlz1k/send-message-template-interactive)
- [Meta/SDK — ButtonParameterObject](https://whatsapp.github.io/WhatsApp-Nodejs-SDK/api-reference/types/button_parameter_object/)
- [Meta/SDK — InteractiveObject](https://whatsapp.github.io/WhatsApp-Nodejs-SDK/api-reference/types/InteractiveObject/) (**SDK arquivado; apenas referência histórica, sem dependência**).

O formato de callback considerado em fixtures é `messages[].type=button; button:{text,payload}` para escolha de template e `messages[].type=interactive; interactive:{type:"button_reply",button_reply:{id,title}}` para botão de mensagem interativa. Esses dois formatos não devem ser confundidos ou promovidos a uma ação comercial por coincidência de rótulo.

## Implementação

`integrations/whatsapp-meta/cloud-button-reply-handoff.ts`: `inspectSignedMetaButtonReplies(rawBody,signature,appSecret,trustedRoute,limits?)`:

- Tira um snapshot dos bytes do corpo antes de operações assíncronas; chama **o verificador existente** `inspectCloudWebhookForHandoff`, que por sua vez valida HMAC SHA256 sobre bytes brutos, tamanho/eventos, App Secret da rota confiável e WABA/phone de todos os eventos. **Não implementa outra assinatura ou outra política de ACK**.
- Somente após a assinatura ser válida, percorre as posições de `messages[]` já inspecionadas, confere ID e participante, separa `template_quick_reply` de `interactive_button_reply` e preserva posição exata, `wamid` recebido, referência de contexto opcional, opção opaca e texto de apresentação.
- Ignora eventos `text` e `statuses[]` nessa extração específica; rejeita todo o resultado quando há `button` malformado, variante interativa ainda não contratada, WABA/phone cruzado, HMAC incorreto ou lote inválido. **Não descarta silenciosamente um botão desconhecido e não faz ACK**.
- Preserva callbacks duplicados em posições distintas: **não deduplica**, não define consentimento e não resolve se a opção existe no catálogo vigente. A escolha técnica ainda precisará ser correlacionada ao `wamid` do envio, à tentativa vinculada e à política da S0; um payload aparentemente correto pode estar obsoleto ou fora de escopo.
- Uma saída positiva é **`SIGNED_CANDIDATES_NOT_DURABLE`** e TODAS as flags `ack_allowed`, `send_authorized`, `s0_write_authorized`, `retry_external`, `production_authorized`, `delivery_confirmed`, `case_transition_authorized`, `commercial_effect_authorized`, `catalog_choice_verified`, `consent_verified`, `deduplicated` permanecem `false`. Assinatura de webhook não é consentimento, contrato de tentativa, nem permanência em banco.

**Dados pessoais:** o objeto técnico inclui identificadores de participantes e valores de botão para eventual reconciliação autorizada. Mantê-los em memória no laboratório; **não registrar em logs, métricas, respostas públicas, arquivos de evidência ou mensagens do assistente**. As negativas incluem apenas códigos e flags, nunca conteúdo.

## Testes úteis, sem repetir laboratórios anteriores

`cloud-button-reply-handoff.test.ts`: 18 casos: mistura de botão template + interativo + texto, status sem clique, contexto ausente/inválido, HMAC errado, rota/WABA errada, payload de opção fora da gramática, botão malformado, subtipo `list_reply` ainda não contratado, getters não relevantes após JSON autenticado, duplicatas sem idempotência, limites e UTF8 malformado.

CI `.github/workflows/meta-cloud-button-replies-offline.yml`: 18 testes novos e apenas regressões focadas de `inbound`, `routed-webhook`, `cloud-webhook-handoff` e `graph-template-interactive`. Não repete WA39–WA68 nem PR #14/#19.

## Dependência para futura integração

**Nenhuma nova porta S0 exigida nesta etapa.** A aceitação de uma escolha clicada já depende de decisões não ratificadas nos PRs #14 e #19:

- vínculo de origem técnica por App/WABA/phone, chave e revalidação M2M;
- associação durável entre `wamid` de envio, tentativa, template e revisão do catálogo;
- classificação e idempotência de um **evento inbound distinto de status outbound**;
- escopo, finalidade e consentimento vigentes, sem inferir autorização de envio ou alteração de caso a partir do clique.

Se ao ratificar PRs #14/#19 o Codex concluir que o vínculo do `wamid` para o botão não está coberto, registrar uma proposta com prova objetiva de ida/volta e teste de duplicata antes de solicitar implementação S0 adicional. **Não abrir uma nova demanda por hipótese.**

**Limites:** esquema de botão deliberadamente estreito. `interactive.list_reply`, CTAs, mídias, respostas com outro envelope e políticas comerciais ficam fora da implementação. Não há autenticação de fonte produtiva, evento persistido, homologação Meta ou garantia de exatamente uma ocorrência.
