# CFI-01 v0.3 — Ponte lógica F03: conciliação S0 ↔ OpenAI ↔ S1/FV/Meta

**Data da leitura:** 22/10/2026. **Tipo:** proposta de contrato cruzado [P/R], com intenções funcionais [DN] registradas em AL-IA-01. **NÃO** é contrato ratificado por S0, payload físico, chamada à OpenAI, autorização de escrita, aceite de privacidade ou alteração nas branches alheias. Retém CFI-01 v0.1 como histórico; a fonte funcional é OAI-05 v0.3.

## 1. Evidência observada versus lacuna

| Fonte/artefato verificado | O que efetivamente demonstra | O que NÃO demonstra |
|---|---|---|
| S0 [PR #12](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/12) e [gate de recibo de 21/10](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-cfi01-f03-auth-preflight-20261020/docs/S0_CFI01_F03_SNAPSHOT_METADATA_RATIFICATION_GATE_2026_10_21.md) | Serviço privado S0 de captura/rechecagem de conclusão autenticada, nonce/HMAC, autorização de caso/atribuição, hash, watermark, contagem e versão do **ciclo**, com testes PG17/GoTrue locais; bridge retorna `VERIFIED_CONTRACT_PENDING` | Payload minimizado de histórico cliente/loja, campos/form_version/catálogo, permissão de transferência ao provedor, revalidação antes de APPLY e nenhuma execução real F03 |
| CFI-01 v0.1 da OpenAI | Mapas candidatos `closure_event_id`, `conversation_snapshot_hash`, `fields_proposed[]` etc. | Nomes físicos aprovados; contrato que abranja **todos os casos do cliente** e mídias; paridade de versão |
| FV [conciliação v0.1](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/frontend-plataforma-visual/frontend/docs/07_CONCILIACAO_INTERFRENTES_FV_S0_OAI_v0_1.md) e [issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4) | UI pede encerramento humano à S0; navegador não chama IA nem interpreta APPLY como mera aceitação | Interface FV definitiva e exclusão formal da exceção de edição manual antiga, que contradiz AL-IA-01 |
| [Issue #15 Meta/WA-22](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/15) | Dependência declarada de autores, templates, datas e mídias em histórico completo de mesma concessionária | Acesso/retencão/licença de envio de mídia ao modelo |
| OAI-05/OAI-07/E01 v0.3 | Escopo lógico F03, ficha única, cutoff por fechamento, extração dos opcionais e transições somente S0 | Estados, enums físicos, banco ou API implementados |

**Nota de atualidade:** PR #12 e issue #4 estavam **Draft/aberta** respectivamente na leitura; testes mencionados são **provas publicadas da S0**, não reexecutadas pela frente OpenAI.

## 2. Mapa campo a campo: nunca igualar versões distintas

| Conceito de integração | Nome/artefato físico verificado na S0 | Forma candidata OpenAI/FV [P] | Decisão exigida [R] |
|---|---|---|---|
| Operação de negócio | Fechamento autenticado gera recibo privado na S0 | `human_close_extract` | Nome/versão pública e quem emite comando |
| Tenant | `store_ref` do recibo | `concessionaria_ref` / `concessionaria_id` | ID canônico, projeção e autorização |
| Caso | `case_ref` | `case_ref` / `caso_id` | Caso ativo versus outros históricos do mesmo cliente |
| Conclusão | `closure_event_ref` | `closure_event_id` / `trigger_ref` | Identificador único, integridade e retries |
| Atribuição | `assignment_ref` | `assignment_ref`, versão candidata | Se há `assignment_version` e como revalidar após redistribuição |
| Versão comercial | `expected_cycle_version`, vindo de `ciclos_comerciais.versao_registro` | `expected_case_version` / `expected_version` | **NÃO equivalentes**; `casos_humanos` não declara `versao_registro` na migration examinada pela S0 |
| Snapshot do recibo S0 | `snapshot_sha256`, `message_watermark`, `message_count` | `conversation_snapshot_hash`, `conversation_snapshot_ref`, corte | Escopo físico do hash hoje por conversa/seq. S0 versus expansão histórica multi-casos |
| Cliente/identidade | Não fornecido pelo recibo isolado | `client_ref`, `history_scope_ref` | Vínculo pessoa/loja, vários telefones com provas antifraude, não fundir tenants |
| Ficha atual | **Não fornecida no recibo** | `current_form_version`, `form_version_observed` | Fonte/guarda distinta do ciclo/caso; ficha única evolutiva |
| Catálogo/obrigatoriedade | **Não fornecido no recibo** | `allowed_fields_catalog_version` | Aprovar classes, tipos, campos, essenciais/opcionais, evidências e motivo de ausência |
| Mídias | **Não fornecidas no recibo** | Fontes/refs multimodais recuperadas até cutoff | Proveito real de áudio, vídeo, imagem e documentos sob LGPD/retenção/Meta |
| Resposta | S0 bridge **não recebe resposta de modelo** | `fields_proposed[]`, `missing_fields[]`, `conflicts[]`, `conversational_assessment`, `commercial_transition_advisory` | Schema e reason codes, evidência, erro, status permitido; silêncio F03 ao cliente |
| Aplicação | S0 ainda **não** aplica F03 | `APPLIED`, `REVIEW_REQUIRED`, `STALE`, `DENIED` [P] | Estados técnicos distintos de status comercial, persistência transacional auditada |

**Nunca converter silenciosamente:** `expected_cycle_version`→`expected_case_version`; `snapshot_sha256` por caso→prova suficiente de **todo** histórico; `message_watermark`→autorização de mídia; `closure_event_ref`→autorização de escrita; `suggested=YES`→ordem F02.

## 3. Ordem de execução candidata e pontos de negação

1. **FV→S0:** Consultor autenticado com autorização sobre o caso clica expressamente **Concluir**; o browser não gera fechamento confiável, nem edita ficha, nem chama provedor.
2. **S0:** verifica concessão/atribuição, revogação, estado e idempotência; captura recibo imutável do fechamento e seu cutoff. Fim da janela Meta, handoff e silêncio são eventos **diferentes** e insuficientes para esta etapa.
3. **S0, etapa ainda ausente [R]:** resolve **identidade da pessoa apenas naquela concessionária**, monta seleção **histórica lógica desde primeiro registro na plataforma** até cutoff, atravessando casos, consultores, F01 e mídias legalmente disponíveis. Projeta fonte, autoria, instante, versão, proveniência, regra de consentimento; não expõe dados de B. Estabelece corte histórico **composto**, sem reduzir à ordenação local de uma única conversa.
4. **S0/gateway, etapa ainda ausente [R/V]:** minimiza o conteúdo, verifica política de transferência/retenção/áudio, define referência recuperável à fonte e escopo permitido da F03. O recibo privado sozinho não autoriza esse passo.
5. **Adaptador F03:** produz **proposta estruturada** de todos campos elegíveis encontrados (inclusive opcionais), conflitos, evidências, desfecho e eventual aconselhamento de transição. Não inventa envio Banco, venda, negativa bancária, nem usa outro tenant.
6. **S0, etapa ainda ausente [R]:** valida schema, catálogo, tipos, fontes reais no mesmo tenant, cutoff, versões separadas, identidade, autorizações vigentes e concorrência **imediatamente antes de gravar**. Conclusão histórica permanece válida após novo inbound, mas resultado antigo pode ficar obsoleto para aplicação.
7. **S0→FV:** comunica resultado **técnico** e necessidades de complemento; essenciais/conflitos realmente irresolvidos retornam preferencialmente ao Consultor original, ou ao seu Gestor somente se indisponível **para o caso**; `intake_paused` de novos leads não equivale a indisponibilidade. Consultor **não edita cadastro**.
8. **Opcional e sempre independente:** pedido F02 pós-humano precisa autorização/motivo separado da S0. A F03 não abre cadeias diretamente. F01 permanece silenciosa após handoff daquele caso.

**Erro ou incidente:** autorização/contexto/mídia insuficientes = falha fechada/pendência explícita, nunca prova inventada. Falha recorrente F03 = incidente de engenharia, **não** fallback habitual de edição humana. Reprocessamentos legítimos têm ID/evento/cutoff claros e não sobrescrevem registro histórico.

## 4. Matriz de decisão a ser ratificada por donos

| ID | Pergunta objetiva | Proposta de conciliação OpenAI | Dono de decisão | Situação |
|---|---|---|---|---|
| CFI3-R01 | Qual evento, ID e versão canônicos do botão Concluir? | Consumir evento S0 autenticado, sem confiar em campo vindo do browser | S0 + FV + S1 | **ABERTO [R]** |
| CFI3-R02 | Que identidade vincula várias conversas/números ao mesmo cliente/loja? | Histórico lógico completo só com identidade resolvida e provada pela S0 | S0 + privacidade + S1 | **ABERTO [R/V]** |
| CFI3-R03 | Como relacionar recibo S0 atual e corte histórico multi-casos? | Conservar hash/recibo de cada fechamento; acrescentar atestado/manifesto da seleção histórica com fontes e último evento permitidos | S0 + OpenAI + Meta | **ABERTO [R]** |
| CFI3-R04 | Como fornecer mídia antiga sem violar retenção? | Apenas fontes disponíveis e autorizadas; ausência retorna aviso, sem forçar persistência eterna | S0 + Meta + privacidade | **ABERTO [R/V]** |
| CFI3-R05 | Onde estão versões do caso, ficha e catálogo? | Manter **versões distintas** e checá-las na aplicação; não usar `expected_cycle_version` como substituto | S0 + OpenAI | **ABERTO [R]** |
| CFI3-R06 | O que exatamente F03 propõe e S0 pode aplicar? | `fields_proposed` com fonte e enum de resultado separado de status; `perdido` por desistência só com regras/causa S0; nunca `vendido` | S0 + OpenAI, FV para projeção | **ABERTO [R]** |
| CFI3-R07 | Quem esclarece falta de essenciais e conflitos? | Consultor do caso; Gestor se indisponibilidade realmente comprovada, sem edição manual da ficha | S0 + S1 + FV | **ABERTO [R]** |
| CFI3-R08 | Qual a semântica de inbound após cutoff? | Recibo histórico imutável, mas elegibilidade de aplicação revalidada; novo fechamento permite nova F03 | S0 + OpenAI | **ABERTO [R]** |
| CFI3-R09 | Privacidade de campos financeiros/documentos e retenção? | Minimizacão explícita, base legal/finalidade e trilha de acesso antes de E04/E05 | S0 + segurança/privacidade | **ABERTO [R/V]** |

**Nada acima é decisão externa já tomada.** A questão da integração direta Banco permanece **adiada**; não usar F03 como atalho para transmissão bancária.

## 5. Rastreabilidade de aceite futuro

- **SYN-06/07, 33/34/35/36/37/38/42/69:** isolamento, histórico, cutoff, multimodal, ficha.
- **SYN-08/09/10/14/15:** semântica de versões, evento/resultado, recheck e idempotência.
- **SYN-39/40/41:** essencial e retorno sem edição, `intake_paused`.
- **SYN-43/44/45/46:** `perdido` por desistência, negativa bancária/venda e remessa.
- **CFI-T01..T36:** matriz da FV histórica; precisa revisão do dono FV, **não declara execução OpenAI**.

**Prova para declarar [R] resolvido:** ata/commit de **dono S0** sobre schema/IDs/versões e validação, revisão OpenAI da porta tipada, aceite S1/FV das operações humanas, Meta/privacidade para evidências multimodais, matriz E02 atualizada. Apenas depois pode virar contrato canônico. **Status desta entrega: pacote para ratificação, 0 execução OpenAI.**
