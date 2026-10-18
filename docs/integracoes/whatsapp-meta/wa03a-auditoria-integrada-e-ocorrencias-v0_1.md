# WA-03A — auditoria cruzada sintética do fluxo Meta (18/10/2026)

**Estado:** auditoria e regressão local com um reparo de isolamento **no simulador**. Não existe integração operacional Meta/Supabase. PRs #1 e #2 seguem Draft, sem merge/deploy. Uso proibido de números reais, tokens, webhook comercial concessionária de demonstração ou migrations hospedadas.

## 1. Escopo, fonte e precedência

Fontes lidas diretamente das branches no GitHub:

- PR #2: `inbound.ts` (HMAC + parsing), `durable-receipt.ts` (decisão estrutural de ACK), `graph-outbound.ts`, `graph-template.ts`, `offline-dispatch.ts` e `technical-reconciliation.ts`, mais seus testes.
- PR #1: `docs/S0_034B_AUDITORIA_CONTRATO_C07_WA01C_2026_10_18.md` e `docs/S0_035_COMPATIBILIDADE_AUTH_REST_2026_10_18.md`. A S0/034B **comprovou** que `registrar_callback_c07_sintetico` exige um ID artificial por ocorrência e que copiar `statuses[].id` colide; S0/030 limita a chave sintética a `message-id + status + timestamp`. O resultado S0/035 no Supabase **local** não autoriza a integração externa. Os módulos WA-01C/WA-02D continuam candidatos [P].
- Contrato compartilhado [S0 ↔ Meta](interface-compartilhada-s0-meta-v0_1.md), DEC-WA-01/02/03 [D] como diretrizes, DEC-WA-05 [D] somente titularidade por concessionária. DEC-WA-04/06 **pendentes**.

## 2. Falha de isolamento identificada e corrigida

**Achado de prioridade ALTA no laboratório (não em produção):** `FakeMetaStatusReconciler.projectionFor()` e `registerAcceptedSend()` usavam apenas App/WABA/emissor/`wamid` e destinatário para consultar ou reconhecer um vínculo preexistente; quando a referência trazia um `concessionaria_id` ou `canal_id` diferente, a projeção técnica ainda podia ser devolvida, e um novo vínculo podia ser classificado falsamente como `ALREADY_LINKED`.

**Prova pré-reparo:** testes adversariais `AUDIT-01..03` falharam **3/3**, com projeções indevidamente acessíveis para loja/canal divergentes e `ALREADY_LINKED` cruzado.

**Reparo na branch PR #2:** cada `LinkedSend` retém um snapshot do `TrustedTemplateScope` recebido da fixture. A decisão `ALREADY_LINKED` e a projeção `projectionFor` agora exigem igualdade exata de concessionária, canal, App, WABA e Phone Number ID, além dos controles anteriores. O escopo se mantém apenas simulado: **não valida a origem do `TrustedTemplateScope`, RLS, JWT ou autorização real**.

**Prova pós-reparo:** `AUDIT-01..03` passam; `REC-01..24` e demais regressões mantidas.

## 3. Contrato mínimo candidato para ocorrência de callback C07 [P]

Um `statuses[].id` é o **ID da mensagem enviada**. Não é um identificador único da ocorrência do callback; `status + timestamp` também não é garantia de exclusividade. O futuro serviço de ingresso confiável da S0 deve:

1. Verificar o HMAC Meta sobre os bytes brutos por App selecionado **via configuração confiável** antes de interpretar o POST. Confirmar canal/loja por registro vigente autenticado, nunca por campo livre do payload.
2. Em **uma transação**, conservar cada unidade relevante do POST e a tarefa durável, associando um **`occurrence_ref` interno gerado no aceite**, diferente de `provider_message_id`, com escopo completo, posição no envelope, instante de ingresso, referência protegida ao payload bruto/fragmento, integridade e política de retenção. `occurrence_ref` identifica um registro **interno**, não uma ocorrência única garantida pelo provedor.
3. Separar **conservação de observações** de **idempotência de efeitos**: reentregas podem chegar novamente e não há como provar universalmente que dois callbacks com mesmo ID/estado/segundo representam a mesma observação física. S0 define reconciliação conservadora sem descartar conteúdo legítimo.
4. Correlacionar C07 pelo envio autorizado e escopo App/WABA/Phone/canal/loja com `wamid`, e destinatário protegido/verificado. Status sem envio correlacionado permanece pendente; variantes 8↔9 não são automaticamente destino autorizado.
5. Nunca usar o `occurrence_ref` para inferir `vendido`/`perdido`, desbloquear retry externo ou afirmar que `read` = venda. `failed` é observação técnica independente, e eventos tardios não diminuem progresso.
6. ACK HTTP `200` **somente após aceite durável comprovado de todos os itens relevantes** e política de quarentena aprovada (DEC-WA-06). O retorno da função `decideBatchAck` aceita formato de recibo hipotético — **não atesta sozinho commit, assinatura da S0 ou payload protegido**. Nenhuma interface real está homologada.

**Campos propostos (não endpoint/RPC ou migração aprovada):** `occurrence_ref`, `ingestion_batch_ref`, `entry_index`, `change_index`, `item_index`, `meta_app_ref`, `waba_id`, `phone_number_id`, `concessionaria_id`, `canal_id`, `provider_message_id`, `provider_status`, `provider_timestamp`, `received_at`, `protected_payload_ref`, `payload_integrity_ref`, `processing_disposition`. Nenhum exemplo inclui dados de cliente real.

## 4. Evidência de execução, integridade dos arquivos

**Reexecução local de arquivos idênticos aos blobs Git versionados** (Node `v22.16.0`, TypeScript `5.8.3`):

- 17 WA-OUT + 24 WA-TPL + 23 SIM + 24 REC = **88** regressões preservadas.
- `scope-isolation.test.ts`: **3** testes adversariais PASS pós-reparo.
- `cross-contract.test.ts`: **14** testes de integração de **módulos reais**: HMAC válido/inválido, POST 2 mensagens + 2 status, recibo hipotético parcial/commit falho, status antes de registro de Graph, repetição mesmo status/segundo, atraso, destinatário diferente, timeout sem `wamid`, bloqueio de reenvio, isolamento, status inbound versus callback, `occurrence_ref` interno sintético e colisão da chave antiga.
- **Total: 105/105 PASS** no Node, com `node --experimental-strip-types --test` dos seis arquivos `*.test.ts` citados.
- `tsc --noEmit --strict` dos seis módulos auditados `inbound.ts`, `durable-receipt.ts`, `graph-outbound.ts`, `graph-template.ts`, `offline-dispatch.ts`, `technical-reconciliation.ts`: **PASS**.
- Blobs Git confirmados: `technical-reconciliation.ts` `cb6cb200d514321cc499941f491424aef1e0f7c7`; `scope-isolation.test.ts` `3cba9e2f2e93d0000ec1052dce14cb1fc01b6a0c`; `cross-contract.test.ts` `8fdadcca8010cf4e39b24a46729ea474d97e1a8c`; `inbound.ts` `3993bf340c8bec04db13a7dbf40efc0cacb744a7`; `durable-receipt.ts` `36f5ccfb41fc42f273afe9b56862f858f32bb94c`.

**Limites:** não foi executado CI GitHub para esta frente; arquivos `*.test.ts` foram executados no Node, não totalmente typechecked por ausência de `@types/node`. O ensaio de ACK usa recibo **fabricado de propósito** e não prova persistência real. A ocorrência com `crypto.randomUUID()` em teste **não é um gerador/contrato de persistência em produção**. Os mocks não modelam locks distribuídos, crash recovery, dados reais, Graph API real ou serviço S0 em rede.

## 5. Gate de continuidade

**GO** para novos testes sintéticos e especificação dos contratos de credenciais, ocorrência e autorização. **NO-GO** para conectar este reconciliador diretamente ao webhook, usar `statuses[].id` ou `status+timestamp` como chave definitiva, declarar ACK durável, enviar mensagens, acionar Graph API ou realizar merge/deploy. A integração final demanda retorno/aceite explícito da frente principal (S0) sobre occurrence ID, payload protegido, acesso de menor privilégio, vínculo de App/canal, política de retransmissão e DEC-WA-04/06.

Nenhum Supabase hospedado, POC concessionária de demonstração, número comercial, App/WABA real, credencial ou recurso pago foi alterado nesta auditoria.
