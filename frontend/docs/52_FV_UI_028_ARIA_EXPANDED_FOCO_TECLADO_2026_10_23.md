# FV-UI-028 — Estado acessível dos detalhes móveis e foco visível por teclado

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** exclusivamente `frontend/`, fixtures e testes sintéticos. **Não homologado em produção.**

**Referências:** [FV-UI-021](./45_FV_UI_021_PREPARACAO_S0_S1_ACESSIBILIDADE_2026_10_22.md), [FV-UI-026](./50_FV_UI_026_EXECUCAO_NATIVA_DIAGNOSTICO_2026_10_22.md) e [FV-UI-027](./51_FV_UI_027_REFLOW_REDUCED_MOTION_CROMIUM_2026_10_23.md).

## Falha reproduzida no Chromium real

Na viewport **390×844 CSS px**, o botão `#detail-toggle` permanecia com `aria-expanded="false"` mesmo quando a navegação móvel já exibia o painel `#detail-pane`. A sequência observada antes da alteração foi:

| Etapa | Painel visível | `aria-expanded` antigo |
|---|---|---|
| Lista | Conversas | false |
| Abrir conversa | Conversa | false |
| Abrir detalhes | Detalhes | **false (incorreto)** |
| Voltar à conversa | Conversa | false |

O valor incorreto é uma discrepância de estado semântico, não evidência de falha em permissões S0. O comportamento visual da navegação já funcionava, mas não a informação de expansão para tecnologias assistivas.

O indicador global de foco pré-existente usava `#5dbbb3`, com contraste calculado aproximado de **2,28:1 contra branco**. Para superfícies claras da workspace, a cor de foco nova `#11685d` alcança aproximadamente **6,64:1 contra branco**, mantendo o contorno global mais claro no trilho escuro. Esses valores são cálculos de cores, não certificação integral WCAG.

## Alterações implementadas

- **`frontend/visual/app.mjs`**: `goto(view)` sincroniza `aria-expanded` com `view==='detail'` apenas no breakpoint móvel `(max-width:760px)`. Desktop continua com sua lógica de expansão/fechamento lateral, sem mudança de autorização, estado comercial ou mensagens.
- **`frontend/visual/styles.css`**: indicador de foco `3px solid #11685d` em botões, campos, seleção, `textarea` e `summary` nas superfícies claras do workspace e nos diálogos, preservando o estilo mais claro na barra lateral escura.
- **`frontend/visual/tests/app.mobile.dom.test.mjs`**: regressão para lista → conversa → detalhe → retorno → mudança de perfil, validando estado visível e `aria-expanded`.
- **`frontend/visual/tests/browser.smoke.py`**: testes Chromium em **390×844** e **320×640**, com verificações nativas de `aria-expanded`, tecla Escape, foco por Tab, contorno calculado `rgb(17,104,93)`, ausência de overflow horizontal e de erros JavaScript.
- **`frontend/visual/tests/source-contract.test.mjs`**: prova estática de presença das regras de sincronização e foco e cobertura do smoke.

## Evidências executadas na cópia local derivada

O ponto de partida foi o ZIP privado originalmente fornecido, já usado nos diagnósticos anteriores. As alterações FV-UI-028 foram aplicadas numa **cópia local do snapshot FV-UI-027**, com manifesto de blobs repinado para os arquivos dessa cópia.

| Gate | Resultado de execução |
|---|---|
| Python `unittest`, regressão do verificador ZIP | **20/20 PASS** |
| Node `--test`, 26 suítes | **320/320 PASS** |
| Chromium/Playwright (smoke integral, incluindo FV-UI-028) | **PASS** |
| Confronto de todos os hashes dos arquivos do Frontend na branch | Registrado após atualização final do manifesto |
| Checkout Git autenticado, árvore limpa e serviços produtivos | **Não executado** |

A cópia local derivada e o HEAD da branch não são o mesmo artefato. Os resultados nativos são evidência da cópia local; a branch recebeu alterações equivalentes nos arquivos-alvo. É necessária uma nova exportação da revisão final para repetir o diagnóstico sobre os bytes publicados.

## Limites e próximo gate

- Não foram testados leitores de tela com usuários, hardware real, voz, zoom real 200%/400%, contraste de **todos** os controles, nem navegação completa por teclado de **todos** os formulários.
- `aria-expanded` representa apenas visibilidade na demonstração; não concede escopo, altera carteira, envia mensagem Meta/WhatsApp nem confirma persistência ou operação bancária.
- Permanecem fora do escopo S0/S1, autenticação/GoTrue, RLS, Meta, OpenAI F01/F03, banco, integrações, merge e deploy.
- **Homologação FV-UI-013 continua pendente** de checkout Git autorizado e validação manual complementar de acessibilidade. A classificação histórica 19F não é modificada por este incremento.

**Próximo passo:** executar `run_acceptance.py --expected-head <SHA_COMPLETO>` em checkout Git limpo da branch e auditar os controles de foco e diálogos com teclado e tecnologia assistiva.
