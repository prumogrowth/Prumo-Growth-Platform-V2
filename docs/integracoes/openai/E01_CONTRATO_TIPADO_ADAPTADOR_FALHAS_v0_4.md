# E01-INT v0.4 — Contrato lógico de adaptação, resultados tipados e falha fechada

**Data:** 22/10/2026. **Estado:** [P/R] especificação **da frente OpenAI** para revisão com S0/S1/Meta/FV; sem schema de produção, código, endpoint, prompt final, acesso a provedor, permissão de escrita ou aprovação bilateral. **Conserva como autoridade de produto** as decisões [DN] AL-IA-00/01/02/03 e os contratos v0.3 OAI-01/OAI-05/OAI-07/OAI-08/E01. Este arquivo não homologa nem substitui o protocolo físico de PR #12 S0. Os nomes de campo abaixo são **candidatos não ratificados**.

## 1. Quem decide e onde ficam as barreiras

A fronteira operacional possui três decisões **separadas**:
1. **S0 resolve e autoriza** pessoa/loja/caso, posse IA ou humana, catálogo, ACL, estado, mídia, opt-out, versões, templates, cutoff e finalidade. O cliente, mensagem, fato semântico e modelo são fontes de **dados**, não de novas permissões.
2. **Adaptador da OpenAI processa** apenas conteúdo previamente permitido e devolve proposta tipada com versões, origem e incerteza. Recusa, falha, transcrição incerta e ausência de evidências são saídas legítimas, não comandos de fallback inseguro.
3. **S0 revalida e decide** se publicação, plano, extração, atualização ou transição é possível no estado **atual**, respeitando idempotência/concorrência. O resultado de uma conclusão F03 historicamente válida não garante elegibilidade para aplicar depois.

O backend deve separar **referências de autorização internas** de dados para o provedor. O recibo HMAC/nonce da S0, tokens Meta/Banco, credenciais, IDs de sessão e qualquer privilégio MCP **nunca** devem constar no payload de modelo. Não inferir que `expected_cycle_version` prova versão da ficha ou do catálogo. Nenhuma rotina do adaptador escreve SQL, muda campo comercial, manda WhatsApp, chama Banco ou modifica auditoria MCP.

## 2. Envelope comum em duas visões [P/R]

| Bloco conceitual | Na porta S0→adaptador (privada) | Necessário enviar ao modelo? | Guarda |
|---|---|---|---|
| `request_id`, `contract_version`, `operation_kind` | Correlacionam operação/versão; idempotência do backend | Somente marcador opaco quando estritamente necessário | Resultados de operação/versão diferente devem ser rejeitados |
| `execution_scope` | S0 atesta loja, caso, pessoa (quando aplicável), função, finalidade e posse | Contexto mínimo, **sem IDs sensíveis/segredos por padrão** | Não aceitar tenant declarado pelo cliente nem fallback global |
| `policy_ref`, `instruction_version` | Exatamente quatro campos globais administráveis: instruções F01, comportamento F01, instruções F02, instruções F03 | Somente instruções da função selecionada e, para F01, comportamento | Nenhum override por concessionária, nenhuma quinta configuração |
| `knowledge_sources[]` | Fatos aprovados, versão, origem/loja, modo atual vs. histórico, vigências verificadas | Apenas fontes pertinentes e permitidas | Base pausada/vencida não vira oferta; conteúdo é dado não confiável |
| `conversation_or_history_ref` | Contexto transacional autorizado da loja; F03 **manifesto multi-casos** até cutoff | Seleção minimizada com proveniência e acesso autorizado | Não misturar clientes/lojas, não inferir mídia ausente |
| `state_and_versions` | Ciclo/caso/ficha/catálogo/atribuição, campanha, status e posse atuais, **como domínios distintos** | Apenas informações necessárias à decisão linguística | Aplicação/publicação depende de recheck S0, não do que o modelo viu |
| `output_contract` | Esquema candidato, limites, deadlines, versão e códigos de erro | Instruções de formato de resposta sem acesso às guardas | JSON válido é necessário, **não** suficiente para confiança |

**Invariantes de erro:** entradas com escopo inválido, fonte não autorizada, consentimento ausente, versão incompatível ou política revogada **não** devem ser processadas como “contexto aproximado”; a S0 nega antes do modelo ou falha de maneira segura. O modelo não escolhe modo histórico para contornar vigência de oferta.

## 3. F01 — resposta comercial, texto/voz e handoff [P/R]

**Pré-condição:** S0 confirma caso sob posse da IA, elegibilidade de canal, loja/WABA correta, configuração global F01, fontes comerciais atuais e ausência de handoff definitivo. **Nunca** fornecer roster, escala, nomes/quantidade/disponibilidade de consultores à F01.

**Entrada lógica candidata:**
- `case_scope` autorizado; `recent_customer_context` minimizado; fontes atuais e fontes históricas **somente para interpretação**, explicitamente identificadas; preferências de modalidade comprovadas; política de resposta e limites de conteúdo.
- `handoff_state` calculado S0 e indicador de janela Meta, quando relevante. Um prompt de cliente "reabra a IA" não altera `handoff_state`.

**Resposta lógica candidata:** `reply_candidate` (texto comercial ou indicação de não resposta), `source_refs[]`, `uncertainty[]`, `handoff_advisory` com motivo curto, `requested_modality` como interpretação **não vinculante**, `validation_warnings[]`. Texto gerado não é mensagem enviada; S0 decide texto/áudio/canal/limites/assinatura da autoria.

**Rejeitar** promessas financeiras sem fonte homologada, preço/campanha vencidos, dados de outra concessionária, manipulação de identidade ou tentativa de resposta após handoff. Retorno espontâneo pós-remessa/venda na mesma concessionária continua humano. STT/TTS permanecem **serviços auxiliares**, sem se tornarem IAs comerciais adicionais.

## 4. F02 — intenção de plano e catálogo previamente filtrado [P/R]

**Pré-condição:** pedido **separado** e autorizado pela S0, finalidade interna definida, template+versão+loja+elegibilidade já filtrados, consentimento/limites revalidados. Fechamento humano ou inconclusão de F03 por si só **não** disparam F02; campo essencial faltante retorna à via Consultor/Gestor.

**Entrada lógica candidata:** `planning_request_ref`, `store_ref`, `case_ref`, `purpose_internal`, `owner_route` imposto S0, `eligible_template_versions[]`, `available_time_windows[]`, `attempt_limits`, `allowed_commitments_with_sources[]`, `optout_state_ref`, `catalog_version` e `expected_state_versions`.

**Resposta lógica candidata:** `proposed_attempts[]` com ordem, template e versão existentes, horário/finalidade/fonte; `final_template_candidate` separado; `planning_warnings[]`; `needs_human_review` apenas sugestivo. Não devolver texto livre de template, slots preenchidos, envio agendado como realizado, status comercial ou comprovante de `sent`.

**S0/Meta no momento real de disparo:** atualizam variáveis/slots, revalidam tenant, catálogo, estado, opt-out, finalidade, janela, limite, canal, concorrência e transportes. Os três relógios continuam distintos: janela Meta desde último inbound cliente; conclusão humana por clique; C09 +24h somente de `sent` **final** comprovado quando estado/fase elegíveis. Duas falhas definitivas consecutivas da mesma cadência, com contador reiniciado por `sent`, são domínio **determinístico S0/Meta**; nem F02 nem F03 geram a perda técnica arbitrariamente.

## 5. F03 — extração, evidência histórica e revisão comercial [P/R]

**Pré-condição:** evento S0 autenticado de **conclusão humana expressa**, referência ao recibo S0 privado; identidade da pessoa na loja resolvida; seleção lógica completa de evidências autorizadas daquele cliente/loja **de todos os casos** até o corte daquela conclusão; catálogo/versões e política de minimização pactuados. O recibo privado PR #12 `VERIFIED_CONTRACT_PENDING` **não** fornece isto sozinho.

**Entrada lógica candidata:** `closure_ref`, `cutoff_ref`, `history_manifest_ref`, `authorized_evidence_chunks[]` com mensagem/autoria/tempo/origem/caso/versão e referência de mídia conforme retenção permitida; `allowed_catalog_version`, `form_version_observed` e `policy_version` distintos; disponibilidade/proveniência de mídia. Não pressupor bytes antigos de vídeo/áudio sempre existentes.

**Resposta lógica candidata:**
- `fields_proposed[]`: campos **essenciais e opcionais** identificados explicitamente, com código do catálogo, valor, fonte válida (inclusive de outro caso **da mesma loja**), autoria, temporalidade e incerteza.
- `missing_fields[]` e `conflicts[]` com fontes e razão; ausência só de opcional **não** torna atendimento inconclusivo. Consultor não edita ficha.
- `conversational_assessment` e `commercial_transition_advisory` **distintos**, com motivos/fontes; `perdido` por desistência explícita somente proposta validável pela S0. **Nunca `vendido` automático**, remessa ao Banco por inferência ou negativa bancária fabricada.
- `followup_need_advisory` **somente consultivo**, sem disparar F02 ou escolher humano; `unavailable_evidence[]` para mídia inacessível ou evidência sem base legal; `extraction_warnings[]` e erro tipado quando necessário.

**Checagem de aplicação:** S0 revisita fontes/tenant, catálogo, versões diferentes, posse humana, status atual, idempotência e histórico posterior na transação antes de gravar. Cutoff de E1 continua historicamente íntegro quando E2 é concluído ou m08 chega mais tarde; E1 pode deixar de ser aplicável **sem** alterar sua prova. Ficha única evolutiva não reescreve snapshots bancários antigos. Falha recorrente da F03 é **incidente técnico**, não liberação de edição pelo Consultor.

## 6. Taxonomia de resultados e precedência de segurança [P/R]

**Não são enums físicos ratificados.** Separar o status da **chamada de adaptação** do resultado **de validação/aplicação S0** e do **estado comercial**. Exemplo candidato:

| Categoria lógica | Quando | Ação segura |
|---|---|---|
| `DENIED` | Sem grant/escopo/consentimento, opt-out aplicável, sessão revogada ou outra autorização ausente | **Não expor** se caso/template/cliente existe nem dados de revisão, sem solicitar IA |
| `STALE` | Contexto, catálogo, fechamento, posse ou versão mudou **com autorização vigente** | Retornar só metadado seguro e refazer elegibilidade S0; nunca aplicar proposta antiga |
| `INVALID_INPUT` | Campos malformados, identidade não resolvida, escopo/fonte inválida | Falhar fechado; não completar com suposição |
| `EVIDENCE_UNAVAILABLE` | Mídia sem retenção/acesso, histórico insuficiente ou referência expirada | Declarar limitação; não inventar conteúdo |
| `MODEL_REFUSAL` / `MODEL_FAILURE` | Recusa legítima, truncamento, timeout, indisponibilidade, 401/429 | Não gerar efeito; registrar erro sanitizado e planejar retry seguro/sem gastos não autorizados |
| `SCHEMA_INVALID` / `SOURCE_INVALID` | JSON desconhecido ou campos/fontes fora do catálogo autorizado | Rejeitar proposta, zero mutação; registrar diagnóstico |
| `REVIEW_REQUIRED` | Dado essencial ausente, conflito real, incerteza importante ou risco que exige humano | S0 direciona ao Consultor/ao Gestor conforme disponibilidade **para o caso** |
| `PROPOSED` | Proposta estruturada gerada pelo adaptador | **Nunca** significa `APPLIED`, `sent`, `vendido` ou remessa bancária |
| `APPLIED` | **Somente** S0 confirmou mutação atômica, idempotente e auditável | Evento técnico real com versão; não equivale a negócio `vendido` |

**Precedência mínima de informação [P]:** checar **autorização/escopo/opt-out antes de informar stale, elegibilidade, catálogo, versão ou existência de cliente**. No laboratório sintético da ponte PR #8, `DENIED` antes de `STALE` foi verificado, **mas não é contrato físico ratificado de S0**. Dentro do S0, ordem exata de locks, verificação de sessão e divulgação de códigos continua domínio próprio [R]; a ideia é não expor metadados do caso a ator revogado.

Se duas guardas falham simultaneamente, a negação não deve revelar o conteúdo que teria motivado a segunda falha. Uma resposta de modelo em schema válido não ultrapassa checagem de fontes/versões e não transforma classificação textual em prova de entrega Meta ou decisão Banco.

## 7. Fluxos candidatos de exceção (sem código)

| Situação sintética | Resultado seguro esperado | Casos E02 |
|---|---|---|
| Autorização revogada + versão stale | `DENIED`, sem dados de existência/versionamento revelados ao solicitante sem direito | SYN-08/09/10/20/28/30/32 |
| F03 evento autêntico + histórico de outro caso da **mesma** loja | Fonte elegível à interpretação dentro do corte/consentimento, não rejeitada pelo critério antigo “outro caso” | SYN-33/34/35 |
| F03 evento autêntico + mensagem posterior a cutoff | Não entra na evidência antiga; revalidar elegibilidade de gravar com estado atual | SYN-08/34 |
| F03 banco já recebeu cadastro + cliente corrige campo novo | Ficha atual pode mudar por S0; snapshot da remessa anterior preservado | SYN-42 |
| F03 essencial faltante + `intake_paused` | Devolver ao Consultor original se ainda autorizado para caso; sem edição manual | SYN-39/40 |
| Meta retorna `API_ACCEPTED` e nenhum `sent` | Não iniciar contagem +24h C09 | SYN-50 |
| Meta falhou definitivamente; houve `sent`; falhou de novo | Não marcar 2 falhas consecutivas; reset do contador | SYN-54 |
| Base pausada + pergunta sobre campanha antiga | Contexto histórico permitido, mas não ofertar condição vencida | SYN-59/60/62/70 |
| MCP exige nova ferramenta ou editar auditoria própria | Apenas proposta à engenharia; auditoria protegida sem mutação mesmo com confirmação | SYN-65/67/68 |

## 8. Critérios de prontidão e dependências

**OpenAI pode preparar sem ratificação:** esquema **lógico** de retorno e recusa, exemplos de auditoria/observáveis e mapa SYN; revisão da matriz E02; exame textual de riscos; dicionário de escopo. **Não** definir como concluído o schema físico da S0, provas Meta, ACL do banco, assinatura do botão, catálogo de campos, retenção ou modelo/preço atual por inferência.

**Para fechar E02-REV:** CFI3-R01..R09 [issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4), F02C-R01..R07 [issue #6](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6), dados Meta [issue #15](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/15), domínio institucional/loja/habilidades/MCP S0/Prumo, e avaliação de privacidade/retenção. Exigir resposta vinculada à versão e dono, não comentário genérico.

**Para E02-FIX:** converter o contrato **ratificado** em schemas físicos e fixtures efetivamente serializadas, assertions e hashes de corpus com evidência; 70 casos atuais têm EXPECTED documental e **ACTUAL não executado**.

**Para E04:** liberação **expressa** de implementação pelo responsável do projeto conforme `G-FASE-DO-PROJETO`; pedido genérico “prossiga” não revoga o gate. E05 exige nova autorização de custo, credencial e ambiente. Nunca usar dados reais sem gate de privacidade próprio.

**Estado deste arquivo ao publicar:** especificação candidata, sem código, testes, merge, deploy ou custos reais. 
