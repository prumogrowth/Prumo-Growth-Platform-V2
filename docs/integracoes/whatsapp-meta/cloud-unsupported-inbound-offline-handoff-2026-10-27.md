# WhatsApp/Meta — mensagens recebidas não suportadas: diagnóstico técnico sem efeito comercial

**27/10/2026 — offline apenas.** Base de desenvolvimento: PR #29, SHA `a4ed61764e43a885be1f1f4faf15b459513cca9d`. Branch nova: `feat/meta-cloud-unsupported-inbound-20261027`.

## Lacuna comprovada

O núcleo `inbound.ts` e `cloud-webhook-handoff.ts` reconhece `messages[].type=unsupported` apenas como tipo genérico, sem analisar `errors[]`. A Meta documenta evento de mensagem recebida não suportada com erro 131051, incluindo campos textuais opcionais; isso é distinto de rejeição do envio pela Graph API e de `statuses[].status=failed`.

Referências:
- [Meta — coleção oficial WhatsApp Cloud API, amostra webhook unsupported](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api?entity=request-13382743-ba924e99-3d98-4954-b4e3-73a519939c33)
- [SERPRO — tipos de mensagens recebidas: mensagens desconhecidas](https://whatsapp.serpro.gov.br/api-docs/documentacao/tipos_mensagens_recebidas/)

O suporte experimental segue uma gramática conservadora, sujeita a validação contra homologação real. Esta implementação não pretende aceitar todos os campos futuros da Meta.

## Implementação

Novo `integrations/whatsapp-meta/cloud-unsupported-inbound-handoff.ts`, export `inspectSignedMetaUnsupportedMessages()`.

- **Reutiliza** `inspectCloudWebhookForHandoff()` para verificação HMAC, bytes originais, autenticação do escopo WABA/phone, lote inteiro, limites e posição.
- Para `type=unsupported`, exige `errors[]` não vazio (máximo 8), extrai apenas `code` inteiro positivo e `error_subcode` opcional. Preserva referência de mensagem, identificador de participante, timestamp, WABA/phone, posição e `unsupported.type` opcional **não confiável**.
- Valida, **mas não devolve**, `title`, `message`, `error_data.details` e `fbtrace_id`; são diagnósticos textuais potencialmente sensíveis e nunca devem ir a logs.
- `code=131051` é **observação**, não autorização para avisar o cliente, deduzir intenção, reenviar, declarar falha comercial ou atualizar o caso.
- Retorna `SIGNED_UNSUPPORTED_NOT_DURABLE` sem permissão de ACK, escrita S0, idempotência, reenvio, confirmação de entrega, resposta automática, recuperação de conteúdo ou contagem definitiva de falhas. 
- Se qualquer erro é inválido ou outro elemento do lote é malformado, **nenhum candidato** é devolvido. Mensagens ordinárias e callbacks de status não viram erros de entrada; duplicatas continuam distintas.
- Os textos não são expostos pelo handoff. IDs e `unsupported.type` ainda são dados sensíveis e não devem ser registrados em logs.

## Verificação e dependências

`cloud-unsupported-inbound-handoff.test.ts` possui 16 cenários inteiramente sintéticos, com assinatura, rota, código/subcódigo, campos desconhecidos, textos malformados, limites, evento duplicado, mutação do buffer e falha atômica. Workflow `.github/workflows/meta-cloud-unsupported-inbound-offline.yml`: 16 novos + 120 regressões focadas, Node 22 `--experimental-strip-types`.

**A certificação deve ser confirmada no GitHub Actions e vinculada ao SHA final exato.** A existência desta documentação não prova que o CI foi aprovado.

Nenhuma solicitação S0 nova imediata: o tratamento empresarial e a resposta ao cliente deverão ser autorizados pela S0 em integração futura, juntamente com persistência/ACK e contrato de mensagens recebidas. Os PRs #14 e #19 permanecem candidatos, sem ratificação. Nenhuma migração, Graph, token, webhook público, banco real, merge, deploy ou alteração S0/S1.
