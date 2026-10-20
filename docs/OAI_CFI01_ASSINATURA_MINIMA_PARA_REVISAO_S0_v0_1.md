# OAI-05/OAI-07 — assinatura mínima para revisão S0, v0.1 [P/R]

**20/10/2026. Somente proposta de conciliação**, não é endpoint, schema homologado, migração, contrato vigente ou chamada de serviço. Fonte de comparação: `S0_OAI_CFI01_CONCILIACAO_IMPLEMENTAVEL_2026_10_20.md`; issue #4 CFI-01 e #6 CF-OP-02. Nada deve ser executado sem assinatura da S0/OpenAI/FV e políticas Banco/LGPD.

## 1. Comando lógico navegador → S0, distinto de operação de IA

O navegador solicita **somente** `case_ref`, `expected_case_version` e `idempotency_key` (mais token da sessão pela camada autenticada do S0). Ator, loja, atribuição, status, `closed_at`, catálogo, cutoff, prova bancária e política **NÃO são controlados pelo navegador**. S0 identifica loja/caso e verifica GoTrue, sessão atual, grant/atribuição de acordo com a regra S1, versão e escopo. O retorno imediato `ACCEPTED_FOR_PROCESSING` nunca significa `APPLIED`.

## 2. Envelope mínimo S0 → OpenAI F03 (nome de campo candidato)

```json
{
  "operation_kind": "human_close_extract",
  "contract_version": "TO_BE_RATIFIED",
  "request_id": "req-sintetico-001",
  "closure_event_id": "close-sintetico-001",
  "scope": {
    "concessionaria_ref": "loja-sintetica-A",
    "caso_ref": "caso-sintetico-A",
    "ciclo_ref": "ciclo-sintetico-A"
  },
  "expected_case_version": 7,
  "form_version_observed": 3,
  "snapshot": {
    "snapshot_hash": "hash-sintetico",
    "message_watermark": "msg-sintetica-004",
    "authorized_messages_ref": "ref-efemera-s0"
  },
  "catalogue": {
    "allowed_fields_catalog_version": "cat-sintetico-01",
    "allowed_fields_policy_ref": "politica-sintetica-s0"
  }
}
```

**Essa é uma proposta de conciliação, NÃO mensagem pronta para a API.** S0 deve ratificar como referências de mensagens autorizadas serão resolvidas e minimizadas, quais campos elegíveis são fornecidos e se é necessário `closed_at` ou `conversa_ref` no envelope. Não enviar IDs reais, JWT de operador, payload D3/D4, telefone, CPF, prova bancária ou transcript completo por padrão. O adaptador recebe apenas recorte autorizado da mesma loja/caso. O `bank_submission_proved` permanece **fora do envelope do modelo**, como prova do domínio S0/Banco.

## 3. Saída mínima OpenAI → S0 (somente proposta; formato candidato)

```json
{
  "contract_version": "TO_BE_RATIFIED",
  "request_id": "req-sintetico-001",
  "closure_event_id": "close-sintetico-001",
  "snapshot_hash": "hash-sintetico",
  "form_version_observed": 3,
  "outcome": "PARTIAL",
  "fields_proposed": [
    {
      "field_code": "CAMPO_FICTICIO_01",
      "proposed_value": "VALOR_FICTICIO",
      "source_message_refs": ["msg-sintetica-003"],
      "source_kind": "client_statement",
      "certainty": "explicit"
    }
  ],
  "missing_fields": [
    {
      "field_code": "CAMPO_FICTICIO_02",
      "reason_code": "NOT_STATED"
    }
  ],
  "conflicts": [],
  "conversational_assessment": {
    "conversation_outcome": "NEEDS_CLARIFICATION",
    "reason_code": "NEEDS_INFORMATION",
    "evidence_message_refs": ["msg-sintetica-004"],
    "certainty": "explicit"
  },
  "followup_need_advisory": {
    "suggested": "UNCERTAIN",
    "evidence_message_refs": ["msg-sintetica-004"]
  }
}
```

**Todos os rótulos e valores são exemplificativos [P/R].** Nem `certainty=explicit` nem `source_message_refs` provam fato: S0 confirma conteúdo, autoria, escopo, catalogação, conflitos, retificações, classe sensível, versão, permissão e estágio bancário. Campos adicionais, `reason_code`, incerteza, tratamento de áudio, erro e limites precisam de JSON Schema canônico ratificado; a implementação offline atual **rejeita** blocos de lacunas/conflitos/advisory não vazios, portanto **NÃO aceita este exemplo composto como payload operacional**.

## 4. Decisões distintas de processamento e autoridade

- `PROPOSED/PARTIAL/NEEDS_REVIEW/FAILED`: somente estado da **resposta do modelo**; o frontend não usa isso para anunciar ficha atualizada.
- `DENIED/STALE/REVIEW_REQUIRED/REVIEW_ONLY`: resultado de **gates sintéticos**, não autorização para gravar.
- `ACCEPTED_FOR_PROCESSING`: prova apenas que a S0 aceitou o pedido técnico, não executou a extração.
- **`APPLIED`/commit de nova ficha**: só se a S0 comprovar transação, nova versão, autoria técnica e auditoria; caso contrário `PARTIAL`, `PENDING` ou falha técnica não alteram dados anteriores. Nomes físicos do estado técnico [R].
- Desfecho `CONTINUE_TO_BANK_REVIEW` é **conversacional**; ausência de remessa comprovada na S0 implica conferência humana, não iniciar C09/recontato comercial, venda ou negativa.
- `followup_need_advisory` é recomendação. Planejamento F02 requer **novo pedido idempotente S0 de finalidade/estágio autorizado**, e a eventual execução da cadeia fica no núcleo S0/Meta. A IA Vendedora jamais reabre após handoff.

## 5. Contrato de aceite dos proprietários (itens a assinar)

1. S0: identificador técnico de conclusão, origem/scope dos grants, regra da atribuição S1 (incluindo pausa intake e exceção por caso), operação autenticada e revalidação/locks.
2. S0/OpenAI: versão única de envelope/reply, lista fechada de reason codes, mensagens autorizadas/hash/cutoff, catálogo de campos e valor de `outcome` técnico.
3. S0/Banco: prova positiva de remessa/resultado, estritamente externa ao texto de WhatsApp.
4. S0/FV: estados técnicos de acompanhamento e confirmação de persistência, sem criar status comercial.
5. S0/Meta/OpenAI: gatilho de eventual cadeia pós-humana, C04, opt-out, C09 por fase, relógios e custo.
6. OpenAI: adaptação do parser offline **somente depois** da escolha canônica, com testes de `deny`/revogação/obsolescência e integração S0 em sandbox local.

**Até todos os gates relevantes estarem explícitos, este documento é somente proposta. Não autoriza conexão real, migração, deployment ou substituição de fixtures por booleanos não comprovados.**
