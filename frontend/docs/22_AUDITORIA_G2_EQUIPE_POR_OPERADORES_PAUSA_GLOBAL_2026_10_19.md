# FV-UI-010 — Auditoria G2: gestores por operadores e pausa global de novos leads

**Data:** 19/10/2026. **Branch:** `feat/frontend-plataforma-visual`. **Escopo:** arquivos em `frontend/`. **Objetivo:** implementar a direção de negócio [D] de 19/10 do responsável: gestor administra **operadores** da Prumo, não o conjunto inteiro de casos de uma concessionária. Concessões A/B/C e composição das equipes permanecem exclusivas do responsável. [Contrato candidato FV-G2-01](21_FV_G2_01_GESTAO_POR_OPERADORES_E_PAUSA_GLOBAL_2026_10_19.md); [issue entre frentes #9](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/9).

## Entregas efetivas na demonstração

- `fixtures.mjs`: vínculos ilustrativos de gestores Marina → Rafael/Lia; Daniel → Bianca/Otávio. Mesmas concessionárias podem ter operadores sob gestores distintos. O cenário de Bianca contempla concessões fictícias A+B e `paused_confirmed`, **sem perda de acesso aos casos que ainda aparecem atribuídos**. O campo `teamManagerId` dos casos sem operador atribuído identifica a equipe na projeção demo; **não representa tabela nem contrato S0 aprovado**.
- `visibleConversations`: gestor vê somente casos atribuídos a membros de sua própria equipe (e casos explicitamente alocados à sua equipe sem titular, ou autoatribuídos a si); operador vê somente seus casos. **Concessão por loja continua uma restrição cumulativa de privacidade até especificação física S0/S1.** Não foi implementada distribuição real.
- `team-operations.mjs`: projeção da equipe e solicitação G2 `pause/resume` restrita a operador sob gestor, apenas para **todas** as suas lojas já concedidas; não oferece controle por concessionária nem consegue alterar `shops`, `teamState`, `assignedTo` ou status comercial.
- `app.mjs`: painel Equipe abre para gestor ativo independentemente do filtro de loja; mostra operadores, suas lojas **somente leitura**, condição da conta separada do recebimento de novos leads, atendimentos autorizados e confirmação visual `SOLICITADO LOCALMENTE — NÃO aplicado`. O pedido fica no browser e é descartado na troca de perfil ou no reset. Perfil operador/suspenso não aciona a função.
- `registration-view.mjs` e `bank-view.mjs`: a filtragem de leitura de caso agora reutiliza `visibleConversations`, negando acesso D2 da **equipe alheia**, sem expor D3/D4 ao gestor não autoatribuído.
- `index.html`, `styles.css` e roteiro `browser.smoke.py`: rótulo da concessionária como filtro, texto da pausa global, diálogo com rolagem em tamanhos menores e roteiro atualizado. **O roteiro Chromium foi alterado, não executado aqui.**

## Correções de regressão

1. Testes antigos supunham gestor com visibilidade de toda a loja; foram adaptados para duas equipes distintas sem misturar operadores/casos.
2. `canSeeTeamSummary` exigia concessionária selecionada, embora a equipe seja de pessoas. Corrigido: a visualização da equipe depende de gestor ativo, não do filtro de loja (sem conceder leituras adicionais da fila).
3. Teste de fonte procurava mensagem de pedido pendente no `app.mjs` em vez do módulo `team-operations.mjs`; as asserções foram corrigidas.
4. Cenários de UI desktop e mobile passam a validar pedidos `pause/resume` locais, a impossibilidade de escolher loja, a persistência ilustrativa do estado confirmado e a ausência de mudança comercial.

## Evidência executada sobre os arquivos recuperados da branch

Os módulos/testes foram recuperados do GitHub após as alterações e submetidos a harness JavaScript V8 com importações e asserções adaptadas:
- **75/75** testes de regras/projeções, incluindo 10 cenários específicos de G2.
- **30/30** interações de DOM simulado (desktop e mobile), incluindo cenários de isolamento por equipe, pausa e retomada.
- **18/18** inspeções estáticas de HTML/CSS/JS e roteiro de navegador.
- **Total: 123/123 verificações sintéticas PASS.** Os módulos de produção examinados passaram pela análise de sintaxe no harness; `import.meta` no teste Node estático é sintaxe válida de módulo, não expressão executável de função simples.

**Não executado:** `node --test` nativo, Playwright/Chromium da versão privada atual, leitor de tela e integrações S0/S1/Meta. O checkout integral autorizado da branch não está disponível no container local; a rede direta do GitHub também não está acessível ali. Não afirmar que a interface está homologada ou que os 123 testes validam operações reais.

## Limites abertos

- A regra de negócio entra em **conflito** com S1-002/I10 anterior, que concedia gestão por loja e pausa A sem B. Essa regra antiga não deve ser implementada silenciosamente; [issue #9](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/9) acompanha a conciliação.
- Cabe ao S0/S1-002 definir projeção autorizada de equipe, políticas de escopo/tenant/concessões, comando autenticado de pausa global, período, idempotência, redistribuição transacional, fila protegida, reativação e auditoria. **Pedido local não redistribui nem bloqueia novos leads.**
- Datas/atestados e informações médicas **não** são capturados por esse painel; somente dados operacionais minimizados devem chegar ao gestor.
- A UI G3 de monitoramento de equipe e G4 de lotes ainda exige execução incremental sem falsa evidência. Não houve merge, deploy, operações em Supabase, mudanças no backend ou reajuste automático do progresso auditado 19F (**69/100**).

**Veredito:** G2 coerente e sinteticamente testado segundo a orientação mais recente, **não integrado nem homologado para produção**.
