# CFI-01 — Conciliação entre FV-01/FV-02, núcleo S0 e OpenAI OAI-05/E01 | v0.1

**Data:** 18/10/2026. **Estado:** REVISÃO DOCUMENTAL cruzada realizada pela frente visual; **[P/R] contrato interfrentes candidato, sem homologação das frentes S0 e OpenAI**. Não equivale a revisão assinada por proprietários externos, implementação de API, autorização financeira/bancária ou testes executados.

## 0. Fontes e snapshots auditados

- **FV (branch `feat/frontend-plataforma-visual`):** `frontend/docs/04_CONTRATO_FV01_UI_BACKEND_v0_1.md` e `05_CONTRATO_FV02_CONCLUSAO_EXTRAÇÃO_POS_HUMANA_v0_1.md`; alterações apenas em `frontend/`.
- **S0 (branch `feat/s0-fundacao-prumo`, commit observado `01e692f692a68111d5527691275b9292ca05fbf2`):** `README.md`, `docs/S1_001_JORNADA_HUMANA_VISUAL_2026_10_18.md`, `docs/D_ORG_01_EQUIPE_PRUMO_2026_10_18.md`, `docs/DECISOES_E_GATES.md`, `backend/identity_boundary.py`. S0 possui demonstração S1 sintética e gateway LOCAL para operações restritas; **não foi identificada nesta revisão uma implementação de conclusão→extração pós-humana na frente S0**. Isso não é prova de inexistência futura.
- **OpenAI (branch `feat/s2-openai-adapter-sintetico`, commit observado `82b2ebf03770756b1a97b6c115737587167c077c`):** `docs/integracoes/openai/OAI_05_CONTRATO_EXTRAÇÃO_PÓS_ATENDIMENTO_HUMANO_v0_1.md` e `E01_CONTRATO_FUNCIONAL_MULTI_CAPACIDADE_v0_2.md`, ambos ainda [P/R]. A E01 mais recente já usa o identificador **`human_close_extract`** consistente com OAI-05.
- **Acervo canônico auditado em 17/10:** 00A, 13A, 21–24, 26, 40 e 41 (pacote de 55 arquivos). A orientação funcional expressa de 18/10 supera o **preenchimento manual rotineiro**, sem revogar a correção individual excepcional [D] do doc.23/D41-04.

Os códigos `C01–C24` e `UQ01–UQ09` são **contratos conceituais [P]** dos docs.26/40, não endpoints disponíveis. A interface S1 de S0 é uma demonstração offline; a nova frente visual não deve alterar ou copiar sua lógica sem coordenação.

## 1. Resultado da compatibilização

| ID | Tema | Compatibilidade/resultado | Estado |
| --- | --- | --- | --- |
| CF-01 | Sem digitação cadastral rotineira na UI, extração automática após conversa | FV-02, OAI-05 e E01 são concordantes quanto à direção de negócio | **[D-direção]** |
| CF-02 | Clique visual, evento técnico S0, operação interna OpenAI | Separação em fronteiras distintas; FV não chama OpenAI diretamente | **[P] compatível** |
| CF-03 | Identificador da operação OpenAI | E01 atual e OAI-05 usam `human_close_extract`; não usar nome anterior `post_human_extract` como enum | **[P] conciliado quanto ao nome** |
| CF-04 | Envelope E01 ↔ OAI-05 | Exemplos não têm os mesmos caminhos, campos e nomes | **[R] diverge; requer padronização pelos donos** |
| CF-05 | Retorno E01 ↔ OAI-05 | `extraction.field_suggestions[]` versus `fields_proposed[]` e resultados/avisos diferentes | **[R] diverge; não escolher payload canônico nesta branch** |
| CF-06 | Autenticação e permissão | S0 autentica e revalida concessão por loja/atribuição; gestor apenas supervisor lê D2, só gestor autoatribuído executa ação de operador | **[D] compatível**, execução S0 pendente |
| CF-07 | Status comercial | Conclusão e extração são evento/estado TÉCNICO; nenhum nono status; nenhum marco de banco/venda/recusa automático | **[D] compatível** |
| CF-08 | Persistência e autoria | OpenAI somente propõe; S0 valida e persiste elegíveis com proveniência e autoria técnica, sem falsificar ação humana C13 | **[P] convergente; contrato físico [R]** |
| CF-09 | O3/UQ03 e C13 | UQ03 pode fornecer versões da ficha e projeção autorizada [P]; status do processamento F03 não foi especificado em UQ03; C13 somente para exceção humana | **[R] extensão de projeção/consulta** |
| CF-10 | C01–C24 | Não existe contrato conceitual completo para “conversa humana concluída → extrator → versão de ficha”; C03 é fala IA e C10 é handoff, C13 é correção HUMANA | **[R] S0 precisa adicionar contrato** |
| CF-11 | D3/D4 e privacidade | Gestor em supervisão não recebe D3/D4 brutos, ainda que possa ler conversa integral D2; políticas de transferência ao modelo, áudio e banco continuam condicionadas | **[D/V]** |
| CF-12 | Reprocessamento/concorrência | Consenso: isolamento, instantâneo imutável, idempotência, falhas sem retomar IA; sem atomicidade física/endpoints definidos | **[P/R]** |
| CF-13 | Cadastro incompleto por atendimento excepcional | Não reclassificar `em atendimento pelo operador` como `cadastro enviado ao operador` só porque extrator terminou; status de IA→humano completo permanece distinto | **[D] invariante; encaixe S0 [R]** |

## 2. Três fronteiras, sem acoplamento direto do navegador ao provedor

**A — Interface (FV-02 → S0):** operador com atribuição ativa em loja concedida aciona, na interface, uma **solicitação lógica** de conclusão da etapa de conversa. Campos originados no browser: `case_ref` opaco, `expected_case_version`, `request_id`/correlação e `idempotency_key` conforme convenção aprovada. **Não** enviar no request: alegação confiável de ator, loja, perfil, data do fechamento, watermark, transcript, catálogo, hash ou credencial.

**B — Domínio S0:** verifica sessão, concessão por loja, atribuição ativa, estado e versão, qualifica o evento (nome físico pendente), registra solicitação/conclusão durável e obtém recorte de conversa autorizada do **mesmo caso e concessionária**. O processamento/retentativa idempotente é propriedade do S0; retorno imediato ao UI significa apenas pedido aceito ou recusado, **não** extração/persistência concluída. O acoplamento técnico de comando/evento com S0 ainda **[R]**.

**C — Porta S0 → OpenAI:** S0 usa a capacidade **`human_close_extract`** de OAI-05/E01, sob contrato final que os proprietários reconciliarão, envia snapshot minimizado e catálogo de campos permitido, recebe apenas propostas com fontes/ausências/conflitos e executa validação/persistência auditável pelo S0. O browser não recebe payload bruto do adaptador, conversa íntegra de escopo alheio, prompt nem metadata sensível.

**D — Exibição pelo S0 → UI:** o backend informa por projeção autorizada o estado técnico da tentativa (sem inventar status comercial), data de atualização e eventualmente a **nova versão efetivamente persistida** da ficha via UQ03 autorizada. O frontend só mostra “Ficha atualizada” se o S0 confirmar commit/versionamento. Fluxos de esclarecimento permanecem humanos; eventual nova extração exige snapshot e autorização novos.

## 3. Compatibilização de exemplos E01 ↔ OAI-05 — nomes candidatos, NÃO conversor aprovado

| Conceito | Exemplo E01 v0.2 | Exemplo OAI-05 v0.1 | Decisão necessária |
| --- | --- | --- | --- |
| Operação | `operation_kind: human_close_extract` | Idêntico | Nome candidato compartilhado; validação final [R] |
| Versão | `contract_version: s0-openai.v0.1-proposed` | Mesmo valor ilustrativo | Numerar contrato físico com S0 |
| Evento | `trigger_ref` | `closure_event_id` e `closed_at` | Selecionar nome e fonte S0 confiável |
| Escopo | `scope.concessionaria_ref/caso_ref/conversa_ref/ciclo_ref` | `concessionaria_id, caso_id, conversa_id, ciclo_id` | Estrutura aninhada vs plana |
| Snapshot | `authorized_context_ref`, `context_version` | `message_watermark`, `conversation_snapshot_hash/ref`, `messages[]` | Exigir vínculo hash/corte/versão verificável sem duplicar dados |
| Catálogo | `fields_policy_version` | `allowed_fields_catalog_version`, `allowed_fields[]` | Definir uma política/versionamento e allowlist |
| Ficha/versionamento | `expected_case_version` | `current_form_version`, `expected_version` | Distinguir versão do caso, snapshot e versão da ficha |
| Saída — campos | `extraction.field_suggestions[] { field_key, value, evidence_refs }` | `fields_proposed[] { field_code, proposed_value, source_message_refs }` | Definir formato canônico único |
| Saída — lacunas | `extraction.missing_field_keys[]` | `missing_fields[]` com `reason_code` | Preservar motivo e aplicabilidade |
| Saída — conflitos | `extraction.conflicts[]` | `conflicts[]` | Especificar fontes e motivos |
| Saída — incerteza | `needs_human_clarification`, `warnings[]` | `outcome PROPOSED/PARTIAL/NEEDS_REVIEW/FAILED`, `extraction_warnings[]` | Definir resultados sem inferir gravação |
| Correlação de retorno | `trigger_ref, context_version, fields_policy_version` | `request_id, snapshot_hash, form_version_observed` | Retorno deve permitir rejeitar proposta obsoleta e atrelar execução a evento/corte |

**Não há tradução automática homologada entre esses exemplos.** A concordância do nome `human_close_extract` não elimina a diferença de payload; a responsabilidade de consolidar o contrato interno é S0 + OpenAI. A interface deve depender **somente** de projeções/commands S0.

## 4. Semântica de resultados — evitar falsos positivos

1. **Request aceito pelo S0:** conclusão técnica solicitada/registrada, ainda sem prova de extração ou ficha atualizada.
2. **OpenAI retornou PROPOSED/PARTIAL/NEEDS_REVIEW/FAILED [P]:** saída informativa do adaptador, ainda sem prova de persistência; um `PROPOSED` nunca vira `APPLIED` na UI por si só.
3. **S0 validou e persistiu nova versão:** pode comunicar ficha atualizada com versão, referência e projeção autorizada; extração parcial somente autoriza exibir os **campos realmente persistidos** e pendências, se S0 confirmar ambos.
4. **Sem campos elegíveis / conflito / ausência:** ficha pode permanecer sem mudanças. Exibir pendência/esclarecimento, não “cadastro completo”.
5. **Falha externa ou versão obsoleta:** registrar estado técnico/falha segura; não marcar vendido/perdido, não enviar ao banco, não reativar IA Vendedora, não autopausar operações por defeito detectado.
6. **C13 humano excepcional:** evento e autoria distintos de `extracted_from_human_conversation`; não atribuir à pessoa uma escrita realizada pelo extrator.

## 5. Questões em aberto para os donos — não decidir por substituição

**S0 (dono do núcleo) [R]:**
- S0-R01. Contrato interno novo para registrar conclusão humana, sem reutilizar C10/C13/C15; modelo de evento, condições de elegibilidade e resposta idempotente.
- S0-R02. Exato instante de corte e política de mensagem em voo (recebimento Meta, envio C12 incerto/atrasado), nova mensagem depois do clique e esclarecimento humano subsequente.
- S0-R03. Versão confiável de caso, conversa, catálogo e ficha, idempotência de fechamento/job/gravação, concorrência com correção C13 ou revogação/reatribuição.
- S0-R04. Projeção mínima de progresso para a UI e UQ03 (sem criar UQ novo unilateralmente); códigos de erro claros; regra de reprocessamento.
- S0-R05. Encaixe em `em atendimento pelo operador` e `cadastro enviado ao operador`, sem transição espúria.
- S0-R06. Catálogo mestre de campos, classes D3, política de autopersistência com fontes e atribuição técnica; tratamento de resultado parcial.

**OpenAI + S0 [R]:**
- OAI-R01. Assinatura/versão canônica do envelope S0↔OAI para `human_close_extract`; resolver diferenças E01/OAI-05.
- OAI-R02. Formato canônico da saída; obrigatoriedade de hash/versão/correlator e razões de ausência/conflito; no-op explícito.
- OAI-R03. Retentativa/custo, segurança de instruções, áudio transcrito, limites, retention e condições para enviar dados ao provedor [V].
- OAI-R04. Em nenhum caso o adaptador recebe credencial de domínio nem grava ficha ou conversa com cliente.

**Produto/privacidade [R/V]:**
- GOV-R01. Sem catálogo de dados obrigatórios/permitidos e bases/condições externas, nenhum exemplo de nome/e-mail/CPF vira especificação normativa.
- GOV-R02. Revisão pontual humana por classe sensível, possibilidade de correção excepcional doc.23/C13 e UX de esclarecimento.
- GOV-R03. Definição textual final do botão, evitando confusão com fechamento de ciclo, remessa ou venda.

## 6. Portões e aceite

- **G-CFI-0 — este relatório:** comparação documental e divergências registradas **CONCLUÍDAS**; não significa aprovação do contrato.
- **G-CFI-1 — confirmação de S0 e OpenAI:** **PENDENTE**; ratificar em revisão os itens S0-R/OAI-R e publicar decisão de versão canônica, sem alterar branches alheias por inferência.
- **G-CFI-2 — contratos executáveis e testes sintéticos:** **NÃO EXECUTADO**; somente após G-CFI-1, com ênfase em isolamento, duplicidade, versionamento, provas e privacidade.
- **G-CFI-3 — integração e lançamento:** **NÃO AUTORIZADO**; Supabase remoto, Meta, Banco, OpenAI real, custos, domínio e hospedagem fora desta entrega.

Ver [matriz de aceite candidata](08_MATRIZ_ACEITE_CONTRATUAL_FV_S0_OAI_v0_1.md). **Nenhuma pontuação do documento 19F é acrescida automaticamente.** O acervo anterior, decisões 13A/21–23/41 e D-ORG-01 continuam prevalecendo.

**Rastreamento de revisão cruzada:** [GitHub issue #4 — CFI-01](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4), ABERTO, ainda sem validação dos proprietários das frentes S0 e OpenAI.
