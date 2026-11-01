# FV-UX-BG-01 — Missão de implementação: Banco e Gestão como páginas da Prumo

**Estado:** IMPLEMENTAÇÃO CANDIDATA EM CURSO, sem aceite funcional/visual, merge ou deploy. O protótipo usa temporariamente elementos `<dialog>` abertos com `.show()` **não modal**, posicionados como páginas internas do workspace, sem top layer; conversão semântica para landmarks `section` e auditoria de leitor de tela seguem necessárias antes da conclusão. **Data:** 01/11/2026. **Base isolada:** `fix/fv-banco-aud-02-fail-closed-20261101` @ `040547d29231561cc3881e85be6abe85f01c8bad`; conferir CI/base antes de integrar código. **Decisão de produto:** [doc. 104](./104_FV_BANCO_01_LISTA_APTOS_TELAS_PROPRIAS_2026_11_01.md), protocolo [#4](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/4) e dependência [#15](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/15).

## Objetivo observável

Ao clicar **Conversas**, **Banco** ou **Gestão** no menu principal, navegar entre **áreas/páginas do mesmo aplicativo**, não abrir `bank-dialog.showModal()` nem `team-dialog.showModal()`. Diálogo só para confirmação pontual permitida. Área Banco tem **lista exclusivamente de nomes de clientes aptos** e detalhe de ficha autorizada, sem etiquetas "Cadastro pronto", sem pendentes/retorno/remessas anteriores. Gestão tem tela independente com Consultores, Monitoramento, Lotes e Fila Compartilhada, condicionada a role/grant.

## Escopo de trabalho técnico

### 1. Navegação e estrutura
- Definir estado discriminado `activeModule` (conversations|bank|team) e áreas com landmarks/heading próprios. Desktop mantém menu lateral e workspace principal. Mobile oferece navegação equivalente e **lista → ficha → voltar**, preservando foco e URL/histórico apenas se a arquitetura existente realmente suportar.
- O menu de Gestão fica oculto/inacessível para Consultor e Gestor inativo. A navegação não modifica `selectedCase`, `demoReadProjection`, atribuição ou status comercial. Entrar em Banco não marca leitura operacional nem abre chat.
- Na troca para Banco/Gestão, rascunho de mensagem/note/áudio não é enviado, descartado nem transportado para outro caso. Respeitar o isolamento já implementado por ator/loja/caso; mudança de perfil/loja pode limpar informações conforme guardas existentes.
- Remover dependência da navegação principal em `showModal()/close()` dos módulos; manter modais menores como confirmação de ações e seus controles de teclado. Ajustar `closeFloatingDetails`, `resize`, `focusExtractionAfterRerender` e seleção após atualização.

### 2. Banco (única fila de entrada)
- **Fonte da lista:** `projectBankReadyList(state.cases,state.actorId,state.shopId)` (somente itens `{id,name}`). Nada de `accessible()` como universo do Banco; este último serve a Conversas. `unavailable` e continuação pós-marco permanecem excluídos até contrato S0.
- Lista pesquisável por nome, item com **somente o nome** como texto visível; nenhuma tag status, CPF, telefone, loja ou referência de remessa no item. Caso nomes sejam iguais, preservá-los em itens distintos com chaves internas, acesso a detalhes devidamente autorizado, contexto acessível sem introduzir novo vazamento de PII.
- Ao selecionar, reconsultar `bankReadyCaseForSelection` e validar ator/loja/caso/aptidão atuais antes de exibir qualquer ficha. Conteúdo D3/D4 só para titular com autorização explícita. Sem consulta a dados reais do cliente ou acesso interloja.
- Reaproveitar o renderizador de ficha existente (valores confirmados, fontes, versões e informações necessárias), na página; não duplicar lógica F03/O3 e não editar ficha manualmente. Se não houver aptos, apresentar estado vazio **"Nenhum cadastro apto para encaminhamento nesta concessionária"**, sem inventar clientes para maquiar a ausência.
- **Registro de envio** futuro C15–C18: no protótipo somente explicar capacidade não habilitada. Não oferecer botão que transfira status por clique local. Registros já enviados e aguardando retorno pertencem ao **histórico**, não à fila de aptos.
- A linha do tempo de remessa e retorno permanece recuperável a partir dos destinos já autorizados, sem confundir busca no histórico com tarefa de registrar novo envio.

### 3. Gestão
- Reaproveitar G1–G4 sem alterar projeções S0/S1 candidatas, contagens ou concessões: Consultores, Monitoramento, Lotes e Fila Compartilhada.
- Conteúdo e botões exibidos conforme `canSeeTeamSummary`, minimizando dados de supervisor. Ao alternar de ator/loja, limpar DOM e estado de equipe anterior antes de renderizar nova área.
- Preservar confirmações locais com `intake-dialog`/`queue-action-dialog`, sem transformá-las em operações reais de pausa/assunção/distribuição; foco volta a aba/ação visível da página, não à janela fechada.

### 4. Testes e UX
- Atualizar explicitamente testes existentes que esperam `bank-dialog`/`team-dialog` (DOM e Chromium), **sem desativá-los**. Confrontar `app.dom`, `app.mobile.dom`, `modules.dom`, `browser.smoke`, `browser.modules`, `browser.revision`, `source-contract` e `source-module-graph`.
- Casos mínimos: (a) Consultor abre Banco, vê apenas nomes aptos; (b) estado desconhecido/continuation/pendência excluído; (c) seleciona e volta sem marcar chat lido; (d) Gestor supervisor sem D3/D4; (e) troca ator/loja limpa DOM e previne acesso obsoleto; (f) manter rascunhos de chat por contexto, áudios e notas; (g) nome duplicado; (h) 320/390/740/900/1440 pixels, claro/escuro, foco, teclado, Escape e zoom; (i) Gestão indisponível no perfil sem autorização; (j) nenhuma remessa local.
- Suítes Node, testes Chromium nos modos ESM/HTML integral, exportação/offline, manifesto pinado após commit de conteúdo; `FULL LOCAL ACCEPTANCE: PASS` no SHA final. Reexecutar todos os testes herdados afetados; passar gate não é aceite visual.

## Dependências/autoridade

S0/S1 tem pendência [#15](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/15): aptidão versionada, ausência de remessa conhecida, nova operação versus remessa prévia, campos essenciais/opcionais e autorização de registro humano. Não abrir outra Issue. Enquanto não entregar, simular somente o caso vazio e casos de teste locais; não implementar contratos de backend ou RLS por conta própria.

**Fora do escopo:** merge na main, deploy, emissão de mensagens, API Meta/Graph/OpenAI/Banco, alteração real de status, acessos D3/D4 não autorizados ou redesenho comercial. **Aceite independente** obrigatório após CI: comparar fluxo autorizado e capturas da nova UI; manter o relatório de limitações e devolver achados por prioridade.
