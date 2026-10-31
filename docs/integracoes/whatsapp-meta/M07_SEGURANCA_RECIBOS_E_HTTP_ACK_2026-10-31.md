# M07 — Segurança de recibos e fronteira HTTP ACK (31/10/2026)

**Classificação:** hardening implementado na branch de laboratório; **política operacional de HTTP ACK NÃO RATIFICADA**.

## Alterações efetivas da frente Meta

1. O módulo histórico `integrations/whatsapp-meta/durable-receipt.ts` nunca mais produz `{status:200, action:'ACK'}` nem qualquer outro status/action HTTP. O `decideBatchAck()` permanece só como compatibilidade legada e devolve objeto congelado `DENIED_NO_HTTP_AUTHORITY` independentemente de contadores, `COMMITTED`, proxy, getter ou assinatura alegada.
2. `cloud-http-ack-authority-audit.ts` permanece exclusivamente negativo: dados de preflight, candidatos S0 e recibos alegados sem autoridade privilegiada não autorizam resposta.
3. `cloud-ack-runtime-guard.mjs` funciona como bloqueio conservador no CI a referências diretas ao helper legado, `status:200` em código Meta POST, retorno `action:'ACK'` e flags positivas de autoridade. O scanner em texto-fonte **não substitui auditoria binária, análise dinâmica ou revisão do deploy**.
4. Há testes negativos específicos em `durable-receipt.test.ts`, `cloud-ack-runtime-guard.test.ts`, `cloud-http-ack-authority-audit.test.ts` e testes históricos atualizados. O teste interfrentes M06 também consome recibo PG17 da S0, mas propositalmente não gera ACK HTTP.

## Distinções obrigatórias

- **Meta GET / verificação do webhook:** `200` após verificar o desafio e token é mecanismo específico do GET, **não** aceite de lote POST.
- **HTTP 200 recebido da Graph API na saída:** é resultado da requisição para a Meta, **não** ACK de webhook de entrada, nem prova de `sent`/entrega.
- **Assinatura HMAC válida:** comprova origem dos bytes, **não** armazenamento durável.
- **Recibo Ed25519 verificado em laboratório:** comprova assinatura/contexto no perfil de teste, **não** autoridade produtiva, M2M externo ratificado ou autorização de resposta `200`.
- **Estado incerto, timeout ou callback ausente:** não implicam sucesso, falha definitiva, deduplicação autorizada ou recuperação automática.

## Critérios de ratificação ainda pendentes — S0 / Meta / Infra

- [ ] Definir **qual serviço confiável** autoriza resposta externa e verificar sua identidade técnica, pin da chave e revogação.
- [ ] Definir a unidade de transação (um POST físico Meta), tenant/App/canais, all-or-nothing, leitura de volta e sem ACK parcial.
- [ ] Aceitar explicitamente contrato durável de bytes/itens e recibo, HMAC + M2M + chave S0 pinada, mecanismo de recuperação pós-crash e replay.
- [ ] Definir política e códigos HTTP externos, incluindo POST 200, erro temporário, conflito, perda da resposta e repetição, com casos positivos/negativos em homologação.
- [ ] Aprovar segurança, observabilidade, limites de dados, rate limit e responsabilidade operacional do endpoint.

**Sem esses cinco aceites, o resultado do M07 é hardening técnico, não uma liberação de HTTP 200.** A homologação multicanais se aprofunda em M08; o aceite formal entre frentes continua em M27; endpoint operacional em M11/M12. Nenhum deploy, Graph real, migração S0/S1 ou mudança comercial está autorizado.
