# E02 — Pacote de revisão de casos fictícios CFI-01 / CF-OP-02 | v0.1

**Data:** 18/10/2026 | **Status:** [P] entradas e resultados esperados para revisão S0/OpenAI/Meta; [R] contrato canônico e matriz de estados C09. **0 casos executados, 0 fixtures programadas, 0 API calls.** Este pacote é *especificação textual de cenários*, não JSON Schema aceito, suite automática nem evidência de desempenho. Qualquer número, loja e dado é sintético.

Referências: [CFI-01 proposta](CFI_01_PROPOSTA_CONCILIACAO_ENVELOPE_F03_v0_1.md), [OAI-08](OAI_08_CONTRATO_PLANEJADORA_POS_HUMANA_CF_OP_02_v0_1.md), [rastreamento E02](E02_RASTREABILIDADE_CF_OP_02_v0_1.md), [issue de revisão #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4) e [coordenação #6](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6).

## 1. Pré-condições sintéticas compartilhadas (sem presunção sobre banco LiberaCred)

- Loja fictícia `loja_A`, caso `caso_A_001`; cliente e operador são personagens fictícios, com atribuição ao operador autorizada pelo **stub S0**. Loja `loja_B` é isolada.
- Para ensaio, somente, a versão do catálogo `catalogo_demo_1` define `campo_req_A` e `campo_req_C` como **essenciais na simulação** e `campo_opt_B` como **opcional**; todos os três têm `auto_apply_allowed=true` na simulação. **NÃO** correspondem a campos obrigatórios reais da instituição financeira, CPF, renda ou número de documento.
- A origem do valor deve ser mensagem do cliente da mesma loja, referenciável pelo ID; pergunta do operador não comprova resposta. A S0 verifica proveniência, catálogo, versão e consentimento/política antes de aplicar.
- F03 somente depois de evento legítimo `closure_event_id`, com watermark/hash e versão de ficha; a guarda comercial da IA Vendedora permanece bloqueada após handoff.
- F02 somente por pedido separado autenticado S0, com allowlist de templates/versões e política de tentativas; mensagens Meta reais e persistência não fazem parte do laboratório textual.
- Onde matriz de estados **não está homologada**, expected é `NO_COMMIT / PENDING_S0_DECISION`, não `PASS` artificial. A observação de `sent` é uma prova **fictícia do stub**, não callback real Meta.

## 2. Casos de revisão (16 descrições concretas)

| Ref | Mensagens / evento sintético de entrada | Resultado esperado na fronteira OpenAI → S0 | Gate |
|---|---|---|---|
| EX-01 | Cliente msg01: “Minha informação A é ALFA e minha informação B é BETA”; msg02: “C é GAMA”; humano encerra com evento válido | F03 propõe **A=ALFA, B=BETA, C=GAMA**, cada um com sua mensagem-fonte; stub S0 aplica A/B/C. B é opcional, mas também é preenchido. Propor encaminhamento para remessa HUMANA conforme elegibilidade, **não** `vendido`. | [P] |
| EX-02 | Cliente fornece A e B; não fornece C, classificado essencial **apenas no catálogo sintético** | Aplicar A/B permitidos; C fica `missing`; sinalizar devolução ao operador com aviso “Falta C para preparar remessa”, sem inventar valor. | [P] |
| EX-03 | Cliente fornece A e C, nada diz sobre B opcional | Aplicar A/C; B permanece ausente sem provocar retorno ao humano por esse motivo. | [P] |
| EX-04 | Operador pergunta “A é ALFA?” e cliente não responde | Não propor A=ALFA como fato do cliente; registrar ausência/pendência se A essencial. | [P] |
| EX-05 | Cliente diz “A é ALFA” e depois diz “Não, é DELTA”, sem contrato S0 sobre prioridade de retificação | Expor duas fontes/retificação com conflito para revisão; NÃO aplicar A arbitrariamente. | [R] política de precedência |
| EX-06 | Não há evento de fechamento humano autenticado | F03 não autorizada; nenhuma ficha ou outro efeito. | [P] |
| EX-07 | Snapshot até msg07, depois novo inbound msg08 antes de aplicar extração | Rejeitar resultado obsoleto, preservar versão e informar necessidade de novo snapshot/fluxo S0; não sobrescrever correção humana. | [P/R] |
| EX-08 | Cliente pede humano durante IA, ocorre handoff, operador encerra depois | `sales_reply` e voz da IA ao cliente continuam bloqueadas; F03 interna com fechamento válido pode analisar/extrair. | [P] |
| EX-09 | Cliente manifesta interesse e aguarda futura remessa, mas NÃO há confirmação bancária de pagamento/venda | `NEGOTIATION_READY_FOR_BANK_HANDOFF` como *avaliação conversacional candidata*; preparar/encaminhar apenas por S0; nunca `vendido`. | [P/R] transição |
| EX-10 | Conversa encerrada inconclusiva: cliente diz “talvez volte no próximo mês” | F03 sugere necessidade possível de acompanhamento e motivo/fonte; compromisso de data fica ambíguo, sem dia/hora inventado e sem agenda escrita. | [P] |
| EX-11 | Operador Prumo ativo/atribuído solicita cadeia; S0 fornece templates fictícios aprovados `TPL_A@1`, `TPL_B@2`, `TPL_FINAL@1` e faixa 2–5 | F02 propõe tentativa(s) dentro de allowlist, final **separado** e horário permitido; **nova** cadeia pós-humana, sem retomar plano cancelado ou falar com cliente. | [P/R] elegibilidade |
| EX-12 | Operador escolhe somente `TPL_A@1`, sem pedir cadeia IA | Não gerar chamada F02; S0 decide intenção Meta de template único sob C04/versões. | [P] |
| EX-13 | Após handoff humano há opt-out explícito ou template fora do catálogo | Nenhum plano executável; tentativa/agenda inválida rejeitada por S0. | [P/V] |
| EX-14 | Template final técnico só `accepted/queued/uncertain`, não `sent` confiável | Não iniciar temporizador C09; nenhuma transição `perdido`. | [P/R/V] |
| EX-15 | Stub informa template FINAL `sent` verdadeiro +24h sem inbound, mas caso em `cadastro enviado ao banco` | C09 proibido; `perdido` não pode ser inferido por silêncio. Recusa bancária exigiria prova/ato humano. | [D/R] |
| EX-16 | Mesmo FINAL `sent` +24h sem inbound, caso em `em atendimento pelo operador`, porém matriz de elegibilidade C09 ainda não homologada | A IA não marca `perdido`. Stub registra `PENDING_S0_DECISION`; somente quando status/fase e regra forem ratificados S0 será possível esperado de transição por silêncio. | **BLOQUEADO [R]** |

## 3. Ilustração de um retorno F03 sem execução

```json
{
  "operation_kind": "human_close_extract",
  "contract_version": "s0-openai.v0.2-candidate",
  "request_id": "req_demo_02",
  "closure_event_id": "close_demo_02",
  "snapshot_hash": "hash_demo_02",
  "form_version_observed": 1,
  "fields_proposed": [
    {"field_code":"campo_req_A","proposed_value":"ALFA","source_message_refs":["msg01"],"source_kind":"client_statement","certainty":"explicit"},
    {"field_code":"campo_opt_B","proposed_value":"BETA","source_message_refs":["msg01"],"source_kind":"client_statement","certainty":"explicit"}
  ],
  "missing_fields": [{"field_code":"campo_req_C","reason_code":"NOT_STATED"}],
  "conflicts": [],
  "conversational_assessment": {"conversation_outcome":"NEEDS_CLARIFICATION","reason_code":"REQUIRED_FIELD_MISSING","evidence_message_refs":[]},
  "followup_need_advisory": {"suggested":"NO","reason_code":"ESSENTIAL_DATA_MISSING","evidence_message_refs":[]}
}
```

**OBS:** nem `NEEDS_CLARIFICATION` nem `suggested=NO` são códigos canônicos aprovados; essa representação candidata somente exemplifica a separação F03/F02. **S0 calcula a essencialidade**, valida campo e motivo, e exibe um handoff interno seguro com códigos legíveis do catálogo. F03 não publica WhatsApp nem cria cadeia, ficha ou status.

## 4. Condições para sair de [P/R] e criar fixtures executáveis E04

1. S0 e OpenAI homologarem a assinatura F03/F02 (nomes, versão, tipos, recusas, snapshots, fontes, idempotência) na issue #4.
2. S0 ratificar a extensão de C09 por status/fase, especialmente se `cadastro enviado ao operador` é elegível; Meta confirmar prova de `sent` e janela inbound; coordenação issue #6.
3. Responsável aprovar rubricas/thresholds E02 antes de usar os resultados como aceite. Em laboratório, usar somente catálogo e falas fictícias; dados reais ainda [V].
4. Para cada caso executável: fixar `input`, `expected`, `actual`, `case_id`, `test_version`, `commit` e prova de execução. Até então, **EX-01..16 são 16 descrições de teste, zero testes implementados e zero resultados**.

**Escopo desta entrega:** documentação para revisão e transição; não programação, deploy, merge, API real, n8n, Supabase, Meta ou gastos.
