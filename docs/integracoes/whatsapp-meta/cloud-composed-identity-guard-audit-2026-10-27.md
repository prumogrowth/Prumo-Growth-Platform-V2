# Auditoria Meta Cloud — identidade técnica de eventos genéricos (offline)

**Data:** 27/10/2026. **Base:** PR #37 `5f75b44e29995a80397ad5cb44bd09f3f46c611e`. **Branch:** `audit/meta-cloud-generic-identifier-guard-20261027`. Não há merge, endpoint real, Graph API ou alteração S0/S1.

## 1. Lacuna demonstrada

`cloud-webhook-handoff.ts` autentica HMAC e vincula o lote à WABA/phone. O parser genérico `inbound.ts` exige apenas *strings não vazias* para `messages[].id`, `messages[].from` e `messages[].type`, e para `statuses[].id`/`recipient_id`. Isso é suficiente para inspecionar o envelope, mas não para emitir identidades técnicas com gramática controlada na **camada composta**.

Um callback perfeitamente assinado em laboratório ainda podia ser aceito como `SIGNED_COMPOSED_NOT_DURABLE` com identificadores como `NON_WAMID`, participantes não numéricos ou com quebras de linha, e tipos genéricos como `TEXT` ou `text\nprivileged`. Nenhuma das cinco especializações era invocada para alguns desses tipos, tornando a recusa dependente da categoria do evento.

**Prova RED:** workflow GitHub Actions `40616694282`, commit `48f0434f43e7e8bf2a099440bfa9c9d4ae455858`: **4/20 casos passaram e 16/20 falharam**, demonstrando os critérios ausentes antes da correção.

## 2. Correção aditiva

Somente `integrations/whatsapp-meta/cloud-composed-observation-handoff.ts` recebe um guard **após a autenticação de TODO o corpo** e **antes da execução de qualquer leitor especializado**:

- `provider_message_id` deve passar em `isMetaWamid()`, predicado técnico **já existente** em `status-evidence.ts`.
- `participant_identifier` exige representação ASCII numérica com 8 a 15 dígitos. Trata-se de um filtro conservador de identificador WhatsApp, não de validação civil ou prova de destinatário.
- Tipos de mensagens de entrada, inclusive os **genéricos/desconhecidos**, exigem `^[a-z][a-z0-9_]{0,63}$`. Tipos novos que respeitem essa gramática continuam como `uninterpreted_inbound`. Estados de `statuses` permanecem limitados pelo classificador já existente.
- Qualquer violação no lote retorna `DENIED / INVALID_TECHNICAL_IDENTIFIERS` e `occurrences: []`, `raw_sha256: null`, com todas as flags de autoridade permanentemente falsas.

O guard não altera a HMAC, seu custo seletivo (1 a 6 verificações por lote), o snapshot de rota/limites, as gramáticas dos leitores especializados, regras de escopo, preservação de duplicatas, nem os contratos S0. Nenhuma escrita, ACK, envio, resposta, tentativa, retry ou mudança comercial é autorizada.

## 3. Testes e cobertura

`integrations/whatsapp-meta/cloud-composed-identity-guard.test.ts` possui **20 testes sintéticos** para:

- payloads genéricos válidos; tipos futuros seguros e preservados;
- falsos `wamid`, novas linhas, caracteres de controle, espaços e Unicode em IDs;
- participantes alfabéticos, com injeção de linhas, curtos, longos e numerais Unicode semelhantes;
- tipos desconhecidos perigosos (caixa alta, quebra de linha, prefixos não previstos);
- callbacks `sent` com ID/destinatário inválidos;
- negativa atômica de lote quando um evento malformado acompanha uma reação válida;
- retenção de eventos repetidos (sem dedupe) e limite de 100 eventos.

Workflow `.github/workflows/meta-cloud-identity-guard-offline.yml`: os **20 testes novos** mais **194 regressões focadas** herdadas (incluem os 20 cenários da auditoria anterior, composição, seleção, mídias, reações, falhas de status, assinaturas e roteamento). **Total esperado: 214 provas, zero falhas**. A certificação exige confirmar GitHub Actions SUCCESS no **HEAD final exato**.

## 4. Limites e integração futura

Essa validação é **sintática e conservadora**, não pode afirmar que o remetente é cliente, que um `wamid` existe na Meta, nem que ocorreu entrega, consentimento ou persistência. Um formato novo da Meta que não siga as gramáticas técnicas aqui assumidas será rejeitado e exigirá revisão explícita, evitando promoção automática de forma desconhecida a evento comercial.

A frente S0 permanece separada e responsável por identidade de cliente, mapeamento de tentativa/caso, idempotência, ingress durável e ACK. PRs candidatos #14/#19 não estão ratificados. O PR #36 paralelo cobre mutação do escopo na borda genérica e não foi modificado nem reproduzido aqui. Nenhuma dependência S0 nova para o teste offline.

Todos os casos usam dados artificiais. Sem segredo Meta, HTTP real, token, webhook de produção, cliente real, Supabase, deploy ou merge.
