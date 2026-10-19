# WA-08 — Validação estrita da conciliação técnica Graph ↔ callback (offline)

**19/10/2026 — desenvolvimento implementado no PR #2 Draft; não homologado nem executado em PostgreSQL/Meta.** Continuação da estrutura **sem conexão com APIs reais**, conforme diretriz de projeto. Não altera contratos S0, status comerciais ou código dos serviços Meta em operação.

## Problema identificado na revisão da fronteira de integração

A rotina `FakeMetaStatusReconciler` em `integrations/whatsapp-meta/technical-reconciliation.ts` já exigia a igualdade exata App/WABA/número/destinatário/wamid ao correlacionar callbacks, mas aceitava:
- Como identificador de mensagem `GraphSendOutcome.provider_message_id`, qualquer string técnica genérica (`id(...)`), mesmo sem prefixo `wamid.` ou com comprimento/formato inválidos; a validação de `classifyGraphSendResult` é mais rigorosa, mas não era revalidada na fronteira que recebia o resultado.
- Uma bandeira `send_state='API_ACCEPTED'` com `api_accepted=true` mesmo que `http_status` fosse nulo, negativo ou erro 4xx/5xx; ou uma combinação contraditória de `meta_error_code`, `meta_error_subcode` e `retry_automatically`. Isso permitiria uma correlação **de laboratório** após um resultado estruturalmente impossível.
- No callback `MetaIngressEvent`, um `provider_message_id` arbitrário e posições sem `array_kind='statuses'` ou índices inteiros não negativos. O `inbound.ts` gera posições legítimas após HMAC, mas a outra fronteira não exigia a sua estrutura.

Essas inconsistências foram encontradas por leitura direta dos módulos; **não houve exploração demonstrada nem tráfego real**.

## Correção aplicada

1. Reutilização de contrato técnico estrito: `wamid.<alfanumérico/base64/segmento permitido>`, tamanho 1..1024 depois do prefixo, sem espaços/controle. O conciliador **não** interpreta ID telefônico ou tenta normalização 8↔9.
2. Em `registerAcceptedSend`, além do estado de API aceita, exige **HTTP 2xx inteiro**, `retry_automatically === false`, códigos de erro Meta nulos e `phone_number_id` numérico 5..25. Resultado Graph `UNCERTAIN_EXTERNAL` nunca vira mensagem correlacionada ou tentativa automática de reenvio.
3. Em `observeAuthenticatedFixture`, exige `provider_message_id` canônico e posição `statuses` com `entry_index/change_index/item_index` inteiros não negativos. `projectionFor` recusa lookup de ID não-canônico. Continua exigindo app_ref **da rota autenticada em outro componente**, sem tratar essa função como autenticação.
4. **Sem colapsar ocorrências distintas:** mesmo `wamid`, mesmo `sent` e mesmo timestamp em posições diferentes continuam como duas observações da simulação. `possible_repeat` é apenas heurística, não prova de dedupe por ID.
5. Nenhuma rotina registra `COMMITTED`, autoriza ACK HTTP, toma decisão comercial C07/C09, altera janela 24h ou chama Graph, banco, n8n, IA ou APIs bancárias.

## Testes adicionados

`integrations/whatsapp-meta/technical-reconciliation.test.ts` ganhou os casos **REC-25..35**:
- REC-25: falso `API_ACCEPTED` com HTTP nulo, 199, 302, 400, 500, NaN não gera vínculo;
- REC-26: IDs Graph não-`wamid`, vazios ou fora da gramática são recusados;
- REC-27: auto-retry/erro Meta contraditórios são recusados;
- REC-28: callback sem posição `statuses`, índice negativo/fracionário/NaN ou posição ausente não altera projeção;
- REC-29: callback sem `wamid` legítimo não ingressa em pendências nem afeta envio correlacionado;
- REC-30: consulta por chave arbitrária é recusada;
- REC-31: phone_number_id Meta não-numérico bloqueia vínculo;
- REC-32: caso positivo legítimo ainda progride somente `NONE → SENT` técnico;
- REC-33: resultado **gerado pelo `classifyGraphSendResult` existente**, sem chamada de API, vincula após HTTP 200 válido mas não prova envio ao destinatário;
- REC-34: duas posições de status permanecem duas observações mesmo com ID/status/tempo repetidos;
- REC-35: classificação real `UNCERTAIN_EXTERNAL` por resposta 200 sem wamid não vincula.

**Estado de evidências:** código e testes publicados/relidos por blob GitHub; **11/11 casos novos definidos, 0/11 executados nesta sessão**. Não existe npm/fetch/Graph ou ambiente TS conectado usado para executar o teste. `REC-01..24` eram testes existentes, mas **não foram reexecutados** nesta sessão. A suíte deve rodar no checkout isolado com Node/TypeScript compatível antes do aceite.

## Gates e continuidade

- [R] Rodar a suíte de conciliação TypeScript em checkout isolado da branch exata e registrar SHA e logs. Não confundir verificação estática ou teste de unitário em memória com PostgreSQL.
- [R] Concluir ingresso real S0/Meta (identidade autenticada fora do JSON, App/WABA/emissor→loja vigente, nonce, escopo, payload protegido, ocorrência posicional, ACK somente depois do COMMIT e recuperação `COMMIT_UNKNOWN`). Os **20 SQL WA-06D ainda não haviam sido executados no PG17** na revisão anterior.
- [R] Confirmar semântica oficial de callbacks Meta e catálogos/templates na etapa final de integração autorizada; não afirmar prova de `sent` efetivo baseada somente em aceite Graph.
- [R] Testes conjuntos S0/S1 seguem pendentes. Nenhuma migração S0 ou interface bancária foi alterada aqui.

**Resultado:** GO para continuar **desenvolvimento interno sem APIs**; NO-GO para interface externa/produção, envio automático, HTTP ACK, conclusão comercial, implantação ou merge sem evidência. Nenhum token real, segredo, número concessionária de demonstração, Supabase hospedado, custo explícito ou API foi utilizado.
