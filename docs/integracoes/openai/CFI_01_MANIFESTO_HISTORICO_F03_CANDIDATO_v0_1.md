# CFI-01E v0.1 — Manifesto de evidências F03, corte e revalidação [P/R]

**Data:** 22/10/2026. **Natureza:** especificação **documental candidata** para submissão à S0 e OpenAI. NÃO corresponde a schema físico, tabela, API, função pronta, autorização de envio ao provedor ou teste executado. Proposta subordinada a AL-IA-01, OAI-05/E01 v0.3, CFI-01 v0.3 e S0 PR #12.

## 1. Por que o recibo atual não basta

A S0 demonstrou em laboratório privado `closure_event_ref`, `store_ref`, `case_ref`, `assignment_ref`, `expected_cycle_version`, `snapshot_sha256`, `message_watermark` e `message_count`. Esse recibo autentica o **evento e recorte físico original de encerramento**; não identifica por si só todo o histórico do mesmo cliente na mesma concessionária, nem autoriza leitura de mídia, terceiros, versões de ficha/catálogo ou envio a OpenAI. **Preservar o recibo; estender a evidência sem fingir que seus campos já possuem nova semântica.**

## 2. Duas camadas de prova — separadas

**Camada A — Recibo atômico S0 existente:** identificar e revalidar o fechamento humano legítimo, sua autoria/concessão, integridade, chave de idempotência, momento e cutoff **do contexto já suportado**. Os valores de PR #12 devem permanecer sob domínio e credenciais S0.

**Camada B — Manifesto histórico candidato:** S0 resolve **identidade do cliente dentro da loja** e o **conjunto lógico dos registros** admissíveis (incluindo casos anteriores e eventos de diferentes consultores) desde a origem na plataforma **até o cutoff daquela conclusão**. Define uma ordenação determinística, IDs por origem, versões/proveniência, vínculo da pessoa/loja, quem falou, tipo de evento/mídia, classificação de privacidade e tratamento de indisponibilidade. Atesta seleção por hash/versão sem reescrever recibos anteriores. O mecanismo de seleção, hash, guarda de PII e assinatura dessa camada **não estão homologados**.

Camada B **não** implica disponibilizar tudo em um único prompt; recuperação parcial precisa comprovar que não omitiu fonte essencial, que fontes podem ser revisitadas, que status de evidência é conhecido e que material de outra concessionária jamais entrou. Se item não está mais legalmente disponível, retornar `unavailable/retention` com contexto permitido, **não** inventar transcrição.

## 3. Estrutura conceitual para decisão, não para execução [P/R]

| Campo lógico candidato | Papel | Condição e bloqueio |
|---|---|---|
| `contract_version` e `request_id` | Correlação de uma operação específica | Um retry não cria segundo efeito |
| `tenant_ref`, `person_ref`, `case_ref` | Escopo multi-tenant e identidade resolvida S0 | Telefone/CPF digitados não substituem resolução antifraude |
| `closure_event_ref`, `closure_cutoff_ref`, `cutoff_at` | Evento humano e último instante permitido | Não incluir evento criado **após** corte, nem voltar no tempo para mutar versão atual |
| `s0_atomic_receipt_ref` | Referência **interna S0** à Camada A | Não entregar assinatura HMAC, nonce, token ou recibo privado ao modelo |
| `history_manifest_ref`, `manifest_version`, `history_digest` | Camada B; seleção lógica e integridade | Necessita autorização/transação S0, critérios de ordenação e minimização |
| `evidence_index[]` | IDs opacos por mensagem/evento/documento, origem, autoria, tempo e disponibilidade | Só metadados autorizados; referências de B são bloqueadas |
| `authorized_content_ref` ou `authorized_chunks[]` | Recorte mínimo para análise do modelo | Bytes e URLs temporárias somente após revisão de finalidade/retenção |
| `form_version`, `catalog_version`, `cycle_version`, `case_version` | Controle de concorrência por domínio | **Não** inferir uns dos outros; campos físicos pendentes |
| `policy_version`, `instruction_version`, `consent_scope` | Rastrear autorização e mudança de regras | Revogação ou versão não elegível nega consulta/aplicação |
| `media_access_status` | Proveniência e acesso autorizado multimodal | Conteúdo faltante ⇒ não reconstruir nem considerar ouvido/visto |
| `execution_status` e `error_code` | Resultado de geração, erro ou recusa | Não confundir `EXTRACTED` com `APPLIED` ou estado comercial |

IDs, tipos, formato de digest, ordem total, consentimento e flags finais são **[R/V]**. Este mapa não pode alimentar diretamente `S0CFI01F03ReceiptBridgeLocal` de PR #12.

## 4. Exemplo inteiramente fictício de manifesto **lógico**, não payload de API

```json
{
  "kind": "f03_history_manifest_CANDIDATE_NOT_API",
  "tenant_ref": "LOJA_FAKE_A",
  "person_ref": "PESSOA_FAKE_01_RESOLVIDA_S0",
  "closure_event_ref": "FECHO_FAKE_02",
  "case_ref": "CASO_FAKE_02",
  "cutoff_marker": "MSG_FAKE_2026_10_22_07",
  "s0_atomic_receipt_ref": "INTERNO_S0_NAO_TRANSMITIR",
  "manifest_version": "M1_FICTICIA",
  "history_index": [
    {"ref": "MSG_FAKE_2026_05_02_01", "case": "CASO_FAKE_01", "author_role": "cliente", "kind": "texto", "summary": "renda = 3000"},
    {"ref": "MEDIA_FAKE_2026_06_02_01", "case": "CASO_FAKE_01", "author_role": "cliente", "kind": "audio", "access": "NAO_DISPONIVEL"},
    {"ref": "MSG_FAKE_2026_10_22_07", "case": "CASO_FAKE_02", "author_role": "cliente", "kind": "texto", "summary": "corrigindo: renda = 3500"}
  ],
  "form_version_CANDIDATE": "V_FAKE_04",
  "catalog_version_CANDIDATE": "CAT_FAKE_01"
}
```

O exemplo demonstra **intenção de campos**, não suas permissões: não autoriza resumo de PII, exportação ao modelo nem aceite de retenção. Evento posterior `MSG_FAKE_2026_10_22_08` está **excluído** do manifesto daquele fechamento; outra conclusão legítima pode produzir manifesto diferente. Áudio indisponível não é transcrição inventada. Em produção, até o uso do campo `summary` do exemplo requer minimização e revisão.

## 5. Contrato de **resposta** F03 e gate de validação

Propor em blocos distintos: `fields_proposed[]` (código de catálogo, valor, fonte real de tenant, autoria, certeza e versões), `missing_fields[]`, `conflicts[]`, `conversational_assessment`, `commercial_transition_advisory`, `followup_need_advisory`, `unavailable_evidence[]` e `errors[]`. **Não permitir** transição `vendido` nem falsa prova de remessa/negativa do Banco. Desistência explícita pode gerar proposta de `perdido` sujeita a política/transição S0.

**Validação em duas fases não fungíveis:**
1. **Validade histórica:** S0 identifica fechamento autêntico, prova tenant/cliente/cutoff, fonte e versão da análise; uma nova mensagem não muda o passado.
2. **Aplicabilidade atual:** antes de uma eventual mutação, S0 revalida concessão, atribuição, identidade, estado/ciclo/caso/ficha/catálogo, proveniência, concorrência, snapshot de remessa e guarda de idempotência. Se o resultado for stale/denied, pode manter o registro analítico histórico, **sem gravar dados atuais**.

**Falhas:** mídia indisponível, fonte conflitante, tipo inválido, campo opcional ausente, falha em identidade, versão revogada e retry recebem estados técnicos distintos sob schema a decidir. Falha de extração reiterada é incidente técnico, não concessão de edição pelo Consultor.

## 6. Perguntas de ratificação com alternativas e consequências

1. **Manifesto multi-casos:** atestar a seleção com digest/versão composta versus outra prova equivalente? S0 deve definir método; não reutilizar `snapshot_sha256` de conversa atual como se fosse de anos de histórico.
2. **Cutoff global:** usar sequência/instante S0 + desempate estável de eventos de **vários casos**? Se evento chega atrasado, regra de inclusão/recebimento precisa ser formalizada, sem transformar relógio Meta em critério de encerramento.
3. **Identidade de vários telefones:** qual evidência de vínculo permite fusão na mesma loja e quem aprova? Sem prova, impedir a associação.
4. **Mídia:** reter cópia/transcrição/metadado, prazo e consentimento? Se não autorizada/disponível, não expor conteúdo ao provedor.
5. **Atualização concorrente:** quais versões reais compõem o preflight e como revalidar na transação APPLY? `expected_cycle_version` não cobre sozinho ficha/catálogo.
6. **Vista FV:** como acompanhar `PENDING/EXTRACTED/REVIEW_REQUIRED/APPLIED/DENIED` sem fingir que IA escreveu ou liberar edição ao Consultor?
7. **Erros/refusal:** quais motivos detalhados podem ir à UI/log sem vazar dado financeiro/PII?

**Saída desta proposta:** levar [CFI-01 v0.3](./CFI_01_CONCILIACAO_PONTE_F03_INTERFRENTES_v0_3.md) e perguntas acima para os donos S0/S1/FV/Meta/privacidade. Não transformar isto em desenho já aceito, nem abrir E04 por “prossiga”.

## 7. Gabaritos E02 vinculados

`SYN-06/07/08/09/10/14/15/32/33/34/35/36/37/38/39/41/42/69`: tenant, recibo, duas versões, histórico multi-casos, separação cutoff/commit, mídia, campos e identidade. Ver matriz E02 v0.3; nenhum deles foi executado.
