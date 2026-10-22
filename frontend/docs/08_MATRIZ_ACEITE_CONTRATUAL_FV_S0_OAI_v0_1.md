> **EMENDA SUPERVENIENTE — 22/10/2026 [D/E]:** para a **frente Frontend** prevalece o [FV-DOC-03 — contrato funcional vigente](./38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md). **A plataforma da Prumo ainda não tem nome; LiberaCred é o produto da instituição financeira.** Papéis visíveis: **Diretor / Gestor / Consultor**. A ficha cadastral do **Consultor é integralmente não editável**, inclusive sem correção excepcional C13 na UI; pendências são esclarecidas por atendimento, e atualização autorizada é confirmada pelo S0. **F01** atende, **F02** planeja templates, **F03** extrai após conclusão humana explícita; a troca de siglas em fala recente está marcada [R-SIGLA-01]. Assinatura de mensagem humana livre deve ser `Cargo Nome:\nMensagem` com validação pelo serviço. IA de melhoria fora da primeira versão. **Descrições anteriores incompatíveis abaixo são históricas e não critérios vigentes de aceite de UI.** Nenhuma alteração de código ou das outras frentes decorre desta emenda.

# MAT-CFI-01 — Matriz de conformidade e aceitação sintética FV ↔ S0 ↔ OpenAI | v0.1

**Data:** 18/10/2026. **Estado:** [P] cenários de teste especificados para futura execução e revisão dos donos S0/OpenAI. **NENHUM teste desta matriz foi executado**, e não existe API real certificada por esta matriz. Rastreabilidade: [CFI-01](07_CONCILIACAO_INTERFRENTES_FV_S0_OAI_v0_1.md), FV-01, FV-02, docs. 13A/21–23/26/40/41/D-ORG-01 e OpenAI OAI-05/E01.

## 1. Contratos sob teste

**Boundary A — UI→S0 [P/R]:** request de conclusão com `case_ref`, `expected_case_version`, `request_id`, `idempotency_key` *candidatos*. Dados de autenticação, permissões, concessionária real e snapshot são derivados pelo S0. Não se trata de endpoint nomeado ou implantado.

**Boundary B — S0→OpenAI [P/R]:** capacidade `human_close_extract`, com evento durável S0, recorte mínimo autorizado, versão/corte e catálogo; OAI-05 e E01 ainda necessitam consolidar o formato exato, **não converter payload por suposição**.

**Boundary C — S0→UI [P/R]:** retorno imediato de aceitação ou negativa, progresso técnico autorizado e UQ03/projeção da ficha persistida. O frontend nunca mostra resultado como gravado a partir somente de retorno do modelo ou de um HTTP 200.

**Fixtures:** identidades fictícias e três casos artificiais isolados em concessionárias Aurora/Horizonte; **mesmo telefone sintético em duas lojas** para prova de separação; marcações textuais fictícias, sem CPF real, credenciais, dados pessoais de clientes, Banco/Meta/OpenAI real ou persistência remota.

## 2. Matriz de testes de contrato (proposta, NÃO executada)

| ID | Dono primário | Cenário sintético | Critério observável |
| --- | --- | --- | --- |
| CFI-T01 | Front/S0 | Operador designado conclui conversa elegível | Pedido gerado uma vez com versão e chave idempotente; resposta imediata não afirma ficha atualizada |
| CFI-T02 | S0 | Operador não atribuído tenta concluir caso | Recusa sem vazar dados do caso ou da loja; UI desabilitada quando souber, servidor sempre revalida |
| CFI-T03 | S0 | Gestor apenas supervisor lê conversa e tenta concluir | UQ02 D2 leitura permitida; escrita recusada sem autoatribuição |
| CFI-T04 | S0 | Gestor autoatribuído executa conclusão | Permissão OP para **aquele caso**; atuação rastreada, sem estender a outros casos |
| CFI-T05 | S0 | Identidade Prumo com concessão A+B, revogada em B | Revogação de B impede leitura/conclusão em B, não elimina A |
| CFI-T06 | S0 | Telefone sintético igual em concessionárias A/B | Snapshot, campo, versão e resposta nunca se cruzam |
| CFI-T07 | S0 | Mesmo request/caso clicado duas vezes | Idempotência, uma conclusão/execução/versão por corte e política; UI não multiplica ação |
| CFI-T08 | S0 | Duas conclusões concorrentes versões distintas | Apenas ação atual é válida; retorno de CONFLICT_VERSION ou repetição determinística |
| CFI-T09 | S0/Meta | Mensagem inbound chega durante/apos fechamento | Watermark confiável impede misturar nova mensagem; reprocessamento precisa novo corte |
| CFI-T10 | S0/Meta | C12 mensagem de saída ainda incerta na hora da conclusão | S0 não afirma conteúdo entregue; regra de inclusão/exclusão do snapshot deve ser explícita e verificável |
| CFI-T11 | S0 | Reatribuição ou revogação após solicitação e antes da gravação | Política de continuidade S0 revalidada; saída tardia nunca amplia acesso nem sobrescreve indiscriminadamente |
| CFI-T12 | S0/OpenAI | Extrator recebe apenas recorte autorizado do caso | Nenhuma outra concessionária, prova D4 bruta, segredo, JWT ou material integral injustificado |
| CFI-T13 | OpenAI | Informação expressamente declarada, campo permitido, fonte válida | Proposta com `source_message_refs` ou equivalente canônico; S0 só grava se política permitir |
| CFI-T14 | OpenAI/S0 | Informação não dita na conversa | Proposta indica ausência; sem preenchimento por palpite/modelo |
| CFI-T15 | OpenAI/S0 | Informação contraditória nas mensagens | Conflito com fontes; S0 não escolhe silenciosamente valor e UI apresenta pendência |
| CFI-T16 | OpenAI/S0 | Operador sugeriu dado que cliente não confirmou | Não tratar hipótese do operador como declaração comprovada do cliente |
| CFI-T17 | OpenAI/S0 | Prompt injection no texto da conversa | Tratado como dado não confiável; nenhuma execução SQL, troca de escopo, mensagem, status ou permissão |
| CFI-T18 | S0 | OpenAI retorna campo fora do catálogo, tipo inválido ou sem origem | Rejeição desse campo; nenhuma persistência desse valor |
| CFI-T19 | S0 | Proposta parcial com dois campos elegíveis e um ausente | Se política permitir, apenas elegíveis viram versão efetiva; UI distingue aplicada/parcial/pendência conforme S0 |
| CFI-T20 | S0 | Saída apenas PROPOSED, sem commit S0 | Frontend **não** exibe “ficha atualizada” |
| CFI-T21 | S0 | Commit S0 confirmado com versão de ficha | UQ03 autorizado fornece versão, origem técnica e informações permitidas; UI confirma só após leitura confiável |
| CFI-T22 [REVISTO 22/10] | S0 | Dados da ficha mudaram após o snapshot por processo autorizado F01/F03/Diretor-MCP, sem edição do Consultor | Resultado obsoleto deve ser rejeitado/reprocessado por S0; não sobrescrever versão mais recente |
| CFI-T23 | S0/OpenAI | Timeout/429/401, payload inválido ou fornecedor indisponível | Erro técnico/retentativa segura sem avanço comercial, sem perda da ficha existente |
| CFI-T24 | S0 | Snapshot desatualizado, job repetido ou resposta fora de ordem | Sem dupla gravação e sem aplicar resultado a versão/caso divergente |
| CFI-T25 | S0/Meta/OpenAI | Áudio sem transcrição/autorização, ou transcrição incerta | Não declarar dado comprovado; pendência conforme política aprovada |
| CFI-T26 | Front/S0 | `em atendimento pelo operador` por exceção e conclusão F03 | Não reclassificar automaticamente como `cadastro enviado ao operador` |
| CFI-T27 | Front/S0 | Cadastro vindo completo da IA em `cadastro enviado ao operador` | Não converter extração pós-humana em novo handoff nem invalidar checklist IA existente |
| CFI-T28 | Front/S0 | Clicar Concluir | Não envia cadastro ao banco, não marca vendido/perdido, não cria nono status, não reativa IA Vendedora |
| CFI-T29 [REVISTO 22/10] | Front | Consultor tenta localizar/acionar correção cadastral excepcional C13 | **Nenhum campo ou comando de edição cadastral do Consultor existe**, nem excepcional; ficha é somente leitura |
| CFI-T30 | Front/S0 | Perfil perde autorização durante navegação/atualização | Dados e ações sensíveis saem da tela; backend nega consultas e comandos |
| CFI-T31 | S0/OpenAI | E01 retorna `extraction.field_suggestions`, OAI-05 `fields_proposed` | Não aceitar integração física enquanto não houver **uma versão canônica homologada** de request/response |
| CFI-T32 | Front/S0 | Ficha D3 técnica exibida a gestor não autoatribuído | Apenas situação/resumo autorizado; D2 integral permitido, D3/D4 bruto não |
| CFI-T33 | S0 | Conclusão/extração incerta após falha cadastral pontual | Sem suspensão automática geral dos atendimentos e sem reparo autônomo do software (doc.23) |
| CFI-T34 | Front/S0 | Novo contato após marco banco ou vendido | Atendimento humano separado; preserva histórico e não reativa IA |
| CFI-T35 | Produto/S0 | Catálogo de campos e política de dados não aprovados | Gate bloqueia uso de dados pessoais reais e afirmação de prontidão; nenhuma inferência de obrigatórios |
| CFI-T36 | Front/S0 | Acessibilidade e responsividade de ações/progresso | Teclado, anúncio de estado sem falso sucesso, vazio/erro, mobile e contraste revisados antes de homologar UI |

## 3. Evidências mínimas para execução futura

Cada caso precisa preservar, em ambiente **descartável/local**:
- versão exata de **contrato FV**, **S0** e **OAI-05**; SHAs das branches/revisões, fixtures e comando de teste;
- request/correlation/event refs **sintéticos** e estado antes/depois sem PII; resultado esperado × obtido e motivo de falha;
- comprovação de autoria técnica, versioneamento, idempotência e ausência de efeito colateral onde pertinente;
- testes negativos de autorização no backend, não apenas screenshot ou filtro visual;
- testes adversariais de isolamento, concorrência, dados ausentes, prompt injection, entrada inválida, atrasos e revogação.

## 4. Gates formais

| Gate | Evidência exigida | Status em 18/10/2026 |
| --- | --- | --- |
| G0 | Comparação FV-01/02 × docs 26/40 × OAI-05/E01 com divergências identificadas | **Concluída documentalmente**, ver CFI-01 |
| G1 | Decisão explícita S0/OpenAI sobre assinatura canônica, comando de conclusão, progresso e catálogo | **Pendente [R]** |
| G2 | Implementação exclusivamente sintética e testes CFI-T01–T36 em fronteiras reais de código | **Não executado** |
| G3 | Revisão de segurança, LGPD/Meta/Banco, autorização de ambientes/custos e validação visual | **Não autorizado** |

**Esta matriz não altera os 69/100 do doc.19F.** A execução da matriz, autorização de APIs e aprovação das frentes não podem ser inferidas de sua redação.
