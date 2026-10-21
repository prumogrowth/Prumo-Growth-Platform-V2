# WA-01C — Identificadores técnicos Meta e pistas de correlação v0.1

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Status: CANDIDATO [P], aguardando revisão cruzada do PR #1.** Incremento de código puramente local, sem DDL, credenciais, chamada Graph, ACK, banco ou deploy. A diretriz DEC-WA-05 de **um aplicativo Meta próprio por concessionária** está aprovada, mas o registro autenticado de vínculos e onboarding real continuam pendentes.

## Evidência do fornecedor e semântica

- A coleção pública Meta WhatsApp Business Platform especifica `messages[].id` como identificador único da **mensagem recebida** e `statuses[].id` como identificador da **mensagem cujo status mudou**. O status pode trazer `sent`, `delivered`, `read`, `failed` etc., junto a um `timestamp`. Portanto **não existe garantia de um ID único por callback de status**.
- Documentação Meta: [Messages Object](https://www.postman.com/meta/whatsapp-business-platform/folder/1dtuocp/messages-object), [Statuses Object](https://www.postman.com/meta/whatsapp-business-platform/folder/fuaee8l/statuses-object) e [Webhook Payload Reference](https://www.postman.com/meta/whatsapp-business-platform/folder/tduohwq/webhook-payload-reference).

## Implementação candidata no PR #2

`integrations/whatsapp-meta/technical-keys.ts` recebe **evento previamente autenticado** e `trustedAppRef` selecionado de **configuração confiável**, nunca de campo textual do remetente. Retorna uma pista de correlação SHA-256 (hex) composta por valores delimitados via JSON, sem número telefônico ou ID Meta bruto no resultado.

- **Inbound:** `app_ref + waba_id + phone_number_id + event_kind + provider_message_id`; não inclui telefone do cliente, texto, posição no POST nem timestamp, para que reentrega e variação 8↔9 não provoquem falso conflito por formatação. Não é prova de igualdade de conteúdo ou de titularidade do contato.
- **Status:** inclui, além do escopo e ID da mensagem de saída, `status + provider_timestamp`. Diferentes progressões/tempos não são confundidos. **Repetições idênticas de status/timestamp recebem a mesma pista e podem representar callbacks distintos**: a pista NÃO autoriza excluir eventos, nem substituir armazenamento completo sob política do núcleo.
- Ambos retornam `safe_to_auto_dedupe: false`. A decisão definitiva de idempotência, conflitos, payload íntegro, canal ativo, privilégio, compatibilidade do callback e política de retenção é do **núcleo S0** após contrato aprovado.

A saída **não** contém `concessionaria_id`, `canal_id`, `lead_id`, telefone nem autorização de envio. O hash não substitui comparação protegida de payload, prova HMAC, vínculo de canal, chave de armazenamento ou sigilo criptográfico; evitar uso em logs ou interfaces públicas.

## Ensaios realizados

`node --experimental-strip-types --test integrations/whatsapp-meta/technical-keys.test.ts`: **WA-KEY-01..12 PASS** em Node 22.16.0 local. Verificados replays 8↔9, IDs distintos, isolamento app/WABA/sender, estados e timestamps diferentes, status sem ID próprio, ausência de PII no resultado e entradas inválidas. `tsc --noEmit` também passou com tipo `MetaIngressEvent` espelhado localmente do PR #2; **não** representa compilação integral do repositório ou CI GitHub.

**Compatibilidade por decidir na S0:** adotar ou rejeitar esta pista como campo não autoritativo; definir a comparação definitiva de payload e dedupe de callbacks, e preservar o mesmo POST com múltiplos emissores em um aceite durável. A migration 029 é **somente protótipo sintético** e não pode ser conectada diretamente ao webhook Meta.

**Gates:** DEC-WA-04 ambiente ainda pendente; DEC-WA-05 titularidade aprovada, provisionamento/mandato efetivo ainda por validar; DEC-WA-06 segurança, retencão, backup e política de quarentena pendente. PR #1 e #2 permanecem Draft. Nenhuma alteração nos números comerciais da concessionária de demonstração.
