# Frente de desenvolvimento visual — Plataforma Prumo (nome técnico provisório)

**Situação:** área de trabalho preparada em 18/10/2026. **Branch:** `feat/frontend-plataforma-visual`, criada a partir de `main` no repositório privado `prumogrowth/Prumo-Growth---Platform`.

Esta branch reserva o trabalho de **frontend, experiência de uso, navegação, visualização de dados autorizados, acessibilidade e componentes de interface** da plataforma de operação comercial do produto **LiberaCred, da instituição financeira**. **Prumo Growth** é identificação técnica; o **nome comercial da plataforma ainda não foi definido**.

## Estado desta entrega

- [x] Branch independente criada no repositório existente.
- [x] Mapa de escopo, responsabilidades e limites registrado em `docs/01_ESCOPO_E_FRONTEIRAS.md`.
- [x] Inventário inicial de telas e fluxos registrado em `docs/02_MAPA_DE_TELAS_E_JORNADAS.md`.
- [x] Materiais-base, precedência normativa e critérios de continuidade reunidos em `docs/03_MATERIAIS_E_PREPARACAO.md`.
- [x] Área `design/` reservada a materiais visuais.
- [x] Contratos técnicos FV-01 e FV-02 redigidos e auditoria documental FV registrada; **homologação S0/OpenAI pendente**.
- [ ] Interface final, componentes e fluxos codificados.
- [ ] Testes visuais/responsivos e acessibilidade executados.
- [ ] Integração autenticada com backend.

**Nenhuma hospedagem, domínio, serviço externo, conexão com banco, credencial ou ambiente Supabase foi criado ou alterado por esta frente.** Dados reais de clientes não podem ser inseridos em mocks, fixtures, imagens ou commits.

## Importante: já existe uma S1 sintética

A branch `feat/s0-fundacao-prumo` já contém `frontend/s1/`, um **protótipo visual local**, com regras/testes sintéticos em desenvolvimento pela frente de fundação. **Não copiar, reescrever, mover, mesclar ou editar esses arquivos a partir desta branch sem revisão e coordenação com sua frente responsável.** Nossa branch parte de `main` para preservar independência. Sua integração ou eventual reaproveitamento da S1 requer comparação de escopo e revisão via PR, sem sobrepor trabalhos.

As branches `feat/s2-openai-adapter-sintetico` (provedor OpenAI) e `docs/whatsapp-meta-concessionária de demonstração-poc-20261017` (Meta/WhatsApp) também permanecem sob suas respectivas frentes.

## Antes de escrever o primeiro componente

1. Seguir as decisões aprovadas D41-01..06, a regra organizacional D-ORG-01 de 18/10 e os oito estados comerciais canônicos.
2. Examinar o caderno de telas (doc. 24) e o comportamento já demonstrado em `frontend/s1/`, **sem inferir que são código ou layout aprovados para produção**.
3. Separar visualização/protótipo de autorização real: permissões, transições e auditoria efetivas são responsabilidade do backend.
4. Definir a abordagem de interface com atenção à integração futura; não escolher hospedagem, domínio ou integração real nesta etapa.
5. Usar **somente conteúdo sintético** e submeter a revisão qualquer interface com ações sensíveis.

Nenhuma mudança nesta branch equivale a aceite de implementação, aprovação de MVP global, autorização externa ou incremento automático na régua de planejamento.

## Contratos técnicos e nova regra de extração pós-humana (18/10/2026)

A partir da decisão funcional mais recente, **operadores não preenchem rotineiramente os campos do cadastro**. O fluxo normal é **conversa humana → ação “Concluir atendimento” (rótulo provisório) → processamento OpenAI de retaguarda → validação/persistência pela S0 → ficha consultável com pendências**. A interface não chama a OpenAI diretamente nem modifica dados no banco. Concluir não envia ao banco, não marca vendido/perdido e não reativa a IA Vendedora.

- [FV-01 — contrato visual ↔ S0](docs/04_CONTRATO_FV01_UI_BACKEND_v0_1.md) — responsabilidades, leitura/escrita, permissões e telas.
- [FV-02 — conclusão de conversa e extração](docs/05_CONTRATO_FV02_CONCLUSAO_EXTRAÇÃO_POS_HUMANA_v0_1.md) — ação, feedback, idempotência, falhas e compatibilidade.
- [Auditoria dos contratos](docs/06_AUDITORIA_CONTRATOS_FV_2026_10_18.md) — achados, limites e pendências.

**Importante:** docs 23 e 41 continuam autorizando **correção humana excepcional** da ficha versionada; isto não significa voltar ao preenchimento manual rotina. O contrato interno OpenAI OAI-05/E01 está em outra branch e permanece sob responsabilidade da sua equipe. FV-01/FV-02 são [P/R] e não foram implementados nem aprovados entre frentes.

## Conciliação contratual S0/OpenAI — 18/10/2026

- [CFI-01 — relatório de conciliação interfrentes](docs/07_CONCILIACAO_INTERFRENTES_FV_S0_OAI_v0_1.md): mapeia FV-01/FV-02, contratos S0 (docs 26/40) e OAI-05/E01, divergências dos envelopes e critérios de decisão.
- [MAT-CFI-01 — 36 cenários de aceite contratual](docs/08_MATRIZ_ACEITE_CONTRATUAL_FV_S0_OAI_v0_1.md): **especificados, não executados**.

A OpenAI padronizou o nome candidato `human_close_extract` nos documentos OAI-05/E01. **Ainda há divergências nas estruturas de request/response**, cuja resolução pertence às frentes S0 e OpenAI. A operação browser→S0 permanece sem nome físico; o navegador **nunca** envia diretamente à OpenAI. Nenhuma revisão por proprietários S0/OpenAI, teste integrado ou deploy foi concluído nesta frente.

**Rastreamento de revisão cruzada:** [GitHub issue #4 — CFI-01](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4), ABERTO, ainda sem validação dos proprietários das frentes S0 e OpenAI.

## FV-UI-001 — primeira estrutura visual de mensageria (18/10/2026)

A versão **navegável e independente da lógica S0**, com composição inspirada no padrão de mensagens do WhatsApp sem copiar a marca, está em [`frontend/visual/`](./visual/README.md). Inclui `index.html`, `styles.css`, `app.mjs`, `fixtures.mjs` e testes Node, sem dependências. Abrir localmente com Python conforme o README de `visual/`. O desenho foi criado para **desktop (lista + conversa + detalhes)** e **celular (lista → conversa → detalhes)**.

**Estado desta etapa:** código visual sintético [P], navegação e estilos elaborados; **sem integração** com S0, Supabase, OpenAI, Meta ou Banco. Usuários e informações exibidas são inteiramente artificiais; filtros JavaScript não são autenticação real. A nova direção exclui preenchimento cadastral manual habitual. O botão de conclusão e a extração retornam apenas sinais artificiais no navegador.

[Diretriz e evidências FV-UI-001](./docs/09_DIRETRIZ_VISUAL_MENSAGERIA_RESPONSIVA_v0_1.md). A frente S0 abriu também `feat/s1-002-equipe-prumo`, que permanece separada; **não copiar nem editar seu diretório `frontend/s1/`**. A aprovação visual do responsável e a auditoria interfrentes do [issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4) seguem pendentes. Sem merge ou mudança automática na pontuação de planejamento 19F.

## FV-UI-002 — Evolução sem dependências externas

Continuação realizada na pasta [`frontend/visual/`](visual/README.md): indicadores de fila e filtros, visão sintética de equipe para gestor, abas de caso com histórico e notas internas, modelos de erro/pendência/versão para extração pós-humana e navegação desktop/mobile. **12 testes Node PASS**, mais ensaio Chromium sintético nos quatro tamanhos; ver [auditoria](docs/10_AUDITORIA_FRONTEND_FV_UI_002_2026_10_18.md). Só a branch frontend foi modificada. O responsável poderá avaliar a experiência visual quando estiver madura, sem antecipar homologação funcional das integrações.


## CF-OP-02 — extensão de jornada para templates e janelas

Esta frente também deve prever concluído humano **sem retirar de imediato o chat**, expiração Meta diferente do encerramento humano, seleção de um template ou solicitação de cadeia pós-humana quando janela expirada e caso não concluído, e perda só se S0 confirmar C09 aplicável. Responsável atual do caso é fornecido pelo backend e pode mudar por S1-002; histórico não é apagado. [FV-03](docs/09_CF_OP_02_CONTRATO_VISUAL_JANELA_CADEIAS_v0_1.md) estabelece a fronteira: interface não cria agenda, não escolhe templates sem S0, não conversa com OpenAI/Meta diretamente. Integração não executada; revisar issue #4/#6 e PR #7.

## FV-03 / CF-OP-02 — revisão e reparos de coerência (18/10/2026)

Foi localizado o novo contrato [FV-03 — janela e cadeias contextuais](docs/09_CF_OP_02_CONTRATO_VISUAL_JANELA_CADEIAS_v0_1.md) e auditada a implementação FV-UI-001/002. A interface sintética agora representa **janela Meta projetada pelo backend, histórico separado de lista ativa, template único elegível por caso, solicitação de cadeia contextual, estados de envio final, situação de conclusão e fila protegida**. Correções de segurança de apresentação: sem texto livre fora da janela projetada, sem tratar template agendado como enviado, sem perda comercial calculada no navegador, sem permissões para profissional suspenso e sem escolher template fora da elegibilidade do caso.

[Relatório FV-AUD-03](docs/12_AUDITORIA_CONFORMIDADE_FV03_CF_OP_02_2026_10_18.md) — **24 testes de lógica em harness V8 PASS** sobre módulos recuperados do GitHub, sintaxe JavaScript PASS e inspeção estática sem chamadas externas. O script de navegador foi atualizado, **mas ainda não foi executado depois dos reparos FV-03**; não afirmar homologação de mobile/desktop pós-revisão. Contratos físicos S0/OpenAI/Meta, privacidade e provas de envio seguem pendentes. A apresentação visual ao responsável continua reservada à etapa posterior; sem merge/deploy ou aumento automático do progresso auditado.

## FV-UI-005 — Verificação de interação (18/10/2026)

Foram criados ensaios DOM de navegação e funções (desktop/mobile) independentes de APIs, com correção de atalho de teclado em diálogo modal. **36 testes sintéticos executados PASS no harness V8** (24 de regras + 12 de interação). Execução Node direta e Chromium pós-FV-03 permanecem pendentes. [Relatório e limites](docs/14_TESTES_INTERACAO_FV_UI_005_2026_10_18.md). Não alterar progresso 19F, não declarar GO de produção.

## FV-UI-006 — Integridade de estado e callbacks (18/10/2026)

Atualização em `frontend/visual/`: conclusão solicitada não é conclusão confirmada; projeções de conclusão ausentes não são interpretadas como sucesso; mensagens/notas e diálogos antigos deixam de produzir efeitos ao trocar de caso, loja ou ator. **48 verificações sintéticas aprovadas no harness V8** (25 regras, 17 interações DOM, 6 inspeções de fonte), com [auditoria e limites](docs/15_AUDITORIA_FV_UI_006_FIDELIDADE_E_CONCORRENCIA_2026_10_18.md). Ainda pendem execução Node nativa e Playwright real, além de revisões externas. Sem alteração do progresso 19F.

## FV-UI-007 — Ficha e proveniência fictícias (O3)

Implementada em [`frontend/visual/`](visual/README.md) a visualização de ficha parcial projetada, com origem, versão, pendências e conflitos; acesso de supervisão restringido a resumo **sem detalhes D3/D4**. **60/60 verificações sintéticas PASS** no harness V8 sobre os arquivos do GitHub, sem testes Node ou Chromium real desta versão. [Auditoria FV-UI-007](docs/16_AUDITORIA_FV_UI_007_FICHA_PROVENIENCIA_2026_10_18.md). Contratos físicos e integrações continuam pendentes.

## FV-UI-008 — Tela O4 bancária (19/10/2026)

A interface agora possui a aba **Banco** com acompanhamento sintético de remessa, prova e retorno, **sem registrar decisão, remeter cadastro, alterar estado ou criar ações bancárias**. Operadores designados veem projeções minimizadas; gestores não herdam evidências D4. **77/77 verificações sintéticas aprovadas em V8**, sem execução literal de Node/Chromium da branch. Ver [auditoria O4](docs/18_AUDITORIA_O4_BANCO_FV_UI_008_2026_10_19.md). Sem homologação real.

## FV-UI-009 — Novo contato após marcos (19/10/2026)

Implementada em `frontend/visual/` a jornada O5 **somente com fixtures**, conectando o atendimento original ao **novo ciclo humano independente** após `cadastro enviado ao banco` ou `vendido`, sem modificar estado original ou reativar a IA Vendedora. Navegação no mesmo escopo e com vínculo verificado; **96/96 verificações sintéticas PASS** no harness V8 sobre o GitHub. Node/Chromium da versão atual **não executados**. [Auditoria O5](docs/19_AUDITORIA_O5_NOVO_CONTATO_FV_UI_009_2026_10_19.md).

## FV-AUD-05 — Auditoria retrospectiva (19/10/2026)

Revisados FV-UI-004–009 contra FV-01/02/03 e as jornadas O1–O5. Corrigidos: resumo O3/O4 exposto a operador não designado; novo ciclo O5 indevidamente bloqueado pela falta de acesso ao caso anterior; cópias superficiais de fixtures O3/O5 contaminando reinicializações. **105/105 verificações sintéticas aprovadas em harness V8** (65 regras, 25 DOM, 15 fonte). Não houve execução Node direta, Chromium real ou homologação S0/Meta/Banco. [Auditoria FV-AUD-05](docs/20_AUDITORIA_RETROSPECTIVA_FV_UI_004_009_2026_10_19.md).

## FV-UI-010 — Equipes por operadores e pausa global de leads (19/10/2026)

Gestão fictícia G2 refeita para **equipes por operador**: Marina gerencia Rafael/Lia; Daniel gerencia Bianca/Otávio, inclusive quando concessionárias coincidem. Lojas dos operadores são **somente leitura** e pertencem à alçada do responsável. Pedido local de **pausa/retomada dos novos leads do operador inteiro** não efetiva redistribuição, suspensão, alteração de permissão nem fluxo Meta. **123/123 verificações sintéticas passaram em V8** (75 regras, 30 DOM, 18 estáticas); Node/Chromium real ainda pendente. [Auditoria FV-UI-010](docs/22_AUDITORIA_G2_EQUIPE_POR_OPERADORES_PAUSA_GLOBAL_2026_10_19.md); [divergência S0/S1-002 #9](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/9).

## FV-UI-011/012 — G3 Monitoramento e G4 Lotes (19/10/2026)

O diálogo de gestão por operadores possui **Operadores**, **Monitoramento** e **Lotes**, preservando equipes e concessionárias concedidas pelo responsável. G3 apresenta indicadores agregados e sinais projetados (espera ilustrativa, fila protegida, banco pendente, recontato), **sem relógio Meta/C09 nem SLA presumido**. G4 exibe lotes sintéticos por equipe e qualidade/versionamento, **sem upload, ingestão, edição de concessões ou distribuição**.

**G3 após conciliação:** [auditoria](docs/23_AUDITORIA_G3_MONITORAMENTO_UNIFICADO_FV_UI_011_2026_10_19.md). **G4:** [auditoria](docs/24_AUDITORIA_G4_LOTES_EQUIPE_FV_UI_012_2026_10_19.md). **180/180 verificações sintéticas de regressão G2/G3/G4 aprovadas no harness V8** (110 regras, 45 DOM, 25 fonte). Não foram executados Node/Chromium da revisão atual nem integração S0/S1.
