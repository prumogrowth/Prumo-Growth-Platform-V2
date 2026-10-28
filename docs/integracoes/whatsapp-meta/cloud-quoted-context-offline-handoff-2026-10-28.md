# Meta Cloud — referência contextual assinada em mensagens recebidas (offline)

**Data:** 28/10/2026. **Base:** PR #41, commit `7ab3e9613eb5afdc2de74048a5e0c076e3449207`. **Branch:** `feat/meta-cloud-quoted-context-20261028`.

## Lacuna e evidência de formato

A documentação da Meta ilustra `messages[].context` em mensagens recebidas, inclusive em uma mensagem de texto com referência a produto e em respostas interativas. O exemplo documentado contém `context.id` e `context.from`, e pode conter metadados adicionais, como `referred_product`. Esta documentação **não** afirma que esse contexto seja prova de existência da mensagem anterior ou autorização de efeito comercial.

Fontes:
- [Meta / WhatsApp Business Platform — coleção oficial Cloud API no Postman](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api?entity=request-13382743-ba924e99-3d98-4954-b4e3-73a519939c33).
- [SERPRO — exemplos de recebimento de respostas interativas com context.id/from](https://whatsapp.serpro.gov.br/api-docs/documentacao/tipos_mensagens_recebidas/).

Os leitores anteriores já aceitavam `context.id` em respostas de botões/listas, mas **não** forneciam essa referência em mensagens recebidas genéricas e mídia, nem uma representação complementar na composição sem duplicar eventos.

## Implementação

**Novo leitor:** `integrations/whatsapp-meta/cloud-quoted-context-handoff.ts` expõe `inspectSignedMetaQuotedContexts()`.

- Cria cópia dos bytes brutos antes do primeiro `await` e reutiliza `inspectCloudWebhookForHandoff()` para HMAC, escopo WABA/phone, limites e atomicidade do lote.
- Inspeciona somente `messages[].context` após autenticação. Se há `context.id`, valida via `isMetaWamid()` e, caso exista, valida `context.from` como identificador técnico numérico de 8 a 15 dígitos. **Não trata o identificador como identidade civil**, consentimento ou correlação com uma tentativa S0.
- Contextos que apenas indicam encaminhamento, sem `id` e sem `from`, **não são classificados como citação**. Campos adicionais (`referred_product`, `mentions`, flags de encaminhamento etc.) não são interpretados, retornados ou enviados para links/Graph.
- Se qualquer contexto relevante contém referência inválida, devolve `DENIED` sem observações parciais; não recupera o texto da mensagem original nem confirma que o ID citado existe.

**Composição aditiva:** `cloud-composed-observation-handoff.ts`.

- Acrescenta `quoted_reference: SignedReplyContextObservation|null` a cada ocorrência **já existente**, sem criar uma segunda ocorrência para a mesma `entry/change/messages[index]`. Isso permite um botão, mídia ou reação preservar sua classificação principal e simultaneamente mostrar um vínculo técnico de mensagem citada.
- Após a HMAC geral, examina apenas o mesmo snapshot autenticado para decidir se algum item contém a propriedade `context`. O novo leitor especializado e **sua própria HMAC** são acionados somente se necessário.
- Confere o `raw_sha256` e alinha posição, ID principal, participante, timestamp e escopo ao evento de base. Para seleções com `reply_to_provider_message_id`, também confere consistência do ID citado.
- Mantém a ordem original, no máximo uma `evidence` especializada por posição, duplicatas sem dedupe, rejeição atômica e todos os indicadores de autorização `false`.
- Contagem de HMAC por webhook fica em **1–7**, dependendo das categorias e da presença de contexto. **Isso não é benchmark de latência.** Sem contexto, o custo seletivo previamente certificado permanece inalterado.

## Limites de compatibilidade

O leitor é deliberadamente conservador: `context.id` ausente implica nenhum vínculo técnico; `context.id` presente mas inválido provoca negativa. `context.from` é opcional, porém deve ser numérico válido quando existir. Um futuro formato oficial da Meta fora dessa gramática exigirá uma revisão explícita, não um rebaixamento silencioso da falha.

Nenhuma associação com cliente, autorização de resposta, conversa/caso, texto original, envio, retry, mensagem lida, persistência, idempotência ou HTTP ACK é inferida de `context`. Os identificadores retornados são potencialmente sensíveis: **não registrar em logs nem enviar indiscriminadamente ao frontend**.

## Certificação

`cloud-quoted-context-handoff.test.ts`: **22 cenários sintéticos** de contexto normal, opcional, forwarding-only, referência inválida, lote misto, scope errado, assinatura adulterada, limites, mutação de buffer, sobreposição de `evidence` com `quoted_reference` e contagem de HMAC.

Workflow `.github/workflows/meta-cloud-quoted-context-offline.yml`: **22 novos + 226 regressões focadas**, incluindo PR #41, #39, #37 e demais leitores HMAC. **Total previsto: 248.** Requer confirmação de SUCCESS no SHA final. Não testa rede, formato live Meta, nem toda a suíte WA39–68.

## Governança

**PR Draft, sem merge/deploy ou alteração S0/S1.** Nenhum Graph GET/POST, token real, usuário real, webhook público, Supabase, ACK, export de conteúdo do cliente ou efeito comercial. PRs #14/#19 continuam candidatos não ratificados. Nenhuma dependência imediata nova da S0 para os testes offline; correlação real de `context.id` depende de política, autenticação e persistência autorizadas pela S0.
