# Meta WhatsApp Cloud API — diagnóstico de erros em status de mensagens enviadas (offline)

**Data:** 27/10/2026. **Frente:** WhatsApp/Meta. **Branch:** `feat/meta-cloud-failed-status-errors-20261027`. **Base:** PR #31, SHA `1d35d79e9e8ca25a96f3e29c738cc5cfc1b91e71`.

## Lacuna verificada

`inbound.ts` e `cloud-webhook-handoff.ts` autenticam a assinatura do callback e identificam `statuses[].status=failed`, porém ignoram o subobjeto `statuses[].errors[]`. `status-evidence.ts` e `technical-reconciliation.ts` já lidam com evidências/correlação técnicas em outra fronteira; este módulo NÃO altera nem substitui tais classificadores, e tampouco interpreta a resposta HTTP síncrona da Graph API.

Referências externas para o formato experimental:
- [Meta — documentation sobre erros Cloud API (reprodução de conteúdo de documentação)](https://github.com/kapso-meta-docs/documentation/blob/main/documentation/whatsapp/error-codes.mdx)
- [Exemplo de webhook de falha contendo statuses[].errors[]](https://support.qiscus.com/hc/en-us/articles/1732590390871-WA-Webhook-sample)
- [Guia de referência de erros Meta em callbacks (terceiro)](https://dualhook.com/docs/api-errors)

Essas fontes não ratificam um contrato operacional com a S0 ou a assinatura de um webhook real.

## Implementação aditiva

`integrations/whatsapp-meta/cloud-failed-status-errors-handoff.ts` exporta `inspectSignedMetaFailedStatusErrors()`.

- Reutiliza diretamente `inspectCloudWebhookForHandoff()` para HMAC dos bytes brutos, limite de corpo/eventos, identidade WABA/phone confiável, verificação de TODO o lote e posições de mensagens/status. Inspeciona o MESMO snapshot do corpo verificado.
- Somente `status=failed` pode gerar `provider_reported_failed_status_errors`; requer `errors[]` não vazio e limitado. Preserva o `statuses[].id` como ID **da mensagem enviada**, não identificador exclusivo de callback; conserva recipient, timestamp, WABA/phone e posição da ocorrência.
- Retorna somente pares `code` e `error_subcode` opcional. O subcódigo é informação legada/depreciada e não é usado para tomar ação. Campos `title`, `message`, `type`, `error_data.details`, `fbtrace_id` e `href` são validados estruturalmente, mas NUNCA expostos na saída nem tratados como link.
- Erros inesperados em `status=sent/delivered/read` provocam negativa integral por ambiguidade, sem declaração de entrega. Se uma ocorrência relevante é malformada, NENHUMA observação parcial é retornada. Duplicatas são preservadas até avaliação S0.
- `SIGNED_FAILED_STATUS_ERRORS_NOT_DURABLE` **não concede** HTTP 200, gravação ou ACK; retry, envio, contagem de falhas definitivas, associação S0 de tentativa, autorização comercial, mudança de caso, dedupe, confirmação de efeito ou entrega. Todos os indicadores de autorização são `false`.

## Certificação e testes

`cloud-failed-status-errors-handoff.test.ts`: 18 casos sintéticos, incluindo códigos 131026/131047/131049, ausência de erro, mistura de mensagens e status, replay duplicado, HMAC inválida, fronteiras WABA/phone, ambiguidade status/erros, campos maliciosos e limites. O workflow `.github/workflows/meta-cloud-failed-status-errors-offline.yml` executa também **136 regressões focadas** de handoffs anteriores e do ingress HMAC. Não executa novamente a suíte WA39–68, nem modifica contratos S0/S1.

**Nota de certificação:** a execução GitHub Actions precisa ser confirmada no SHA final exato. A documentação não substitui a prova de CI.

## Pendências e governança

Sem demanda nova para a S0 nesta etapa técnica. Futuro significado de `failed`, correlação com tentativas, idempotência, armazenamento, ACK, dedupe, políticas de reenvio e decisão comercial continuam sob autoridade da S0 e respectivos contratos, que ainda não estão ratificados nos PRs #14/#19.

Nenhuma chamada Graph, nenhum token/segredo real, endpoint público, envio, download, usuários reais, Supabase, alteração S0/S1, merge ou deploy.