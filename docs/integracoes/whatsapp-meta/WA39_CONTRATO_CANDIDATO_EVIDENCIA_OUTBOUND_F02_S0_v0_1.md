# WA-39 — Contrato candidato de evidência outbound Meta → S0 → F02

**Status:** PROPOSTA / revisão pela OpenAI e S0/S1. **Solicitação origem:** [Issue #9 — OpenAI→Meta](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9). **Data:** 31/10/2026. **NÃO homologado**, não é endpoint, instrução de Graph, autorização de envio ou de mudança comercial.

## 1. Responsabilidades e fronteiras

- **S0/S1:** única fonte autoritativa da loja/canal, intento, caso, cadeia F02, tentativa, template+versão, evento final, consentimento, elegibilidade e qualquer efeito WDC-13/C09. Só S0 pode aplicar estados comerciais ou contar falhas na cadência.
- **Meta:** observa resultado Graph e callback Meta, valida HMAC de um POST original pelo segredo confiado por App, vincula ocorrências por identidade e escopo, produz **proposta de evidência técnica**. Não infere envio de uma resposta API 2xx, nem confere privilégio S0.
- **OpenAI/F02:** recebe somente projeção minimizada, autorizada e versionada **após** conciliação da S0. Pode replanejar se houver pedido expresso competente; nunca envia, cria templates ou aplica perda.
- **Infra:** operação, segredo, rota, resiliência, chave de recibo e autorização HTTP são separadas dos modelos candidatos. A [#2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2) permanece a única demanda de ACK/ingresso.

## 2. Evidências distintas — não colapsar

| Dimensão | Origem | O que pode significar | O que NÃO significa |
|---|---|---|---|
| Resultado Graph `API_ACCEPTED` | Resposta HTTP a tentativa de envio | API aceitou processar pedido com `wamid` validado quando aplicável | Não é `sent`, `delivered`, cliente ativo, janela C09, grant de novo envio ou sucesso bancário. |
| `UNKNOWN` / timeout / erro externo incerto | Transporte Graph | Requer conciliação autorizada | Não é falha definitiva, reenviar automaticamente, nem cancelar cadeia. |
| Callback Meta `sent` | POST Meta com HMAC verdadeiro e canal confiado, posteriormente vinculado ao intento S0 | Candidato a evidência de envio técnico **somente após readback e correlação S0** | HMAC isolado não prova tentativa/cadeia nem persistência. |
| Callback `delivered` / `read` | Mesmo vínculo técnico | Progresso técnico observado e correlacionado, com histórico imutável | Não é decisão comercial nem leitura humana na UI. |
| Callback `failed` | Mesmo vínculo + erro Meta | Candidato a falha técnica, que precisa de classificação definitiva correlacionada na tentativa correta | Não é automaticamente desinteresse, perda, interrupção F02 ou segunda falha consecutiva. |
| Código `131049` | Erro técnico da Meta, contexto/versionamento do provedor | Diagnóstico técnico a preservar sem segredos | Não é desistência nem limite universal de mensagens/24h. |
| Recibo S0 durável e vínculo | Serviço S0 autorizado | Resultado de persistência, idem/correlação, revisões e progresso reconhecido pela S0 | Não constitui automaticamente ACK HTTP ou envio; a autoridade depende de contrato ratificado. |

## 3. Dados candidatos, por camada (não API real)

**3.1 Origem/autorização S0 da tentativa** (referência interna, não entregue ao cliente)
`concessionaria_id`, `canal_id`, `meta_app_ref`, `meta_waba_id`, `phone_number_id`, `case_ref`, `flow_ref`, `plan_ref`, `attempt_ref`, `intent_ref`, `template_ref`, `template_version_ref`, `is_final_template` e `authorization_revision`. S0 deve definir tipos e estabilidade desses nomes, vínculos e versão do contrato. Referências não são prova de autorização por si.

**3.2 Observação Meta técnica** (sem efeito comercial)
`provider_message_id` (`wamid` quando válido), `attempt_ref` / `correlation_ref` após resolução confiável, `event_kind` (`GRAPH_RESPONSE` ou `STATUS_CALLBACK`), `provider_status`, `provider_error_code/subcode` saneados, `event_timestamp`, posição do evento no lote físico, identificador de lote e digest dos bytes originais. Regra: **não usar só `wamid` ou um timestamp como chave global de pessoa/loja**. Não transportar conteúdo de mensagem, token, telefone em claro, mídia privada ou HMAC para a F02.

**3.3 Resultado de conciliação S0** (candidato à futura resposta interna F02)
`evidence_version`, `attempt_ref`, `flow_ref`, `plan_revision`, `template_version_ref`, `is_final_template` com fonte S0, `correlation_state` proposto:
- `PENDING_CORRELATION`: callback técnico observado mas tentativa/autenticidade interna não provada;
- `CORRELATED_SENT`: evidência `sent` formalmente vinculada à tentativa;
- `CORRELATED_DELIVERED` e `CORRELATED_READ`: progresso técnico correlacionado;
- `CORRELATED_DEFINITIVE_FAILURE`: falha definitiva comprovada para a tentativa;
- `UNCERTAIN`, `CONFLICT`, `QUARANTINED`: nenhuma inferência automática de sucesso/falha.

**Esses rótulos são PROPOSTOS.** S0 e OpenAI devem confirmar se são suficientes ou optar por um contrato versionado diferente. Nenhuma saída contém `send_authorized:true`, `case_transition_authorized:true` nem `production_authorized:true` pela própria Meta.

## 4. Estados e regras invariantes

1. Um callback só é consumível após autenticação do POST original pelo segredo da App, vínculo App/WABA/número/canal/tenant autoritativo e tentativa S0, com deduplicação por **ocorrência**, preservando ordem e contradições. Mesmo `wamid` não é uma pessoa nem equivale a duas tentativas.
2. Reordenação `read` antes de `sent`, duplicações exatas e relatórios tardios não reescrevem histórico anterior. Divergência de evento/escopo gera `CONFLICT`/quarentena para S0; callback ausente não vira `failed`.
3. **WDC-13:** duas falhas **definitivas correlacionadas, em tentativas consecutivas da mesma cadência**, provocam efeito **apenas na S0**, sem IA. Um `sent` comprovado da tentativa seguinte zera a sequência, mesmo sem resposta do cliente. `API_ACCEPTED`, `UNKNOWN`, timeout e ACK não contam como `sent` ou falha.
4. **C09:** só `sent` comprovado do **template final** pode subsidiar a janela pós-humano de 24h, após avaliação S0 de elegibilidade. Não confundir com a janela de atendimento Meta de 24h desde o último inbound, nem com conclusão humana.
5. Falhas de template **pausado/rejeitado** do catálogo e falha técnica de **envio** são fluxos distintos (WDC-12). F02 não recebe chamada por falha normal de entrega; apenas S0 pode solicitar planejamento/replanejamento autorizado.
6. Não declarar `sent` por retropropagação inferida de `delivered` ou `read` sem regra explícita ratificada. Tratar sinais contraditórios por critério formal de conciliação S0.
7. Escopo de opt-out é concessionária; nenhuma nova mensagem inbound concede opt-in. No envio, todos os gates são rechecados pela S0 conforme a [#10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10).

## 5. Testes mínimos propostos antes de aceite

- Positivo: tentativa S0 cadastrada e Graph `API_ACCEPTED` seguida de HMAC Meta válido `sent`, `wamid` e canal correspondentes — produzir evidência correlacionada sem transição comercial na Meta.
- Negativos: App diferente, tenant diferente, `wamid` não correspondente, tentativa/versão revogada, HMAC inválido, mesmo evento divergente, erro Meta desconhecido, falha não definitiva, API_ACCEPTED sem callback e timeout após possível envio.
- Ordem/convergência: duplicado exato, `read` antes de `sent`, falha tardia, erro `131049`, `sent` intermediário que zera WDC-13 e duas falhas consecutivas sem `sent` entre elas.
- Evento final: template final declarado exclusivamente pelo plano/tentativa S0 atual; um `sent` de template anterior não abre C09.
- Concorrência e disponibilidade: retorno perdido S0, readback, binding stale, mudança de concessão, reprocessamento, no double count, no Graph auto-retry; minimização de dados à F02.

## 6. Base já implementada, lacunas e encaminhamento

**Candidatos offline existentes (reutilizar, não duplicar):** `status-evidence.ts`, `technical-reconciliation.ts`, `cloud-wire-observation.ts`, `wa31-late-evidence-classifier.ts`, `wa32-signed-status-s0-forensic-bridge.ts`, `wa35-signed-ingress-handoff-fixture.ts`. A última suíte auditada M07/M08 passou em [CI 41194019498](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41194019498), com 1.210 testes Meta e 18 checks físicos PG17. **Isso não comprova o presente contrato outbound em ambiente real.**

**Lacunas:** identidade de serviço S0, schema/versionamento da projeção F02, assinatura/readback de estado técnico, fonte de `is_final_template`, mídia/PII, callbacks reais, Graph real, custódia e implantação. **Sem licença para implementar esses serviços fora da frente autorizada.**

**Próximo passo:** Meta revisa as invariantes de transporte com a OpenAI na [#9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9) e encaminha a parte de prova persistida/autorização à S0/S1. Qualquer implementação exige missão explícita e separação de responsabilidades. M19 e M20 permanecem pendentes.
