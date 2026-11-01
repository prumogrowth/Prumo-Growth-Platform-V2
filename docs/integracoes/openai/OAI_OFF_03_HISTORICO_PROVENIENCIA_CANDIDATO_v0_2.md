# OFF-03 — Adendo ao contrato candidato F03 v0.2 (auditoria)

**Versões substitutivas da interface offline:** `prumo.openai.f03-history-private/0.2-candidate`, `prumo.openai.f03-history-provider/0.2-candidate` e `prumo.openai.f03-history-proposal/0.2-candidate`. A v0.1 permanece como registro histórico; **não é compatível automaticamente** com a v0.2.

## Delta obrigatório

- No envelope PRIVADO acrescentar `providerTag` (ID opaco de tentativa, fornecido pela fixture S0; sem pessoa/loja/caso, segredo, sessão ou nonce de autorização).
- A projeção ao fornecedor ecoa **somente** `providerTag` para vincular a tentativa; o output também **deve** conter `providerTag` idêntico. Resposta de tentativa diferente é `SCHEMA_INVALID`.
- Cada alias citado em um campo é verificado isoladamente quanto a código, valor e fonte disponível. A presença de uma única fonte correta não pode legitimar aliases extras.
- `commercialAdvisory:perdido` só é elegível como sugestão humana, sem efeito, quando há prova sintética terminal `customer_withdrawal:true` de **mensagem do cliente**, sem correção ou contradição posterior. Declaração apenas humana ou da IA não é prova automática de desistência do cliente.
- `safeAuditEvent` da OFF-02 utiliza allowlist explícita de status e não aceita `APPLIED`/`SENT` de payload não confiável.

Não se trata de autenticação do S0, idempotência entre sessões, recibo assinado, interpretação semântica provada ou política de transição comercial. Permanecem as demais regras e limites do contrato v0.1.
