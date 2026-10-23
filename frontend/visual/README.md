# FV-UI-001 — Central de Atendimento, estrutura visual responsiva

> **Estado mais recente (FV-UI-017, 22/10/2026):** aplicar primeiro [FV-DOC-03](../docs/38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md) e [o registro do incremento](../docs/41_FV_UI_017_INTEGRIDADE_CONTEXTO_MENSAGENS_2026_10_22.md). Papéis visíveis **Diretor/Gestor/Consultor**; identificadores técnicos legados e oito estados comerciais mantidos. A ficha do Consultor **não possui edição manual, inclusive C13**. O composer agora distingue texto digitado, prévia de autoria e mensagem incluída **somente na demonstração**, nunca enviada. Ao trocar caso/ator/loja, o rascunho anterior é descartado. Testes V8 do novo incremento não equivalem a Node/Chromium ou integração real. Registros históricos deste README permanecem datados de suas versões.

> **FV-UI-018 (22/10/2026):** adicionado [registro da fila compartilhada e case-only](../docs/42_FV_UI_018_PERMISSOES_DISTRIBUICAO_2026_10_22.md). Novo painel G2 de **fila sem titular por concessionária**, com ações fictícias sem resultado de S0; caso `A-117` demonstra acesso excepcional da Consultora Lia a **um único atendimento** de Aurora, sem acesso geral à loja. D-AL-02 de casos pausados continua separado da distribuição regular de novos leads. Testes V8 não são aceite Node/Chromium nem autorização real. Leituras históricas abaixo conservam seu contexto de época.

> **FV-UI-019 (22/10/2026):** acrescentadas [conclusões sucessivas e ficha viva sintéticas](../docs/43_FV_UI_019_CONCLUSOES_F03_FICHA_VIVA_2026_10_22.md). `A-108` contém dois eventos históricos de F03 **já projetados pela fixture** e um cenário alternativo para simular um novo clique de conclusão, com cutoff **candidato, não confirmado**. `A-114` mostra ficha atualizada e remessa antiga preservada, sem inferir edição manual ou movimentação bancária. Testes V8 não são homologação nativa nem integração S0.

> **FV-UI-020 (22/10/2026):** [registro de estados técnicos e matriz de aceitação](../docs/44_FV_UI_020_ERROS_TRANSPORTE_E_MATRIZ_ACEITACAO_2026_10_22.md). ACK Meta não prova envio; recibos e erros são apenas projeções sintéticas, sem reenvio automático, cadastro manual ou transição comercial. `C13` foi excluído das ações candidatas da UI. `run_acceptance.py` inventaria as 24 suítes e impede homologação sem revisão correta/Chromium. Execução V8 não substitui testes Node nativos.

> **FV-UI-021 (22/10/2026):** [preparação S0/S1 e acessibilidade](../docs/45_FV_UI_021_PREPARACAO_S0_S1_ACESSIBILIDADE_2026_10_22.md). O novo `integration-gate-view.mjs` classifica **somente estruturas candidatas**, nunca autentica, libera registros, comandos ou ações comerciais. O Frontend demonstra anúncio acessível de contexto, foco entre telas móveis, Home/End nas abas e ajustes para altura reduzida. Verificações V8 não substituem Node/Chromium/leitor de tela nativos.

> **FV-UI-022 (22/10/2026):** [proteções de Escape/rascunho e smoke Chromium](../docs/46_FV_UI_022_ESCAPE_RASCUNHO_SMOKE_REGRESSAO_2026_10_22.md). O Escape móvel agora recupera foco da tela visível, cancelamento de prévia conserva o rascunho só no atendimento original, o mock trata campos como `INPUT` e o smoke exige 12 casos na supervisão Marina/Aurora. Testes V8 aprovados; **execução nativa e homologação pendentes**.

> **FV-UI-023 (22/10/2026):** [validação offline de ZIP autenticado por hashes](../docs/47_FV_UI_023_MANIFESTO_ZIP_OFFLINE_NATIVO_2026_10_22.md). O pacote da branch pode ser baixado manualmente pelo GitHub e validado sem clone: `verify_offline_export.py` exige hashes Git de todos os arquivos da frente, teste de manifesto e o mesmo verificador do pacote, sem aceitar arquivos extras. O verificador executa Node/Chromium **somente** após conferir integralmente os arquivos; isso é diagnóstico do snapshot, não homologação de checkout Git nem integração S0/S1.

> **FV-UI-024 (22/10/2026):** [testes adversariais e gate do pacote offline](../docs/48_FV_UI_024_TESTES_ADVERSARIAIS_ZIP_E_GATE_NATIVO_2026_10_22.md). A validação do ZIP passa a exigir 15 cenários Python sintéticos (`test_offline_export.py`) contra adulteração/arquivos duplicados, caminhos, symlink e troca de verificador. O check nativo offline e o checkout Git exigem essa suíte, além de Node/Chromium. Manifesto Git é atualizado ao final das alterações para não misturar revisões. **Nenhum teste nativo/Chromium foi executado nesta conversa.**

> **FV-UI-025 (22/10/2026):** [gates fail-closed de validação](../docs/49_FV_UI_025_GATES_SEQUENCIAIS_VALIDACAO_2026_10_22.md). Corrigido o verificador de ZIP e o runner Git para executar **Python adversarial → Node ESM → Chromium**, interrompendo etapas posteriores se uma falhar. Testes `python -B` preservam a limpeza do checkout. A suíte adversarial agora reúne 20 testes Python. Checagem estática do código não constitui execução nativa nem homologação.

> **FV-UI-026 (22/10/2026):** [primeiro diagnóstico nativo Python/Node/Chromium](../docs/50_FV_UI_026_EXECUCAO_NATIVA_DIAGNOSTICO_2026_10_22.md). O ZIP original com 54 blobs verificados obteve 20/20 Python e 316/317 Node; o Chromium foi bloqueado pelo gate. Duas correções nos **testes** (regex da matriz FV-22 e espera de foco no Chromium) permitiram **20/20 Python, 317/317 Node e smoke Chromium PASS** em cópia local derivada com manifesto atualizado. Isto **não** homologa checkout Git nem serviços reais. Repetir sobre nova exportação pinada da branch.

> **FV-UI-027 (23/10/2026):** [reflow, rolagem em janela baixa e movimento reduzido](../docs/51_FV_UI_027_REFLOW_REDUCED_MOTION_CROMIUM_2026_10_23.md). Em viewport curto (até 700px de altura e 760px de largura), a lista de conversas agora rola inteira, tornando o rodapé e casos acessíveis sem overflow horizontal. Smoke Chromium passa a testar 720×850, 360×500 e 320×640 CSS px, foco móvel, conteúdo alcançável e `reduced_motion='reduce'`. Diagnóstico em cópia local derivada: **20/20 Python, 318/318 Node, Chromium PASS**. Não representa zoom de navegador real, leitor de tela nem homologação de checkout Git.

> **FV-UI-028 (23/10/2026):** [painel móvel anunciado corretamente e foco acessível](../docs/52_FV_UI_028_ARIA_EXPANDED_FOCO_TECLADO_2026_10_23.md). O botão de detalhes atualiza `aria-expanded` junto com a navegação móvel, sem mudar o comportamento do painel desktop. Nos controles das superfícies claras, o foco ganha contorno `#11685d` contrastante, incluindo `textarea` e `summary`. Testes nativos em cópia derivada do ZIP: **20/20 Python, 320/320 Node, smoke Chromium PASS** com Tab, Escape e viewports 390×844 e 320×640. O estado de homologação Git permanece pendente.

> **FV-UI-029 (23/10/2026):** [foco e anúncio em confirmações aninhadas de equipe](../docs/53_FV_UI_029_RETORNO_FOCO_MODAIS_ANINHADOS_2026_10_23.md). Confirmações de pausa/retomada e fila compartilhada deixam de perder o foco após o rerender do botão que abriu o diálogo. O foco retorna à aba estável da janela da equipe, com anúncio `role="status"` de efeito **somente local**. Cenários Chromium em 390×844 e 1366×768 e testes de regressão em snapshot local: **20 Python, 323 Node, Chromium PASS**. Não é homologação de checkout Git nem autorização S0/S1.

> **FV-UI-030 (23/10/2026):** [separação dos testes para suportar redesign](../docs/54_FV_UI_030_TESTES_POR_CAMADA_PREPARACAO_REDESIGN_2026_10_23.md). Diagnósticos seletivos por `node frontend/visual/tests/run_validation_layers.mjs domain|interaction|source|browser`: 19 suítes de domínio, 3 de interação, 5 de contratos/integridade e 1 smoke Chromium. **Após mudar a estrutura do layout, os testes de interação e navegador precisam ser repetidos e, se necessário, atualizados.** Isso não substitui `run_acceptance.py` em checkout Git verificado nem prova autorização externa.

**Branch proprietária:** `feat/frontend-plataforma-visual`. **Referência visual:** organização de mensageiro familiar ao WhatsApp, sem copiar sua identidade, marca ou recursos. **Situação:** demonstração local com dados 100% sintéticos; não é portal operacional.

## Abrir localmente

Na raiz do repositório:

```bash
python3 -m http.server 4174 --directory frontend/visual --bind 127.0.0.1
```

Abra `http://127.0.0.1:4174` no navegador. Não publicar na internet nem expor o servidor de demonstração na rede. Não há instalação de dependências. O carregamento de módulos ES exige HTTP local, e não `file://`.

## Testar fixtures e sintaxe

```bash
node --check frontend/visual/fixtures.mjs
node --check frontend/visual/app.mjs
node --test frontend/visual/tests/*.test.mjs
```

Os seis testes de regras artificiais foram executados localmente, com resultado PASS. A inspeção visual e navegação em Chromium headless foi realizada nos tamanhos 1440, 900, 390 e 320 px, sem erro de script nem overflow horizontal. Por restrições do ambiente, o navegador de testes recebeu HTML/CSS/JS localmente e não acessou a URL via rede; a carga HTTP direta ainda precisa de verificação em ambiente permitido.

## Experiência demonstrada

- **Desktop:** barra lateral fina, lista de conversas e filtros, conversa aberta e painel de detalhes.
- **Celular:** lista → conversa em tela cheia → detalhes; botões para voltar.
- **Perfis fictícios:** operadores Rafael, Bianca e Lia e gestora Marina (equipe Prumo). A gestora visualiza lojas concedidas e pode agir apenas num caso de exemplo autoatribuído. **Esse seletor não autentica ninguém.**
- **Conversa:** mensagens sintéticas podem ser acrescentadas só na memória do navegador. Nada é transmitido.
- **Conclusão FV-02:** botão em caso humano atribuído abre confirmação e mostra solicitação fictícia; detalhe pode demonstrar resultado parcial fictício. Não chama OpenAI nem grava cadastro.
- **Cadastro:** não há formulário de preenchimento manual habitual. Catálogo definitivo de campos, correções excepcionais C13 e processamento real pertencem às frentes responsáveis.
- **Estados comerciais:** somente os oito aprovados. Conclusão/extração são eventos técnicos, não marcos de venda ou remessa.

## Limites críticos

O código **não possui** autenticação, RLS, backend, Supabase, OpenAI, Meta/WhatsApp, instituição financeira, gravação persistente, API, chamadas de rede, cookies, localStorage, segredos nem dados reais. Filtrar dados no JavaScript de uma demonstração não protege informações; em implantação o S0 deve filtrar no servidor.

Esta área `frontend/visual/` é **separada** de `frontend/s1/` e da branch `feat/s1-002-equipe-prumo` (frente S0). Não reutilizar a demonstração como regras de negócio. A integração depende dos contratos FV-01/FV-02 e da revisão S0/OpenAI [Issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4), ainda pendente.

**Identidade:** Prumo é referência técnica e organizacional, não nome comercial aprovado da plataforma. LiberaCred é produto da instituição financeira.

## Critérios de continuidade

Revisar estética/responsividade com responsável; testar navegação por teclado e tecnologia assistiva; obter revisão S0/OpenAI antes de consumir serviços reais. Não configurar domínio, hospedagem ou migrações.

## FV-UI-002 — Incremento funcional de interface, 18/10/2026

Sem alterar a identidade do protótipo, foram acrescentados filtro por status comercial (apenas os oito valores canônicos), indicadores sintéticos da fila, quatro abas de detalhe (**Resumo, Histórico, Notas e Extração**), notas internas demonstrativas, visão de equipe apenas para o perfil fictício de gestor e três cenários de retorno da extração (parcial, falha, versão obsoleta), além do pedido aceito. Nenhum cenário persiste a ficha, envia mensagem ou modifica estado comercial.

Teclas adicionais: **Ctrl/Cmd+K** busca, setas direita/esquerda para abas e Escape para voltar em telas pequenas fora de formulários/dialogs.

**Teste Node executado:** `node --test frontend/visual/tests/*.test.mjs` → **12/12 PASS**. **Teste Chromium headless executado:** quatro larguras (1440, 900, 390, 320) e fluxo de gestor/duas lojas, sem erro JS nem overflow. O ensaio Chromium foi feito por injeção local de HTML/CSS/JS pois o ambiente bloqueia HTTP loopback; ele não valida serviço HTTP ou autenticação. Roteiro opcional reproduzível (com Playwright + Chromium já instalados): `python frontend/visual/tests/browser.smoke.py`.

[Auditoria FV-UI-002](../docs/10_AUDITORIA_FRONTEND_FV_UI_002_2026_10_18.md). Falta aprovação visual futura, acessibilidade aprofundada e homologação de integração; **não é aplicação de produção**.

## FV-03 — revisão após CF-OP-02 (18/10/2026)

**Diretriz vigente:** [FV-03](../docs/09_CF_OP_02_CONTRATO_VISUAL_JANELA_CADEIAS_v0_1.md), com [auditoria e reparos registrados](../docs/12_AUDITORIA_CONFORMIDADE_FV03_CF_OP_02_2026_10_18.md).

- A lista de **Ativas / pendentes** só inclui projeções explícitas `inboxProjection=active`; **Histórico** permite consultar, sem apagar mensagens, projeções `historical`. Um caso sem projeção não fica visível por inferência.
- `metaWindowProjection=open/expired/unknown` é fornecida pela fixture (futura S0). **Não existe relógio JavaScript que autorize mensagem livre ou que marque perdido**.
- Profissional Prumo ativo, com loja e atribuição válidas na projeção de demonstração, só tem compositor livre quando o S0 fictício sinaliza `allowedActionsProjection.free_text`. A janela vencida mantém a conversa humana **não concluída** na lista e exibe, se elegíveis, ações distintas para **template único** e **solicitação de cadeia**.
- Modelos do modal são **fictícios, pré-listados por caso e versão**. O retorno do clique é `requested`, jamais prova `sent`. Cadeia ilustrativa mostra tentativas agendadas/pendentes e template final separado, sem criar plano real.
- Atendimento humano concluído pode continuar na lista ativa se a janela fictícia ainda está aberta. Concluído+janela expirada aparece no histórico, sem exclusão. A aba de extração não afirma resultado quando apenas a conclusão está projetada.
- Perfil suspenso fica sem carteira no simulador; gestora pode enxergar caso em **fila protegida**, sem escolher novo atendente. A operação verdadeira cabe à S1-002/S0.
- `cadastro enviado ao banco` e `vendido` nunca passam a `perdido` por silêncio nesta UI. O único exemplo de caso perdido está pré-projetado em fixture histórica de ciclo elegível, jamais calculado.

**Verificação realizada:** 24/24 testes sintéticos executados sobre o conteúdo da branch GitHub por harness de asserções V8; sintaxe dos módulos aprovada; inspeção de HTML/CSS e guardas sem chamada externa. **Ainda pendente:** execução do script Playwright atualizado depois da FV-03, acessibilidade aprofundada e contratos reais. Testes Node da FV-UI-002 de 12/12 permanecem históricos e não comprovam as novas capacidades. Não é aplicação de produção.

## FV-UI-004 — Reforço de interação

O protótipo agora oculta a visão Equipe de operadores e perfis suspensos, distingue equipe indisponível, protege os diálogos contra confirmação residual e relaciona melhor as abas de detalhes ao painel acessível. O roteiro Playwright foi atualizado para também testar equipe móvel e cancelamento de template, **ainda não reexecutado**. Seis novos testes de inspeção de fonte foram criados em `tests/source-contract.test.mjs`, além das 24 provas de lógica sintética já executadas em V8. Ver [registro de qualidade](../docs/13_AUDITORIA_FV_UI_004_USABILIDADE_E_REGRESSOES_2026_10_18.md). Sem integração real.

## FV-UI-005 — Ensaios de DOM desktop e mobile

`tests/dom-fixture.mjs` e `tests/app.dom.test.mjs` / `app.mobile.dom.test.mjs` verificam navegação, diálogos, seleção de template elegível, acesso à equipe e suspensão **com DOM simulado**. **36/36 PASS** no V8, incluindo os 24 testes anteriores de regras. O atalho Ctrl/Cmd+K não tira o foco de um modal aberto. [Relatório FV-UI-005](../docs/14_TESTES_INTERACAO_FV_UI_005_2026_10_18.md). Node direto e Chromium real após FV-03 **ainda não executados**.

## FV-UI-006 — Concorrência visual e estados conservadores

Ao solicitar conclusão, o protótipo apresenta **“Conclusão solicitada”**, não “etapa concluída” ou ficha gravada. Sem projeção S0 de conclusão, aparece **não confirmada**. Mudanças de ator, loja, conversa e inbox invalidam diálogos anteriores; callbacks de notas/extração recusam referência a caso antigo. Foi adicionada cobertura de testes para esses cenários.

**Evidência:** 48/48 verificações sintéticas em V8 sobre conteúdos recuperados da branch (25 regras, 17 testes DOM, 6 inspeções de código). **Não** foram executados nesta revisão Node nativo ou Chromium real. [Relatório FV-UI-006](../docs/15_AUDITORIA_FV_UI_006_FIDELIDADE_E_CONCORRENCIA_2026_10_18.md).

## FV-UI-007 — Ficha processada e sigilo de dados

A aba **Extração** possui agora um cenário ilustrativo O3 (`A-108`) com **versão fictícia confirmada, origem, informação aplicada, ausência e contradição**. Informação somente proposta não é exibida como dado salvo. O perfil gestor em mera supervisão vê apenas um resumo; os detalhes de ficha permanecem omitidos. A implementação em `registration-view.mjs` usa **projeções 100% sintéticas**; filtros de JavaScript **não** protegem dados reais — S0 deverá minimizar antes de enviar resposta.

**60/60 verificações sintéticas aprovadas em harness V8** (33 regras, 19 interações DOM, 8 inspeções); Node direto/Chromium pós-FV-UI-007 ainda não executados. [Auditoria O3](../docs/16_AUDITORIA_FV_UI_007_FICHA_PROVENIENCIA_2026_10_18.md).

## FV-UI-008 — Banco (O4) somente leitura e dados fictícios

Na aba **Banco**, o caso A-105 ilustra remessa humana verificada no cenário e **retorno não comprovado**. O navegador não processa prova, marca vendido/perdido ou comunica a instituição financeira. Gestores de mera supervisão recebem apenas resumo, sem conteúdo D4; o perfil sem atribuição não recebe detalhes. Novo módulo `bank-view.mjs`, teste `tests/bank-view.test.mjs` e roteiro Chromium atualizado.

**Evidência:** 77/77 verificações sintéticas em V8 (46 regras, 21 interações, 10 estáticas), com [auditoria completa](../docs/18_AUDITORIA_O4_BANCO_FV_UI_008_2026_10_19.md). **Ainda pendente** executar checkout atual com Node e Chromium real, além da homologação S0/Banco.

## FV-UI-009 — Navegação O5 de novo ciclo humano

A aba **Novo contato** consulta vínculos sintéticos recíprocos de casos após remessa bancária ou venda: A-105 → A-114 e A-115 → A-116. Um botão abre o caso novo **já presente na fixture**, com retorno ao original preservado. **Não** cria ciclo, altera `vendido`, registra remessa, reabre a IA ou envia WhatsApp. Alteração de loja, perfil, vínculo ou versão impede navegação para caso fora do escopo. O compositor do novo caso só simula a operação do profissional atribuído, com janela e permissão projetadas. Ver [auditoria FV-UI-009](../docs/19_AUDITORIA_O5_NOVO_CONTATO_FV_UI_009_2026_10_19.md).

**Validação:** 96/96 ensaios sintéticos PASS (59 domínio, 25 DOM, 12 fonte). Checkout Node direto/Chromium real, segurança S0, mensagens Meta e criação C14 seguem pendentes.

## FV-AUD-05 — Correções antes de continuar G2–G4

Os projetores de ficha/banco negam qualquer resumo a operador não designado; O5 permite operação no **novo** caso autorizado sem conceder leitura do histórico anterior; `copyCFDemoFixtures` isola objetos de projeção entre resets. Regressão **105/105 PASS** apenas com harness V8, sem execução nativa do Node nem Chromium atual. [Auditoria e limites](../docs/20_AUDITORIA_RETROSPECTIVA_FV_UI_004_009_2026_10_19.md).

## Atualização de autoridade G1/G2 — gestão por operadores (19/10/2026)

**Orientação nova do responsável:** cada gestor supervisiona um grupo de operadores da Prumo, não concessionárias inteiras. Pode solicitar pausa do recebimento de novos leads de **uma pessoa em todas as concessionárias já concedidas** e acompanhamento do remanejamento; **não** pode selecionar A versus B, criar concessão C ou gerenciar membros fora da equipe. Concessões de loja e composição de equipes pertencem ao responsável. A FV-UI-010 agora demonstra Marina e Daniel com **equipes distintas por operador** e disponibiliza botões de pausa/retomada **somente local**, sem endpoint, suspensão, realocação ou mudança real de concessões. Veja [FV-G2-01](../docs/21_FV_G2_01_GESTAO_POR_OPERADORES_E_PAUSA_GLOBAL_2026_10_19.md) e [issue interfrentes #9](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/9).

### FV-UI-010 — Testes e limites de integração (19/10/2026)

A gestão G2 opera exclusivamente com dados demonstrativos e mantém **disponibilidade de novos leads** separada de **estado da conta**. O seletor de concessionária filtra conversas, não altera a equipe; solicitações de pausa são globais para todas as lojas já concedidas a cada profissional e não alteram o estado confirmado. A relação gestor→operadores, concessões e distribuição precisam ser confirmadas pelo backend. **123/123 verificações sintéticas no harness V8**; Playwright/Chromium e `node --test` sobre o checkout atual **não executados**. [Auditoria](../docs/22_AUDITORIA_G2_EQUIPE_POR_OPERADORES_PAUSA_GLOBAL_2026_10_19.md).

## FV-UI-011/012 — Painel G3 e lotes G4 por equipe

O gestor fictício acessa **Operadores**, **Monitoramento** e **Lotes**. G3 concilia os oito status comerciais num quadro separado dos indicadores técnicos e mostra alertas somente quando há projeção fictícia S0. G4 utiliza projeções de lotes versionadas e minimizadas por gestor/equipe/loja; não contém upload, aceite de arquivo, seleção de destinatário nem concessões novas. Ao trocar gestor, os dados renderizados das três abas são apagados.

**180/180 verificações sintéticas G2–G4 aprovadas** (110 regras, 45 interações DOM, 25 inspeções). **Node direto/Chromium real ainda pendentes.** Auditorias: [G3](../docs/23_AUDITORIA_G3_MONITORAMENTO_UNIFICADO_FV_UI_011_2026_10_19.md) e [G4](../docs/24_AUDITORIA_G4_LOTES_EQUIPE_FV_UI_012_2026_10_19.md).


### FV-UI-013 — Execução nativa com revisão rastreada (19/10/2026)

A validação integral só pode ser declarada se houver um checkout Git completo, limpo e situado na branch `feat/frontend-plataforma-visual`, com o SHA **idêntico** ao HEAD da branch consultado no GitHub. Após conferir o SHA atualizado, executar a partir da raiz do repositório:

```bash
python3 frontend/visual/tests/run_acceptance.py \
  --expected-head SHA_COMPLETO_DE_40_CARACTERES \
  --json-report /tmp/fv-ui-013-evidencia.json
```

Se Chromium não estiver no caminho usual, definir `CHROMIUM_EXECUTABLE` antes do comando. O runner recusa checkout truncado, branch/revisão diferentes ou alterações locais em `frontend/visual`; `--skip-browser` nunca é aceite completo. A suíte possui verificação que compila o bundle de teste Chromium como script único. A verificação da revisão, o bloqueio em checkout incompleto e seis cenários artificiais de orquestração do executor foram exercitados em ambiente local; **não houve execução Node/Chromium do frontend privado completo nesta etapa**. Consulte [auditoria FV-UI-013](../docs/25_AUDITORIA_TECNICA_FV_UI_013_2026_10_19.md). Não declarar homologação ou alterar a régua 19F em razão destes ensaios.

## FV-UI-031 — Foco após adicionar nota fictícia (23/10/2026)

Ao incluir nota na aba **Notas**, o formulário é reconstruído e o foco retorna ao novo campo `#note-text`. A nota permanece somente em memória e o callback obsoleto continua rejeitado. O teste DOM, o smoke Chromium e a inspeção de fonte receberam regressões, **ainda não executadas nativamente nesta revisão**. Veja [FV-UI-031](../docs/55_FV_UI_031_FOCO_APOS_NOTA_LOCAL_2026_10_23.md). O redesign futuro e a homologação de checkout Git permanecem pendentes.

## FV-UI-032 — Navegação acessível na Extração e no vínculo O5 (23/10/2026)

Na aba **Extração**, resultados técnicos fictícios e esclarecimento que recriam controles restauram o foco na aba ativa, com aviso de contexto. A navegação O5 para caso já projetado restaura foco na conversa do destino em desktop/tablet e no botão Voltar no celular. Não cria caso ou execução F03, nem concede acesso novo. Testes DOM, mobile e roteiro Chromium receberam regressões. [FV-UI-032](../docs/56_FV_UI_032_FOCO_EXTRACAO_NAVEGACAO_O5_2026_10_23.md).

## FV-UI-033 — Zoom/reflow com foco estável ao alternar desktop e celular (23/10/2026)

O listener de transição de breakpoint preserva o painel que continha o foco (Lista, Conversa ou Detalhes). Se a tela encolher enquanto um controle de Detalhes estiver ativo, o aplicativo mantém a aba visível e recupera o foco antes perdido; ao expandir a viewport, uma aba Detalhes aberta no móvel permanece acessível no desktop mesmo quando o painel lateral estava recolhido originalmente. Modais retêm o próprio foco; não há mudança de atribuição, dado ou autorização. Teste Chromium inclui 1440→360→1440, 320→1440, foco em busca/compositor e teclado Home/End. Valores de viewport representam **reflow equivalente**, não comprovam zoom real no navegador. [FV-UI-033](../docs/58_FV_UI_033_REFLOW_FOCO_BREAKPOINT_2026_10_23.md).

## FV-UI-034 — Fechamento acessível do painel Detalhes em tablet (23/10/2026)

Em largura intermediária (761–1040 CSS px), o botão **Fechar detalhes** e a tecla **Escape** no painel flutuante agora fecham somente o painel visual e devolvem o foco ao botão **Mostrar detalhes**. Escape dentro do compositor/editor de nota não fecha o painel; diálogos nativos não são interceptados. Caso selecionado, conteúdo de ficha, papel e autorização não mudam. Cobertura: testes DOM com fixture tablet, regressão estática e Chromium em 900/1024 px. [FV-UI-034](../docs/60_FV_UI_034_FOCO_FECHAR_DETALHES_TABLET_2026_10_23.md).

## FV-UI-035 — Foco após ampliar viewport móvel para tablet/desktop (23/10/2026)

O controle **Voltar** existe somente no layout móvel e desaparece ao ampliar a janela. Na transição de 390 para 900/1440 CSS pixels, quando esse botão estava focado, o foco agora vai à região nomeada da **Conversa** (`#thread-pane`) ou à aba ativa de **Detalhes** ainda autorizada e visível. O tratamento não muda caso, atendimento, permissão, rascunho ou evento comercial, e não interfere no foco de diálogo modal. O teste Chromium cobre os dois destinos, incluindo reflow e ausência de overflow; **não substitui zoom manual ou leitor de tela humano**. [FV-UI-035](../docs/62_FV_UI_035_FOCO_MOBILE_PARA_DESKTOP_2026_10_23.md).
