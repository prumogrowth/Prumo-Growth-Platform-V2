# E02-REV v0.3 — Pacote de revisão cruzada, decisões e gate de aceite

> **CF-OP-02/FREQ [R] acrescido (22/10/2026):** [análise Meta frequency capping e F02](./CF_OP_02_META_FREQUENCY_CAPPING_F02_2026_10_22_v0_1.md). Perguntas FREQ-R01..R05 exigem resposta de S0/Meta/Prumo: cota de MARKETING adaptativa (sem número oficial universal confirmado), rejeição 131049, política local, duas falhas técnicas e relógio C09. **66 testes unitários offline Node** deste incremento, **0 execuções originais SYN**; nenhuma ratificação.

> **Nova evidência E04 isolada, não ratificação E02:** [normalizador sintético `sent`/falhas Meta](./e04_offline_lab/transport-evidence.mjs) testado por [28 casos em Node](./e04_offline_lab/tests/transport-evidence.test.mjs), 28 PASS/0 FAIL. Complementa SYN-50..54 e cenários correlatos, mas **não** prova webhooks, recibos ou elegibilidade estado/fase da S0/Meta. E02-REV e as issues #6/#15 permanecem abertas.

> **Portões de conhecimento e MCP explicitados:** [KH-R01..KH-R08](./E01_GOVERNANCA_CONHECIMENTO_MCP_PORTOES_v0_4.md) e [24 controles adversariais AX](./E02_MATRIZ_ADVERSARIAL_CONHECIMENTO_MCP_v0_1.md). Nenhum foi homologado pela S0/Prumo; seus EXPECTED são revisões documentais, **não** resultados de teste.

> **QA interna documental:** [E02-QA v0.1 — 70 casos, 65 P0/5 P1 e 7 achados editoriais corrigidos](./E02_AUDITORIA_QA_GABARITOS_70_v0_1.md). A auditoria **não fecha** E02-REV nem E02-FIX: seguem pendentes donos de interfaces, schema, provas e autorização E04.

> **Material adicional para os revisores [P/R]:** [E01-INT v0.4 — portões do adaptador, resultados e erros](./E01_CONTRATO_TIPADO_ADAPTADOR_FALHAS_v0_4.md). Usar como proposta de contrato a homologar, não como evidência de implementação. Questões encaminhadas às issues #4/#6/#15 continuam pendentes.

> **Novo apoio à ratificação:** [resumo de sete decisões por frente](./E02_RESUMO_DECISOES_PARA_RATIFICACAO_v0_4.md), [manifesto de evidências F03](./CFI_01_MANIFESTO_HISTORICO_F03_CANDIDATO_v0_1.md) e [70 oráculos E02 v0.4](./E02_CADERNO_70_ORACULOS_E_OBSERVAVEIS_v0_4.md). Revisores **não** homologaram campos/ACL nem liberaram implementação por esses textos.

**Elaborado em:** 22/10/2026. **Status real:** **PACOTE DOCUMENTAL PREPARADO; E02-REV NÃO RATIFICADO; E02-FIX PARCIAL DOCUMENTAL; 0 TESTES OPENAI EXECUTADOS.** Isto é checklist de decisão, **não** pedido de autorização de implementação, merge, acesso a segredos, transferência de dados ou gasto. Todas as pendências [R/V] continuam abertas até prova expressa da frente titular.

## 1. Quadro executivo para revisores

| Frente / contrato | O que OpenAI já entregou nesta branch | O que falta ao dono | Pode avançar E04? |
|---|---|---|---|
| **F03/CFI-01** | OAI-05/OAI-07/E01 v0.3; [mapa CFI-01 v0.3](./CFI_01_CONCILIACAO_PONTE_F03_INTERFRENTES_v0_3.md); SYN-06/07/08/09/10/33..46/69 | **S0:** identidade, histórico de todos casos/loja, versões distintas, catálogo, status/erro, recheck APPLY. **S1/FV:** Concluir e pendência sem edição. **Meta/privacidade:** mídia. | **Não** |
| **F02/CF-OP-02/C09** | OAI-08/E01 v0.3; [mapa CF-OP/C09 v0.3](./CF_OP_02_C09_CONCILIACAO_F02_INTERFRENTES_v0_3.md); SYN-17/19/20/47..56 | **S0/Meta:** elegibilidade de templates/estados/finalidades, prova `sent`, falhas definitivas; **S1:** pedido/rota pós-humano; custos e opt-out. | **Não** |
| **Conhecimento/habilidades** | [E01-KH v0.3](./E01_CONHECIMENTO_HABILIDADES_E_MCP_OPERACIONAL_v0_3.md); SYN-57..65/70 | **S0/Prumo:** esquema físico, ACL, versionamento, semântica de vigência, owner da base, API de busca e operações já implementadas. | **Não** |
| **MCP Diretor** | Regras de confirmação por operação e auditoria protegida; SYN-65..68 | **S0/MCP:** serviços de prévia/confirmar com vínculo criptográfico ou equivalente, grants, anti-replay, auditoria imutável fora da superfície MCP; UI/ator. | **Não** |
| **Voz/privacidade e modelos** | OAI-06 histórico + [segurança E02 v0.3](./E02_SEGURANCA_E_GATES_OPERACIONAIS_v0_3.md) | **Meta/privacidade:** consentimento, mídia disponível, prazo de retenção, transferência ao provedor, minimização; **responsável:** orçamento e métricas (etapas posteriores). | **Não** |

**Importante:** testes PG17/GoTrue publicados pela S0 no PR #12 são provas **somente da S0**. A ponte `VERIFIED_CONTRACT_PENDING` não é API OpenAI pronta; não foi reexecutada nesta frente nem fornece payload F03. A issue #4 de 18/10 conserva referência a "correção humana excepcional" **superada pela decisão posterior de não editar ficha pelo Consultor**. A issue #6 de 20/10 conserva redação anterior que não deve provocar F02 automática por resultado F03. A issue #15 de Meta (22/10) já aponta essas duas divergências como pendentes de conciliação.

## 2. Critérios de saída E02-REV — somente marcar com prova

**Campos por linha:** `ID | Responsável decisor | Evidência/versionamento aceitos | Resultado PASS/NEEDS_REVIEW/REJECTED | Data | Link do aceite`. **Estado inicial de TODAS as linhas: NEEDS_REVIEW; sem assinatura.**

| Gate | Evidência mínima para aprovação documental | Quem aprova | Estado |
|---|---|---|---|
| REV-01 | Evento do Concluir e snapshot/manifesto de histórico da pessoa/loja multi-caso, cutoff e identidade com múltiplos telefones | S0 + OpenAI + S1/FV | **PENDENTE** |
| REV-02 | Dicionário do envelope de F03 com tipos, proveniência, versões de ciclo/caso/ficha/catálogo separadas, política de concorrência e erro | S0 + OpenAI | **PENDENTE** |
| REV-03 | Matriz S0 de transições e motivos (inclusive `perdido` por desistência), proibição de `vendido` automático e prova externa de remessa/negativa | S0 + produto/financeiro, FV para operação humana | **PENDENTE** |
| REV-04 | ACL, papéis, retorno de pendência para Consultor ou Gestor se indisponível no caso, ausência de edição pelo Consultor, comportamento `intake_paused` | S0 + S1 + FV | **PENDENTE** |
| REV-05 | Pedido distinto F02 pós-humano, rotas, estados/fases C09, limites, templates e finalidades versionados, slots resolvidos no envio | S0 + Meta + OpenAI | **PENDENTE** |
| REV-06 | Prova real de `sent`, sem confundir `accepted`/`queued`/`unknown`, e estados de falha definitiva/cancelamento/retry | S0 + Meta | **PENDENTE** |
| REV-07 | Escopo/ACL das bases institucionais e por loja, elegibilidade temporal de **base e fato**, reativação, cache opcional, quatro globais sem override | S0 + Prumo + OpenAI | **PENDENTE** |
| REV-08 | Habilidades só sobre ferramentas existentes; guias MCP separados dos prompts; mutação confirmada individualmente; auditoria protegida impossível de editar por MCP | S0 + Prumo/MCP + segurança | **PENDENTE** |
| REV-09 | Finalidade/minimização, dados financeiros, disponibilidade multimodal, LGPD/Meta, retenção e transferência ao fornecedor | Privacidade + S0 + Meta; Banco se exigido | **PENDENTE** |
| REV-10 | E02 corpus e critérios P0, source of truth dos EXPECTED, versões e responsabilidade de cada cenário, inclusive negativas interfrentes | OpenAI + donos relevantes + responsável | **PENDENTE** |
| REV-11 | Gate **expresso de início de implementação E04**, separado da aceitação técnica de contratos | Responsável do projeto | **NÃO SOLICITADO/NÃO CONCEDIDO** |
| REV-12 | Ambiente/projeto/secret manual e orçamento E05 para testes **somente fictícios**, quando aplicável | Responsável do projeto + segurança | **ADIADO** |

**Semântica de aceite:** ratificação precisa de artefato rastreável assinado/aprovado pelo proprietário real, com ID de contrato, versão, deltas, evidências e ressalvas. Silêncio em issue, texto desta frente ou existência de branch **não são aceite**. "Aceite parcial" não transforma os outros gates em PASS.

## 3. Roteiro das decisões sem invadir outras frentes

1. **F03 primeiro (issue #4):** encaminhar CFI3-R01..R09 ao dono S0/S1/FV/Meta com o mapa campo a campo, destacando que PR #12 comprova recibo limitado e que história lógica multi-casos não está contemplada. Pedir escolha **explícita** sobre `expected_cycle_version` versus versões de ficha/caso/catálogo, prova de cliente e manifesto de histórico.
2. **F02/C09 (issue #6):** encaminhar F02C-R01..R07 ao S0/Meta, incluindo pergunta objetiva de elegibilidade por status+fase e distinção entre `sent`, aceites e falha definitiva. Aguardar resposta formal; não codificar a regra pelo nome do status.
3. **Conhecimento/MCP:** preparar dicionário físico de dados/regras com Prumo/S0; decidir tecnologia só depois de ACL/recuperação e confirmação por operação pactuadas. Os **quatro globais**, exclusão de instruções de loja e auditoria imutável são decisões **funcionais**, não propriedades de tecnologia vetorial já escolhida.
4. **Segurança e E02-FIX:** fechar fontes permitidas e geração de dados inteiramente fictícios para os 70 cenários; completar amostras com assertions formais após decisão de schema. **Nenhuma** chamada real de OpenAI/Meta/Banco.
5. **Marco de autorização:** somente após o planejamento estar pronto e o responsável liberar **expressamente E04**, preparar stub/harness offline; E05 e além possuem gates independentes.

**Dependência externa evitada:** não abrir issue/pr em nome de S0, não editar schema em branches alheias, não mudar roadmap global, não escolher integração Banco (investigação adiada), não confundir status comercial com evento técnico.

## 4. Proposta de pacote de aceite por revisão

Em qualquer revisão conjunta, registrar um item por decisão:

```text
ID_DECISAO: CFI3-Rxx | F02C-Rxx | REV-xx
DONA_DA_DECISAO: [frente/pessoa humana autorizada]
ESTADO: PENDENTE | ACEITO | ACEITO_COM_RESSALVAS | DEVOLVIDO
ESCOPO_EXATO: [campo/regra/operação/tenant/dados abrangidos]
ARTEFATO_E_VERSAO: [link/commit/versão do contrato]
PROVA_DE_REVISAO: [link do aceite humano]
IMPACTO: [S0/S1/FV/Meta/OpenAI]
REGRESSAO_QUE_COBRE: [SYN-xx, CF2-xx, CFI-Txx]
PONTOS_NAO_RESOLVIDOS: [...]
```

Não inventar aprovações nem preencher campos de pessoa/assinatura. Se há conflito com decisão [DN] posterior, escalar a **questão**, não homologar trecho histórico pelo simples fato de já ter código.

## 5. Medições e status antes de executar

- **32 SYN originais + 38 novos = 70 cenários documentados**, com 10 exemplos de fixtures narrativas. **0 fixtures executadas**, **0 PASS/FAIL observados**, **0 métricas medidas** de modelos desta frente.
- **E01:** intenção funcional/documental atualizada, **interface S0 física não ratificada**.
- **E02-DOC:** pacote de critérios, matriz e mapas de divergências **preparado nesta branch**; revisão e aceite ainda pendentes.
- **E02-REV:** **PENDENTE**; E02-FIX físico **NÃO FECHADO** (10 exemplos narrativos não equivalem a 70 fixtures executáveis).
- **E03:** credenciais/billing adiados; **E04/E05:** não iniciados; **E06–E08:** não iniciados.
- **PR #3 Draft:** não executar merge ou alterar PRs S0/S1/Meta/FV sem autorização específica.

**Referências imutáveis desta rodada:** [PR #12 S0](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/12), [issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4), [issue #6](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6), [issue #15](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/15), AL-IA-00/01/02/03/04/07/08 e contratos v0.3 da OpenAI. Se mudar outra branch, revalidar suas fontes antes de promover qualquer gate.
