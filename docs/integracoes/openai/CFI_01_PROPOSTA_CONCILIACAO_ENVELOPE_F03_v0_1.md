# CFI-01 — Proposta de conciliação do contrato F03 S0 ↔ OpenAI | v0.1

> **AVISO DE PRECEDÊNCIA — AUDITORIA DA FRENTE OPENAI, 22/10/2026.** Este documento anterior permanece preservado como **contrato candidato/histórico**; trechos conflitantes **NÃO são a direção funcional vigente**. Ler primeiro [AL-IA-00 — índice e precedência](./ALINHAMENTO_2026_10_22_00_INDICE_E_PRECEDENCIA_v0_1.md), [AL-IA-01 — jornada](./ALINHAMENTO_2026_10_22_01_JORNADA_F01_F02_F03_v0_1.md), [AL-IA-04 — deltas](./ALINHAMENTO_2026_10_22_04_RASTREABILIDADE_DELTAS_PENDENCIAS_v0_1.md), [AL-IA-07 — dependências entre frentes](./ALINHAMENTO_2026_10_22_07_DEPENDENCIAS_RELEVANTES_OUTRAS_FRENTES_v0_1.md) e [AL-IA-08 — auditoria documental](./ALINHAMENTO_2026_10_22_08_AUDITORIA_FECHAMENTO_DOCUMENTAL_FRENTE_OPENAI_v0_1.md). O texto abaixo documenta o estado de sua data original, **sem emendar código, criar autorização S0, nem corrigir documentação de outras frentes**.
>
> **Atenção especial:** o envelope descrito foi proposto antes do alinhamento de histórico lógico F03 por cliente/concessionária até o corte e sem correção cadastral pelo Consultor; não interpretar proposta de hash/versão do caso atual como contrato suficiente para todos os históricos, mídias e fechamentos recorrentes. Ratificação interfrentes S0↔OpenAI ainda pendente.


**Data:** 18/10/2026 | **Estado:** [P] proposta de assinatura e mapa de migração, **NÃO interface canônica homologada**. Aceites S0 e OpenAI pendentes [R]; frontend revisa apenas a projeção UI↔S0; privacidade Banco/Meta/LGPD [V]. Coordenar em [issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4) e [CF-OP-02 issue #6](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6). Não alterar PRs de outras frentes.

## 1. Escolha técnica candidata, não homologação

Como referência única de mapeamento **para revisão**, adotar terminologia primária já documentada no **OAI-05** para a porta F03: operação `human_close_extract`, `closure_event_id`, `conversation_snapshot_hash`, `allowed_fields_catalog_version`, `fields_proposed[]`, `field_code`, `proposed_value`, `source_message_refs[]`, `missing_fields[]` e `conflicts[]`. A escolha simplifica a apresentação, **não obriga S0/Frontend a adotá-la**. O evento humano e o snapshot reais permanecem propriedade S0.

### Mapa explícito E01 → nomenclatura candidata OAI-05

| E01 v0.2 | Proposta OAI-05 v0.1 | Regra |
|---|---|---|
| `trigger_ref` | `closure_event_id` | Referência ao evento AUTORIZADO de conclusão humana; S0 gera/valida; sem aceitar evento arbitrário do navegador |
| `scope.concessionaria_ref`, `caso_ref`, `conversa_ref`, `ciclo_ref` | `concessionaria_id`, `caso_id`, `conversa_id`, `ciclo_id` | Preferir IDs opacos planos sob resolução por S0; estrutura/nome final [R] |
| `expected_case_version` | `expected_version` | Versão do caso; registrar separadamente `current_form_version` / versão da ficha |
| `authorized_context_ref` / `context_version` | `conversation_snapshot_ref`, `conversation_snapshot_hash`, `message_watermark` | Snapshot autenticado e corte; não confundir hash com política de autorização |
| `fields_policy_version` | `allowed_fields_catalog_version` | Catálogo de campos e sensibilidade aprovado por S0; não inventar requisitos LiberaCred |
| `extraction.field_suggestions[]` | `fields_proposed[]` | Mesmo conceito lógico: sugestões sem efeitos |
| `field_key` / `value` | `field_code` / `proposed_value` | Nunca receber código fora do catálogo nem inferir valores ausentes |
| `evidence_refs[]` | `source_message_refs[]` | Provas que S0 revalida no mesmo caso/loja e autoria da mensagem |
| `missing_field_keys[]` | `missing_fields[]` | Com `reason_code`; essencialidade calculada SOMENTE com catálogo S0 |
| `needs_human_clarification` | Derivado por S0 a partir de campos essenciais/conflitos + policy | Não tratar booleano sugerido pela IA como ordem de fila |
| `proposed_effect=validate_then_apply_by_s0` | Remover da saída executável; efeito sempre via S0 | Não oferecer comando de DB à IA |
| `warnings[]` | `extraction_warnings[]` | Diagnóstico controlado, sem mensagens pessoais em logs |
| OAI-07 `conversational_assessment` | Bloco complementar `conversational_assessment` [P] | Resultado conversacional, NÃO status nem prova bancária |
| OAI-08 `followup_need_advisory` | Bloco complementar `followup_need_advisory` [P] | Sugestão silenciosa; pedido F02 **SEPARADO** somente se S0 autorizar |

**Pontos que exigem aceite conjunto:** nome físico do evento (`atendimento_humano_concluido` / `human_conversation_completed`), assinatura do comando Frontend→S0, formato do snapshot, autenticação interna, `expected_version` vs. versão específica de cadastro, tipos/validação por campo, classe D3 e política de retorno após inbound novo.

## 2. Exemplo do envelope candidato F03 — somente dados fictícios

```json
{
  "contract_version": "s0-openai.v0.2-candidate",
  "request_id": "req_demo_001",
  "operation_kind": "human_close_extract",
  "concessionaria_id": "loja_demo_A",
  "caso_id": "caso_demo_1",
  "conversa_id": "conversa_demo_1",
  "closure_event_id": "closure_demo_1",
  "message_watermark": "msg_demo_10",
  "conversation_snapshot_hash": "snapshot_hash_demo",
  "conversation_snapshot_ref": "snapshot_autorizado_demo",
  "expected_version": 14,
  "current_form_version": 4,
  "allowed_fields_catalog_version": "catalogo_demo_v1",
  "policy_versions": {"prompt": "demo_p1", "privacy": "demo_priv1"},
  "authorized_context_ref": "ref_minima_demo",
  "deadline_ref": "prazo_backend"
}
```

`authorized_context_ref` é opção candidata de gateway interno; se o adaptador receber `messages[]`, esses trechos só poderão ser materializados depois da validação e minimização da S0. Referências não contêm CPF, telefone ou segredos. O modelo não cria nem autentica `closure_event_id`. Nenhum endpoint físico é afirmado.

## 3. Exemplo da resposta composta F03 — somente dados fictícios

```json
{
  "contract_version": "s0-openai.v0.2-candidate",
  "request_id": "req_demo_001",
  "operation_kind": "human_close_extract",
  "closure_event_id": "closure_demo_1",
  "snapshot_hash": "snapshot_hash_demo",
  "form_version_observed": 4,
  "outcome": "PARTIAL",
  "fields_proposed": [{
    "field_code": "CAMPO_EXEMPLO_01",
    "proposed_value": "VALOR_DEMONSTRATIVO",
    "source_message_refs": ["msg_demo_03"],
    "source_kind": "client_statement",
    "certainty": "explicit"
  }],
  "missing_fields": [{"field_code": "CAMPO_EXEMPLO_02", "reason_code": "NOT_STATED"}],
  "conflicts": [],
  "conversational_assessment": {
    "conversation_outcome": "INCONCLUSIVE",
    "reason_code": "AWAITING_CUSTOMER_FOLLOWUP",
    "evidence_message_refs": ["msg_demo_08"]
  },
  "followup_need_advisory": {
    "suggested": "YES",
    "reason_code": "INCONCLUSIVE_WITH_FUTURE_COMMITMENT",
    "evidence_message_refs": ["msg_demo_08"],
    "commitment_date_candidate": null,
    "date_ambiguity": "FUTURE_MONTH_WITHOUT_DAY"
  },
  "extraction_warnings": []
}
```

O exemplo NÃO implica que a política de data aceita ou recusa estes enums: **enum/schema, validação de datas, `outcome` e compatibilidade com OAI-07/OAI-08 estão [P/R]**. Os nomes e valores demonstrativos não são campos bancários. A IA jamais devolve a classe final `required_for_bank_submission` como verdade; S0 calcula a partir do catálogo e das regras externas.

**Sem efeito colateral:** S0 valida isoladamente campos e propostas, persiste somente valores permitidos, classifica o resultado técnico/comercial, decide se encaminha a humano ou se precisa um pedido distinto `recontact_plan`. O exemplo `suggested=YES` NÃO cria plano nem autoriza template. Em situação de venda bancária alegada, nenhuma resposta promove `vendido`. `cadastro enviado ao banco` depende de remessa comprovada.

## 4. Contrato separado da Planejadora F02 [P/R]

Entrada lógica: `planning_request_ref`, `concessionaria_id`, `caso_id`, `initiator` (`operator|post_human_assessment|ai_flow`), `owner_route` (imposto por S0: `human|seller_ai`), `allowed_template_catalog_version`, `eligible_template_refs[]`, `attempt_min/max`, `allowed_windows[]`, `policy_version`, `expected_case_version`, compromissos explícitos e fontes minimizadas.

Saída lógica: `proposed_attempts[]` com `template_id`/`template_version`/`scheduled_at`/`evidence_refs[]`, `final_template_candidate` SEPARADO, erros/ambiguidades e usage sem PII. Para cliente já atendido e silencioso, referência de **2–5 tentativas e template final separado** conforme ATD-01B, sujeitos a elegibilidade e aceite S0 [R/V]. Pedir template único pelo operador é S0→Meta e NÃO depende de OpenAI. Plano da IA anterior cancelado no handoff NUNCA pode ser retomado por reutilização de ID.

**Regra de roteamento:** após handoff, resposta à cadeia vai ao operador humano atual autorizado, mesmo se outro profissional foi redistribuído legitimamente; caso ainda sob IA sem handoff pode voltar à IA quando elegível. OpenAI não identifica ator pelo texto da conversa.

## 5. Três relógios e C09 (NÃO resolver regra S0 nesta branch)

1. **Janela Meta:** +24h desde último inbound real do cliente; apenas regra de canal. Template outbound NÃO abre janela de texto livre.
2. **Conclusão humana:** ato técnico do operador; inicia F03 e não encerra automaticamente o caso comercial nem o prazo Meta.
3. **Silêncio pós-template final:** +24h a partir de prova efetiva de `sent` do último template elegível e separadamente aprovado; se não houver inbound, S0 verifica status/ciclo, opt-out, concorrência e demais guardas. **Somente S0** pode propor/efetivar `perdido` por silêncio de caso pré-banco ELEGÍVEL, conforme emenda CF-OP-02 a ratificar.

**NUNCA C09 por silêncio em `cadastro enviado ao banco`, `vendido`, `perdido` histórico.** O estado `cadastro enviado ao operador` ainda [R] e não é implicitamente elegível. Recusa definitiva do Banco é fluxo separado, comprovado e humano, jamais silenciamento de template.

## 6. Bloqueios, testes e critérios de aprovação

- **Assinatura:** S0 e OpenAI validam nomes, versão, tratamento da falta de dados e fontes, código de recusa/erro, `followup_need_advisory`; Frontend avalia apenas payload/projeção do S0, nunca se conecta ao adaptador OpenAI.
- **Concorrência:** snapshot com resposta nova, correção humana ou mudança de responsável → rejeitar resultado obsoleto e revisar autorização; não retransmitir automaticamente por novo responsável.
- **Segurança:** cross-tenant e opt-out; Data D3 apenas sob finalidade/validação [V]; sem SQL/Meta/MCP como tools; logs e custos sem PII.
- **Aceite:** revisão em issue #4 com evidência de aceite S0 e OpenAI, atualização de referências OAI-01/E01/OAI-05/OAI-08 e documentação de compatibilidade. Somente depois escrever fixtures executáveis do envelope acordado e refletir na UI.
- **Dependência externa:** norma de C09 ampliado, concorrência template individual versus cadeia, elegibilidade por status e prova de `sent` continuam com S0/Meta/CF-OP-02 e NÃO podem ser resolvidas por escolha de campo OAI.

**Estado no momento da publicação:** proposta de conciliação pronta para revisão [P/R]. Zero testes, endpoints, credenciais, chamadas, merges ou liberações operacionais. Não alterar percentual global 19F.
