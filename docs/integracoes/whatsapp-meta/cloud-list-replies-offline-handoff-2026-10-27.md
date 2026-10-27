# WhatsApp/Meta — extensão aditiva: seleção de item de lista

**27/10/2026 — frente Cloud API, laboratório independente.** Origem PR #24, branch `feat/meta-cloud-list-replies-20261027`. Sem mudança no núcleo S0/S1, PRs #14/#19, credenciais reais, endpoint, Graph, ACK, banco hospedado, merge ou deploy.

## Lacuna e referência

O PR #24 já extrai botões de template (`messages[].type=button`) e botões interativos (`messages[].interactive.type=button_reply`) a partir de HMAC Meta e WABA/phone conferidos por rota confiável. Porém **nega** `messages[].interactive.type=list_reply` em vez de extrair a linha que a pessoa selecionou. Essa informação tem formato técnico distinto, contendo `list_reply.id`, `list_reply.title` e, opcionalmente, `list_reply.description`.

Referências consultadas:
- Meta, coleção oficial: [Send Reply to List Message](https://www.postman.com/meta/whatsapp-business-platform/request/0v36tbh/send-reply-to-list-message), envio interativo do tipo `list`;
- [Referência dos campos de callback de mensagens interativas](https://support.chatarchitect.com/books/meta-whatsapp/page/interactive-messages-webhook-reference-developer-documentation) (espelho da documentação Meta, 2025);
- [Exemplo de webhook list_reply do SERPRO](https://whatsapp.serpro.gov.br/api-docs/documentacao/tipos_mensagens_recebidas/).

Essas fontes embasam o **shape experimental**; não homologam uma conta Meta, campos adicionais/limites variáveis da Graph API vigente ou qualquer autorização comercial.

## Implementação efetiva e preservação da API existente

Arquivo: `integrations/whatsapp-meta/cloud-button-reply-handoff.ts`:

- Preserva o export **`inspectSignedMetaButtonReplies()`** e seu comportamento PR #24: segue aceitando os dois tipos de botão e **negando listas**. Todos os antigos testes continuam válidos.
- Exporta nova entrada **`inspectSignedMetaSelections()`** usando o **mesmo núcleo interno**; além dos dois botões anteriores, passa a aceitar `interactive.list_reply` estrito. **Sem segunda verificação HMAC**: ambas reutilizam `inspectCloudWebhookForHandoff`, parser de posição, snapshot dos bytes, binding WABA/phone e falha integral por lote.
- Para listas, preserva `provider_message_id` do inbound, `reply_to_provider_message_id` do contexto opcional, `participant_identifier`, índice exato no lote, ID da linha, título e descrição opcional. `kind=interactive_list_reply`; descrição ausente é `null`. Botões e listas não são convertidos em um mesmo tipo comercial.
- Limita a gramática de ID opaco local a ASCII `[A-Za-z0-9_.:-]`, 1–128; título até 24 caracteres Unicode; descrição opcional até 72; recusa subtipos novos, propriedades injettadas no objeto interativo, contextos inválidos e lotes mistos parcialmente malformados. Valores fora do perfil conservador devem ser contratados e testados antes de ampliar.
- Retorna `SIGNED_CANDIDATES_NOT_DURABLE` **mesmo para uma lista válida**, com todos indicadores `ack_allowed`, `send_authorized`, `s0_write_authorized`, `production_authorized`, `commercial_effect_authorized`, `catalog_choice_verified`, `consent_verified`, `deduplicated`, `retry_external`, `delivery_confirmed` e `case_transition_authorized` fixados em `false`.

**Não confundir:** o `list_reply.id` observado não comprova que havia uma lista previamente enviada/aprovada, que a opção era válida na revisão corrente, que houve consentimento ou que há um caso/venda. HMAC assinado não substitui persistência/ACK, autorização de negócio ou idempotência. O retorno contém telefone/valores textuais e não deve ser logado ou exposto para cliente final.

## Provas isoladas

`cloud-list-reply-handoff.test.ts` — **15 cenários novos**: escolha de lista; descrição ausente; três tipos mistos; compatibilidade estrita com export legado; opção desconhecida; caracteres inválidos, campos extra, subtipos desconhecidos, HMAC incorreto, troca WABA/phone, callbacks repetidos, contexto inexistente e lote com status malformado.

Workflow `.github/workflows/meta-cloud-list-replies-offline.yml`: executa esses 15 testes + regressões focadas de `cloud-button-reply-handoff`, `cloud-webhook-handoff`, `inbound` e `routed-webhook`. Não executa novamente WA39–WA68 nem testes candidatos PR #14/#19.

## Dependências e decisão de integração

**Nenhuma nova solicitação S0 imediata.** Futuramente, associar uma seleção de lista à respectiva mensagem enviada, tentativa/tenant e um conjunto de opções definido por origem backend confiável demandará **contrato específico de escolhas interativas**, que não é equivalente à aprovação de templates `META-S0-TEMPLATE-CATALOG-05` (PR #19). Não criar tal contrato automaticamente nem transformar esta observação em regra comercial. A equipe S0/Codex só deverá ser acionada quando o fluxo de **envio de listas** estiver sendo integrado e os critérios de autoria, vínculo por `wamid`, idempotência e política estiverem definidos.

Os quatro contratos candidatos do PR #14, T1–T6 do PR #19 e a autenticação/ACK operacional seguem não ratificados. Não há rede, garantia de envio, retenção ou aprovação Meta.
