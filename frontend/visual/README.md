# FV-UI-001 — Central de Atendimento, estrutura visual responsiva

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
