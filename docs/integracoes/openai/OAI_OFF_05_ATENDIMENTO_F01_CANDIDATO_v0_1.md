# OAI-OFF-05 — Atendimento F01, fronteira de proposta e transferência humana (v0.1-candidate)

**Data:** 31/10/2026. **Frente:** OpenAI. **Condição:** CANDIDATO OFFLINE, sem autoridade produtiva, sem cliente de modelo/SDK, sem S0 físico ratificado, sem autorização de mensagem, áudio, status ou transferência.

## Base, precedência e escopo

Base formal conhecida: OFF-01 `394512327cd3756dfbe61ff970a6279c354b6565` → S2 `1747cb0fee2a95322dc768044bafe9817d8cc540`, com `core.mjs:validateF01`, `journey.mjs:evaluateOfflineJourney` e [E01 v0.4](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/1747cb0fee2a95322dc768044bafe9817d8cc540/docs/integracoes/openai/E01_CONTRATO_TIPADO_ADAPTADOR_FALHAS_v0_4.md). OFF-02 a OFF-04 são patches **locais incrementais**, ainda sem commit GitHub ou homologação de compatibilidade com todos os ancestrais.

A F01 atua apenas antes de transferência humana definitiva, para casos sob posse da IA confirmada pela S0. Ela recebe somente instrução global F01 e comportamento global F01 (dois dos quatro parâmetros globais autorizados), nunca um override por loja. F02 e F03 usam parâmetros próprios. O conteúdo de mensagens de clientes, fonte histórica e texto do modelo são **dados não confiáveis**, nunca autorização. Não enviar escala, nomes, volume/disponibilidade de Consultores, segredos ou recibos S0 ao fornecedor.

## API candidata do módulo puro

Arquivo: `e04_offline_lab/f01-sales-boundary.mjs`.

- `prepareF01Turn(privateEnvelope)` → `READY_CANDIDATE` com cópia interna congelada, ou falha tipada. Confere alegações sintéticas de autenticação/loja/caso/pessoa/posse IA, autorização de conteúdo, permissão de canal, opt-out, estados terminais, e oito versões separadas (`case, cycle, assignment, catalog, policy, knowledge, route, consent`). **Os booleans são fixtures, NÃO atestados S0.**
- `f01ProviderView(ready)` → somente `providerTag`, instrução e comportamento F01, contexto selecionado, mensagem/transcrição confirmada, fontes com alias, conteúdo e códigos sintéticos de claims. Não contém `requestId`, IDs originais de loja/caso/pessoa/fonte, recibos, concessões, cargos ou escala. **Aliases não anonimizam PII de texto livre**; entrada precisa vir minimizada de S0.
- `evaluateF01Model(ready,raw,{nowMs,currentScope,prior?})` → valida JSON exato, tag, claims, fontes atuais, vigência no instante de retorno, revogação e versões. Só devolve `S0_RECHECK_ONLY`, com rascunho interno e flags `publishAuthorized=false`, `handoffAuthorized=false`, `customerMessageSent=false`, `semanticVerified=false`, `physicalS0Recheck=false`; ou falha sanitizada.
- `reviewF01Handoff({scope,events,prior?})` → auditoria sintética de eventos ordenados. A partir de `HANDOFF_TO_HUMAN`, `NEW_INBOUND`, `HUMAN_CLOSE` ou outra mensagem não devolvem o caso à IA; `AI_TURN` posterior é negado. Não concede posse da IA em estado anterior: `AI_ELIGIBILITY_S0_RECHECK` também tem `aiResumeAuthorized=false`.
- `f01SafeAudit(result)` → dicionário de operação, status e estágio permitidos, sem texto, IDs ou stack.

### Entradas e saídas do modelo (somente candidato)

Entrada privada: `prumo.openai.f01-private/0.1-candidate`, com `requestId`, `providerTag`, relógio lógico/deadline, escopo, privacidade, instruções F01, `customerInput`, até 20 mensagens recentes e até 48 fontes previamente autorizadas.

Entrada minimizada do fornecedor: `prumo.openai.f01-provider/0.1-candidate`. A distinção de fonte `current` x `historical` é explícita; fontes históricas podem ser usadas apenas para interpretação e não para sustentar oferta atual.

Resposta do fornecedor: `prumo.openai.f01-response/0.1-candidate`, em JSON estrito:

```json
{
  "schemaVersion": "prumo.openai.f01-response/0.1-candidate",
  "providerTag": "opaque_1",
  "state": "completed",
  "output": {
    "replyText": "Oferta sujeita a confirmação.",
    "commercial": true,
    "sourceAliases": ["src_001"],
    "claims": [{"claimCode": "offer_available", "sourceAlias": "src_001"}],
    "modalityHint": "text",
    "handoffAdvisory": {"needed": false, "reason": "NONE"},
    "uncertaintyCodes": []
  }
}
```

O exemplo é inteiramente fictício: **códigos de claims atestados na fixture não provam correspondência semântica entre texto e fonte**. Portanto nenhum resultado libera publicação automática. Campo comercial requer pelo menos uma fonte **atual, ativa, vigente** e claim aliada à mesma fonte no allowlist. Histórico, fonte expirando antes do retorno, alias de outro fornecedor/loja, código inventado, `tool_calls`, `send`, `vendido`, aprovação bancária e alterações de status são rejeitados; texto livre ainda precisa de inspeção substantiva posterior S0.

Entrada de áudio é **apenas transcrição STT confirmada previamente**, em texto. Transcrição incerta gera `REVIEW_REQUIRED`. `modalityHint` é opinião sem efeito, não áudio, TTS nem despacho. Pedido de áudio de uma entrada textual vai para revisão. Handoff sugerido é somente consultivo; nenhum evento é criado pela IA.

## Replay, falhas e relógio

- A autorização é checada **antes** de stale, resposta, deadline ou existência de caso. No recheck, posse humana, opt-out, pós-venda/remessa e tenant errado negam até um rascunho tardio.
- A chave de replay é candidata: SHA-256 de **bytes exatos do JSON de retorno** + request/tag; prior é declarado pela fixture e **não autenticado/persistido**. Mesmo replay exato retorna `ALREADY_HANDLED_REVIEW_ONLY`, sem publicar. Replay divergente: `REPLAY_CONFLICT`.
- Relógio lógico é parâmetro de teste, sem `Date.now()`, rede, retries, custos ou eventos autônomos. Timeout e recusa do modelo não mudam caso.
- Fonte comercial histórica é permitida no payload **somente como contexto interpretativo**, não como evidência de oferta atual. Não se garante que o modelo respeitará o texto; por isso S0 precisa avaliar a proposta.

## Dependências reais não absorvidas

1. **S0/S1:** resolução confiável de posse/transferência definitiva e reinício, canal/consentimento, seleção e vigência de fontes de conhecimento, versões separadas, dedupe/late e autorização de publicação. A ser registrada em Issue F01 específica; não é S0 paralela.
2. **Meta:** transporte, janela de atendimento WhatsApp, confirmação de envio e política de mídias conforme contratos da frente Meta; não confundir entrega com texto gerado. Ingresso/ACK em #2, cadastro/rota em #8 e recheck de envio na #10, sem duplicá-las.
3. **Proprietário:** decisões de recursos reais, voz/STT/TTS/retenção de áudio, gasto de modelo, privacidade e publicação produtiva seguem reservadas.
4. OFF-01/02/03/04 e oráculos E02: regressão completa S2/342 herdados e E02 70 cenários ainda não foram executados neste lote; A38 histórica continua indisponível. Não promover resultados locais a homologação.

**Exclusões:** nenhum SQL/RLS, websocket, API HTTP, Meta Graph, credenciais, IA otimizadora, acesso a Banco, mudança de ficha, nomeação administrativa, merge/deploy/produção ou chamada paga.
