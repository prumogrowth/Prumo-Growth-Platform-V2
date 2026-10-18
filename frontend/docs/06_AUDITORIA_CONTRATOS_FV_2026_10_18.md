# Auditoria dos contratos técnicos da frente visual — 18/10/2026

**Escopo auditado:** arquivos preparados na branch `feat/frontend-plataforma-visual` (README e docs 01–03); documentos normativos do pacote de 17/10 (00A, 13A, 21–24, 26, 40, 41); decisão organizacional D-ORG-01 na branch S0; contratos OAI-05 e E01 v0.2 na branch OpenAI; referência à S1 sintética sob S0. **Resultado:** nenhum contrato próprio frontend↔S0 ou conclusão→extração existia na branch; FV-01 e FV-02 são sua primeira redação [P], não protocolos previamente aprovados. Testes reais não executados.

## Achados e encaminhamentos

| ID | Severidade | Achado documentado | Tratamento nesta branch |
| --- | --- | --- | --- |
| FV-AUD-01 | Importante | O2/O3 do doc.24 e SI03/UQ03 do doc.40 ainda sugerem correção/edição de ficha, enquanto a nova orientação elimina **preenchimento manual rotineiro** | FV-01/FV-02 e atualização do mapa de telas: O3 nominal de consulta, conferência e pendência; C13 somente exceção [D] |
| FV-AUD-02 | Importante | C01–C24 (doc.26) e UQ01–09 (doc.40) **não cobrem inteiramente** clique Concluir → execução F03 → resultado gravado | FV-02 acrescenta operação **lógica candidata**, sem roubar numeração C/UQ nem implementar S0 |
| FV-AUD-03 | Crítico se implementado incorretamente | Browser chamar API OpenAI diretamente, controlar catálogo/escopo ou gravar dados extraídos permitiria fuga de dados, autoria falsa e bypass | Contrato exige browser→S0→OpenAI→S0; segredo e persistência só no backend |
| FV-AUD-04 | Importante | OAI-05 e E01 v0.2 documentam a extração. **Em leitura posterior, a E01 já adotou o nome candidato `human_close_extract`**, mas os exemplos de request/response continuam divergentes; não são API única aprovada | Comparação campo a campo documentada em CFI-01; harmonização física é de S0/OpenAI; frontend não implementa o adaptador |
| FV-AUD-05 | Importante | 'Concluir' é ambíguo e pode parecer venda, fechamento de ciclo ou envio bancário | FV-02 especifica **conclusão técnica de conversa humana**, sem transição comercial; rótulo/semântica finais [R] |
| FV-AUD-06 | Crítico se implementado incorretamente | Regras D41/D-ORG de papel e atribuição não podem ser feitas só por seleção no browser | S0 revalida ator, concessionária, concessão, caso e versão; gestor autoatribuído tem direitos OP só no caso |
| FV-AUD-07 | Importante | Normas doc.23/D41-04 ainda aprovam correção humana individual excepcional | **Não revogada**: manter rota extraordinária sob auditoria; eventual retirada completa exige nova decisão expressa |
| FV-AUD-08 | Importante | Fonte/catálogo/validação de e-mail, nome, CPF e outros campos ainda não são lista-mestre normativa; tratamento de dados pessoais está condicionado | Não definir campos obrigatórios ou enviar conteúdo real; S0 autoriza catálogo, dados e proveniência |
| FV-AUD-09 | Importante | Sucesso de clique ou retorno OpenAI não comprova preenchimento da ficha | Somente nova versão persistida/confirmada pelo S0 habilita mensagem de sucesso |
| FV-AUD-10 | Importante | Resposta tardia, nova mensagem, duplicidade e revogação podem revelar/alterar dados indevidamente | Exigir snapshot, controle de versão, idempotência, descarte de cache e feedback honesto |
| FV-AUD-11 | Observação | Documentos R1–R4 tratam de MCP administrativo, não dashboard web com escrita geral | Não criar painel administrativo por inferência |
| FV-AUD-12 | Observação | S1 sintética permanece na frente S0, com UX e testes anteriores | Não copiar nem modificar outra branch; examinar antes de nova implementação |

## Rastreabilidade e classificação

- **[D] Normas anteriores:** oito estados; doc.23 (cadastro pronto e correção excepcional); doc.41 D41-01..06; D-ORG-01; prova real de banco e intervenção humana; handoff IA definitivo.
- **[D-direção atual do responsável]:** operador não faz preenchimento manual de cadastro como fluxo rotineiro; após concluir conversa humana, ocorre processamento OpenAI para extrair e preencher por S0 quando validado.
- **[P] Desenho desta branch:** FV-01 e FV-02; estados e rótulos de UX, comando lógico, projeção de progresso e testes.
- **[R]:** evento/rota/JSON final S0, cadastro mestre, compatibilidade de fluxo com oito status, exceção C13 na UI, revisão cruzada OpenAI↔S0↔frontend.
- **[V]:** direitos e condições externos de Banco, Meta, LGPD, áudio e dados sensíveis.

## Limite e veredito de auditoria

**Auditoria documental: concluída quanto às fontes inspecionadas e lacunas localizadas. Contratos FV-01/FV-02: REDIGIDOS, MAS NÃO HOMOLOGADOS INTERFRENTES.** Não afirmar aprovação de API, autorização de produção, segurança efetiva de RLS nem validação de layout e testes. Não existem testes de contrato ou extração executados por esta branch. Não alterar status do projeto nem incrementar barra 19F automaticamente.

**Próximo gate obrigatório antes de conectar qualquer frontend real:** aceite das estruturas pelo proprietário S0 e da ponte de extração pela frente OpenAI, definições de catálogo de campos e da política de privacidade/autorização; depois executar casos de testes sintéticos. Sem implementação, deploy, segredos ou dependências neste ato.

## Adendo — auditoria cruzada posterior com S0/OpenAI (18/10/2026)

O relatório original acima era a auditoria **interna da frente FV** e registrava lacunas de forma preliminar. Agora existe [CFI-01](07_CONCILIACAO_INTERFRENTES_FV_S0_OAI_v0_1.md), baseado também em leitura de S0 e das versões mais recentes OAI-05/E01. A atualização do item FV-AUD-04 reflete a **padronização do nome** `human_close_extract`, **não** a aprovação de payload. As divergências de `trigger_ref/closure_event_id`, `field_suggestions/fields_proposed` e `missing_field_keys/missing_fields` continuam pendentes.

[Matriz MAT-CFI-01](08_MATRIZ_ACEITE_CONTRATUAL_FV_S0_OAI_v0_1.md): 36 testes contratuais definidos [P], **0 executados neste trabalho**. Gate de revisão S0/OpenAI permanece [R]. Não confundir auditoria documental da FV com validação assinada pelas outras duas frentes.
